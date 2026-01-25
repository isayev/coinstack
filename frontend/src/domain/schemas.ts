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

export const DimensionsSchema = z.object({
  weight_g: z.coerce.number().min(0).nullable().optional(),
  diameter_mm: z.coerce.number().min(0).nullable().optional(),
  thickness_mm: z.coerce.number().min(0).nullable().optional(),
  die_axis: z.coerce.number().min(0).max(12).nullable().optional(),
})

export const AttributionSchema = z.object({
  issuer: z.string().min(1).nullable().optional(),
  mint: z.string().nullable().optional(),
  year_start: z.coerce.number().nullable().optional(),
  year_end: z.coerce.number().nullable().optional(),
})

export const GradingDetailsSchema = z.object({
  grading_state: GradingStateSchema.optional(),
  grade: z.string().nullable().optional(),
  service: GradeServiceSchema.nullable().optional(),
  certification_number: z.string().nullable().optional(),
  strike: z.string().nullable().optional(),
  surface: z.string().nullable().optional(),
  eye_appeal: z.number().nullable().optional(),
  toning_description: z.string().nullable().optional(),
})

export const AcquisitionDetailsSchema = z.object({
  price: z.coerce.number().min(0).nullable().optional(),
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
  reign_start: z.number().nullable().optional(),
  reign_end: z.number().nullable().optional(),
  mint_year_start: z.number().nullable().optional(),
  mint_year_end: z.number().nullable().optional(),
  is_circa: z.boolean().optional(),

  // Physical
  weight_g: z.number().nullable().optional(),
  diameter_mm: z.number().nullable().optional(),
  thickness_mm: z.number().nullable().optional(),
  die_axis: z.number().nullable().optional(),

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
  acquisition_price: z.number().nullable().optional(),
  acquisition_source: z.string().nullable().optional(),
  acquisition_date: z.string().nullable().optional(),
  acquisition_currency: z.string().nullable().optional(),
  acquisition_url: z.string().nullable().optional(),

  // Mint
  mint_name: z.string().nullable().optional(),

  // Relations
  images: z.array(ImageSchema).default([]).optional(),
  tags: z.array(z.string()).optional(),
  auction_data: z.array(z.any()).optional(),
  provenance_events: z.array(z.any()).optional(),
})

// Schema for the Nested Domain Entity (used by Forms and UI components)
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

  reign_start: z.number().nullable().optional(),
  reign_end: z.number().nullable().optional(),
  mint_year_start: z.number().nullable().optional(),
  mint_year_end: z.number().nullable().optional(),
  is_circa: z.boolean().optional(),

  // Nested Objects
  dimensions: DimensionsSchema,
  attribution: AttributionSchema,
  grading: GradingDetailsSchema,
  acquisition: AcquisitionDetailsSchema.nullable().optional(), // acquisition can be null

  mint_name: z.string().nullable().optional(),

  obverse_legend: z.string().nullable().optional(),
  obverse_description: z.string().nullable().optional(),
  reverse_legend: z.string().nullable().optional(),
  reverse_description: z.string().nullable().optional(),
  description: z.string().nullable().optional(),

  images: z.array(ImageSchema).default([]).optional(),
  tags: z.array(z.string()).optional(),
})

// Export CoinSchema as the Domain structure since backend V2 returns this nested format
export const CoinSchema = DomainCoinSchema;

// Legacy flat schema if needed for reference or flat inputs
// export const CoinSchemaOld = BaseCoinSchema.transform(...)

export type Metal = z.infer<typeof MetalSchema>
export type Category = z.infer<typeof CategorySchema>
export type GradingState = z.infer<typeof GradingStateSchema>
export type GradeService = z.infer<typeof GradeServiceSchema>
export type Dimensions = z.infer<typeof DimensionsSchema>
export type Attribution = z.infer<typeof AttributionSchema>
export type GradingDetails = z.infer<typeof GradingDetailsSchema>
export type AcquisitionDetails = z.infer<typeof AcquisitionDetailsSchema>
export type Image = z.infer<typeof ImageSchema>
export type Coin = z.infer<typeof CoinSchema>

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