# Numismatic Catalog Reference and Parser – Deep Code Analysis

**Purpose**: Deep code analysis of catalog reference domain, all parser implementations (central rule-based, scraper extraction, frontend), persistence, and external catalog services.

**Consulted**: `docs/COIN-CATALOG-REFERENCES-ANALYSIS.md`, `docs/ai-guide/05-DATA-MODEL.md`, `backend/src/domain/coin.py`, `backend/src/infrastructure/services/catalogs/parser.py`, `backend/src/infrastructure/scrapers/shared/reference_patterns.py`, `backend/src/application/services/reference_sync.py`, `backend/src/infrastructure/repositories/coin_repository.py`, `backend/src/infrastructure/web/routers/llm.py`, `backend/src/infrastructure/services/catalogs/registry.py`, `frontend/src/lib/referenceLinks.ts`.

---

## 1. Domain and Types

### 1.1 Domain Entity: `CatalogReference` (backend)

**File**: `backend/src/domain/coin.py`

- **Type**: Immutable dataclass (value object).
- **Fields**:
  - `catalog: str` — Display name: "RIC", "RRC", "RPC", "Sear", "RSC", "BMC", "SNG".
  - `number: str` — Reference number, e.g. "756", "44/5", "1234a".
  - `volume: Optional[str]` — "II", "V.1", etc.
  - `suffix: Optional[str]` — Qualifiers (not persisted in V1 schema).
  - `raw_text: str` — Original text as found.
  - `is_primary: bool` — Primary reference for the coin.
  - `notes: Optional[str]` — Specimen-specific notes.
  - `source: Optional[str]` — "user" | "import" | "scraper" | "llm_approved" | "catalog_lookup".

**Repository contract** (`backend/src/domain/repositories.py`):

- `ICoinRepository.get_by_reference(catalog, number, volume=None) -> List[Coin]` — find coins by catalog reference.

### 1.2 Scraper Model: `CatalogReference` (scrapers)

**File**: `backend/src/infrastructure/scrapers/shared/models.py`

- **Type**: Pydantic `BaseModel` (scraper layer only).
- **Fields**: `catalog`, `volume`, `number`, `suffix`, `raw_text`, `needs_verification`.
- **Computed**: `normalized` (catalog + volume + number), `full_reference`.
- **Usage**: Auction scrapers (Heritage, CNG, Biddr, eBay, Agora) use this for extracted references; not the same type as domain `CatalogReference` but maps conceptually (catalog, number, volume, raw_text).

### 1.3 Frontend Types

- **`CatalogReference`** (`frontend/src/domain/schemas.ts`): Zod schema — catalog, number, volume, is_primary, notes, raw_text, source, etc.
- **`CatalogReference`** (`frontend/src/lib/referenceLinks.ts`): Interface for `buildExternalLinks` / `formatReference` — catalog, number, volume, raw_text, source.

---

## 2. Parser Implementations (Three Places)

### 2.1 Central Rule-Based Parser (Single Source of Truth for Persistence)

**File**: `backend/src/infrastructure/services/catalogs/parser.py`

**Entry point**: `parse_catalog_reference(raw: str) -> Dict[str, Optional[str]]`  
Returns `{"catalog": "RIC"|"RRC"|..., "volume": str|None, "number": str|None}`. Used by:

- LLM router `_parse_catalog_reference` (delegates to this).
- `ReferenceSyncService` when normalizing refs (string or dict → catalog, number, volume, raw_text).
- Bulk enrich (after lookup, for numismatic validation).
- Catalog services (OCRE/CRRO) via `ReferenceParser.parse()` for normalize/parse.

**Internal class**: `ReferenceParser`

- **Patterns** (`PATTERNS`): Regex per system:
  - **ric**: Roman volume (RIC I 207, RIC II³ 430), Arabic (RIC 1 207, RIC 2.3 430), hyphen (RIC II-123).
  - **crawford**: Standard (Crawford 335/1c, Cr. 335/1, RRC 335/1c), bare (335/1c), no subnumber (Cr 123).
  - **rpc**: Roman volume (RPC I 1234), Arabic (RPC 1 5678), no volume (RPC 5678 — lower confidence, needs_llm).
  - **rsc**: RSC 45, RSC II 123.
  - **bmcre**: BMCRE 123, BMC 456.
  - **sear**: Sear 1234, S 5678, SCV 123.
  - **sydenham**: Sydenham 123, Syd. 456.

- **Output**: `ParseResult` (Pydantic) — system, volume, number, subtype, edition/main_number/sub_number, normalized, confidence, needs_llm, llm_reason.
- **Display mapping**: `_SYSTEM_TO_CATALOG` maps internal `system` to API/ORM display: ric→RIC, crawford→RRC, rpc→RPC, rsc→RSC, bmcre→BMCRE, sear→Sear, sydenham→Sydenham.
- **Fallback**: If no pattern matches but `_looks_like_reference(raw)`, returns needs_llm=True; else returns catalog=None. If no system matched but raw has tokens, fallback in `parse_catalog_reference` uses first word as catalog, last as number.

**Convenience**: `parse_references(text)` — splits by `[;,\n]` and ` / `, returns `List[ParseResult]`.

### 2.2 Scraper Reference Extraction (Auction Text)

**File**: `backend/src/infrastructure/scrapers/shared/reference_patterns.py`

- **Purpose**: Extract references from free text (descriptions, titles); not used for DB write path normalization.
- **API**: `extract_references(text, needs_verification=False) -> List[CatalogReference]` (scraper `CatalogReference`), `extract_primary_reference(text)`, `normalize_reference(raw_ref)`, `is_valid_reference(text)`.
- **Patterns**: `REFERENCE_PATTERNS` — list of `(compiled_regex, catalog_name, has_volume)` with named groups `vol`, `num`, `suffix`. Covers: RIC, Crawford, RSC, RPC, Sear, BMC, Cohen, Sydenham, SNG, MIR, Calicó, BMCRR, CRR, DOC, SB, Babelon.
- **Difference from central parser**: More catalogs (SNG, MIR, DOC, SB, Babelon, etc.); different regex style (finditer, named groups); output is scraper `CatalogReference` with `normalized` as "Catalog Vol Number"; no single entry point for persistence — sync path uses central `parse_catalog_reference` when refs are passed as strings.

### 2.3 Frontend Parser (Display / Links)

**File**: `frontend/src/lib/referenceLinks.ts`

- **Function**: `parseReference(refString: string): CatalogReference | null` — best-effort parse for display/link building.
- **Patterns**: RIC (RIC + Roman + rest), Crawford/RRC (Crawford|RRC + rest), generic (word + rest).
- **Usage**: Building links when only a string is available; not used for form submit — form sends structured catalog/number/volume.

**Alignment**: Backend is authoritative for persistence and validation; frontend parser is for display only and may not match all backend patterns.

---

## 3. Persistence (ORM and Sync)

### 3.1 Schema

- **`reference_types`** (`ReferenceTypeModel`): id, system (ric, crawford, rpc, …), local_ref, local_ref_normalized, volume, number, external_id, external_url.
- **`coin_references`** (`CoinReferenceModel`): id, coin_id, reference_type_id, is_primary, plate_coin, position, variant_notes, page, plate, note_number, notes, **source** (user | import | scraper | llm_approved | catalog_lookup).

### 3.2 Single Write Path: ReferenceSyncService

**File**: `backend/src/application/services/reference_sync.py`

- **Entry**: `sync_coin_references(session, coin_id, refs, source, *, external_ids=None, merge=False)`.
- **Input**: `refs` = list of strings or dicts (catalog, number, volume, raw_text, is_primary, notes). Strings are normalized via `parse_catalog_reference(raw)`.
- **Logic**: Dedupe by (system, local_ref); find-or-create `ReferenceTypeModel` by (system, local_ref); create/update `CoinReferenceModel` links; optionally set external_id/external_url from `external_ids`; if not merge, remove links not in new set.
- **Catalog → system**: Display "RRC" → system "crawford"; otherwise catalog lowercased.

**Callers**:

- V2 create/update: `sync_coin_references(db, saved_coin.id, [r.model_dump() for r in request.references], "user")`.
- LLM approve: sync with source `"llm_approved"`, merge=True.
- Import commit: sync with source `"import"`, optional external_ids from CatalogRegistry.lookup.
- Bulk enrich: after successful lookup, sync with source `"catalog_lookup"`, merge=True, external_ids from result.

### 3.3 Repository Read/Write

**File**: `backend/src/infrastructure/repositories/coin_repository.py`

- **save()**: Does not write references; references are persisted only via ReferenceSyncService (called from V2 router after save).
- **get_by_id / get_all**: Eager load `references` and `reference_type`; `_reference_to_domain()` maps `ReferenceTypeModel` (system, volume, number, local_ref) + `CoinReferenceModel` (is_primary, notes, source) → domain `CatalogReference`. Suffix not stored in V1 (None).
- **get_by_reference(catalog, number, volume)**:
  - Raw SQL on `coin_references` JOIN `reference_types`; filter by UPPER(rt.system)=UPPER(:catalog), rt.number=:number, optional rt.volume=:volume; then loads coins by id.
  - **Issue**: `reference_types.system` is stored lowercase (ric, crawford, rpc). API accepts catalog "RIC", "Crawford", "RRC". UPPER(rt.system) gives "RIC", "CRAWFORD" — so catalog "RRC" never matches system "crawford". **Recommendation**: Normalize catalog to system before query (e.g. RRC/Crawford → crawford).
  - **Issue**: Returned coins are loaded with only `selectinload(CoinModel.images)`; references (and reference_type) are not eager-loaded, causing N+1 when serializing. **Recommendation**: Add `selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type)` for get_by_reference fetch.
  - **Bug**: Unreachable code after `return [self._to_domain(c) for c in orm_coins]` (if conditions / return query).

---

## 4. External Catalog Services

### 4.1 Registry

**File**: `backend/src/infrastructure/services/catalogs/registry.py`

- **get_service(system)**: ric → OCREService, crawford/rrc → CRROService, rpc → RPCService.
- **lookup(system, reference, context)**: Optional auto-detect via `detect_system(raw)` using central parser; cache (24h TTL); rate limit (30/min per system); then service.reconcile + optional fetch_type_data/parse_payload.
- **get_by_id(system, external_id)**: Fetch by external ID, cached and rate-limited.
- **detect_system(raw_reference)**: `parser.parse(raw_reference).system`.

### 4.2 Catalog Service Interface

**File**: `backend/src/infrastructure/services/catalogs/base.py`

- **CatalogService**: normalize_reference, parse_reference, build_reconcile_query, reconcile, fetch_type_data, parse_payload, build_url.
- **OCRE** (`ocre.py`): Uses central `parser.parse()` for normalize_reference and parse_reference; builds reconcile query (e.g. "RIC I(2) Augustus 207"); reconciles and fetches JSON-LD; parse_payload maps to CatalogPayload.
- **CRRO / RPC**: Same pattern (use parser where applicable, reconcile, fetch, parse_payload).

### 4.3 Numismatic Validation

**File**: `backend/src/application/services/catalog_validation.py`

- **validate_reference_for_coin(catalog, number, volume, coin_category, …)** → CatalogValidationResult(status, message).
- **Logic**: Map catalog to allowed categories (e.g. RIC → imperial/provincial/Byzantine; RRC/crawford → roman_republic). If coin category not in allowed, return warning. Used by LLM review and bulk enrich; result exposed as numismatic_warning.

---

## 5. Data Flow Summary

| Source of references       | Where stored / used              | How they get into DB                    |
|----------------------------|----------------------------------|-----------------------------------------|
| CreateCoinRequest.references | reference_types + coin_references | ReferenceSyncService after save, source "user" |
| UpdateCoinRequest.references | reference_types + coin_references | ReferenceSyncService after save, source "user" |
| LLM (identify, context)   | llm_suggested_references (JSON) | Written by context_generate / identify  |
| User approves suggestions | reference_types + coin_references | Approve endpoint → sync_coin_references, source "llm_approved", merge=True |
| Import commit             | reference_types + coin_references | sync_coin_references after create, source "import", optional external_ids |
| Bulk enrich (success lookup) | reference_types (external_id/url) + link | sync_coin_references(..., merge=True, external_ids=...) |
| Scrapers (auction text)   | AuctionLot / import preview      | extract_references(); import commit can pass ref strings into sync |
| GET by-reference          | N/A                              | Reads coin_references + reference_types |

---

## 6. Parser Alignment and Gaps

- **Central vs LLM**: LLM router uses central `parse_catalog_reference` only; no duplicate parsing logic in router.
- **Central vs Scraper**: Scraper extraction uses its own regex list (reference_patterns); when scraped refs are later synced (e.g. via import), they are passed as strings and normalized by central parser. So scraper output (catalog name, volume, number) can differ from central (e.g. "Crawford" vs "RRC"); sync normalizes by string and central parse.
- **Central vs Frontend**: Frontend `parseReference` is minimal; backend is source of truth for create/update and validation.
- **get_by_reference**: Catalog "RRC" vs system "crawford" not normalized; eager load missing; dead code after return.

---

## 7. File Reference (Quick)

| Layer / concern       | File(s) |
|-----------------------|--------|
| Domain entity         | `backend/src/domain/coin.py` (CatalogReference), `repositories.py` (get_by_reference) |
| Central parser        | `backend/src/infrastructure/services/catalogs/parser.py` (parse_catalog_reference, ReferenceParser, ParseResult) |
| Scraper extraction    | `backend/src/infrastructure/scrapers/shared/reference_patterns.py`, `shared/models.py` (scraper CatalogReference) |
| Sync                  | `backend/src/application/services/reference_sync.py` |
| ORM                   | `backend/src/infrastructure/persistence/orm.py` (ReferenceTypeModel, CoinReferenceModel) |
| Repository            | `backend/src/infrastructure/repositories/coin_repository.py` (_reference_to_domain, get_by_reference, save) |
| V2 API                | `backend/src/infrastructure/web/routers/v2.py` (CatalogReferenceInput/Response, create/update/by-reference) |
| LLM parse/validate    | `backend/src/infrastructure/web/routers/llm.py` (_parse_catalog_reference, _validate_catalog_reference) |
| Catalog registry      | `backend/src/infrastructure/services/catalogs/registry.py`, base.py, ocre.py, crro.py, rpc.py |
| Catalog validation    | `backend/src/application/services/catalog_validation.py` |
| Bulk enrich           | `backend/src/infrastructure/services/catalog_bulk_enrich.py` (_ref_string_from_coin, sync after lookup) |
| Import                | `backend/src/infrastructure/web/routers/import_v2.py` (enrich-preview, commit with sync_coin_references) |
| Frontend types/links  | `frontend/src/domain/schemas.ts`, `frontend/src/lib/referenceLinks.ts` (buildExternalLinks, formatReference, parseReference) |
| Tests                 | `backend/tests/unit/infrastructure/services/test_catalog_parser.py` |

---

*Deep analysis from codebase. Last updated: 2026-01-29.*
