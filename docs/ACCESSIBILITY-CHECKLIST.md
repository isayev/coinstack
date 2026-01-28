# CoinStack Accessibility (a11y) Checklist

Use this checklist for manual and tool-assisted audits. It complements the UX/UI report and focuses on WCAG 2.1 Level AA–oriented checks.

---

## 1. Keyboard Navigation

| # | Check | Pass? | Notes |
|---|-------|-------|--------|
| 1.1 | All interactive elements reachable via Tab (no traps). | | |
| 1.2 | Tab order matches visual order (no `tabindex` > 0 without reason). | | |
| 1.3 | Enter/Space activates buttons and links; Space does not scroll when focus is on a button. | | |
| 1.4 | Command Palette (⌘K): opens with keyboard, focus moves into dialog, Esc closes and returns focus. | | |
| 1.5 | Command Palette: arrow keys move between items, Enter selects. | | |
| 1.6 | Modals/dialogs (Add Coin, Delete confirm, Scrape, etc.): focus trapped inside; Esc or explicit Close returns focus to trigger. | | |
| 1.7 | Grid/table: arrow keys or Tab move between cards/rows if they are in tab order; or “skip to content” / “next page” is available. | | |
| 1.8 | Sidebar: each nav item is focusable and activatable with Enter/Space. | | |
| 1.9 | No “keyboard inaccessible” custom controls (e.g. div with onClick but no role/button). | | |

**Components to test:** `CommandPalette`, `Sidebar`, `BulkActionsBar` (delete dialog), `CoinForm` steps, `ScrapeDialog`, `QuickScrapePopover`, `CertLookupPopover`, collection grid/table cards.

---

## 2. Focus Management

| # | Check | Pass? | Notes |
|---|-------|-------|--------|
| 2.1 | Focus visible on all focusable elements (ring/outline, not only on mouse hover). | | |
| 2.2 | Focus style has at least 2 px and sufficient contrast (or follow `:focus-visible` spec). | | |
| 2.3 | After submit (e.g. Add Coin, Save Edit): focus moves to a logical target (e.g. first field of new form, or “View coin” link). | | |
| 2.4 | After closing a modal: focus returns to element that opened it. | | |
| 2.5 | Skip link “Skip to main content” present and works when applicable. | | |

---

## 3. Screen Reader (ARIA & Semantics)

| # | Check | Pass? | Notes |
|---|-------|-------|--------|
| 3.1 | Every icon-only button has `aria-label` or visible text (e.g. sidebar collapse, trash, external link). | | |
| 3.2 | Form inputs have associated `<label>` or `aria-label` / `aria-labelledby`. | | |
| 3.3 | Required fields and errors: `aria-required`, `aria-invalid`, `aria-describedby` pointing to error text. | | |
| 3.4 | Headings form a logical outline (single h1 per view; h2/h3 order). | | |
| 3.5 | Custom widgets (combobox, tabs, dialogs): correct `role`, `aria-expanded`, `aria-controls`, `aria-selected` where applicable. | | |
| 3.6 | Toasts: announced (e.g. `role="status"` or `aria-live="polite"`). | | |
| 3.7 | Loading states: “Loading…” or equivalent exposed (e.g. `aria-busy="true"` or live region). | | |
| 3.8 | Empty states (e.g. “No coins found”) are in the accessibility tree and not only decorative. | | |

**Components:** `CoinForm` (steps + fields), `VocabAutocomplete`, `Tabs` (Details / Audit, Review tabs), Sonner/Toaster, `CoinCard`/grid, `ReviewEmptyState`.

---

## 4. Color & Contrast

| # | Check | Pass? | Notes |
|---|-------|-------|--------|
| 4.1 | Text (and icons used as info): ≥ 4.5:1 against background (large text ≥ 3:1). | | |
| 4.2 | Metal tokens (gold, silver, bronze, etc.) on cards/badges: contrast on `--bg-card` / `--bg-elevated` meets AA. | | |
| 4.3 | Category bar colors: contrast and/or not the only way to convey category (text/label also present). | | |
| 4.4 | Grade/cert badges: contrast and legibility. | | |
| 4.5 | Error/destructive text and borders: distinguishable and sufficient contrast. | | |
| 4.6 | Focus ring: visible against both light and dark backgrounds. | | |

**Tokens to verify:** `--metal-au`, `--metal-ag`, `--metal-ar`, `--metal-ae`, `--text-primary`, `--text-muted`, `--destructive`, `--border-subtle`, `--bg-card`, `--bg-elevated`.

---

## 5. Motion & Flashing

| # | Check | Pass? | Notes |
|---|-------|-------|--------|
| 5.1 | No content that flashes more than 3 times per second (or allow “reduce motion”). | | |
| 5.2 | Prefer `prefers-reduced-motion` for non-essential animations (e.g. card flip, transitions). | | |

---

## 6. Forms & Errors

| # | Check | Pass? | Notes |
|---|-------|-------|--------|
| 6.1 | Submit errors (e.g. “Validation Failed”) are associated with fields or summarized in an announced region. | | |
| 6.2 | Inline validation errors are announced (e.g. when invalid on blur/submit). | | |
| 6.3 | Required fields are clearly indicated (label or aria). | | |
| 6.4 | Date/year inputs (BC/AD): format and expectations clear (placeholders, labels). | | |

---

## 7. Mobile / Touch (if in scope)

| # | Check | Pass? | Notes |
|---|-------|-------|--------|
| 7.1 | Touch targets ≥ 44×44 px where possible. | | |
| 7.2 | Command Palette or “Search” reachable on mobile (not only ⌘K). | | |
| 7.3 | No essential actions hidden behind hover-only UI. | | |

---

## Quick Test Stack

- **Keyboard:** Navigate collection → Add Coin → fill one step → next → submit; open Command Palette → type → pick item; trigger bulk delete → confirm/cancel.
- **Screen reader:** NVDA (Windows) or VoiceOver (macOS) on same flows; check announcements for toasts, errors, empty states.
- **Contrast:** DevTools or axe DevTools / Contrast checker on metal badges, category bars, and error states.
- **Automated:** axe-core or pa11y on critical routes (/, /coins/new, /coins/1, /review).

---

## References

- [WCAG 2.1 Level AA](https://www.w3.org/WAI/WCAG21/quickref/?currentsidebar=%23col_customize&levels=aaa)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [MDN :focus-visible](https://developer.mozilla.org/en-US/docs/Web/CSS/:focus-visible)
