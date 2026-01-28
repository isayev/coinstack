# Plan: Browser UX Recommendations

**Source:** [BROWSER-UX-FINDINGS.md](BROWSER-UX-FINDINGS.md) (Section 4 — Issues & Improvement Ideas)  
**Date:** January 27, 2026

This plan turns the browser validation recommendations into ordered, actionable steps with files, dependencies, and acceptance criteria.

---

## Overview

| Phase | Focus | Effort | Dependencies |
|-------|--------|--------|--------------|
| **A** | Header search submit on Enter | S | None |
| **B** | Command Palette coin suggestions (verify/fix) | S–M | None |
| **C** | Empty collection: filters-on vs first-time copy | S | filterStore already has `getActiveFilterCount`, `reset` |
| **D** | Two “Add” entry points — clarify or document | XS | None |
| **E** | Coin image placeholder — “No image” / a11y | S | None |

Effort: XS = tiny, S = small, M = medium, L = large.

---

## Phase A: Header Search Submit on Enter

**Goal:** Ensure pressing Enter in the header search field reliably navigates to `/collection/grid?search=...` and applies the filter.

**Current behavior:** Form uses `onSubmit={handleSearch}` and `navigate('/collection/grid?search=' + …)`. URL→filter sync already works when the user lands with `?search=`. In one browser run, Enter in the field did not change the URL.

**Files:** `frontend/src/components/layout/CommandBar/index.tsx`

**Steps:**

1. **Inspect submit path**
   - Confirm the search `<form>` wraps only the one `<Input>` (and the ⌘K hint is `type="button"` so it doesn’t submit).
   - Confirm no `onKeyDown` on the input calls `preventDefault()` for `Enter`.

2. **Harden submit-on-Enter**
   - If the native form submit is unreliable (e.g. focus/React), add on the search input:
     - `onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSearch(e as unknown as React.FormEvent); } }}`
     - Or use a hidden `<button type="submit">` and ensure the input is the only focusable field that can trigger it.

3. **Optional: Sync input from URL**
   - When the user lands on `/collection/grid?search=Augustus`, consider initializing the header search input from `searchParams.get('search')` so the bar reflects the current filter (docs-only if out of scope).

**Acceptance criteria:**

- [ ] From collection grid, focus header search, type “Augustus”, press Enter.
- [ ] URL becomes `/collection/grid?search=Augustus` and the list is filtered to issuer “Augustus”.

**Docs:** If behavior or scope is clarified, update `docs/ai-guide/11-FRONTEND-COMPONENTS.md` (CommandBar search) and/or [BROWSER-UX-FINDINGS.md](BROWSER-UX-FINDINGS.md) issue #1.

---

## Phase B: Command Palette Coin Suggestions (Verify / Fix)

**Goal:** When the user types 2+ characters in the Command Palette, issuer-filtered coin suggestions appear and selecting one navigates to that coin.

**Current behavior:** Palette uses `client.getCoins({ issuer: search.trim(), per_page: 5, page: 1 })`. In the browser snapshot, typing “Aug” showed a “Suggestions” listbox but coin options were not clearly visible in the a11y tree.

**Files:** `frontend/src/components/layout/CommandPalette.tsx`, and any shared combobox/list component it uses.

**Steps:**

1. **Verify behavior manually**
   - Open palette (Ctrl+K), type “Aug” (or “Constantius”).
   - Confirm that up to 5 coin suggestions appear and that each has a visible label (e.g. ruler + denom).
   - Confirm that choosing a suggestion navigates to `/coins/{id}`.

2. **Fix visibility/discoverability if needed**
   - If suggestions never show: check query (issuer), loading state, and where results are rendered (command list vs. a nested listbox).
   - If they show but are hard to see: improve structure/labels so the “Suggestions” (or “Coins”) group and each option are clearly exposed (e.g. `role="option"`, `aria-label` on groups).

3. **Optional: loading/empty state**
   - While `issuer` query is in flight, show a short “Searching…” or spinner.
   - If there are 0 results, show “No coins match” (or reuse existing CommandEmpty).

**Acceptance criteria:**

- [ ] Typing 2+ characters shows up to 5 issuer-filtered coin suggestions.
- [ ] Selecting a suggestion navigates to that coin’s detail page.
- [ ] (Optional) Loading and empty states are clear.

**Docs:** Note resolution in [BROWSER-UX-FINDINGS.md](BROWSER-UX-FINDINGS.md) issue #2; add a line to `docs/ai-guide/11-FRONTEND-COMPONENTS.md` for Command Palette coin search if not already there.

---

## Phase C: Empty Collection — “No Match” vs “First Time”

**Goal:** When the collection is empty, use different copy and actions when filters are active vs when the collection is brand‑new.

**Current behavior:** `CoinGridPage` and `CoinTablePage` both use “No coins found” + “Add your first coin…” + “Add Coin” for every empty list.

**Files:**
- `frontend/src/pages/CoinGridPage.tsx`
- `frontend/src/pages/CoinTablePage.tsx`
- `frontend/src/stores/filterStore.ts` (use `getActiveFilterCount`, `reset`)

**Steps:**

1. **Use active-filter count in empty branch**
   - In both pages, in the `coins.length === 0` branch, call `getActiveFilterCount()` from `useFilterStore()`.

2. **Branch copy and actions**
   - **If `getActiveFilterCount() > 0`:**
     - Title: “No coins match your filters”
     - Short line: “Try clearing or changing filters.”
     - Primary action: “Clear filters” — onClick: `reset()`, then optional `navigate('/collection/grid')` or equivalent to clear `?search=…` if present.
     - Secondary (optional): “Add Coin” as a secondary button or link.
   - **If `getActiveFilterCount() === 0`:**
     - Keep current: “No coins found” + “Add your first coin to start your collection.” + “Add Coin” (navigate to `/coins/new`).

3. **URL vs store**
   - If search (and other filters) are synced to the URL, “Clear filters” should both reset the store and update the URL (e.g. strip `?search=…`). If URL sync is not implemented yet, resetting the store is enough for this phase.

**Acceptance criteria:**

- [ ] With no filters: empty list shows “No coins found” and “Add Coin” as today.
- [ ] With any filters (e.g. search “Augustus” or metal/category): empty list shows “No coins match your filters” and “Clear filters” (and list updates after reset).

**Docs:** Update [UX-UI-EXPLORATION-REPORT.md](UX-UI-EXPLORATION-REPORT.md) §9 Empty States and [BROWSER-UX-FINDINGS.md](BROWSER-UX-FINDINGS.md) issue #3 when done.

---

## Phase D: Two “Add” Entry Points — Clarify or Document

**Goal:** Remove ambiguity between header “Add Coin” and collection toolbar “Add”; either make the difference obvious in the UI or document that they are the same.

**Current behavior:**
- **CommandBar:** “Add Coin” (with dropdown: Import, Enrich, etc.) — primary action, navigates to `/coins/new` on main click.
- **CollectionToolbar:** “Add” with Plus icon — same `navigate('/coins/new')`.

So both are “add coin” from the user’s perspective.

**Files:**
- `frontend/src/components/layout/CommandBar/index.tsx` (Add Coin)
- `frontend/src/features/collection/CollectionToolbar.tsx` (Add button)

**Steps (choose one direction):**

**Option A — Same action, clearer label**
- In `CollectionToolbar`, change label from “Add” to “Add coin” (or “Add Coin”) and/or set `title="Add coin"` so hover matches the header. No behavior change.

**Option B — Keep both, document**
- Add a short note in `docs/ai-guide/11-FRONTEND-COMPONENTS.md`: “Add Coin (header) and Add (collection toolbar) both go to New Coin; header includes Import/Normalize in dropdown.”

**Option C — Remove toolbar “Add”**
- If product prefers a single entry point, remove the “Add” button from `CollectionToolbar` and rely on header “Add Coin” and Command Palette “Add Coin”.

**Recommendation:** Option A (align label/tooltip) is the smallest change; Option C reduces redundancy if you want one primary entry point.

**Acceptance criteria:**

- [ ] Either labels/tooltips clearly indicate both do “add coin”, or one entry point is removed, or behavior is documented in the component guide.

**Docs:** Update [BROWSER-UX-FINDINGS.md](BROWSER-UX-FINDINGS.md) issue #4 and `docs/ai-guide/11-FRONTEND-COMPONENTS.md` as chosen.

---

## Phase E: Coin Image Placeholder — “No image” / A11y

**Goal:** When a coin has no obverse/reverse image, the placeholder is clearly recognizable as “no image” and is accessible (e.g. for screen readers).

**Current behavior:** `CoinCard` (and similar) use a generic icon (e.g. Coins) when `!images.obverse` or `!images.reverse`. No explicit “No image” text or `aria-label`.

**Files:**
- `frontend/src/components/coins/CoinCard.tsx` (grid card image area)
- Any table cell or detail view that shows the same placeholder (e.g. `CoinTableRow`, coin detail image panels).

**Steps:**

1. **Card placeholder**
   - In the block that renders the Coins icon when there is no obverse/reverse image, add:
     - `aria-label="No image"` (or “No obverse image” / “No reverse image” if the component knows the side).
     - Optional: a small visible “No image” (or “—”) under or over the icon, using existing design tokens so it’s subtle but scannable.

2. **Detail and table**
   - Apply the same idea wherever the same placeholder is used (e.g. detail obverse/reverse panels, table thumbnails): ensure either an `aria-label` or a short visible “No image” so state is clear.

3. **Design**
   - Reuse `text-muted-foreground` or `--text-ghost` so the text doesn’t dominate the card; keep the icon as the main visual.

**Acceptance criteria:**

- [ ] Placeholder regions have `aria-label="No image"` (or “No obverse/reverse image” where applicable).
- [ ] (Optional) A short “No image” or “—” is visible on card/detail/table placeholder for quick scanning.

**Docs:** Note in [BROWSER-UX-FINDINGS.md](BROWSER-UX-FINDINGS.md) issue #5 and in [ACCESSIBILITY-CHECKLIST.md](ACCESSIBILITY-CHECKLIST.md) under “Images / placeholders” if that section exists.

---

## Execution Order and Tracking

Suggested order: **A → B → C** (search and discovery first), then **D** and **E** (clarity and a11y) in any order.

| Phase | Owner | Status |
|-------|--------|--------|
| A — Header search Enter | — | Done |
| B — Command Palette coins | — | Done |
| C — Empty state copy | — | Done |
| D — Add entry points | — | Done |
| E — Image placeholder a11y | — | Done |

When implementing, mark phases in this table and add a one-line “Done: …” under each phase’s acceptance criteria. After each phase, update the linked docs (BROWSER-UX-FINDINGS, 11-FRONTEND-COMPONENTS, UX report §9, ACCESSIBILITY-CHECKLIST) as indicated above.
