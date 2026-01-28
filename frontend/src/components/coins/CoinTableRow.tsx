/**
 * CoinTableRow - Expanded table row with comprehensive numismatic information
 * 
 * New Numismatic Layout (18 cols):
 * 1. Cat Bar (4px)
 * 2. ID (50px)
 * 3. Image (48px)
 * 4. Ruler/Issuer (140px)
 * 5. Reign (110px) [NEW]
 * 6. Denom (90px)
 * 7. Mint (100px)
 * 8. Date (90px)
 * 9. Obverse Legend (1fr) [NEW]
 * 10. Reverse Legend (1fr) [NEW]
 * 11. Weight (60px)
 * 12. Dia (50px)
 * 13. Dies (50px)
 * 14. Status (40px)
 * 15. Ref (100px)
 * 16. Grade (50px)
 * 17. Rarity (50px)
 * 18. Value (90px)
 */

import { Coins, AlertTriangle } from 'lucide-react';
import { Coin } from '@/domain/schemas';
import { GradeBadge } from '@/components/design-system/GradeBadge';
import { RarityIndicator } from '@/components/design-system/RarityIndicator';
import { parseCategory } from '@/components/design-system/colors';
import { formatYear } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

export interface CoinTableRowProps {
  coin: Coin;
  selected?: boolean;
  onSelect?: (coinId: number) => void;
  onClick?: (coin: Coin) => void;
  className?: string;
}

const TABLE_GRID_LAYOUT = "4px 40px 50px 48px minmax(120px, 1.5fr) 110px 90px 40px minmax(90px, 1.2fr) 90px minmax(100px, 2fr) minmax(100px, 2fr) minmax(100px, 2fr) minmax(100px, 2fr) 60px 60px 60px 40px minmax(100px, 1.2fr) 60px minmax(60px, 80px) 50px 90px";

export function CoinTableRow({
  coin,
  selected = false,
  onSelect,
  onClick,
  className,
}: CoinTableRowProps) {
  // Parse category for color
  const categoryType = parseCategory(coin.category);

  // Format year range
  const displayYear = (): string => {
    if (!coin.attribution) return 'Unknown';
    const { year_start, year_end } = coin.attribution;
    if (year_start === null || year_start === undefined) return '—';
    if (year_end === null || year_end === undefined || year_start === year_end) {
      return formatYear(year_start);
    }
    return `${formatYear(year_start)}–${formatYear(year_end)}`;
  };

  // Format Reign
  const displayReign = (): string => {
    if (coin.reign_start === null || coin.reign_start === undefined) return '—';
    if (coin.reign_end === null || coin.reign_end === undefined) return formatYear(coin.reign_start);
    return `${formatYear(coin.reign_start)}–${formatYear(coin.reign_end)}`;
  };

  // Get primary image
  const primaryImage = coin.images?.find(img => img.is_primary)?.url || coin.images?.[0]?.url;

  // Format reference
  const references = coin.references;
  const reference = references?.[0]
    ? `${references[0].catalog || 'Ref'} ${references[0].number || ''}`
    : '—';

  // Issue Status Icon
  const isFourree = coin.issue_status === 'fourree';
  const isOfficial = !coin.issue_status || coin.issue_status === 'official';

  // Value
  const currentValue = coin.market_value || coin.acquisition?.price;

  return (
    <div
      className={cn(
        'relative group cursor-pointer border-b border-[var(--border-subtle)] transition-all hover:bg-[var(--bg-hover)] hidden md:grid items-center gap-2 px-2 py-0',
        selected && 'bg-[var(--bg-elevated)]',
        className
      )}
      style={{
        height: '60px', // Slightly taller for legends
        gridTemplateColumns: TABLE_GRID_LAYOUT,
      }}
      onClick={() => onClick?.(coin)}
    >
      {/* 1. Category Bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[4px] transition-all group-hover:w-[6px]"
        style={{ background: `var(--cat-${categoryType})` }}
      />
      <div />

      {/* 2. Checkbox */}
      <div className="flex items-center justify-center" onClick={(e) => e.stopPropagation()}>
        <Checkbox
          checked={selected}
          onCheckedChange={() => coin.id && onSelect?.(coin.id)}
          className="border-[var(--border-strong)]"
        />
      </div>

      {/* 2. ID */}
      <div className="text-xs font-mono tabular-nums text-muted-foreground" title={`Coin ID: ${coin.id}`}>
        #{coin.id || '—'}
      </div>

      {/* 3. Thumbnail */}
      <div className="w-[48px] h-[40px] rounded overflow-hidden bg-[var(--bg-elevated)] relative">
        {primaryImage ? (
          <img
            src={primaryImage}
            alt={coin.attribution?.issuer || 'Coin'}
            className="w-full h-full object-cover transition-transform group-hover:scale-110"
            loading="lazy"
          />
        ) : (
          <div
            className="flex flex-col items-center justify-center w-full h-full gap-0.5 text-[var(--text-ghost)]"
            aria-label="No image"
            role="img"
          >
            <Coins className="w-5 h-5" />
            <span className="text-[8px] text-muted-foreground">No image</span>
          </div>
        )}
      </div>

      {/* 4. Ruler/Issuer */}
      <div className="min-w-0 pr-2">
        <div className="text-sm font-semibold truncate text-foreground">
          {coin.attribution?.issuer || 'Unknown'}
        </div>
      </div>

      {/* 5. Reign [NEW] */}
      <div className="text-xs text-muted-foreground truncate font-mono">
        {displayReign()}
      </div>

      {/* 6. Denomination */}
      <div className="text-sm truncate text-secondary-foreground font-medium pr-2">
        {coin.denomination || '—'}
      </div>

      {/* 7. Metal [NEW] */}
      <div className="flex justify-center">
        <Badge variant="outline" className="text-[10px] px-1 h-5">{coin.metal?.slice(0, 2).toUpperCase() || '—'}</Badge>
      </div>

      {/* 7. Mint */}
      <div className="text-sm truncate text-muted-foreground hidden lg:block pr-2">
        {coin.attribution?.mint || coin.mint_name || '—'}
      </div>

      {/* 8. Date */}
      <div className="text-sm truncate text-muted-foreground hidden lg:block">
        {displayYear()}
      </div>

      {/* 9. Obverse Legend */}
      <div className="text-[10px] text-muted-foreground truncate hidden xl:block" title={coin.design?.obverse_legend || coin.obverse_legend || ''}>
        {coin.design?.obverse_legend || coin.obverse_legend || '—'}
      </div>

      {/* 9b. Obverse Description [NEW] */}
      <div className="text-[10px] text-muted-foreground truncate hidden 2xl:block" title={coin.design?.obverse_description || coin.obverse_description || ''}>
        {coin.design?.obverse_description || coin.obverse_description || '—'}
      </div>

      {/* 10. Reverse Legend */}
      <div className="text-[10px] text-muted-foreground truncate hidden xl:block" title={coin.design?.reverse_legend || coin.reverse_legend || ''}>
        {coin.design?.reverse_legend || coin.reverse_legend || '—'}
      </div>

      {/* 10b. Reverse Description [NEW] */}
      <div className="text-[10px] text-muted-foreground truncate hidden 2xl:block" title={coin.design?.reverse_description || coin.reverse_description || ''}>
        {coin.design?.reverse_description || coin.reverse_description || '—'}
      </div>

      {/* 11. Weight */}
      <div className="text-xs tabular-nums text-muted-foreground hidden 2xl:block text-right pr-2">
        {coin.dimensions?.weight_g ? `${coin.dimensions.weight_g.toFixed(2)}` : '—'}
      </div>

      {/* 12. Diameter */}
      <div className="text-xs tabular-nums text-muted-foreground hidden 2xl:block text-right pr-2">
        {coin.dimensions?.diameter_mm ? `${coin.dimensions.diameter_mm.toFixed(1)}` : '—'}
      </div>

      {/* 13. Dies */}
      <div className="text-[10px] font-mono text-muted-foreground hidden 3xl:flex flex-col leading-tight truncate text-center">
        {coin.die_info ? (
          <>
            {coin.die_info.obverse_die_id && <span>O:{coin.die_info.obverse_die_id}</span>}
            {coin.die_info.reverse_die_id && <span>R:{coin.die_info.reverse_die_id}</span>}
          </>
        ) : '—'}
      </div>


      {/* 14. Issue Status */}
      <div className="flex justify-center hidden 2xl:flex">
        {isFourree ? (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <div className="w-5 h-5 rounded-full bg-orange-500/10 flex items-center justify-center items-center">
                  <AlertTriangle className="w-3 h-3 text-orange-500" />
                </div>
              </TooltipTrigger>
              <TooltipContent>Fourree / Plated</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ) : !isOfficial && coin.issue_status ? (
          <Badge variant="outline" className="text-[10px] py-0 h-5 px-1">{coin.issue_status.slice(0, 1).toUpperCase()}</Badge>
        ) : (
          <span className="text-muted-foreground/30 text-[10px]">•</span>
        )}
      </div>

      {/* 15. Reference */}
      <div className="text-[11px] font-mono truncate text-muted-foreground hidden xl:block pr-2" title={reference}>
        {reference}
      </div>

      {/* 16. Grade */}
      <div className="flex justify-center">
        <GradeBadge grade={coin.grading?.grade ?? '?'} size="sm" />
      </div>

      {/* 16b. Storage [NEW] */}
      <div className="text-[10px] text-muted-foreground truncate hidden 2xl:block px-1" title={coin.storage_location || ''}>
        {coin.storage_location || '—'}
      </div>

      {/* 17. Rarity */}
      <div className="flex justify-center gap-1 hidden 2xl:flex">
        {coin.rarity ? (
          <>
            <RarityIndicator rarity={coin.rarity} variant="dot" />
            <span className="text-[10px] font-medium text-muted-foreground">{coin.rarity.toUpperCase()}</span>
          </>
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </div>

      {/* 18. Value */}
      <div className="text-right tabular-nums pr-2 text-sm font-semibold">
        {currentValue ? (
          new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: coin.acquisition?.currency || 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }).format(currentValue)
        ) : (
          <span className="text-muted-foreground">—</span>
        )}
      </div>
    </div>
  );
}

export interface CoinTableHeaderProps {
  onSelectAll?: () => void;
  allSelected?: boolean;
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
  onSort?: (column: string) => void;
}

export function CoinTableHeader({
  onSelectAll,
  allSelected,
  sortColumn,
  sortDirection,
  onSort,
}: CoinTableHeaderProps) {
  const SortIcon = ({ column }: { column: string }) => {
    if (sortColumn !== column) return <span className="opacity-30 ml-1 text-[10px]">⇅</span>;
    return sortDirection === 'asc' ? <span className="ml-1 text-primary text-[10px]">↑</span> : <span className="ml-1 text-primary text-[10px]">↓</span>;
  };

  const HeaderCell = ({
    label,
    sortKey,
    className = "",
    align = "left"
  }: {
    label: string,
    sortKey?: string,
    className?: string,
    align?: "left" | "center" | "right"
  }) => {
    if (!sortKey || !onSort) {
      return (
        <div className={cn(
          "text-[10px] font-bold uppercase tracking-wider text-muted-foreground select-none truncate flex items-center",
          align === "center" && "justify-center",
          align === "right" && "justify-end",
          className
        )}>
          {label}
        </div>
      );
    }

    return (
      <button
        onClick={() => onSort(sortKey)}
        className={cn(
          "text-[10px] font-bold uppercase tracking-wider text-muted-foreground select-none flex items-center hover:text-foreground transition-colors truncate",
          align === "center" && "justify-center",
          align === "right" && "justify-end",
          className
        )}
      >
        {label}
        <SortIcon column={sortKey} />
      </button>
    );
  };

  return (
    <div
      className="sticky top-0 z-10 border-b shadow-sm hidden md:grid items-center gap-2 px-2"
      style={{
        background: 'var(--bg-elevated)',
        borderColor: 'var(--border-subtle)',
        height: '40px',
        gridTemplateColumns: TABLE_GRID_LAYOUT,
      }}
    >
      <div />
      <div className="flex items-center justify-center">
        <Checkbox
          checked={allSelected}
          onCheckedChange={onSelectAll}
          className="border-[var(--border-strong)]"
        />
      </div>

      <HeaderCell label="ID" sortKey="id" />
      <div /> {/* Image */}

      <HeaderCell label="Ruler" sortKey="name" />
      <HeaderCell label="Reign" sortKey="reign" />
      <HeaderCell label="Denom" sortKey="denomination" />
      <HeaderCell label="Mtl" sortKey="metal" align="center" />
      <HeaderCell label="Mint" sortKey="mint" className="hidden lg:flex" />
      <HeaderCell label="Date" sortKey="year" className="hidden lg:flex" />

      <HeaderCell label="Obv Leg" sortKey="obverse_legend" className="hidden xl:flex" />
      <HeaderCell label="Obv Desc" sortKey="obverse_description" className="hidden 2xl:flex" />
      <HeaderCell label="Rev Leg" sortKey="reverse_legend" className="hidden xl:flex" />
      <HeaderCell label="Rev Desc" sortKey="reverse_description" className="hidden 2xl:flex" />

      <HeaderCell label="Wgt" sortKey="weight" align="right" className="hidden 2xl:flex pr-2" />
      <HeaderCell label="Dia" sortKey="diameter" align="right" className="hidden 2xl:flex pr-2" />

      <HeaderCell label="Dies" className="hidden 3xl:flex" align="center" />
      <HeaderCell label="Sts" sortKey="issue_status" align="center" className="hidden 2xl:flex" />

      <HeaderCell label="Ref" sortKey="reference" className="hidden xl:flex" />
      <HeaderCell label="Grd" sortKey="grade" align="center" />
      <HeaderCell label="Loc" sortKey="storage_location" className="hidden 2xl:block" />
      <HeaderCell label="Rty" sortKey="rarity" align="center" className="hidden 2xl:flex" />
      <HeaderCell label="Value" sortKey="value" align="right" className="pr-2" />
    </div>
  );
}
