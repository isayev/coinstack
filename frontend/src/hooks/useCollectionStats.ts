/**
 * useCollectionStats - Hook for fetching collection statistics
 * 
 * Fetches data from /api/v2/stats/summary endpoint
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface HealthMetrics {
  overall_pct: number;
  total_coins: number;
  with_images: number;
  with_attribution: number;
  with_references: number;
  with_provenance: number;
  with_values: number;
}

export interface CategoryDistribution {
  category: string;
  count: number;
  color: string;
}

export interface MetalDistribution {
  metal: string;
  symbol: string;
  count: number;
}

export interface GradeDistribution {
  grade: string;
  count: number;
  numeric: number | null;
}

export interface CertificationDistribution {
  service: string;
  count: number;
}

export interface RulerDistribution {
  ruler: string;
  ruler_id: number | null;
  count: number;
  reign_start: number | null;
}

export interface YearDistribution {
  year: number;
  count: number;
}

export interface AcquisitionMonth {
  month: string;
  count: number;
  value_usd: number | null;
}

export interface FilterContext {
  applied_filters: { field: string; value: string }[];
  filtered_count: number;
  filtered_value_usd: number | null;
}

export interface StatsSummary {
  total_coins: number;
  total_value_usd: number | null;
  health: HealthMetrics;
  by_category: CategoryDistribution[];
  by_metal: MetalDistribution[];
  by_grade: GradeDistribution[];
  by_certification: CertificationDistribution[];
  by_ruler: RulerDistribution[];
  by_year: YearDistribution[];
  acquisitions: AcquisitionMonth[];
  filter_context: FilterContext | null;
}

interface UseCollectionStatsOptions {
  category?: string;
  metal?: string;
  grade?: string;
  issuer?: string;
  year_gte?: number;
  year_lte?: number;
  enabled?: boolean;
}

export function useCollectionStats(options: UseCollectionStatsOptions = {}) {
  const { enabled = true, ...filters } = options;
  
  // Build query params
  const params = new URLSearchParams();
  if (filters.category) params.set('category', filters.category);
  if (filters.metal) params.set('metal', filters.metal);
  if (filters.grade) params.set('grade', filters.grade);
  if (filters.issuer) params.set('issuer', filters.issuer);
  if (filters.year_gte) params.set('year_gte', String(filters.year_gte));
  if (filters.year_lte) params.set('year_lte', String(filters.year_lte));
  
  const queryString = params.toString();
  const url = `/api/v2/stats/summary${queryString ? `?${queryString}` : ''}`;

  return useQuery<StatsSummary>({
    queryKey: ['collection-stats', filters],
    queryFn: async () => {
      const response = await api.get(url);
      return response.data;
    },
    enabled,
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}

/**
 * Utility function to format currency
 */
export function formatCurrency(value: number | null | undefined, currency = 'USD'): string {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Utility function to format large numbers
 */
export function formatNumber(value: number): string {
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + 'M';
  }
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + 'K';
  }
  return String(value);
}
