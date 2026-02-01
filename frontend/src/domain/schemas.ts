import { z } from 'zod'

export const MetalSchema = z.enum([
  'gold',
  'silver',
  'bronze',
  'copper',
  'electrum',
  'billon',
  'potin',
  'orichalcum',
  'lead',
  'ae',
])

export const CategorySchema = z.enum([
  // Core categories
  'greek',
  'roman_imperial',
  'roman_republic',
  'roman_provincial',
  'byzantine',
  'medieval',
  // Breakaway empires
  'gallic_empire',
  'palmyrene_empire',
  'romano_british',
  // Other ancient categories
  'celtic',
  'judaean',
  'parthian',
  'sasanian',
  'migration',
  'other'
])

export const GradingStateSchema = z.enum([
  'raw',
  'slabbed',
  'capsule',
  'flip',
])

export const GradeServiceSchema = z.enum([
  'ngc',
  'pcgs',
  'icg',
  'anacs',
  'none',
])

export const IssueStatusSchema = z.enum([
  'official',
  'fourree',
  'imitation',
  'barbarous',
  'modern_fake',
  'tooling_altered',
])

// --- Phase 1.5b: Countermark System Enums ---
export const CountermarkTypeSchema = z.enum([
  'revalidation',
  'revaluation',
  'imperial_portrait',
  'imperial_monogram',
  'legionary',
  'civic_symbol',
  'royal_dynastic',
  'trade_merchant',
  'religious_cult',
  'uncertain',
])
export type CountermarkType = z.infer<typeof CountermarkTypeSchema>

export const CountermarkPositionSchema = z.enum([
  'obverse',
  'reverse',
  'edge',
  'both_sides',
])
export type CountermarkPosition = z.infer<typeof CountermarkPositionSchema>

export const CountermarkConditionSchema = z.enum([
  'clear',
  'partial',
  'worn',
  'uncertain',
])
export type CountermarkCondition = z.infer<typeof CountermarkConditionSchema>

export const PunchShapeSchema = z.enum([
  'rectangular',
  'circular',
  'oval',
  'square',
  'irregular',
  'triangular',
  'star',
  'uncertain',
])
export type PunchShape = z.infer<typeof PunchShapeSchema>

// Countermark schema
export const CountermarkSchema = z.object({
  id: z.number().optional(),
  coin_id: z.number().optional(),
  countermark_type: CountermarkTypeSchema.nullable().optional(),
  position: CountermarkPositionSchema.nullable().optional(),
  condition: CountermarkConditionSchema.nullable().optional(),
  punch_shape: PunchShapeSchema.nullable().optional(),  // Shape of punch (rectangular, circular, etc.)
  description: z.string().nullable().optional(),
  authority: z.string().nullable().optional(),
  reference: z.string().nullable().optional(),  // Howgego number
  date_applied: z.string().nullable().optional(),
  notes: z.string().nullable().optional(),
  created_at: z.string().nullable().optional(),  // Backend returns null, not in domain model
})
export type Countermark = z.infer<typeof CountermarkSchema>

// Strike quality detail schema
export const StrikeQualityDetailSchema = z.object({
  detail: z.string().nullable().optional(),
  is_double_struck: z.boolean().optional().default(false),
  is_brockage: z.boolean().optional().default(false),
  is_off_center: z.boolean().optional().default(false),
  off_center_pct: z.number().min(5).max(95).nullable().optional(),  // Percentage off-center
})
export type StrikeQualityDetail = z.infer<typeof StrikeQualityDetailSchema>

// Helper to safely handle NaN/empty values from number inputs
const preprocessNaN = (v: any) => {
  if (v === "" || v === null || v === undefined) return null;
  if (typeof v === 'number' && isNaN(v)) return null;
  return v;
};

export const DimensionsSchema = z.object({
  weight_g: z.preprocess(preprocessNaN, z.coerce.number().min(0).nullable().optional()),
  diameter_mm: z.preprocess(preprocessNaN, z.coerce.number().min(0).nullable().optional()),
  thickness_mm: z.preprocess(preprocessNaN, z.coerce.number().min(0).nullable().optional()),
  die_axis: z.preprocess(
    preprocessNaN,
    z.coerce.number().min(0).max(12).nullable().optional()
  ),
  specific_gravity: z.preprocess(preprocessNaN, z.coerce.number().min(0).nullable().optional()),
})

export const DieInfoSchema = z.object({
  obverse_die_id: z.string().nullable().optional(),
  reverse_die_id: z.string().nullable().optional(),
})

export const MonogramSchema = z.object({
  id: z.number().optional(),
  label: z.string(),
  image_url: z.string().nullable().optional(),
  vector_data: z.string().nullable().optional(),
})

export const FindDataSchema = z.object({
  find_spot: z.string().nullable().optional(),
  find_date: z.string().nullable().optional(),
})

export const AttributionSchema = z.object({
  issuer: z.string().nullable().optional(),
  issuer_id: z.number().nullable().optional(),
  mint: z.string().nullable().optional(),
  mint_id: z.number().nullable().optional(),
  year_start: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  year_end: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
})

export const SeriesSlotSchema = z.object({
  id: z.number(),
  series_id: z.number(),
  slot_number: z.number(),
  name: z.string(),
  status: z.string(),
  coin_id: z.number().nullable().optional(),
})

export const SeriesSchema = z.object({
  id: z.number(),
  name: z.string(),
  slug: z.string(),
  description: z.string().nullable().optional(),
  series_type: z.string(),
  category: z.string().nullable().optional(),
  target_count: z.number().nullable().optional(),
  is_complete: z.boolean(),
  completion_date: z.string().nullable().optional(),
  canonical_vocab_id: z.number().nullable().optional(),  // V3: Link to canonical series definition
  slots: z.array(SeriesSlotSchema).optional(),
  coin_count: z.number().optional(),  // Computed field
})

/** Normalize strike/surface: "4/5" -> "4", only "1"-"5" or null. */
const strikeSurfaceSchema = z.preprocess(
  (v) => {
    if (v == null || v === '') return null
    const s = String(v).trim()
    if (!s) return null
    const normalized = s.includes('/') ? s.split('/')[0].trim() : s
    const n = parseInt(normalized, 10)
    if (Number.isNaN(n) || n < 1 || n > 5) return null
    return String(n)
  },
  z.union([z.enum(['1', '2', '3', '4', '5']), z.null()]).optional()
)

export const GradingDetailsSchema = z.object({
  grading_state: GradingStateSchema.optional(),
  grade: z.string().nullable().optional(),
  service: GradeServiceSchema.nullable().optional(),
  certification_number: z.string().nullable().optional(),
  strike: strikeSurfaceSchema,
  surface: strikeSurfaceSchema,
  eye_appeal: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  toning_description: z.string().nullable().optional(),
})

export const AcquisitionDetailsSchema = z.object({
  price: z.preprocess(preprocessNaN, z.coerce.number().min(0).nullable().optional()),
  currency: z.string().nullable().optional(),
  source: z.string().nullable().optional(),
  date: z.string().nullable().optional(), // ISO string
  url: z.string().url().nullable().optional(),
})

export const ImageSchema = z.object({
  id: z.number().optional(),
  url: z.string().optional(),
  file_path: z.string().optional(),
  image_type: z.string().optional(),
  is_primary: z.boolean().default(false),
  source_url: z.string().nullable().optional(),
})

// Comprehensive Schema matching Backend CoinDetail
export const BaseCoinSchema = z.object({
  id: z.number().nullable(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),

  // Classification
  category: z.string(),
  sub_category: z.string().nullable().optional(),
  denomination: z.string().nullable().optional(),
  metal: MetalSchema.optional(),
  series: z.string().nullable().optional(),

  // People
  issuing_authority: z.string().nullable().optional(),
  portrait_subject: z.string().nullable().optional(),
  status: z.string().nullable().optional(),

  // Chronology
  reign_start: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  reign_end: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  mint_year_start: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  mint_year_end: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  is_circa: z.boolean().optional(),

  // Physical
  weight_g: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  diameter_mm: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  thickness_mm: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  die_axis: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),

  // Design
  obverse_legend: z.string().nullable().optional(),
  obverse_description: z.string().nullable().optional(),
  reverse_legend: z.string().nullable().optional(),
  reverse_description: z.string().nullable().optional(),
  description: z.string().nullable().optional(),

  // Grading
  grade: z.string().nullable().optional(),
  grade_service: z.string().nullable().optional(),
  certification_number: z.string().nullable().optional(),
  grading_state: z.string().nullable().optional(),
  strike_quality: z.string().nullable().optional(),
  surface_quality: z.string().nullable().optional(),

  // Acquisition
  acquisition_price: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  acquisition_source: z.string().nullable().optional(),
  acquisition_date: z.string().nullable().optional(),
  acquisition_currency: z.string().nullable().optional(),
  acquisition_url: z.string().nullable().optional(),

  // Mint
  mint_name: z.string().nullable().optional(),

  // Relations
  images: z.array(ImageSchema).default([]).optional(),
  tags: z.array(z.string()).optional(),
  auction_data: z.array(z.record(z.string(), z.unknown())).optional(),
  provenance_events: z.array(z.record(z.string(), z.unknown())).optional(),
})

// Schema for the Nested Domain Entity (used by Forms and UI components)
// Design schema for legends and descriptions
export const DesignSchema = z.object({
  obverse_legend: z.string().nullable().optional(),
  obverse_description: z.string().nullable().optional(),
  reverse_legend: z.string().nullable().optional(),
  reverse_description: z.string().nullable().optional(),
  exergue: z.string().nullable().optional(),
}).nullable().optional();

export const CatalogReferenceSchema = z.object({
  id: z.number().optional(),
  catalog: z.string(),
  number: z.string(),
  volume: z.string().nullable().optional(),
  is_primary: z.boolean().optional(),
  plate_coin: z.boolean().optional(),
  position: z.string().nullable().optional(),
  variant_notes: z.string().nullable().optional(),
  page: z.string().nullable().optional(),
  plate: z.string().nullable().optional(),
  note_number: z.string().nullable().optional(),
  notes: z.string().nullable().optional(),
  raw_text: z.string().nullable().optional(),
  source: z.string().nullable().optional(), // "user" | "import" | "scraper" | "llm_approved" | "catalog_lookup"
  variant: z.string().nullable().optional(),   // e.g. "a", "b" (RIC, Crawford)
  mint: z.string().nullable().optional(),       // RIC mint code
  supplement: z.string().nullable().optional(),  // RPC S, S2
  collection: z.string().nullable().optional(), // SNG collection
  // Phase 3: Reference System Enhancements
  attribution_confidence: z.enum(['certain', 'probable', 'possible', 'tentative']).nullable().optional(),
  catalog_rarity_note: z.string().nullable().optional(), // e.g., "R2" from RIC, "Very Rare" from BMC
  disagreement_note: z.string().nullable().optional(),   // e.g., "RIC attributes to Nero, but legend style suggests Vespasian"
  page_reference: z.string().nullable().optional(),      // e.g., "p. 234, pl. XV.7"
  variant_note: z.string().nullable().optional(),        // e.g., "var. b with AVGVSTI"
}).nullable().optional();

export type CatalogReference = z.infer<typeof CatalogReferenceSchema>;

export const DomainCoinSchema = z.object({
  id: z.number().nullable(),
  created_at: z.string().optional(),
  updated_at: z.string().optional(),

  category: z.string(), // or CategorySchema
  sub_category: z.string().nullable().optional(),
  denomination: z.string().nullable().optional(),
  metal: MetalSchema.optional(),
  series: z.string().nullable().optional(),

  issuing_authority: z.string().nullable().optional(),
  portrait_subject: z.string().nullable().optional(),
  status: z.string().nullable().optional(),

  reign_start: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  reign_end: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  mint_year_start: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  mint_year_end: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  is_circa: z.boolean().optional(),

  // Nested Objects
  dimensions: DimensionsSchema,
  attribution: AttributionSchema,
  grading: GradingDetailsSchema,
  acquisition: AcquisitionDetailsSchema.nullable().optional(), // acquisition can be null

  mint_name: z.string().nullable().optional(),

  // Design object (nested legends and descriptions from backend)
  design: DesignSchema,

  // For backwards compatibility, also allow flat fields
  obverse_legend: z.string().nullable().optional(),
  obverse_description: z.string().nullable().optional(),
  reverse_legend: z.string().nullable().optional(),
  reverse_description: z.string().nullable().optional(),
  description: z.string().nullable().optional(),

  images: z.array(ImageSchema).default([]).optional(),
  tags: z.array(z.string()).optional(),
  references: z.array(CatalogReferenceSchema).optional(),
  // Provenance uses forward reference since ProvenanceEventSchema is defined later
  provenance: z.array(z.object({
    id: z.number().optional(),
    coin_id: z.number().optional(),
    event_type: z.string(),
    source_name: z.string().nullable().optional(), // V3 unified field
    event_date: z.string().nullable().optional(),
    date_string: z.string().nullable().optional(),
    sale_name: z.string().nullable().optional(), // V3 field
    sale_number: z.string().nullable().optional(),
    lot_number: z.string().nullable().optional(),
    catalog_reference: z.string().nullable().optional(),
    hammer_price: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
    buyers_premium_pct: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
    total_price: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
    currency: z.string().nullable().optional(),
    url: z.string().nullable().optional(),
    receipt_available: z.boolean().nullable().optional(),
    notes: z.string().nullable().optional(),
    sort_order: z.number().nullable().optional(),
    is_acquisition: z.boolean().nullable().optional(), // V3 field
    // Legacy fields (backward compat)
    auction_house: z.string().nullable().optional(),
    sale_series: z.string().nullable().optional(),
    dealer_name: z.string().nullable().optional(),
    collection_name: z.string().nullable().optional(),
  })).optional(),

  // Collection management
  storage_location: z.string().nullable().optional(),
  personal_notes: z.string().nullable().optional(),

  // -------------------------------------------------------------------------
  // LLM-Generated Fields
  // -------------------------------------------------------------------------
  obverse_legend_expanded: z.string().nullable().optional(),
  reverse_legend_expanded: z.string().nullable().optional(),
  historical_significance: z.string().nullable().optional(),  // LLM historical context
  catalog_description: z.string().nullable().optional(),
  condition_observations: z.string().nullable().optional(),  // JSON string
  llm_enriched_at: z.string().nullable().optional(),
  llm_analysis_sections: z.union([z.record(z.string(), z.unknown()), z.string()]).nullable().optional(),

  // -------------------------------------------------------------------------
  // Iconography and Design Details
  // -------------------------------------------------------------------------
  obverse_iconography: z.union([z.array(z.string()), z.string()]).nullable().optional(),
  reverse_iconography: z.union([z.array(z.string()), z.string()]).nullable().optional(),
  control_marks: z.union([z.array(z.string()), z.string()]).nullable().optional(),
  obverse_symbols: z.string().nullable().optional(),
  reverse_symbols: z.string().nullable().optional(),

  // -------------------------------------------------------------------------
  // Mint Details
  // -------------------------------------------------------------------------
  mintmark: z.string().nullable().optional(),
  field_marks: z.string().nullable().optional(),
  officina: z.string().nullable().optional(),  // Mint workshop

  // -------------------------------------------------------------------------
  // Die Study Fields
  // -------------------------------------------------------------------------
  die_state: z.string().nullable().optional(),  // early, middle, late, worn
  die_match_notes: z.string().nullable().optional(),

  // -------------------------------------------------------------------------
  // Republican Coinage Specific
  // -------------------------------------------------------------------------
  moneyer: z.string().nullable().optional(),

  // -------------------------------------------------------------------------
  // Edge Details
  // -------------------------------------------------------------------------
  edge_type: z.string().nullable().optional(),  // plain, reeded, lettered, decorated
  edge_inscription: z.string().nullable().optional(),

  // -------------------------------------------------------------------------
  // Attribution Confidence
  // -------------------------------------------------------------------------
  attribution_confidence: z.enum(['certain', 'probable', 'possible', 'uncertain']).nullable().optional(),
  attribution_notes: z.string().nullable().optional(),

  // -------------------------------------------------------------------------
  // Conservation and Cleaning History
  // -------------------------------------------------------------------------
  cleaning_history: z.string().nullable().optional(),
  conservation_notes: z.string().nullable().optional(),

  // -------------------------------------------------------------------------
  // Rarity and Condition Notes
  // -------------------------------------------------------------------------
  // Backend/LLM may return uppercase (e.g. R2); normalize to lowercase for enum
  rarity: z.preprocess(
    (v) => (typeof v === 'string' ? v.toLowerCase().trim() : v),
    z.enum(['c', 's', 'r1', 'r2', 'r3', 'u']).nullable().optional()
  ),
  rarity_notes: z.string().nullable().optional(),
  style_notes: z.string().nullable().optional(),
  toning_description: z.string().nullable().optional(),
  eye_appeal: z.string().nullable().optional(),
  surface_issues: z.string().nullable().optional(),  // JSON array

  // -------------------------------------------------------------------------
  // Market Value Tracking
  // -------------------------------------------------------------------------
  market_value: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  market_value_date: z.string().nullable().optional(),

  // -------------------------------------------------------------------------
  // Additional Fields from Backend
  // -------------------------------------------------------------------------
  script: z.string().nullable().optional(),  // Latin, Greek, etc.
  dating_certainty: z.string().nullable().optional(),  // BROAD, NARROW, EXACT
  provenance_notes: z.string().nullable().optional(),
  orientation: z.string().nullable().optional(),

  llm_suggested_references: z.array(z.string()).nullable().optional(),
  llm_suggested_rarity: z.record(z.string(), z.unknown()).nullable().optional(),

  // -------------------------------------------------------------------------
  // Research Grade Extensions (V2.1)
  // -------------------------------------------------------------------------
  issue_status: IssueStatusSchema.optional(),
  die_info: DieInfoSchema.nullable().optional(),
  monograms: z.array(MonogramSchema).default([]).optional(),
  secondary_treatments: z.array(z.record(z.string(), z.unknown())).nullable().optional(),
  find_data: FindDataSchema.nullable().optional(),

  // Navigation helpers (added by API)
  prev_id: z.number().nullable().optional(),
  next_id: z.number().nullable().optional(),

  // -------------------------------------------------------------------------
  // Schema V3 - Phase 1: Core Numismatic Enhancements (Nested Objects)
  // -------------------------------------------------------------------------

  // Attribution enhancements (nested objects from API)
  secondary_authority: z.object({
    name: z.string().nullable().optional(),
    term_id: z.number().nullable().optional(),
    authority_type: z.string().nullable().optional(),
  }).nullable().optional(),
  co_ruler: z.object({
    name: z.string().nullable().optional(),
    term_id: z.number().nullable().optional(),
    portrait_relationship: z.string().nullable().optional(),
  }).nullable().optional(),
  moneyer_gens: z.string().nullable().optional(),

  // Physical enhancements (nested object)
  physical_enhancements: z.object({
    weight_standard: z.string().nullable().optional(),
    expected_weight_g: z.number().nullable().optional(),
    flan_shape: z.string().nullable().optional(),
    flan_type: z.string().nullable().optional(),
    flan_notes: z.string().nullable().optional(),
  }).nullable().optional(),

  // Secondary treatments V3 (nested object)
  secondary_treatments_v3: z.object({
    is_overstrike: z.boolean().optional(),
    undertype_visible: z.string().nullable().optional(),
    undertype_attribution: z.string().nullable().optional(),
    has_test_cut: z.boolean().optional(),
    test_cut_count: z.number().nullable().optional(),
    test_cut_positions: z.string().nullable().optional(),
    has_bankers_marks: z.boolean().optional(),
    has_graffiti: z.boolean().optional(),
    graffiti_description: z.string().nullable().optional(),
    was_mounted: z.boolean().optional(),
    mount_evidence: z.string().nullable().optional(),
  }).nullable().optional(),

  // Tooling/repairs (nested object)
  tooling_repairs: z.object({
    tooling_extent: z.string().nullable().optional(),
    tooling_details: z.string().nullable().optional(),
    has_ancient_repair: z.boolean().optional(),
    ancient_repairs: z.string().nullable().optional(),
  }).nullable().optional(),

  // Centering (nested object)
  centering_info: z.object({
    centering: z.string().nullable().optional(),
    centering_notes: z.string().nullable().optional(),
  }).nullable().optional(),

  // Die study enhancements (nested object)
  die_study: z.object({
    obverse_die_state: z.string().nullable().optional(),
    reverse_die_state: z.string().nullable().optional(),
    die_break_description: z.string().nullable().optional(),
  }).nullable().optional(),

  // Grading TPG enhancements (nested object)
  grading_tpg: z.object({
    grade_numeric: z.number().nullable().optional(),
    grade_designation: z.string().nullable().optional(),
    has_star_designation: z.boolean().optional(),
    photo_certificate: z.boolean().optional(),
    verification_url: z.string().nullable().optional(),
    // Phase 1.5b: NGC-specific fields (PCGS doesn't use 1-5 scale for ancients)
    ngc_strike_grade: z.number().min(1).max(5).nullable().optional(),
    ngc_surface_grade: z.number().min(1).max(5).nullable().optional(),
    is_fine_style: z.boolean().optional().default(false),
  }).nullable().optional(),

  // Chronology enhancements (nested object)
  chronology: z.object({
    date_period_notation: z.string().nullable().optional(),
    emission_phase: z.string().nullable().optional(),
  }).nullable().optional(),

  // Phase 1.5b: Strike quality detail (nested object)
  strike_quality_detail: StrikeQualityDetailSchema.nullable().optional(),

  // Phase 1.5b: Countermarks (array of countermark objects)
  countermarks: z.array(CountermarkSchema).optional().default([]),
})

// Export CoinSchema as the Domain structure since backend V2 returns this nested format
export const CoinSchema = DomainCoinSchema;

// Legacy flat schema if needed for reference or flat inputs
// export const CoinSchemaOld = BaseCoinSchema.transform(...)

// --- Provenance Event Types (V3) ---
export const ProvenanceEventTypeSchema = z.enum([
  'auction',
  'dealer',
  'collection',
  'private_sale',
  'publication',
  'hoard_find',
  'estate',
  'acquisition',  // Current ownership - my purchase
  'unknown'
]);

export const ProvenanceSourceSchema = z.enum([
  'manual_entry',
  'scraper',
  'import',
  'llm_enrichment',
  'migration',
  'auto_acquisition'
]);

// --- Provenance Event Schema (V3) ---
export const ProvenanceEventSchema = z.object({
  id: z.number().optional(),
  coin_id: z.number().optional(),

  // Event classification - UNIFIED source_name field
  event_type: ProvenanceEventTypeSchema,
  source_name: z.string(),  // Unified: auction house, dealer, collection, etc.

  // Dating (flexible)
  event_date: z.string().nullable().optional(),
  date_string: z.string().nullable().optional(),  // "1920s", "circa 1840"

  // Auction/Sale details
  sale_name: z.string().nullable().optional(),  // "January 2024 NYINC Sale"
  sale_number: z.string().nullable().optional(),
  lot_number: z.string().nullable().optional(),
  catalog_reference: z.string().nullable().optional(),

  // Pricing
  hammer_price: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  buyers_premium_pct: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  total_price: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  computed_total: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),  // Computed from hammer + premium
  currency: z.string().nullable().optional(),

  // Documentation
  url: z.string().nullable().optional(),
  receipt_available: z.boolean().nullable().optional(),
  notes: z.string().nullable().optional(),

  // Metadata
  source_origin: ProvenanceSourceSchema.optional().default('manual_entry'),
  sort_order: z.preprocess(preprocessNaN, z.coerce.number().nullable().optional()),
  raw_text: z.string().optional().default(''),  // Display string
  is_acquisition: z.boolean().optional().default(false),  // True if current ownership

  // Legacy fields (for backward compat during migration)
  auction_house: z.string().nullable().optional(),
  dealer_name: z.string().nullable().optional(),
  collection_name: z.string().nullable().optional(),
  sale_series: z.string().nullable().optional(),
});

export type ProvenanceEvent = z.infer<typeof ProvenanceEventSchema>;
export type ProvenanceEventType = z.infer<typeof ProvenanceEventTypeSchema>;
export type ProvenanceSource = z.infer<typeof ProvenanceSourceSchema>;

// --- Provenance Chain Response ---
export const ProvenanceChainSchema = z.object({
  coin_id: z.number(),
  entries: z.array(ProvenanceEventSchema),
  earliest_known_year: z.number().nullable().optional(),
  has_acquisition: z.boolean().default(false),
  total_entries: z.number().default(0),
});

export type ProvenanceChain = z.infer<typeof ProvenanceChainSchema>;

export type Metal = z.infer<typeof MetalSchema>
export type Category = z.infer<typeof CategorySchema>
export type GradingState = z.infer<typeof GradingStateSchema>
export type Rarity = 'c' | 's' | 'r1' | 'r2' | 'r3' | 'u';
export type GradeService = z.infer<typeof GradeServiceSchema>
export type IssueStatus = z.infer<typeof IssueStatusSchema>
export type Dimensions = z.infer<typeof DimensionsSchema>
export type DieInfo = z.infer<typeof DieInfoSchema>
export type Monogram = z.infer<typeof MonogramSchema>
export type FindData = z.infer<typeof FindDataSchema>
export type Attribution = z.infer<typeof AttributionSchema>
export type GradingDetails = z.infer<typeof GradingDetailsSchema>
export type AcquisitionDetails = z.infer<typeof AcquisitionDetailsSchema>
export type Image = z.infer<typeof ImageSchema>
export type Coin = z.infer<typeof CoinSchema>
export type Series = z.infer<typeof SeriesSchema>
export type SeriesSlot = z.infer<typeof SeriesSlotSchema>

// --- Legend Expansion Types ---
export interface LegendExpansionRequest {
  text: string;
  side: "obverse" | "reverse";
  coin_id?: number;
}

export interface LegendExpansionResponse {
  original: string;
  expanded: string;
  confidence: number;
  tokens: Array<{
    token: string;
    expansion: string | null;
    meaning?: string;
  }>;
}

// =============================================================================
// Schema V3 - Phase 1: Core Numismatic Enhancements
// =============================================================================

export const AuthorityTypeSchema = z.enum([
  // Greek civic officials
  'magistrate', 'strategos', 'archon', 'epistates', 'tyrant',
  // Hellenistic rulers
  'satrap', 'dynast', 'basileus', 'monarch',
  // Roman provincial officials
  'proconsul', 'procurator', 'prefect', 'legate',
  // Judaean authorities
  'tetrarch', 'ethnarch',
  // Roman Republican officials
  'quaestor', 'praetor'
]);

// --- Phase 1 Value Object Schemas (nested representation) ---

export const SecondaryAuthoritySchema = z.object({
  name: z.string().nullable().optional(),
  term_id: z.number().nullable().optional(),
  authority_type: z.string().nullable().optional(),
}).nullable().optional();

export const CoRulerSchema = z.object({
  name: z.string().nullable().optional(),
  term_id: z.number().nullable().optional(),
  portrait_relationship: z.string().nullable().optional(),
}).nullable().optional();

export const PhysicalEnhancementsSchema = z.object({
  weight_standard: z.string().nullable().optional(),
  expected_weight_g: z.number().nullable().optional(),
  flan_shape: z.string().nullable().optional(),
  flan_type: z.string().nullable().optional(),
  flan_notes: z.string().nullable().optional(),
}).nullable().optional();

export const SecondaryTreatmentsV3Schema = z.object({
  is_overstrike: z.boolean().optional(),
  undertype_visible: z.string().nullable().optional(),
  undertype_attribution: z.string().nullable().optional(),
  has_test_cut: z.boolean().optional(),
  test_cut_count: z.number().nullable().optional(),
  test_cut_positions: z.string().nullable().optional(),
  has_bankers_marks: z.boolean().optional(),
  has_graffiti: z.boolean().optional(),
  graffiti_description: z.string().nullable().optional(),
  was_mounted: z.boolean().optional(),
  mount_evidence: z.string().nullable().optional(),
}).nullable().optional();

export const ToolingRepairsSchema = z.object({
  tooling_extent: z.string().nullable().optional(),
  tooling_details: z.string().nullable().optional(),
  has_ancient_repair: z.boolean().optional(),
  ancient_repairs: z.string().nullable().optional(),
}).nullable().optional();

export const CenteringInfoSchema = z.object({
  centering: z.string().nullable().optional(),
  centering_notes: z.string().nullable().optional(),
}).nullable().optional();

export const DieStudyEnhancementsSchema = z.object({
  obverse_die_state: z.string().nullable().optional(),
  reverse_die_state: z.string().nullable().optional(),
  die_break_description: z.string().nullable().optional(),
}).nullable().optional();

export const GradingTPGEnhancementsSchema = z.object({
  grade_numeric: z.number().nullable().optional(),
  grade_designation: z.string().nullable().optional(),
  has_star_designation: z.boolean().optional(),
  photo_certificate: z.boolean().optional(),
  verification_url: z.string().nullable().optional(),
  // Phase 1.5b: NGC-specific fields (PCGS doesn't use 1-5 scale for ancients)
  ngc_strike_grade: z.number().min(1).max(5).nullable().optional(),
  ngc_surface_grade: z.number().min(1).max(5).nullable().optional(),
  is_fine_style: z.boolean().optional().default(false),
}).nullable().optional();

export const ChronologyEnhancementsSchema = z.object({
  date_period_notation: z.string().nullable().optional(),
  emission_phase: z.string().nullable().optional(),
}).nullable().optional();

export const PortraitRelationshipSchema = z.enum([
  // Direct relationships
  'self', 'consort', 'heir', 'parent', 'sibling',
  // Succession relationships
  'predecessor', 'ancestor', 'adoptive_parent',
  // Commemorative
  'commemorative', 'divus', 'diva',
  // Divine/symbolic
  'deity', 'personification'
]);

export const WeightStandardSchema = z.enum([
  // Greek weight standards
  'attic', 'aeginetan', 'corinthian', 'phoenician', 'alexandrine',
  'ptolemaic', 'chian', 'milesian', 'euboic', 'persic', 'rhodian',
  // Roman Republican weight standards
  'libral', 'sextantal', 'denarius_early', 'denarius_reformed', 'antoninianus',
  // Late Roman weight standards
  'solidus', 'siliqua', 'tremissis', 'follis_reform',
  // Byzantine weight standards
  'histamenon', 'tetarteron', 'hyperpyron'
]);

export const FlanShapeSchema = z.enum([
  'round', 'irregular', 'oval', 'square', 'scyphate',
  'rectangular', 'incuse_square'
]);

export const FlanTypeSchema = z.enum([
  'cast', 'struck', 'cut_from_bar', 'hammered',
  'dump', 'spread', 'serrated'
]);

export const FlanEdgeSchema = z.enum([
  'plain', 'reeded', 'lettered', 'serrated', 'beveled', 'incuse'
]);

export const ToolingExtentSchema = z.enum([
  'none', 'minor', 'moderate', 'significant', 'extensive'
]);

export const CenteringSchema = z.enum([
  'well-centered', 'slightly_off', 'off_center', 'significantly_off'
]);

export const DieStateSchema = z.enum([
  'fresh', 'early', 'middle', 'late', 'worn', 'broken', 'repaired'
]);

export const GradeDesignationSchema = z.enum([
  'Fine Style', 'Choice', 'Gem', 'Superb Gem'
]);

// =============================================================================
// Schema V3 - Phase 2: Grading & Rarity System
// =============================================================================

export const GradingEventTypeSchema = z.enum([
  'initial', 'crossover', 'regrade', 'crack_out', 'upgrade_attempt'
]);

export const GradingHistoryEntrySchema = z.object({
  id: z.number().optional(),
  coin_id: z.number(),

  grading_state: z.string(),
  grade: z.string().nullable().optional(),
  grade_service: z.string().nullable().optional(),
  certification_number: z.string().nullable().optional(),
  strike_quality: z.string().nullable().optional(),
  surface_quality: z.string().nullable().optional(),
  grade_numeric: z.number().nullable().optional(),
  designation: z.string().nullable().optional(),
  has_star: z.boolean().optional(),
  photo_cert: z.boolean().optional(),
  verification_url: z.string().nullable().optional(),

  event_type: GradingEventTypeSchema,
  graded_date: z.string().nullable().optional(),
  recorded_at: z.string().optional(),
  submitter: z.string().nullable().optional(),
  turnaround_days: z.number().nullable().optional(),
  grading_fee: z.number().nullable().optional(),
  notes: z.string().nullable().optional(),

  sequence_order: z.number().optional(),
  is_current: z.boolean().optional(),
});

export const RaritySystemSchema = z.enum([
  'RIC', 'catalog', 'census', 'market_frequency', 'custom'
]);

export const RaritySourceTypeSchema = z.enum([
  'catalog', 'census_data', 'auction_analysis', 'expert_opinion', 'database'
]);

export const RarityAssessmentSchema = z.object({
  id: z.number().optional(),
  coin_id: z.number(),

  rarity_code: z.string(),
  rarity_system: RaritySystemSchema,
  source_type: RaritySourceTypeSchema,
  source_name: z.string().nullable().optional(),
  source_url: z.string().nullable().optional(),
  source_date: z.string().nullable().optional(),

  grade_range_low: z.string().nullable().optional(),
  grade_range_high: z.string().nullable().optional(),
  grade_conditional_notes: z.string().nullable().optional(),

  census_total: z.number().nullable().optional(),
  census_this_grade: z.number().nullable().optional(),
  census_finer: z.number().nullable().optional(),
  census_date: z.string().nullable().optional(),

  confidence: z.enum(['low', 'medium', 'high', 'authoritative']).optional(),
  notes: z.string().nullable().optional(),
  is_primary: z.boolean().optional(),
  created_at: z.string().optional(),
});

export const CensusSnapshotSchema = z.object({
  id: z.number().optional(),
  coin_id: z.number(),
  service: z.enum(['NGC', 'PCGS']),
  snapshot_date: z.string(),
  total_graded: z.number(),
  grade_breakdown: z.record(z.string(), z.number()).nullable().optional(),
  coins_at_grade: z.number().nullable().optional(),
  coins_finer: z.number().nullable().optional(),
  percentile: z.number().nullable().optional(),
  catalog_reference: z.string().nullable().optional(),
  notes: z.string().nullable().optional(),
});

// =============================================================================
// Schema V3 - Phase 4: LLM Architecture
// =============================================================================

export const LLMCapabilitySchema = z.enum([
  'context_generate', 'attribution_suggest', 'catalog_lookup',
  'provenance_parse', 'design_describe', 'value_estimate',
  'rarity_assess', 'condition_assess', 'iconography_identify',
  'historical_context', 'artistic_analysis'
]);

export const LLMReviewStatusSchema = z.enum([
  'pending', 'approved', 'rejected', 'revised'
]);

export const LLMEnrichmentSchema = z.object({
  id: z.number().optional(),
  coin_id: z.number(),

  capability: LLMCapabilitySchema,
  capability_version: z.number().optional(),
  model_id: z.string(),
  model_version: z.string().nullable().optional(),

  input_hash: z.string(),
  output_content: z.string(),

  confidence: z.number(),
  needs_review: z.boolean().optional(),
  quality_flags: z.array(z.string()).nullable().optional(),

  cost_usd: z.number().nullable().optional(),
  input_tokens: z.number().nullable().optional(),
  output_tokens: z.number().nullable().optional(),
  cached: z.boolean().optional(),
  latency_ms: z.number().nullable().optional(),

  review_status: LLMReviewStatusSchema.optional(),
  reviewed_by: z.string().nullable().optional(),
  reviewed_at: z.string().nullable().optional(),
  review_notes: z.string().nullable().optional(),

  created_at: z.string().optional(),
  expires_at: z.string().nullable().optional(),
});

// =============================================================================
// Schema V3 - Phase 5: Market Tracking & Wishlists
// =============================================================================

export const MarketSourceTypeSchema = z.enum([
  'auction_realized', 'auction_unsold', 'dealer_asking', 'private_sale', 'estimate'
]);

export const MarketPriceSchema = z.object({
  id: z.number().optional(),
  attribution_key: z.string(),
  issuer: z.string().nullable().optional(),
  denomination: z.string().nullable().optional(),
  mint: z.string().nullable().optional(),
  metal: z.string().nullable().optional(),
  category: z.string().nullable().optional(),
  catalog_ref: z.string().nullable().optional(),

  avg_price_vf: z.number().nullable().optional(),
  avg_price_ef: z.number().nullable().optional(),
  avg_price_au: z.number().nullable().optional(),
  avg_price_ms: z.number().nullable().optional(),
  min_price_seen: z.number().nullable().optional(),
  max_price_seen: z.number().nullable().optional(),
  median_price: z.number().nullable().optional(),

  data_point_count: z.number().optional(),
  last_sale_date: z.string().nullable().optional(),
  last_updated: z.string().nullable().optional(),
});

export const MarketDataPointSchema = z.object({
  id: z.number().optional(),
  market_price_id: z.number(),
  price: z.number(),
  currency: z.string().optional(),
  price_usd: z.number().nullable().optional(),
  source_type: MarketSourceTypeSchema,
  date: z.string(),
  grade: z.string().nullable().optional(),
  grade_numeric: z.number().nullable().optional(),
  condition_notes: z.string().nullable().optional(),
  auction_house: z.string().nullable().optional(),
  sale_name: z.string().nullable().optional(),
  lot_number: z.string().nullable().optional(),
  lot_url: z.string().nullable().optional(),
  dealer_name: z.string().nullable().optional(),
  // Price breakdown for auction sales
  is_hammer_price: z.boolean().optional(),
  buyers_premium_pct: z.number().nullable().optional(),
  // Slabbed coin information
  is_slabbed: z.boolean().optional(),
  grading_service: z.string().nullable().optional(),
  certification_number: z.string().nullable().optional(),
  confidence: z.enum(['low', 'medium', 'high', 'verified']).optional(),
  notes: z.string().nullable().optional(),
  created_at: z.string().optional(),
});

export const CoinValuationSchema = z.object({
  id: z.number().optional(),
  coin_id: z.number(),
  valuation_date: z.string(),

  purchase_price: z.number().nullable().optional(),
  purchase_currency: z.string().nullable().optional(),
  purchase_date: z.string().nullable().optional(),

  current_market_value: z.number().nullable().optional(),
  value_currency: z.string().optional(),
  market_confidence: z.enum(['low', 'medium', 'high', 'strong']).nullable().optional(),

  comparable_count: z.number().nullable().optional(),
  comparable_avg_price: z.number().nullable().optional(),
  comparable_date_range: z.string().nullable().optional(),
  price_trend_6mo: z.number().nullable().optional(),
  price_trend_12mo: z.number().nullable().optional(),
  price_trend_36mo: z.number().nullable().optional(),

  gain_loss_usd: z.number().nullable().optional(),
  gain_loss_pct: z.number().nullable().optional(),

  valuation_method: z.string().nullable().optional(),
  notes: z.string().nullable().optional(),
  created_at: z.string().optional(),
});

export const WishlistPrioritySchema = z.enum(['1', '2', '3', '4']);

export const WishlistStatusSchema = z.enum([
  'wanted', 'watching', 'bidding', 'acquired', 'cancelled'
]);

export const WishlistItemSchema = z.object({
  id: z.number().optional(),
  title: z.string(),
  description: z.string().nullable().optional(),

  issuer: z.string().nullable().optional(),
  issuer_id: z.number().nullable().optional(),
  mint: z.string().nullable().optional(),
  mint_id: z.number().nullable().optional(),
  year_start: z.number().nullable().optional(),
  year_end: z.number().nullable().optional(),
  denomination: z.string().nullable().optional(),
  metal: z.string().nullable().optional(),
  category: z.string().nullable().optional(),
  catalog_ref: z.string().nullable().optional(),
  catalog_ref_pattern: z.string().nullable().optional(),

  min_grade: z.string().nullable().optional(),
  min_grade_numeric: z.number().nullable().optional(),
  condition_notes: z.string().nullable().optional(),
  max_price: z.number().nullable().optional(),
  target_price: z.number().nullable().optional(),
  currency: z.string().optional(),

  priority: z.number().optional(),
  tags: z.string().nullable().optional(),
  series_slot_id: z.number().nullable().optional(),
  status: WishlistStatusSchema.optional(),

  acquired_coin_id: z.number().nullable().optional(),
  acquired_at: z.string().nullable().optional(),
  acquired_price: z.number().nullable().optional(),

  notify_on_match: z.boolean().optional(),
  notify_email: z.boolean().optional(),
  notes: z.string().nullable().optional(),
  created_at: z.string().optional(),
  updated_at: z.string().nullable().optional(),
});

export const WishlistMatchSchema = z.object({
  id: z.number().optional(),
  wishlist_item_id: z.number(),

  match_type: z.string(),
  match_source: z.string().nullable().optional(),
  match_id: z.string(),
  match_url: z.string().nullable().optional(),

  title: z.string(),
  description: z.string().nullable().optional(),
  image_url: z.string().nullable().optional(),

  grade: z.string().nullable().optional(),
  price: z.number().nullable().optional(),
  estimate_low: z.number().nullable().optional(),
  estimate_high: z.number().nullable().optional(),
  currency: z.string().optional(),

  auction_date: z.string().nullable().optional(),

  match_score: z.number().nullable().optional(),
  match_confidence: z.enum(['exact', 'high', 'medium', 'possible']).nullable().optional(),

  is_below_budget: z.boolean().nullable().optional(),
  is_below_market: z.boolean().nullable().optional(),
  value_score: z.number().nullable().optional(),

  notified: z.boolean().optional(),
  dismissed: z.boolean().optional(),
  saved: z.boolean().optional(),

  created_at: z.string().optional(),
});

export const PriceAlertTriggerSchema = z.enum([
  'price_below', 'price_above', 'price_change_pct', 'new_listing', 'auction_soon'
]);

export const PriceAlertStatusSchema = z.enum([
  'active', 'triggered', 'paused', 'expired', 'deleted'
]);

export const PriceAlertSchema = z.object({
  id: z.number().optional(),

  attribution_key: z.string().nullable().optional(),
  coin_id: z.number().nullable().optional(),
  wishlist_item_id: z.number().nullable().optional(),

  trigger_type: PriceAlertTriggerSchema,
  threshold_value: z.number().nullable().optional(),
  threshold_pct: z.number().nullable().optional(),
  threshold_grade: z.string().nullable().optional(),

  status: PriceAlertStatusSchema.optional(),
  created_at: z.string().optional(),
  triggered_at: z.string().nullable().optional(),
  expires_at: z.string().nullable().optional(),

  notification_sent: z.boolean().optional(),
  cooldown_hours: z.number().optional(),
  notes: z.string().nullable().optional(),
});

// =============================================================================
// Schema V3 - Phase 6: Collections & Sub-collections
// =============================================================================

export const CollectionTypeSchema = z.enum([
  'custom', 'smart', 'series', 'type_set', 'system'
]);

export const CollectionPurposeSchema = z.enum([
  'study', 'display', 'type_set', 'duplicates', 'reserves', 'insurance', 'general'
]);

export const SmartCriteriaSchema = z.object({
  match: z.enum(['all', 'any']).optional(),
  conditions: z.array(z.record(z.string(), z.unknown())).optional(),
});

export const CollectionSchema = z.object({
  id: z.number().optional(),
  name: z.string(),
  description: z.string().nullable().optional(),
  slug: z.string().nullable().optional(),

  collection_type: CollectionTypeSchema.optional(),
  purpose: CollectionPurposeSchema.optional(),
  smart_criteria: SmartCriteriaSchema.nullable().optional(),
  series_id: z.number().nullable().optional(),

  // Type set tracking
  is_type_set: z.boolean().optional(),
  type_set_definition: z.string().nullable().optional(),
  completion_percentage: z.number().nullable().optional(),

  // Display settings
  cover_image_url: z.string().nullable().optional(),
  cover_coin_id: z.number().nullable().optional(),
  color: z.string().nullable().optional(),
  icon: z.string().nullable().optional(),
  display_order: z.number().nullable().optional(),
  default_sort: z.string().nullable().optional(),
  default_view: z.enum(['grid', 'table', 'timeline']).nullable().optional(),

  // Cached statistics
  coin_count: z.number().optional(),
  total_value: z.number().nullable().optional(),
  stats_updated_at: z.string().nullable().optional(),

  // Flags
  is_favorite: z.boolean().optional(),
  is_hidden: z.boolean().optional(),
  is_public: z.boolean().optional(),

  // Hierarchy (limited to 3 levels)
  parent_id: z.number().nullable().optional(),
  level: z.number().optional(),

  // Physical storage mapping
  storage_location: z.string().nullable().optional(),

  notes: z.string().nullable().optional(),
  created_at: z.string().optional(),
  updated_at: z.string().nullable().optional(),
});

export const CollectionCoinSchema = z.object({
  collection_id: z.number(),
  coin_id: z.number(),
  added_at: z.string().optional(),
  added_by: z.string().nullable().optional(),
  position: z.number().nullable().optional(),
  custom_order: z.number().nullable().optional(),
  notes: z.string().nullable().optional(),
  is_featured: z.boolean().optional(),
  is_cover_coin: z.boolean().optional(),
  // From numismatic review
  is_placeholder: z.boolean().optional(),
  exclude_from_stats: z.boolean().optional(),
  fulfills_type: z.string().nullable().optional(),
  series_slot_id: z.number().nullable().optional(),
});

export const CollectionStatisticsSchema = z.object({
  collection_id: z.number(),
  coin_count: z.number().optional(),
  total_value: z.number().nullable().optional(),
  total_cost: z.number().nullable().optional(),
  unrealized_gain_loss: z.number().nullable().optional(),
  metal_breakdown: z.record(z.string(), z.number()).nullable().optional(),
  denomination_breakdown: z.record(z.string(), z.number()).nullable().optional(),
  category_breakdown: z.record(z.string(), z.number()).nullable().optional(),
  grade_distribution: z.record(z.string(), z.number()).nullable().optional(),
  average_grade: z.number().nullable().optional(),
  slabbed_count: z.number().optional(),
  raw_count: z.number().optional(),
  earliest_coin_year: z.number().nullable().optional(),
  latest_coin_year: z.number().nullable().optional(),
  completion_percentage: z.number().nullable().optional(),
});

// =============================================================================
// Schema V3 Type Exports
// =============================================================================

export type AuthorityType = z.infer<typeof AuthorityTypeSchema>;
export type PortraitRelationship = z.infer<typeof PortraitRelationshipSchema>;
export type WeightStandard = z.infer<typeof WeightStandardSchema>;
export type FlanShape = z.infer<typeof FlanShapeSchema>;
export type FlanType = z.infer<typeof FlanTypeSchema>;
export type FlanEdge = z.infer<typeof FlanEdgeSchema>;
export type ToolingExtent = z.infer<typeof ToolingExtentSchema>;
export type CenteringQuality = z.infer<typeof CenteringSchema>;
export type DieState = z.infer<typeof DieStateSchema>;
export type GradeDesignation = z.infer<typeof GradeDesignationSchema>;

// Phase 1 Value Object Types
export type SecondaryAuthority = z.infer<typeof SecondaryAuthoritySchema>;
export type CoRuler = z.infer<typeof CoRulerSchema>;
export type PhysicalEnhancements = z.infer<typeof PhysicalEnhancementsSchema>;
export type SecondaryTreatmentsV3 = z.infer<typeof SecondaryTreatmentsV3Schema>;
export type ToolingRepairs = z.infer<typeof ToolingRepairsSchema>;
export type CenteringInfo = z.infer<typeof CenteringInfoSchema>;
export type DieStudyEnhancements = z.infer<typeof DieStudyEnhancementsSchema>;
export type GradingTPGEnhancements = z.infer<typeof GradingTPGEnhancementsSchema>;
export type ChronologyEnhancements = z.infer<typeof ChronologyEnhancementsSchema>;

export type GradingEventType = z.infer<typeof GradingEventTypeSchema>;
export type GradingHistoryEntry = z.infer<typeof GradingHistoryEntrySchema>;
export type RaritySystem = z.infer<typeof RaritySystemSchema>;
export type RaritySourceType = z.infer<typeof RaritySourceTypeSchema>;
export type RarityAssessment = z.infer<typeof RarityAssessmentSchema>;
export type CensusSnapshot = z.infer<typeof CensusSnapshotSchema>;

export type LLMCapability = z.infer<typeof LLMCapabilitySchema>;
export type LLMReviewStatus = z.infer<typeof LLMReviewStatusSchema>;
export type LLMEnrichment = z.infer<typeof LLMEnrichmentSchema>;

export type MarketSourceType = z.infer<typeof MarketSourceTypeSchema>;
export type MarketPrice = z.infer<typeof MarketPriceSchema>;
export type MarketDataPoint = z.infer<typeof MarketDataPointSchema>;
export type CoinValuation = z.infer<typeof CoinValuationSchema>;
export type WishlistPriority = z.infer<typeof WishlistPrioritySchema>;
export type WishlistStatus = z.infer<typeof WishlistStatusSchema>;
export type WishlistItem = z.infer<typeof WishlistItemSchema>;
export type WishlistMatch = z.infer<typeof WishlistMatchSchema>;
export type PriceAlertTrigger = z.infer<typeof PriceAlertTriggerSchema>;
export type PriceAlertStatus = z.infer<typeof PriceAlertStatusSchema>;
export type PriceAlert = z.infer<typeof PriceAlertSchema>;

export type CollectionType = z.infer<typeof CollectionTypeSchema>;
export type CollectionPurpose = z.infer<typeof CollectionPurposeSchema>;
export type SmartCriteria = z.infer<typeof SmartCriteriaSchema>;
export type Collection = z.infer<typeof CollectionSchema>;
export type CollectionCoin = z.infer<typeof CollectionCoinSchema>;
export type CollectionStatistics = z.infer<typeof CollectionStatisticsSchema>;