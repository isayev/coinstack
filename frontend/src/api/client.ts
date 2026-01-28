import api from './api'
import { Coin, CoinSchema, SeriesSchema } from '@/domain/schemas'
import { z } from 'zod'

const PaginatedCoinsSchema = z.object({
  items: z.array(CoinSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
  pages: z.number()
})

const SeriesListSchema = z.object({
  items: z.array(SeriesSchema),
  total: z.number()
})

// Schema for creating a new series
const SeriesCreateSchema = z.object({
  name: z.string().min(1),
  slug: z.string().optional(),
  description: z.string().optional(),
  series_type: z.string(),
  category: z.string().optional(),
  target_count: z.number().optional(),
  canonical_vocab_id: z.number().nullable().optional(),
})

// Schema for adding coin to series response
const AddCoinToSeriesResponseSchema = z.object({
  success: z.boolean(),
  series_id: z.number(),
  coin_id: z.number(),
  slot_id: z.number().nullable().optional(),
})

export type PaginatedCoinsResponse = z.infer<typeof PaginatedCoinsSchema>
export type SeriesListResponse = z.infer<typeof SeriesListSchema>

export const DiscrepancySchema = z.object({
  field: z.string(),
  current_value: z.string(),
  auction_value: z.string(),
  confidence: z.number(),
  source: z.string()
})

export const AuditResultSchema = z.object({
  coin_id: z.number(),
  has_issues: z.boolean(),
  discrepancies: z.array(DiscrepancySchema)
})

export const ScrapeResultSchema = z.object({
  source: z.string(),
  lot_id: z.string(),
  url: z.string(),
  sale_name: z.string().nullable().optional(),
  lot_number: z.string().nullable().optional(),
  hammer_price: z.coerce.number().nullable().optional(),
  issuer: z.string().nullable().optional(),
  grade: z.string().nullable().optional()
})

export type Discrepancy = z.infer<typeof DiscrepancySchema>
export type AuditResult = z.infer<typeof AuditResultSchema>
export type ScrapeResult = z.infer<typeof ScrapeResultSchema>


// --- Stats Schemas ---
const CategoryDistributionSchema = z.object({
  category: z.string(),
  count: z.number(),
  color: z.string()
})

const MetalDistributionSchema = z.object({
  metal: z.string(),
  symbol: z.string(),
  count: z.number()
})

const GradeDistributionSchema = z.object({
  grade: z.string(),
  count: z.number(),
  numeric: z.number().nullable().optional()
})

const RulerDistributionSchema = z.object({
  ruler: z.string(),
  ruler_id: z.number().nullable().optional(),
  count: z.number(),
  reign_start: z.number().nullable().optional()
})

const RarityDistributionSchema = z.object({
  rarity: z.string(),
  count: z.number()
})

const YearDistributionSchema = z.object({
  year: z.number(),
  count: z.number()
})

const AcquisitionMonthSchema = z.object({
  month: z.string(),
  count: z.number(),
  value_usd: z.number().nullable().optional()
})

const HealthMetricsSchema = z.object({
  overall_pct: z.number(),
  total_coins: z.number(),
  with_images: z.number(),
  with_attribution: z.number(),
  with_references: z.number(),
  with_provenance: z.number(),
  with_values: z.number()
})

const StatsSummarySchema = z.object({
  total_coins: z.number(),
  total_value_usd: z.number().nullable().optional(),
  health: HealthMetricsSchema,
  by_category: z.array(CategoryDistributionSchema),
  by_metal: z.array(MetalDistributionSchema),
  by_grade: z.array(GradeDistributionSchema),
  // by_certification
  by_ruler: z.array(RulerDistributionSchema),
  by_year: z.array(YearDistributionSchema),
  by_rarity: z.array(RarityDistributionSchema).optional().default([]),
  acquisitions: z.array(AcquisitionMonthSchema)
})

export type StatsSummaryResponse = z.infer<typeof StatsSummarySchema>

/** Type-safe query params for getCoins */
export interface GetCoinsParams {
  page?: number;
  per_page?: number;
  limit?: number; // Alternative to per_page
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
  category?: string;
  sub_category?: string;
  metal?: string;
  issuing_authority?: string;
  issuer?: string; // Mapped from issuing_authority
  is_ruler_unknown?: boolean;
  mint_name?: string;
  is_mint_unknown?: boolean;
  denomination?: string;
  grade?: string;
  rarity?: string;
  storage_location?: string;
  acquisition_price_gte?: number;
  acquisition_price_lte?: number;
  mint_year_gte?: number;
  mint_year_lte?: number;
  is_year_unknown?: boolean;
  is_circa?: boolean;
  is_test_cut?: boolean;
  search?: string; // Full-text search query
}

export const client = {
  getCoins: async (params?: GetCoinsParams): Promise<PaginatedCoinsResponse> => {
    const response = await api.get('/api/v2/coins', { params })
    return PaginatedCoinsSchema.parse(response.data)
  },

  getCoin: async (id: number): Promise<Coin> => {
    const response = await api.get(`/api/v2/coins/${id}`)
    return CoinSchema.parse(response.data)
  },

  createCoin: async (coin: Omit<Coin, 'id'>): Promise<Coin> => {
    const payload = mapCoinToPayload(coin)
    const response = await api.post('/api/v2/coins', payload)
    return CoinSchema.parse(response.data)
  },

  updateCoin: async (id: number, coin: Omit<Coin, 'id'>): Promise<Coin> => {
    const payload = mapCoinToPayload(coin)
    const response = await api.put(`/api/v2/coins/${id}`, payload)
    return CoinSchema.parse(response.data)
  },

  deleteCoin: async (id: number): Promise<void> => {
    await api.delete(`/api/v2/coins/${id}`)
  },

  // Series (backend prefix: /api/v2/series)
  getSeries: async (): Promise<SeriesListResponse> => {
    const response = await api.get('/api/v2/series')
    return SeriesListSchema.parse(response.data)
  },

  getSeriesDetail: async (id: number): Promise<z.infer<typeof SeriesSchema>> => {
    const response = await api.get(`/api/v2/series/${id}`)
    return SeriesSchema.parse(response.data)
  },

  createSeries: async (data: z.infer<typeof SeriesCreateSchema>): Promise<z.infer<typeof SeriesSchema>> => {
    const validatedData = SeriesCreateSchema.parse(data)
    const response = await api.post('/api/v2/series', validatedData)
    return SeriesSchema.parse(response.data)
  },

  addCoinToSeries: async (seriesId: number, coinId: number, slotId?: number): Promise<z.infer<typeof AddCoinToSeriesResponseSchema>> => {
    const response = await api.post(`/api/v2/series/${seriesId}/coins/${coinId}`, null, {
      params: { slot_id: slotId }
    })
    return AddCoinToSeriesResponseSchema.parse(response.data)
  },

  // Audit
  auditCoin: async (id: number): Promise<AuditResult> => {
    const response = await api.get(`/api/v2/audit/${id}`)
    return AuditResultSchema.parse(response.data)
  },

  applyEnrichment: async (id: number, field: string, value: string): Promise<void> => {
    await api.post(`/api/v2/audit/${id}/apply`, { field, value })
  },

  // Scrape
  scrapeLot: async (url: string): Promise<ScrapeResult> => {
    const response = await api.post('/api/v2/scrape/lot', { url })
    return ScrapeResultSchema.parse(response.data)
  },

  // Import API (Richer than scrape)
  importFromUrl: async (url: string): Promise<ImportPreviewResponse> => {
    const response = await api.post('/api/v2/import/from-url', { url })
    // We don't strict parse here to avoid breaking on minor schema mismatches during dev
    // but in prod we should. For now return as is or use partial parse.
    return response.data as ImportPreviewResponse
  },

  confirmImport: async (data: any): Promise<any> => {
    const response = await api.post('/api/v2/import/confirm', data)
    return response.data
  },

  getCoinsByReference: async (catalog: string, number: string, volume?: string): Promise<Coin[]> => {
    const response = await api.get('/api/v2/coins/by-reference', {
      params: { catalog, number, volume }
    })
    // This returns a list of coins (clones or similar types)
    return z.array(CoinSchema).parse(response.data.coins)
  },

  getStatsSummary: async (params?: Partial<GetCoinsParams>): Promise<StatsSummaryResponse> => {
    const response = await api.get('/api/v2/stats/summary', { params })
    // Use safe parse or standard parse
    return StatsSummarySchema.parse(response.data)
  }
}

// --- Import Schemas ---
export interface ImportPreviewResponse {
  success: boolean
  error?: string
  source_type?: string
  source_id?: string
  source_url?: string
  coin_data?: any // Rich preview data
  images?: any[]
  raw_data?: any
}


/**
 * Helper to map nested domain object to flat/structured API request
 * Maps the frontend Coin domain model to the backend API expected format
 */
function mapCoinToPayload(coin: Omit<Coin, 'id'>) {
  return {
    // Classification
    category: coin.category,
    sub_category: coin.sub_category,
    metal: coin.metal,
    denomination: coin.denomination,
    series: coin.series,

    // Physical dimensions
    weight_g: coin.dimensions?.weight_g,
    diameter_mm: coin.dimensions?.diameter_mm,
    thickness_mm: coin.dimensions?.thickness_mm,
    die_axis: coin.dimensions?.die_axis,
    specific_gravity: coin.dimensions?.specific_gravity,

    // Attribution
    issuer: coin.attribution?.issuer,
    issuer_id: coin.attribution?.issuer_id,
    mint: coin.attribution?.mint,
    mint_id: coin.attribution?.mint_id,
    year_start: coin.attribution?.year_start,
    year_end: coin.attribution?.year_end,

    // Grading
    grading_state: coin.grading?.grading_state,
    grade: coin.grading?.grade,
    grade_service: coin.grading?.service,
    certification: coin.grading?.certification_number,
    strike: coin.grading?.strike,
    surface: coin.grading?.surface,

    // Acquisition
    acquisition_price: coin.acquisition?.price,
    acquisition_source: coin.acquisition?.source,
    acquisition_date: coin.acquisition?.date || null,
    acquisition_url: coin.acquisition?.url,
    acquisition_currency: coin.acquisition?.currency,

    // Design
    obverse_legend: coin.design?.obverse_legend,
    obverse_description: coin.design?.obverse_description,
    reverse_legend: coin.design?.reverse_legend,
    reverse_description: coin.design?.reverse_description,
    exergue: coin.design?.exergue,

    // Research Extensions
    issue_status: coin.issue_status,
    obverse_die_id: coin.die_info?.obverse_die_id,
    reverse_die_id: coin.die_info?.reverse_die_id,
    find_spot: coin.find_data?.find_spot,
    find_date: coin.find_data?.find_date || null,

    // Mint details
    mint_name: coin.mint_name,
    mintmark: coin.mintmark,
    officina: coin.officina,

    // Die study
    die_state: coin.die_state,
    die_match_notes: coin.die_match_notes,

    // Condition and rarity
    rarity: coin.rarity,
    rarity_notes: coin.rarity_notes,
    toning_description: coin.toning_description,
    surface_issues: coin.surface_issues,
    cleaning_history: coin.cleaning_history,
    conservation_notes: coin.conservation_notes,

    // Market
    market_value: coin.market_value,
    market_value_date: coin.market_value_date,

    // Images
    images: (coin.images || []).map(img => ({
      url: img.url,
      image_type: img.image_type || 'other',
      is_primary: img.is_primary || false
    })),

    // Collection management
    storage_location: coin.storage_location,
    personal_notes: coin.personal_notes,

    // References (if passed)
    references: coin.references?.map(ref => ({
      catalog: ref?.catalog,
      number: ref?.number,
      volume: ref?.volume,
      is_primary: ref?.is_primary,
      plate_coin: ref?.plate_coin,
      notes: ref?.notes,
    })),
  }
}