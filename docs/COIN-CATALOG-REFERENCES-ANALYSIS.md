# Coin Catalog References – Code Analysis

**Purpose**: Deep code analysis of how catalog references (RIC, RPC, Crawford, Sear, etc.) work in CoinStack and where they are used.

---

## 1. How Catalog Reference Code Works

### 1.1 Domain Layer

**Entity**: `CatalogReference` (`backend/src/domain/coin.py`)

- **Definition**: Immutable value object for a single catalog reference.
- **Fields**:
  - `catalog`: str — system name (e.g. "RIC", "Crawford", "Sear", "RSC", "RPC", "BMC", "SNG").
  - `number`: str — reference number (e.g. "756", "44/5", "1234a").
  - `volume`: Optional[str] — volume (e.g. "II", "V.1").
  - `suffix`: Optional[str] — qualifiers.
  - `raw_text`: str — original text as found.
  - `is_primary`: bool — primary reference for the coin.
  - `notes`: Optional[str].

Coins hold a list of these: `Coin.references: List[CatalogReference]`.

**Repository contract** (`backend/src/domain/repositories.py`):

- `ICoinRepository.get_by_reference(catalog, number, volume=None) -> List[Coin]` — find coins by catalog reference.

---

### 1.2 Persistence (ORM)

**Two-table design (V1-compatible):**

1. **`reference_types`** (`ReferenceTypeModel`, `backend/src/infrastructure/persistence/orm.py`)
   - Stores the catalog *type* once per unique reference string.
   - Columns: `id`, `system` (e.g. "ric", "crawford"), `local_ref` (e.g. "RIC I 207"), `local_ref_normalized`, `volume`, `number`, `external_id`, `external_url`.
   - Many `coin_references` rows can point to the same `reference_type`.

2. **`coin_references`** (`CoinReferenceModel`)
   - Join table: coin ↔ reference type.
   - Columns: `id`, `coin_id` (FK → `coins_v2.id`), `reference_type_id` (FK → `reference_types.id`), `is_primary`, `plate_coin`, `position`, `variant_notes`, `page`, `plate`, `note_number`, `notes`.
   - Relationship: `CoinModel.references` → list of `CoinReferenceModel`; each has `reference_type` → `ReferenceTypeModel`.

**CoinModel** (`orm.py`):

- `references: Mapped[List["CoinReferenceModel"]]` with `cascade="all, delete-orphan"`.
- `llm_suggested_references`: JSON column storing a list of suggested reference strings (for review before applying).

---

### 1.3 Repository Mapping

**SqlAlchemyCoinRepository** (`backend/src/infrastructure/repositories/coin_repository.py`):

- **Read path (ORM → domain)**:
  - `get_by_id` / `get_all` use `selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type)` to avoid N+1.
  - `_to_domain()` builds `Coin.references` by calling `_reference_to_domain(ref)` for each `CoinReferenceModel` that has a `reference_type`.
  - `_reference_to_domain()` maps `ReferenceTypeModel` (system, volume, number, local_ref) and `CoinReferenceModel` (is_primary, notes) → domain `CatalogReference` (catalog, number, volume, suffix, raw_text, is_primary, notes).

- **Write path (domain → ORM)**:
  - **Important**: In `save()`, references are **not** written to `coin_references` / `reference_types`. The code has a TODO and currently does:
    - If `coin.references` is present, it JSON-serializes `[ref.raw_text for ref in coin.references]` into `CoinModel.llm_suggested_references`.
  - So **creating/updating a coin via the normal API (CreateCoinRequest / UpdateCoinRequest) does not persist references into `coin_references`**. References are only persisted when:
    1. The user approves LLM suggestions (see §2.4), or
    2. Some other path explicitly creates `ReferenceTypeModel` + `CoinReferenceModel` (e.g. import flow if/when it does so).

- **Search by reference**:
  - `get_by_reference(catalog, number, volume)` runs raw SQL joining `coin_references` and `reference_types` on `reference_type_id`, filtering by `rt.system`, `rt.number`, and optionally `rt.volume`, then loads full coins for those `coin_id`s.

---

### 1.4 Parsing and Validation

**Rule-based parser (infrastructure)**  
`backend/src/infrastructure/services/catalogs/parser.py`:

- `ReferenceParser` with regex patterns per system (RIC, Crawford, RPC, RSC, BMCRE, Sear, Sydenham).
- `parse(raw) -> ParseResult`: system, volume, number, subtype, normalized, confidence, needs_llm.
- Used by `CatalogRegistry.detect_system()` and by catalog services.

**Router-level parsing (LLM router)**  
`backend/src/infrastructure/web/routers/llm.py`:

- `_parse_catalog_reference(ref_text)` — returns dict `{catalog, volume, number}` for RIC, RSC, Cohen, Sear, RRC/Crawford, BMC, RPC.
- Used when applying approved LLM suggestions: parses each suggested string, then finds-or-creates `ReferenceTypeModel` and links via `CoinReferenceModel`.

**Validation (LLM router)**  
`_validate_catalog_reference(ref_text, coin_issuer, coin_mint, year_start, year_end, existing_refs)`:

- Parses the string, checks if it already exists in `existing_refs`, returns `CatalogReferenceValidation` (validation_status, confidence, match_reason, etc.). Used in the LLM review queue to show validation status for suggested refs.

**Scraper extraction**  
`backend/src/infrastructure/scrapers/shared/reference_patterns.py`:

- `REFERENCE_PATTERNS`: list of (regex, catalog_name, has_volume) for RIC, Crawford, RSC, RPC, Sear, BMC, Cohen, Sydenham, etc.
- `extract_references(text) -> List[CatalogReference]` (scraper `CatalogReference` from `shared/models.py`: catalog, volume, number, suffix, raw_text, needs_verification).
- `extract_primary_reference(text)`, `normalize_reference(raw_ref)`, `is_valid_reference(text)`.
- Used by Heritage, CNG, Biddr, eBay, Agora scrapers to pull references from auction/listing text.

---

### 1.5 External Catalog Services

**CatalogRegistry** (`backend/src/infrastructure/services/catalogs/registry.py`):

- `get_service(system)` — returns catalog service for "ric", "crawford"/"rrc", "rpc" (OCRE, CRRO, RPC implementations).
- `lookup(system, reference, context)` — reconcile reference string → `CatalogResult` (status, external_id, external_url, payload).
- `get_by_id(system, external_id)` — fetch by external ID.
- `detect_system(raw_reference)` — uses `parser.parse()` to infer system.
- `build_url(system, external_id)` — build catalog URL.

**Catalog router** (`backend/src/infrastructure/web/routers/catalog.py`):

- `POST /api/catalog/lookup` — lookup by reference string or by external_id; uses `CatalogRegistry.lookup` or `get_by_id`.
- Bulk enrich job uses `CatalogRegistry` to look up references and fill coin fields.

**Bulk enrich** (`backend/src/infrastructure/services/catalog_bulk_enrich.py`):

- `_ref_string_from_coin(coin)` — gets first reference string from `coin.references` (raw_text or "catalog volume number").
- For each coin, runs catalog lookup and builds fills (issuer, mint, legends, dates, etc.) via `ApplyEnrichmentService`.

---

### 1.6 LLM Integration

- **reference_validate** (capability): `POST /api/v2/llm/reference/validate` — LLM validates/cross-references a catalog number.
- **catalog_parse** (capability): `POST /api/v2/llm/catalog/parse` — LLM parses a reference string into components.
- **context_generate**: Can suggest new references; they are stored in `llm_suggested_references` (JSON list of strings).
- **image_identify / legend_transcribe**: Can suggest references; also end up in suggestion fields or identify response.
- **Review queue**: Coins with `llm_suggested_references` (or other llm_suggested_* ) appear in `GET /api/v2/llm/review`; each suggested ref is validated with `_validate_catalog_reference`.
- **Approve**: `POST /api/v2/llm/review/{coin_id}/approve` parses each suggested ref with `_parse_catalog_reference`, find-or-creates `ReferenceTypeModel`, creates `CoinReferenceModel` links, then clears `llm_suggested_references`.

---

## 2. Where It Is Used and How

### 2.1 API (V2 Coins)

- **GET /api/v2/coins**, **GET /api/v2/coins/{id}**: Response includes `references: List[CatalogReferenceResponse]` (catalog, number, volume, suffix, raw_text) and `llm_suggested_references: List[str]`.
- **POST /api/v2/coins** (CreateCoinRequest): **Does not** include references. CreateCoinDTO has no references; repository save does not write to `coin_references` (only to `llm_suggested_references` if domain had references, which create flow doesn’t set).
- **PUT /api/v2/coins/{id}**: Update path preserves `existing_coin.references` and `existing_coin.llm_suggested_references`; it does not accept or persist new references from the request body (references are not in the update request schema for normal updates).
- **GET /api/v2/coins/by-reference?catalog=...&number=...&volume=...**: Returns coins whose `coin_references` + `reference_types` match the given catalog/number/volume.

So: **references are read from DB and returned; they are only written to `coin_references` when applying LLM suggestions**, not when creating/editing a coin via the main CRUD API.

---

### 2.2 Frontend – Display

- **ReferencesCard** (`frontend/src/features/collection/CoinDetail/ReferencesCard.tsx`): Shows primary + concordance references; builds external links via `buildExternalLinks()` from `@/lib/referenceLinks`.
- **referenceLinks.ts**: `buildExternalLinks(references)` builds OCRE (RIC), CRRO (Crawford/RRC), RPC Online, ACSearch, Wildwinds, CoinArchives links from `catalog`/`number`/`volume`. `formatReference(ref)` for display.
- **CoinCard** / **CoinTableRow**: Show first reference as `references[0].catalog + ' ' + references[0].number` when present.

---

### 2.3 Frontend – Editing

- **ReferenceListEditor** (`frontend/src/components/coins/CoinForm/ReferenceListEditor.tsx`): Form array for `references` with catalog, number, notes/vol/page. Data is part of the form and can be submitted with the coin.
- **API gap**: Backend create/update do not accept or persist this references array; they only persist references when approving LLM suggestions. So edits in ReferenceListEditor are not currently persisted to `coin_references` by the standard update endpoint.

---

### 2.4 LLM Review and Apply

- **Review queue**: `GET /api/v2/llm/review` returns coins with pending `llm_suggested_references` (and other llm_suggested_*); each suggested ref is validated with `_validate_catalog_reference`.
- **AIReviewTab / LLMReviewTab**: UI for reviewing and approving suggested catalog references and rarity.
- **Approve**: `POST /api/v2/llm/review/{coin_id}/approve` creates `ReferenceTypeModel` (if needed) and `CoinReferenceModel` for each suggested ref string, then clears `llm_suggested_references`. This is the main path that **writes** to `coin_references` / `reference_types`.

---

### 2.5 Import and Scrapers

- **Scrapers** (Heritage, CNG, Biddr, eBay, Agora): Use `reference_patterns.extract_references()` or similar to get `CatalogReference` lists from descriptions; these are part of the scraped `AuctionLot` (e.g. `catalog_references` or primary reference).
- **Import**: `POST /api/v2/import/.../enrich-preview` accepts `references` and uses `CatalogRegistry.lookup()` to get catalog data and suggestions. How (or if) import persists references into `coin_references` when creating coins from import would need to be checked in the import commit/apply logic; the enrich-preview only returns suggestions.
- **Bulk enrich**: Uses existing `coin.references` (from DB) to get a reference string per coin and run catalog lookup to fill fields.

---

### 2.6 Catalog Lookup and Bulk Enrich

- **POST /api/catalog/lookup**: Reference or external_id lookup via CatalogRegistry; used by frontend or import to resolve references.
- **Bulk enrich**: Uses `_ref_string_from_coin(coin)` so it only enriches coins that already have at least one reference in the DB (from `coin_references` or from domain mapping of that).

---

## 3. Data Flow Summary

| Source of references       | Where stored                         | How they get into DB                    |
|---------------------------|--------------------------------------|-----------------------------------------|
| LLM (identify, context)   | `llm_suggested_references` (JSON)    | Written by context_generate / identify  |
| User approves suggestions | `reference_types` + `coin_references`| Approve endpoint find-or-creates rows   |
| Scrapers (auction text)   | AuctionLot / import preview          | Not written to coin_references by default unless import flow does it |
| Manual form (ReferenceListEditor) | Sent in request body        | **Not persisted** by current create/update |
| Catalog lookup / bulk enrich | N/A                               | Reads from `coin.references` (DB)       |

---

## 4. Gaps and Inconsistencies

1. **Create/Update do not persist references**: The repository `save()` does not create/update `reference_types` or `coin_references` from `coin.references`; it only dumps refs into `llm_suggested_references`. So:
   - References in the create request are ignored for DB persistence.
   - ReferenceListEditor changes are not saved to `coin_references` by the standard PUT.

2. **Single source of truth for “applied” references**: Only the LLM approve flow and any explicit import logic that creates reference_types/coin_references actually persist references. Search by reference (`by-reference`) and bulk enrich depend on that.

3. **Two parsers**: Router `_parse_catalog_reference()` in llm.py vs. `ReferenceParser` in catalogs/parser.py; behavior should stay aligned for RIC, Crawford, RPC, etc.

4. **Provenance**: `provenance_events.catalog_reference` is a separate string field on events (e.g. auction lot reference), not the same as coin-level `references`.

---

## 5. File Reference

| Layer / concern      | File(s) |
|----------------------|--------|
| Domain entity        | `backend/src/domain/coin.py` (CatalogReference), `repositories.py` (get_by_reference) |
| ORM                  | `backend/src/infrastructure/persistence/orm.py` (ReferenceTypeModel, CoinReferenceModel, CoinModel.references) |
| Repository mapping   | `backend/src/infrastructure/repositories/coin_repository.py` (_reference_to_domain, get_by_reference, save) |
| V2 API schemas       | `backend/src/infrastructure/web/routers/v2.py` (CatalogReferenceResponse, by-reference) |
| LLM parse/validate/apply | `backend/src/infrastructure/web/routers/llm.py` (_parse_catalog_reference, _validate_catalog_reference, approve) |
| Catalog services     | `backend/src/infrastructure/services/catalogs/registry.py`, `parser.py`, OCRE/CRRO/RPC |
| Catalog API          | `backend/src/infrastructure/web/routers/catalog.py` |
| Bulk enrich          | `backend/src/infrastructure/services/catalog_bulk_enrich.py` |
| Scraper extraction   | `backend/src/infrastructure/scrapers/shared/reference_patterns.py`, `shared/models.py` |
| Frontend types       | `frontend/src/domain/schemas.ts` (CatalogReferenceSchema), `lib/referenceLinks.ts` |
| Frontend UI          | `frontend/src/features/collection/CoinDetail/ReferencesCard.tsx`, `components/coins/CoinForm/ReferenceListEditor.tsx`, CoinCard, CoinTableRow, AIReviewTab, LLMReviewTab |

---

## 6. Implementation update (2026-01-29)

**Phase A implemented:**

- **Central parser**: Single entry point `parse_catalog_reference(raw) -> dict` in `backend/src/infrastructure/services/catalogs/parser.py`. LLM router `_parse_catalog_reference` delegates to it.
- **Schema**: `CoinReferenceModel.source` added (migration `scripts/migrations/add_coin_references_source.py`). Domain `CatalogReference` has optional `source`.
- **ReferenceSyncService**: `sync_coin_references(session, coin_id, refs, source, merge=False)` in `backend/src/application/services/reference_sync.py`. Used by: LLM approve (merge=True), create_coin, update_coin, import commit.
- **First-class API**: `CreateCoinRequest.references: List[CatalogReferenceInput]`, `CatalogReferenceResponse.source`. Create/update call `sync_coin_references` after save with source `"user"`. Import commit calls sync with source `"import"`.
- **Repository**: No longer writes `coin.references` into `llm_suggested_references`; refs are persisted only via ReferenceSyncService.
- **Mapping**: Comment in `coin_repository._reference_to_domain` documents ORM→domain mapping. Unit tests in `tests/unit/infrastructure/services/test_catalog_parser.py`.

**Phase B/C implemented (2026-01-29):**

- **Integrity check**: Script `backend/scripts/check_reference_integrity.py` (run: `uv run python scripts/check_reference_integrity.py [--json] [--orphans]`). Application service `src/application/services/reference_integrity.py` (`run_integrity_check`). GET `GET /api/catalog/integrity?orphans=false` returns same summary for dashboard.
- **external_id/url persistence**: Bulk enrich calls `sync_coin_references(..., external_ids={ref_str: (result.external_id, result.external_url)}, merge=True)` after successful lookup. Import confirm runs `CatalogRegistry.lookup` per ref and passes `external_ids` into `sync_coin_references`.
- **Cache and rate limit**: In-memory cache (24h TTL) and per-system rate limit (30 req/min) in `CatalogRegistry.lookup` and `get_by_id` (`backend/src/infrastructure/services/catalogs/registry.py`).
- **Numismatic validation**: `src/application/services/catalog_validation.py` — `validate_reference_for_coin(catalog, number, volume, coin_category, ...)` returns status/message (category vs catalog alignment). LLM review calls it from `_validate_catalog_reference` and includes `numismatic_warning` in `CatalogReferenceValidation`. Bulk enrich adds `numismatic_warning` to result entry when validation returns warning.
- **Frontend**: `CatalogReferenceSchema` and `CatalogReference` (referenceLinks) include optional `raw_text` and `source`. ReferencesCard shows source label when present. LLMReviewTab ReferenceBadge shows `numismatic_warning` from validated_references. mapCoinToPayload sends `raw_text` when present.

---

*Generated from codebase analysis. Last updated: 2026-01-29.*
