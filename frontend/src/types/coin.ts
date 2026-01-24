// ============================================================================
// ENUMS - Match backend exactly
// ============================================================================

export type Category = 
  | "greek" 
  | "celtic" 
  | "republic" 
  | "imperial" 
  | "provincial" 
  | "judaean" 
  | "byzantine" 
  | "migration" 
  | "pseudo_roman" 
  | "other";

export type Metal = 
  | "gold" 
  | "electrum" 
  | "silver" 
  | "billon" 
  | "potin" 
  | "orichalcum" 
  | "bronze" 
  | "copper" 
  | "lead" 
  | "ae" 
  | "uncertain";

export type DatingCertainty = "exact" | "narrow" | "broad" | "unknown";

export type GradeService = "ngc" | "pcgs" | "self" | "dealer";

export type HolderType = "ngc_slab" | "pcgs_slab" | "flip" | "capsule" | "tray" | "raw";

export type Rarity = "common" | "scarce" | "rare" | "very_rare" | "extremely_rare" | "unique";

export type Orientation = "obverse_up" | "reverse_up" | "rotated";

export type ReferencePosition = "obverse" | "reverse" | "both";

export type CountermarkType = "host_validation" | "value_reduction" | "military" | "civic" | "imperial" | "other";

export type CountermarkCondition = "clear" | "partial" | "worn" | "uncertain";

export type ProvenanceType = "auction" | "private_sale" | "dealer" | "find" | "inheritance" | "gift" | "collection" | "exchange";


// ============================================================================
// REFERENCE TYPES
// ============================================================================

export interface ReferenceType {
  id: number;
  system: string;
  local_ref: string;
  volume?: string;
  number?: string;
  edition?: string;
  external_id?: string;
  external_url?: string;
  lookup_status?: string;
  lookup_confidence?: number;
}

export interface CoinReference {
  id: number;
  reference_type_id: number;
  is_primary: boolean;
  plate_coin: boolean;
  position?: ReferencePosition;
  variant_notes?: string;
  page?: string;
  plate?: string;
  note_number?: string;
  reference_type?: ReferenceType;
}

export interface CoinReferenceCreate {
  reference_type_id: number;
  is_primary?: boolean;
  plate_coin?: boolean;
  position?: ReferencePosition;
  variant_notes?: string;
  page?: string;
  plate?: string;
  note_number?: string;
}


// ============================================================================
// IMAGES
// ============================================================================

export interface CoinImage {
  id: number;
  image_type: string;
  file_path: string;
  is_primary: boolean;
  source_url?: string | null;
  source_house?: string | null;
}


// ============================================================================
// COUNTERMARKS
// ============================================================================

export interface Countermark {
  id: number;
  countermark_type: CountermarkType;
  description: string;
  expanded?: string;
  placement: string;
  position?: string;
  condition?: CountermarkCondition;
  authority?: string;
  date_applied?: string;
  image_url?: string;
  notes?: string;
}

export interface CountermarkCreate {
  countermark_type: CountermarkType;
  description: string;
  expanded?: string;
  placement: string;
  position?: string;
  condition?: CountermarkCondition;
  authority?: string;
  date_applied?: string;
  image_url?: string;
  notes?: string;
}


// ============================================================================
// PROVENANCE
// ============================================================================

export interface ProvenanceEvent {
  id: number;
  event_type: ProvenanceType;
  event_date?: string;
  auction_house?: string;
  sale_series?: string;
  sale_number?: string;
  lot_number?: string;
  catalog_reference?: string;
  hammer_price?: number;
  buyers_premium_pct?: number;
  total_price?: number;
  currency?: string;
  dealer_name?: string;
  collection_name?: string;
  url?: string;
  receipt_available?: boolean;
  notes?: string;
}

export interface ProvenanceEventCreate {
  event_type: ProvenanceType;
  event_date?: string;
  auction_house?: string;
  sale_series?: string;
  sale_number?: string;
  lot_number?: string;
  catalog_reference?: string;
  hammer_price?: number;
  buyers_premium_pct?: number;
  total_price?: number;
  currency?: string;
  dealer_name?: string;
  collection_name?: string;
  url?: string;
  receipt_available?: boolean;
  notes?: string;
}


// ============================================================================
// AUCTION DATA
// ============================================================================

export interface AuctionData {
  id: number;
  auction_house: string;
  sale_name?: string;
  lot_number?: string;
  auction_date?: string;
  url: string;
  estimate_low?: number;
  estimate_high?: number;
  hammer_price?: number;
  total_price?: number;
  currency?: string;
  sold?: boolean;
  grade?: string;
  title?: string;
  primary_photo_url?: string;
  photos?: string[] | null;
}

export interface AuctionDataCreate {
  auction_house: string;
  sale_name?: string;
  lot_number?: string;
  auction_date?: string;
  url: string;
  estimate_low?: number;
  estimate_high?: number;
  hammer_price?: number;
  total_price?: number;
  currency?: string;
  sold?: boolean;
  grade?: string;
  title?: string;
  description?: string;
  photos?: string[];
  primary_photo_url?: string;
}


// ============================================================================
// COIN LIST/DETAIL
// ============================================================================

export interface CoinListItem {
  id: number;
  category: Category;
  sub_category?: string;
  denomination: string;
  metal: Metal;
  issuing_authority: string;
  portrait_subject?: string;
  mint_name?: string;
  mint_year_start?: number;
  mint_year_end?: number;
  is_circa?: boolean;
  is_test_cut?: boolean;
  rarity?: Rarity;
  grade?: string;
  acquisition_price?: string | number;
  estimated_value_usd?: string | number;
  storage_location?: string;
  primary_image?: string;
  // Additional fields for redesigned table view
  reign_start?: number;
  reign_end?: number;
  primary_reference?: string;
  weight_g?: number;
  diameter_mm?: number;
  die_axis?: number;
  acquisition_date?: string;
  acquisition_source?: string;
  // Obverse/Reverse legends
  obverse_legend?: string;
  reverse_legend?: string;
}

export interface CoinDetail {
  id: number;
  created_at: string;
  updated_at: string;
  
  // Classification
  category: Category;
  sub_category?: string;
  denomination: string;
  metal: Metal;
  series?: string;
  
  // People
  issuing_authority: string;
  portrait_subject?: string;
  status?: string;
  
  // Chronology
  reign_start?: number;
  reign_end?: number;
  mint_year_start?: number;
  mint_year_end?: number;
  is_circa?: boolean;
  dating_certainty?: DatingCertainty;
  dating_notes?: string;
  
  // Physical
  weight_g?: number;
  diameter_mm?: number;
  diameter_min_mm?: number;
  thickness_mm?: number;
  die_axis?: number;
  orientation?: Orientation;
  is_test_cut?: boolean;
  
  // Design: Obverse
  obverse_legend?: string;
  obverse_legend_expanded?: string;
  obverse_description?: string;
  obverse_symbols?: string;
  
  // Design: Reverse
  reverse_legend?: string;
  reverse_legend_expanded?: string;
  reverse_description?: string;
  reverse_symbols?: string;
  exergue?: string;
  
  // Mint
  mint_id?: number;
  mint_name?: string;
  officina?: string;
  
  // Grading
  grade_service?: GradeService;
  grade?: string;
  strike_quality?: number;
  surface_quality?: number;
  certification_number?: string;
  eye_appeal?: string;
  toning_description?: string;
  style_notes?: string;
  
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
  insured_value?: number;
  
  // Storage
  holder_type?: HolderType;
  storage_location?: string;
  for_sale: boolean;
  asking_price?: number;
  
  // Research
  rarity?: Rarity;
  rarity_notes?: string;
  historical_significance?: string;
  die_match_notes?: string;
  personal_notes?: string;
  provenance_notes?: string;
  
  // Die study
  die_study_obverse_id?: number;
  die_study_reverse_id?: number;
  die_study_group?: string;
  
  // Relations
  references: CoinReference[];
  images: CoinImage[];
  tags: string[];
  countermarks: Countermark[];
  provenance_events: ProvenanceEvent[];
  auction_data: AuctionData[];
}


// ============================================================================
// COIN CREATE/UPDATE
// ============================================================================

export interface CoinCreate {
  // Required
  category: Category;
  denomination: string;
  metal: Metal;
  issuing_authority: string;
  
  // Classification
  sub_category?: string;
  series?: string;
  
  // People
  portrait_subject?: string;
  status?: string;
  
  // Chronology
  reign_start?: number;
  reign_end?: number;
  mint_year_start?: number;
  mint_year_end?: number;
  is_circa?: boolean;
  dating_certainty?: DatingCertainty;
  dating_notes?: string;
  
  // Physical
  weight_g?: number;
  diameter_mm?: number;
  diameter_min_mm?: number;
  thickness_mm?: number;
  die_axis?: number;
  orientation?: Orientation;
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
  mint_id?: number;
  officina?: string;
  
  // Grading
  grade_service?: GradeService;
  grade?: string;
  strike_quality?: number;
  surface_quality?: number;
  certification_number?: string;
  eye_appeal?: string;
  toning_description?: string;
  style_notes?: string;
  
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
  insured_value?: number;
  
  // Storage
  holder_type?: HolderType;
  storage_location?: string;
  for_sale?: boolean;
  asking_price?: number;
  
  // Research
  rarity?: Rarity;
  rarity_notes?: string;
  historical_significance?: string;
  die_match_notes?: string;
  personal_notes?: string;
  provenance_notes?: string;
  
  // Die study
  die_study_obverse_id?: number;
  die_study_reverse_id?: number;
  die_study_group?: string;
  
  // Nested creates
  references?: CoinReferenceCreate[];
  countermarks?: CountermarkCreate[];
  tags?: string[];
}

export interface CoinUpdate {
  // Classification
  category?: Category;
  sub_category?: string;
  denomination?: string;
  metal?: Metal;
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
  dating_certainty?: DatingCertainty;
  dating_notes?: string;
  
  // Physical
  weight_g?: number;
  diameter_mm?: number;
  diameter_min_mm?: number;
  thickness_mm?: number;
  die_axis?: number;
  orientation?: Orientation;
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
  mint_id?: number;
  officina?: string;
  
  // Grading
  grade_service?: GradeService;
  grade?: string;
  strike_quality?: number;
  surface_quality?: number;
  certification_number?: string;
  eye_appeal?: string;
  toning_description?: string;
  style_notes?: string;
  
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
  insured_value?: number;
  
  // Storage
  holder_type?: HolderType;
  storage_location?: string;
  for_sale?: boolean;
  asking_price?: number;
  
  // Research
  rarity?: Rarity;
  rarity_notes?: string;
  historical_significance?: string;
  die_match_notes?: string;
  personal_notes?: string;
  provenance_notes?: string;
  
  // Die study
  die_study_obverse_id?: number;
  die_study_reverse_id?: number;
  die_study_group?: string;
}


// ============================================================================
// PAGINATION
// ============================================================================

export interface PaginatedCoins {
  items: CoinListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}


// ============================================================================
// LEGEND EXPANSION
// ============================================================================

export interface LegendExpansionRequest {
  legend: string;
  use_llm_fallback?: boolean;
}

export interface LegendExpansionResponse {
  original: string;
  expanded: string;
  method: "dictionary" | "llm" | "partial";
  confidence: number;
  unknown_terms: string[];
  expansion_map: Record<string, string>;
}
