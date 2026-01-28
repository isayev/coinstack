# Browser-Based UX Validation Findings

**Date:** January 27, 2026  
**Method:** Live browser (cursor-ide-browser) against frontend on `http://localhost:3000` with backend on port 8000.  
**Reference:** [UX-UI-EXPLORATION-REPORT.md](UX-UI-EXPLORATION-REPORT.md)

---

## 1. Typical Flows Tested

| Flow | Result | Notes |
|------|--------|--------|
| **Land on app** | ✓ | `/` → redirect to `/collection/grid`; grid loads with coins, filters, sort, Grid/Table toggle. |
| **Search by URL** | ✓ | Navigate to `/collection/grid?search=Augustus` → collection filters to issuer “Augustus”; shows “Filters 1”, “Reset”, “All 2 coins loaded”. Filter facets (Metal Ag 2, Category Imperial 2, Grade Fine/Unknown) match the 2 coins. |
| **Header search submit** | ⚠ | Typing “Augustus” in header search and pressing Enter did *not* change the URL in one session. Direct navigation to `?search=Augustus` works and applies the filter. Form uses `onSubmit={handleSearch}` and `navigate('/collection/grid?search=' + ...)` — recommend verifying Enter-in-field submit in real usage (focus, form structure). |
| **Command Palette (Ctrl+K)** | ✓ | Opens combobox “Search coins, commands…”. Quick actions: Add Coin, Paste Auction URL, Import, Cert Lookup, Bulk Normalize, Run Audit (“Open Review Center”), Go to Collection/Statistics/Settings. “Run Audit” description matches Audit→Review labeling. |
| **Command Palette coin search** | ⊘ | Typed “Aug” in palette; “Suggestions” listbox present but snapshot did not show coin options as children. May be async or structure; suggest manual check that issuer-filtered coin suggestions appear and are clickable. |
| **Table view** | ✓ | `/collection/table` shows sortable columns (ID, Ruler, Reign, Denom, Mtl, Mint, Date, Obv/Rev, Wgt, Dia, Sts, Ref, Grd, Loc, Rty, Value), row checkboxes, Grid/Table toggle. Same chrome and filters as grid. |
| **Review Center** | ✓ | `/review` loads; “Review Center” heading and subtitle; tabs Vocabulary (2), AI Suggestions (11), Images, Discrepancies, Enrichments, Auto-Merge, History, Data. Vocabulary tab shows items (e.g. “#64 · travel mint?”, “#20 · Marcus Aurelius…”), Reject, Confidence/Smart Sort/Refresh. |
| **Series** | ✓ | `/series` loads; empty state “No series created yet”, “Start by creating a custom series or using a template”, “Create your first series” / “Create Series”. Confirms Series API base path fix (`/api/v2/series`) — no 404. |

---

## 2. Corner Cases Tested

| Case | URL / Action | Result | UI Shown |
|------|--------------|--------|----------|
| **Nonexistent coin** | `/coins/999999` | ✓ | “Coin not found”; “The coin you're looking for doesn't exist or has been deleted.”; “Back to Collection” button. |
| **Invalid coin ID** | `/coins/abc` | ✓ | “Invalid Coin ID”; “The URL contains an invalid coin identifier.”; “Back to Collection” button. |
| **Search-by-URL** | `/collection/grid?search=Augustus` | ✓ | Filter applied; 2 coins; “Filters 1”, “All 2 coins loaded”. |

---

## 3. Visual & UX Consistency

| Area | Observation |
|------|-------------|
| **Layout** | Header (logo, Add Coin, Paste URL, Cert #, search, ⌘K, theme, settings) and left sidebar (Collection, Series, Auctions, Review Center, Statistics, Import, Enrich, Settings, Collapse) are stable across Collection grid/table, coin 404, invalid ID, Review, Series. |
| **Empty states** | Series: “No series created yet” + clear CTA. Coin 404 / invalid ID: short copy + “Back to Collection”. |
| **Error differentiation** | 404 → “Coin not found” / “doesn't exist or has been deleted”; invalid id → “Invalid Coin ID” / “invalid coin identifier”. Both offer same recovery CTA. |
| **Collection** | Grid and table share filters, sort, view toggle. Grid shows cards with ruler, denom, mint, badges; table shows sortable columns and row selection. |
| **Review Center** | Tabs, counts, and item cards (Vocabulary “#64 …”, “#20 …”) align with report §9 empty states and Phase 2 flows. |
| **Add actions** | Header “Add Coin” and collection bar “Add” both present; report/screenshots noted possible redundancy — confirm if both do “add coin” or differ in scope. |

---

## 4. Issues & Improvement Ideas

**Implementation plan:** [BROWSER-UX-RECOMMENDATIONS-PLAN.md](BROWSER-UX-RECOMMENDATIONS-PLAN.md) — phased steps, files, and acceptance criteria. **Phases A–E implemented** (header search Enter, Command Palette loading/empty/aria, empty-state copy + Clear filters, Add coin label/title, image placeholder aria + "No image").

| # | Issue / Idea | Severity | Suggestion |
|---|--------------|----------|-----------|
| 1 | Header search: Enter in field did not trigger navigation to `?search=...` in one run. | Medium | Confirm form submit on Enter (default submit, no intercept by ⌘K or other handlers). If needed, add explicit submit-on-Enter in input. |
| 2 | Command Palette coin suggestions for “Aug” not clearly visible in accessibility snapshot. | Low | Manually verify that typing 2+ chars shows issuer-filtered coins and that selecting one navigates to coin detail. |
| 3 | Empty collection copy same for “no data” and “filters applied, no match”. | Low | Per report §9: when filters are active, consider “No coins match your filters” + “Clear filters” vs “No coins found” + “Add Coin”. |
| 4 | Two “Add” entry points (header “Add Coin”, collection “Add”) may duplicate the same action. | Low | Clarify in UI or docs, or merge if identical. |
| 5 | Placeholder for missing coin images (e.g. “OD” or generic icon) — improve discoverability. | Low | Consider “No image” or similar short label on placeholder for accessibility and clarity. |

---

## 5. Summary

- **URL → filter sync:** Visiting `/collection/grid?search=Augustus` correctly filters by issuer and shows “Filters 1” and “All N coins loaded.”
- **Series:** Empty state loads correctly; no 404, so client use of `/api/v2/series` is validated in-browser.
- **Error recovery:** Coin 404 and invalid ID each have clear copy and “Back to Collection.”
- **Consistency:** Layout, theming, and CTAs are consistent across Collection, Review, Series, and error pages.
- **Implemented (Phases A–E):** Header search submit on Enter; Command Palette loading/empty states and aria-labels; empty collection “No coins match your filters” + Clear filters; toolbar “Add coin” label/title; image placeholders with aria-label and “No image” in CoinCard and CoinTableRow.
