/**
 * Provenance Hooks (V3)
 *
 * TanStack Query hooks for provenance (pedigree) CRUD operations.
 * Supports optimistic updates with rollback on error.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import type { ProvenanceEvent, ProvenanceChain, Coin } from '@/domain/schemas';

// API base URL
const API_BASE = '/api/v2';

// =============================================================================
// API Functions
// =============================================================================

async function fetchProvenanceChain(coinId: number): Promise<ProvenanceChain> {
  const response = await fetch(`${API_BASE}/coins/${coinId}/provenance`);
  if (!response.ok) {
    throw new Error(`Failed to fetch provenance: ${response.statusText}`);
  }
  return response.json();
}

async function createProvenanceEntry(
  coinId: number,
  entry: Omit<ProvenanceEvent, 'id' | 'coin_id'>
): Promise<ProvenanceEvent> {
  const response = await fetch(`${API_BASE}/coins/${coinId}/provenance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to create provenance entry');
  }
  return response.json();
}

async function updateProvenanceEntry(
  provenanceId: number,
  entry: Partial<ProvenanceEvent>
): Promise<ProvenanceEvent> {
  const response = await fetch(`${API_BASE}/provenance/${provenanceId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to update provenance entry');
  }
  return response.json();
}

async function deleteProvenanceEntry(provenanceId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/provenance/${provenanceId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to delete provenance entry');
  }
}

// =============================================================================
// Query Hooks
// =============================================================================

/**
 * Fetch provenance chain for a coin.
 */
export function useProvenanceChain(coinId: number) {
  return useQuery({
    queryKey: ['provenance', coinId],
    queryFn: () => fetchProvenanceChain(coinId),
    enabled: !!coinId,
  });
}

// =============================================================================
// Mutation Hooks with Optimistic Updates
// =============================================================================

/**
 * Add a new provenance entry with optimistic update.
 */
export function useAddProvenanceEntry(coinId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entry: Omit<ProvenanceEvent, 'id' | 'coin_id'>) =>
      createProvenanceEntry(coinId, entry),

    // Optimistic update
    onMutate: async (newEntry) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ['provenance', coinId] });
      await queryClient.cancelQueries({ queryKey: ['coin', coinId] });

      // Snapshot current state
      const previousChain = queryClient.getQueryData<ProvenanceChain>(['provenance', coinId]);
      const previousCoin = queryClient.getQueryData<Coin>(['coin', coinId]);

      // Optimistically add entry with temporary ID
      const tempEntry: ProvenanceEvent = {
        ...newEntry,
        id: -Date.now(), // Temporary negative ID
        coin_id: coinId,
        is_acquisition: newEntry.event_type === 'acquisition',
      };

      queryClient.setQueryData<ProvenanceChain>(['provenance', coinId], (old) =>
        old
          ? {
              ...old,
              entries: [...old.entries, tempEntry].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0)),
              total_entries: old.total_entries + 1,
              has_acquisition: old.has_acquisition || newEntry.event_type === 'acquisition',
            }
          : old
      );

      return { previousChain, previousCoin };
    },

    // Rollback on error
    onError: (err, _, context) => {
      if (context?.previousChain) {
        queryClient.setQueryData(['provenance', coinId], context.previousChain);
      }
      toast.error(err instanceof Error ? err.message : 'Failed to add provenance entry');
    },

    // Refetch on success
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['provenance', coinId] });
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] });
      toast.success('Provenance entry added');
    },
  });
}

/**
 * Update a provenance entry with optimistic update.
 */
export function useUpdateProvenanceEntry(coinId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ProvenanceEvent> }) =>
      updateProvenanceEntry(id, data),

    // Optimistic update
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ['provenance', coinId] });

      const previousChain = queryClient.getQueryData<ProvenanceChain>(['provenance', coinId]);

      queryClient.setQueryData<ProvenanceChain>(['provenance', coinId], (old) =>
        old
          ? {
              ...old,
              entries: old.entries.map((entry) =>
                entry.id === id ? { ...entry, ...data } : entry
              ),
            }
          : old
      );

      return { previousChain };
    },

    onError: (err, _, context) => {
      if (context?.previousChain) {
        queryClient.setQueryData(['provenance', coinId], context.previousChain);
      }
      toast.error(err instanceof Error ? err.message : 'Failed to update provenance entry');
    },

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['provenance', coinId] });
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] });
      toast.success('Provenance entry updated');
    },
  });
}

/**
 * Delete a provenance entry with optimistic update.
 */
export function useDeleteProvenanceEntry(coinId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteProvenanceEntry(id),

    // Optimistic update
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['provenance', coinId] });

      const previousChain = queryClient.getQueryData<ProvenanceChain>(['provenance', coinId]);

      queryClient.setQueryData<ProvenanceChain>(['provenance', coinId], (old) =>
        old
          ? {
              ...old,
              entries: old.entries.filter((entry) => entry.id !== id),
              total_entries: old.total_entries - 1,
              has_acquisition: old.entries.filter((e) => e.id !== id).some((e) => e.is_acquisition),
            }
          : old
      );

      return { previousChain };
    },

    onError: (err, _, context) => {
      if (context?.previousChain) {
        queryClient.setQueryData(['provenance', coinId], context.previousChain);
      }
      toast.error(err instanceof Error ? err.message : 'Failed to delete provenance entry');
    },

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['provenance', coinId] });
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] });
      toast.success('Provenance entry deleted');
    },
  });
}

/**
 * Reorder provenance entries (update sort_order for all).
 */
export function useReorderProvenance(coinId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ oldIndex, newIndex }: { oldIndex: number; newIndex: number }) => {
      const chain = queryClient.getQueryData<ProvenanceChain>(['provenance', coinId]);
      if (!chain?.entries) throw new Error('No provenance chain');

      // Reorder array
      const entries = [...chain.entries];
      const [moved] = entries.splice(oldIndex, 1);
      entries.splice(newIndex, 0, moved);

      // Update sort_order for affected entries
      const updates = entries.map((entry, i) => ({
        id: entry.id!,
        sort_order: i,
      }));

      // Batch update (sequential for simplicity)
      for (const update of updates) {
        if (update.id > 0) {
          // Skip temp IDs
          await updateProvenanceEntry(update.id, { sort_order: update.sort_order });
        }
      }

      return entries;
    },

    // Optimistic update
    onMutate: async ({ oldIndex, newIndex }) => {
      await queryClient.cancelQueries({ queryKey: ['provenance', coinId] });

      const previousChain = queryClient.getQueryData<ProvenanceChain>(['provenance', coinId]);

      queryClient.setQueryData<ProvenanceChain>(['provenance', coinId], (old) => {
        if (!old) return old;
        const entries = [...old.entries];
        const [moved] = entries.splice(oldIndex, 1);
        entries.splice(newIndex, 0, moved);
        return {
          ...old,
          entries: entries.map((e, i) => ({ ...e, sort_order: i })),
        };
      });

      return { previousChain };
    },

    onError: (_error, _vars, context) => {
      if (context?.previousChain) {
        queryClient.setQueryData(['provenance', coinId], context.previousChain);
      }
      toast.error('Failed to reorder provenance');
    },

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['provenance', coinId] });
      toast.success('Provenance reordered');
    },
  });
}
