# Code Review: Parser Catalog Expansion Phase 1

**Scope**: Phase 1 changes (ParseResult extension, _parse_result_to_dict, single-parse refactor, reference_sync, catalog_v2 response, tests).

---

## 1. Summary

The refactor correctly implements a single parse path, extends ParseResult with mint/supplement/collection, and uses _parse_result_to_dict in reference_sync. No critical bugs found. A few minor consistency issues and one latent bug for Phase 2 are noted below.

---

## 2. Correctness

### 2.1 Single parse path

- **reference_sync** (string branch): Calls only `parse_catalog_reference_full(ref.strip())`, then `_parse_result_to_dict(full)`. No double parse. Correct.
- **parse_catalog_reference**: Calls `parse_catalog_reference_full` then `_parse_result_to_dict`. One parse. Correct.
- **LLM router / bulk enrich**: Still call `parse_catalog_reference`; they get the same dict shape (with optional extra keys). `.get("catalog")`, `.get("number")`, `.get("volume")` unchanged. Correct.

### 2.2 Data flow

- **ParseResult**: mint, supplement, collection are set in `_parsed_ref_to_result` from ParsedRef. Parsers (ric, rpc, etc.) currently do not set them; they remain None until Phase 2. Correct.
- **_parse_result_to_dict**: Builds number as `(result.number or "") + (result.subtype or "")`, so variant is included in number for display/storage. Also returns variant=result.subtype. Sync and canonical use this dict; canonical(parsed) for dict uses volume, mint, collection, number (variant is inside number). Correct.
- **reference_sync** (string): Uses parsed.get("variant"), parsed.get("mint"), etc. All keys are present in the dict returned by _parse_result_to_dict. Correct.
- **catalog_v2**: Builds number with subtype concatenated and passes variant=result.subtype, mint=result.mint, etc. CatalogReferenceResponse receives them. Correct.

### 2.3 Edge cases

- **Empty string**: `parse_catalog_reference("")` returns early with `{"catalog": None, "volume": None, "number": None}`. reference_sync string path: `full` is ParseResult for empty; _parse_result_to_dict returns all Nones; local_ref = ref.strip() = ""; we store catalog "Unknown", number "". Acceptable (same as before).
- **Parse failure (unknown string)**: _parse_result_to_dict returns catalog=None, number=None. reference_sync uses local_ref = ref.strip() and catalog "Unknown", number "". So we can still create reference_types with system="unknown". This is pre-existing; LLM approve does not filter by parse success. Optional improvement: filter in sync or at LLM approve for refs with confidence below threshold.
- **Successful parse with number empty**: If a parser ever returned number="", we’d get number.strip() or None = None, so d.get("number") is None and we’d fall through to fallback. Unlikely in current parsers. Acceptable.
- **raw not a string**: parse_catalog_reference(None) would do str(None).strip() = "None" and parse the literal "None". Callers (LLM, bulk enrich) pass strings. No change from before; could add an explicit None check if desired.

---

## 3. Inconsistencies and Desired Behavior

### 3.1 Return shape of parse_catalog_reference (minor)

- **Issue**: Empty input returns 3 keys: `{"catalog": None, "volume": None, "number": None}`. Successful parse and fallback return 7 keys (catalog, volume, number, variant, mint, supplement, collection). So the return shape is inconsistent.
- **Impact**: Low. All current callers use .get("catalog"), .get("number"), .get("volume") only; .get("variant") etc. would yield None for the 3-key return.
- **Recommendation**: For consistency, return the same 7 keys for the empty case, e.g. add variant, mint, supplement, collection: None to the early return and to the final `return {"catalog": None, "volume": None, "number": None}`.

### 3.2 canonical() does not include supplement (latent bug for Phase 2)

- **Issue**: In parser.py, canonical() builds parts from (display, volume, mint, collection, number) for both ParsedRef and dict. It does **not** include supplement. So "RPC I 123" and "RPC I S 123" (when RPC supplement is added in Phase 2) would get the same canonical string and the same local_ref, and would incorrectly dedupe to one reference_types row.
- **Impact**: None with current parsers (supplement is always None). When Phase 2 adds RPC supplement parsing, dedupe would be wrong without a fix.
- **Recommendation**: In Phase 2, add supplement to canonical(): for ParsedRef include ref.supplement in parts (e.g. after volume); for dict include d.get("supplement"). Order and position should match the plan (e.g. display + volume + supplement + mint + collection + number).

---

## 4. Sync and Filtering

- **V2 create/update**: Filter refs before sync (valid_refs with non-empty catalog and number). Correct.
- **LLM approve**: Passes list of strings; only filters empty strings. Does not filter by parse success, so unparseable strings can still create reference_types with system="unknown". Pre-existing; optional improvement is to skip refs where _parse_result_to_dict yields catalog None or confidence below threshold (would require passing confidence from normalize into sync or filtering in the approve handler).

---

## 5. Tests

- **test_parse_catalog_reference_full_returns_subtype**: Asserts subtype for "RIC IV.1 351b". Correct.
- **test_parse_catalog_reference_matches_parse_result_to_dict**: Asserts parse_catalog_reference(raw) matches _parse_result_to_dict(parse_catalog_reference_full(raw)) for catalog, volume, number. Uses "RIC II 756" (successful parse). Correct; would fail for unknown refs because parse_catalog_reference uses fallback and _parse_result_to_dict returns Nones, which is expected.
- Existing tests (parse_ric, canonical equivalence, dict shape, etc.) still pass; behavior for existing call paths is preserved.

---

## 6. Recommendations Summary

| Priority | Item | Action | Status |
|----------|------|--------|--------|
| Low | Consistent return shape for parse_catalog_reference | Add variant, mint, supplement, collection to the two returns that currently have only catalog, volume, number (empty and final fallback). | **Fixed**: Both empty and final fallback now return 7 keys. |
| Phase 2 | canonical() and supplement | Include supplement in canonical() (ParsedRef and dict branches) so "RPC I S 123" and "RPC I 123" get distinct local_ref when Phase 2 adds RPC supplement. | **Fixed**: canonical() now includes supplement in parts (after volume, before mint/collection/number). |
| Optional | LLM approve / sync | Consider filtering out refs that fail to parse (catalog None) or have confidence below threshold before calling sync_coin_references. | Deferred. |

---

## 7. No Issues Found

- No recursion (parse_catalog_reference -> parse_catalog_reference_full -> parser.parse; no cycle).
- reference_sync dict path unchanged; string path correctly uses full and _parse_result_to_dict.
- catalog_to_system("Unknown") and empty catalog/number handling unchanged.
- CatalogReferenceResponse and v2 API already support variant, mint, supplement, collection; catalog_v2 now populates them from ParseResult.

---

*Review date: 2026-01-29. Scope: Phase 1 parser expansion and single-parse refactor.*

---

## 8. Fixes applied (before Phase 2)

- **Consistent return shape**: `parse_catalog_reference` now returns 7 keys (catalog, volume, number, variant, mint, supplement, collection) in all paths: empty input, successful parse, fallback with parts, and final fallback.
- **canonical() and supplement**: `canonical()` now includes supplement in the parts list for both ParsedRef and dict branches (order: display, volume, supplement, mint, collection, number), so "RPC I S 123" and "RPC I 123" produce distinct local_ref when Phase 2 adds RPC supplement.
- **Test**: `test_canonical_includes_supplement` added to assert distinct canonical strings for refs with and without supplement.
