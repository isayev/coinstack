# CoinStack UI/UX Design Audit & Consolidation Report

**Date:** January 28, 2026  
**Scope:** Full design audit per systematic visual inventory, problem identification, token specification, and consolidation.  
**Focus areas:** Collection grid/table, coin detail/edit forms, filter/search, review queue, series, controlled vocabulary surfaces.  
**Sources:** Codebase (`frontend/src`, `index.css`, `tailwind.config.js`), design docs (`10-DESIGN-SYSTEM.md`, `design/`), browser review of http://localhost:3000.

**Implementation status:** Phase A–D completed Jan 2026. Quick wins: cert cleanup, doc alignment, AIReviewTab/ReviewQueuePage tokens. Phase B: typography CSS variables, Card/CoinCard tokens, empty-state spec, focus on `--ring`. Phase C: design-tokens.json as canonical; URL↔filter sync; touch targets ≥44px. Phase D: VC-004 radius usage doc; LS-001/LS-002 tokens (`--content-max-width`, `--card-content-padding-*`) in index.css + 10-DESIGN-SYSTEM; IF-003 TableRowSkeleton + loading pattern doc; VC-003 badge usage table in 11-FRONTEND-COMPONENTS. See [DESIGN-AUDIT-IMPLEMENTATION-PLAN.md](DESIGN-AUDIT-IMPLEMENTATION-PLAN.md) and [DESIGN-AUDIT-ISSUE-LOG.md](DESIGN-AUDIT-ISSUE-LOG.md).

---

## PHASE 1: Systematic Visual Inventory

### 1.1 Typography Inventory

| Source | Font family | Usage |
|--------|-------------|--------|
| `index.css` | Inter (300–700) | Body, UI; primary |
| `index.css` | JetBrains Mono (400–700) | References, catalog numbers |
| `index.css` | EB Garamond (400–600, italic) | Legible serif option |
| `index.css` | Cinzel (400–700) | Legends, classical feel (design spec) |
| `tailwind` | (default sans) | Via `font-sans` → Inter |

**Font sizes (extracted):**

| Value | Where | Purpose |
|-------|-------|---------|
| 8px | Design spec (badges) | Badge text, microcopy |
| 9px | Design spec | Catalog refs (mono) |
| 10px | Design spec, MetalBadge sm | Legends, small labels |
| 10px / text-[10px] | MetalBadge `sm` | Desktop-only badge |
| 11px | CoinCard `fontSize.legend` | OBV/REV legends |
| 12px | CoinCard `fontSize.subtitle`, table caption | Secondary text |
| 12px | Table `text-sm` (Tailwind ≈ 14px) | Table body (Tailwind sm = 0.875rem) |
| 14px | Design spec `--font-size-base` | Body (spec) |
| 0.875rem (14px) | Tailwind `text-sm`, CardDescription, Input | Body/small UI |
| 1rem (16px) | Tailwind `text-base` | Base body |
| 15px / 17px | CoinCard `fontSize.title` | Ruler name (17px spec) |
| 1.25rem (20px) | CardTitle `text-2xl` | Section titles |
| 1.5rem (24px) | CardTitle `text-2xl` | Card titles |
| text-xl | Various | 1.25rem |
| text-2xl | CardTitle | 1.5rem |
| text-3xl | ReviewQueuePage h1 | 1.875rem |
| text-6xl | CoinGridPage empty emoji | Decorative |

**Font weights:** 300, 400, 500, 600, 700 (Inter); 400–700 (JetBrains Mono, Cinzel).  
**Line-heights:** 1.2, 1.3, 1.5 (Tailwind leading-tight/normal/relaxed), `leading-none` on CardTitle.  
**Letter-spacing:** `tracking-tight` (CardTitle), `tracking-wide` (MarkdownContent).

**Inconsistencies:**

- Design doc `--font-size-xs: 8px` etc. are not defined as CSS variables; components use px, Tailwind, or inline styles.
- Same semantic “small label” uses 10px (spec), `text-xs` (Tailwind 12px), and `text-sm` (14px) in different components.
- CardTitle uses `text-2xl` (1.5rem) while design spec suggests `--font-size-xxl: 20px` for page titles — close but not tokenized.

### 1.2 Color Inventory

**Base / surfaces (from `index.css`):**

- `--bg-app`: #050814  
- `--bg-elevated`: #0B1020  
- `--bg-card`: #0F1526  
- `--bg-hover`: #1A1F35  
- `--bg-subtle`: #14192a  

**Text:**

- `--text-primary`: #F5F5F7  
- `--text-secondary`: #D1D5DB  
- `--text-muted`: #9CA3AF  
- `--text-ghost`: #6B7280  

**Borders:**

- `--border-subtle`: rgba(148,163,184,0.18)  
- `--border-strong`: rgba(148,163,184,0.40)  

**Shadcn/HSL mapping:** `--background`, `--foreground`, `--card`, `--primary` (45 100% 50%), `--muted`, `--accent`, `--destructive`, `--border`, `--input`, `--ring` — all via `hsl(var(...))` in Tailwind.

**Semantic / feedback:**

- Success: `--text-success` #22c55e, `--bg-success`, `--border-success`  
- Warning: `--text-warning` #eab308, `--bg-warning`, `--border-warning`  
- Error: `--text-error` #ef4444, `--bg-error`, `--border-error`  
- Performance: `--perf-positive` #10B981, `--perf-negative` #EF4444, `--perf-neutral` #9CA3AF  

**Duplicate/override in same file:** Certification block appears twice. First (≈249–251): `--cert-ngc: #1A73E8`, `--cert-pcgs: #2E7D32`. Second (≈341–346): `--cert-ngc: #003366`, `--cert-pcgs: #00529B` — **later block wins**. Effective values: NGC #003366, PCGS #00529B.

**“Almost identical”:** `--cat-other` / `--unknown` / `--grade-unknown` = #6e6e73 (intentional shared neutral).  
**Health vs semantic:** `--health-good` #22C55E vs `--text-success` #22c55e — same hue, can be unified.

### 1.3 Spacing Inventory

| Value | Tailwind | Where |
|-------|----------|--------|
| 0 | 0, p-0, m-0 | Resets |
| 2px | (custom) | CoinCard legend gap |
| 0.25rem (4px) | p-1, m-1, gap-1 | Badge padding, tight gaps |
| 0.5rem (8px) | p-2, m-2, gap-2, rounded-md | Sidebar nav, buttons |
| 0.75rem (12px) | p-3, gap-3 | Sidebar item gap |
| 1rem (16px) | p-4, m-4, gap-4 | Table cell px-4, spacing |
| 1.5rem (24px) | p-6 | Card padding (CardHeader/CardContent p-6) |
| 2rem (32px) | - | - |
| 3rem (48px) | - | Sidebar w-48 |

**Gaps:** `gap-1` (4px), `gap-2` (8px), `gap-3` (12px), `gap-4` (16px) used widely.  
**Inconsistencies:** Card uses `p-6` (24px); CoinCard content uses 12px 14px 12px 16px in spec — implementation uses mixed Tailwind and inline padding. No single 4/8px grid token set; Tailwind scale is followed loosely.

### 1.4 Component Inventory

**Buttons (shadcn):** default, destructive, outline, secondary, ghost, link; sizes default (h-10 px-4 py-2), sm (h-9 px-3), lg (h-11 px-8), icon (h-10 w-10). Base: `text-sm font-medium rounded-md`, focus-visible ring.

**Form inputs:** Input h-10, rounded-md, border-input, px-3 py-2, text-sm; label/textarea/select use same token set.  
**Cards:** Card rounded-lg border bg-card; CardHeader/CardContent p-6; CardTitle text-2xl font-semibold; CardDescription text-sm text-muted-foreground.

**Navigation:** Sidebar w-48 (open) / w-14 (collapsed); nav item px-2.5 py-2, gap-3; active indicator 0.5×h-5; inline `var(--bg-elevated)`, `var(--border-subtle)`, `var(--metal-au)` for active.

**Tables:** Table text-sm; TableHead h-12 px-4, font-medium text-muted-foreground; TableCell p-4; TableRow border-b, hover:bg-muted/50.

**Badges:** Badge rounded-full px-2.5 py-0.5 text-xs font-semibold; variants default, secondary, destructive, outline, plus metal/grade (gold, silver, bronze, grade-ms, grade-au, etc.). MetalBadge has sm/md/lg (28×22, 36×28, 44×44) with design-system tokens.

**Modals/dialogs:** shadcn Dialog/Sheet; no single max-width token referenced in audit.  
**Icons:** Lucide; sizes w-4 h-4, w-5 h-5, w-8 h-8 common. No second icon set.

---

## PHASE 2: Design Problem Identification

### 2.1 Visual Consistency Issues

| ID | Location | Description | Severity |
|----|----------|-------------|----------|
| VC-001 | `index.css` | Certification colors defined twice; latter block overrides (NGC/PCGS differ from first block). | 4 |
| VC-002 | Design doc vs code | 10-DESIGN-SYSTEM says grade-ms #DC2626, rarity-r3 #F59E0B; code uses --grade-ms #FF6B6B, --rarity-r3 #EF4444. | 3 |
| VC-003 | Badges | Generic Badge uses Tailwind semantic names (primary, secondary); MetalBadge/GradeBadge use CSS vars. Two systems for “badge”. | 2 |
| VC-004 | Radius | Tailwind lg = var(--radius), md = calc(var(--radius)-2px), sm = calc(-4px). Card uses rounded-lg; some panels use rounded-md. Mixed. | 2 |
| VC-005 | Focus ring | Base uses `outline: 2px solid var(--cat-imperial)`; shadcn uses ring-ring. Different visual focus treatment. | 2 |
| VC-006 | Cert tokens | grade-ngc/grade-pcgs vs cert-ngc/cert-pcgs both exist; cert-* overridden later. Confusing for maintainers. | 4 |

### 2.2 Hierarchy & Readability

| ID | Location | Description | Severity |
|----|----------|-------------|----------|
| HR-001 | Empty states | “No coins” uses text-xl font-semibold + text-muted-foreground; hierarchy is clear but could use a single “empty state title” token. | 1 |
| HR-002 | ReviewQueuePage | h1 “Review Queue” text-3xl font-bold; body text-sm text-muted-foreground — good. | 0 |
| HR-003 | Tables | TableHead text-muted-foreground, TableCell default — adequate. Dense tables (CoinTableRow 18 cols) may need row hover/selected state more visible. | 2 |
| HR-004 | AIReviewTab | Badges use blue-500/10 and purple-500/10 — raw Tailwind, not design tokens. | 3 |

### 2.3 Interaction & Feedback

| ID | Location | Description | Severity |
|----|----------|-------------|----------|
| IF-001 | Buttons | Hover/disabled from Tailwind; focus-visible ring present. | 0 |
| IF-002 | CoinCard | Hover lift -2px, shadow; 3D flip on image — good. | 0 |
| IF-003 | Loading | Loader2 + animate-spin used; no skeleton for card/table chunks in same pattern everywhere. | 2 |
| IF-004 | Review queue actions | Green/red icon buttons use Tailwind green-600/red-600 instead of semantic tokens. | 2 |
| IF-005 | Touch targets | MetalBadge lg = 44px; sidebar nav and some icon-only buttons may be &lt; 44px. | 3 |

### 2.4 Layout & Spacing

| ID | Location | Description | Severity |
|----|----------|-------------|----------|
| LS-001 | Card padding | Spec 12px 14px 12px 16px; Tailwind Card uses p-6 (24px). Different contexts. | 2 |
| LS-002 | Content width | No single max-width token for main content; pages use different wrappers. | 2 |
| LS-003 | Grid | CoinGridPage uses responsive grid; breakpoints from Tailwind + 3xl/4xl/5xl. Doc grid column counts listed but not enforced by tokens. | 1 |

### 2.5 Information Architecture

| ID | Location | Description | Severity |
|----|----------|-------------|----------|
| IA-001 | Review vs Audit | /audit redirects to /review; “Run Audit” in UI — clear in code, ok for users. | 0 |
| IA-002 | Filters | Collection filters in sidebar/toolbar; search and URL not synced (see UX-UI-EXPLORATION-REPORT). | 3 |
| IA-003 | Badge order | Design spec [Cert][Grade][Metal][Rarity●] — implemented in CoinCard/CoinTableRow. | 0 |

---

## PHASE 3: Design Token Specification

Production-oriented token set below. Values are taken from **current** `index.css` and `tailwind.config.js`; semantic names are normalized. Certification uses the **effective** (later) definitions: NGC #003366, PCGS #00529B.

### 3.1 Design Tokens JSON (excerpt — full file separate)

```json
{
  "color": {
    "primitive": {
      "gray": {
        "50": {"value": "#fafafa"},
        "100": {"value": "#f5f5f5"},
        "200": {"value": "#e5e5e5"},
        "300": {"value": "#d4d4d4"},
        "400": {"value": "#a3a3a3"},
        "500": {"value": "#737373"},
        "600": {"value": "#525252"},
        "700": {"value": "#404040"},
        "800": {"value": "#262626"},
        "900": {"value": "#171717"}
      },
      "brand": {
        "primary": {"value": "hsl(45 100% 50%)"},
        "gold": {"value": "#FFD700"}
      }
    },
    "semantic": {
      "background": {
        "app": {"value": "#050814"},
        "elevated": {"value": "#0B1020"},
        "card": {"value": "#0F1526"},
        "hover": {"value": "#1A1F35"},
        "subtle": {"value": "#14192a"}
      },
      "text": {
        "primary": {"value": "#F5F5F7"},
        "secondary": {"value": "#D1D5DB"},
        "muted": {"value": "#9CA3AF"},
        "ghost": {"value": "#6B7280"}
      },
      "border": {
        "subtle": {"value": "rgba(148, 163, 184, 0.18)"},
        "strong": {"value": "rgba(148, 163, 184, 0.40)"}
      },
      "feedback": {
        "success": {"value": "#22C55E"},
        "warning": {"value": "#EAB308"},
        "error": {"value": "#EF4444"},
        "info": {"value": "#3B82F6"}
      },
      "cert": {
        "ngc": {"value": "#003366"},
        "pcgs": {"value": "#00529B"},
        "anacs": {"value": "#8B0000"}
      }
    }
  },
  "typography": {
    "fontFamily": {
      "sans": {"value": "Inter, -apple-system, BlinkMacSystemFont, sans-serif"},
      "mono": {"value": "JetBrains Mono, monospace"},
      "legends": {"value": "Cinzel, serif"}
    },
    "fontSize": {
      "xs": {"value": "0.75rem"},
      "sm": {"value": "0.875rem"},
      "base": {"value": "1rem"},
      "lg": {"value": "1.125rem"},
      "xl": {"value": "1.25rem"},
      "2xl": {"value": "1.5rem"},
      "3xl": {"value": "1.875rem"}
    },
    "fontWeight": {
      "normal": {"value": "400"},
      "medium": {"value": "500"},
      "semibold": {"value": "600"},
      "bold": {"value": "700"}
    },
    "lineHeight": {
      "tight": {"value": "1.25"},
      "normal": {"value": "1.5"},
      "relaxed": {"value": "1.75"}
    }
  },
  "spacing": {
    "0": {"value": "0"},
    "1": {"value": "0.25rem"},
    "2": {"value": "0.5rem"},
    "3": {"value": "0.75rem"},
    "4": {"value": "1rem"},
    "6": {"value": "1.5rem"},
    "8": {"value": "2rem"}
  },
  "borderRadius": {
    "none": {"value": "0"},
    "sm": {"value": "calc(var(--radius) - 4px)"},
    "md": {"value": "calc(var(--radius) - 2px)"},
    "lg": {"value": "var(--radius)"},
    "full": {"value": "9999px"}
  },
  "radius": {"value": "0.5rem"}
}
```

### 3.2 Token Mapping Table (current → canonical)

| Current value | Occurrences / context | New token / note |
|---------------|------------------------|------------------|
| #1A73E8 (NGC first block) | Overridden by later block | Remove; use cert.ngc #003366 |
| #003366 | Effective NGC in CSS | color.semantic.cert.ngc |
| #00529B | Effective PCGS in CSS | color.semantic.cert.pcgs |
| #22c55e / #22C55E | health-good, text-success | color.semantic.feedback.success |
| 14px / 0.875rem | Body, inputs, labels | typography.fontSize.sm |
| 12px | Legends, small labels | typography.fontSize.xs or new token “xs2” 12px |
| 17px | CoinCard ruler | typography.fontSize.lg or custom “ruler” |
| text-2xl | Card titles | typography.fontSize.2xl |
| p-6 | Card padding | spacing.6 |
| px-4 py-2 | Button default | spacing.4 horizontal, spacing.2 vertical |

---

## PHASE 4: Design Overhaul Opportunities

### 4.1 Quick Wins

1. **Remove duplicate cert block in `index.css`** — Keep one “Certification” section; use effective values (#003366, #00529B, #8B0000) and document in 10-DESIGN-SYSTEM.
2. **Align 10-DESIGN-SYSTEM with code** — Update grade-ms, rarity-r3, cert-ngc/cert-pcgs to match `index.css` (or change code to match spec and remove override).
3. **Replace raw Tailwind in AIReviewTab / ReviewQueuePage** — Use `var(--text-success)`, `var(--text-error)`, or semantic badge tokens instead of blue-500/10, green-600, red-600.
4. **Standardize “empty state”** — One component or token set for title (e.g. text-xl font-semibold) + description (text-muted-foreground).

### 4.2 Medium-Term

1. **Typography tokens** — Add CSS variables for --font-size-xs, --font-size-sm, --font-size-base, --font-size-lg, --font-size-xl, --font-size-xxl and use them in CoinCard, badges, and forms.
2. **Single badge system** — Prefer design-system MetalBadge/GradeBadge/CertBadge + semantic Badge variants; reduce ad-hoc Tailwind color classes.
3. **Loading and skeletons** — Reusable skeleton for card/table rows and align Loader2 placement/size with a “loading” token.
4. **Touch targets** — Audit icon-only buttons and nav items; ensure ≥44px where needed (e.g. sidebar when collapsed).

### 4.3 Strategic Recommendations

**Recommendation: Consolidate certification and grade tokens**

- **Current:** Two certification blocks in CSS; grade-ngc/grade-pcgs and cert-ngc/cert-pcgs overlap; design doc out of sync.
- **Proposed:** One canonical set: `--cert-ngc`, `--cert-pcgs`, `--cert-anacs` (and -subtle). Use only these for cert badges. Remove grade-ngc/grade-pcgs or alias them to cert-*.
- **Impact:** Clearer maintenance; no cascade surprises.
- **Complexity:** Low.
- **Dependencies:** None.

**Recommendation: URL ↔ filter sync for collection**

- **Current:** Search in header/command palette does not persist to collection filters or URL (see UX-UI-EXPLORATION-REPORT).
- **Proposed:** Sync `?search=`, and optionally category/metal, to filterStore and URL on collection; restore from URL on load.
- **Impact:** Better IA and shareable/bookmarkable collection views.
- **Complexity:** Medium.
- **Dependencies:** filterStore + router.

**Recommendation: Design tokens as single source of truth**

- **Current:** Tokens live in CSS and Tailwind config; design doc is prose + snippets.
- **Proposed:** Maintain one design-tokens.json (or CSS custom property set) and generate Tailwind theme extend and doc tables from it.
- **Impact:** No drift between code and docs; easier theming.
- **Complexity:** Medium (build step or manual sync).
- **Dependencies:** Build pipeline or script.

### 4.4 Accessibility Audit Summary (from CHECKLIST + audit)

- **Contrast:** Base palette (--text-primary on --bg-app, etc.) is dark-theme; contrast should be checked for AA/AAA (see ACCESSIBILITY-CHECKLIST §4).
- **Focus:** :focus-visible uses 2px outline (var(--cat-imperial)); shadcn ring may differ — unify and ensure ≥2px.
- **Labels/ARIA:** Form inputs and icon buttons need consistent aria-label / labelledby (checklist §3).
- **Touch targets:** MetalBadge lg meets 44px; other controls need audit (checklist implied in §4 / touch).
- **Loading/empty:** Expose loading and empty states to assistive tech (aria-busy, live regions) per checklist §3.6–3.8.

---

## PHASE 5: Deliverables Checklist

| Artifact | Location / status |
|----------|-------------------|
| Visual inventory (typography, color, spacing, components) | §1.1–1.4 above |
| Issue log (with severity) | §2.1–2.5 tables |
| Design tokens JSON (excerpt) | §3.1; full token file: `docs/design-tokens.json` (see below) |
| Token migration map | §3.2 |
| Component audit (buttons, inputs, cards, badges, tables) | §1.4, §2 |
| Recommendations (quick / medium / strategic) | §4.1–4.3 |
| Accessibility summary | §4.4 |

Before/after mockups are recommended as a follow-up (e.g. cert color fix, AI review badges, empty state) once quick wins are implemented.

---

## References

- `docs/ai-guide/10-DESIGN-SYSTEM.md` — Design system spec
- `docs/UX-UI-EXPLORATION-REPORT.md` — UX flows, search, API mismatch
- `docs/ACCESSIBILITY-CHECKLIST.md` — a11y checks
- `frontend/src/index.css` — Current CSS tokens
- `frontend/tailwind.config.js` — Theme extend
