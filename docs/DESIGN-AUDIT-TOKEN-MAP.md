# Design Token Migration Map

**Purpose:** Map current values in code/CSS to canonical design tokens. Use when consolidating colors, typography, and spacing.

**Source:** DESIGN-AUDIT-REPORT.md Phase 3.  
**Target tokens:** `docs/design-tokens.json`.

---

## Color

| Current value / location | Occurrences / context | New token / action |
|-------------------------|------------------------|--------------------|
| `#1A73E8` (NGC, first block in index.css) | Overridden by later block | Remove; use `color.semantic.cert.ngc` = #003366 |
| `#003366` | Effective NGC in index.css (later block) | `color.semantic.cert.ngc` |
| `#00529B` | Effective PCGS in index.css (later block) | `color.semantic.cert.pcgs` |
| `#8B0000` | ANACS in index.css | `color.semantic.cert.anacs` |
| `#22c55e` / `#22C55E` | --health-good, --text-success | `color.semantic.feedback.success` |
| `#EF4444` | --text-error, --perf-negative, destructive | `color.semantic.feedback.error` |
| `#EAB308` | --text-warning, --health-warning | `color.semantic.feedback.warning` |
| `#F5F5F7` | --text-primary | `color.semantic.text.primary` |
| `#D1D5DB` | --text-secondary | `color.semantic.text.secondary` |
| `#9CA3AF` | --text-muted, --perf-neutral | `color.semantic.text.muted` |
| `#6B7280` | --text-ghost | `color.semantic.text.ghost` |
| `#050814` | --bg-app | `color.semantic.background.app` |
| `#0B1020` | --bg-elevated | `color.semantic.background.elevated` |
| `#0F1526` | --bg-card | `color.semantic.background.card` |
| `blue-500/10`, `purple-500/10` (Tailwind in AIReviewTab) | Ad-hoc badges | Replace with semantic tokens or new `--accent-ai-*` vars |
| `green-600`, `red-600` (ReviewQueuePage actions) | Icon buttons | `color.semantic.feedback.success` / `error` |

---

## Typography

| Current value | Occurrences / context | New token / action |
|---------------|------------------------|--------------------|
| 14px / 0.875rem | Body, inputs, CardDescription, text-sm | `typography.fontSize.sm` (0.875rem) |
| 12px / 0.75rem | Legends, small labels, text-xs | `typography.fontSize.xs` (0.75rem) |
| 10px | Design spec badges, MetalBadge sm | New token `typography.fontSize.2xs` or keep 10px only in MetalBadge |
| 17px | CoinCard ruler (title) | Design token “ruler” or `typography.fontSize.lg` (1.125rem ≈ 18px) — or keep 17px as custom |
| 1.5rem (24px) | CardTitle text-2xl | `typography.fontSize.2xl` |
| 1.875rem (30px) | ReviewQueuePage h1 text-3xl | `typography.fontSize.3xl` |
| Inter | body font-family | `typography.fontFamily.sans` |
| Cinzel | Legends (spec) | `typography.fontFamily.legends` |
| JetBrains Mono | References | `typography.fontFamily.mono` |

---

## Spacing

| Current value | Occurrences / context | New token / action |
|---------------|------------------------|--------------------|
| p-6 (24px) | CardHeader, CardContent | `spacing.6` (1.5rem) |
| px-4 py-2 | Button default | `spacing.4` horizontal, `spacing.2` vertical |
| px-2.5 py-2 | Sidebar nav item | Keep or align to spacing.2 / 2.5 |
| gap-2 (8px) | Badge row, flex gaps | `spacing.2` |
| gap-3 (12px) | Sidebar item gap | `spacing.3` |
| gap-4 (16px) | Table cell, sections | `spacing.4` |
| 12px 14px 12px 16px | CoinCard content (spec) | Consider spacing tokens: 3 3.5 3 4 (rem) or keep as card-specific |

---

## Radius

| Current value | Occurrences / context | New token / action |
|---------------|------------------------|--------------------|
| 0.5rem (--radius) | Tailwind lg, base | `radius` (0.5rem) |
| calc(var(--radius) - 2px) | Tailwind md | `borderRadius.md` |
| calc(var(--radius) - 4px) | Tailwind sm | `borderRadius.sm` |
| rounded-lg | Card, panels | `borderRadius.lg` |
| rounded-md | Buttons, inputs | `borderRadius.md` |
| rounded-full | Badge | `borderRadius.full` |

---

## Implementation notes

1. **CSS-first:** Prefer adding/using CSS variables in `index.css` that mirror `design-tokens.json`, then reference them in Tailwind and components.
2. **Cert cleanup:** Remove the first certification block in `index.css` (or the second), then point design doc and components at the single remaining set.
3. **Replace ad-hoc Tailwind:** In AIReviewTab and ReviewQueuePage, swap `blue-500/10`, `green-600`, `red-600` for `var(--...)` semantic tokens.
