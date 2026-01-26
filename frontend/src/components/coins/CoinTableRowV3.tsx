/**
 * CoinTableRowV3 - Expanded table row with comprehensive numismatic information
 *
 * Expanded column layout with logical numismatic ordering:
 * 1. Category bar (4px visual)
 * 2. Checkbox (40px)
 * 3. ID (60px)
 * 4. Thumbnail (48px)
 * 5. Category (80px)
 * 6. Ruler/Issuer (140px - name + reign)
 * 7. Denomination (100px)
 * 8. Metal (48px badge)
 * 9. Date (100px)
 * 10. Mint (100px)
 * 11. Weight (70px)
 * 12. Diameter (70px)
 * 13. Script (60px)
 * 14. Obverse Legend (150px)
 * 15. Reverse Legend (150px)
 * 16. Exergue (100px)
 * 17. Reference (120px - RIC/Crawford)
 * 18. Grade (56px pill)
 * 19. Rarity (56px dot + code)
 * 20. Value (120px - current + paid + %)
 *
 * Row Height: 56px
 * Hover: Slide right 4px + intensify border + lighten bg
 *
 * @module coins/CoinTableRowV3
 */

import { Coins } from 'lucide-react';
import { Coin } from '@/domain/schemas';
import { MetalBadge } from '@/components/design-system/MetalBadge';
import { GradeBadge } from '@/components/design-system/GradeBadge';
import { RarityIndicator } from '@/components/design-system/RarityIndicator';
import { parseCategory } from '@/components/design-system/colors';
import { formatYear } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import { Checkbox } from '@/components/ui/checkbox';

export interface CoinTableRowV3Props {
  coin: Coin;
  selected?: boolean;
  onSelect?: (coinId: number) => void;
  onClick?: (coin: Coin) => void;
  className?: string;
}

export function CoinTableRowV3({
  coin,
  selected = false,
  onSelect,
  onClick,
  className,
}: CoinTableRowV3Props) {
  // Parse category for color
  const categoryType = parseCategory(coin.category);

  // Format year range
  const displayYear = (): string => {
    const { year_start, year_end } = coin.attribution;
    if (year_start === null || year_start === undefined) return 'Unknown';
    if (year_end === null || year_end === undefined || year_start === year_end) {
      return formatYear(year_start);
    }
    return `${formatYear(year_start)}–${formatYear(year_end)}`;
  };

  // Get primary image
  const primaryImage = coin.images?.find(img => img.is_primary)?.url || coin.images?.[0]?.url;

  // Format reference - check if references exists
  const references = coin.references;
  const reference = references?.[0]
    ? `${references[0].catalog || 'Ref'} ${references[0].number || ''}`
    : '—';

  // Get legends from design object or flat fields
  const obverseLegend = coin.design?.obverse_legend || coin.obverse_legend || '—';
  const reverseLegend = coin.design?.reverse_legend || coin.reverse_legend || '—';
  const exergue = coin.design?.exergue || '—';

  // Format category display for badge
  const categoryLabel = coin.category
    ? coin.category.replace(/_/g, ' ').replace(/roman /gi, '').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
    : 'Other';

  // Format physical dimensions
  const weightDisplay = coin.dimensions?.weight_g
    ? `${coin.dimensions.weight_g.toFixed(2)}g`
    : coin.weight_g
      ? `${coin.weight_g.toFixed(2)}g`
      : '—';
  
  const diameterDisplay = coin.dimensions?.diameter_mm
    ? `${coin.dimensions.diameter_mm.toFixed(1)}mm`
    : coin.diameter_mm
      ? `${coin.diameter_mm.toFixed(1)}mm`
      : '—';

  // Calculate performance
  const marketValue = coin.market_value;
  const currentValue = marketValue || coin.acquisition?.price;
  const paidPrice = coin.acquisition?.price;
  const performance = currentValue && paidPrice && currentValue !== paidPrice
    ? ((currentValue - paidPrice) / paidPrice) * 100
    : null;

  return (
    <div
      className={cn(
        'relative',
        'h-[56px]',
        'flex items-center',
        'bg-[var(--bg-card)]',
        'border-b border-[var(--border-subtle)]',
        'transition-all duration-200',
        'hover:bg-[var(--bg-hover)]',
        'hover:translate-x-1',
        'group',
        'cursor-pointer',
        className
      )}
      onClick={() => onClick?.(coin)}
    >
      {/* 1. Category Bar (4px left edge) */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[4px] transition-all group-hover:w-[6px]"
        style={{
          background: `var(--cat-${categoryType})`,
        }}
      />

      {/* Content Container - Expanded columns */}
      <div className="flex items-center w-full pl-3 pr-4 gap-2 overflow-x-auto">
        {/* 2. Checkbox (40px) */}
        <div className="w-[40px] flex items-center justify-center flex-shrink-0">
          <Checkbox
            checked={selected}
            onCheckedChange={() => coin.id && onSelect?.(coin.id)}
            onClick={(e) => e.stopPropagation()}
            className="border-[var(--border-strong)]"
          />
        </div>

        {/* 3. ID (60px) */}
        <div className="w-[60px] min-w-0 flex-shrink-0">
          <div
            className="text-xs font-mono tabular-nums"
            style={{ color: 'var(--text-muted)' }}
            title={`Coin ID: ${coin.id}`}
          >
            #{coin.id || '—'}
          </div>
        </div>

        {/* 4. Thumbnail (48px) */}
        <div className="w-[48px] h-[40px] flex-shrink-0 rounded overflow-hidden bg-[var(--bg-elevated)]">
          {primaryImage ? (
            <img
              src={primaryImage}
              alt={coin.attribution.issuer || 'Coin'}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="flex items-center justify-center w-full h-full text-[var(--text-ghost)]">
              <Coins className="w-5 h-5" />
            </div>
          )}
        </div>

        {/* 5. Category Badge (80px) */}
        <div className="w-[80px] min-w-0 flex-shrink-0 flex items-center">
          <div
            className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide whitespace-nowrap"
            style={{
              color: `var(--cat-${categoryType})`,
              background: 'rgba(0, 0, 0, 0.05)',
              border: `1px solid var(--cat-${categoryType})40`,
            }}
            title={categoryLabel}
          >
            {categoryLabel}
          </div>
        </div>

        {/* 6. Ruler/Issuer (140px) */}
        <div className="w-[140px] min-w-0 flex-shrink-0">
          <div
            className="text-sm font-semibold truncate"
            style={{ color: 'var(--text-primary)' }}
            title={coin.attribution.issuer ?? undefined}
          >
            {coin.attribution.issuer || 'Unknown'}
          </div>
          <div
            className="text-[11px] truncate"
            style={{ color: 'var(--text-muted)' }}
          >
            {displayYear()}
          </div>
        </div>

        {/* 7. Denomination (100px) */}
        <div className="w-[100px] min-w-0 flex-shrink-0">
          <div
            className="text-sm truncate"
            style={{ color: 'var(--text-secondary)' }}
            title={coin.denomination || 'Unknown'}
          >
            {coin.denomination || '—'}
          </div>
        </div>

        {/* 8. Metal Badge (48px) */}
        <div className="w-[48px] flex items-center justify-center flex-shrink-0">
          {coin.metal ? (
            <MetalBadge metal={coin.metal} size="xs" />
          ) : (
            <span style={{ color: 'var(--text-ghost)' }}>—</span>
          )}
        </div>

        {/* 9. Date (100px) */}
        <div className="w-[100px] min-w-0 flex-shrink-0 hidden lg:block">
          <div
            className="text-sm truncate"
            style={{ color: 'var(--text-secondary)' }}
          >
            {displayYear()}
          </div>
        </div>

        {/* 10. Mint (100px) */}
        <div className="w-[100px] min-w-0 flex-shrink-0 hidden lg:block">
          <div
            className="text-sm truncate"
            style={{ color: 'var(--text-secondary)' }}
            title={coin.attribution.mint || coin.mint_name || 'Uncertain'}
          >
            {coin.attribution.mint || coin.mint_name || '—'}
          </div>
        </div>

        {/* 11. Weight (70px) */}
        <div className="w-[70px] min-w-0 flex-shrink-0 hidden xl:block">
          <div
            className="text-xs tabular-nums truncate"
            style={{ color: 'var(--text-secondary)' }}
            title={weightDisplay}
          >
            {weightDisplay}
          </div>
        </div>

        {/* 12. Diameter (70px) */}
        <div className="w-[70px] min-w-0 flex-shrink-0 hidden xl:block">
          <div
            className="text-xs tabular-nums truncate"
            style={{ color: 'var(--text-secondary)' }}
            title={diameterDisplay}
          >
            {diameterDisplay}
          </div>
        </div>

        {/* 13. Script (60px) */}
        <div className="w-[60px] min-w-0 flex-shrink-0 hidden 2xl:block">
          <div
            className="text-xs truncate"
            style={{ color: 'var(--text-secondary)' }}
            title={coin.script || 'Unknown'}
          >
            {coin.script || '—'}
          </div>
        </div>

        {/* 14. Obverse Legend (150px) */}
        <div className="w-[150px] min-w-0 flex-shrink-0 hidden 2xl:block">
          <div
            className="text-xs truncate italic"
            style={{ color: 'var(--text-secondary)' }}
            title={obverseLegend}
          >
            {obverseLegend}
          </div>
        </div>

        {/* 15. Reverse Legend (150px) */}
        <div className="w-[150px] min-w-0 flex-shrink-0 hidden 2xl:block">
          <div
            className="text-xs truncate italic"
            style={{ color: 'var(--text-secondary)' }}
            title={reverseLegend}
          >
            {reverseLegend}
          </div>
        </div>

        {/* 16. Exergue (100px) */}
        <div className="w-[100px] min-w-0 flex-shrink-0 hidden 2xl:block">
          <div
            className="text-xs truncate"
            style={{ color: 'var(--text-secondary)' }}
            title={exergue}
          >
            {exergue}
          </div>
        </div>

        {/* 17. Reference (120px) */}
        <div className="w-[120px] min-w-0 flex-shrink-0 hidden lg:block">
          <div
            className="text-[12px] font-mono truncate"
            style={{ color: 'var(--text-secondary)' }}
            title={reference}
          >
            {reference}
          </div>
        </div>

        {/* 18. Grade Pill (56px) */}
        <div className="w-[56px] flex items-center justify-center flex-shrink-0">
          <GradeBadge
            grade={coin.grading.grade ?? '?'}
            size="sm"
          />
        </div>

        {/* 19. Rarity (56px) */}
        <div className="w-[56px] flex items-center justify-center gap-1 flex-shrink-0">
          {coin.rarity ? (
            <>
              <RarityIndicator rarity={coin.rarity} variant="dot" />
              <span
                className="text-[10px] font-medium"
                style={{ color: 'var(--text-secondary)' }}
              >
                {coin.rarity.toUpperCase()}
              </span>
            </>
          ) : (
            <span style={{ color: 'var(--text-ghost)' }}>—</span>
          )}
        </div>

        {/* 20. Value (120px) */}
        <div className="w-[120px] text-right tabular-nums flex-shrink-0">
          {currentValue ? (
            <div className="space-y-0.5">
              {/* Current value */}
              <div
                className="text-sm font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: coin.acquisition?.currency || 'USD',
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0,
                }).format(currentValue)}
              </div>

              {/* Performance indicator */}
              {performance !== null && (
                <div
                  className="text-[10px] font-semibold"
                  style={{
                    color: performance > 0
                      ? 'var(--perf-positive)'
                      : performance < 0
                        ? 'var(--perf-negative)'
                        : 'var(--perf-neutral)',
                  }}
                >
                  {performance > 0 ? '▲' : performance < 0 ? '▼' : '●'}{' '}
                  {Math.abs(performance).toFixed(0)}%
                </div>
              )}
            </div>
          ) : (
            <span style={{ color: 'var(--text-ghost)' }}>—</span>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * CoinTableHeaderV3 - Sticky table header with sorting
 */
export interface CoinTableHeaderV3Props {
  onSelectAll?: () => void;
  allSelected?: boolean;
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
  onSort?: (column: string) => void;
}

export function CoinTableHeaderV3({
  onSelectAll,
  allSelected,
  sortColumn,
  sortDirection,
  onSort,
}: CoinTableHeaderV3Props) {
  const SortIcon = ({ column }: { column: string }) => {
    if (sortColumn !== column) return <span className="opacity-30">⇅</span>;
    return sortDirection === 'asc' ? <span>↑</span> : <span>↓</span>;
  };

  return (
    <div
      className="sticky top-0 z-10 h-[48px] flex items-center border-b-2"
      style={{
        background: 'var(--bg-elevated)',
        borderColor: 'var(--border-strong)',
      }}
    >
      {/* Category bar spacer */}
      <div className="w-[4px]" />

      <div className="flex items-center w-full pl-3 pr-4 gap-2 overflow-x-auto">
        {/* Checkbox */}
        <div className="w-[40px] flex items-center justify-center flex-shrink-0">
          <Checkbox
            checked={allSelected}
            onCheckedChange={onSelectAll}
            className="border-[var(--border-strong)]"
          />
        </div>

        {/* ID */}
        <button
          onClick={() => onSort?.('id')}
          className="w-[60px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          ID <SortIcon column="id" />
        </button>

        {/* Thumbnail */}
        <div className="w-[48px] flex-shrink-0" />

        {/* Category */}
        <button
          onClick={() => onSort?.('category')}
          className="w-[80px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Category <SortIcon column="category" />
        </button>

        {/* Ruler */}
        <button
          onClick={() => onSort?.('ruler')}
          className="w-[140px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Ruler <SortIcon column="ruler" />
        </button>

        {/* Denomination */}
        <button
          onClick={() => onSort?.('denomination')}
          className="w-[100px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Denom <SortIcon column="denomination" />
        </button>

        {/* Metal */}
        <button
          onClick={() => onSort?.('metal')}
          className="w-[48px] text-center text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-1 hover:opacity-70 flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Metal <SortIcon column="metal" />
        </button>

        {/* Date */}
        <button
          onClick={() => onSort?.('date')}
          className="w-[100px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 hidden lg:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Date <SortIcon column="date" />
        </button>

        {/* Mint */}
        <button
          onClick={() => onSort?.('mint')}
          className="w-[100px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 hidden lg:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Mint <SortIcon column="mint" />
        </button>

        {/* Weight */}
        <button
          onClick={() => onSort?.('weight')}
          className="w-[70px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 hidden xl:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Wt <SortIcon column="weight" />
        </button>

        {/* Diameter */}
        <button
          onClick={() => onSort?.('diameter')}
          className="w-[70px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 hidden xl:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Ø <SortIcon column="diameter" />
        </button>

        {/* Script */}
        <div
          className="w-[60px] text-left text-xs font-semibold uppercase tracking-wider hidden 2xl:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Script
        </div>

        {/* Obverse Legend */}
        <div
          className="w-[150px] text-left text-xs font-semibold uppercase tracking-wider hidden 2xl:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Obv Legend
        </div>

        {/* Reverse Legend */}
        <div
          className="w-[150px] text-left text-xs font-semibold uppercase tracking-wider hidden 2xl:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Rev Legend
        </div>

        {/* Exergue */}
        <div
          className="w-[100px] text-left text-xs font-semibold uppercase tracking-wider hidden 2xl:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Exergue
        </div>

        {/* Reference */}
        <button
          onClick={() => onSort?.('reference')}
          className="w-[120px] text-left text-xs font-semibold uppercase tracking-wider flex items-center gap-1 hover:opacity-70 hidden lg:block flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Reference <SortIcon column="reference" />
        </button>

        {/* Grade */}
        <button
          onClick={() => onSort?.('grade')}
          className="w-[56px] text-center text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-1 hover:opacity-70 flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Grade <SortIcon column="grade" />
        </button>

        {/* Rarity */}
        <button
          onClick={() => onSort?.('rarity')}
          className="w-[56px] text-center text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-1 hover:opacity-70 flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Rarity <SortIcon column="rarity" />
        </button>

        {/* Value */}
        <button
          onClick={() => onSort?.('value')}
          className="w-[120px] text-right text-xs font-semibold uppercase tracking-wider flex items-center justify-end gap-1 hover:opacity-70 flex-shrink-0"
          style={{ color: 'var(--text-secondary)' }}
        >
          Value <SortIcon column="value" />
        </button>
      </div>
    </div>
  );
}
