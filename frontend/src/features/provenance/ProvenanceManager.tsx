/**
 * ProvenanceManager - Unified provenance management component
 *
 * Features:
 * - Pedigree timeline visualization
 * - Add/Edit provenance entries via sheet/dialog
 * - Optimistic updates with TanStack Query
 * - Progressive disclosure form
 *
 * @module features/provenance/ProvenanceManager
 */

import { useState, useCallback } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { TooltipProvider } from '@/components/ui/tooltip';
import type { ProvenanceEvent } from '@/domain/schemas';
import {
  useProvenanceChain,
  useAddProvenanceEntry,
  useUpdateProvenanceEntry,
  useDeleteProvenanceEntry,
} from './useProvenance';
import { ProvenanceTimelineV3 } from './ProvenanceTimelineV3';
import { ProvenanceEntryForm } from './ProvenanceEntryForm';
import type { ProvenanceFormData } from './schema';

interface ProvenanceManagerProps {
  /** Coin ID */
  coinId: number;
  /** Category type for styling */
  categoryType?: string;
  /** Additional CSS classes */
  className?: string;
}

export function ProvenanceManager({
  coinId,
  categoryType = 'imperial',
  className,
}: ProvenanceManagerProps) {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<ProvenanceEvent | null>(null);

  // Query hooks
  const { data: chain, isLoading } = useProvenanceChain(coinId);
  const addEntry = useAddProvenanceEntry(coinId);
  const updateEntry = useUpdateProvenanceEntry(coinId);
  const deleteEntry = useDeleteProvenanceEntry(coinId);

  // Handlers
  const handleAdd = useCallback(() => {
    setEditingEntry(null);
    setSheetOpen(true);
  }, []);

  const handleEdit = useCallback((entry: ProvenanceEvent) => {
    setEditingEntry(entry);
    setSheetOpen(true);
  }, []);

  const handleDelete = useCallback(
    (entryId: number) => {
      deleteEntry.mutate(entryId);
    },
    [deleteEntry]
  );

  const handleSubmit = useCallback(
    (data: ProvenanceFormData) => {
      if (editingEntry?.id) {
        // Update existing
        updateEntry.mutate(
          {
            id: editingEntry.id,
            data: formDataToApiPayload(data),
          },
          {
            onSuccess: () => setSheetOpen(false),
          }
        );
      } else {
        // Create new
        addEntry.mutate(formDataToApiPayload(data), {
          onSuccess: () => setSheetOpen(false),
        });
      }
    },
    [editingEntry, addEntry, updateEntry]
  );

  const handleCancel = useCallback(() => {
    setSheetOpen(false);
    setEditingEntry(null);
  }, []);

  const isSubmitting = addEntry.isPending || updateEntry.isPending;

  return (
    <TooltipProvider>
      <ProvenanceTimelineV3
        chain={chain}
        isLoading={isLoading}
        onAdd={handleAdd}
        onEdit={handleEdit}
        onDelete={handleDelete}
        categoryType={categoryType}
        className={className}
      />

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent className="sm:max-w-[480px] overflow-y-auto">
          <SheetHeader>
            <SheetTitle>
              {editingEntry ? 'Edit Provenance Entry' : 'Add Provenance Entry'}
            </SheetTitle>
            <SheetDescription>
              {editingEntry
                ? 'Update the ownership record for this coin.'
                : 'Add a new entry to this coin\'s ownership history (pedigree).'}
            </SheetDescription>
          </SheetHeader>
          <div className="mt-6">
            <ProvenanceEntryForm
              initialValues={editingEntry ? apiPayloadToFormData(editingEntry) : undefined}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              isSubmitting={isSubmitting}
              mode={editingEntry ? 'edit' : 'add'}
            />
          </div>
        </SheetContent>
      </Sheet>
    </TooltipProvider>
  );
}

// ============================================================================
// Data Transformation Helpers
// ============================================================================

/**
 * Convert form data to API payload
 */
function formDataToApiPayload(data: ProvenanceFormData): Omit<ProvenanceEvent, 'id' | 'coin_id'> {
  return {
    event_type: data.event_type,
    source_name: data.source_name,
    event_date: data.event_date || null,
    date_string: data.date_string || null,
    sale_name: data.sale_name || null,
    sale_number: data.sale_number || null,
    lot_number: data.lot_number || null,
    catalog_reference: data.catalog_reference || null,
    hammer_price: data.hammer_price || null,
    buyers_premium_pct: data.buyers_premium_pct || null,
    total_price: data.total_price || null,
    currency: data.currency || 'USD',
    url: data.url || null,
    receipt_available: data.receipt_available || false,
    notes: data.notes || null,
    sort_order: data.sort_order || 0,
    is_acquisition: data.event_type === 'acquisition',
    raw_text: '',
    source_origin: 'manual_entry',
  };
}

/**
 * Convert API payload to form data
 */
function apiPayloadToFormData(entry: ProvenanceEvent): Partial<ProvenanceFormData> {
  return {
    event_type: entry.event_type as any,
    source_name: entry.source_name || '',
    event_date: entry.event_date || null,
    date_string: entry.date_string || null,
    sale_name: entry.sale_name || null,
    sale_number: entry.sale_number || null,
    lot_number: entry.lot_number || null,
    catalog_reference: entry.catalog_reference || null,
    hammer_price: entry.hammer_price || null,
    buyers_premium_pct: entry.buyers_premium_pct || null,
    total_price: entry.total_price || null,
    currency: entry.currency || 'USD',
    url: entry.url || null,
    receipt_available: entry.receipt_available || false,
    notes: entry.notes || null,
    sort_order: entry.sort_order || 0,
  };
}

// ============================================================================
// Standalone Provenance Dialog (for use in other contexts)
// ============================================================================

interface ProvenanceDialogProps {
  coinId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entryToEdit?: ProvenanceEvent | null;
}

export function ProvenanceDialog({
  coinId,
  open,
  onOpenChange,
  entryToEdit,
}: ProvenanceDialogProps) {
  const addEntry = useAddProvenanceEntry(coinId);
  const updateEntry = useUpdateProvenanceEntry(coinId);

  const handleSubmit = useCallback(
    (data: ProvenanceFormData) => {
      if (entryToEdit?.id) {
        updateEntry.mutate(
          { id: entryToEdit.id, data: formDataToApiPayload(data) },
          { onSuccess: () => onOpenChange(false) }
        );
      } else {
        addEntry.mutate(formDataToApiPayload(data), {
          onSuccess: () => onOpenChange(false),
        });
      }
    },
    [entryToEdit, addEntry, updateEntry, onOpenChange]
  );

  const isSubmitting = addEntry.isPending || updateEntry.isPending;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-[480px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {entryToEdit ? 'Edit Provenance Entry' : 'Add Provenance Entry'}
          </SheetTitle>
          <SheetDescription>
            {entryToEdit
              ? 'Update the ownership record for this coin.'
              : 'Add a new entry to this coin\'s ownership history (pedigree).'}
          </SheetDescription>
        </SheetHeader>
        <div className="mt-6">
          <ProvenanceEntryForm
            initialValues={entryToEdit ? apiPayloadToFormData(entryToEdit) : undefined}
            onSubmit={handleSubmit}
            onCancel={() => onOpenChange(false)}
            isSubmitting={isSubmitting}
            mode={entryToEdit ? 'edit' : 'add'}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
