# Bulk Enrichment – Logs and Queue

## Where “the queue” and results live

- **Queue** = the bulk enrichment **job** created by `POST /api/catalog/bulk-enrich`. There is no separate “enrichment queue” list; each run creates one job with a `job_id`.
- **Results** = job status and outcome, returned by **`GET /api/catalog/job/{job_id}`** and shown on the **Bulk Enrich** page (`/bulk-enrich`) while you stay on that page and it polls.

So “I don’t see any results in the queue” usually means either:
1. The job never progressed (stayed `queued` or disappeared), or  
2. You navigated away before the job finished, and the UI no longer shows that job (it doesn’t list past jobs).

## Where to check logs

- **Backend** logs go to **stdout/stderr** when you run the server (e.g. `uv run run_server.py`). There is no log file unless you redirect output or add your own file handler.
- Useful lines:
  - `Bulk enrich job <job_id> queued (total=N)` – job was created and committed before the background task started.
  - `Bulk enrich job <job_id> starting` – background task found the job and began work.
  - `Bulk enrich job <job_id> completed: updated=... conflicts=... not_found=... errors=...` – task finished and wrote results into `enrichment_jobs`.
  - `Enrichment job <job_id> not found in DB` – background task ran but could not see the job (bug that’s now addressed by committing the job before enqueueing the task).

## Why jobs sometimes showed no results (fixed)

The background task runs in a **new DB session**. The job row was created in the request session and only committed when the request’s dependency teardown ran. Depending on ordering, the task could run **before** that commit, so `session.get(EnrichmentJobModel, job_id)` returned `None`, the task logged “Enrichment job … not found” and exited without updating the job. The job then stayed `queued` with no progress/results.

**Fix:** In `POST /api/catalog/bulk-enrich`, the job is **committed** (`db.commit()`) **before** `background_tasks.add_task(run_bulk_enrich, ...)` is called. The task’s new session can then see the job and run to completion.

## How to confirm it works

1. Start a bulk enrichment run from the Bulk Enrich page (choose a filter, optionally turn off dry run, start).
2. **Stay on the same page** so it keeps polling `GET /api/catalog/job/{job_id}`.
3. In the terminal where the backend is running, you should see:
   - `Bulk enrich job … queued (total=…)`
   - `Bulk enrich job … starting`
   - `Bulk enrich job … completed: updated=… conflicts=… not_found=… errors=…`
4. On the Bulk Enrich page, progress and “updated / conflicts / not_found / errors” (and any `results` in the job status) should update and then show the final counts when the job completes.

## If the table is missing

The `enrichment_jobs` table is created by `Base.metadata.create_all(...)` in `init_db()` when the app starts, **if** `EnrichmentJobModel` is imported (it is, via `orm` in `database.py`). If you added the model after the DB was first created and don’t run migrations that create this table, it may be missing. In that case, create it explicitly:

```bash
# From repo root
sqlite3 backend/coinstack_v2.db < backend/scripts/create_enrichment_jobs_table.sql
```

Or run: `backend/scripts/run_create_enrichment_jobs.py`.

## References

- Backend: `backend/src/infrastructure/web/routers/catalog.py` (bulk-enrich, job status), `backend/src/infrastructure/services/catalog_bulk_enrich.py` (background task).
- Frontend: `frontend/src/pages/BulkEnrichPage.tsx`, `frontend/src/hooks/useCatalog.ts` (`useBulkEnrich`, `useJobStatus`).
- Table: `enrichment_jobs` in `backend/src/infrastructure/persistence/orm.py` (`EnrichmentJobModel`).
