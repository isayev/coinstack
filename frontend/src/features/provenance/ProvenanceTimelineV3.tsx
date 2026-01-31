/**
 * ProvenanceTimelineV3 - Pedigree timeline visualization
 *
 * Features:
 * - Visual timeline with connectors (oldest at top, newest at bottom)
 * - Special styling for ACQUISITION entries ("Current Owner")
 * - Gap detection (>10 years between entries)
 * - Inline edit/delete actions on hover
 * - Empty state with call-to-action
 */

import { memo, useState } from 'react';
import {
  Plus,
  Trash2,
  Edit2,
  Gavel,
  Store,
  Library,
  Handshake,
  BookOpen,
  Map,
  Home,
  ShoppingBag,
  ExternalLink,
  Crown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import type { ProvenanceEvent, ProvenanceChain } from '@/domain/schemas';

// Icon mapping for event types
const EVENT_TYPE_ICONS: Record<string, React.ElementType> = {
  auction: Gavel,
  dealer: Store,
  collection: Library,
  private_sale: Handshake,
  publication: BookOpen,
  hoard_find: Map,
  estate: Home,
  acquisition: ShoppingBag,
  unknown: Library,
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  auction: 'Auction',
  dealer: 'Dealer',
  collection: 'Collection',
  private_sale: 'Private Sale',
  publication: 'Publication',
  hoard_find: 'Hoard/Find',
  estate: 'Estate',
  acquisition: 'My Purchase',
  unknown: 'Unknown',
};

interface ProvenanceTimelineV3Props {
  /** Provenance chain data */
  chain: ProvenanceChain | null | undefined;
  /** Loading state */
  isLoading?: boolean;
  /** Callback when "Add" is clicked */
  onAdd?: () => void;
  /** Callback when "Edit" is clicked */
  onEdit?: (entry: ProvenanceEvent) => void;
  /** Callback when "Delete" is confirmed */
  onDelete?: (entryId: number) => void;
  /** Category type for styling */
  categoryType?: string;
  /** Additional CSS classes */
  className?: string;
}

export const ProvenanceTimelineV3 = memo(function ProvenanceTimelineV3({
  chain,
  isLoading = false,
  onAdd,
  onEdit,
  onDelete,
  categoryType = 'imperial',
  className,
}: ProvenanceTimelineV3Props) {
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [entryToDelete, setEntryToDelete] = useState<ProvenanceEvent | null>(null);

  const entries = chain?.entries || [];

  const handleDeleteClick = (entry: ProvenanceEvent) => {
    setEntryToDelete(entry);
    setDeleteConfirmOpen(true);
  };

  const confirmDelete = () => {
    if (entryToDelete?.id && onDelete) {
      onDelete(entryToDelete.id);
    }
    setDeleteConfirmOpen(false);
    setEntryToDelete(null);
  };

  // Sort by sort_order (oldest first = lowest sort_order)
  const sortedEntries = [...entries].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));

  // Detect gaps (> 10 years between entries)
  const entriesWithGaps = sortedEntries.map((entry, i) => {
    if (i === 0) return { entry, hasGapBefore: false, yearGap: 0 };
    const prevYear = getEntryYear(sortedEntries[i - 1]);
    const thisYear = getEntryYear(entry);
    const yearGap = thisYear && prevYear ? thisYear - prevYear : 0;
    return { entry, hasGapBefore: yearGap > 10, yearGap };
  });

  if (isLoading) {
    return (
      <div className={cn('relative rounded-xl p-5', className)} style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-muted rounded w-1/3" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-3">
                <div className="w-3 h-3 bg-muted rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-muted rounded w-1/4" />
                  <div className="h-4 bg-muted rounded w-2/3" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn('relative rounded-xl p-5', className)}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Category bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-xl"
        style={{ background: `var(--cat-${categoryType})` }}
      />

      {/* Header */}
      <div className="flex items-center justify-between mb-4 pl-2">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
            Provenance
          </h2>
          {chain && chain.total_entries > 0 && (
            <Badge variant="secondary" className="text-[10px] px-1.5">
              {chain.total_entries} {chain.total_entries === 1 ? 'entry' : 'entries'}
            </Badge>
          )}
        </div>
        {onAdd && (
          <button
            className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors"
            style={{
              background: 'transparent',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-subtle)',
            }}
            onClick={onAdd}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--bg-subtle)';
              e.currentTarget.style.color = 'var(--text-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            <Plus size={14} />
            Add
          </button>
        )}
      </div>

      {/* Timeline content */}
      <div className="pl-2">
        {sortedEntries.length === 0 ? (
          <EmptyState onAdd={onAdd} />
        ) : (
          <div className="space-y-0">
            {entriesWithGaps.map(({ entry, hasGapBefore, yearGap }, index) => (
              <div key={entry.id || index}>
                {/* Gap indicator */}
                {hasGapBefore && (
                  <div className="flex items-center gap-2 py-2 pl-1">
                    <span
                      className="w-[2px] h-6 border-l-2 border-dashed"
                      style={{ borderColor: 'var(--border-subtle)' }}
                    />
                    <span
                      className="text-[10px] italic"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      ~{yearGap} year gap
                    </span>
                  </div>
                )}

                <TimelineEntry
                  entry={entry}
                  index={index}
                  totalEntries={sortedEntries.length}
                  onEdit={onEdit}
                  onDelete={handleDeleteClick}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Provenance Record?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This record will be permanently removed from the coin's pedigree.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
});

// ============================================================================
// TimelineEntry Component
// ============================================================================

interface TimelineEntryProps {
  entry: ProvenanceEvent;
  index: number;
  totalEntries: number;
  onEdit?: (entry: ProvenanceEvent) => void;
  onDelete?: (entry: ProvenanceEvent) => void;
}

function TimelineEntry({ entry, index, totalEntries, onEdit, onDelete }: TimelineEntryProps) {
  const Icon = EVENT_TYPE_ICONS[entry.event_type] || Library;
  const isAcquisition = entry.is_acquisition || entry.event_type === 'acquisition';
  const isLast = index === totalEntries - 1;

  return (
    <div className="flex gap-3 group relative">
      {/* Timeline connector */}
      <div className="flex flex-col items-center w-4 flex-shrink-0">
        <span
          className={cn(
            'w-3 h-3 rounded-full flex-shrink-0 border-2 flex items-center justify-center',
            isAcquisition
              ? 'border-emerald-500 bg-emerald-500/20'
              : isLast
              ? 'border-[var(--cat-imperial)] bg-[var(--cat-imperial)]/20'
              : 'border-[var(--border-subtle)] bg-[var(--bg-elevated)]'
          )}
        >
          {isAcquisition && <Crown size={8} className="text-emerald-500" />}
        </span>
        {!isLast && (
          <span
            className="w-[2px] flex-1 mt-1 mb-1"
            style={{ background: 'var(--border-subtle)' }}
          />
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          'flex-1 pb-4 pr-2 rounded-lg transition-colors',
          isAcquisition && 'bg-emerald-500/5 -ml-1 pl-1 pt-1'
        )}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* Acquisition badge */}
            {isAcquisition && (
              <Badge
                variant="outline"
                className="text-[10px] px-1.5 mb-1 border-emerald-500/50 text-emerald-600 bg-emerald-500/10"
              >
                Current Owner
              </Badge>
            )}

            {/* Date */}
            <span className="text-xs font-semibold block" style={{ color: 'var(--text-muted)' }}>
              {formatEntryDate(entry)}
            </span>

            {/* Source with icon */}
            <div className="flex items-center gap-1.5 mt-0.5">
              <Icon size={14} style={{ color: 'var(--text-secondary)' }} />
              <span className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                {entry.source_name || EVENT_TYPE_LABELS[entry.event_type] || 'Unknown'}
              </span>
            </div>

            {/* Sale/Lot details */}
            {(entry.sale_name || entry.lot_number) && (
              <span className="text-xs block mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                {entry.sale_name && <span>{entry.sale_name}</span>}
                {entry.sale_name && entry.lot_number && <span> · </span>}
                {entry.lot_number && <span>lot {entry.lot_number}</span>}
              </span>
            )}

            {/* Price */}
            {(entry.total_price || entry.hammer_price) && (
              <span className="text-xs block mt-0.5" style={{ color: 'var(--text-secondary)' }}>
                {formatCurrency(entry.total_price || entry.hammer_price || 0, entry.currency)}
                {entry.buyers_premium_pct && (
                  <span className="text-muted-foreground"> (incl. {entry.buyers_premium_pct}% BP)</span>
                )}
              </span>
            )}

            {/* Notes */}
            {entry.notes && (
              <span className="text-xs italic block mt-1" style={{ color: 'var(--text-muted)' }}>
                {entry.notes}
              </span>
            )}

            {/* URL link */}
            {entry.url && (
              <a
                href={entry.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs mt-1 hover:underline"
                style={{ color: 'var(--text-link)' }}
              >
                View source <ExternalLink size={10} />
              </a>
            )}
          </div>

          {/* Actions (Visible on Group Hover) */}
          <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity ml-2">
            {onEdit && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => onEdit(entry)}
                    className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all"
                  >
                    <Edit2 size={14} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top">Edit</TooltipContent>
              </Tooltip>
            )}
            {onDelete && !isAcquisition && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => onDelete(entry)}
                    className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-destructive transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top">Delete</TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Empty State Component
// ============================================================================

interface EmptyStateProps {
  onAdd?: () => void;
}

function EmptyState({ onAdd }: EmptyStateProps) {
  return (
    <div className="text-center py-6 border-2 border-dashed rounded-lg" style={{ borderColor: 'var(--border-subtle)' }}>
      <Library size={32} className="mx-auto mb-2" style={{ color: 'var(--text-muted)' }} />
      <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
        No provenance recorded
      </p>
      <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
        Add ownership history to build this coin's pedigree
      </p>
      {onAdd && (
        <button
          className="text-sm mt-3 underline"
          style={{ color: 'var(--text-link)' }}
          onClick={onAdd}
        >
          Add first entry
        </button>
      )}
    </div>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function getEntryYear(entry: ProvenanceEvent): number | null {
  if (entry.event_date) {
    const date = new Date(entry.event_date);
    if (!isNaN(date.getTime())) {
      return date.getFullYear();
    }
  }
  if (entry.date_string) {
    // Extract year from date string like "1920s", "1985", "circa 1990"
    const match = entry.date_string.match(/\d{4}/);
    if (match) {
      return parseInt(match[0], 10);
    }
  }
  return null;
}

function formatEntryDate(entry: ProvenanceEvent): string {
  if (entry.event_date) {
    const date = new Date(entry.event_date);
    if (!isNaN(date.getTime())) {
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
      });
    }
  }
  if (entry.date_string) {
    return entry.date_string;
  }
  return 'Unknown date';
}

function formatCurrency(amount: number, currency?: string | null): string {
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${currency || '$'}${amount.toLocaleString()}`;
  }
}
