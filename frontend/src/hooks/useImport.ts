/**
 * Import hooks for URL scraping, NGC lookup, duplicate detection, and import confirmation.
 * 
 * @module hooks/useImport
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/api/api";

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
  is_primary?: boolean;
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

// Flat interface for the Import Preview Editor (DTO)
export interface CoinPreviewData {
  category?: string;
  sub_category?: string;
  denomination?: string;
  metal?: string;
  series?: string;
  issuing_authority?: string;
  portrait_subject?: string;
  status?: string;
  reign_start?: number;
  reign_end?: number;
  mint_year_start?: number;
  mint_year_end?: number;
  is_circa?: boolean;
  dating_certainty?: string;
  dating_notes?: string;
  weight_g?: number;
  diameter_mm?: number;
  diameter_min_mm?: number;
  thickness_mm?: number;
  die_axis?: number;
  is_test_cut?: boolean;
  obverse_legend?: string;
  obverse_legend_expanded?: string;
  obverse_description?: string;
  obverse_symbols?: string;
  reverse_legend?: string;
  reverse_legend_expanded?: string;
  reverse_description?: string;
  reverse_symbols?: string;
  exergue?: string;
  mint_name?: string;
  mint_id?: number;
  officina?: string;
  grade_service?: string;
  grade?: string;
  strike_quality?: number;
  surface_quality?: number;
  certification_number?: string;
  eye_appeal?: string;
  toning_description?: string;
  style_notes?: string;
  surface_issues?: string[];
  acquisition_date?: string;
  acquisition_price?: number;
  acquisition_currency?: string;
  acquisition_source?: string;
  acquisition_url?: string;
  estimate_low?: number;
  estimate_high?: number;
  estimated_value_usd?: number;
  holder_type?: string;
  storage_location?: string;
  for_sale?: boolean;
  rarity?: string;
  rarity_notes?: string;
  historical_significance?: string;
  personal_notes?: string;
  provenance_notes?: string;
  images: ImagePreview[];
  references: string[];
  auction_house?: string;
  sale_name?: string;
  lot_number?: string;
  auction_date?: string;
  hammer_price?: number;
  total_price?: number;
  currency?: string;
  sold?: boolean;
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
  lookup_results?: any[];
  suggestions?: Record<string, EnrichmentField>;
}

export interface EnrichmentField {
  field: string;
  value: unknown;
  source: string;
  confidence: number;
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

export interface ImportError {
  message: string;
  code?: string;
  retryAfter?: number;
  manualEntrySuggested?: boolean;
}

export function useUrlImport() {
  return useMutation<ImportPreviewResponse, ImportError, string>({
    mutationFn: async (url: string) => {
      const { data } = await api.post<ImportPreviewResponse>("/api/v2/import/from-url", { url });
      return data;
    },
  });
}

export function useNgcImport() {
  return useMutation<ImportPreviewResponse, ImportError, string>({
    mutationFn: async (certNumber: string) => {
      const { data } = await api.post<ImportPreviewResponse>("/api/v2/import/from-ngc", { 
        cert_number: certNumber 
      });
      return data;
    },
  });
}

export function useImportConfirm() {
  const queryClient = useQueryClient();
  
  return useMutation<ImportConfirmResponse, Error, CoinImportConfirm>({
    mutationFn: async (confirmData) => {
      const { data } = await api.post<ImportConfirmResponse>(
        "/api/v2/import/confirm",
        confirmData
      );
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      if (data.coin_id) {
        queryClient.invalidateQueries({ queryKey: ["coin", data.coin_id] });
      }
    },
  });
}

export function useEnrichPreview() {
  return useMutation<ImportPreviewResponse, Error, any>({
    mutationFn: async (request) => {
      const { data } = await api.post<ImportPreviewResponse>(
        "/api/v2/import/enrich-preview",
        request
      );
      return data;
    },
  });
}

export function useBatchUrlImport() {
  return useMutation<any, Error, string[]>({
    mutationFn: async (urls) => {
      const { data } = await api.post("/api/v2/import/batch-urls", { urls });
      return data;
    },
  });
}

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
  // ... rest same
};

export function detectAuctionSource(url: string): string | null {
  if (/coins\.ha\.com|ha\.com/i.test(url)) return "heritage";
  if (/cngcoins\.com/i.test(url)) return "cng";
  return null;
}
