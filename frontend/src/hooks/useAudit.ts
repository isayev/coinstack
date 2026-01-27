import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

import {
  Discrepancy,
  Enrichment,
  DiscrepancyFilters,
  EnrichmentFilters,
  AuditSummary,
  AuditRunProgress,
  ImageDownloadResult,
  PaginatedResponse,
  DiscrepancyStatus,
  EnrichmentStatus,
  TrustLevel,
  LLMSuggestionItem,
  LLMReviewQueueResponse,
} from "@/types/audit";

// Re-export types for convenience
export type {
  Discrepancy,
  Enrichment,
  DiscrepancyFilters,
  EnrichmentFilters,
  DiscrepancyStatus,
  EnrichmentStatus,
  TrustLevel
};

export interface AutoMergePreviewResult {
  total_coins: number;
  changes: number;
  details: any[];
}

export interface MergeBatch {
  id: string;
  status: string;
  created_at: string;
  summary?: {
    auto_filled: number;
    auto_updated: number;
  };
}

export interface FieldChange {
  field: string;
  old_value: any;
  new_value: any;
}

export interface FieldHistoryEntry {
  id: number;
  coin_id: number;
  field: string;
  old_value: any;
  new_value: any;
  change_type: string;
  new_source?: string;
  reason?: string;
  changed_at: string;
  batch_id?: string;
}

/**
 * STUB: Discrepancies query - returns empty data
 * TODO: Implement /api/v2/audit/discrepancies endpoint
 */
export function useDiscrepancies(filters: DiscrepancyFilters = {}) {
  return useQuery({
    queryKey: ["discrepancies", filters],
    queryFn: async () => {
      // STUB: Backend endpoint not implemented
      return {
        items: [] as Discrepancy[],
        total: 0,
        pages: 1,
        page: 1,
        _isStub: true,
      } as PaginatedResponse<Discrepancy> & { _isStub: boolean };
    },
    staleTime: Infinity, // Stub data never becomes stale
  });
}

/**
 * STUB: Enrichments query - returns empty data
 * TODO: Implement /api/v2/audit/enrichments endpoint
 */
export function useEnrichments(filters: EnrichmentFilters = {}) {
  return useQuery({
    queryKey: ["enrichments", filters],
    queryFn: async () => {
      // STUB: Backend endpoint not implemented
      return {
        items: [] as Enrichment[],
        total: 0,
        pages: 1,
        page: 1,
        _isStub: true,
      } as PaginatedResponse<Enrichment> & { _isStub: boolean };
    },
    staleTime: Infinity,
  });
}

/**
 * STUB: Audit summary query - returns empty data
 * TODO: Implement /api/v2/audit/summary endpoint
 */
export function useAuditSummary() {
  return useQuery({
    queryKey: ["audit-summary"],
    queryFn: async () => {
      // STUB: Backend endpoint not implemented
      return {
        pending_discrepancies: 0,
        pending_enrichments: 0,
        discrepancies_by_trust: { authoritative: 0, high: 0, medium: 0, low: 0, untrusted: 0 },
        discrepancies_by_field: {},
        discrepancies_by_source: {},
        recent_runs: [],
        _isStub: true,
      } as AuditSummary & { _isStub: boolean };
    },
    staleTime: Infinity,
  });
}

/**
 * STUB: Audit polling hook - not functional
 * TODO: Implement real audit polling with WebSocket or polling
 */
export function useAuditWithPolling() {
  const start = useMutation({
    mutationFn: async (_params: { scope: string }) => {
      // STUB: No-op
      return { run_id: 123, _isStub: true };
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Audit start failed:', error.message);
      }
    },
  });

  return {
    start: start.mutate,
    progress: null as AuditRunProgress | null,
    isStarting: start.isPending,
    isPolling: false,
    isComplete: false,
    _isStub: true,
  };
}

/**
 * STUB: Bulk resolve discrepancies - no-op
 * TODO: Implement /api/v2/audit/discrepancies/resolve endpoint
 */
export function useBulkResolveDiscrepancies() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { discrepancy_ids: number[], resolution: string }) => {
      // STUB: No-op
      return { resolved: params.discrepancy_ids.length, _isStub: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["discrepancies"] });
      queryClient.invalidateQueries({ queryKey: ["audit-summary"] });
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Bulk resolve failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Bulk apply enrichments - no-op
 * TODO: Implement /api/v2/audit/enrichments/apply endpoint
 */
export function useBulkApplyEnrichments() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (ids: number[]) => {
      // STUB: No-op
      return { applied: ids.length, _isStub: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enrichments"] });
      queryClient.invalidateQueries({ queryKey: ["audit-summary"] });
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Bulk apply failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Auto-apply all enrichments - no-op
 * TODO: Implement /api/v2/audit/enrichments/auto-apply endpoint
 */
export function useAutoApplyAllEnrichments() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      // STUB: No-op
      return { applied: 0, applied_by_field: {} as Record<string, number>, _isStub: true };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enrichments"] });
      queryClient.invalidateQueries({ queryKey: ["audit-summary"] });
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Auto apply failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Field history query - returns empty data
 * TODO: Implement /api/v2/audit/field-history endpoint
 */
export function useFieldHistory(coinId: number) {
  return useQuery({
    queryKey: ["field-history", coinId],
    queryFn: async () => {
      // STUB: No-op
      return [] as FieldHistoryEntry[];
    },
    enabled: coinId > 0,
    staleTime: Infinity,
  });
}

/**
 * STUB: Merge batches query - returns empty data
 * TODO: Implement /api/v2/audit/merge-batches endpoint
 */
export function useMergeBatches() {
  return useQuery({
    queryKey: ["merge-batches"],
    queryFn: async () => [] as MergeBatch[],
    staleTime: Infinity,
  });
}

/**
 * STUB: Auto-merge preview - no-op
 * TODO: Implement /api/v2/audit/merge/preview endpoint
 */
export function useAutoMergePreview() {
  return useMutation({
    mutationFn: async (_params: unknown) => {
      // STUB: No-op
      return { total_coins: 0, changes: 0, details: [], _isStub: true } as AutoMergePreviewResult & { _isStub: boolean };
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Auto merge preview failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Auto-merge batch - no-op
 * TODO: Implement /api/v2/audit/merge/execute endpoint
 */
export function useAutoMergeBatch() {
  return useMutation({
    mutationFn: async (_params: unknown) => {
      // STUB: No-op
      return { batch_id: "123", summary: { auto_filled: 0, auto_updated: 0 }, _isStub: true };
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Auto merge batch failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Rollback batch - no-op
 * TODO: Implement /api/v2/audit/merge/rollback endpoint
 */
export function useRollbackBatch() {
  return useMutation({
    mutationFn: async (_batchId: string) => {
      // STUB: No-op
      return { status: "success", _isStub: true };
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Rollback batch failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Download coin images - no-op
 * TODO: Implement /api/v2/coins/{id}/download-images endpoint
 */
export function useDownloadCoinImages() {
  return useMutation({
    mutationFn: async (params: { coinId: number, auctionDataId?: number }) => {
      // STUB: No-op
      return { coin_id: params.coinId, _isStub: true } as ImageDownloadResult & { _isStub: boolean };
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Download images failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Resolve discrepancy - no-op
 * TODO: Implement /api/v2/audit/discrepancies/{id}/resolve endpoint
 */
export function useResolveDiscrepancy() {
  return useMutation({
    mutationFn: async (_params: { id: number, request: unknown }) => {
      // STUB: No-op
      return { status: "success", _isStub: true };
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Resolve discrepancy failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Apply enrichment - no-op
 * TODO: Implement /api/v2/audit/enrichments/{id}/apply endpoint
 */
export function useApplyEnrichment() {
  return useMutation({
    mutationFn: async (params: { id: number }) => {
      // STUB: No-op
      return { status: "success", id: params.id, _isStub: true };
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Apply enrichment failed:', error.message);
      }
    },
  });
}

/**
 * STUB: Reject enrichment - no-op
 * TODO: Implement /api/v2/audit/enrichments/{id}/reject endpoint
 */
export function useRejectEnrichment() {
  return useMutation({
    mutationFn: async (params: { id: number }) => {
      // STUB: No-op
      return { status: "success", id: params.id, _isStub: true };
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Reject enrichment failed:', error.message);
      }
    },
  });
}

// =============================================================================
// LLM Suggestions Review Queue
// =============================================================================

export function useLLMSuggestions() {
  return useQuery({
    queryKey: ["llm-suggestions"],
    queryFn: async () => {
      const response = await api.get<LLMReviewQueueResponse>("/api/v2/llm/review");
      return response.data;
    },
  });
}

export function useDismissLLMSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { coinId: number; dismissReferences?: boolean; dismissRarity?: boolean }) => {
      const response = await api.post(`/api/v2/llm/review/${params.coinId}/dismiss`, null, {
        params: {
          dismiss_references: params.dismissReferences ?? true,
          dismiss_rarity: params.dismissRarity ?? true,
        },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm-suggestions"] });
    },
  });
}

// Re-export LLM types for convenience
export type { LLMSuggestionItem, LLMReviewQueueResponse };
