# Plan to Fix All Issues

**Date**: 2026-01-28  
**Scope**: LLM review API/frontend mismatch, backend session handling, type/lint checks, tests, docs.

**Path A executed**: 2026-01-28 — Full LLM review restored (design/attribution in queue, dismiss_design/dismiss_attribution, approve endpoint, Depends(get_db)). All 17 integration tests pass.

---

## 1. Issue Summary

| # | Issue | Severity | Location |
|---|--------|----------|----------|
| I1 | Frontend calls `POST /api/v2/llm/review/{coin_id}/approve` but endpoint was removed | **High** – 404 on Approve | Backend `llm.py` |
| I2 | Frontend sends `dismiss_design`, `dismiss_attribution`; backend ignores them and never clears `llm_suggested_design` / `llm_suggested_attribution` | **High** – dismiss doesn’t clear design/attribution | Backend `llm.py` dismiss endpoint |
| I3 | Frontend expects `suggested_design`, `suggested_attribution` on queue items; backend omits them | **High** – design/attribution UI always empty, approve has nothing to apply | Backend `get_llm_review_queue` + `LLMSuggestionItem` |
| I4 | `get_llm_review_queue` and `dismiss_llm_suggestions` use `SessionLocal()` + manual `close()` instead of `Depends(get_db)` | **Medium** – session lifecycle, possible connection leaks | Backend `llm.py` |
| I5 | GET /review SQL does not include coins with only `llm_suggested_design` or `llm_suggested_attribution` | **Medium** – those coins never appear in queue | Backend `get_llm_review_queue` WHERE clause |
| I6 | Backend mypy fails: duplicate module `"enrichment"` (domain vs `src/infrastructure/cli/enrichment.py`) | **Low** – blocks `mypy src/` | Backend `pyproject.toml` / layout |
| I7 | Backend ruff check reports many violations | **Low** – pre-existing | Backend `src/` |
| I8 | Integration tests expect design/attribution in queue, dismiss_design/dismiss_attribution, and approve endpoint | **High** – tests fail on current backend | `backend/tests/integration/test_llm_review_api.py` |

---

## 2. Resolution Paths

Two consistent end states:

- **Path A – Restore full LLM review**: design + attribution in queue, dismiss_design/dismiss_attribution, and approve/apply. Matches current frontend and existing tests.
- **Path B – Align to simplified LLM review**: refs + rarity only; no design/attribution in queue, no approve. Frontend and tests are updated to match.

Recommendation: **Path A** – frontend and tests already implement the full flow; backend was simplified without a matching frontend change.

---

## 3. Path A – Restore Full LLM Review (Recommended)

### 3.1 Backend – Restore design/attribution in queue

**File**: `backend/src/infrastructure/web/routers/llm.py`

1. **Pydantic models**  
   - Re-add `LlmSuggestedDesign` and `LlmSuggestedAttribution` (or equivalent) with fields used by frontend.  
   - Add `suggested_design: Optional[LlmSuggestedDesign] = None` and `suggested_attribution: Optional[LlmSuggestedAttribution] = None` to `LLMSuggestionItem`.

2. **GET /review SQL and mapping**  
   - In the `SELECT`, add: `llm_suggested_design`, `llm_suggested_attribution`.  
   - In the `WHERE`, add:  
     `OR llm_suggested_design IS NOT NULL OR llm_suggested_attribution IS NOT NULL`.  
   - When building each item, parse `design_json` / `attribution_json` and set `suggested_design` / `suggested_attribution` on `LLMSuggestionItem` (same structure as frontend types).  
   - Include an item if it has suggested_refs, rarity_info, suggested_design, or suggested_attribution.

3. **Session handling**  
   - Switch back to `Depends(get_db)` for both `get_llm_review_queue` and `dismiss_llm_suggestions`.  
   - Remove local `SessionLocal()` and `try/finally`/`db.close()`.

### 3.2 Backend – Restore dismiss design/attribution

**File**: `backend/src/infrastructure/web/routers/llm.py`

- Add query params: `dismiss_design: bool = Query(True, ...)`, `dismiss_attribution: bool = Query(True, ...)`.
- In the update list:  
  - If `dismiss_design`: append `"llm_suggested_design = NULL"`.  
  - If `dismiss_attribution`: append `"llm_suggested_attribution = NULL"`.

### 3.3 Backend – Restore approve endpoint

**File**: `backend/src/infrastructure/web/routers/llm.py`

- Re-add `POST /review/{coin_id}/approve` that:
  1. Loads coin (with references) via repository/ORM.
  2. If no pending suggestions (refs/rarity/design/attribution), return 400.
  3. Applies `llm_suggested_rarity` → coin.rarity / rarity_notes; clear `llm_suggested_rarity`.
  4. Applies `llm_suggested_references` → create/link reference types and coin_references; clear `llm_suggested_references`.
  5. Applies `llm_suggested_design` → obverse_legend, reverse_legend, exergue, obverse/reverse_description, *_expanded; clear `llm_suggested_design`.
  6. Applies `llm_suggested_attribution` → issuer, mint, denomination, year_start, year_end; clear `llm_suggested_attribution`.
  7. Commits and returns `{ status, coin_id, applied_rarity, applied_references, applied_design, applied_attribution }`.

Use the implementation that existed on `main` (or equivalent logic) and ensure it uses the same request-scoped `db` from `Depends(get_db)`.

### 3.4 Frontend

- No API contract or feature changes needed for Path A; existing use of approve, dismiss_design/dismiss_attribution, and suggested_design/suggested_attribution is correct once backend is restored.

### 3.5 Tests

**File**: `backend/tests/integration/test_llm_review_api.py`

- Ensure tests that assert design/attribution in queue, dismiss_design/dismiss_attribution clearing those columns, and approve applying them are present and pass (they align with the restored backend).

### 3.6 Docs

- **docs/ai-guide/07-API-REFERENCE.md**: Document `GET /api/v2/llm/review`, `POST .../dismiss` (including `dismiss_design`, `dismiss_attribution`), and `POST .../approve`, plus response shape with `suggested_design` and `suggested_attribution`.
- **docs/AI-SUGGESTIONS-REVIEW-QUEUE-COMPATIBILITY.md**: Extend §3 to include design/attribution in the LLM queue and the approve endpoint.

---

## 4. Path B – Align to Simplified LLM Review (Refs + Rarity Only)

Use only if product decision is to drop design/attribution from the review queue and approve.

### 4.1 Backend

- Leave current implementation as-is (no design/attribution in queue, no dismiss_design/dismiss_attribution, no approve).
- Optionally keep `Depends(get_db)` and remove `SessionLocal()` in both handlers for consistency and session lifecycle (see §5.1).

### 4.2 Frontend

- **useAudit.ts**:  
  - Remove or no-op the approve mutation (or point it to a stub if you need the action to exist).  
  - For dismiss, stop sending `dismiss_design` and `dismiss_attribution`, or send them only for backward compatibility if backend adds optional params that are ignored.
- **AIReviewTab.tsx**:  
  - Remove use of `suggested_design` and `suggested_attribution` (sections that render design/attribution).  
  - Remove “Approve” action and bulk-approve, or replace with a message that approve is not available.
- **types/audit.ts**:  
  - Make `suggested_design` and `suggested_attribution` strictly optional and document that they are not returned by the current API (or remove if you strip UI entirely).

### 4.3 Tests

- Remove or adjust tests that expect design/attribution in the queue, dismiss_design/dismiss_attribution, and the approve endpoint so they match the simplified API.

### 4.4 Docs

- **docs/AI-SUGGESTIONS-REVIEW-QUEUE-COMPATIBILITY.md**: Already describes the simplified API; add a short note that design/attribution and approve are out of scope for the review queue.
- **docs/ai-guide/07-API-REFERENCE.md**: Describe only the endpoints that exist (no approve; dismiss only references/rarity).

---

## 5. Backend Quality (Apply for Either Path)

### 5.1 Session handling in LLM router

- **Change**: Use `db: Session = Depends(get_db)` in `get_llm_review_queue` and `dismiss_llm_suggestions` (and in `approve` if restoring it).  
- **Remove**: `SessionLocal()`, `try/finally`, and manual `db.close()`.  
- **Reason**: Request-scoped sessions and connection handling are managed by the FastAPI dependency; manual session creation can cause leaks or wrong transaction boundaries.

### 5.2 Mypy – duplicate module "enrichment"

- **Options** (choose one):  
  - **A)** In `pyproject.toml` under `[tool.mypy]`, set `exclude = ["src/infrastructure/cli/enrichment.py"]`.  
  - **B)** Rename `src/infrastructure/cli/enrichment.py` to something that doesn’t clash with `src/domain/enrichment.py` (e.g. `cli_enrich.py` or `enrich_cli.py`) and update any imports/scripts.  
  - **C)** Run mypy with explicit package bases, e.g. `mypy --explicit-package-bases -p src`, and fix any new errors reported (may be many).  
- **Recommendation**: A for a quick fix; B if you prefer a clean module layout.

### 5.3 Ruff

- Run `uv run ruff check src/` and fix or exempt reported rules file-by-file (e.g. add `# noqa` or adjust `[tool.ruff]` in `pyproject.toml`).  
- Prefer fixing obvious issues (unused imports, line length, etc.) before broad ignores.

---

## 6. Execution Order (Path A)

1. Backend: Restore Pydantic models and queue logic (§3.1), then dismiss params (§3.2), then approve endpoint (§3.3).  
2. Backend: Switch both GET /review and dismiss (and approve) to `Depends(get_db)` (§5.1).  
3. Run integration tests; fix any remaining assertions or wiring.  
4. Update 07-API-REFERENCE and AI-SUGGESTIONS-REVIEW-QUEUE-COMPATIBILITY (§3.6).  
5. Optionally: apply mypy exclude (§5.2) and start tackling ruff (§5.3).

---

## 7. Execution Order (Path B)

1. Frontend: Remove or adapt approve and design/attribution UI and params (§4.2).  
2. Tests: Adjust or remove design/attribution/approve tests (§4.3).  
3. Backend: Optionally switch to `Depends(get_db)` (§5.1).  
4. Docs: Clarify simplified scope (§4.4).  
5. Optionally: mypy (§5.2) and ruff (§5.3).

---

## 8. References

- Backend LLM router: `backend/src/infrastructure/web/routers/llm.py`
- Frontend: `useAudit.ts`, `AIReviewTab.tsx`, `frontend/src/types/audit.ts`
- Integration tests: `backend/tests/integration/test_llm_review_api.py`
- Docs: `docs/ai-guide/07-API-REFERENCE.md`, `docs/AI-SUGGESTIONS-REVIEW-QUEUE-COMPATIBILITY.md`
- DB: `coins_v2.llm_suggested_design`, `coins_v2.llm_suggested_attribution` (already added in schema fix)
