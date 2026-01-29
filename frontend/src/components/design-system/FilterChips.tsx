/**
 * FilterChips - Selectable filter chips with counts (Category, Grade, Rarity)
 *
 * Match MetalChip pattern: rounded button with label/symbol + count,
 * design-token background/border/color, selected ring.
 *
 * @module design-system/FilterChips
 */

import { cn } from '@/lib/utils';
import {
  CATEGORY_CONFIG,
  CategoryType,
  GradeTier,
  RARITY_CONFIG,
  RarityType,
} from './colors';

const CHIP_BASE =
  'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md transition-all text-xs font-semibold';
const SELECTED_RING =
  'ring-2 ring-offset-2 scale-105';
const SELECTED_BOX_SHADOW =
  '0 0 0 2px var(--bg-surface), 0 0 0 4px var(--metal-au)';

// ---------------------------------------------------------------------------
// CategoryChip
// ---------------------------------------------------------------------------

export interface CategoryChipProps {
  category: CategoryType;
  count?: number;
  selected?: boolean;
  onClick?: () => void;
}

export function CategoryChip({
  category,
  count,
  selected,
  onClick,
}: CategoryChipProps) {
  const config = CATEGORY_CONFIG[category];
  const cssVar = config?.cssVar ?? 'other';

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(CHIP_BASE, selected && SELECTED_RING)}
      style={{
        background: `var(--category-${cssVar}-subtle)`,
        color: `var(--category-${cssVar})`,
        border: `1px solid var(--category-${cssVar})`,
        boxShadow: selected ? SELECTED_BOX_SHADOW : undefined,
      }}
      title={config?.period || undefined}
      aria-pressed={selected}
    >
      <span>{config?.label ?? category}</span>
      {count !== undefined && (
        <span className="opacity-60 tabular-nums">{count}</span>
      )}
    </button>
  );
}

// ---------------------------------------------------------------------------
// GradeChip
// ---------------------------------------------------------------------------

const GRADE_LABELS: Record<GradeTier, string> = {
  poor: 'Poor',
  good: 'Good',
  fine: 'Fine',
  ef: 'EF',
  au: 'AU',
  ms: 'MS',
  unknown: 'Unknown',
};

export interface GradeChipProps {
  tier: GradeTier;
  count?: number;
  selected?: boolean;
  onClick?: () => void;
}

export function GradeChip({ tier, count, selected, onClick }: GradeChipProps) {
  const label = GRADE_LABELS[tier];
  const cssVar = tier;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(CHIP_BASE, selected && SELECTED_RING)}
      style={{
        background: `var(--grade-${cssVar}-bg)`,
        color: `var(--grade-${cssVar})`,
        border: `1px solid var(--grade-${cssVar})`,
        boxShadow: selected ? SELECTED_BOX_SHADOW : undefined,
      }}
      title={label}
      aria-pressed={selected}
    >
      <span>{label}</span>
      {count !== undefined && (
        <span className="opacity-60 tabular-nums">{count}</span>
      )}
    </button>
  );
}

// ---------------------------------------------------------------------------
// RarityChip - value can be backend key (common, scarce, rare...) or RarityType (c, s, r1...)
// ---------------------------------------------------------------------------

function rarityValueToType(value: string): RarityType {
  const v = value?.toLowerCase().trim();
  if (v === 'u' || v === 'unique') return 'u';
  if (v === 'r3' || v === 'extremely_rare' || v?.includes('extremely')) return 'r3';
  if (v === 'r2' || v === 'very_rare' || v?.includes('very')) return 'r2';
  if (v === 'r1' || v === 'rare' || v === 'r') return 'r1';
  if (v === 's' || v === 'scarce' || v?.includes('scarce')) return 's';
  return 'c'; // common or default
}

export interface RarityChipProps {
  /** Backend key (common, scarce, rare, very_rare, extremely_rare, unique) or RarityType (c, s, r1, ...) */
  value: string;
  count?: number;
  selected?: boolean;
  onClick?: () => void;
}

export function RarityChip({
  value,
  count,
  selected,
  onClick,
}: RarityChipProps) {
  const rarityType = rarityValueToType(value);
  const config = RARITY_CONFIG[rarityType];
  const cssVar = rarityType;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(CHIP_BASE, selected && SELECTED_RING)}
      style={{
        background: `var(--rarity-${cssVar}-bg)`,
        color: `var(--rarity-${cssVar})`,
        border: `1px solid var(--rarity-${cssVar})`,
        boxShadow: selected ? SELECTED_BOX_SHADOW : undefined,
      }}
      title={config?.label}
      aria-pressed={selected}
    >
      <span>{config?.code}</span>
      {count !== undefined && (
        <span className="opacity-60 tabular-nums">{count}</span>
      )}
    </button>
  );
}
