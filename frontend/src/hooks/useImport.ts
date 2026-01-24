/**
 * Import hooks for URL scraping, NGC lookup, duplicate detection, and import confirmation.
 * 
 * @module hooks/useImport
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ============================================================================
// Types
// ============================================================================

export type FieldConfidence = "high" | "medium" | "low";

export type ImageSource = 
  | "heritage" 
  | "cng" 
  | "ngc_photovision" 
  | "ebay" 
  | "biddr" 
  | "roma" 
  | "agora" 
  | "uploaded";

export type ImageType = 
  | "obverse" 
  | "reverse" 
  | "slab_front" 
  | "slab_back" 
  | "detail" 
  | "combined";

export type MatchReason = "exact_source" | "ngc_cert" | "physical_match";

export interface ImagePreview {
  url: string;
  source: ImageSource;
  image_type: ImageType;
  thumbnail_url?: string;
  local_path?: string;
  width?: number;
  height?: number;
}

export interface CoinSummary {
  id: number;
  title: string;
  thumbnail?: string;
  source_id?: string;
  source_type?: string;
  match_reason: MatchReason;
  match_confidence?: number;
  issuing_authority?: string;
  denomination?: string;
  metal?: string;
  weight_g?: number;
  grade?: string;
}

export interface CoinPreviewData {
  // Classification
  category?: string;
  sub_category?: string;
  denomination?: string;
  metal?: string;
  series?: string;
  
  // People
  issuing_authority?: string;
  portrait_subject?: string;
  status?: string;
  
  // Chronology
  reign_start?: number;
  reign_end?: number;
  mint_year_start?: number;
  mint_year_end?: number;
  is_circa?: boolean;
  dating_certainty?: string;
  dating_notes?: string;
  
  // Physical
  weight_g?: number;
  diameter_mm?: number;
  diameter_min_mm?: number;
  thickness_mm?: number;
  die_axis?: number;
  is_test_cut?: boolean;
  
  // Design
  obverse_legend?: string;
  obverse_legend_expanded?: string;
  obverse_description?: string;
  obverse_symbols?: string;
  reverse_legend?: string;
  reverse_legend_expanded?: string;
  reverse_description?: string;
  reverse_symbols?: string;
  exergue?: string;
  
  // Mint
  mint_name?: string;
  mint_id?: number;
  officina?: string;
  
  // Grading
  grade_service?: string;
  grade?: string;
  strike_quality?: number;
  surface_quality?: number;
  certification_number?: string;
  eye_appeal?: string;
  toning_description?: string;
  style_notes?: string;
  surface_issues?: string[];
  
  // Acquisition
  acquisition_date?: string;
  acquisition_price?: number;
  acquisition_currency?: string;
  acquisition_source?: string;
  acquisition_url?: string;
  
  // Valuation
  estimate_low?: number;
  estimate_high?: number;
  estimated_value_usd?: number;
  
  // Storage
  holder_type?: string;
  storage_location?: string;
  for_sale?: boolean;
  
  // Research
  rarity?: string;
  rarity_notes?: string;
  historical_significance?: string;
  personal_notes?: string;
  provenance_notes?: string;
  
  // Images
  images: ImagePreview[];
  
  // References
  references: string[];
  
  // Auction data
  auction_house?: string;
  sale_name?: string;
  lot_number?: string;
  auction_date?: string;
  hammer_price?: number;
  total_price?: number;
  currency?: string;
  sold?: boolean;
  
  // Raw description
  title?: string;
  description?: string;
}

export interface ImportPreviewResponse {
  success: boolean;
  error?: string;
  error_code?: string;
  retry_after?: number;
  manual_entry_suggested: boolean;
  
  source_type?: string;
  source_id?: string;
  source_url?: string;
  
  coin_data?: CoinPreviewData;
  field_confidence: Record<string, FieldConfidence>;
  similar_coins: CoinSummary[];
  detected_references: string[];
  enrichment_available: boolean;
  raw_data?: Record<string, unknown>;
}

export interface DuplicateCheckResponse {
  has_duplicates: boolean;
  similar_coins: CoinSummary[];
}

export interface ImportConfirmResponse {
  success: boolean;
  coin_id?: number;
  error?: string;
  merged: boolean;
}

export interface CoinImportConfirm {
  coin_data: CoinPreviewData;
  source_type: string;
  source_id?: string;
  source_url?: string;
  raw_data?: Record<string, unknown>;
  track_price_history: boolean;
  sold_price_usd?: number;
  auction_date?: string;
  auction_house?: string;
  lot_number?: string;
  merge_with_coin_id?: number;
}

// ============================================================================
// Error Types
// ============================================================================

export interface ImportError {
  message: string;
  code?: string;
  retryAfter?: number;
  manualEntrySuggested?: boolean;
}

// ============================================================================
// URL Import Hook
// ============================================================================

export function useUrlImport() {
  return useMutation<ImportPreviewResponse, ImportError, string>({
    mutationFn: async (url: string) => {
      try {
        const { data } = await api.post<ImportPreviewResponse>("/api/import/from-url", { url });
        
        // Transform API error into thrown error for mutation handling
        if (!data.success) {
          throw {
            message: data.error || "Import failed",
            code: data.error_code,
            retryAfter: data.retry_after,
            manualEntrySuggested: data.manual_entry_suggested,
          } as ImportError;
        }
        
        return data;
      } catch (error: any) {
        // Re-throw ImportError as is
        if (error.code) {
          throw error;
        }
        // Wrap other errors
        throw {
          message: error.message || "Failed to import from URL",
        } as ImportError;
      }
    },
  });
}

// ============================================================================
// NGC Import Hook
// ============================================================================

export function useNgcImport() {
  return useMutation<ImportPreviewResponse, ImportError, string>({
    mutationFn: async (certNumber: string) => {
      try {
        const { data } = await api.post<ImportPreviewResponse>("/api/import/from-ngc", { 
          cert_number: certNumber 
        });
        
        if (!data.success) {
          throw {
            message: data.error || "NGC lookup failed",
            code: data.error_code,
            retryAfter: data.retry_after,
            manualEntrySuggested: data.manual_entry_suggested,
          } as ImportError;
        }
        
        return data;
      } catch (error: any) {
        if (error.code) {
          throw error;
        }
        throw {
          message: error.message || "Failed to lookup NGC certificate",
        } as ImportError;
      }
    },
  });
}

// ============================================================================
// Duplicate Check Hook
// ============================================================================

export interface DuplicateCheckParams {
  source_type?: string;
  source_id?: string;
  ngc_cert?: string;
  weight_g?: number;
  diameter_mm?: number;
  issuing_authority?: string;
  denomination?: string;
}

export function useDuplicateCheck() {
  return useMutation<DuplicateCheckResponse, Error, DuplicateCheckParams>({
    mutationFn: async (params) => {
      const { data } = await api.post<DuplicateCheckResponse>(
        "/api/import/check-duplicate",
        params
      );
      return data;
    },
  });
}

// ============================================================================
// Import Confirm Hook
// ============================================================================

export function useImportConfirm() {
  const queryClient = useQueryClient();
  
  return useMutation<ImportConfirmResponse, Error, CoinImportConfirm>({
    mutationFn: async (confirmData) => {
      const { data } = await api.post<ImportConfirmResponse>(
        "/api/import/confirm",
        confirmData
      );
      
      if (!data.success) {
        throw new Error(data.error || "Import confirmation failed");
      }
      
      return data;
    },
    onSuccess: (data) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["coins"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.invalidateQueries({ queryKey: ["database-info"] });
      
      if (data.coin_id) {
        queryClient.invalidateQueries({ queryKey: ["coin", data.coin_id] });
      }
    },
  });
}

// ============================================================================
// Source Detection Utility
// ============================================================================

const SOURCE_PATTERNS: Record<string, RegExp> = {
  heritage: /coins\.ha\.com|ha\.com/i,
  cng: /cngcoins\.com/i,
  ebay: /ebay\./i,
  biddr: /biddr\.com/i,
  roma: /romanumismatics\.com/i,
  agora: /agoraauctions\.com/i,
  ngc: /ngccoin\.com/i,
};

export function detectAuctionSource(url: string): string | null {
  for (const [source, pattern] of Object.entries(SOURCE_PATTERNS)) {
    if (pattern.test(url)) {
      return source;
    }
  }
  return null;
}

// Source display configuration
export const SOURCE_CONFIG: Record<string, {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
}> = {
  heritage: {
    label: "Heritage Auctions",
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
  },
  cng: {
    label: "CNG",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
  },
  ebay: {
    label: "eBay",
    color: "text-yellow-600",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
  },
  biddr: {
    label: "Biddr",
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/30",
  },
  roma: {
    label: "Roma",
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/30",
  },
  agora: {
    label: "Agora",
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/30",
  },
  ngc: {
    label: "NGC",
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
  },
};

// ============================================================================
// Confidence Display Utility
// ============================================================================

export const CONFIDENCE_CONFIG: Record<FieldConfidence, {
  borderColor: string;
  bgColor: string;
  icon: string;
  tooltip: string;
}> = {
  high: {
    borderColor: "border-input",
    bgColor: "",
    icon: "",
    tooltip: "High confidence - data verified",
  },
  medium: {
    borderColor: "border-yellow-500/50",
    bgColor: "",
    icon: "info",
    tooltip: "Medium confidence - may need review",
  },
  low: {
    borderColor: "border-amber-500",
    bgColor: "bg-amber-500/5",
    icon: "alert",
    tooltip: "Low confidence - please verify this value",
  },
};

// ============================================================================
// Enrichment Types and Hook
// ============================================================================

export interface EnrichmentField {
  field: string;
  value: unknown;
  source: string;
  confidence: number;
}

export interface EnrichPreviewResponse {
  success: boolean;
  error?: string;
  suggestions: Record<string, EnrichmentField>;
  lookup_results: Array<{
    reference: string;
    system?: string;
    status: string;
    external_id?: string;
    external_url?: string;
    confidence?: number;
    error?: string;
  }>;
}

export interface EnrichPreviewRequest {
  references: string[];
  context?: Record<string, unknown>;
}

export function useEnrichPreview() {
  return useMutation<EnrichPreviewResponse, Error, EnrichPreviewRequest>({
    mutationFn: async (request) => {
      const { data } = await api.post<EnrichPreviewResponse>(
        "/api/import/enrich-preview",
        request
      );
      return data;
    },
  });
}

// ============================================================================
// Batch Import Types and Hook
// ============================================================================

export interface BatchPreviewItem {
  url: string;
  success: boolean;
  error?: string;
  source_type?: string;
  source_id?: string;
  title?: string;
  thumbnail?: string;
  preview?: ImportPreviewResponse;
}

export interface BatchURLImportResponse {
  total: number;
  successful: number;
  failed: number;
  items: BatchPreviewItem[];
}

export function useBatchUrlImport() {
  return useMutation<BatchURLImportResponse, Error, string[]>({
    mutationFn: async (urls) => {
      const { data } = await api.post<BatchURLImportResponse>(
        "/api/import/batch-urls",
        { urls }
      );
      return data;
    },
  });
}
