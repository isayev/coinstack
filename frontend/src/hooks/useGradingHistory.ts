/**
 * React Query hooks for Grading History (TPG lifecycle) management.
 *
 * Provides hooks for CRUD operations on grading history entries,
 * tracking a coin's journey through TPG services.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  client,
  type GradingHistoryEntry,
  type GradingHistoryListResponse,
} from '@/api/client'

// Query key factory for consistent cache management
export const gradingHistoryKeys = {
  all: ['grading-history'] as const,
  list: (coinId: number) => [...gradingHistoryKeys.all, 'list', coinId] as const,
  detail: (coinId: number, entryId: number) => [...gradingHistoryKeys.all, 'detail', coinId, entryId] as const,
}

/**
 * Fetch all grading history entries for a coin.
 */
export function useGradingHistory(coinId: number) {
  return useQuery<GradingHistoryListResponse>({
    queryKey: gradingHistoryKeys.list(coinId),
    queryFn: () => client.getGradingHistory(coinId),
    enabled: !!coinId,
  })
}

/**
 * Create a new grading history entry.
 */
export function useCreateGradingHistory(coinId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (entry: Omit<GradingHistoryEntry, 'id' | 'coin_id' | 'recorded_at'>) =>
      client.createGradingHistory(coinId, entry),
    onSuccess: () => {
      // Invalidate the list to refetch
      queryClient.invalidateQueries({ queryKey: gradingHistoryKeys.list(coinId) })
      // Also invalidate coin data as grading info might affect display
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Create grading history failed:', error.message)
      }
    },
  })
}

/**
 * Update an existing grading history entry.
 */
export function useUpdateGradingHistory(coinId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ entryId, entry }: { entryId: number; entry: Partial<GradingHistoryEntry> }) =>
      client.updateGradingHistory(coinId, entryId, entry),
    onSuccess: (_, { entryId }) => {
      queryClient.invalidateQueries({ queryKey: gradingHistoryKeys.list(coinId) })
      queryClient.invalidateQueries({ queryKey: gradingHistoryKeys.detail(coinId, entryId) })
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Update grading history failed:', error.message)
      }
    },
  })
}

/**
 * Delete a grading history entry.
 */
export function useDeleteGradingHistory(coinId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (entryId: number) => client.deleteGradingHistory(coinId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gradingHistoryKeys.list(coinId) })
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Delete grading history failed:', error.message)
      }
    },
  })
}

/**
 * Mark a grading history entry as the current grading state.
 */
export function useSetCurrentGrading(coinId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (entryId: number) => client.setCurrentGrading(coinId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gradingHistoryKeys.list(coinId) })
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Set current grading failed:', error.message)
      }
    },
  })
}

// Export types for convenience
export type { GradingHistoryEntry, GradingHistoryListResponse }
