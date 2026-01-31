/**
 * useLLM - React hooks for LLM-powered numismatic operations
 * 
 * Connects to /api/v2/llm/* endpoints for:
 * - Legend expansion
 * - Condition observations
 * - Historical context generation
 * 
 * @module hooks/useLLM
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api/api";

// ============================================================================
// Types
// ============================================================================

export interface LegendExpandRequest {
  abbreviation: string;
}

export interface LegendExpandResponse {
  expanded: string;
  confidence: number;
  cost_usd: number;
  model_used: string;
  cached: boolean;
}

export interface ConditionObserveRequest {
  image_b64: string;
  hints?: Record<string, any>;
}

export interface ConditionObserveResponse {
  wear_observations: string;
  surface_notes: string;
  strike_quality: string;
  notable_features: string[];
  concerns: string[];
  recommendation: string;
  confidence: number;
  cost_usd: number;
}

export interface HistoricalContextRequest {
  coin_id: number;
  // Backend fetches all coin data from DB - no need to pass fields
}

export interface RarityInfo {
  rarity_code: string | null;
  rarity_description: string | null;
  specimens_known: string | null;
  source: string | null;
}

export interface ContextSection {
  key: string;
  title: string;
  content: string;
}

export interface HistoricalContextResponse {
  sections: ContextSection[];
  raw_content: string;
  confidence: number;
  cost_usd: number;
  model_used: string;
  // Citation tracking for audit
  existing_references: string[];
  all_llm_citations: string[];      // All references LLM cited in response
  suggested_references: string[];   // New refs found by LLM, not in DB
  matched_references: string[];     // LLM refs that matched DB refs
  // Rarity tracking for audit
  rarity_info: RarityInfo | null;
}

/** Which provider API keys are set (presence only; values never exposed). */
export interface ProviderKeysStatus {
  anthropic: boolean;
  openrouter: boolean;
  google: boolean;
}

export interface LLMStatusResponse {
  status: string;
  profile: string;
  monthly_cost_usd: number;
  monthly_budget_usd: number;
  budget_remaining_usd: number;
  capabilities_available: string[];
  ollama_available: boolean;
  provider_keys?: ProviderKeysStatus;
}

/** Cost and usage report from GET /api/v2/llm/cost-report */
export interface LLMCostReportResponse {
  period_days: number;
  total_cost_usd: number;
  by_capability: Record<string, number>;
  by_model: Record<string, number>;
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * Expand abbreviated Latin legend
 * 
 * @example
 * const expandLegend = useExpandLegendV2();
 * expandLegend.mutate({ abbreviation: "IMP CAES AVG" });
 */
export function useExpandLegendV2() {
  return useMutation({
    mutationFn: async (request: LegendExpandRequest): Promise<LegendExpandResponse> => {
      const response = await api.post<LegendExpandResponse>(
        "/api/v2/llm/legend/expand",
        request
      );
      return response.data;
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Legend expansion failed:', error.message);
      }
    },
  });
}

/**
 * Observe coin condition from image (NOT grades)
 * 
 * @example
 * const observeCondition = useObserveCondition();
 * observeCondition.mutate({ image_b64: base64Image });
 */
export function useObserveCondition() {
  return useMutation({
    mutationFn: async (request: ConditionObserveRequest): Promise<ConditionObserveResponse> => {
      const response = await api.post<ConditionObserveResponse>(
        "/api/v2/llm/condition/observe",
        request
      );
      return response.data;
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Condition observation failed:', error.message);
      }
    },
  });
}

/**
 * Generate historical context for a coin
 * 
 * This is a custom endpoint that generates and stores historical context
 * based on coin attributes (issuer, dates, category).
 * 
 * @example
 * const generateContext = useGenerateHistoricalContext();
 * generateContext.mutate({ coin_id: 123, issuer: "Augustus" });
 */
export function useGenerateHistoricalContext() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: HistoricalContextRequest): Promise<HistoricalContextResponse> => {
      const response = await api.post<HistoricalContextResponse>(
        "/api/v2/llm/context/generate",
        request
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      // Invalidate coin query to refresh with new historical context
      queryClient.invalidateQueries({ queryKey: ["coin", variables.coin_id] });
    },
  });
}

/**
 * Get LLM service status (mutation - call mutate() to fetch).
 *
 * @example
 * const statusMutation = useLLMStatus();
 * statusMutation.mutate();
 */
export function useLLMStatus() {
  return useMutation({
    mutationFn: async (): Promise<LLMStatusResponse> => {
      const response = await api.get<LLMStatusResponse>("/api/v2/llm/status");
      return response.data;
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('LLM status check failed:', error.message);
      }
    },
  });
}

/**
 * LLM status query - fetches on mount/refetch. Use on Settings page.
 */
export function useLLMStatusQuery() {
  return useQuery({
    queryKey: ["llm-status"],
    queryFn: async (): Promise<LLMStatusResponse> => {
      const response = await api.get<LLMStatusResponse>("/api/v2/llm/status");
      return response.data;
    },
  });
}

/**
 * LLM cost report - usage and cost by capability/model.
 *
 * @param days Period in days (1–365), default 30
 */
export function useLLMCostReport(days: number = 30) {
  return useQuery({
    queryKey: ["llm-cost-report", days],
    queryFn: async (): Promise<LLMCostReportResponse> => {
      const response = await api.get<LLMCostReportResponse>("/api/v2/llm/cost-report", {
        params: { days },
      });
      return response.data;
    },
  });
}

/**
 * Submit feedback on LLM suggestion
 */
export interface FeedbackRequest {
  coin_id: number;
  capability: string;
  field: string;
  suggested_value: any;
  action: 'accepted' | 'rejected' | 'modified';
  user_value?: any;
  reason?: string;
  confidence: number;
  model_used: string;
}

export function useSubmitLLMFeedback() {
  return useMutation({
    mutationFn: async (request: FeedbackRequest): Promise<{ status: string; event_id: string }> => {
      const response = await api.post("/api/v2/llm/feedback", request);
      return response.data;
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('LLM feedback submission failed:', error.message);
      }
    },
  });
}

/**
 * Parse auction description
 */
export interface AuctionParseRequest {
  description: string;
  hints?: Record<string, any>;
}

export interface AuctionParseResponse {
  issuer: string | null;
  denomination: string | null;
  metal: string | null;
  mint: string | null;
  year_start: number | null;
  year_end: number | null;
  weight_g: number | null;
  diameter_mm: number | null;
  obverse_legend: string | null;
  obverse_description: string | null;
  reverse_legend: string | null;
  reverse_description: string | null;
  references: string[];
  grade: string | null;
  confidence: number;
  cost_usd: number;
}

export function useParseAuction() {
  return useMutation({
    mutationFn: async (request: AuctionParseRequest): Promise<AuctionParseResponse> => {
      const response = await api.post<AuctionParseResponse>(
        "/api/v2/llm/auction/parse",
        request
      );
      return response.data;
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Auction parsing failed:', error.message);
      }
    },
  });
}

/**
 * Normalize vocabulary term
 */
export interface VocabNormalizeRequest {
  raw_text: string;
  vocab_type: 'issuer' | 'mint' | 'denomination';
  context?: Record<string, any>;
}

export interface VocabNormalizeResponse {
  canonical_name: string;
  confidence: number;
  cost_usd: number;
  model_used: string;
  cached: boolean;
  reasoning: string[];
}

export function useNormalizeVocab() {
  return useMutation({
    mutationFn: async (request: VocabNormalizeRequest): Promise<VocabNormalizeResponse> => {
      const response = await api.post<VocabNormalizeResponse>(
        "/api/v2/llm/vocab/normalize",
        request
      );
      return response.data;
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Vocab normalization failed:', error.message);
      }
    },
  });
}

/** Run legend/transcribe on the coin's primary image and save to llm_suggested_design */
export function useTranscribeLegendForCoin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (coinId: number) => {
      const response = await api.post(`/api/v2/llm/legend/transcribe/coin/${coinId}`);
      return response.data as { obverse_legend?: string; reverse_legend?: string; exergue?: string; confidence: number; cost_usd: number };
    },
    onSuccess: (_, coinId) => {
      queryClient.invalidateQueries({ queryKey: ["llm-suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["coins", coinId] });
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

/** Run identify on the coin's primary image and save to llm_suggested_attribution + design + refs */
export function useIdentifyCoinForCoin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (coinId: number) => {
      const response = await api.post(`/api/v2/llm/identify/coin/${coinId}`);
      return response.data as { ruler?: string; denomination?: string; mint?: string; date_range?: string; confidence: number; cost_usd: number };
    },
    onSuccess: (_, coinId) => {
      queryClient.invalidateQueries({ queryKey: ["llm-suggestions"] });
      queryClient.invalidateQueries({ queryKey: ["coins", coinId] });
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

// ============================================================================
// Phase 4: LLM Enrichment API Types and Hooks
// ============================================================================

/** LLM Enrichment record from llm_enrichments table */
export interface LLMEnrichmentRecord {
  id: number;
  coin_id: number;
  capability: string;
  capability_version: number;
  model_id: string;
  model_version: string | null;
  input_hash: string;
  output_content: string;
  confidence: number;
  needs_review: boolean;
  quality_flags: string | null;
  cost_usd: number;
  input_tokens: number | null;
  output_tokens: number | null;
  cached: boolean;
  review_status: 'pending' | 'provisional' | 'approved' | 'rejected' | 'superseded';
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  created_at: string;
  expires_at: string | null;
  superseded_by: number | null;
  request_id: string | null;
  batch_job_id: string | null;
}

export interface EnrichmentsListResponse {
  enrichments: LLMEnrichmentRecord[];
  total_count: number;
}

/** Get all enrichments for a coin */
export function useCoinEnrichments(coinId: number, options?: {
  capability?: string;
  reviewStatus?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["llm-enrichments", coinId, options],
    queryFn: async (): Promise<EnrichmentsListResponse> => {
      const params = new URLSearchParams();
      if (options?.capability) params.set("capability", options.capability);
      if (options?.reviewStatus) params.set("review_status", options.reviewStatus);
      if (options?.skip) params.set("skip", options.skip.toString());
      if (options?.limit) params.set("limit", options.limit.toString());

      const url = `/api/v2/llm-enrichments/coin/${coinId}${params.toString() ? `?${params}` : ""}`;
      const response = await api.get<EnrichmentsListResponse>(url);
      return response.data;
    },
    enabled: coinId > 0,
  });
}

/** Get current active enrichment for a coin/capability */
export function useCurrentEnrichment(coinId: number, capability: string) {
  return useQuery({
    queryKey: ["llm-enrichment-current", coinId, capability],
    queryFn: async (): Promise<LLMEnrichmentRecord | null> => {
      try {
        const response = await api.get<LLMEnrichmentRecord>(
          `/api/v2/llm-enrichments/coin/${coinId}/current/${capability}`
        );
        return response.data;
      } catch {
        return null;
      }
    },
    enabled: coinId > 0 && !!capability,
  });
}

/** Get enrichments pending review */
export function usePendingReviewEnrichments(capability?: string, limit: number = 100) {
  return useQuery({
    queryKey: ["llm-enrichments-pending", capability, limit],
    queryFn: async (): Promise<EnrichmentsListResponse> => {
      const params = new URLSearchParams();
      if (capability) params.set("capability", capability);
      params.set("limit", limit.toString());

      const response = await api.get<EnrichmentsListResponse>(
        `/api/v2/llm-enrichments/pending-review?${params}`
      );
      return response.data;
    },
  });
}

/** Update enrichment review status */
export interface UpdateReviewStatusRequest {
  review_status: 'pending' | 'provisional' | 'approved' | 'rejected';
  reviewed_by?: string;
  review_notes?: string;
}

export function useUpdateEnrichmentReviewStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      enrichmentId,
      request,
    }: {
      enrichmentId: number;
      request: UpdateReviewStatusRequest;
    }): Promise<LLMEnrichmentRecord> => {
      const response = await api.post<LLMEnrichmentRecord>(
        `/api/v2/llm-enrichments/${enrichmentId}/review-status`,
        request
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["llm-enrichments"] });
      queryClient.invalidateQueries({ queryKey: ["llm-enrichments-pending"] });
      queryClient.invalidateQueries({ queryKey: ["llm-enrichment-current", data.coin_id] });
    },
  });
}

/** Get confidence thresholds for auto-provisional approval */
export function useConfidenceThresholds() {
  return useQuery({
    queryKey: ["llm-confidence-thresholds"],
    queryFn: async () => {
      const response = await api.get<{ thresholds: Record<string, number>; description: string }>(
        "/api/v2/llm-enrichments/confidence-thresholds/list"
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

/** Get quality flags descriptions */
export function useQualityFlags() {
  return useQuery({
    queryKey: ["llm-quality-flags"],
    queryFn: async () => {
      const response = await api.get<{
        flags: Record<string, string>;
        blocking_flags: string[];
      }>("/api/v2/llm-enrichments/quality-flags/list");
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
