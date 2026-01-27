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

import { useMutation, useQueryClient } from "@tanstack/react-query";
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

export interface LLMStatusResponse {
  status: string;
  profile: string;
  monthly_cost_usd: number;
  monthly_budget_usd: number;
  budget_remaining_usd: number;
  capabilities_available: string[];
  ollama_available: boolean;
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
 * Get LLM service status
 * 
 * @example
 * const { data: status } = useLLMStatus();
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
