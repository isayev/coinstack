# Enrichment Functionality – Frontend Exploration & Code Analysis

This report documents where enrichment is used in the frontend, how it is invoked, and how it is implemented (including backend API alignment). It serves as a reference for “specialized” follow-up work (e.g. wiring bulk enrich, implementing catalog enrich/job endpoints, or unifying audit vs catalog enrichment).

---

## 1. Where Enrichment Is Used (Usage Map)

### 1.1 Navigation & Entry Points

| Entry point | Route / Target | Component / File |
|-------------|----------------|-------------------|
| **Sidebar** | `/bulk-enrich` | `Sidebar.tsx` – nav item "Enrich" (Sparkles icon) |
| **Command palette** | `⌘K` → "Bulk Normalize" | `CommandPalette.tsx` – id `bulk-enrich`, path `/bulk-enrich` |
| **Command bar (header)** | Add Coin dropdown | `CommandBar/index.tsx` – "Bulk Normalize" → `navigate("/bulk-enrich")` |
| **Collection dashboard** | Sidebar dashboard | `CollectionDashboard/index.tsx` – "AI Enrich" button → `handleEnrichAll()` → `navigate('/bulk-enrich')` |
| **Collection health widget** | Same dashboard | `CollectionHealthWidget.tsx` – `onEnrichAll` → "AI Enrich" button |

So “Bulk Enrich” / “AI Enrich” in the UI generally leads to the **Bulk Enrich** page (`/bulk-enrich`).

### 1.2 Pages That Own or Embed Enrichment UI

| Page | File | Role |
|------|------|------|
| **Bulk Enrich** | `pages/BulkEnrichPage.tsx` | Standalone page: filter presets, dry-run, start job, poll status, show progress/results. Uses **catalog** bulk-enrich API (`useCatalog`). |
| **Coin detail** | `pages/CoinDetailPage.tsx` | “Enrich legend” per obverse/reverse: **LLM legend expansion** (`useExpandLegendV2`), not catalog enrichment. |
| **Review Center** | `pages/ReviewCenterPage.tsx` | Tab "Enrichments" renders `EnrichmentsReviewTab`; uses **audit** enrichments (list, bulk apply, apply all). |
| **Audit** | `pages/AuditPage.tsx` | Tab "Enrichments" with filters, selection, bulk apply, apply all; uses same **audit** enrichment hooks. |
| **Import** | `pages/ImportPage.tsx` | `EnrichmentPanel` in import flow: **catalog-style** lookup for references on **preview** data before coin is created. |

### 1.3 Components That Expose or Use Enrichment

| Component | File | What it does |
|-----------|------|---------------|
| **BulkActionsBar** | `features/collection/BulkActionsBar.tsx` | When coins are selected: "Enrich" calls `onEnrich(ids)` if provided; otherwise shows toast `Enriching N coins...` and does **not** call any API. |
| **EnrichmentsReviewTab** | `components/review/EnrichmentsReviewTab.tsx` | Lists “enrichment opportunities”, Run Enrichments, Apply All, filters, selection, bulk apply. Data from `useEnrichments` (audit). |
| **EnrichmentCard** | `components/audit/EnrichmentCard.tsx` | Shows one enrichment (field, source, trust, etc.), Apply/Reject. Uses `useApplyEnrichment`, `useRejectEnrichment` (audit stubs). |
| **EnrichmentPanel** (import) | `components/import/EnrichmentPanel.tsx` | “Catalog Enrichment”: detected references, “Enrich from Catalog”, then apply selected fields to preview. Uses `useEnrichPreview()` → `POST /api/v2/import/enrich-preview`. |
| **AuditPanel** | `features/audit/AuditPanel.tsx` | Per-coin audit: discrepancy list and “apply” per discrepancy. Calls `client.applyEnrichment(coinId, field, value)` → `POST /api/v2/audit/{id}/apply`. |
| **CoinDetail / ObverseReversePanel / CoinSidePanel** | `features/collection/CoinDetail/*` | Props `onEnrichLegend`, `isEnrichingObverse/Reverse`; sparkles button “Enrich legend” → **LLM** expand abbreviation (`useExpandLegendV2`), not catalog. |
| **CollectionHealthWidget** | `components/dashboard/CollectionHealthWidget.tsx` | Renders “AI Enrich” when `onEnrichAll` is passed (e.g. from `CollectionDashboard` → `/bulk-enrich`). |

### 1.4 Quick Reference: “Enrich” Actions by Concept

- **Catalog bulk enrich (OCRE/CRRO)**  
  - **Where:** Bulk Enrich page, entered via Sidebar / Command Palette / Command Bar / Dashboard “AI Enrich”.  
  - **Implementation:** `BulkEnrichPage` + `useBulkEnrich` / `useJobStatus` from `useCatalog.ts` → `POST /api/catalog/bulk-enrich`, `GET /api/catalog/job/{id}`.  
  - **Backend:** Catalog router only has `POST /api/catalog/lookup`. **No** `/api/catalog/enrich/{id}`, `/api/catalog/bulk-enrich`, or `/api/catalog/job/{id}` in current backend.

- **Catalog single-coin enrich**  
  - **Where:** `useEnrichCoin()` in `useCatalog.ts` exists but is **not** used by any visible UI in the codebase.  
  - **Implementation:** Would call `POST /api/catalog/enrich/{coinId}`.  
  - **Backend:** Not implemented.

- **“Enrich legend” on coin detail**  
  - **Where:** Coin detail page, obverse/reverse legend area (“Enrich” / Sparkles).  
  - **Implementation:** `handleEnrichLegend` → `useExpandLegendV2()` → `POST /api/v2/llm/legend/expand`.  
  - **Backend:** LLM router; this is **LLM legend expansion**, not catalog enrichment.

- **Audit “apply enrichment” (accept suggested value)**  
  - **Where:** `AuditPanel` (per-coin audit), and conceptually “Enrichments” in Review Center / Audit page.  
  - **Implementation:** `client.applyEnrichment(coinId, field, value)` → `POST /api/v2/audit/{coin_id}/apply`.  
  - **Backend:** Implemented in `audit_v2.py`; applies one field/value to the coin.

- **Review “enrichments” list / bulk apply**  
  - **Where:** `EnrichmentsReviewTab`, `AuditPage` “Enrichments” tab.  
  - **Implementation:** `useEnrichments`, `useBulkApplyEnrichments`, `useAutoApplyAllEnrichments`, `useApplyEnrichment`, `useRejectEnrichment` from `useAudit.ts`.  
  - **Backend:** All of these are **stubs** in the frontend (return empty data or no-op). No `/api/v2/audit/enrichments`, `.../apply`, `.../reject` etc. in backend.

- **Import “Enrich from Catalog”**  
  - **Where:** Import flow, `EnrichmentPanel`, when references are detected.  
  - **Implementation:** `useEnrichPreview()` → `POST /api/v2/import/enrich-preview`.  
  - **Backend:** `import_v2` has no `enrich-preview` route. Only in v1 archive.

- **Bulk selection “Enrich” in collection**  
  - **Where:** `BulkActionsBar` when coins are selected on collection view.  
  - **Implementation:** Only runs if parent passes `onEnrich`. `CollectionPage` (and any grid/table page using it) passes **no** `onEnrich`, so it only shows a toast and does **not** call any enrich API.

---

## 2. How It Is Currently Implemented

### 2.1 Catalog Enrichment (OCRE/CRRO, Bulk Enrich Page)

**Frontend**

- **Hooks:** `useCatalog.ts`  
  - `useBulkEnrich()` – `mutationFn: bulkEnrich`  
  - `useJobStatus(jobId, { refetchInterval })` – polls job status  
  - `useEnrichCoin()` – present but **unused** in UI
- **API calls:**
  - `POST /api/catalog/bulk-enrich` – body: `{ coin_ids?, missing_fields?, reference_system?, category?, dry_run?, max_coins? }`
  - `GET /api/catalog/job/{jobId}`
  - (Unused) `POST /api/catalog/enrich/{coinId}` – body: `{ dry_run, apply_conflicts }`
- **Flow:** User picks a filter preset (e.g. “RIC without OCRE link”, “Missing legends”) and options (e.g. dry run), clicks “Start Enrichment”. Frontend calls bulk-enrich, gets `job_id`, then polls job status and shows progress (updated/conflicts/not_found/errors) and recent results.

**Backend**

- **Catalog router** (`backend/src/infrastructure/web/routers/catalog.py`):  
  - Only implements `POST /api/catalog/lookup`.  
  - **No** `POST /api/catalog/enrich/{id}`, `POST /api/catalog/bulk-enrich`, or `GET /api/catalog/job/{id}`.
- So the Bulk Enrich page’s **catalog** calls have no corresponding backend today and will 404 or fail when used.

### 2.2 Audit “Apply Enrichment” (Accept Discrepancy Value)

**Frontend**

- **Client:** `api/client.ts`  
  - `applyEnrichment(id, field, value)` → `POST /api/v2/audit/{id}/apply` with `{ field, value }`.
- **Usage:** `AuditPanel` uses a mutation that calls `client.applyEnrichment(coinId, field, value)` when the user accepts a discrepancy.

**Backend**

- **Audit router** (`backend/src/infrastructure/web/routers/audit_v2.py`):  
  - `POST /{coin_id}/apply` with `ApplyEnrichmentRequest(field, value)`.  
  - Updates the coin (e.g. grade) via repository and returns `{ status, field, new_value }`.  
- This is the only “apply enrichment” flow that is **fully wired** frontend → backend.

### 2.3 Review Center / Audit Page “Enrichments” (List + Bulk Apply)

**Frontend**

- **Hooks:** `useAudit.ts`  
  - `useEnrichments(filters)` – **stub**: returns `{ items: [], total: 0, pages: 1, page: 1 }`, no HTTP call.  
  - `useBulkApplyEnrichments()` – **stub**: mutation no-op, invalidates `["enrichments"]`, `["audit-summary"]`.  
  - `useAutoApplyAllEnrichments()` – **stub**: mutation no-op, same invalidations.  
  - `useApplyEnrichment()` – **stub**: mutation no-op for `{ id }`.  
  - `useRejectEnrichment()` – **stub**: mutation no-op for `{ id }`.
- **UI:**  
  - `EnrichmentsReviewTab` and `AuditPage` “Enrichments” tab use these hooks, so they always see an empty list and “apply” does not persist.  
  - `EnrichmentCard` uses `useApplyEnrichment` / `useRejectEnrichment`; in real use they would need to call an API that applies by enrichment **id** (or by coin+field+value).

**Backend**

- No `/api/v2/audit/enrichments`, `.../enrichments/apply`, `.../enrichments/auto-apply`, or `.../enrichments/{id}/apply` or `.../reject` in `audit_v2.py`. So the “Enrichments” review/audit UI is **fully stub** on both sides for list/bulk/apply-by-id.

### 2.4 “Enrich Legend” on Coin Detail (LLM)

**Frontend**

- **Hook:** `useExpandLegendV2()` in `useLLM.ts`  
  - `POST /api/v2/llm/legend/expand` with `{ abbreviation }`.
- **Usage:** `CoinDetailPage.handleEnrichLegend(side)` runs `expandLegend.mutateAsync({ abbreviation: legend })` and writes the expanded text into the coin cache for that side.  
- Labeled “Enrich” in the UI but behavior is **LLM legend expansion**, not catalog or audit enrichment.

**Backend**

- Implemented under the LLM router (`/api/v2/llm/...`). No change needed for “enrichment” semantics; this is a different feature.

### 2.5 Import “Enrich from Catalog”

**Frontend**

- **Hook:** `useEnrichPreview()` in `useImport.ts`  
  - `POST /api/v2/import/enrich-preview` with request that includes `references` and `context`.
- **Usage:** `EnrichmentPanel` calls it, then lets the user select suggested fields and call `onApplyEnrichment(updates)` to push those into the import preview state (no second request; apply is local to the preview).

**Backend**

- **Import router** (`import_v2.py`): Only `from-ngc`, `from-url`, `confirm`. **No** `enrich-preview`.  
- The v1 archive had `POST /enrich-preview` in `import_export.py`; that route is not present in the current app. So this flow will 404 when the user clicks “Enrich from Catalog” in the import UI.

### 2.6 BulkActionsBar “Enrich” (Collection Selection)

**Frontend**

- **Component:** `BulkActionsBar` takes optional `onEnrich?: (ids: number[]) => void`.  
- **Behavior:** On “Enrich” click it calls `onEnrich(ids)` if provided; otherwise it only shows a toast and does nothing.
- **Parent:** `CollectionPage` renders `<BulkActionsBar />` with **no** `onEnrich` (and no `onExport`). So “Enrich” is never wired to any API or navigation.

**Backend**

- No dedicated “bulk enrich selection” endpoint is called here. Any future implementation could call catalog bulk-enrich with `coin_ids` or a new endpoint.

---

## 3. Implementation Summary Table

| Feature | Frontend hook / client | HTTP endpoint(s) | Backend implemented? |
|---------|------------------------|------------------|------------------------|
| Catalog bulk enrich (page) | `useBulkEnrich`, `useJobStatus` | `POST /api/catalog/bulk-enrich`, `GET /api/catalog/job/{id}` | No |
| Catalog single-coin enrich | `useEnrichCoin` (unused in UI) | `POST /api/catalog/enrich/{id}` | No |
| Catalog lookup | `useLookupReference` | `POST /api/catalog/lookup` | Yes |
| Audit apply (field/value) | `client.applyEnrichment` | `POST /api/v2/audit/{id}/apply` | Yes |
| Review enrichments list | `useEnrichments` | (stub, no request) | No |
| Review bulk apply enrichments | `useBulkApplyEnrichments` | (stub, no request) | No |
| Review apply/reject by id | `useApplyEnrichment`, `useRejectEnrichment` | (stub, no request) | No |
| LLM “Enrich legend” | `useExpandLegendV2` | `POST /api/v2/llm/legend/expand` | Yes |
| Import enrich preview | `useEnrichPreview` | `POST /api/v2/import/enrich-preview` | No |
| BulkActionsBar Enrich | (no hook, optional `onEnrich`) | — | N/A (not wired) |

---

## 4. Recommendations for Follow-Up Work

- **Catalog bulk enrich:** Add `POST /api/catalog/bulk-enrich` and `GET /api/catalog/job/{id}` (and optionally `POST /api/catalog/enrich/{id}`) in `catalog.py` or a dedicated catalog Jobs module, and ensure request/response shapes match `useCatalog.ts` and `BulkEnrichPage`.
- **Review enrichments:** Implement backend endpoints for list, bulk apply, and apply/reject by id; then replace the stubs in `useAudit.ts` with real API calls that match the existing `Enrichment` / `EnrichmentFilters` types.
- **Import enrich preview:** Either add `POST /api/v2/import/enrich-preview` in `import_v2.py` (with behavior similar to v1 if desired) or switch the Import UI to use catalog lookup + custom aggregation for preview-only enrichment.
- **BulkActionsBar “Enrich”:** Either pass `onEnrich` from the collection page that calls catalog bulk-enrich with selected ids (or navigates to `/bulk-enrich` with preselected ids), or remove/relabel the button until that flow exists.
- **Naming:** Consider clearer labels so “Enrich” in the UI maps obviously to catalog vs audit vs LLM (e.g. “Bulk Normalize (Catalog)”, “Accept suggestion”, “Expand legend”).

---

**Doc generated from codebase exploration.**  
**Files touched:** `BulkEnrichPage`, `useCatalog`, `useAudit`, `api/client`, `EnrichmentPanel`, `useImport`, `CoinDetailPage`, `useLLM`, `AuditPanel`, `EnrichmentsReviewTab`, `EnrichmentCard`, `BulkActionsBar`, `CollectionPage`, `CollectionDashboard`, `Sidebar`, `CommandPalette`, `CommandBar`, backend `catalog.py`, `audit_v2.py`, `import_v2.py`, `scrape_v2.py`.
