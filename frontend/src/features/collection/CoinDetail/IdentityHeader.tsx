/**
 * IdentityHeader - Scholarly catalog-style header for coin detail page
 * 
 * Layout:
 * - Large side navigation arrows for sequential browsing
 * - 6px category bar (left border)
 * - Category label uppercase
 * - Ruler with reign dates
 * - Type line: Denomination · Mint · Date
 * - References line
 * - Provenance preview (Ex: collection)
 * 
 * Design principle: Headers identify, cards detail.
 * 
 * @module features/collection/CoinDetail/IdentityHeader
 */

import { memo } from 'react';
import { Pencil, MoreHorizontal, Trash2, Copy, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Coin } from '@/domain/schemas';
import { parseCategory, CATEGORY_CONFIG } from '@/components/design-system/colors';
import { formatYear } from '@/lib/formatters';
import { cn } from '@/lib/utils';

interface IdentityHeaderProps {
  coin: Coin;
  onEdit: () => void;
  onDelete?: () => void;
  onNavigatePrev?: () => void;
  onNavigateNext?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
  className?: string;
}

/**
 * Format provenance preview - find the most notable entry
 */
function formatProvenancePreview(provenance: any[] | null | undefined): string | null {
  if (!provenance?.length) return null;

  // Prefer collection names over auction houses
  const collection = provenance.find(p => p.event_type === 'collection');
  if (collection?.source_name) return collection.source_name;

  // Fall back to notable auction houses
  const notable = provenance.find(p =>
    p.source_name?.includes('Triton') ||
    p.source_name?.includes('NAC') ||
    p.source_name?.includes('Heritage') ||
    p.source_name?.includes('CNG')
  );
  if (notable?.source_name) return notable.source_name;

  // Fall back to first entry with a source name
  return provenance[0]?.source_name || null;
}

export const IdentityHeader = memo(function IdentityHeader({
  coin,
  onEdit,
  onDelete,
  onNavigatePrev,
  onNavigateNext,
  hasPrev = false,
  hasNext = false,
  className
}: IdentityHeaderProps) {
  const categoryType = parseCategory(coin.category);
  const categoryConfig = CATEGORY_CONFIG[categoryType];

  // Format date range
  const formatDateRange = (start?: number | null, end?: number | null): string => {
    if (!start && !end) return '';
    if (!end || start === end) return formatYear(start!);
    return `${formatYear(start!)}–${formatYear(end)}`;
  };

  // Build references string
  const referencesString = coin.references
    ?.filter(ref => ref?.catalog && ref?.number)
    .map(ref => `${ref!.catalog} ${ref!.number}`)
    .join(' · ') || '';

  // Build type line parts
  const typeParts: string[] = [];
  if (coin.denomination) typeParts.push(coin.denomination);
  if (coin.attribution?.mint) typeParts.push(coin.attribution.mint);
  const dateRange = formatDateRange(coin.attribution?.year_start, coin.attribution?.year_end);
  if (dateRange) typeParts.push(dateRange);

  // Get provenance preview
  const provenancePreview = formatProvenancePreview(coin.provenance);

  return (
    <div className={cn('identity-header-wrapper relative', className)}>
      {/* Left Navigation Arrow */}
      <button
        onClick={onNavigatePrev}
        disabled={!hasPrev}
        className={cn(
          'nav-arrow nav-arrow--left',
          'absolute top-1/2 -translate-y-1/2 z-10',
          'w-12 h-12 rounded-full flex items-center justify-center',
          'transition-all duration-200 ease-out',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          hasPrev ? 'cursor-pointer' : 'cursor-not-allowed'
        )}
        style={{
          left: '-24px',
          background: hasPrev ? 'var(--bg-subtle)' : 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          color: hasPrev ? 'var(--text-secondary)' : 'var(--text-ghost)',
          opacity: hasPrev ? 0.8 : 0.3,
        }}
        onMouseEnter={(e) => {
          if (hasPrev) {
            e.currentTarget.style.opacity = '1';
            e.currentTarget.style.background = 'var(--bg-elevated)';
            e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
          }
        }}
        onMouseLeave={(e) => {
          if (hasPrev) {
            e.currentTarget.style.opacity = '0.8';
            e.currentTarget.style.background = 'var(--bg-subtle)';
            e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
          }
        }}
        aria-label="Previous coin"
        title="Previous coin (←)"
      >
        <ChevronLeft size={28} />
      </button>

      {/* Right Navigation Arrow */}
      <button
        onClick={onNavigateNext}
        disabled={!hasNext}
        className={cn(
          'nav-arrow nav-arrow--right',
          'absolute top-1/2 -translate-y-1/2 z-10',
          'w-12 h-12 rounded-full flex items-center justify-center',
          'transition-all duration-200 ease-out',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          hasNext ? 'cursor-pointer' : 'cursor-not-allowed'
        )}
        style={{
          right: '-24px',
          background: hasNext ? 'var(--bg-subtle)' : 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          color: hasNext ? 'var(--text-secondary)' : 'var(--text-ghost)',
          opacity: hasNext ? 0.8 : 0.3,
        }}
        onMouseEnter={(e) => {
          if (hasNext) {
            e.currentTarget.style.opacity = '1';
            e.currentTarget.style.background = 'var(--bg-elevated)';
            e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)';
          }
        }}
        onMouseLeave={(e) => {
          if (hasNext) {
            e.currentTarget.style.opacity = '0.8';
            e.currentTarget.style.background = 'var(--bg-subtle)';
            e.currentTarget.style.transform = 'translateY(-50%) scale(1)';
          }
        }}
        aria-label="Next coin"
        title="Next coin (→)"
      >
        <ChevronRight size={28} />
      </button>

      {/* Header Content */}
      <header
        className="identity-header relative rounded-xl"
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
        }}
        role="banner"
        aria-label={`Coin details: ${coin.attribution?.issuer || coin.issuing_authority || 'Unknown ruler'}`}
      >
        {/* Category bar (6px left border) */}
        <div
          className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-xl"
          style={{
            background: `var(--cat-${categoryConfig.cssVar})`,
          }}
        />

        {/* Content with left padding for category bar */}
        <div className="pl-6 pr-4 py-5">
          {/* Top row: Category + Actions */}
          <div className="flex items-start justify-between mb-3">
            {/* Category label */}
            <span
              className="text-[11px] font-bold tracking-[1px] uppercase"
              style={{ color: `var(--cat-${categoryConfig.cssVar})` }}
            >
              {categoryConfig.label}
            </span>

            {/* Issue Status Badge */}
            {coin.issue_status && coin.issue_status !== 'official' && (
              <span
                className="ml-3 px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider"
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  color: 'rgb(239, 68, 68)',
                  border: '1px solid rgba(239, 68, 68, 0.2)'
                }}
              >
                {coin.issue_status.replace(/_/g, ' ')}
              </span>
            )}

            {/* Actions */}
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={onEdit}
                className="h-8 px-3 gap-1.5"
              >
                <Pencil size={14} />
                Edit
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreHorizontal size={16} />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => navigator.clipboard.writeText(window.location.href)}>
                    <Copy size={14} className="mr-2" />
                    Copy Link
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => window.open(coin.acquisition?.url || '', '_blank')}>
                    <ExternalLink size={14} className="mr-2" />
                    View Source
                  </DropdownMenuItem>
                  {onDelete && (
                    <>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={onDelete}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 size={14} className="mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Ruler name with reign dates */}
          <h1
            className="text-2xl font-bold mb-1"
            style={{ color: 'var(--text-primary)' }}
          >
            {coin.attribution?.issuer || coin.issuing_authority || 'Unknown Issuer'}
            {(coin.reign_start || coin.reign_end) && (
              <span
                className="font-normal ml-2 text-lg"
                style={{ color: 'var(--text-secondary)' }}
              >
                ({formatDateRange(coin.reign_start, coin.reign_end)})
              </span>
            )}
          </h1>

          {/* Type line: Denomination · Mint · Date */}
          {typeParts.length > 0 && (
            <p
              className="text-base mb-2"
              style={{ color: 'var(--text-secondary)' }}
            >
              {typeParts.join(' · ')}
            </p>
          )}

          {/* References line */}
          {referencesString && (
            <p
              className="font-mono text-[13px] mb-2"
              style={{ color: 'var(--text-muted)' }}
            >
              {referencesString}
            </p>
          )}

          {/* Provenance preview */}
          {provenancePreview && (
            <p
              className="text-sm italic"
              style={{ color: 'var(--text-muted)' }}
            >
              Ex: {provenancePreview}
            </p>
          )}
        </div>
      </header>
    </div>
  );
});
