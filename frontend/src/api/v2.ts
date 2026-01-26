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
  hammer_price: z.number().nullable().optional(),
  issuer: z.string().nullable().optional(),
  grade: z.string().nullable().optional()
})

export type Discrepancy = z.infer<typeof DiscrepancySchema>
export type AuditResult = z.infer<typeof AuditResultSchema>
export type ScrapeResult = z.infer<typeof ScrapeResultSchema>

export const v2 = {
  getCoins: async (params?: Record<string, any>): Promise<PaginatedCoinsResponse> => {
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

  // Series
  getSeries: async (): Promise<SeriesListResponse> => {
    const response = await api.get('/api/series')
    return SeriesListSchema.parse(response.data)
  },

  getSeriesDetail: async (id: number): Promise<z.infer<typeof SeriesSchema>> => {
    const response = await api.get(`/api/series/${id}`)
    return SeriesSchema.parse(response.data)
  },

  createSeries: async (data: z.infer<typeof SeriesCreateSchema>): Promise<z.infer<typeof SeriesSchema>> => {
    const validatedData = SeriesCreateSchema.parse(data)
    const response = await api.post('/api/series', validatedData)
    return SeriesSchema.parse(response.data)
  },

  addCoinToSeries: async (seriesId: number, coinId: number, slotId?: number): Promise<z.infer<typeof AddCoinToSeriesResponseSchema>> => {
    const response = await api.post(`/api/series/${seriesId}/coins/${coinId}`, null, {
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
  }
}

// Helper to map nested domain object to flat/structured API request
function mapCoinToPayload(coin: Omit<Coin, 'id'>) {
  return {
    category: coin.category,
    metal: coin.metal,
    weight_g: coin.dimensions.weight_g,
    diameter_mm: coin.dimensions.diameter_mm,
    die_axis: coin.dimensions.die_axis,
    issuer: coin.attribution.issuer,
    issuer_id: coin.attribution.issuer_id,
    mint: coin.attribution.mint,
    mint_id: coin.attribution.mint_id,
    year_start: coin.attribution.year_start,
    year_end: coin.attribution.year_end,
    grading_state: coin.grading.grading_state,
    grade: coin.grading.grade,
    grade_service: coin.grading.service,
    certification: coin.grading.certification_number,
    strike: coin.grading.strike,
    surface: coin.grading.surface,
    acquisition_price: coin.acquisition?.price,
    acquisition_source: coin.acquisition?.source,
    acquisition_date: coin.acquisition?.date,
    acquisition_url: coin.acquisition?.url
  }
}