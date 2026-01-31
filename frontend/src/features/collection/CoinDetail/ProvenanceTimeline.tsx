/**
 * ProvenanceTimeline - Visual timeline of coin ownership history
 * 
 * Features:
 * - Chronological display of provenance events
 * - Gap detection (>10 years between entries)
 * - Visual timeline with connectors
 * - Support for approximate dates
 * - Add provenance button
 * 
 * @module features/collection/CoinDetail/ProvenanceTimeline
 */

import { memo, useState } from 'react';
import { Plus, Trash2, Edit2 } from 'lucide-react';
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
} from "@/components/ui/alert-dialog";

interface ProvenanceEntry {
  id?: number;
  /** ISO date string or approximate date like "1920s" */
  event_date?: string | null;
  /** Flexible date string like "1920s", "circa 1980" */
  date_string?: string | null;
  /** 'exact' | 'year' | 'decade' | 'approximate' */
  date_precision?: string;
  /** 'auction' | 'private_sale' | 'collection' | 'acquired' | 'gift' | 'unknown' */
  event_type?: string;
  /** Source name like "Sotheby's Zurich" or "European private collection" */
  source_name?: string | null;
  /** Lot number for auctions */
  lot_number?: string | null;
  /** Sale price */
  price?: number | null;
  /** Currency code */
  currency?: string | null;
  /** Additional notes */
  notes?: string | null;
}

interface ProvenanceTimelineProps {
  /** Array of provenance events */
  provenance: ProvenanceEntry[] | null | undefined;
  /** Category type for styling */
  categoryType?: string;
  /** Callback when "Add" is clicked */
  onAddProvenance?: () => void;
  /** Callback when "Edit" is clicked */
  onEditProvenance?: (entry: ProvenanceEntry) => void;
  /** Callback when "Delete" is clicked */
  onDeleteProvenance?: (entry: ProvenanceEntry) => void;
  /** Additional CSS classes */
  className?: string;
}

export const ProvenanceTimeline = memo(function ProvenanceTimeline({
  provenance,
  categoryType = 'imperial',
  onAddProvenance,
  onEditProvenance,
  onDeleteProvenance,
  className,
}: ProvenanceTimelineProps) {
  const events = provenance || [];
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [entryToDelete, setEntryToDelete] = useState<ProvenanceEntry | null>(null);

  const handleDeleteClick = (entry: ProvenanceEntry) => {
    setEntryToDelete(entry);
    setDeleteConfirmOpen(true);
  };

  const confirmDelete = () => {
    if (entryToDelete && onDeleteProvenance) {
      onDeleteProvenance(entryToDelete);
    }
    setDeleteConfirmOpen(false);
    setEntryToDelete(null);
  };

  // Sort by date (oldest first)
  const sortedEvents = [...events].sort((a, b) => {
    const dateA = parseProvenanceDate(a.event_date);
    const dateB = parseProvenanceDate(b.event_date);
    return dateA - dateB;
  });

  // Detect gaps (> 10 years between entries)
  const entriesWithGaps = sortedEvents.map((entry, i) => {
    if (i === 0) return { entry, hasGapBefore: false };
    const prevDate = parseProvenanceDate(sortedEvents[i - 1].event_date);
    const thisDate = parseProvenanceDate(entry.event_date);
    const yearGap = (thisDate - prevDate) / (365 * 24 * 60 * 60 * 1000);
    return { entry, hasGapBefore: yearGap > 10 };
  });

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
        <h2 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
          Provenance
        </h2>
        {onAddProvenance && (
          <button
            className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors"
            style={{
              background: 'transparent',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-subtle)',
            }}
            onClick={onAddProvenance}
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
        {sortedEvents.length === 0 ? (
          <div className="text-center py-4">
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              No provenance recorded.
            </p>
            {onAddProvenance && (
              <button
                className="text-sm mt-2 underline"
                style={{ color: 'var(--text-link)' }}
                onClick={onAddProvenance}
              >
                Add first entry
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-0">
            {entriesWithGaps.map(({ entry, hasGapBefore }, index) => (
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
                      gap in provenance
                    </span>
                  </div>
                )}

                {/* Entry */}
                <div className="flex gap-3 group relative">
                  {/* Timeline connector */}
                  <div className="flex flex-col items-center w-3 flex-shrink-0">
                    <span
                      className={cn(
                        'w-2.5 h-2.5 rounded-full flex-shrink-0 border-2',
                        index === sortedEvents.length - 1
                          ? 'border-[var(--cat-imperial)] bg-[var(--cat-imperial)]'
                          : 'border-[var(--border-subtle)] bg-[var(--bg-elevated)]'
                      )}
                    />
                    {index < sortedEvents.length - 1 && (
                      <span
                        className="w-[2px] flex-1 mt-1 mb-1"
                        style={{ background: 'var(--border-subtle)' }}
                      />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 pb-4">
                    <div className="flex items-start justify-between">
                      <div>
                        {/* Date */}
                        <span
                          className="text-xs font-semibold block"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          {formatProvenanceDate(entry.date_string || entry.event_date, entry.date_precision)}
                        </span>

                        {/* Source */}
                        <span
                          className="text-sm block mt-0.5"
                          style={{ color: 'var(--text-primary)' }}
                        >
                          {entry.source_name || (entry as any).auction_house || (entry as any).dealer_name || (entry as any).collection_name || getEventTypeLabel(entry.event_type)}
                          {entry.lot_number && (
                            <span style={{ color: 'var(--text-muted)' }}>
                              {' '}· lot {entry.lot_number}
                            </span>
                          )}
                        </span>
                      </div>

                      {/* Actions (Visible on Group Hover) */}
                      <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                        {onEditProvenance && (
                          <button
                            onClick={() => onEditProvenance(entry)}
                            className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-all mr-1"
                            title="Edit entry"
                          >
                            <Edit2 size={14} />
                          </button>
                        )}
                        {onDeleteProvenance && (
                          <button
                            onClick={() => handleDeleteClick(entry)}
                            className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-destructive transition-all"
                            title="Delete entry"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Price */}
                    {(entry.price || (entry as any).total_price) && (
                      <span
                        className="text-xs block mt-0.5"
                        style={{ color: 'var(--text-secondary)' }}
                      >
                        {formatCurrency(entry.price || (entry as any).total_price, entry.currency)}
                      </span>
                    )}

                    {/* Notes */}
                    {entry.notes && (
                      <span
                        className="text-xs italic block mt-1"
                        style={{ color: 'var(--text-muted)' }}
                      >
                        {entry.notes}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Provenance Record?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This record will be permanently removed from the coin's history.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
});

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Parse provenance date string to timestamp for sorting
 */
function parseProvenanceDate(date?: string | null): number {
  if (!date) return 0;

  // Handle decade format: "1920s"
  const decadeMatch = date.match(/^(\d{4})s$/);
  if (decadeMatch) {
    return new Date(`${decadeMatch[1]}-01-01`).getTime();
  }

  // Handle year only: "1985"
  if (/^\d{4}$/.test(date)) {
    return new Date(`${date}-01-01`).getTime();
  }

  // Handle ISO date or parseable format
  const parsed = new Date(date);
  if (!isNaN(parsed.getTime())) {
    return parsed.getTime();
  }

  return 0;
}

/**
 * Format provenance date for display
 */
function formatProvenanceDate(date?: string | null, precision?: string): string {
  if (!date) return 'Unknown date';

  // Decade precision
  if (precision === 'decade') {
    const year = date.match(/\d{4}/)?.[0];
    return year ? `${year}s` : date;
  }

  // Year precision or just year
  if (precision === 'year' || /^\d{4}$/.test(date)) {
    return date;
  }

  // Approximate
  if (precision === 'approximate') {
    return `c. ${date}`;
  }

  // Full date - format nicely
  const parsed = new Date(date);
  if (!isNaN(parsed.getTime())) {
    return parsed.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
    });
  }

  return date;
}

/**
 * Get display label for event type
 */
function getEventTypeLabel(type?: string): string {
  const labels: Record<string, string> = {
    auction: 'Auction',
    private_sale: 'Private Sale',
    collection: 'Collection',
    acquired: 'Acquired',
    gift: 'Gift',
    inheritance: 'Inheritance',
    unknown: 'Unknown source',
  };
  return labels[type || 'unknown'] || type || 'Unknown source';
}

/**
 * Format currency for display
 */
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
