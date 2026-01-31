/**
 * Market tracking hooks for Phase 5.
 *
 * Provides TanStack Query hooks for:
 * - Market prices (type-level pricing aggregates)
 * - Market data points (individual price observations)
 * - Coin valuations (per-coin portfolio valuations)
 * - Portfolio summary
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  MarketPrice,
  MarketDataPoint,
  CoinValuation
} from "@/domain/schemas";

// =============================================================================
// API Types
// =============================================================================

interface MarketPriceFilters {
  issuer?: string;
  denomination?: string;
  metal?: string;
  skip?: number;
  limit?: number;
}

interface MarketPriceListResponse {
  prices: MarketPrice[];
  total: number;
  skip: number;
  limit: number;
}

interface MarketDataPointListResponse {
  data_points: MarketDataPoint[];
  total: number;
}

interface CoinValuationListResponse {
  coin_id: number;
  valuations: CoinValuation[];
  total: number;
}

interface PortfolioSummary {
  total_coins: number;
  total_purchase_value: number;
  total_current_value: number;
  total_gain_loss_usd: number;
  total_gain_loss_pct: number | null;
}

type MarketPriceCreate = Omit<MarketPrice, 'id' | 'last_updated'>;
type MarketPriceUpdate = Partial<MarketPriceCreate>;
type MarketDataPointCreate = Omit<MarketDataPoint, 'id' | 'created_at'>;
type MarketDataPointUpdate = Partial<MarketDataPointCreate>;
type CoinValuationCreate = Omit<CoinValuation, 'id' | 'coin_id' | 'created_at'>;
type CoinValuationUpdate = Partial<CoinValuationCreate>;

// =============================================================================
// API Client Functions
// =============================================================================

const API_BASE = "/api/v2";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// =============================================================================
// Market Price Hooks
// =============================================================================

export function useMarketPrices(filters: MarketPriceFilters = {}) {
  const { issuer, denomination, metal, skip = 0, limit = 100 } = filters;

  const params = new URLSearchParams();
  if (issuer) params.set("issuer", issuer);
  if (denomination) params.set("denomination", denomination);
  if (metal) params.set("metal", metal);
  params.set("skip", String(skip));
  params.set("limit", String(limit));

  return useQuery<MarketPriceListResponse>({
    queryKey: ["market-prices", filters],
    queryFn: () => fetchJson(`${API_BASE}/market/prices?${params}`),
  });
}

export function useMarketPrice(priceId: number) {
  return useQuery<MarketPrice>({
    queryKey: ["market-price", priceId],
    queryFn: () => fetchJson(`${API_BASE}/market/prices/${priceId}`),
    enabled: !!priceId,
  });
}

export function useMarketPriceByAttribution(attributionKey: string) {
  return useQuery<MarketPrice | null>({
    queryKey: ["market-price-attribution", attributionKey],
    queryFn: () => fetchJson(`${API_BASE}/market/prices/by-attribution?attribution_key=${encodeURIComponent(attributionKey)}`),
    enabled: !!attributionKey,
  });
}

export function useCreateMarketPrice() {
  const queryClient = useQueryClient();

  return useMutation<MarketPrice, Error, MarketPriceCreate>({
    mutationFn: (data) => fetchJson(`${API_BASE}/market/prices`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["market-prices"] });
    },
  });
}

export function useUpdateMarketPrice() {
  const queryClient = useQueryClient();

  return useMutation<MarketPrice, Error, { id: number; data: MarketPriceUpdate }>({
    mutationFn: ({ id, data }) => fetchJson(`${API_BASE}/market/prices/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["market-prices"] });
      queryClient.invalidateQueries({ queryKey: ["market-price", id] });
    },
  });
}

export function useDeleteMarketPrice() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: (id) => fetchJson(`${API_BASE}/market/prices/${id}`, {
      method: "DELETE",
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["market-prices"] });
    },
  });
}

// =============================================================================
// Market Data Point Hooks
// =============================================================================

export function useMarketDataPoints(priceId: number, sourceType?: string) {
  const params = new URLSearchParams();
  if (sourceType) params.set("source_type", sourceType);

  return useQuery<MarketDataPointListResponse>({
    queryKey: ["market-data-points", priceId, sourceType],
    queryFn: () => fetchJson(`${API_BASE}/market/prices/${priceId}/data-points?${params}`),
    enabled: !!priceId,
  });
}

export function useMarketDataPoint(dataPointId: number) {
  return useQuery<MarketDataPoint>({
    queryKey: ["market-data-point", dataPointId],
    queryFn: () => fetchJson(`${API_BASE}/market/data-points/${dataPointId}`),
    enabled: !!dataPointId,
  });
}

export function useCreateMarketDataPoint() {
  const queryClient = useQueryClient();

  return useMutation<MarketDataPoint, Error, { priceId: number; data: MarketDataPointCreate }>({
    mutationFn: ({ priceId, data }) => fetchJson(`${API_BASE}/market/prices/${priceId}/data-points`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
    onSuccess: (_, { priceId }) => {
      queryClient.invalidateQueries({ queryKey: ["market-data-points", priceId] });
      queryClient.invalidateQueries({ queryKey: ["market-price", priceId] });
    },
  });
}

export function useUpdateMarketDataPoint() {
  const queryClient = useQueryClient();

  return useMutation<MarketDataPoint, Error, { id: number; data: MarketDataPointUpdate }>({
    mutationFn: ({ id, data }) => fetchJson(`${API_BASE}/market/data-points/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["market-data-points", result.market_price_id] });
      queryClient.invalidateQueries({ queryKey: ["market-data-point", result.id] });
    },
  });
}

export function useDeleteMarketDataPoint() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { id: number; priceId: number }>({
    mutationFn: ({ id }) => fetchJson(`${API_BASE}/market/data-points/${id}`, {
      method: "DELETE",
    }),
    onSuccess: (_, { priceId }) => {
      queryClient.invalidateQueries({ queryKey: ["market-data-points", priceId] });
    },
  });
}

// =============================================================================
// Coin Valuation Hooks
// =============================================================================

export function useCoinValuations(coinId: number) {
  return useQuery<CoinValuationListResponse>({
    queryKey: ["coin-valuations", coinId],
    queryFn: () => fetchJson(`${API_BASE}/coins/${coinId}/valuations`),
    enabled: !!coinId,
  });
}

export function useLatestValuation(coinId: number) {
  return useQuery<CoinValuation | null>({
    queryKey: ["coin-valuation-latest", coinId],
    queryFn: () => fetchJson(`${API_BASE}/coins/${coinId}/valuations/latest`),
    enabled: !!coinId,
  });
}

export function useCoinValuation(coinId: number, valuationId: number) {
  return useQuery<CoinValuation>({
    queryKey: ["coin-valuation", coinId, valuationId],
    queryFn: () => fetchJson(`${API_BASE}/coins/${coinId}/valuations/${valuationId}`),
    enabled: !!coinId && !!valuationId,
  });
}

export function useCreateValuation() {
  const queryClient = useQueryClient();

  return useMutation<CoinValuation, Error, { coinId: number; data: CoinValuationCreate }>({
    mutationFn: ({ coinId, data }) => fetchJson(`${API_BASE}/coins/${coinId}/valuations`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
    onSuccess: (_, { coinId }) => {
      queryClient.invalidateQueries({ queryKey: ["coin-valuations", coinId] });
      queryClient.invalidateQueries({ queryKey: ["coin-valuation-latest", coinId] });
      queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] });
    },
  });
}

export function useUpdateValuation() {
  const queryClient = useQueryClient();

  return useMutation<CoinValuation, Error, { coinId: number; valuationId: number; data: CoinValuationUpdate }>({
    mutationFn: ({ coinId, valuationId, data }) => fetchJson(`${API_BASE}/coins/${coinId}/valuations/${valuationId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
    onSuccess: (_, { coinId, valuationId }) => {
      queryClient.invalidateQueries({ queryKey: ["coin-valuations", coinId] });
      queryClient.invalidateQueries({ queryKey: ["coin-valuation", coinId, valuationId] });
      queryClient.invalidateQueries({ queryKey: ["coin-valuation-latest", coinId] });
      queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] });
    },
  });
}

export function useDeleteValuation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { coinId: number; valuationId: number }>({
    mutationFn: ({ coinId, valuationId }) => fetchJson(`${API_BASE}/coins/${coinId}/valuations/${valuationId}`, {
      method: "DELETE",
    }),
    onSuccess: (_, { coinId }) => {
      queryClient.invalidateQueries({ queryKey: ["coin-valuations", coinId] });
      queryClient.invalidateQueries({ queryKey: ["coin-valuation-latest", coinId] });
      queryClient.invalidateQueries({ queryKey: ["portfolio-summary"] });
    },
  });
}

// =============================================================================
// Portfolio Summary Hook
// =============================================================================

export function usePortfolioSummary() {
  return useQuery<PortfolioSummary>({
    queryKey: ["portfolio-summary"],
    queryFn: () => fetchJson(`${API_BASE}/valuations/portfolio-summary`),
  });
}
