/**
 * BulkActionsBar - Fixed bottom bar for bulk operations
 * 
 * Appears when coins are selected, provides quick actions:
 * - Enrich: Run AI enrichment on selected
 * - Export: Download CSV/JSON
 * - Delete: Remove selected (with confirmation)
 * 
 * @module features/collection/BulkActionsBar
 */

import { useState } from 'react';
import { useSelection } from '@/stores/selectionStore';
import { Button } from '@/components/ui/button';
import {
  Sparkles,
  Download,
  Trash2,
  X,
  Loader2,
  CheckCircle2
} from 'lucide-react';
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
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { client } from '@/api/client';
import { toast } from 'sonner';

interface BulkActionsBarProps {
  /** Callback when enrichment is triggered */
  onEnrich?: (ids: number[]) => void;
  /** Callback when export is triggered */
  onExport?: (ids: number[], format: 'csv' | 'json') => void;
}

export function BulkActionsBar({ onEnrich, onExport }: BulkActionsBarProps) {
  const { selectedCount, getSelectedIds, clear } = useSelection();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  // Delete mutation with proper error handling for partial failures
  const deleteMutation = useMutation({
    mutationFn: async (ids: number[]) => {
      // Use allSettled to track individual success/failure
      const results = await Promise.allSettled(ids.map(id => client.deleteCoin(id)));

      const succeeded = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;

      // Return results for onSuccess/onError to handle
      return { succeeded, failed, total: ids.length };
    },
    onSuccess: ({ succeeded, failed }) => {
      if (failed === 0) {
        toast.success(`Deleted ${succeeded} coin${succeeded > 1 ? 's' : ''}`);
      } else if (succeeded === 0) {
        toast.error(`Failed to delete all ${failed} coins`);
      } else {
        toast.warning(`Deleted ${succeeded} coin${succeeded > 1 ? 's' : ''}, ${failed} failed`);
      }
      queryClient.invalidateQueries({ queryKey: ['coins'] });
      clear();
    },
    onError: (error) => {
      toast.error('Failed to delete coins');
      if (import.meta.env.DEV) {
        console.error('Delete error:', error);
      }
    },
  });

  // Don't render if nothing is selected
  if (selectedCount === 0) {
    return null;
  }

  const handleEnrich = () => {
    const ids = getSelectedIds();
    if (onEnrich) {
      onEnrich(ids);
    } else {
      toast.info(`Enriching ${ids.length} coin${ids.length > 1 ? 's' : ''}...`);
      // Future: call enrich API
    }
  };

  const handleExport = (format: 'csv' | 'json') => {
    const ids = getSelectedIds();
    if (onExport) {
      onExport(ids, format);
    } else {
      toast.info(`Exporting ${ids.length} coin${ids.length > 1 ? 's' : ''} as ${format.toUpperCase()}`);
      // Future: call export API
    }
  };

  const handleDelete = () => {
    const ids = getSelectedIds();
    deleteMutation.mutate(ids);
    setDeleteDialogOpen(false);
  };

  return (
    <>
      {/* Fixed bottom bar */}
      <div
        className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-2.5 rounded-xl shadow-2xl"
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          backdropFilter: 'blur(8px)',
        }}
      >
        {/* Selection count */}
        <div
          className="flex items-center gap-2 pr-3 border-r"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--metal-au)' }} />
          <span
            className="text-sm font-semibold tabular-nums"
            style={{ color: 'var(--text-primary)' }}
          >
            {selectedCount} selected
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Enrich */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleEnrich}
            className="gap-1.5"
            style={{ color: 'var(--text-secondary)' }}
          >
            <Sparkles className="w-4 h-4" />
            <span className="hidden sm:inline">Enrich</span>
          </Button>

          {/* Export */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleExport('csv')}
            className="gap-1.5"
            style={{ color: 'var(--text-secondary)' }}
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export</span>
          </Button>

          {/* Delete */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDeleteDialogOpen(true)}
            disabled={deleteMutation.isPending}
            className="gap-1.5 hover:text-red-500 hover:bg-red-500/10"
            style={{ color: 'var(--text-secondary)' }}
          >
            {deleteMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
            <span className="hidden sm:inline">Delete</span>
          </Button>
        </div>

        {/* Clear selection */}
        <Button
          variant="ghost"
          size="icon"
          onClick={clear}
          className="ml-2"
          style={{ color: 'var(--text-muted)' }}
          title="Clear selection (Esc)"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectedCount} coin{selectedCount > 1 ? 's' : ''}?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the selected
              coin{selectedCount > 1 ? 's' : ''} from your collection.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
