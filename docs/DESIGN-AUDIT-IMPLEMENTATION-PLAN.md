# Design Audit — Step-by-Step Implementation Plan

**Purpose:** Ordered, actionable steps to fix design-audit issues and adopt the token system.  
**Source:** [DESIGN-AUDIT-REPORT.md](DESIGN-AUDIT-REPORT.md), [DESIGN-AUDIT-ISSUE-LOG.md](DESIGN-AUDIT-ISSUE-LOG.md), [DESIGN-AUDIT-TOKEN-MAP.md](DESIGN-AUDIT-TOKEN-MAP.md).

**Conventions:**  
- Step N = one clear outcome; “Verify” = how to confirm it’s done.  
- Close the corresponding issue in the issue log when a step is done.

---

## Phase A — Quick wins (low effort, high impact)

### Step 1 — Remove duplicate certification block in CSS  
**Issues:** VC-001, VC-006

1. Open `frontend/src/index.css`.
2. Find the **first** certification block (around lines 249–251):
   - `--cert-ngc: #1A73E8;`
   - `--cert-pcgs: #2E7D32;`
   - `--cert-anacs: #9C27B0;`
3. **Delete** that first block only (leave the “Legacy aliases” `--grade-ngc` / `--grade-pcgs` that follow if they reference cert; see Step 2).
4. Keep the **second** certification block (around 339–346) as the single source:
   - `--cert-ngc: #003366;`
   - `--cert-ngc-subtle: rgba(0, 51, 102, 0.15);`
   - `--cert-pcgs: #00529B;`
   - `--cert-pcgs-subtle: rgba(0, 82, 155, 0.15);`
   - `--cert-anacs: #8B0000;` and `-subtle`.
5. **Verify:** Search `index.css` for `--cert-ngc` — only one definition remains. Cert badges (NGC/PCGS/ANACS) still render; color is the “navy” set (#003366 / #00529B).

---

### Step 2 — Unify cert vs grade aliases (avoid double-definition)  
**Issues:** VC-006

1. In `frontend/src/index.css`, in the “Legacy aliases” area (around 254–257):
   - Keep `--grade-ngc` and `--grade-pcgs` **only** if they are used for “grade” styling (e.g. grade badges that look like NGC/PCGS).
   - If they are purely duplicating cert colors, set them to the cert vars:
     - `--grade-ngc: var(--cert-ngc);`
     - `--grade-ngc-bg: var(--cert-ngc-subtle);`
     - `--grade-pcgs: var(--cert-pcgs);`
     - `--grade-pcgs-bg: var(--cert-pcgs-subtle);`
2. Ensure no other block redefines `--cert-ngc` / `--cert-pcgs` / `--cert-anacs`.
3. **Verify:** Cert and grade-related badges use the same underlying color; grep for `--grade-ngc` / `--cert-ngc` shows no conflicting definitions.

---

### Step 3 — Align design doc with code (cert, grade-ms, rarity-r3)  
**Issue:** VC-002

1. Open `docs/ai-guide/10-DESIGN-SYSTEM.md`.
2. In **§2.4 Grade Colors** (or equivalent):
   - Set **grade-ms** in the doc to match code: `#FF6B6B` (not `#DC2626`).
   - Ensure any “MS/FDC” row says `#FF6B6B` and references `--grade-ms`.
3. In **§2.5 Rarity Colors** (or equivalent):
   - Set **rarity-r3** (or “R3 / Extremely Rare”) to match code: `#EF4444` (not `#F59E0B`).
   - Set **rarity-unique** if documented: code uses `#FFFFFF` for Unique.
4. Add or update a **Certification** subsection:
   - `--cert-ngc: #003366` (NGC navy)
   - `--cert-pcgs: #00529B` (PCGS blue)
   - `--cert-anacs: #8B0000` (ANACS dark red)
   - Prefer referencing these from cert badges; mention `--grade-ngc` / `--grade-pcgs` only as aliases of cert if you kept them in Step 2.
5. **Verify:** Doc values match `index.css` for grade-ms, rarity-r3, and cert-ngc/cert-pcgs. No contradictory hexes.

---

### Step 4 — Replace raw Tailwind in AIReviewTab with tokens  
**Issue:** HR-004

1. Open `frontend/src/components/review/AIReviewTab.tsx`.
2. Find classes that use `blue-500/10`, `blue-700`, `dark:blue-400`, `purple-500/10`, `purple-700`, `dark:purple-400` (or similar).
3. Replace with design tokens, e.g.:
   - “Source” / info-style badges → `var(--accent-ai-subtle)` background, `var(--accent-ai)` or `var(--text-link)` for text, or `var(--border-subtle)` if neutral.
   - If you keep “blue = API/model” and “purple = AI”: ensure corresponding vars exist in `index.css` (e.g. `--accent-ai`, `--accent-ai-subtle`) and use them instead of Tailwind color names.
4. **Verify:** AI Review tab renders with token-based colors; no `blue-500` or `purple-500` in that file. Contrast still OK.

---

### Step 5 — Replace raw Tailwind in ReviewQueuePage action buttons  
**Issue:** IF-004

1. Open `frontend/src/pages/ReviewQueuePage.tsx`.
2. Find icon buttons that use `text-green-600`, `hover:text-green-700`, `hover:bg-green-50` (accept) and `text-red-600`, `hover:text-red-700`, `hover:bg-red-50` (reject).
3. Replace with semantic tokens, e.g.:
   - Accept: `style={{ color: 'var(--text-success)' }}` or className using a utility that maps to `--text-success`; hover via `var(--bg-success)` or existing success utility.
   - Reject: same for `--text-error` / `--bg-error` (or destructive).
4. If no utility exists, add a small `.text-success` / `.text-error` (and hover bg) in `index.css` that use `var(--text-success)` / `var(--text-error)` and use those classes.
5. **Verify:** Accept/reject buttons still clearly green/red and meet contrast; no `green-600` or `red-600` in ReviewQueuePage.

---

### Step 6 — Update DESIGN-AUDIT-ISSUE-LOG and DESIGN-AUDIT-REPORT  
**Housekeeping**

1. In `docs/DESIGN-AUDIT-ISSUE-LOG.md`, set **Status** (or add a “Done” column) for:
   - VC-001, VC-002, VC-006 → Done  
   - HR-004, IF-004 → Done  
2. In `docs/DESIGN-AUDIT-REPORT.md`, add a short “Implementation status” note at the top:  
   - “Quick wins (Steps 1–5) completed on [date]. Cert cleanup, doc alignment, and AI/Review token swaps done.”
3. **Verify:** Issue log and report reflect current state so future work doesn’t redo these.

---

## Phase B — Medium-term (token & component consistency)

### Step 7 — Add CSS variables for typography scale  
**Addresses:** Typography inconsistencies called out in Phase 1

1. In `frontend/src/index.css`, inside `:root`, add:
   - `--font-size-xs: 0.75rem;`
   - `--font-size-sm: 0.875rem;`
   - `--font-size-base: 1rem;`
   - `--font-size-lg: 1.125rem;`
   - `--font-size-xl: 1.25rem;`
   - `--font-size-2xl: 1.5rem;`
   - `--font-size-3xl: 1.875rem;`
2. In `docs/ai-guide/10-DESIGN-SYSTEM.md`, add or update a “Font size tokens” table that lists these and points to `index.css`.
3. **Verify:** Variables exist and doc matches. No component changes required in this step; adoption is Step 8+.

---

### Step 8 — Prefer tokens in at least two high-traffic components  
**Addresses:** Drift between spec and code

1. Choose two components, e.g. **Card** (title/description) and **CoinCard** (ruler/legend).
2. In `CardTitle` / `CardDescription`: optionally replace Tailwind font size classes with `font-size: var(--font-size-2xl)` and `var(--font-size-sm)` if you keep a single source of truth in CSS.
3. In **CoinCard** (or the shared text block), use `var(--font-size-lg)` or `var(--font-size-xl)` for ruler, and `var(--font-size-sm)` or `var(--font-size-xs)` for legend/subtitle where it matches the spec.
4. **Verify:** No visual regressions; typography still matches 10-DESIGN-SYSTEM.

---

### Step 9 — Standardize empty-state presentation  
**Issue:** HR-001

1. Add a small “Empty state” section to `docs/ai-guide/10-DESIGN-SYSTEM.md` or `11-FRONTEND-COMPONENTS.md`:
   - Title: e.g. `text-xl font-semibold` (or `var(--font-size-xl)` + font-weight 600).
   - Description: `text-muted-foreground` or `var(--text-muted)`.
2. Optionally add a shared component `EmptyState` (title + description + optional illustration) and use it in CoinGridPage, ReviewQueuePage, and similar.
3. **Verify:** At least one of: (a) doc specifies empty-state tokens, or (b) one page uses a shared EmptyState component.

---

### Step 10 — Unify focus styling (outline vs ring)  
**Issue:** VC-005

1. In `frontend/src/index.css`, in the `:focus-visible` block, ensure the outline is at least 2px and clearly visible (e.g. `outline: 2px solid var(--ring)` or `var(--cat-imperial)`).
2. In shadcn **Button** (and optionally Input, Select): ensure `focus-visible:ring-2` uses `--ring` so it matches the same token. If you want one canonical focus color, set `--ring` to that value in `:root`.
3. **Verify:** Keyboard tab through buttons and inputs; focus indicator is consistent and visible.

---

## Phase C — Strategic (token source of truth & IA)

### Step 11 — Use design-tokens.json as the single source of truth  
**Strategic**

1. Decide format: keep `docs/design-tokens.json` as authoritative and either (a) generate Tailwind `theme.extend` from it, or (b) keep Tailwind and CSS in sync manually via a short “Sync tokens” section in 09-TASK-RECIPES or the dev guide.
2. If (a): add a small script (e.g. Node) that reads `design-tokens.json` and writes `tailwind.config.js` theme extend and/or a `tokens.css` fragment. Run it when tokens change.
3. If (b): in `docs/ai-guide/10-DESIGN-SYSTEM.md`, state that `docs/design-tokens.json` is canonical and `index.css` / `tailwind.config.js` must be updated to match when tokens change.
4. **Verify:** Either the build uses the generated config, or the doc clearly names the canonical token file and the sync process.

---

### Step 12 — URL ↔ filter sync for collection  
**Issue:** IA-002

1. Design: collection URL supports e.g. `?search=...&category=...&metal=...`; on load, read query and push into filterStore; on filter change, update URL (replace or pushState).
2. Implement in the collection router/page that mounts grid/table:
   - On mount: `useSearchParams()` or equivalent → parse `search`, `category`, `metal` → `filterStore.setSearch(...)` etc.
   - On filter change: update search params from filterStore (debounce if needed).
3. Ensure header/command-palette “search then go to collection” sets `?search=...` and navigates to `/collection/grid?search=...` so the collection page can read it (see UX-UI-EXPLORATION-REPORT).
4. **Verify:** Changing filters updates the URL; reloading with `?search=...` applies that search. No 404s or broken back/forward.

---

### Step 13 — Touch target audit (sidebar + icon buttons)  
**Issue:** IF-005

1. List interactive elements: sidebar nav items (collapsed = icon-only), header icon buttons, Review queue action icons, any other icon-only controls.
2. Measure or inspect: ensure each has a clickable area ≥ 44×44px (or document exceptions and rationale).
3. Fix: add padding or min-width/min-height so touch targets meet 44px, or use a “tap target” wrapper that extends the hit area.
4. **Verify:** Manual test or layout inspection shows ≥ 44px for those controls; document any deliberate exceptions in ACCESSIBILITY-CHECKLIST or the design audit report.

---

## Phase D — Optional / backlog

- **VC-003 (Badge systems):** Consolidate generic Badge vs MetalBadge/GradeBadge usage so semantic roles are clear and token usage is consistent.
- **VC-004 (Radius):** Standardize on when to use `rounded-lg` vs `rounded-md` and document in 10-DESIGN-SYSTEM.
- **IF-003 (Loading):** Introduce a shared skeleton pattern for card/table chunks and use it in grid and table loading states.
- **LS-001, LS-002:** Define a content max-width token and/or card padding token and adopt in key layouts.
- **Before/after mockups:** For Steps 1–5, optional one-pager with “before” (duplicate cert, raw Tailwind) vs “after” (single cert, tokens).

---

## Execution checklist

Use this as a tick list; update dates when done.

| Step | Phase | Description | Done (date) |
|------|-------|-------------|-------------|
| 1 | A | Remove duplicate cert block in index.css | Jan 2026 |
| 2 | A | Unify cert vs grade aliases | Jan 2026 |
| 3 | A | Align 10-DESIGN-SYSTEM with code (cert, grade-ms, rarity-r3) | Jan 2026 |
| 4 | A | Replace raw Tailwind in AIReviewTab | Jan 2026 |
| 5 | A | Replace raw Tailwind in ReviewQueuePage actions | Jan 2026 |
| 6 | A | Update issue log and audit report status | Jan 2026 |
| 7 | B | Add typography CSS variables | Jan 2026 |
| 8 | B | Use tokens in Card + CoinCard (or two chosen components) | Jan 2026 |
| 9 | B | Standardize empty-state (doc or component) | Jan 2026 |
| 10 | B | Unify focus styling (outline/ring) | Jan 2026 |
| 11 | C | design-tokens.json as single source of truth | Jan 2026 |
| 12 | C | URL ↔ filter sync for collection | Jan 2026 |
| 13 | C | Touch target audit (sidebar + icon buttons) | Jan 2026 |
| D1 | D | VC-004: Document rounded-lg vs rounded-md in 10-DESIGN-SYSTEM | Jan 2026 |
| D2 | D | LS-001/LS-002: Content max-width + card padding tokens | Jan 2026 |
| D3 | D | IF-003: Shared skeleton (TableRowSkeleton, doc) | Jan 2026 |
| D4 | D | VC-003: Badge usage doc in 11-FRONTEND-COMPONENTS | Jan 2026 |

---

## Dependency order

- **1 → 2:** Step 1 removes duplicate cert definitions; Step 2 cleans up grade/cert aliases against the single block.
- **1–2 → 3:** Doc (Step 3) should describe the final, single cert/grade state.
- **4, 5** can be done in any order; both are self-contained token swaps.
- **6** should be done after 1–5 so the issue log reflects “quick wins done.”
- **7 → 8:** Typography variables (7) before using them in components (8).
- **11** can be done anytime; 7–8 are nicer if tokens flow from 11 later.
- **12** is independent of A/B; **13** can follow B.

Recommended first run: **1 → 2 → 3 → 4 → 5 → 6**, then **7 → 8** when you’re ready for typography tokens.
