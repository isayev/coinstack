# Catalog Parser Review and Edge Cases

> Review of rule-based catalog reference parsers (`backend/src/infrastructure/services/catalogs/parsers/`).  
> Central orchestration: `parser.py` (parse_catalog_reference, parse_catalog_reference_full).

## Supported Catalogs

| System   | Display | Parser   | Notes |
|----------|---------|----------|--------|
| ric      | RIC     | ric.py   | Volume Roman (I–X+); part Arabic or Roman (IV.1, V.II); optional mint; edition ²/³ |
| crawford | RRC     | crawford.py | Crawford/Cr/RRC; hyphen→slash, range→first variant |
| rpc      | RPC     | rpc.py   | Volume Roman, supplement S/S2/S3 |
| rsc      | RSC     | rsc.py   | Optional volume, warning when missing |
| doc      | DOC     | doc.py   | Volumes 1–5 (I–V) only |
| bmcrr    | BMCRR   | bmcrr.py | British Museum Roman Republic; BMCRR or BMC RR (before BMCRE) |
| bmcre    | BMCRE   | bmcre.py | British Museum Roman Empire; BMC alias |
| sng      | SNG     | sng.py   | Sylloge Nummorum Graecorum; SNG [collection] number (ParsedRef.collection) |
| cohen    | Cohen   | cohen.py | Roman Imperial (Cohen); optional volume I–VIII, variant letter |
| calico   | Calicó  | calico.py | Spanish catalog; Calicó/Cal. + number |
| sear     | Sear    | sear.py  | **Sear** or **SCV** only (no bare "S") |
| sydenham | Sydenham| sydenham.py | Sydenham/Syd./Syd |

## Refinements Applied

- **Sear**: Pattern changed from `(?:Sear|SCV|S)\s+(\d+)` to `(?:Sear|SCV)\s+(\d+)` so bare "S 123" is not parsed as Sear (avoids confusion with RPC supplement "S").
- **DOC**: Only volumes 1–5 (arabic or Roman I–V); DOC 6 / DOC VI return None from DOC parser.
- **Crawford**: Bare "335/1c" or "335-1c" (no prefix) parse as Crawford with appropriate warnings.

## Edge Cases Covered by Tests

- **Empty/whitespace**: Empty string and whitespace-only → null catalog.
- **RIC**: IV.1 / IV-1 / IV/1 → same canonical; V.II 325 (Roman part) → volume V.2 for canonical/OCRE; RIC I (2) 207 / RIC I(2) 207 (parenthesized edition) → volume I.2; edition ²/³ → volume .2/.3; unknown mint → title case.
- **Crawford**: Bare format warnings; no-subnumber (Cr 123); hyphen and range warnings.
- **RPC**: No-volume (RPC 5678) warning; supplement S/S2 precedence.
- **RSC**: With and without volume; warning when volume missing.
- **DOC**: Volume bounds 1–5; DOC 6, DOC VI, DOC IX → no match from DOC parser.
- **BMCRE**: BMC and BMCRE aliases.
- **Sear**: Sear 123 and SCV 123 only; "S 123" must not be Sear.
- **Sydenham**: Sydenham, Syd., Syd aliases.
- **Precedence**: RIC vs DOC by prefix; RPC I S 123 → supplement, not number; BMCRR before BMCRE.
- **SNG**: Collection in ref (e.g. SNG Cop 123, SNG ANS 336); canonical includes collection.
- **Cohen**: Optional volume (I–VIII); warning when no volume.
- **Calicó**: Calicó or Cal. alias; display name "Calicó".
- **Dict shape**: parse_catalog_reference returns 7 keys (catalog, volume, number, variant, mint, supplement, collection).
- **Canonical**: Includes mint, supplement, and collection when present.

## Test File

`backend/tests/unit/infrastructure/services/test_catalog_parser.py`:

- Happy-path and variant tests (parametrized).
- Per-catalog edge cases (DOC bounds, RSC volume, RPC no-volume, Crawford bare, Sear disambiguation).
- Canonical equivalence and dict shape tests.

## Design and Maintainability

- **Single parse path**: `parse_catalog_reference(raw)` delegates to `parse_catalog_reference_full(raw)` then `_parse_result_to_dict(result)`; no separate legacy path.
- **No heuristic fallback**: Unrecognized strings (e.g. "UnknownCatalog 99") return a 7-key dict with `catalog: None`, `number: None`; they are not interpreted as "first word = catalog, last = number". Sync and API treat them as unparsed; callers can show raw text or prompt for correction.
- **Canonical from one source**: `canonical(ref)` accepts either `ParsedRef` or the 7-key dict; used for `local_ref` and dedupe. Display names come from `catalog_systems.SYSTEM_TO_DISPLAY`.
- **Reference detection**: `_looks_like_reference(raw)` uses `catalog_systems.reference_detection_pattern()` (built from `REFERENCE_DETECTION_WORDS`); add display names and aliases there when adding catalogs.
- **ParseResult**: Core fields only (system, volume, number, subtype, mint, supplement, collection, raw, normalized, confidence, needs_llm, warnings). CRRO/OCRE derive main_number, sub_number, edition from number/volume.
- **OCRE query**: When volume has a dot (volume.part, e.g. V.2 from RIC V.II 325), OCRE `build_reconcile_query` sends it as-is ("RIC V.2 325"); edition (2)/(3) is only added for single-segment volume (e.g. "RIC II(2) 756"). When context has ruler/authority (e.g. Diocletian), the query omits edition so "RIC V Diocletian 325" matches (OCRE does not match "RIC V(2) Diocletian 325"). Quick Lookup (IdentityStep) passes issuer and mint as `coinContext` so RIC V 325 with Diocletian selected resolves to RIC V Diocletian 325. See `tests/unit/infrastructure/services/test_ocre.py`.
- **Shared helpers**: `parsers.base.make_simple_ref(system, number, variant)` for single-pattern catalogs; `crawford._crawford_ref(main_num, sub_num, variant, warnings)` for Crawford.

## Frontend Integration

- **Catalog systems**: `useCatalogSystems()` (GET /api/v2/catalog/systems) returns display names; `SUPPORTED_CATALOGS_FALLBACK` in `lib/referenceLinks.ts` used when API is unavailable (e.g. CoinPreviewEditor quick-add buttons).
- **Parse API**: `useParseCatalogReference().mutateAsync({ raw })` (POST /api/v2/catalog/parse) for authoritative parsing; use for validation or inline feedback.
- **Display**: `formatReference(ref)` in `lib/referenceLinks.ts` includes catalog, volume, supplement, mint, collection, number; used by ReferencesCard and external link search queries.
- **Client parse**: `parseReference(refString)` in `lib/referenceLinks.ts` is best-effort (RIC, RPC, RRC, SNG, DOC, generic); backend parse is source of truth for sync.
- **Audit**: `FieldComparators` uses `parseReference` and `formatReference` from referenceLinks for reference diffing.

## Adding or Changing Parsers

1. Add or edit parser in `parsers/<catalog>.py`; export `parse(raw) -> Optional[ParsedRef]`.
2. Register in `parsers/__init__.py` (`SYSTEM_PARSERS`) and `catalog_systems.py` (`SYSTEM_TO_DISPLAY`).
3. Add any detection prefix/alias for `_looks_like_reference()` in `parser.py` (see `REFERENCE_DETECTION_PATTERN` / catalog_systems).
4. Add unit tests (happy path + edge cases) in `test_catalog_parser.py`.
5. Update this doc and `07-API-REFERENCE.md` / `01-OVERVIEW.md` if supported catalogs or behavior change.
