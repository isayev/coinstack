# Code review and functionality test report

**Date:** 2026-01-27  
**Scope:** LLM review queue (AI suggestions), approve/dismiss, and related frontend/API paths.

---

## 1. Code review summary

### 1.1 Backend – LLM review flow

**GET /api/v2/llm/review** (`llm.py` ~1286–1408)

- Uses raw SQL to select coins with `llm_suggested_references IS NOT NULL OR llm_suggested_rarity IS NOT NULL`, then loads each coin via `SqlAlchemyCoinRepository.get_by_id` for existing references.
- Builds `LLMSuggestionItem` with: coin context (issuer, denomination, mint, years, category, legends), `existing_references`, `suggested_references`, `validated_references` (from `_validate_catalog_reference`), `rarity_info`, `enriched_at`.
- Only includes rows that have at least one of `suggested_refs` or `rarity_info`.
- **Session handling:** Creates its own `SessionLocal()` and closes it in `finally`. Does not use FastAPI `Depends(get_db)`, so integration tests that override `get_db` do not affect this path; it always uses the app’s default DB.

**POST /api/v2/llm/review/{coin_id}/dismiss** (~1403–1443)

- Accepts `dismiss_references` and `dismiss_rarity` (default true). Builds `UPDATE coins_v2 SET ... WHERE id = :coin_id` and runs `db.commit()`.
- Uses its own `SessionLocal()`.
- Returns `{"status": "dismissed", "coin_id": …}`.

**POST /api/v2/llm/review/{coin_id}/approve** (~1446–1552)

- Loads coin with `selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type)`.
- Applies rarity from `llm_suggested_rarity` → `coin.rarity`, `coin.rarity_notes`, then clears it.
- Applies references from `llm_suggested_references` via `_parse_catalog_reference`, creates/finds `ReferenceTypeModel`, creates `CoinReferenceModel`, dedupes by `(system, local_ref)`.
- Commits and returns `{ status, coin_id, applied_rarity, applied_references }`.
- Uses its own `SessionLocal()`.

**Findings**

- Logic is consistent with the “suggest → review → approve/dismiss” design.
- Rarity and reference application and clearing of `llm_suggested_*` look correct.
- **Improvement:** Inject `get_db` (or a session factory) into these handlers so the same endpoints can be tested against an overridden DB in integration tests.

---

### 1.2 Frontend – AI review tab and hooks

**useAudit.ts**

- `useLLMSuggestions()` – `GET /api/v2/llm/review`, queryKey `["llm-suggestions"]`.
- `useDismissLLMSuggestion()` – `POST .../dismiss` with `dismiss_references`, `dismiss_rarity` from params; invalidates `["llm-suggestions"]` on success.
- `useApproveLLMSuggestion()` – `POST .../approve` with empty body; on success invalidates `["llm-suggestions"]`, `["coins", coinId]`, and `["coins"]`. Typing expects `{ status, coin_id, applied_rarity, applied_references }`.

**AIReviewTab.tsx**

- Uses `useLLMSuggestions`, `useDismissLLMSuggestion`, `useApproveLLMSuggestion`.
- Fetches coin previews with `api.get("/api/v2/coins", { params: { ids: coinIds.join(","), limit: 200 } })`. Backend list supports `ids` and returns those coins; `limit` is ignored when `ids` is set, so behavior is correct.
- Sort options: Coin ID, Suggestion count (references + rarity).
- Per-item: Approve → `handleApprove(coinId)` (toast with “Applied rarity and N reference(s)”); Reject → `handleDismiss(coinId)`.
- Bulk: “Approve all” / “Reject all” over selected ids. Toasts and undo stack used as designed.
- Empty state: `ReviewEmptyState variant="ai"` when `items.length === 0`.

**ReviewCenterPage**

- Renders `AIReviewTab` in the “AI Suggestions” tab; tab id `"ai"`. Counts and tab selection use `useReviewCountsRealtime` and `?tab=ai`.

**Findings**

- Hooks and UI match the backend contracts (dismiss params, approve response shape, invalidations).
- No obvious mismatches between frontend and backend for the current AI (rarity + references) flow.

---

### 1.3 API contracts

- **List coins:** `GET /api/v2/coins?ids=1,2,3` returns those coins; `limit` is not used when `ids` is present. AIReviewTab’s preview request is valid.
- **Review:** Response has `items: LLMSuggestionItem[]`, `total: number`; each item has `coin_id`, context fields, `suggested_references`, `rarity_info`, etc., matching `frontend/src/types/audit.ts` `LLMSuggestionItem` / `LLMReviewQueueResponse`.

---

## 2. Test results

### 2.1 Backend

**Relevant tests (enrichment + LLM + LLM review API):**

- `tests/integration/test_enrichment_api.py` – **10 passed**
- `tests/integration/test_llm_review_api.py` – **7 passed** (GET review empty/with data, POST dismiss, POST approve, 400/404 edge cases)
- `tests/unit/domain/test_llm_domain.py` – **27 passed**
- `tests/unit/infrastructure/services/test_llm_service.py` – **31 passed**

**Full test run:**

- **183 passed, 9 failed.** Failures are in:
  - `test_series_service.py` – `test_create_series` (expects `session.commit()`)
  - `test_vocab_sync.py` – `test_sync_issuers` (expects `session.commit()`)
  - `test_series_router.py` – 4 tests (all 404; router/path or app mount likely wrong in test)
  - `test_vocab_router.py` – 3 tests (all 404; same kind of routing/mount issue)

**Update:** Part B of the plan has been applied (series/vocab paths and flush assertions), so the full suite now has **199 passed**. Part A is done: `tests/integration/test_llm_review_api.py` covers `GET /api/v2/llm/review`, `POST .../dismiss`, and `POST .../approve`.

### 2.2 Frontend

- **TypeScript:** `npm run typecheck` — **passed** (no type errors).

---

## 3. Functionality assessment

- **Backend:** Review queue, dismiss, and approve are implemented and consistent with the design. Integration tests in `tests/integration/test_llm_review_api.py` cover GET review, POST dismiss, and POST approve against the test DB.
- **Frontend:** Types and API usage match the backend. Invalidations and toasts align with approve/dismiss behavior.
- **End-to-end:** Manual check is recommended: run backend and frontend, open Review Center → AI Suggestions, and confirm that when coins have `llm_suggested_references` or `llm_suggested_rarity`, they appear in the list, and that Approve updates the coin and removes the item while Dismiss clears suggestions and removes the item.

---

## 4. Recommendations

1. **Add integration tests for LLM review** — **DONE**  
   - Review/dismiss/approve handlers now use `Depends(get_db)` from `src.infrastructure.web.dependencies`; tests override `get_db` with the test DB.
   - **Tests:** `tests/integration/test_llm_review_api.py` — GET review (empty + with suggestions), POST dismiss (clears suggestions), POST approve (applies rarity/refs, clears suggestions), and edge cases (400 when nothing to dismiss, 400 when no suggestions, 404 for unknown coin).
   - **Plan used:** [docs/PLAN-LLM-TESTS-AND-FIX-SERIES-VOCAB.md](PLAN-LLM-TESTS-AND-FIX-SERIES-VOCAB.md) (Part A).
2. **Fix existing failing tests**  
   - Series and vocab router tests (404): align test client base URL or app mounts with the real app (e.g. ensure requests hit `/api/v2/...` as the app does).
   - Series/vocab service tests that expect `commit()`: align with the project rule (“repositories use flush(), never commit()”) and adjust tests or document where commit is required (e.g. at router level).
   - **Step-by-step plan:** [docs/PLAN-LLM-TESTS-AND-FIX-SERIES-VOCAB.md](PLAN-LLM-TESTS-AND-FIX-SERIES-VOCAB.md) (Part B).
3. **Optional:** Add a short E2E or manual test checklist for “AI Suggestions” in `docs/NUMISMATIC-EDGE-CASE-TEST-PLAN.md` or a dedicated QA doc (e.g. “With coins that have LLM suggestions, review queue shows them; Approve updates coin and removes item; Dismiss removes item and clears suggestions”).

---

## 5. Files reviewed

| Area | Files |
|------|--------|
| Backend LLM review | `backend/src/infrastructure/web/routers/llm.py` (get_llm_review_queue, dismiss_llm_suggestions, approve_llm_suggestions, _parse_catalog_reference, _validate_catalog_reference) |
| Frontend hooks | `frontend/src/hooks/useAudit.ts` (useLLMSuggestions, useDismissLLMSuggestion, useApproveLLMSuggestion) |
| Frontend UI | `frontend/src/components/review/AIReviewTab.tsx`, `frontend/src/pages/ReviewCenterPage.tsx` |
| Types | `frontend/src/types/audit.ts` (LLMSuggestionItem, LLMReviewQueueResponse) |
| Coins API | `backend/src/infrastructure/web/routers/v2.py` (get_coins with `ids`) |
| App routing | `frontend/src/App.tsx`, `backend/src/infrastructure/web/main.py` |
