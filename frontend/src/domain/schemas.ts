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
  'greek',
  'roman_imperial',
  'roman_republic',
  'roman_provincial',
  'byzantine',
  'medieval',
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
  eye_appeal: z.preprocess(preprocessNaN, z.number().nullable().optional()),
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
  reign_start: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  reign_end: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  mint_year_start: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  mint_year_end: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  is_circa: z.boolean().optional(),

  // Physical
  weight_g: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  diameter_mm: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  thickness_mm: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  die_axis: z.preprocess(preprocessNaN, z.number().nullable().optional()),

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
  acquisition_price: z.preprocess(preprocessNaN, z.number().nullable().optional()),
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

  reign_start: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  reign_end: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  mint_year_start: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  mint_year_end: z.preprocess(preprocessNaN, z.number().nullable().optional()),
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
    event_date: z.string().nullable().optional(),
    auction_house: z.string().nullable().optional(),
    sale_series: z.string().nullable().optional(),
    sale_number: z.string().nullable().optional(),
    lot_number: z.string().nullable().optional(),
    catalog_reference: z.string().nullable().optional(),
    hammer_price: z.preprocess(preprocessNaN, z.number().nullable().optional()),
    buyers_premium_pct: z.preprocess(preprocessNaN, z.number().nullable().optional()),
    total_price: z.preprocess(preprocessNaN, z.number().nullable().optional()),
    currency: z.string().nullable().optional(),
    dealer_name: z.string().nullable().optional(),
    collection_name: z.string().nullable().optional(),
    url: z.string().nullable().optional(),
    receipt_available: z.boolean().nullable().optional(),
    notes: z.string().nullable().optional(),
    sort_order: z.number().nullable().optional(),
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
  market_value: z.preprocess(preprocessNaN, z.number().nullable().optional()),
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
})

// Export CoinSchema as the Domain structure since backend V2 returns this nested format
export const CoinSchema = DomainCoinSchema;

// Legacy flat schema if needed for reference or flat inputs
// export const CoinSchemaOld = BaseCoinSchema.transform(...)

// --- Provenance Event Schema ---
export const ProvenanceEventSchema = z.object({
  id: z.number().optional(),
  coin_id: z.number().optional(),
  event_type: z.string(),  // auction, dealer, collection, private_sale
  event_date: z.string().nullable().optional(),
  auction_house: z.string().nullable().optional(),
  sale_series: z.string().nullable().optional(),
  sale_number: z.string().nullable().optional(),
  lot_number: z.string().nullable().optional(),
  catalog_reference: z.string().nullable().optional(),
  hammer_price: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  buyers_premium_pct: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  total_price: z.preprocess(preprocessNaN, z.number().nullable().optional()),
  currency: z.string().nullable().optional(),
  dealer_name: z.string().nullable().optional(),
  collection_name: z.string().nullable().optional(),
  url: z.string().nullable().optional(),
  receipt_available: z.boolean().nullable().optional(),
  notes: z.string().nullable().optional(),
  sort_order: z.number().nullable().optional(),
});

export type ProvenanceEvent = z.infer<typeof ProvenanceEventSchema>;

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