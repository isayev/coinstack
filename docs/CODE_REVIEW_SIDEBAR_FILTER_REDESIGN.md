# Code Review: Sidebar Filter Badge Redesign + Grade/Stats Fixes

**Scope**: Filter chip redesign (Category, Grade, Rarity, Ruler), FilterChips.tsx, CollectionSidebar.tsx, useCoins.ts, docs; stats router tier-based grade filter and mint_year param alignment; v2 coins year param alignment.  
**Review date**: January 2026

---

## 1. Summary of Changes

| Area | Change |
|------|--------|
| **Design system** | New `FilterChips.tsx`: CategoryChip, GradeChip, RarityChip (badge + count, design tokens, selected ring). |
| **CollectionSidebar** | Category/Grade/Rarity filters use chip layout; Ruler expanded by default, top 12 chips; Mint/Year/Attributes chip styling aligned. |
| **useCoins** | Rarity counts key normalized so backend "Very Rare" → `very_rare` (matches RARITY_OPTIONS). |
| **FilterSection** | Nested button fixed: header is a div with separate toggle and Clear buttons (a11y + valid HTML). |
| **FilterChips** | `aria-pressed` on toggle chips for screen readers. |
| **Docs** | 10-DESIGN-SYSTEM.md § 4.7, 11-FRONTEND-COMPONENTS.md § 3.5. |

---

## 2. Fixes Applied During Review

### 2.1 Rarity counts key mismatch (bug)

- **Issue**: `useCollectionStats()` built `rarity_counts` with `curr.rarity.toLowerCase()` only, so "Very Rare" → `"very rare"` (space). CollectionSidebar uses `RARITY_OPTIONS = ['common', 'scarce', 'rare', 'very_rare', 'extremely_rare', 'unique']`, so `counts["very_rare"]` was always undefined and "Very Rare" chips never showed.
- **Fix**: In `useCoins.ts`, normalize rarity key: lowercase, trim, and replace spaces with underscores (`very rare` → `very_rare`). Aggregate counts per normalized key so multiple backend variants (e.g. "Very Rare" and "very_rare") sum correctly.

### 2.2 Invalid HTML / accessibility: button inside button

- **Issue**: FilterSection had a `<button>` (section toggle) containing another `<button>` (Clear). Nested interactive controls are invalid and break assistive tech and keyboard behavior.
- **Fix**: Replaced outer control with a `<div className="flex items-center justify-between py-2">` containing (1) a `<button>` for expand/collapse (with `aria-expanded`) and (2) a separate `<button>` for Clear. Both `type="button"`.

### 2.3 Accessibility: filter chips

- **Enhancement**: CategoryChip, GradeChip, and RarityChip now set `aria-pressed={selected}` so screen readers announce toggle state. Count spans left visible to SR (no `aria-hidden`).

---

## 3. Review by File

### 3.1 `frontend/src/components/design-system/FilterChips.tsx`

**Strengths**

- Clear split: CategoryChip, GradeChip, RarityChip with shared constants (`CHIP_BASE`, `SELECTED_RING`, `SELECTED_BOX_SHADOW`).
- Uses existing design tokens; no new CSS variables.
- RarityChip accepts both backend keys (`common`, `very_rare`) and RarityType (`c`, `r1`) via `rarityValueToType()`.
- Safe fallbacks: CategoryChip uses `config?.cssVar ?? 'other'` and `config?.label ?? category` when config is missing.

**Notes**

- **DRY**: Selected ring + boxShadow duplicated with MetalChip. Could be a shared hook or small util (e.g. `getChipSelectedStyle(selected)`) in a follow-up; not required for this change.
- **GradeChip**: `GRADE_LABELS` duplicates labels that exist in CollectionSidebar’s `GRADE_FILTER_CONFIG`. Single source of truth could live in `colors.ts` or a shared constant; current duplication is minor and localized.
- **RarityChip** `rarityValueToType`: Order of checks (r3 before r2 before r1, etc.) is correct. "rare" mapping to `r1` is intentional; "very" alone would match r2, so `v?.includes('very')` is correct.

**Edge cases**

- Category: If a future category is not in `CATEGORY_CONFIG`, `cssVar` falls back to `'other'` and `--category-other` / `--category-other-subtle` exist in `index.css`. Safe.
- Rarity: Unknown backend value falls back to `'c'` (common). Acceptable default.

### 3.2 `frontend/src/components/coins/CollectionSidebar.tsx`

**Strengths**

- Metal, Category, Grade, Rarity filters use the same pattern: `flex flex-wrap gap-1.5` + chip components; empty state message when no options.
- Ruler: Design-token chips, `defaultOpen={true}`, top 12, truncation with `title`, Unknown Ruler chip same style as others.
- Mint/Year/Attributes: Unknown Mint/Year in `flex flex-wrap gap-1.5`; Attributes use same chip padding and selected boxShadow (grade-fine / rarity-r3).
- FilterSection no longer uses nested buttons; layout and a11y improved.

**Notes**

- **FilterSection**: Toggle button uses `flex-1 min-w-0` so long titles don’t push Clear off; Clear is `flex-shrink-0`. Good.
- **Ruler chips**: `max-w-[140px] truncate` on the button; ruler name in inner `<span className="truncate">`. Redundant but harmless; could keep only on the inner span if desired.
- **Grade comment**: "Grade - NEW temperature-scale design" could be shortened to "Grade" now that design is established; optional cleanup.

**Data flow**

- `categoryCounts`, `gradeCounts`, `rarityCounts` from `useCollectionStats()`; keys match DISPLAY_CATEGORIES, GRADE_FILTER_CONFIG tiers, and RARITY_OPTIONS. Category keys are mapped in useCoins via `mapCategoryToKey`; grade via `getGradeTier`; rarity now via normalized key (see § 2.1).

### 3.3 `frontend/src/hooks/useCoins.ts`

**Change**

- `rarity_counts` built with a normalized key: `rarityKey(r) = r.toLowerCase().trim().replace(/\s+/g, '_')`, and counts summed per key so multiple backend variants (e.g. "Very Rare", "very_rare") aggregate correctly.

**Note**

- Other stats (metal_counts, category_counts, grade_counts) unchanged; only rarity normalization added.

### 3.4 `frontend/src/components/design-system/index.ts`

- Exports for CategoryChip, GradeChip, RarityChip and their props added. No issues.

### 3.5 Documentation

- **10-DESIGN-SYSTEM.md § 4.7**: Accurately describes the unified filter chip pattern, tokens, and Ruler/Unknown/Attributes behavior.
- **11-FRONTEND-COMPONENTS.md**: CollectionSidebar added to directory tree and § 3.5 added with location, purpose, and link to design system. Correct.

---

## 4. Consistency and Conventions

| Convention | Status |
|------------|--------|
| Design tokens only (no raw hex/Tailwind colors for accents) | Met; Ruler/Mint/Year/Attributes use `var(--*)`. |
| Chip pattern (padding, gap, rounded-md, selected ring) | Consistent across Metal, Category, Grade, Rarity, Ruler, Unknown, Attributes. |
| Empty states | "No categories found", "No graded coins", "No rarity data" in place. |
| TypeScript | Typed props; CategoryType, GradeTier, string rarity. No `any` in changed code. |
| File header comments | CollectionSidebar and FilterChips headers updated. |

---

## 5. Remaining Considerations (Optional Follow-ups)

1. **Backend rarity filter**: API uses `CoinModel.rarity.ilike(filters["rarity"])`. If the UI sends `rarity=very_rare` and the DB has "Very Rare", `ilike('very_rare')` won’t match. If the backend stores mixed formats, consider normalizing in the repository (e.g. map common frontend values to DB values) or accepting multiple forms. Current fix only aligns stats display with sidebar options.
2. **MetalChip**: For full consistency, MetalChip could get `type="button"` and `aria-pressed={selected}` if it’s used as a toggle elsewhere; currently it’s only in CollectionSidebar and behaves as a toggle.
3. **Single source for grade labels**: GRADE_LABELS in FilterChips.tsx and GRADE_FILTER_CONFIG in CollectionSidebar could be replaced by one shared constant (e.g. in colors or a small filters config module) to avoid drift.
4. **E2E / integration**: Consider a quick smoke test that opens the collection page, expands Ruler, and asserts that at least one Metal and one Category chip are visible and clickable.

---

## 6. Conclusion

- **Correctness**: Rarity counts key normalization and FilterSection structure fix address the only functional and validity issues found.
- **Consistency**: Filter chips and sidebar sections are aligned in layout, tokens, and selected state.
- **Accessibility**: Nested button removed; `aria-expanded` on section toggle; `aria-pressed` on filter chips.
- **Docs**: Design system and component docs updated and match implementation.

No further blocking issues; optional follow-ups above are small improvements.

---

## 7. Backend Fixes (Grade + Stats Year Params)

### 7.1 Stats router – tier-based grade filter

**Issue**: `_apply_filters` used `CoinModel.grade.like(f"%{grade}%")`, so `grade=fine` matched "Fine", "Very Fine", and "Extremely Fine" (EF). Stats and sidebar counts were wrong; selecting Fine showed EF count and wrong total.

**Fix**: Added `_grade_tier_condition(tier)` in `stats.py` mirroring `coin_repository` tier logic (fine = Fine/VF/F only; ef = EF/XF/Extremely only). Stats and coin list now use the same grade semantics.

### 7.2 Stats API – year param names

**Issue**: Frontend sends `mint_year_gte` / `mint_year_lte`; stats API only accepted `year_gte` / `year_lte`, so year filter was ignored and multi-filter counts could be wrong or 0.

**Fix**: Stats endpoint now accepts `mint_year_gte` and `mint_year_lte`; `_apply_filters` uses `year_gte or mint_year_gte` and `year_lte or mint_year_lte`.

### 7.3 Coins list API – year param names

**Issue**: Frontend sends `mint_year_gte` / `mint_year_lte`; v2 coins endpoint only accepted `year_start` / `year_end`, so year filter was not applied to the list.

**Fix**: v2 `get_coins` now accepts `mint_year_gte` and `mint_year_lte` and maps them to `year_start` / `year_end` when the primary params are not set.
