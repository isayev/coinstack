# Enrichment Consolidation – Assessment of User Analysis

This document assesses the user’s analysis of the Enrichment Consolidation plan and adds refinements grounded in the current codebase.

---

## Summary Verdict

The analysis is **strong and implementable**. The decision table, phased migration, job execution strategy, ApplyEnrichmentService sketch, and “Option B first” recommendation are all sound. A few refinements are needed so the design matches the **domain shape** (frozen value objects, nested Attribution/Grading/Design) and the **existing frontend types** (useCatalog, BulkEnrichPage).

---

## 1. What’s Strong (Affirmed)

- **Problem diagnosis** — Correct that the four scattered “enrich” concepts and frontend calling non-existent backend are the core issues.
- **Clean Architecture** — Correct that a shared “apply field to coin” abstraction is the main unifying element; Option A and B both hinge on it.
- **DB approach** — Reusing existing tables and adding only `enrichment_jobs` (and optionally `enrichment_opportunities`) fits the current schema.
- **Option B for personal tool** — For a single-user collection tool, Option B is the right default: unblock quickly, refactor toward Option A later if the two subsystems feel redundant.

---

## 2. Decision Criteria (Accepted and Slightly Extended)

The proposed table is useful. One extra row:

| Factor | Favor Option A | Favor Option B |
|--------|----------------|----------------|
| Timeline | Can invest 2–3 weeks | Need working version in days |
| Future extensions | Adding more enrichment sources (LLM, external APIs) | Catalog + audit are the only two for now |
| Team familiarity | Comfortable with larger refactors | Prefer incremental changes |
| Current pain | Users confused by scattered UX | Backend 404s are the main blocker |
| **Backend surface** | Want one `/api/v2/enrichment/*` surface to document and secure | Okay with `/api/catalog/*` and `/api/v2/audit/*` living side by side |

Recommendation stands: **Option B**, with ApplyEnrichmentService introduced now so a later move to Option A is mostly routing and naming.

---

## 3. Background Job Execution (Accepted with One Clarification)

Using **FastAPI `BackgroundTasks`** for bulk-enrich is appropriate for a single-process, single-user app:

- No extra infra (Redis, Celery, etc.).
- Job state lives in `enrichment_jobs`; the handler updates `progress`, `status`, and result summary as it runs.
- Frontend already polls `GET /api/catalog/job/{id}` (see [useCatalog.ts](frontend/src/hooks/useCatalog.ts) `useJobStatus` with `refetchInterval`).

**Clarification:** The plan assumed “store progress in enrichment_jobs” but did not name the mechanism. Your choice of `BackgroundTasks.add_task(run_bulk_enrich, ...)` is the right level of detail. For true multi-worker or persistence across restarts, you’d add a task queue later; that’s out of scope for the current consolidation.

---

## 4. ApplyEnrichmentService (Refinement: Field → Domain Mapping)

The idea of a single service that applies “suggested value to coin field” is right. The important refinement is **how `field_name` maps onto the domain**.

In this codebase, `Coin` is a dataclass whose writable “fields” are often **nested value objects** ([domain/coin.py](backend/src/domain/coin.py)):

- `Attribution`: `issuer`, `mint`, `year_start`, `year_end`
- `GradingDetails`: `grade`, `service`, `certification_number`, …
- `Design`: `obverse_legend`, `reverse_legend`, `obverse_description`, `reverse_description`, …
- Top-level: `dimensions`, `attribution`, `grading`, `design`, `acquisition`, …

So `setattr(coin, "issuer", value)` cannot work: there is no top-level `issuer`. [audit_v2.apply_enrichment](backend/src/infrastructure/web/routers/audit_v2.py) already does the right kind of thing for `grade`:

- Build a new value object: `new_grading = GradingDetails(..., grade=val, ...)`  
- Rebuild the aggregate: `updated_coin = replace(coin, grading=new_grading)`  
- Persist: `repo.save(updated_coin)`

**Recommendation for ApplyEnrichmentService:**

- Keep the idea of `EnrichmentApplication(coin_id, field_name, new_value, source_type, source_id)` and `ApplicationResult(success, field_name, old_value, new_value, error)`.
- Add an explicit **field-name → domain mapping** instead of a single `setattr`:
  - `issuer` → replace `coin.attribution` with `Attribution(issuer=new_value, ...)`
  - `mint` → replace `coin.attribution` with `Attribution(..., mint=new_value, ...)`
  - `grade` → replace `coin.grading` with `GradingDetails(..., grade=new_value, ...)` (as in audit_v2)
  - `obverse_legend` / `reverse_legend` → replace `coin.design` with updated `Design(...)`
  - etc.
- Implement this either as a small **strategy map** (e.g. `FIELD_HANDLERS: dict[str, Callable[[Coin, Any], Coin]]`) or a dedicated helper that returns `(path, new_value_object)` so the service always does `replace(coin, **{path: new_value_object})`. That keeps the service as the single place that knows how to apply a field.

`ALLOWED_FIELDS` should list the **API-level** names (e.g. `issuer`, `mint`, `grade`, `obverse_legend`); the service then translates each to the correct domain update. This matches the existing audit_v2 pattern and keeps the door open for catalog payloads that use the same names.

---

## 5. Migration Path (Accepted and Tightened)

The phased sequence is right. One tightening:

- **Phase 1 (stubs):**  
  Stub responses should **match the existing frontend types** so that when Phase 2 lands, no frontend changes are needed. Concretely:
  - `POST /api/catalog/bulk-enrich` → return `{ job_id, total_coins, status, message }` consistent with [BulkEnrichResponse](frontend/src/hooks/useCatalog.ts) (e.g. `status: "pending"`, `total_coins: 0` or from request).
  - `GET /api/catalog/job/{id}` → return an object that matches [JobStatus](frontend/src/hooks/useCatalog.ts): `job_id`, `status` (`"queued"` | `"running"` | `"completed"` | `"failed"`), `progress`, `total`, `updated`, `conflicts`, `not_found`, `errors`, `results`, `error_message`, `started_at`, `completed_at`. Stub can use `status: "completed"`, `progress: total`, and zeroed counts.

That way Phase 2 only swaps stub logic for real logic behind the same contracts.

---

## 6. API Contract Specifics (Align with Existing Frontend)

Your proposed TypeScript types are in the right direction; the main point is to **reuse and document the existing frontend expectations** so backend and frontend stay aligned.

**Catalog bulk and job status**

[BulkEnrichPage](frontend/src/pages/BulkEnrichPage.tsx) and [useCatalog](frontend/src/hooks/useCatalog.ts) already assume:

- **BulkEnrichResponse:** `job_id: string`, `total_coins: number`, `status: string`, `message: string | null`
- **JobStatus:** `job_id`, `status` (`"queued"` | `"running"` | `"completed"` | `"failed"`), `progress`, `total`, `updated`, `conflicts`, `not_found`, `errors`, `results: Array<{ coin_id, status }> | null`, `error_message`, `started_at`, `completed_at`

So the backend should implement **these** shapes (or a small, backward-compatible extension). Your `JobStatusResponse` used `processed` and `results.fills_applied` / `conflicts_found`; the live UI uses `progress`, `updated`, `conflicts`, `not_found`, `errors`. Mapping from internal counters to these names (e.g. `updated` ← fills applied, `conflicts` ← conflicts found) in the backend keeps the frontend unchanged.

**Audit enrichments list**

For `GET /api/v2/audit/enrichments`, your `EnrichmentOpportunity` and `EnrichmentsListResponse` are a good target. The frontend today uses [Enrichment](frontend/src/types/audit.ts) (e.g. `id`, `coin_id`, `auction_data_id`, `field_name`, `suggested_value`, `source_house`, `trust_level`, `confidence`, `auto_applicable`, `status`, …). So either:

- The new endpoint returns items that match that `Enrichment` shape (with optional extra fields like `source_label`), or  
- The response type is updated once and used everywhere.  

Recommendation: define the **backend** response (and any new DTOs) to match the existing `Enrichment` + pagination shape where possible, and add fields only where Phase 3/4 need them.

---

## 7. Error Handling (Accepted)

Your table (timeout → skip/report, invalid value → skip/log, coin deleted → skip, DB lost → fail job, partial → commit success and report) is appropriate. No change needed. Optional additions:

- **Catalog lookup timeout:** Use a single configurable timeout (e.g. 10–15 s) and one retry before marking that coin as lookup_failed.
- **Invalid field value:** Validation can come from the domain (e.g. enums, value-object constructors) or from catalog payload coercion; the service should catch and return `ApplicationResult(success=False, error=...)` so callers can aggregate into job stats.

---

## 8. Testing Strategy (Accepted and Extended)

Your scenarios are the right ones. Two additions:

- **ApplyEnrichmentService**
  - Rejects disallowed `field_name` with a clear error (and no DB change).
  - For an allowed field, when the domain rejects the value (e.g. invalid enum or constraint), the service returns failure and does not call `repo.save`.
- **Bulk-enrich job**
  - At least one test that runs a small bulk job and asserts transition `queued` → `running` → `completed` and that `progress`/`total`/`updated` (and optionally `conflicts`/`errors`) match expectations.

That keeps the shared “apply” logic and the job state machine under test.

---

## 9. Implementation Recommendation (Endorsed)

Your “Option B, structured for future Option A migration” is endorsed:

1. **Implement ApplyEnrichmentService now** with an explicit field → domain mapping (Section 4).
2. **Add endpoints incrementally** in existing routers (catalog, audit_v2, import_v2).
3. **Use a single `enrichment_jobs` table** for any async catalog work.
4. **Skip `enrichment_opportunities` initially** and compute audit “enrichments” from `coins_v2` + `auction_data`.
5. **Revisit unification** once both catalog bulk and audit enrichments work and UX is stable.

---

## 10. Immediate First PR (Refined)

Your first-PR list is right; one refinement:

1. **Add `enrichment_jobs` model** to [orm.py](backend/src/infrastructure/persistence/orm.py) (and migration or create-if-missing logic as per project practice).
2. **Add ApplyEnrichmentService** (or equivalent) with **field_name → domain mapping** for at least `grade`, `issuer`, `mint`, and one of `obverse_legend` / `reverse_legend`, so audit_v2 and future catalog apply can share it.
3. **Implement `POST /api/catalog/bulk-enrich`** (real implementation): resolve coin set from request (filters or `coin_ids`), create row in `enrichment_jobs`, kick off `BackgroundTasks.add_task(run_bulk_enrich, ...)`.
4. **Implement `GET /api/catalog/job/{id}`** to read from `enrichment_jobs` and return a payload that matches [JobStatus](frontend/src/hooks/useCatalog.ts).
5. **Refactor** [audit_v2.apply_enrichment](backend/src/infrastructure/web/routers/audit_v2.py) to call ApplyEnrichmentService instead of inlined “grade” logic, so all “apply field to coin” flows go through one place.

After that, BulkEnrichPage works end-to-end for catalog bulk, and the apply path is unified and ready for Phase 4 (bulk-apply, import enrich-preview, etc.).

---

## 11. Gaps the Analysis Did Not Change

These remain as in the original plan:

- **Import enrich-preview:** Backend still needs `POST /api/v2/import/enrich-preview` (or equivalent) and a contract that matches [useEnrichPreview](frontend/src/hooks/useImport.ts) and [EnrichmentPanel](frontend/src/components/import/EnrichmentPanel.tsx).
- **BulkActionsBar “Enrich”:** Collection page still needs to pass `onEnrich` (e.g. navigate to `/bulk-enrich` with selected ids, or call catalog bulk-enrich with those ids).
- **Naming and docs:** Sidebar/UX and [ENRICHMENT-EXPLORATION-REPORT](docs/ENRICHMENT-EXPLORATION-REPORT.md) / [07-API-REFERENCE](docs/ai-guide/07-API-REFERENCE.md) should clearly separate “Catalog Enrich” vs “Audit apply” vs “LLM expand legend” so the consolidated behavior is easy to reason about.

---

## 12. Conclusion

Your analysis correctly prioritizes Option B, a phased migration, and a shared ApplyEnrichmentService. The main adjustments are:

1. **ApplyEnrichmentService** must use an explicit **field_name → domain mapping** (replace value objects, use `dataclasses.replace`), not a single `setattr` on the root Coin.
2. **Phase 1 stubs** and **Phase 2+ real implementations** should conform to **existing** [BulkEnrichResponse](frontend/src/hooks/useCatalog.ts) and [JobStatus](frontend/src/hooks/useCatalog.ts) so the current BulkEnrichPage and useCatalog stay valid.
3. **First PR** should include refactoring audit_v2’s apply logic into ApplyEnrichmentService so “apply field to coin” is unified from the start.

With those in place, the rest of your migration path, error-handling table, and test ideas are ready to implement as specified.

---

## Implemented (Enrichment Consolidation Plan)

Option B was implemented per the step-by-step plan. Current behavior:

- **Catalog bulk-enrich:** `POST /api/catalog/bulk-enrich`, `GET /api/catalog/job/{job_id}` — real CatalogRegistry lookups, `enrichment_jobs` table, BackgroundTasks.
- **Audit enrichments:** `GET /api/v2/audit/enrichments` (computed from coins + auction_data), `POST /api/v2/audit/enrichments/bulk-apply`, `POST /api/v2/audit/enrichments/apply`, `POST /api/v2/audit/enrichments/auto-apply-empty`.
- **ApplyEnrichmentService:** Single place for “apply field to coin”; used by audit apply and catalog bulk.
- **Import enrich-preview:** `POST /api/v2/import/enrich-preview` — real CatalogRegistry lookup per reference; returns `suggestions` and `lookup_results` for EnrichmentPanel.
- **BulkActionsBar:** Collection page passes `onEnrich={(ids) => navigate(\`/bulk-enrich?coin_ids=${ids.join(",")}\`)}`; BulkEnrichPage reads `coin_ids` from URL and offers “Selected coins (N)” preset.

**API and data model:** See [07-API-REFERENCE](ai-guide/07-API-REFERENCE.md) (Audit Enrichments, Catalog API, Import API) and [05-DATA-MODEL](ai-guide/05-DATA-MODEL.md) (`enrichment_jobs`).
