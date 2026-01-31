/**
 * React Query hooks for Rarity Assessment management.
 *
 * Provides hooks for CRUD operations on rarity assessments,
 * supporting multiple sources (catalog, census, market analysis).
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  client,
  type RarityAssessment,
  type RarityAssessmentListResponse,
} from '@/api/client'

// Query key factory for consistent cache management
export const rarityAssessmentKeys = {
  all: ['rarity-assessments'] as const,
  list: (coinId: number) => [...rarityAssessmentKeys.all, 'list', coinId] as const,
  detail: (coinId: number, assessmentId: number) =>
    [...rarityAssessmentKeys.all, 'detail', coinId, assessmentId] as const,
}

/**
 * Fetch all rarity assessments for a coin.
 */
export function useRarityAssessments(coinId: number) {
  return useQuery<RarityAssessmentListResponse>({
    queryKey: rarityAssessmentKeys.list(coinId),
    queryFn: () => client.getRarityAssessments(coinId),
    enabled: !!coinId,
  })
}

/**
 * Create a new rarity assessment.
 */
export function useCreateRarityAssessment(coinId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (assessment: Omit<RarityAssessment, 'id' | 'coin_id' | 'created_at'>) =>
      client.createRarityAssessment(coinId, assessment),
    onSuccess: () => {
      // Invalidate the list to refetch
      queryClient.invalidateQueries({ queryKey: rarityAssessmentKeys.list(coinId) })
      // Also invalidate coin data as rarity info might affect display
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Create rarity assessment failed:', error.message)
      }
    },
  })
}

/**
 * Update an existing rarity assessment.
 */
export function useUpdateRarityAssessment(coinId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      assessmentId,
      assessment,
    }: {
      assessmentId: number
      assessment: Partial<RarityAssessment>
    }) => client.updateRarityAssessment(coinId, assessmentId, assessment),
    onSuccess: (_, { assessmentId }) => {
      queryClient.invalidateQueries({ queryKey: rarityAssessmentKeys.list(coinId) })
      queryClient.invalidateQueries({
        queryKey: rarityAssessmentKeys.detail(coinId, assessmentId),
      })
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Update rarity assessment failed:', error.message)
      }
    },
  })
}

/**
 * Delete a rarity assessment.
 */
export function useDeleteRarityAssessment(coinId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (assessmentId: number) =>
      client.deleteRarityAssessment(coinId, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rarityAssessmentKeys.list(coinId) })
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Delete rarity assessment failed:', error.message)
      }
    },
  })
}

/**
 * Mark a rarity assessment as the primary assessment.
 */
export function useSetPrimaryRarityAssessment(coinId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (assessmentId: number) =>
      client.setPrimaryRarityAssessment(coinId, assessmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rarityAssessmentKeys.list(coinId) })
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Set primary rarity assessment failed:', error.message)
      }
    },
  })
}

// Export types for convenience
export type { RarityAssessment, RarityAssessmentListResponse }
