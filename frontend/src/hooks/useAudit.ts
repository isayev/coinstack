import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

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
  TrustLevel
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

export function useDiscrepancies(filters: DiscrepancyFilters = {}) {
  return useQuery({
    queryKey: ["discrepancies", filters],
    queryFn: async () => {
      return {
        items: [] as Discrepancy[],
        total: 0,
        pages: 1,
        page: 1
      } as PaginatedResponse<Discrepancy>;
    }
  });
}

export function useEnrichments(filters: EnrichmentFilters = {}) {
  return useQuery({
    queryKey: ["enrichments", filters],
    queryFn: async () => {
      return {
        items: [] as Enrichment[],
        total: 0,
        pages: 1,
        page: 1
      } as PaginatedResponse<Enrichment>;
    }
  });
}

export function useAuditSummary() {
  return useQuery({
    queryKey: ["audit-summary"],
    queryFn: async () => {
      return {
        pending_discrepancies: 0,
        pending_enrichments: 0,
        discrepancies_by_trust: { authoritative: 0, high: 0, medium: 0, low: 0, untrusted: 0 },
        discrepancies_by_field: {},
        discrepancies_by_source: {},
        recent_runs: []
      } as AuditSummary;
    }
  });
}

export function useAuditWithPolling() {
  const start = useMutation({
    mutationFn: async (_params: { scope: string }) => {
      return { run_id: 123 };
    }
  });

  return {
    start: start.mutate,
    progress: null as AuditRunProgress | null,
    isStarting: start.isPending,
    isPolling: false,
    isComplete: false
  };
}

export function useBulkResolveDiscrepancies() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (params: { discrepancy_ids: number[], resolution: string }) => {
      return { resolved: params.discrepancy_ids.length };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["discrepancies"] });
      queryClient.invalidateQueries({ queryKey: ["audit-summary"] });
    }
  });
}

export function useBulkApplyEnrichments() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (ids: number[]) => {
      return { applied: ids.length };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enrichments"] });
      queryClient.invalidateQueries({ queryKey: ["audit-summary"] });
    }
  });
}

export function useAutoApplyAllEnrichments() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return { applied: 0, applied_by_field: {} as Record<string, number> };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enrichments"] });
      queryClient.invalidateQueries({ queryKey: ["audit-summary"] });
    }
  });
}

export function useFieldHistory(coinId: number) {
  return useQuery({
    queryKey: ["field-history", coinId],
    queryFn: async () => {
      return [] as FieldHistoryEntry[];
    },
    enabled: coinId > 0
  });
}

export function useMergeBatches() {
  return useQuery({
    queryKey: ["merge-batches"],
    queryFn: async () => [] as MergeBatch[]
  });
}

export function useAutoMergePreview() {
  return useMutation({
    mutationFn: async (_params: any) => {
      return { total_coins: 0, changes: 0, details: [] } as AutoMergePreviewResult;
    }
  });
}

export function useAutoMergeBatch() {
  return useMutation({
    mutationFn: async (_params: any) => {
      return { batch_id: "123", summary: { auto_filled: 0, auto_updated: 0 } };
    }
  });
}

export function useRollbackBatch() {
  return useMutation({
    mutationFn: async (_batchId: string) => {
      return { status: "success" };
    }
  });
}

export function useDownloadCoinImages() {
  return useMutation({
    mutationFn: async (params: { coinId: number, auctionDataId?: number }) => {
      return { coin_id: params.coinId } as ImageDownloadResult;
    }
  });
}

export function useResolveDiscrepancy() {
  return useMutation({
    mutationFn: async (_params: { id: number, request: any }) => {
      return { status: "success" };
    }
  });
}

export function useApplyEnrichment() {
  return useMutation({
    mutationFn: async (params: { id: number }) => {
      return { status: "success", id: params.id };
    }
  });
}

export function useRejectEnrichment() {
  return useMutation({
    mutationFn: async (params: { id: number }) => {
      return { status: "success", id: params.id };
    }
  });
}
