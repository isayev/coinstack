# Plan: (a) LLM Review Integration Tests + (b) Fix Series/Vocab Test Failures

Step-by-step plan for both workstreams.

---

## Part A – Add integration tests for LLM review endpoints

### Goal

Add tests that hit `GET /api/v2/llm/review`, `POST /api/v2/llm/review/{coin_id}/approve`, and `POST /api/v2/llm/review/{coin_id}/dismiss`, using the same test DB setup as `test_enrichment_api.py` (overridden `get_db`).

### A.1 – Refactor LLM router to use `Depends(get_db)` for review/dismiss/approve

**Why:** Today the three handlers create `SessionLocal()` inside the handler. Tests that override `get_db` do not affect them, so we cannot run review/approve/dismiss against the test DB.

**What:** Use FastAPI’s `Depends(get_db)` (or a session factory dependency) in the review, dismiss, and approve handlers so the test app can inject the test session.

**Files:**

- `backend/src/infrastructure/web/routers/llm.py`

**Steps:**

1. **Add get_db to LLM router**  
   The router already defines a local `get_db()` (~line 617) that returns `next(_get_db())`. Reuse that, or import `get_db` from `src.infrastructure.web.dependencies` so the same dependency is used app-wide.

2. **`get_llm_review_queue`**  
   - Signature: add `db: Session = Depends(get_db)`.
   - Remove `db = SessionLocal()` at the start.
   - Remove `db.close()` in `finally` (caller/yield manages lifecycle when using `get_db`).  
   - If the dependency yields and the caller manages the session, do **not** call `db.close()` inside the handler; the dependency’s `finally` will close it.

3. **`dismiss_llm_suggestions`**  
   - Add `db: Session = Depends(get_db)`.
   - Replace `db = SessionLocal()` with the injected `db`.
   - Remove the `finally: db.close()` (session is managed by the dependency).
   - Keep `db.commit()` in the success path; keep `db.rollback()` in the `except` path.

4. **`approve_llm_suggestions`**  
   - Add `db: Session = Depends(get_db)`.
   - Replace `db = SessionLocal()` with the injected `db`.
   - Remove the `finally: db.close()`.
   - Keep `db.commit()` / `db.rollback()` as today.

**Import:** Ensure `get_db` is the one from `src.infrastructure.web.dependencies` so `app.dependency_overrides[get_db] = ...` in tests applies to these handlers. If the LLM router currently uses a local `get_db`, switch it to `from src.infrastructure.web.dependencies import get_db` (and remove the local definition if it is only used by these three handlers).

**Deliverable:** Review, dismiss, and approve use an injected `Session`; integration tests can override `get_db` and run against the test DB.

---

### A.2 – Add integration test module (or extend existing)

**Options:**

- **New file:** `backend/tests/integration/test_llm_review_api.py`
- **Or extend:** `backend/tests/integration/test_enrichment_api.py` with a new section “LLM review API”.

**Recommended:** New file `test_llm_review_api.py` so LLM review tests are easy to find and run alone.

**Fixtures:** Reuse the same pattern as `test_enrichment_api.py`:

- `app(db_session)` – `create_app()` with `app.dependency_overrides[get_db] = lambda: (yield db_session)` (or the same override used there).
- `client(app)` – `TestClient(app)`.

**Dependency:** Tests need a `db_session` that backs the same in-memory DB. Reuse `conftest.py`’s `db_session` and ensure the override passes that session when the LLM handlers call `Depends(get_db)`.

---

### A.3 – Test: GET /api/v2/llm/review (empty and with data)

**Test 1 – empty**

- Request: `GET /api/v2/llm/review`.
- Assert: `200`, body `{ "items": [], "total": 0 }`.

**Test 2 – with suggestions**

- In the same test (or a fixture), insert a row into the test DB’s `coins_v2` (or equivalent table name in the test schema) with:
  - `id = 1`
  - `llm_suggested_references = '["RIC II 123"]'` (or valid JSON array)
  - `llm_suggested_rarity = NULL` (or a valid JSON object)
  - Other required columns set to satisfy NOT NULL / FK if any.
- Request: `GET /api/v2/llm/review`.
- Assert: `200`, `total >= 1`, at least one item has `coin_id == 1`, `suggested_references` contains `"RIC II 123"`.

**Table/ORM:** Use the same ORM/table names as the rest of the app (e.g. `coins_v2`). If the test DB is created from `Base.metadata.create_all`, use the ORM model to insert, e.g. `CoinModel(...)` and `db_session.add(coin); db_session.flush()` so the row is visible in the same transaction.

**Deliverable:** Two tests (or one parameterized) that assert empty and non-empty behaviour of GET review.

---

### A.4 – Test: POST /api/v2/llm/review/{coin_id}/dismiss

- Insert a coin with `id = 2`, `llm_suggested_references = '["RSC 456"]'`, `llm_suggested_rarity = '{"rarity_code":"R1"}'` (and other required fields).
- Request: `POST /api/v2/llm/review/2/dismiss?dismiss_references=true&dismiss_rarity=true`.
- Assert: `200`, body `{ "status": "dismissed", "coin_id": 2 }`.
- Assert: In DB, coin 2 has `llm_suggested_references IS NULL` and `llm_suggested_rarity IS NULL` (read via same session or new query in the test).

**Deliverable:** One test that dismisses both refs and rarity and checks DB state.

---

### A.5 – Test: POST /api/v2/llm/review/{coin_id}/approve

- Insert coin `id = 3` with `llm_suggested_rarity = '{"rarity_code":"S","rarity_description":"Scarce","source":"RIC"}'` and `llm_suggested_references = '["RIC II 789"]'`. Ensure the coin has no existing `coin_references` row for that ref (or the test asserts the new ref is added).
- Request: `POST /api/v2/llm/review/3/approve`.
- Assert: `200`, body has `applied_rarity: true`, `applied_references: 1` (or the appropriate counts).
- Assert: Coin 3’s `rarity` and `rarity_notes` are updated; a new `reference_types` + `coin_references` row exists for `"RIC II 789"`; `llm_suggested_rarity` and `llm_suggested_references` on coin 3 are cleared.

**Deliverable:** One test that approves rarity + refs and checks both application and clearing of suggestion fields.

---

### A.6 – Edge cases (optional)

- Approve with `coin_id` that does not exist → `404`.
- Approve with coin that has no suggestions → `400` and “No pending suggestions”.
- Dismiss with `dismiss_references=false`, `dismiss_rarity=false` → `400` “Nothing to dismiss”.

**Deliverable:** Optional tests; at least one 404 and one 400 case improves coverage.

---

### A.7 – Docs

- In `docs/ai-guide/07-API-REFERENCE.md` or `docs/CODE-REVIEW-AND-TEST-REPORT.md`: note that LLM review/approve/dismiss are covered by integration tests in `tests/integration/test_llm_review_api.py`.
- In `docs/CODE-REVIEW-AND-TEST-REPORT.md`: update “Recommendations” to mark “Add integration tests for LLM review” as done (or in progress), and point to this plan.

---

## Part B – Fix the 9 failing series/vocab tests

### B.1 – Series router tests (4 failures) – wrong paths

**Failure:** All four tests get `404`. Tests call `/api/series`, `/api/series/1/slots`, `/api/series/1/coins/1`, but the series router has `prefix="/api/v2/series"`. So the correct paths are under `/api/v2/series`.

**File:** `backend/tests/unit/infrastructure/web/routers/test_series_router.py`

**Changes:**

| Test | Current request | Correct request |
|------|------------------|------------------|
| test_create_series | `POST "/api/series"` | `POST "/api/v2/series"` |
| test_add_slot | `POST "/api/series/1/slots"` | `POST "/api/v2/series/1/slots"` |
| test_add_coin_to_series | `POST "/api/series/1/coins/1"` | `POST "/api/v2/series/1/coins/1"` |
| test_remove_coin_from_series | `DELETE "/api/series/1/coins/1"` | `DELETE "/api/v2/series/1/coins/1"` |

**Steps:** Replace the request paths in each test with the values in the “Correct request” column. No change to mocks or app setup.

**Deliverable:** All four series router tests use `/api/v2/series/...` and pass.

---

### B.2 – Vocab router tests (3 failures) – wrong router/paths

**Failure:** All three get `404`. The test app does `app.include_router(vocab.router)` (V3 router with prefix `/api/v2/vocab`). The tests call:

- `GET "/api/vocab/issuers"`
- `POST "/api/vocab/normalize/issuer"` (with params)
- `POST "/api/vocab/sync/nomisma/issuers"`

Those paths belong to the **legacy** router (`vocab.legacy_router`, prefix `/api/vocab`). The test app never includes the legacy router, so those URLs are not mounted.

**File:** `backend/tests/unit/infrastructure/web/routers/test_vocab_router.py`

**Fix:** Include the legacy router so those routes exist, and keep the same request paths so the tests still target the legacy endpoints.

**Steps:**

1. Import the legacy router:  
   `from src.infrastructure.web.routers.vocab import router, legacy_router`
2. Include both:  
   - `app.include_router(router)`  
   - `app.include_router(legacy_router)`  
   (Or use the same variable names as in the router module; the goal is that `/api/vocab/issuers`, `/api/vocab/normalize/issuer`, `/api/vocab/sync/nomisma/issuers` are defined.)
3. Keep the same `get_db` override so both routers use the mock session.
4. Leave the request URLs as they are: `/api/vocab/issuers`, `/api/vocab/normalize/issuer`, `/api/vocab/sync/nomisma/issuers`.

**Deliverable:** All three vocab router tests hit the legacy routes and pass (assuming mocks remain valid for those handlers).

---

### B.3 – Series service test (1 failure) – wrong assertion

**Failure:** `test_create_series` expects `mock_session.commit.assert_called()`, but `SeriesService.create_series` uses `self.session.flush()` and `self.session.refresh()`, and does **not** call `commit()`. Per project rules, the service/repository layer uses `flush()`, and the HTTP layer (or `get_db`) commits.

**File:** `backend/tests/unit/infrastructure/services/test_series_service.py`

**Change:** Replace the commit assertion with a flush assertion.

**Steps:**

1. In `test_create_series`, change  
   `mock_session.commit.assert_called()`  
   to  
   `mock_session.flush.assert_called()`  
   (and keep `mock_session.add.assert_called()` if present).
2. Optionally add `mock_session.refresh.assert_called()` if the test should assert that refresh is used.
3. Do **not** add `commit()` to `SeriesService`; the test should reflect current (and desired) behaviour.

**Deliverable:** `test_create_series` passes and asserts `flush` (and optionally `refresh`) instead of `commit`.

---

### B.4 – Vocab sync test (1 failure) – wrong assertion

**Failure:** `test_sync_issuers` expects `mock_session.commit.assert_called()`. `VocabSyncService._sync_sparql` uses `self.session.flush()` and explicitly does not commit (see comment “Do NOT commit here – transaction is managed by get_db() dependency”).

**File:** `backend/tests/unit/infrastructure/services/test_vocab_sync.py`

**Change:** Assert flush instead of commit.

**Steps:**

1. In `test_sync_issuers`, change  
   `mock_session.commit.assert_called()`  
   to  
   `mock_session.flush.assert_called()`.
2. Do **not** change `VocabSyncService` to call `commit()`.

**Deliverable:** `test_sync_issuers` passes and asserts `flush` instead of `commit`.

---

## Implementation order

| Order | Part | Task | Dependencies |
|-------|------|------|----------------|
| 1 | B | B.1 Series router paths | None |
| 2 | B | B.2 Vocab router – include legacy_router | None |
| 3 | B | B.3 Series service – assert flush | None |
| 4 | B | B.4 Vocab sync – assert flush | None |
| 5 | A | A.1 LLM router use Depends(get_db) | None |
| 6 | A | A.2 New test file + fixtures | A.1, conftest |
| 7 | A | A.3 GET review tests | A.1, A.2 |
| 8 | A | A.4 Dismiss test | A.1, A.2 |
| 9 | A | A.5 Approve test | A.1, A.2 |
| 10 | A | A.6 Edge-case tests (optional) | A.3–A.5 |
| 11 | A | A.7 Update docs | A.3–A.6 |

Part B can be done first (all four edits are small and independent). Part A.1 is the only change to production code; A.2–A.7 are test and doc updates.

---

## File checklist

| Part | File | Action |
|------|------|--------|
| A.1 | `backend/src/infrastructure/web/routers/llm.py` | Use Depends(get_db) in review, dismiss, approve; use shared get_db from dependencies |
| A.2–A.6 | `backend/tests/integration/test_llm_review_api.py` | **New**: fixtures, GET empty/non-empty, dismiss, approve, optional edge cases |
| A.7 | `docs/CODE-REVIEW-AND-TEST-REPORT.md` | Note LLM review integration tests and this plan |
| B.1 | `backend/tests/unit/infrastructure/web/routers/test_series_router.py` | Change request paths to `/api/v2/series/...` |
| B.2 | `backend/tests/unit/infrastructure/web/routers/test_vocab_router.py` | Include legacy_router, keep `/api/vocab/...` paths |
| B.3 | `backend/tests/unit/infrastructure/services/test_series_service.py` | Assert flush (and optionally refresh) instead of commit |
| B.4 | `backend/tests/unit/infrastructure/services/test_vocab_sync.py` | Assert flush instead of commit |

---

## Verification

After both parts:

- `uv run pytest tests/unit/infrastructure/web/routers/test_series_router.py tests/unit/infrastructure/web/routers/test_vocab_router.py tests/unit/infrastructure/services/test_series_service.py tests/unit/infrastructure/services/test_vocab_sync.py -v` → all pass.
- `uv run pytest tests/integration/test_llm_review_api.py -v` → all pass.
- `uv run pytest tests -v` → 9 previously failing tests pass; new LLM review tests pass; no regressions.
