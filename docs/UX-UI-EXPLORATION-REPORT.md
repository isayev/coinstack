# CoinStack UX/UI Exploration & Evaluation Report

**Date:** January 27, 2026  
**Scope:** Frontend (React/Vite) + API contract alignment, entry points, user journeys, consistency, error handling.

**Tested browsers/environments:** Browser validation run Jan 27, 2026 (cursor-ide-browser, localhost:3000 + 8000). See [Browser UX Findings](BROWSER-UX-FINDINGS.md). Recommend Chrome 120+ / Edge 120+ on Windows; Safari/Firefox for cross-browser check.

---

## 1. Executive Summary

- **Critical:** Series API base path mismatch — frontend calls `/api/series` while backend serves `/api/v2/series`; Series list/detail/create/add-coin will 404. Fix client to use `/api/v2/series` (and document in 07-API-REFERENCE).
- **Major:** Header/CommandBar “search then go to collection” does not apply the search: navigation is to `/?search=...`, redirect goes to `/collection/grid` without preserving query, and `filterStore` has no `search` field or URL sync — users see unfiltered collection. Add URL→filter sync and/or preserve `?search=` on redirect.
- **Major:** Command Palette coin search uses `client.getCoins({ search, limit: 5 })` but coins list API has no `search` parameter (only `issuer`, filters). Backend does not support full-text search on list; Command Palette “search” returns first page, not matches. Add backend `search`/FTS support or map UI search to `issuer` and document.
- **Minor:** API reference (07-API-REFERENCE) documents coins list as `skip`/`limit`; implementation uses `page`/`per_page`. Frontend matches implementation; doc is wrong and can mislead integrators.
- **Pagination:** The collection view uses **infinite scroll** (no page-number UI). `page`/`per_page` are used only to request “chunks” (e.g. 20 or 1000 for “all”). Traditional pagination controls are not used; `per_page`/`page` in API can be clarified as “chunk size”/“offset page” or deprecated in favor of cursor/limit if the API evolves.
- **Positive:** Strong patterns — Error Boundary, global Toaster, Zod + react-hook-form on coin create/edit, toast on mutation success/error, design tokens, and clear layout/sidebar/command palette.
- **Not assessed in this pass:** Accessibility (keyboard/screen reader, contrast, focus), mobile responsiveness, image handling (upload limits, zoom/gallery), and numismatic domain edge cases (BC/AD input, reference formats, die linking). Recommend follow-up passes; see [Accessibility Checklist](ACCESSIBILITY-CHECKLIST.md) and [Numismatic Edge Case Test Plan](NUMISMATIC-EDGE-CASE-TEST-PLAN.md).

---

## 2. Phase 1: Discovery & Mapping

### 2.1 Entry Points

| Type | Entry | Location / Notes |
|------|--------|------------------|
| **URL routes** | `/` → `/collection/grid` | `App.tsx` (`Navigate` replace) |
| | `/collection`, `/collection/grid`, `/collection/table` | Grid vs table view |
| | `/coins/new`, `/coins/:id`, `/coins/:id/edit` | Add, detail, edit |
| | `/import`, `/stats`, `/settings`, `/bulk-enrich`, `/auctions` | Feature pages |
| | `/audit` → `/review` | Redirect to Review Center |
| | `/series`, `/series/new`, `/series/:id` | Series flows |
| | `/review` | Review Center (tabs: discrepancies, enrichments, etc.) |
| **Sidebar** | Collection, Series, Auctions, Review Center, Statistics, Import, Enrich, Settings | `Sidebar.tsx`; links to `/`, `/series`, `/auctions`, `/review`, `/stats`, `/import`, `/bulk-enrich`, `/settings` |
| **Command palette (⌘K)** | Go to Collection/Statistics/Settings; Add Coin, Paste Auction URL, Import, Cert Lookup, Bulk Normalize, Run Audit | `CommandPalette.tsx`; Run Audit uses `/audit` → redirects to `/review` |
| **Command bar** | Logo → `/`, search submit → `/?search=...`, Add Coin, Paste URL, Cert Lookup | `CommandBar/index.tsx` |
| **Backend API** | `GET/POST /api/v2/coins`, `GET/PUT/DELETE /api/v2/coins/{id}` | Coins CRUD |
| | `GET /api/v2/stats/summary`, `POST /api/v2/scrape?url=...`, `POST /api/v2/import/from-url`, etc. | Stats, scrape, import |
| | Series: backend prefix `/api/v2/series` | Routers: `series.py` |
| **Frontend API client** | `client.getCoins`, `client.getCoin`, `client.createCoin`, `client.updateCoin`, `client.deleteCoin` | `api/client.ts` |
| | `client.getSeries`, `client.getSeriesDetail`, `client.createSeries`, `client.addCoinToSeries` | Uses **`/api/series`** → **mismatch** |

### 2.2 Primary User Journeys

1. **Browse collection**  
   Sidebar “Collection” or `/` → redirect to `/collection/grid` → infinite scroll list (or table via `/collection/table`). Filters live in `filterStore` and `CollectionSidebar`/`CollectionToolbar`; no URL sync for search.
2. **Add coin (manual)**  
   “Add Coin” or `/coins/new` → multi-step `CoinForm` (Identity → Physical → Design → Research → Commercial → Finalize) → submit → success toast + redirect.
3. **View/edit coin**  
   Click card or row → `/coins/:id`; edit → `/coins/:id/edit` → same form, then save.
4. **Search from header**  
   User types in Command bar search and submits → `navigate('/?search=' + q)` → app redirects to `/collection/grid` (replace), so `?search=` is dropped and never applied to filters or API.
5. **Search from Command Palette**  
   User types ≥2 chars → `client.getCoins({ search, limit: 5 })` → backend receives `search` and `limit`; coins list endpoint does not define `search` and uses `per_page` not `limit` → effective request is default list (e.g. first 20 coins), not search results.
6. **Series**  
   Sidebar “Series” → `/series` → dashboard; “New” → `/series/new`; “View” → `/series/:id`. All series calls go to `/api/series`* → 404 until client is fixed to `/api/v2/series`.
7. **Review Center**  
   Sidebar “Review Center” or “Run Audit” → `/review`; tab state in `?tab=...`.
8. **Import / Scrape / Bulk Enrich**  
   Dedicated pages and command-palette actions; backend uses `/api/v2/...` and is consistent for these.

### 2.3 Mental Model

- **Collection-centric:** Coins are the core entity; grid/table, filters, and detail/edit all revolve around the list.
- **Single-user desktop:** No auth, no rate limiting; local/dev usage assumed.
- **Numismatic domain:** Category, metal, issuer, mint, dates, grade, references, provenance, die study; vocabulary (issuer/mint) is normalized.
- **Workflows:** Manual add (multi-step form), import (Excel/URL), scrape (auction URL), bulk normalize, then review (discrepancies/enrichments) and audit.
- **Navigation:** Sidebar + Command Palette + header search; “Audit” in UI means “Review Center” (redirect).

---

## 3. Phase 2: Deep Functional Exploration (Code & Contract Level)

### 3.0 Pagination vs. infinite scroll

The **collection view does not use traditional pagination UI**. It uses **infinite scroll** via `useInfiniteQuery` and `IntersectionObserver` in `useCoinCollection` / `CoinGridPage` / `CoinTablePage`. The API still receives `page` and `per_page` (or `per_page: 1000` for “all” from filterStore). Recommendation: treat `page`/`per_page` as “chunk/offset” semantics; deprecate or rename in docs if moving to cursor-based or “limit/offset” only.

### 3.1 Phase 2a — Happy path: Coins list and search

| Input | Expected | Actual (from code) | Verdict |
|-------|----------|--------------------|---------|
| `GET /api/v2/coins?page=1&per_page=20` | First 20 coins, total, pages | Backend uses `page`, `per_page`; returns `items`, `total`, `page`, `per_page`, `pages` | **PASS** |
| `GET /api/v2/coins?search=Augustus` | Filter/search by text | Backend has no `search` param; only `issuer`, `category`, `metal`, etc. | **FAIL** – search not implemented |
| Header search → `/?search=X` | Collection filtered by X | Redirect to `/collection/grid` drops query; filterStore has no `search`; no component reads `?search=` | **FAIL** – search not applied |
| Command Palette `getCoins({ search, limit: 5 })` | Up to 5 matches for search | Backend ignores `search`; treats as default list (e.g. per_page=20 if sent as `per_page`) | **FAIL** – not search |

### 3.2 Phase 2a — Series API

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `client.getSeries()` → `GET /api/series` | 200, list of series | Backend mounts at `/api/v2/series` | **FAIL** – 404 |
| `client.getSeriesDetail(id)` → `GET /api/series/{id}` | 200, one series | Same | **FAIL** – 404 |
| `client.createSeries(...)` → `POST /api/series` | 201, series | Same | **FAIL** – 404 |
| `client.addCoinToSeries(...)` → `POST /api/series/{id}/coins/{coinId}` | 200/201 | Same | **FAIL** – 404 |

### 3.3 Phase 2a — Coin create/edit (happy path)

- **Form:** `CoinForm` uses `CreateCoinSchema` (Zod) + `zodResolver` + `react-hook-form`; steps: Identity, Physical, Design, Research, Commercial, Finalize.
- **Validation:** Schema includes “end year ≥ start year”; validation errors surface via `onError` + toast “Validation Failed” + inline list.
- **Submit:** `onSubmit` → `client.createCoin` / `client.updateCoin` → success/error toasts. **Expected:** PASS for valid payloads.

### 3.4 Phase 2b — Edge cases (from code)

- **Empty/invalid IDs:** Coin detail `/coins/:id` — CoinDetailPage validates `id` before query: if `!id || isNaN(coinId)` it shows “Invalid Coin ID” + “Back to Collection.” 404 from API is handled with “The coin you're looking for doesn't exist or has been deleted.” *(component: CoinDetailPage)*
- **Category mapping:** filterStore `toParams()` maps `imperial` → `roman_imperial`, `provincial` → `roman_provincial`, `republic` → `roman_republic`. Backend and other callers must use same taxonomy.
- **Empty states:** Documented in [§ 9. Empty States](#9-empty-states).

### 3.5 Phase 2c — Stress / boundary (from code)

- **Large list:** Infinite scroll uses `per_page` 20–1000; backend cap `per_page` 1000. No explicit “max items in DOM” or virtualization — potential jank with 1000+ cards in grid. Not measured.
- **Rapid actions:** No debounce on bulk delete or bulk enrich; `Promise.allSettled` used for bulk delete, with toast for partial success/failure.
- **Large inputs:** Form schema and backend define limits implicitly; no explicit max length on text fields (e.g. legends, notes) checked in this pass.

---

## 4. Phase 3: Consistency Audit

### 4.1 Naming and parameters

| Area | Inconsistency |
|------|----------------|
| **Coins list** | API reference: `skip`, `limit`. Implementation: `page`, `per_page`. Frontend uses `page`/`per_page`. |
| **Series base path** | Frontend client: `/api/series`. Backend router: `prefix="/api/v2/series"`. |
| **Search** | Frontend `GetCoinsParams.search` and Command Palette/header use “search”; backend coins list has no `search`, only `issuer` (partial). |

### 4.2 Patterns

- **Success/error feedback:** Mutations use `toast.success` / `toast.error` consistently (AddCoin, EditCoin, BulkActions, Scraper, Import, Review, etc.).
- **Form validation:** Coin create/edit use Zod + resolver; other forms (e.g. NGC cert) use local state + validation; no single standard for all forms.
- **API errors:** `api` (axios) interceptor normalizes to `Error` with message from `detail` or `error`; consumers often do `toast.error(error.message)`.

### 4.3 Documentation vs behavior

| Doc (07-API-REFERENCE) | Implementation | Gap |
|------------------------|----------------|-----|
| Coins list: `skip`, `limit` | `page`, `per_page` | Doc wrong |
| Series: “`/api/v2/series`” | Backend matches `/api/v2/series` | Client uses `/api/series` — doc and backend align; client does not |

---

## 5. Phase 4: UX Evaluation Criteria

| Criterion | Rating (1–5) | Evidence |
|-----------|--------------|----------|
| **Learnability** | 4 | Clear sidebar labels (Collection, Series, Auctions, Review, Statistics, Import, Enrich, Settings); Command Palette with shortcuts; multi-step Add Coin with step names and icons. Minus: “Audit” redirects to “Review” with no explanation; search in header looks like it should filter but doesn’t. |
| **Efficiency** | 4 | Grid/table toggle, filters, infinite scroll, bulk actions, keyboard shortcuts (e.g. N, G C/S/E). Minus: Series broken by wrong API path; header/command search doesn’t actually search. |
| **Memorability** | 4 | Stable nav and routes; Command Palette reinforces actions. Minus: Audit→Review and search behavior not obvious to re-learn. |
| **Error recovery** | 4 | Error Boundary with “Reload” and stack; toasts on mutation failure; validation errors listed in form. Minus: No explicit “retry” on network errors in list; Series 404 leaves user on empty/broken view. |
| **Satisfaction** | 4 | Theming, layout, and design tokens (e.g. metal colors) support a coherent look; Sonner toasts and step progress feel modern. Minus: Broken series and search reduce trust. |
| **Discoverability** | 4 | Sidebar, Command Palette, and header actions expose main features. Minus: “Audit” vs “Review” and that “Run Audit” goes to Review Center could be clearer; bulk enrich/series depend on paths that are broken or undocumented. |
| **Feedback** | 4 | Loading states, toasts, validation messages, and infinite-scroll “Load more” are present. Minus: When series calls 404 or search does nothing, feedback is generic (network/error) or missing. |
| **Flexibility** | 4 | Grid vs table, filters, sort, per_page options, optional steps in form. Minus: Search and series flows are not yet fully flexible due to bugs. |

---

## 6. Phase 5: Error & Exception Handling

- **Global:** `App` wraps app in `ErrorBoundary`; uncaught render errors show “Something went wrong” + stack + “Reload Page.” Toaster is global.
- **API:** Axios interceptor maps `response.data.detail` or `response.data.error` to `Error.message`; request-without-response → “Network error. Please check your connection.” This is consistent and sufficient for toasts.
- **Mutations:** Create/update/delete and other mutations use `onError` with `toast.error(error.message)` (or equivalent). Pattern is consistent.
- **Forms:** CoinForm uses `onError` + “Validation Failed” toast + list of validation messages; NGC cert panel uses local `validationError` state and inline message. Validation is present where checked.
- **Gaps:** No retry button or automatic retry for list/detail fetches; Series 404 is not turned into a clear “Series unavailable” message; header/command search doing nothing is a silent failure from the user’s perspective.

---

## 7. Phase 6: Findings and Action Plan

### 7.1 Issue Registry

#### Critical (breaks functionality)

| Issue | Location | Description | Suggested fix | Status |
|-------|----------|-------------|----------------|--------|
| Series API 404 | `frontend/src/api/client.ts` | All series calls use `/api/series` and `/api/series/{id}`; backend serves `/api/v2/series`. | Change `client.getSeries`, `getSeriesDetail`, `createSeries`, `addCoinToSeries` to use `/api/v2/series` (and `/api/v2/series/{id}`, etc.) to match backend and 07-API-REFERENCE. | **Fixed:** client updated to `/api/v2/series` in this pass. |

#### Major (significant UX friction)

| Issue | Location | Description | Suggested fix |
|-------|----------|-------------|----------------|
| Header search ignored | CommandBar, routes, filterStore | Submit goes to `/?search=...`; redirect to `/collection/grid` loses query; no `search` in filterStore or URL sync. | (a) Use `/collection/grid?search=...` and avoid replacing the whole URL when redirecting, or (b) add `search` to filterStore and sync from `useSearchParams()` on collection pages, then pass `search` in `toParams()` and to API. |
| Command Palette “search” not real search | CommandPalette, backend coins list | `getCoins({ search, limit: 5 })`; backend has no `search`, and uses `per_page` not `limit`. | Add `search` (and optionally `limit` → `per_page`) to coins list API and implement FTS or `issuer`-like filter; or map UI “search” to `issuer` and pass `per_page=5`, and document behavior. |
| Coins list API doc wrong | `docs/ai-guide/07-API-REFERENCE.md` | Documents `skip`/`limit` for list coins. | Update to `page`/`per_page` to match backend and frontend. |

#### Minor (polish)

| Issue | Location | Description | Suggested fix |
|-------|----------|-------------|----------------|
| Audit vs Review naming | Sidebar, Command Palette, routes | “Run Audit” and `/audit` send users to “Review Center”; link says “Audit.” | Use “Review” in labels and command names, or add one-line tooltip/description: “Audit: open Review Center.” |
| ReviewQueuePage not routed | `pages/ReviewQueuePage.tsx` | File exists; routes use `ReviewCenterPage` for `/review`. | Remove if dead code, or document and route under `/review/queue` or a tab. |

#### Suggestions (enhancements)

| Issue | Description | Suggested fix |
|-------|-------------|----------------|
| Retry on list/load failure | Failed fetch shows toast but no retry. | Add “Retry” in alert or toast action for query errors. |
| Series 404 message | When series API returns 404, show “Series service unavailable” or “Check backend” instead of generic error. | In series hooks/pages, treat 404 as config/setup issue and show specific message. |
| URL ↔ filters | Filters (including future search) not reflected in URL. | Sync filterStore (and search) with `?category=...&search=...` so links and refresh preserve state. |

### 7.2 Consistency Matrix

| Topic | Frontend | Backend | Docs | Consistent? |
|-------|----------|---------|------|-------------|
| Coins list pagination | `page`, `per_page` | `page`, `per_page` | `skip`, `limit` | ✗ (docs) |
| Series base path | `/api/series` | `/api/v2/series` | `/api/v2/series` | ✗ (client) |
| Coins “search” | `search` param used in client/palette | Not accepted | Not documented | ✗ (behavior) |
| Error feedback | Toasts + ErrorBoundary | HTTP + `detail` | — | ✓ |
| Category values | `roman_imperial` etc. in toParams | Same in filters | — | ✓ (implied) |

### 7.3 Prioritized Action Plan

| Order | Action | Impact | Effort | Owner |
|-------|--------|--------|--------|-------|
| 1 | Fix Series API base path in `client.ts` to `/api/v2/series` | Unblocks Series flows | S | Dev |
| 2 | Implement or document coins “search”: backend param + filter, or map to `issuer` + `per_page`; fix Command Palette and header flow | Makes search actionable | M | Backend + Frontend |
| 3 | Sync header/collection search with URL and filterStore (e.g. `?search=` on `/collection/grid`) | Search-from-header works | M | Frontend |
| 4 | Update 07-API-REFERENCE coins list to `page`/`per_page` | Prevents integrator mistakes | S | Docs |
| 5 | Clarify Audit vs Review in UI (label or tooltip) | Reduces confusion | S | Frontend |
| 6 | Optional: URL ↔ filters (and search) for shareable/refreshable state | Better links and refresh | L | Frontend |
| 7 | Clarify or deprecate `page`/`per_page` in API/docs (infinite scroll only; no pagination UI) | Reduces confusion for integrators | S | Docs / API |

---

## 8. Appendix: Evidence and References

- **Routes:** `frontend/src/App.tsx` (Routes, Navigate).
- **Sidebar:** `frontend/src/components/layout/Sidebar.tsx` (nav items, `to`).
- **Command palette:** `frontend/src/components/layout/CommandPalette.tsx` (actions, `getCoins({ search, limit: 5 })`).
- **Command bar:** `frontend/src/components/layout/CommandBar/index.tsx` (`navigate('/?search=' + …)`).
- **Filter store:** `frontend/src/stores/filterStore.ts` (no `search`; `toParams()`).
- **API client:** `frontend/src/api/client.ts` (Series calls to `/api/series`).
- **Coins router:** `backend/src/infrastructure/web/routers/v2.py` (get_coins: `page`, `per_page`, no `search`).
- **Series router:** `backend/src/infrastructure/web/routers/series.py` (`prefix="/api/v2/series"`).
- **API reference:** `docs/ai-guide/07-API-REFERENCE.md` (coins list `skip`/`limit`).
- **Error handling:** `frontend/src/api/api.ts` (interceptor), `frontend/src/App.tsx` (ErrorBoundary), and grep for `toast`/`onError` across pages and hooks.

---

## 9. Empty States

| Context | Component / location | What the user sees |
|--------|-----------------------|---------------------|
| **Empty collection (new user)** | `CoinGridPage`, `CoinList` | “No coins found” + 📦 emoji, “Add your first coin…” + primary “Add Coin” / “Add Your First Coin” CTA. *[screenshot: empty collection view]* |
| **Empty collection (filters applied)** | Same | Same copy — no distinct “No results for filters” vs “Start from scratch.” Consider “No coins match your filters” with “Clear filters” when filters are active. |
| **Empty series list** | Series dashboard | Not verified in this pass; recommend adding empty state + “Create series” CTA. |
| **No search results (once search works)** | Command palette, collection | Command palette: `CommandEmpty` “No results found.” Collection: reuses “No coins found” unless filterStore distinguishes search. |
| **No auctions tracked** | Auctions page | `AuctionListV2` has error Alert for load failure; empty list UX not confirmed. |
| **Review tabs empty** | `ReviewCenterPage` tabs | `ReviewEmptyState` variants: `all-clear`, `vocabulary`, `ai`, `images`, `data` — each with icon, title, description, and optional action (e.g. “View Collection”, “Run Bulk Normalize”). *(components: AIReviewTab, VocabularyReviewTab, EnrichmentsReviewTab, DiscrepanciesReviewTab, DataReviewTab)* |

---

## 10. Loading & Skeleton States

| Context | Mechanism | Notes |
|---------|------------|--------|
| **Collection grid load** | `CoinCardV3Skeleton` × N in grid | `CoinGridPage` shows ~10 skeletons; `CoinList` uses same. |
| **Collection table load** | `<Skeleton className="h-14 w-full" />` per row | `CoinTablePage`. |
| **Coin detail load** | Multiple `<Skeleton>` blocks (header, content areas) | `CoinDetailPage`. |
| **Edit coin load** | `<Skeleton className="h-[600px] w-full" />` | `EditCoinPage`. |
| **Stats dashboard** | Skeletons for header + chart areas | `StatsPageV3`. |
| **Import preview (URL / NGC)** | Small skeletons for image/content placeholders | `URLImportPanel`, `NGCImportPanel`. |
| **Auctions list** | `<Skeleton className="h-[280px] w-full rounded-lg" />` per row | `AuctionListV2`. |
| **Infinite scroll “load more”** | Text “Loading more coins…” + spinner | `CoinGridPage` sentinel. No skeleton for appended rows. |

*Jank/hydration:* Not measured. Recommend spot-check on slow throttling and with 100+ items in DOM.

---

## 11. Destructive Actions & Confirmation

| Action | Confirmation? | Location / notes |
|--------|----------------|-------------------|
| **Bulk delete (multiple coins)** | Yes — `AlertDialog`: “Delete N coin(s)? This action cannot be undone…” + Cancel / Delete | `BulkActionsBar.tsx` — `AlertDialog` + `AlertDialogTitle` / `AlertDialogDescription` / `AlertDialogAction` (red). |
| **Single-coin delete** | No — `IdentityHeader` exposes “Delete” in dropdown only when `onDelete` is passed; **CoinDetailPage does not pass `onDelete`**, so there is no delete on the detail page in current code. | If/when wired: add confirmation dialog before calling `client.deleteCoin(id)`. |
| **Remove coin from series** | Not verified | Recommend confirmation if implemented. |
| **Import confirm / overwrite** | Context-dependent; `ScrapeDialog` uses “confirm” for saving scraped data. | Import flows use `confirmImport`; exact prompts not enumerated here. |

---

## 12. Accessibility (a11y) — Not Fully Audited

*Follow-up: use [ACCESSIBILITY-CHECKLIST.md](ACCESSIBILITY-CHECKLIST.md).*

| Area | Status | Notes |
|------|--------|--------|
| **Keyboard navigation** | Partial | Shortcuts (⌘K, N, G C/S/E, /) in `useKeyboardShortcuts`; Command Palette is dialog (likely focus trap via shadcn). Toolbar/sidebar and grid cards need explicit check (tab order, Enter/Space on cards). |
| **Screen readers** | Unaudited | Icon-only buttons (e.g. sidebar collapse, card actions) — need `aria-label` or visually hidden text. Toasts: Sonner/Radix may use live region; confirm `role="status"` or `aria-live`. |
| **Color contrast** | Unaudited | Metal tokens (gold, silver, bronze) and grade/category colors — need contrast check on `--bg-card` / `--bg-elevated` for WCAG AA. |
| **Focus indicators** | Partial | shadcn/Radix use `:focus-visible`; custom buttons/links may need `ring` or `outline`. |

---

## 13. Numismatic Domain Edge Cases

*Follow-up: use [NUMISMATIC-EDGE-CASE-TEST-PLAN.md](NUMISMATIC-EDGE-CASE-TEST-PLAN.md).*

| Edge case | Current handling (from code) |
|-----------|------------------------------|
| **BC/AD dates** | `year_start` / `year_end` are signed integers; negative = BC. `formatYear()` and UI labels use “27 BC” / “AD 14”. Placeholders: “e.g., -27 for 27 BC” (CoinPreviewEditor, CollectionDashboard). Schema: `year_end >= year_start` in `CreateCoinSchema`. |
| **Uncertain date ranges** | Schema supports `year_start` ≠ `year_end`. `dating_certainty` exists in domain (`BROAD`, `NARROW`, `EXACT`) — UI usage not fully traced. |
| **Reference formats (RIC, RSC, RPC, BMC)** | References are structured (catalog, number, volume). Vocab/autocomplete and `ReferenceSuggest`; no strict format validation found in frontend — often free text + catalog type. |
| **Denomination variants** | Denomination filter/vocab; “Aureus vs double aureus” — controlled vocab vs free text not fully audited. |
| **Die study / linking** | `obverse_die_id` / `reverse_die_id` and die-study UI; backend has die-study endpoints. “Multiple specimens from same dies” linking mechanism exists in domain; UX for linking not fully walked. |

---

## 14. Image Handling

| Aspect | Status |
|--------|--------|
| **Upload flow** | No local file upload found; images are URLs (e.g. from scraped auction data or pasted URLs). `ImageManager` assigns obverse/reverse from auction-sourced URLs. |
| **Size/format limits** | Not enforced in frontend; backend/storage limits not checked in this pass. |
| **Missing image placeholder** | Cards and detail use `images?.[0]?.url` or fallback icon (e.g. Coins icon in Command Palette); explicit “no image” placeholder component not enumerated. |
| **Zoom / gallery on detail** | Obverse/reverse panels; zoom or lightbox not confirmed. |
| **Obverse/reverse pairing** | `ImageManager` and Finalize step allow selecting which URL is obverse vs reverse; pairing logic exists. |

---

## 15. Responsive / Mobile

| Aspect | Evidence |
|--------|----------|
| **Breakpoints** | Tailwind `sm:`, `md:`, `lg:`, `xl:`, `2xl:`, `3xl:`, `4xl:` used in grid, Command bar, layout (e.g. `CollectionLayout` sidebar `hidden lg:block`). |
| **Design target** | Layout and sidebar suggest desktop-first; grid cols reduce on small screens. |
| **Touch targets** | Not measured; card/row height and button size should be checked for 44×44 px (or equivalent) on touch devices. |
| **Command palette on mobile** | ⌘K is desktop; mobile needs an alternative (e.g. floating action, or “Search” in header that opens same palette). |

---

## 16. Performance Baseline

- **Bundle size:** Not measured. Run `npm run build` and inspect `dist/` and Vite summary for chunk sizes.
- **LCP on collection grid:** Not measured. Suggest Lighthouse or WebPageTest with cold load.
- **Infinite scroll + memory:** List appends nodes; no virtualization seen. With 1000+ coins, risk of high DOM count and sluggish scroll; consider virtualized list for table/grid if needed.

---

## 17. Partial Failure in Bulk Operations

| Flow | Behavior (from code) |
|------|----------------------|
| **Bulk delete** | `Promise.allSettled(ids.map(id => client.deleteCoin(id)))`; toasts: “Deleted N coins” (all success), “Failed to delete all N” (all fail), “Deleted N, M failed” (mixed). No per-coin error list in UI. |
| **Bulk normalize / enrich** | `BulkEnrichPage` shows per-coin status (e.g. success/error) in results; exact messaging and retry/partial-apply behavior need verification. |
| **Import from Excel** | Import confirm and batch endpoints; row-level errors vs all-or-nothing not fully traced. |

---

## 18. Browser DevTools / Console

- **Console warnings/errors:** Not captured. Recommend a clean run (e.g. open Collection → Add Coin → Save) and note React warnings, missing keys, or deprecations.
- **Strict Mode:** If enabled, double-invoked effects may surface; no specific issues noted in this pass.
- **Missing keys:** Some lists use `key={id}` or `key={\`${coin.id}-${index}\`}`; audit remaining `.map()` for stable, unique keys.

---

## 19. Security Note (Single-User Context)

Even for a single-user app, consider:

| Risk | Mitigation |
|------|-------------|
| **XSS via coin text** | Render user-authored fields (legends, notes, descriptions) as plain text or sanitized HTML; avoid `dangerouslySetInnerHTML` on unsanitized input. |
| **URL injection in scraping** | Validate auction URLs (allowlist of domains or patterns) before calling scrape; avoid `javascript:` or `data:` and open redirects. |
| **Local storage / IndexedDB** | filterStore is persisted; avoid storing secrets. If moving to IndexedDB for offline, treat as untrusted on shared devices. |

---

## 20. Browser Testing (Live Session)

A live browser pass was run on **January 27, 2026** to simulate realistic user flows and check UI/UX consistency. Full notes: **[BROWSER-UX-FINDINGS.md](BROWSER-UX-FINDINGS.md)**.

**Validated:** URL→filter sync (`/collection/grid?search=Augustus` filters correctly); coin 404 vs invalid-ID messaging and “Back to Collection”; Series empty state (no 404); Review Center tabs and counts; table view and grid parity; Command Palette open and “Run Audit → Open Review Center” label.

**To double-check:** Header search submit on Enter (form navigation to `?search=...`); Command Palette coin suggestions when typing 2+ chars; optional copy and “Add” placement improvements listed in the findings doc.

**Implementation plan for recommendations:** [BROWSER-UX-RECOMMENDATIONS-PLAN.md](BROWSER-UX-RECOMMENDATIONS-PLAN.md) — phased steps (A–E), files, and acceptance criteria.
