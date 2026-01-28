# Enrichment Consolidation – Code Review and Attachment-Point Verification

**Date:** 2026-01-27  
**Scope:** All enrichment-related changes (Phases 1–6). Verification of every attachment point against the new API.

---

## 1. Attachment Points Checklist

### 1.1 Audit Enrichments (GET/POST /api/v2/audit/enrichments*)

| Attachment Point | Hook / Call | API Contract | Status |
|-----------------|-------------|--------------|--------|
| **EnrichmentsReviewTab** | `useEnrichments(filters)` | GET `/api/v2/audit/enrichments` with `status`, `trust_level`, `coin_id`, `auto_applicable`, `page`, `per_page` | ✅ Verified |
| **EnrichmentsReviewTab** | `useBulkApplyEnrichments()` → `mutateAsync(toApply)` | POST `/api/v2/audit/enrichments/bulk-apply` body `{ applications: [{ coin_id, field_name, value }] }`; hook accepts `Enrichment[]`, maps to `applications` | ✅ Verified |
| **EnrichmentsReviewTab** | `useAutoApplyAllEnrichments()` → `mutateAsync()` | POST `/api/v2/audit/enrichments/auto-apply-empty`; response `{ applied, applied_by_field? }` | ✅ Verified |
| **AuditPage** | Same three hooks, `handleBulkApplyEnrichments` passes `enrichmentsData.items.filter(e => selectedEnrichments.includes(e.id))` | Same as above | ✅ Verified |
| **EnrichmentCard** | `useApplyEnrichment()` → `mutateAsync({ coin_id, field_name, value: enrichment.suggested_value })` | POST `/api/v2/audit/enrichments/apply` body `{ coin_id, field_name, value }` | ✅ Verified |
| **useAudit.ts** | `useApplyEnrichment` invalidates `["enrichments"]`, `["audit-summary"]` onSuccess | N/A (client) | ✅ Verified |

**Backend:** `list_enrichments` returns `{ items, total, page, per_page, pages }`; each item has `id`, `coin_id`, `auction_data_id`, `field_name`, `suggested_value`, `source_house`, `trust_level`, `confidence`, `auto_applicable`, `status`, `applied`, `applied_at`, `rejection_reason`, `created_at`, `source_url`, `auction_images`. Frontend `Enrichment` and types match. Synthetic `id` is stable (hash of coin_id, auction_data_id, field_name).

### 1.2 Catalog Bulk Enrich (POST /api/catalog/bulk-enrich, GET /api/catalog/job/{id})

| Attachment Point | Hook / Call | API Contract | Status |
|-----------------|-------------|--------------|--------|
| **BulkEnrichPage** | `useBulkEnrich()` → `mutateAsync({ coin_ids, dry_run, max_coins } \| { ...filter, dry_run, max_coins })` | POST `/api/catalog/bulk-enrich`; request may include `coin_ids`, `missing_fields`, `reference_system`, `category`, `dry_run`, `max_coins` | ✅ Verified |
| **BulkEnrichPage** | `useJobStatus(jobResponse?.job_id, { refetchInterval })` | GET `/api/catalog/job/{job_id}`; response `JobStatus` with `job_id`, `status`, `progress`, `total`, `updated`, `conflicts`, `not_found`, `errors`, `results?`, `error_message?`, `started_at?`, `completed_at?` | ✅ Verified |
| **useCatalog.ts** | `bulkEnrich(request)`, `getJobStatus(jobId)` | Same as above | ✅ Verified |

**Backend:** Catalog router creates job with `total = len(coin_ids)` when `coin_ids` is non-empty, else `total = max_coins or 50`. `run_bulk_enrich` uses `request.coin_ids` when present. Frontend `BulkEnrichResponse` and `JobStatus` match backend models.

### 1.3 Import Enrich-Preview (POST /api/v2/import/enrich-preview)

| Attachment Point | Hook / Call | API Contract | Status |
|-----------------|-------------|--------------|--------|
| **EnrichmentPanel** | `useEnrichPreview()` → `enrich({ references, context })` | POST `/api/v2/import/enrich-preview` body `{ references: string[], context?: Record }` | ✅ Verified |
| **EnrichmentPanel** | Uses `data.suggestions`, `data.lookup_results` | Response `{ success, suggestions: Record<field, { value, source, confidence }>, lookup_results: Array<{ reference, status, system?, confidence?, error?, external_url? }> }` | ✅ Verified |

**Backend:** `enrich_preview` calls `CatalogRegistry.lookup` per reference; maps payload to `_payload_to_suggestions` keys (`issuing_authority`, `mint_name`, `mint_year_start`, `mint_year_end`, `denomination`, `obverse_legend`, `reverse_legend`, `obverse_description`, `reverse_description`). Each suggestion is `{ value, source, confidence }`. EnrichmentPanel uses `suggestion.value`, `suggestion.source`, `suggestion.confidence` and keys by field name — matches.

**Note:** `useEnrichPreview` uses `api` from `@/api/api`; other audit/catalog hooks use `api` from `@/lib/api`. Both target the same base URL; behavior is consistent.

### 1.4 Collection → Bulk Enrich (BulkActionsBar “Enrich”)

| Attachment Point | Flow | API / Route | Status |
|-----------------|------|--------------|--------|
| **CollectionPage** | Passes `onEnrich={(ids) => navigate(\`/bulk-enrich?coin_ids=${ids.join(",")}\`)}` to `BulkActionsBar` | No direct API; navigates to `/bulk-enrich?coin_ids=1,2,3` | ✅ Verified |
| **BulkActionsBar** | `handleEnrich` calls `onEnrich(getSelectedIds())` when `onEnrich` provided | Uses `useSelection().getSelectedIds()` | ✅ Verified |
| **BulkEnrichPage** | `useSearchParams()` → `coin_ids` from `?coin_ids=…`; “Selected coins (N)” preset sends `{ coin_ids, dry_run, max_coins }` to catalog bulk-enrich | POST `/api/catalog/bulk-enrich` with `coin_ids` | ✅ Verified |

---

## 2. Fixes Applied During Review

1. **BulkEnrichPage progress NaN:** When `jobStatus.total === 0`, `(progress / total) * 100` was NaN. Now: `progress = jobStatus && jobStatus.total > 0 ? Math.round((jobStatus.progress / jobStatus.total) * 100) : 0`.
2. **Catalog bulk-enrich total when `coin_ids` present:** Initial response used `request.max_coins or 50` even when `request.coin_ids` was set. Now: `total = len(request.coin_ids) if (request.coin_ids and len(request.coin_ids) > 0) else (request.max_coins or 50)` so the job total matches the number of selected coins when coming from the collection page.

---

## 3. API Shape Verification Summary

| Endpoint | Request | Response | Frontend consumer |
|----------|---------|----------|-------------------|
| GET `/api/v2/audit/enrichments` | Query: `status`, `trust_level`, `coin_id`, `auto_applicable`, `page`, `per_page` | `{ items: Enrichment[], total, page, per_page, pages }` | `useEnrichments` |
| POST `/api/v2/audit/enrichments/bulk-apply` | `{ applications: [{ coin_id, field_name, value }] }` | `{ applied: number }` | `useBulkApplyEnrichments` |
| POST `/api/v2/audit/enrichments/apply` | `{ coin_id, field_name, value }` | `{ status, field, new_value }` or 400 | `useApplyEnrichment` |
| POST `/api/v2/audit/enrichments/auto-apply-empty` | (none) | `{ applied, applied_by_field? }` | `useAutoApplyAllEnrichments` |
| POST `/api/catalog/bulk-enrich` | `{ coin_ids?, missing_fields?, reference_system?, category?, dry_run?, max_coins? }` | `{ job_id, total_coins, status, message? }` | `useBulkEnrich` |
| GET `/api/catalog/job/{job_id}` | Path | `JobStatus` | `useJobStatus` |
| POST `/api/v2/import/enrich-preview` | `{ references: string[], context? }` | `{ success, suggestions, lookup_results }` | `useEnrichPreview` |

All consumers send and parse the shapes above; no mismatches found.

---

## 3.1 Naming: “Catalog Enrich” vs “Audit apply” vs “LLM expand legend”

| Term | Meaning | Where |
|------|---------|--------|
| **Catalog Enrich** | Fill coin fields from OCRE/CRRO/RPC via `CatalogRegistry.lookup`. Bulk: `POST /api/catalog/bulk-enrich` + job polling. Per-reference during import: `POST /api/v2/import/enrich-preview`. | BulkEnrichPage, EnrichmentPanel (import) |
| **Audit apply** | Apply a suggested field value from auction/audit data to a coin. Uses `ApplyEnrichmentService`. List: `GET /api/v2/audit/enrichments`; apply: `POST /api/v2/audit/enrichments/apply` or bulk-apply / auto-apply-empty. | EnrichmentsReviewTab, AuditPage, EnrichmentCard |
| **LLM expand legend** | LLM-generated expansion of legend text (separate from catalog/audit). | LLM endpoints; not part of this consolidation |

---

## 4. Edge Cases and Behavior

- **Audit enrichments list:** Computed on the fly from coins with linked `auction_data`. No persistence of “applied” per opportunity; once a field is applied via apply/bulk-apply/auto-apply, the next list run may drop that row (coin field no longer empty). Filter `status=applied` correctly returns no rows for MVP.
- **Catalog bulk-enrich with `coin_ids`:** `run_bulk_enrich` uses `request.coin_ids` and loads those coins; job `total` is set from `len(coin_ids)` when provided and non-empty.
- **Import enrich-preview:** Empty `references` yields `suggestions={}`, `lookup_results=[]`. EnrichmentPanel hides when `references.length === 0`.
- **EnrichmentCard apply:** Sends `enrichment.coin_id`, `enrichment.field_name`, `enrichment.suggested_value`; backend uses `ApplyEnrichmentService`; invalidates enrichments and audit-summary on success.

---

## 5. Remaining Stubs (Out of Scope for Enrichment Consolidation)

- `useDiscrepancies`, `useAuditSummary`, `useAuditWithPolling`, `useBulkResolveDiscrepancies`, `useRejectEnrichment`: still stubs; left as-is per consolidation scope.
- `useApplyEnrichment` / `useRejectEnrichment`: Reject is stub; apply is real and wired to POST `/api/v2/audit/enrichments/apply`.

---

## 6. Files Touched in This Review

- `frontend/src/pages/BulkEnrichPage.tsx` — progress guard when `total === 0`.
- `backend/src/infrastructure/web/routers/catalog.py` — `total` from `coin_ids` when provided and non-empty.

---

## 7. Verification Commands

```bash
# Backend: ensure routers and enrichment services load
cd backend && uv run python -c "from src.infrastructure.web.routers import audit_v2, import_v2, catalog; print('OK')"

# Frontend: typecheck
cd frontend && npm run typecheck
```

All attachment points for enrichment have been traced to the new API and verified; the two fixes above are applied.
