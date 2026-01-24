/**
 * React Query hooks for audit functionality.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";
import api from "@/lib/api";
import type {
  Discrepancy,
  Enrichment,
  AuditRun,
  AuditRunProgress,
  AuditSummary,
  CoinAuditSummary,
  PaginatedResponse,
  DiscrepancyFilters,
  EnrichmentFilters,
  StartAuditRequest,
  ResolveDiscrepancyRequest,
  ImageDownloadResult,
} from "@/types/audit";

// =============================================================================
// Query Keys
// =============================================================================

export const auditKeys = {
  all: ["audit"] as const,
  summary: () => [...auditKeys.all, "summary"] as const,
  runs: () => [...auditKeys.all, "runs"] as const,
  run: (id: number) => [...auditKeys.runs(), id] as const,
  runProgress: (id: number) => [...auditKeys.run(id), "progress"] as const,
  discrepancies: () => [...auditKeys.all, "discrepancies"] as const,
  discrepancyList: (filters: DiscrepancyFilters) =>
    [...auditKeys.discrepancies(), filters] as const,
  discrepancy: (id: number) => [...auditKeys.discrepancies(), id] as const,
  coinDiscrepancies: (coinId: number) =>
    [...auditKeys.discrepancies(), "coin", coinId] as const,
  enrichments: () => [...auditKeys.all, "enrichments"] as const,
  enrichmentList: (filters: EnrichmentFilters) =>
    [...auditKeys.enrichments(), filters] as const,
  enrichment: (id: number) => [...auditKeys.enrichments(), id] as const,
  coinEnrichments: (coinId: number) =>
    [...auditKeys.enrichments(), "coin", coinId] as const,
  stats: () => [...auditKeys.all, "stats"] as const,
  fields: () => [...auditKeys.all, "fields"] as const,
  trustLevels: () => [...auditKeys.all, "trust-levels"] as const,
};

// =============================================================================
// Audit Summary & Statistics
// =============================================================================

export function useAuditSummary() {
  return useQuery({
    queryKey: auditKeys.summary(),
    queryFn: async () => {
      const { data } = await api.get<AuditSummary>("/api/audit/summary");
      return data;
    },
  });
}

export function useDiscrepancyStats() {
  return useQuery({
    queryKey: [...auditKeys.stats(), "discrepancies"],
    queryFn: async () => {
      const { data } = await api.get("/api/audit/stats/discrepancies");
      return data;
    },
  });
}

export function useEnrichmentStats() {
  return useQuery({
    queryKey: [...auditKeys.stats(), "enrichments"],
    queryFn: async () => {
      const { data } = await api.get("/api/audit/stats/enrichments");
      return data;
    },
  });
}

// =============================================================================
// Audit Runs
// =============================================================================

export function useAuditRuns(page = 1, perPage = 20) {
  return useQuery({
    queryKey: [...auditKeys.runs(), page, perPage],
    queryFn: async () => {
      const { data } = await api.get<AuditRun[]>("/api/audit/runs", {
        params: { page, per_page: perPage },
      });
      return data;
    },
  });
}

export function useAuditRun(runId: number) {
  return useQuery({
    queryKey: auditKeys.run(runId),
    queryFn: async () => {
      const { data } = await api.get<AuditRun>(`/api/audit/runs/${runId}`);
      return data;
    },
    enabled: runId > 0,
  });
}

export function useAuditRunProgress(runId: number, enabled = true) {
  return useQuery({
    queryKey: auditKeys.runProgress(runId),
    queryFn: async () => {
      const { data } = await api.get<AuditRunProgress>(
        `/api/audit/runs/${runId}/progress`
      );
      return data;
    },
    enabled: enabled && runId > 0,
    refetchInterval: (query) => {
      // Poll every 2s while running, stop when complete
      if (query.state.data?.status === "running") {
        return 2000;
      }
      return false;
    },
  });
}

export function useStartAudit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: StartAuditRequest) => {
      const { data } = await api.post<AuditRun>("/api/audit/run", request);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.runs() });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
    },
  });
}

export function useAuditCoin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (coinId: number) => {
      const { data } = await api.post<CoinAuditSummary>(
        `/api/audit/coin/${coinId}`
      );
      return data;
    },
    onSuccess: (_, coinId) => {
      queryClient.invalidateQueries({ queryKey: auditKeys.coinDiscrepancies(coinId) });
      queryClient.invalidateQueries({ queryKey: auditKeys.coinEnrichments(coinId) });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
    },
  });
}

/**
 * Hook to start an audit and poll for completion.
 */
export function useAuditWithPolling() {
  const [runId, setRunId] = useState<number | null>(null);
  const startAudit = useStartAudit();
  const { data: progress, isLoading: isPolling } = useAuditRunProgress(
    runId ?? 0,
    runId !== null
  );

  const start = useCallback(
    async (request: StartAuditRequest) => {
      const run = await startAudit.mutateAsync(request);
      setRunId(run.id);
      return run;
    },
    [startAudit]
  );

  const isComplete = progress?.status === "completed" || progress?.status === "failed";

  useEffect(() => {
    if (isComplete) {
      // Clear runId when complete
      setRunId(null);
    }
  }, [isComplete]);

  return {
    start,
    progress,
    isStarting: startAudit.isPending,
    isPolling: isPolling && runId !== null,
    isComplete,
    error: startAudit.error,
    reset: () => setRunId(null),
  };
}

// =============================================================================
// Discrepancies
// =============================================================================

export function useDiscrepancies(filters: DiscrepancyFilters = {}) {
  return useQuery({
    queryKey: auditKeys.discrepancyList(filters),
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Discrepancy>>(
        "/api/audit/discrepancies",
        { params: filters }
      );
      return data;
    },
  });
}

export function useDiscrepancy(id: number) {
  return useQuery({
    queryKey: auditKeys.discrepancy(id),
    queryFn: async () => {
      const { data } = await api.get<Discrepancy>(
        `/api/audit/discrepancies/${id}`
      );
      return data;
    },
    enabled: id > 0,
  });
}

export function useCoinDiscrepancies(coinId: number) {
  return useQuery({
    queryKey: auditKeys.coinDiscrepancies(coinId),
    queryFn: async () => {
      const { data } = await api.get<Discrepancy[]>(
        `/api/audit/coin/${coinId}/discrepancies`
      );
      return data;
    },
    enabled: coinId > 0,
  });
}

export function useResolveDiscrepancy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      request,
    }: {
      id: number;
      request: ResolveDiscrepancyRequest;
    }) => {
      const { data } = await api.post<Discrepancy>(
        `/api/audit/discrepancies/${id}/resolve`,
        request
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: auditKeys.discrepancies() });
      queryClient.invalidateQueries({
        queryKey: auditKeys.coinDiscrepancies(data.coin_id),
      });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
    },
  });
}

export function useBulkResolveDiscrepancies() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      discrepancy_ids,
      resolution,
      notes,
    }: {
      discrepancy_ids: number[];
      resolution: "accepted" | "rejected" | "ignored";
      notes?: string;
    }) => {
      const { data } = await api.post("/api/audit/discrepancies/bulk-resolve", {
        discrepancy_ids,
        resolution,
        notes,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.discrepancies() });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
    },
  });
}

// =============================================================================
// Enrichments
// =============================================================================

export function useEnrichments(filters: EnrichmentFilters = {}) {
  return useQuery({
    queryKey: auditKeys.enrichmentList(filters),
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Enrichment>>(
        "/api/audit/enrichments",
        { params: filters }
      );
      return data;
    },
  });
}

export function useEnrichment(id: number) {
  return useQuery({
    queryKey: auditKeys.enrichment(id),
    queryFn: async () => {
      const { data } = await api.get<Enrichment>(
        `/api/audit/enrichments/${id}`
      );
      return data;
    },
    enabled: id > 0,
  });
}

export function useCoinEnrichments(coinId: number) {
  return useQuery({
    queryKey: auditKeys.coinEnrichments(coinId),
    queryFn: async () => {
      const { data } = await api.get<Enrichment[]>(
        `/api/audit/coin/${coinId}/enrichments`
      );
      return data;
    },
    enabled: coinId > 0,
  });
}

export function useApplyEnrichment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<Enrichment>(
        `/api/audit/enrichments/${id}/apply`
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: auditKeys.enrichments() });
      queryClient.invalidateQueries({
        queryKey: auditKeys.coinEnrichments(data.coin_id),
      });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
      // Also invalidate coin data since it was updated
      queryClient.invalidateQueries({ queryKey: ["coins", data.coin_id] });
    },
  });
}

export function useAutoApplyAllEnrichments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<{
        applied: number;
        failed: number;
        total: number;
        applied_by_field: Record<string, number>;
      }>("/api/audit/enrichments/auto-apply-empty");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.enrichments() });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useRejectEnrichment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, reason }: { id: number; reason?: string }) => {
      const { data } = await api.post<Enrichment>(
        `/api/audit/enrichments/${id}/reject`,
        null,
        { params: { reason } }
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: auditKeys.enrichments() });
      queryClient.invalidateQueries({
        queryKey: auditKeys.coinEnrichments(data.coin_id),
      });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
    },
  });
}

export function useBulkApplyEnrichments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (enrichment_ids: number[]) => {
      const { data } = await api.post("/api/audit/enrichments/bulk-apply", {
        enrichment_ids,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.enrichments() });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useBulkRejectEnrichments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      enrichment_ids,
      reason,
    }: {
      enrichment_ids: number[];
      reason?: string;
    }) => {
      const { data } = await api.post("/api/audit/enrichments/bulk-reject", {
        enrichment_ids,
        reason,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.enrichments() });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
    },
  });
}

export function useAutoEnrichCoin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (coinId: number) => {
      const { data } = await api.post(`/api/audit/coin/${coinId}/auto-enrich`);
      return data;
    },
    onSuccess: (_, coinId) => {
      queryClient.invalidateQueries({ queryKey: auditKeys.coinEnrichments(coinId) });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["coins", coinId] });
    },
  });
}

// =============================================================================
// Image Downloads
// =============================================================================

export function useDownloadCoinImages() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      coinId,
      auctionDataId,
    }: {
      coinId: number;
      auctionDataId?: number;
    }) => {
      const { data } = await api.post<ImageDownloadResult>(
        `/api/audit/coin/${coinId}/download-images`,
        auctionDataId ? { auction_data_id: auctionDataId } : {}
      );
      return data;
    },
    onSuccess: (_, { coinId }) => {
      // Invalidate coin images
      queryClient.invalidateQueries({ queryKey: ["coins", coinId, "images"] });
      queryClient.invalidateQueries({ queryKey: ["coins", coinId] });
    },
  });
}

// =============================================================================
// Metadata
// =============================================================================

export function useAuditableFields() {
  return useQuery({
    queryKey: auditKeys.fields(),
    queryFn: async () => {
      const { data } = await api.get("/api/audit/fields");
      return data;
    },
    staleTime: Infinity, // Static data
  });
}

export function useTrustLevels() {
  return useQuery({
    queryKey: auditKeys.trustLevels(),
    queryFn: async () => {
      const { data } = await api.get("/api/audit/trust-levels");
      return data;
    },
    staleTime: Infinity, // Static data
  });
}

// =============================================================================
// Auto-Merge
// =============================================================================

export interface AutoMergePreviewResult {
  summary: {
    total_coins: number;
    will_auto_fill: number;
    will_auto_update: number;
    will_flag: number;
    will_skip: number;
  };
  details: AutoMergeCoinResult[];
}

export interface AutoMergeCoinResult {
  batch_id: string;
  coin_id: number;
  auction_data_id: number | null;
  auto_filled: FieldChange[];
  auto_updated: FieldChange[];
  skipped: Array<{ field: string; reason: string; current_value: unknown }>;
  flagged: FieldChange[];
  errors: string[];
  total_changes: number;
  rollback_available: boolean;
}

export interface FieldChange {
  field: string;
  old: unknown;
  new: unknown;
  old_source: string | null;
  new_source: string;
  conflict_type: string | null;
  reason: string;
}

export interface MergeBatch {
  batch_id: string;
  changes: number;
  coins_affected: number;
  started_at: string;
  rollback_available: boolean;
}

export interface FieldHistoryEntry {
  id: number;
  field: string;
  old_value: unknown;
  new_value: unknown;
  old_source: string | null;
  new_source: string | null;
  change_type: string;
  changed_at: string;
  changed_by: string;
  batch_id: string | null;
  conflict_type: string | null;
  reason: string | null;
}

export interface RollbackResult {
  batch_id: string;
  restored: number;
  fields_affected: string[];
  coins_affected: number[];
}

export const autoMergeKeys = {
  all: ["autoMerge"] as const,
  batches: () => [...autoMergeKeys.all, "batches"] as const,
  history: (coinId: number) => [...autoMergeKeys.all, "history", coinId] as const,
  preview: (coinIds: number[]) => [...autoMergeKeys.all, "preview", coinIds] as const,
};

export function useMergeBatches(limit = 20) {
  return useQuery({
    queryKey: autoMergeKeys.batches(),
    queryFn: async () => {
      const { data } = await api.get<MergeBatch[]>("/api/audit/batches", {
        params: { limit },
      });
      return data;
    },
  });
}

export function useFieldHistory(coinId: number, field?: string) {
  return useQuery({
    queryKey: [...autoMergeKeys.history(coinId), field],
    queryFn: async () => {
      const params: Record<string, unknown> = { limit: 50 };
      if (field) params.field = field;
      const { data } = await api.get<FieldHistoryEntry[]>(
        `/api/audit/field-history/${coinId}`,
        { params }
      );
      return data;
    },
    enabled: coinId > 0,
  });
}

export function useAutoMergePreview() {
  return useMutation({
    mutationFn: async (coinIds: number[]) => {
      const { data } = await api.post<AutoMergePreviewResult>(
        "/api/audit/auto-merge/preview",
        { coin_ids: coinIds }
      );
      return data;
    },
  });
}

export function useAutoMergeBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      coinIds,
      confirmed = false,
    }: {
      coinIds: number[];
      confirmed?: boolean;
    }) => {
      const { data } = await api.post("/api/audit/auto-merge", {
        coin_ids: coinIds,
        confirmed,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: autoMergeKeys.batches() });
      queryClient.invalidateQueries({ queryKey: auditKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useAutoMergeSingle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      coinId,
      auctionDataId,
    }: {
      coinId: number;
      auctionDataId?: number;
    }) => {
      const { data } = await api.post<AutoMergeCoinResult>(
        `/api/audit/coin/${coinId}/auto-merge`,
        auctionDataId ? { auction_data_id: auctionDataId } : {}
      );
      return data;
    },
    onSuccess: (_, { coinId }) => {
      queryClient.invalidateQueries({ queryKey: autoMergeKeys.batches() });
      queryClient.invalidateQueries({ queryKey: autoMergeKeys.history(coinId) });
      queryClient.invalidateQueries({ queryKey: ["coins", coinId] });
    },
  });
}

export function useRollbackBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (batchId: string) => {
      const { data } = await api.post<RollbackResult>(
        `/api/audit/rollback/${batchId}`
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: autoMergeKeys.batches() });
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useVerifyField() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      coinId,
      field,
      userNote,
    }: {
      coinId: number;
      field: string;
      userNote?: string;
    }) => {
      const { data } = await api.post(
        `/api/audit/field/${coinId}/${field}/verify`,
        userNote ? { user_note: userNote } : {}
      );
      return data;
    },
    onSuccess: (_, { coinId }) => {
      queryClient.invalidateQueries({ queryKey: ["coins", coinId] });
      queryClient.invalidateQueries({ queryKey: autoMergeKeys.history(coinId) });
    },
  });
}

export function useUnverifyField() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ coinId, field }: { coinId: number; field: string }) => {
      const { data } = await api.delete(
        `/api/audit/field/${coinId}/${field}/verify`
      );
      return data;
    },
    onSuccess: (_, { coinId }) => {
      queryClient.invalidateQueries({ queryKey: ["coins", coinId] });
    },
  });
}
