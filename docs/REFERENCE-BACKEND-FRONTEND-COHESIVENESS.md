# Catalog Reference – Backend/Frontend Cohesiveness and Trace Report

**Purpose**: Trace reference code paths, document fixes applied, and compare backend vs frontend for consistency.

**Related**: [COIN-CATALOG-REFERENCES-ANALYSIS.md](COIN-CATALOG-REFERENCES-ANALYSIS.md), [NUMISMATIC-CATALOG-REFERENCE-PARSER-ANALYSIS.md](NUMISMATIC-CATALOG-REFERENCE-PARSER-ANALYSIS.md).

---

## 1. Bugs Fixed (2026-01-29)

### 1.1 Repository: `get_by_reference`

- **Catalog vs system**: API accepts `catalog` as "RIC", "Crawford", "RRC"; DB stores `reference_types.system` as "ric", "crawford", "rpc". Query used `UPPER(rt.system)=UPPER(:catalog)`, so `catalog=RRC` never matched `system=crawford`.
  - **Fix**: Added `_catalog_to_system(catalog)` (RRC/Crawford → crawford, else lowercased). Query now uses `rt.system = :system` with normalized system.
- **N+1 on returned coins**: Coins were loaded with only `selectinload(CoinModel.images)`; references and reference_type were lazy-loaded when serializing.
  - **Fix**: Eager-load `selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type)` and `selectinload(CoinModel.provenance_events)` when fetching by reference.
- **Dead code**: Unreachable block after `return [self._to_domain(c) for c in orm_coins]` (if conditions / return query).
  - **Fix**: Removed the dead block.

### 1.2 API response: display catalog

- **Inconsistency**: `_reference_to_domain` returned `catalog=ref_type.system.upper()` (e.g. "CRAWFORD"); API/parser use display name "RRC" for Roman Republican.
  - **Fix**: Parser exports `SYSTEM_TO_DISPLAY_CATALOG`; repository uses it in `_reference_to_domain` so response catalog is "RRC", "RIC", "RPC", etc., matching parser and frontend expectations.

### 1.3 V2 create/update: empty references

- **Issue**: Submitting refs with empty catalog/number created reference_types with system "unknown" and number "".
  - **Fix**: Before calling `sync_coin_references`, filter to refs where both `catalog.strip()` and `number.strip()` are non-empty (create and update).

---

## 2. Code Path Trace

### 2.1 Write path (references into DB)

| Entry | Flow | Sync call |
|-------|------|-----------|
| POST /api/v2/coins | CreateCoinRequest.references → sync_coin_references(coin_id, valid_refs, "user") | After repo.save; valid_refs = refs with catalog and number non-empty |
| PUT /api/v2/coins/{id} | UpdateCoinRequest.references → sync_coin_references(coin_id, valid_refs, "user") | After repo.save; same filter |
| POST /api/v2/llm/review/{id}/approve | llm_suggested_references (JSON list of strings) → sync_coin_references(coin_id, ref_strings, "llm_approved", merge=True) | Refs as strings; central parser used inside sync |
| Import confirm | ref_strings from payload → CatalogRegistry.lookup per ref → sync_coin_references(coin_id, ref_strings, "import", external_ids=...) | Optional external_ids from lookup |
| Bulk enrich | _ref_string_from_coin(coin) → lookup → sync_coin_references(coin_id, [ref_str], "catalog_lookup", merge=True, external_ids=...) | After successful lookup |

### 2.2 Read path (references from DB)

| Entry | Flow |
|-------|------|
| GET /api/v2/coins, GET /api/v2/coins/{id} | repo.get_all / get_by_id → selectinload(references).selectinload(reference_type) → _reference_to_domain → catalog_display from SYSTEM_TO_DISPLAY_CATALOG |
| GET /api/v2/coins/by-reference?catalog=...&number=...&volume=... | repo.get_by_reference(catalog, number, volume) → _catalog_to_system(catalog) → SQL on coin_references + reference_types → eager-load refs → _to_domain |

### 2.3 Frontend

| Usage | Source |
|-------|--------|
| Coin form (create/edit) | ReferenceListEditor: catalog, volume, number, notes. mapCoinToPayload sends catalog, number, volume, is_primary, notes, raw_text. |
| By-reference search | client.getCoinsByReference(catalog, number, volume) → GET /api/v2/coins/by-reference. Used by useSmartIngest (e.g. after scrape to find similar coins). |
| Display | ReferencesCard uses buildExternalLinks(references), formatReference(ref). referenceLinks expects catalog, number, volume; OCRE/CRRO/RPC links built from primary ref. |

---

## 3. Backend vs Frontend Cohesiveness

### 3.1 Aligned

- **Catalog display names**: Backend now returns "RRC", "RIC", "RPC" (via SYSTEM_TO_DISPLAY_CATALOG). Frontend referenceLinks and form use same names (RIC, RRC, RPC).
- **By-reference search**: Backend accepts catalog=RIC|Crawford|RRC|RPC and normalizes to system; frontend sends catalog/number/volume; response coins include full references (eager-loaded).
- **Create/update payload**: CatalogReferenceInput has catalog, number, volume, suffix, is_primary, notes, raw_text. Frontend CatalogReferenceSchema and mapCoinToPayload include catalog, number, volume, notes, raw_text. Volume is now editable in ReferenceListEditor.
- **Filtering empty refs**: Backend ignores refs with empty catalog or number on create/update; frontend can still submit blank rows but they are not persisted.

### 3.2 Optional improvements

- **Frontend validation**: Consider validating in the form that at least one of catalog or number is set before submit (or disable submit for empty rows) to avoid sending useless refs.
- **referenceLinks.parseReference**: Frontend has a minimal parser for display; backend is source of truth. No change required.
- **ReferenceListEditor**: Volume field added; placeholders updated for RIC/RPC/RRC (e.g. "756", "44/5").

### 3.3 Schema summary

| Field | Backend (CatalogReferenceInput / Response) | Frontend (CatalogReferenceSchema / mapCoinToPayload) |
|-------|-------------------------------------------|------------------------------------------------------|
| catalog | required | required |
| number | required | required |
| volume | optional | optional (now in form) |
| suffix | optional | not in form |
| is_primary | default False | sent |
| notes | optional | sent |
| raw_text | optional | sent when present |
| source | response only | in schema (read-only) |

---

## 4. Files Touched (Fixes)

| File | Change |
|------|--------|
| backend/src/infrastructure/repositories/coin_repository.py | get_by_reference: _catalog_to_system, eager-load refs/provenance, remove dead code. _reference_to_domain: use SYSTEM_TO_DISPLAY_CATALOG. Import SYSTEM_TO_DISPLAY_CATALOG. |
| backend/src/infrastructure/services/catalogs/parser.py | Export SYSTEM_TO_DISPLAY_CATALOG; keep _SYSTEM_TO_CATALOG as alias. |
| backend/src/infrastructure/web/routers/v2.py | Create/update: filter request.references to valid_refs (catalog and number non-empty) before sync_coin_references. |
| frontend/src/components/coins/CoinForm/ReferenceListEditor.tsx | Add volume field; addReference includes volume: null; layout: Catalog, Vol, Number, Notes. |

---

*Trace and cohesiveness report. Last updated: 2026-01-29.*
