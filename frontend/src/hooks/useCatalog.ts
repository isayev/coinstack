import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types
export interface CatalogCandidate {
  external_id: string;
  external_url: string | null;
  confidence: number;
  name: string | null;
  description: string | null;
}

export interface LookupResponse {
  status: "success" | "not_found" | "ambiguous" | "deferred" | "error";
  external_id: string | null;
  external_url: string | null;
  confidence: number;
  candidates: CatalogCandidate[] | null;
  payload: Record<string, unknown> | null;
  error_message: string | null;
  reference_type_id: number | null;
  last_lookup: string | null;
  cache_hit: boolean;
}

export interface Conflict {
  field: string;
  current: unknown;
  catalog: unknown;
  note: string | null;
}

export interface EnrichmentDiff {
  fills: Record<string, unknown>;
  conflicts: Record<string, Conflict>;
  unchanged: string[];
  fill_count: number;
  conflict_count: number;
  unchanged_count: number;
  has_changes: boolean;
}

export interface EnrichResponse {
  success: boolean;
  coin_id: number;
  diff: EnrichmentDiff;
  applied_fills: string[];
  applied_conflicts: string[];
  error: string | null;
}

export interface BulkEnrichResponse {
  job_id: string;
  total_coins: number;
  status: string;
  message: string | null;
}

export interface JobStatus {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress: number;
  total: number;
  updated: number;
  conflicts: number;
  not_found: number;
  errors: number;
  results: Array<{ coin_id: number; status: string }> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ReferenceType {
  id: number;
  system: string;
  local_ref: string;
  local_ref_normalized: string | null;
  external_id: string | null;
  external_url: string | null;
  lookup_status: string | null;
  lookup_confidence: number | null;
  last_lookup: string | null;
  payload: Record<string, unknown> | null;
}

// API functions
async function lookupReference(request: {
  raw_reference?: string;
  context?: Record<string, unknown>;
}): Promise<LookupResponse> {
  if (!request.raw_reference) throw new Error("Reference required");
  
  // Use V2 LLM Catalog Parse
  const response = await api.post("/api/v2/llm/catalog/parse", {
    reference: request.raw_reference
  });
  
  const data = response.data;
  
  return {
    status: "success",
    external_id: data.raw_reference,
    external_url: null,
    confidence: data.confidence,
    candidates: [],
    // Map parsed data to payload for form auto-population
    payload: {
      authority: data.issuer,
      mint: data.mint,
      date_from: data.year_start,
      date_to: data.year_end,
      metal: data.metal,
      obverse_description: data.obverse_description,
      reverse_description: data.reverse_description
    },
    error_message: null,
    reference_type_id: null,
    last_lookup: new Date().toISOString(),
    cache_hit: false
  };
}

async function enrichCoin(
  coinId: number,
  dryRun: boolean = true,
  applyConflicts: string[] = []
): Promise<EnrichResponse> {
  const response = await api.post(`/api/catalog/enrich/${coinId}`, {
    dry_run: dryRun,
    apply_conflicts: applyConflicts,
  });
  return response.data;
}

async function bulkEnrich(request: {
  coin_ids?: number[];
  missing_fields?: string[];
  reference_system?: string;
  category?: string;
  dry_run?: boolean;
  max_coins?: number;
}): Promise<BulkEnrichResponse> {
  const response = await api.post("/api/catalog/bulk-enrich", request);
  return response.data;
}

async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await api.get(`/api/catalog/job/${jobId}`);
  return response.data;
}

async function getReferenceTypes(params?: {
  system?: string;
  status?: string;
  limit?: number;
}): Promise<ReferenceType[]> {
  const response = await api.get("/api/catalog/reference-types", { params });
  return response.data;
}

// Hooks
export function useLookupReference() {
  return useMutation({
    mutationFn: lookupReference,
  });
}

export function useEnrichCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({
      coinId,
      dryRun = true,
      applyConflicts = [],
    }: {
      coinId: number;
      dryRun?: boolean;
      applyConflicts?: string[];
    }) => enrichCoin(coinId, dryRun, applyConflicts),
    onSuccess: (_, variables) => {
      if (!variables.dryRun) {
        queryClient.invalidateQueries({ queryKey: ["coin", variables.coinId] });
        queryClient.invalidateQueries({ queryKey: ["coins"] });
      }
    },
  });
}

export function useBulkEnrich() {
  return useMutation({
    mutationFn: bulkEnrich,
  });
}

export function useJobStatus(jobId: string | null, options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: options?.refetchInterval,
  });
}

export function useReferenceTypes(params?: {
  system?: string;
  status?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["reference-types", params],
    queryFn: () => getReferenceTypes(params),
  });
}
