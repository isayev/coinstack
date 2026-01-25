/**
 * CoinTableEnhanced - Full-featured table view for 4K displays
 * 
 * 18+ columns with all coin data:
 * 1. Checkbox (40px) - sticky
 * 2. Image (56px) - sticky
 * 3. Ruler (140px) - sticky
 * 4. Category (80px)
 * 5. Denomination (100px)
 * 6. Metal (50px)
 * 7. Date (80px)
 * 8. Mint (100px)
 * 9. Die Axis (50px)
 * 10. Weight (60px)
 * 11. Diameter (60px)
 * 12. Obverse Legend (200px)
 * 13. Reverse Legend (200px)
 * 14. Grade (60px)
 * 15. Cert (60px)
 * 16. Acquired From (120px)
 * 17. Acquired Date (100px)
 * 18. Storage (100px)
 * 19. Value (80px)
 * 
 * Features:
 * - Sticky first 3 columns (checkbox, image, ruler)
 * - Horizontal scroll on smaller screens
 * - Sortable columns
 * - Column visibility toggle (future)
 */

import { Coins, ExternalLink } from 'lucide-react';
import { Coin } from '@/domain/schemas';
import { parseCategory } from '@/components/design-system/colors';
import { formatYear } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import { Checkbox } from '@/components/ui/checkbox';
import { MetalBadge } from '@/components/ui/badges/MetalBadge';
import { GradeBadge } from '@/components/ui/badges/GradeBadge';
import { CertBadge } from '@/components/ui/badges/CertBadge';

// ============================================================================
// Column Definitions
// ============================================================================

interface Column {
  id: string;
  label: string;
  width: string;
  sticky?: boolean;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  hideBelow?: '3xl' | '4xl' | 'xl' | 'lg';
}

const COLUMNS: Column[] = [
  { id: 'checkbox', label: '', width: '40px', sticky: true },
  { id: 'image', label: '', width: '56px', sticky: true },
  { id: 'ruler', label: 'Ruler', width: '140px', sticky: true, sortable: true },
  { id: 'category', label: 'Category', width: '80px', sortable: true },
  { id: 'denomination', label: 'Denom', width: '100px', sortable: true },
  { id: 'metal', label: 'Metal', width: '50px', align: 'center' },
  { id: 'date', label: 'Date', width: '80px', sortable: true },
  { id: 'mint', label: 'Mint', width: '100px', sortable: true },
  { id: 'die_axis', label: 'Die', width: '50px', align: 'center', hideBelow: 'xl' },
  { id: 'weight', label: 'Weight', width: '60px', align: 'right', sortable: true, hideBelow: 'lg' },
  { id: 'diameter', label: 'Dia', width: '60px', align: 'right', hideBelow: 'lg' },
  { id: 'obverse', label: 'Obverse Legend', width: '200px', hideBelow: '3xl' },
  { id: 'reverse', label: 'Reverse Legend', width: '200px', hideBelow: '3xl' },
  { id: 'grade', label: 'Grade', width: '60px', align: 'center', sortable: true },
  { id: 'cert', label: 'Cert', width: '60px', align: 'center', hideBelow: 'xl' },
  { id: 'source', label: 'Acquired From', width: '120px', hideBelow: '4xl' },
  { id: 'acq_date', label: 'Acq Date', width: '100px', sortable: true, hideBelow: '4xl' },
  { id: 'storage', label: 'Storage', width: '100px', hideBelow: '4xl' },
  { id: 'value', label: 'Value', width: '80px', align: 'right', sortable: true },
];

// ============================================================================
// Table Header
// ============================================================================

interface CoinTableHeaderEnhancedProps {
  onSelectAll?: () => void;
  allSelected?: boolean;
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
  onSort?: (column: string) => void;
}

export function CoinTableHeaderEnhanced({
  onSelectAll,
  allSelected,
  sortColumn,
  sortDirection,
  onSort,
}: CoinTableHeaderEnhancedProps) {
  const SortIcon = ({ column }: { column: string }) => {
    if (sortColumn !== column) return <span className="opacity-30 text-[10px]">⇅</span>;
    return <span className="text-[10px]">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
  };

  const getHideClass = (col: Column) => {
    if (!col.hideBelow) return '';
    const hideMap = {
      'lg': 'hidden lg:table-cell',
      'xl': 'hidden xl:table-cell',
      '3xl': 'hidden 3xl:table-cell',
      '4xl': 'hidden 4xl:table-cell',
    };
    return hideMap[col.hideBelow] || '';
  };

  return (
    <thead
      className="sticky top-0 z-20"
      style={{ background: 'var(--bg-elevated)' }}
    >
      <tr className="border-b-2" style={{ borderColor: 'var(--border-strong)' }}>
        {COLUMNS.map((col) => (
          <th
            key={col.id}
            className={cn(
              'h-12 px-2 text-xs font-semibold uppercase tracking-wider whitespace-nowrap',
              col.sticky && 'sticky bg-[var(--bg-elevated)] z-30',
              col.align === 'center' && 'text-center',
              col.align === 'right' && 'text-right',
              col.align !== 'center' && col.align !== 'right' && 'text-left',
              col.sortable && 'cursor-pointer hover:opacity-70',
              getHideClass(col)
            )}
            style={{
              width: col.width,
              minWidth: col.width,
              left: col.sticky 
                ? col.id === 'checkbox' ? '0' 
                : col.id === 'image' ? '40px' 
                : col.id === 'ruler' ? '96px' 
                : undefined
                : undefined,
              color: 'var(--text-secondary)',
            }}
            onClick={() => col.sortable && onSort?.(col.id)}
          >
            {col.id === 'checkbox' ? (
              <Checkbox
                checked={allSelected}
                onCheckedChange={onSelectAll}
                className="border-[var(--border-strong)]"
              />
            ) : (
              <span className="flex items-center gap-1">
                {col.label}
                {col.sortable && <SortIcon column={col.id} />}
              </span>
            )}
          </th>
        ))}
      </tr>
    </thead>
  );
}

// ============================================================================
// Table Row
// ============================================================================

interface CoinTableRowEnhancedProps {
  coin: Coin;
  selected?: boolean;
  onSelect?: (coinId: number) => void;
  onClick?: (coin: Coin) => void;
}

export function CoinTableRowEnhanced({
  coin,
  selected = false,
  onSelect,
  onClick,
}: CoinTableRowEnhancedProps) {
  const categoryType = parseCategory(coin.category);
  const primaryImage = coin.images?.find(img => img.is_primary)?.url || coin.images?.[0]?.url;

  // Format year
  const displayYear = (): string => {
    const { year_start, year_end } = coin.attribution;
    if (year_start === null || year_start === undefined) return '—';
    if (year_end === null || year_end === undefined || year_start === year_end) {
      return formatYear(year_start);
    }
    return `${formatYear(year_start)}–${formatYear(year_end)}`;
  };

  // Format die axis
  const formatDieAxis = (axis: number | null | undefined): string => {
    if (axis === null || axis === undefined) return '—';
    return `${axis}h`;
  };

  // Format acquisition date
  const formatAcqDate = (date: string | null | undefined): string => {
    if (!date) return '—';
    try {
      return new Date(date).toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short' 
      });
    } catch {
      return date;
    }
  };

  // Value formatting
  const currentValue = coin.market_value || coin.acquisition?.price;
  const formatValue = (val: number | null | undefined) => {
    if (!val) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getHideClass = (col: Column) => {
    if (!col.hideBelow) return '';
    const hideMap = {
      'lg': 'hidden lg:table-cell',
      'xl': 'hidden xl:table-cell',
      '3xl': 'hidden 3xl:table-cell',
      '4xl': 'hidden 4xl:table-cell',
    };
    return hideMap[col.hideBelow] || '';
  };

  return (
    <tr
      className={cn(
        'h-14 border-b transition-colors cursor-pointer',
        'hover:bg-[var(--bg-hover)]',
        selected && 'bg-[var(--bg-hover)]'
      )}
      style={{ 
        borderColor: 'var(--border-subtle)',
        background: 'var(--bg-card)',
      }}
      onClick={() => onClick?.(coin)}
    >
      {/* Checkbox - sticky */}
      <td 
        className="sticky left-0 z-10 px-2"
        style={{ 
          background: selected ? 'var(--bg-hover)' : 'var(--bg-card)',
          width: '40px',
          borderLeft: `4px solid var(--cat-${categoryType})`,
        }}
      >
        <Checkbox
          checked={selected}
          onCheckedChange={() => coin.id && onSelect?.(coin.id)}
          onClick={(e) => e.stopPropagation()}
          className="border-[var(--border-strong)]"
        />
      </td>

      {/* Image - sticky */}
      <td 
        className="sticky left-[40px] z-10 px-2"
        style={{ 
          background: selected ? 'var(--bg-hover)' : 'var(--bg-card)',
          width: '56px',
        }}
      >
        <div className="w-10 h-10 rounded overflow-hidden bg-[var(--bg-elevated)]">
          {primaryImage ? (
            <img
              src={primaryImage}
              alt={coin.attribution.issuer || 'Coin'}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="flex items-center justify-center w-full h-full">
              <Coins className="w-5 h-5" style={{ color: 'var(--text-ghost)' }} />
            </div>
          )}
        </div>
      </td>

      {/* Ruler - sticky */}
      <td 
        className="sticky left-[96px] z-10 px-2"
        style={{ 
          background: selected ? 'var(--bg-hover)' : 'var(--bg-card)',
          width: '140px',
        }}
      >
        <div className="truncate text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {coin.attribution.issuer || 'Unknown'}
        </div>
      </td>

      {/* Category */}
      <td className="px-2" style={{ width: '80px' }}>
        <span 
          className="text-xs font-medium px-2 py-0.5 rounded capitalize"
          style={{ 
            background: `var(--cat-${categoryType}-subtle)`,
            color: `var(--cat-${categoryType})`,
          }}
        >
          {coin.category?.replace('_', ' ') || '—'}
        </span>
      </td>

      {/* Denomination */}
      <td className="px-2 text-sm truncate" style={{ color: 'var(--text-secondary)', width: '100px' }}>
        {coin.denomination || '—'}
      </td>

      {/* Metal */}
      <td className="px-2 text-center" style={{ width: '50px' }}>
        {coin.metal ? <MetalBadge metal={coin.metal} size="sm" /> : <span style={{ color: 'var(--text-ghost)' }}>—</span>}
      </td>

      {/* Date */}
      <td className="px-2 text-sm" style={{ color: 'var(--text-secondary)', width: '80px' }}>
        {displayYear()}
      </td>

      {/* Mint */}
      <td className="px-2 text-sm truncate" style={{ color: 'var(--text-secondary)', width: '100px' }}>
        {coin.attribution.mint || '—'}
      </td>

      {/* Die Axis */}
      <td className={cn("px-2 text-sm text-center", getHideClass(COLUMNS.find(c => c.id === 'die_axis')!))} style={{ color: 'var(--text-secondary)', width: '50px' }}>
        {formatDieAxis(coin.dimensions?.die_axis)}
      </td>

      {/* Weight */}
      <td className={cn("px-2 text-sm text-right tabular-nums", getHideClass(COLUMNS.find(c => c.id === 'weight')!))} style={{ color: 'var(--text-secondary)', width: '60px' }}>
        {coin.dimensions?.weight_g ? `${coin.dimensions.weight_g}g` : '—'}
      </td>

      {/* Diameter */}
      <td className={cn("px-2 text-sm text-right tabular-nums", getHideClass(COLUMNS.find(c => c.id === 'diameter')!))} style={{ color: 'var(--text-secondary)', width: '60px' }}>
        {coin.dimensions?.diameter_mm ? `${coin.dimensions.diameter_mm}mm` : '—'}
      </td>

      {/* Obverse Legend */}
      <td 
        className={cn("px-2 text-xs truncate font-mono", getHideClass(COLUMNS.find(c => c.id === 'obverse')!))} 
        style={{ color: 'var(--text-muted)', width: '200px' }}
        title={coin.design?.obverse_legend || undefined}
      >
        {coin.design?.obverse_legend || '—'}
      </td>

      {/* Reverse Legend */}
      <td 
        className={cn("px-2 text-xs truncate font-mono", getHideClass(COLUMNS.find(c => c.id === 'reverse')!))} 
        style={{ color: 'var(--text-muted)', width: '200px' }}
        title={coin.design?.reverse_legend || undefined}
      >
        {coin.design?.reverse_legend || '—'}
      </td>

      {/* Grade */}
      <td className="px-2 text-center" style={{ width: '60px' }}>
        <GradeBadge grade={coin.grading.grade || '?'} size="sm" showNumeric={false} />
      </td>

      {/* Cert */}
      <td className={cn("px-2 text-center", getHideClass(COLUMNS.find(c => c.id === 'cert')!))} style={{ width: '60px' }}>
        <CertBadge 
          service={coin.grading.service} 
          certNumber={coin.grading.certification_number}
          size="sm"
        />
      </td>

      {/* Acquired From */}
      <td className={cn("px-2 text-sm truncate", getHideClass(COLUMNS.find(c => c.id === 'source')!))} style={{ color: 'var(--text-secondary)', width: '120px' }}>
        {coin.acquisition?.source || '—'}
      </td>

      {/* Acquired Date */}
      <td className={cn("px-2 text-sm", getHideClass(COLUMNS.find(c => c.id === 'acq_date')!))} style={{ color: 'var(--text-secondary)', width: '100px' }}>
        {formatAcqDate(coin.acquisition?.date)}
      </td>

      {/* Storage */}
      <td className={cn("px-2 text-sm truncate", getHideClass(COLUMNS.find(c => c.id === 'storage')!))} style={{ color: 'var(--text-secondary)', width: '100px' }}>
        {coin.storage_location || '—'}
      </td>

      {/* Value */}
      <td className="px-2 text-sm text-right font-semibold tabular-nums" style={{ color: 'var(--text-primary)', width: '80px' }}>
        {formatValue(currentValue)}
      </td>
    </tr>
  );
}

// ============================================================================
// Main Table Component
// ============================================================================

interface CoinTableEnhancedProps {
  coins: Coin[];
  selectedIds?: number[];
  onSelect?: (coinId: number) => void;
  onSelectAll?: () => void;
  allSelected?: boolean;
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
  onSort?: (column: string) => void;
  onCoinClick?: (coin: Coin) => void;
  className?: string;
}

export function CoinTableEnhanced({
  coins,
  selectedIds = [],
  onSelect,
  onSelectAll,
  allSelected,
  sortColumn,
  sortDirection,
  onSort,
  onCoinClick,
  className,
}: CoinTableEnhancedProps) {
  return (
    <div 
      className={cn("overflow-x-auto rounded-lg border", className)}
      style={{ borderColor: 'var(--border-subtle)' }}
    >
      <table className="w-full border-collapse" style={{ minWidth: '1600px' }}>
        <CoinTableHeaderEnhanced
          onSelectAll={onSelectAll}
          allSelected={allSelected}
          sortColumn={sortColumn}
          sortDirection={sortDirection}
          onSort={onSort}
        />
        <tbody>
          {coins.map((coin) => (
            <CoinTableRowEnhanced
              key={coin.id}
              coin={coin}
              selected={coin.id ? selectedIds.includes(coin.id) : false}
              onSelect={onSelect}
              onClick={onCoinClick}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
