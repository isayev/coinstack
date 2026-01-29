/**
 * TypeScript types for audit functionality.
 */

export type TrustLevel = "authoritative" | "high" | "medium" | "low" | "untrusted";
export type DifferenceType = 
  | "exact" 
  | "equivalent" 
  | "within_tolerance" 
  | "overlapping" 
  | "adjacent" 
  | "partial" 
  | "format_diff" 
  | "mismatch" 
  | "missing";
export type DiscrepancyStatus = "pending" | "accepted" | "rejected" | "ignored";
export type EnrichmentStatus = "pending" | "applied" | "rejected" | "ignored";
export type AuditRunStatus = "running" | "completed" | "failed" | "cancelled";
export type AuditScope = "single" | "selected" | "all";

/**
 * Discrepancy record - data conflict between coin and auction
 */
export interface Discrepancy {
  id: number;
  coin_id: number;
  auction_data_id: number | null;
  audit_run_id: number | null;
  field_name: string;
  current_value: string | null;
  auction_value: string | null;
  normalized_current: string | null;
  normalized_auction: string | null;
  similarity: number | null;
  difference_type: DifferenceType | null;
  comparison_notes: string | null;
  source_house: string;
  trust_level: TrustLevel;
  auto_acceptable: boolean;
  status: DiscrepancyStatus;
  resolved_at: string | null;
  resolution: string | null;
  resolution_notes: string | null;
  created_at: string;
  // Extended data from related tables
  source_url?: string | null;
  auction_images?: string[];
  coin_primary_image?: string | null;
  // Coin details
  coin_ruler?: string | null;
  coin_denomination?: string | null;
  coin_metal?: string | null;
  coin_grade?: string | null;
  coin_category?: string | null;
  coin_mint_year_start?: number | null;
  coin_mint_year_end?: number | null;
  coin_is_circa?: boolean;
}

/**
 * Enrichment record - suggested field update from auction data
 */
export interface Enrichment {
  id: number;
  coin_id: number;
  auction_data_id: number | null;
  audit_run_id: number | null;
  field_name: string;
  suggested_value: string;
  source_house: string;
  trust_level: TrustLevel;
  confidence: number | null;
  auto_applicable: boolean;
  status: EnrichmentStatus;
  applied: boolean;
  applied_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  // Extended data from related tables
  source_url?: string | null;
  auction_images?: string[];
  coin_primary_image?: string | null;
  // Coin details
  coin_ruler?: string | null;
  coin_denomination?: string | null;
  coin_metal?: string | null;
  coin_grade?: string | null;
  coin_category?: string | null;
  coin_mint_year_start?: number | null;
  coin_mint_year_end?: number | null;
  coin_is_circa?: boolean;
}

/**
 * Audit run - tracks an audit execution session
 */
export interface AuditRun {
  id: number;
  scope: AuditScope;
  coin_ids: number[] | null;
  status: AuditRunStatus;
  total_coins: number;
  coins_audited: number;
  coins_with_issues: number;
  discrepancies_found: number;
  enrichments_found: number;
  images_downloaded: number;
  auto_accepted: number;
  auto_applied: number;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
}

/**
 * Audit run progress for polling
 */
export interface AuditRunProgress {
  id: number;
  status: AuditRunStatus;
  progress_percent: number;
  coins_audited: number;
  total_coins: number;
  discrepancies_found: number;
  enrichments_found: number;
}

/**
 * Audit summary statistics
 */
export interface AuditSummary {
  pending_discrepancies: number;
  pending_enrichments: number;
  discrepancies_by_trust: Record<string, number>;
  discrepancies_by_field: Record<string, number>;
  discrepancies_by_source: Record<string, number>;
  recent_runs: Array<{
    id: number;
    scope: string;
    status: string;
    started_at: string | null;
    coins_audited: number;
    discrepancies_found: number;
  }>;
}

/**
 * Coin audit summary
 */
export interface CoinAuditSummary {
  coin_id: number;
  auctions_checked: number;
  discrepancies: number;
  enrichments: number;
  message?: string;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

/**
 * Filter options for discrepancies
 */
export interface DiscrepancyFilters {
  status?: DiscrepancyStatus;
  field_name?: string;
  source_house?: string;
  trust_level?: TrustLevel;
  coin_id?: number;
  audit_run_id?: number;
  min_similarity?: number;
  max_similarity?: number;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

/**
 * Filter options for enrichments
 */
export interface EnrichmentFilters {
  status?: EnrichmentStatus;
  field_name?: string;
  source_house?: string;
  trust_level?: TrustLevel;
  coin_id?: number;
  audit_run_id?: number;
  auto_applicable?: boolean;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

/**
 * Request to start an audit
 */
export interface StartAuditRequest {
  scope: AuditScope;
  coin_ids?: number[];
}

/**
 * Request to resolve a discrepancy
 */
export interface ResolveDiscrepancyRequest {
  resolution: "accepted" | "rejected" | "ignored";
  notes?: string;
}

/**
 * Image download result
 */
export interface ImageDownloadResult {
  coin_id: number;
  auctions_processed: number;
  images_downloaded: number;
  duplicates_skipped: number;
  errors: number;
}

/**
 * Trust level badge color mapping - works in both light and dark mode
 * Uses outline style with colored text for better visibility
 */
export const TRUST_LEVEL_COLORS: Record<TrustLevel, string> = {
  authoritative: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/40",
  high: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/40",
  medium: "bg-sky-500/15 text-sky-700 dark:text-sky-400 border-sky-500/40",
  low: "bg-orange-500/15 text-orange-700 dark:text-orange-400 border-orange-500/40",
  untrusted: "bg-slate-500/15 text-slate-700 dark:text-slate-400 border-slate-500/40",
};

/**
 * Difference type display labels
 */
export const DIFFERENCE_TYPE_LABELS: Record<DifferenceType, string> = {
  exact: "Exact Match",
  equivalent: "Equivalent",
  within_tolerance: "Within Tolerance",
  overlapping: "Overlapping",
  adjacent: "Adjacent",
  partial: "Partial Match",
  format_diff: "Format Difference",
  mismatch: "Mismatch",
  missing: "Missing",
};

/**
 * LLM-suggested rarity information
 */
export interface LLMRarityInfo {
  rarity_code: string | null;
  rarity_description: string | null;
  specimens_known: number | null;
  source: string | null;
}

/**
 * Catalog reference validation result
 */
export interface CatalogReferenceValidation {
  reference_text: string;
  parsed_catalog: string | null;
  parsed_number: string | null;
  parsed_volume: string | null;
  validation_status: "matches" | "partial_match" | "mismatch" | "unknown";
  confidence: number;
  match_reason: string | null;
  existing_reference: string | null;
  /** Category/catalog consistency warning from backend catalog_validation */
  numismatic_warning?: string | null;
}

/**
 * LLM-suggested design (legends, exergue, descriptions)
 */
export interface LlmSuggestedDesign {
  obverse_legend?: string | null;
  reverse_legend?: string | null;
  exergue?: string | null;
  obverse_description?: string | null;
  reverse_description?: string | null;
  obverse_legend_expanded?: string | null;
  reverse_legend_expanded?: string | null;
}

/**
 * LLM-suggested attribution (issuer, mint, denomination, dates)
 */
export interface LlmSuggestedAttribution {
  issuer?: string | null;
  mint?: string | null;
  denomination?: string | null;
  year_start?: number | null;
  year_end?: number | null;
}

/**
 * LLM suggestion item for review queue
 */
export interface LLMSuggestionItem {
  coin_id: number;
  // Core coin identification
  issuer: string | null;
  denomination: string | null;
  mint: string | null;
  year_start: number | null;
  year_end: number | null;
  category: string | null;
  // Legends for context
  obverse_legend: string | null;
  reverse_legend: string | null;
  // Existing catalog references (for comparison)
  existing_references: string[];
  // LLM suggestions
  suggested_references: string[];
  validated_references: CatalogReferenceValidation[];
  rarity_info: LLMRarityInfo | null;
  /** Design suggestions (legends, exergue, descriptions) from transcribe/identify */
  suggested_design?: LlmSuggestedDesign | null;
  /** Attribution suggestions (issuer, mint, denomination, dates) from identify */
  suggested_attribution?: LlmSuggestedAttribution | null;
  enriched_at: string | null;
}

/**
 * LLM review queue response
 */
export interface LLMReviewQueueResponse {
  items: LLMSuggestionItem[];
  total: number;
}
