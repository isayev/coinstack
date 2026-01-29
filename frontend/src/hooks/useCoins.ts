import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { client, type PaginatedCoinsResponse } from "@/api/client";
import { Coin } from "@/domain/schemas";
import { useFilterStore } from "@/stores/filterStore";
import { getGradeTier } from "@/utils/gradeUtils";

export interface YearBucket {
  start: number;
  end: number;
  count: number;
  label: string;
}

export interface RulerStat {
  ruler: string;
  count: number;
}

export interface CollectionStats {
  total_coins: number;
  total_value: number;
  average_price: number;
  median_price: number;
  highest_value_coin: number;
  lowest_value_coin: number;
  metal_counts: Record<string, number>;
  category_counts: Record<string, number>;
  grade_counts: Record<string, number>; // Keys are GradeTiers (fine, ef, etc)
  rarity_counts: Record<string, number>;
  ruler_counts: Record<string, number>; // For unknown calc
  top_rulers: RulerStat[]; // Top rulers list
  year_range: { min: number | null; max: number | null; unknown_count: number };
  year_distribution: YearBucket[];
  unknown_counts: { grade: number; year: number; ruler: number; mint: number; denomination: number; rarity: number };
}

export function useCoins() {
  return useQuery<PaginatedCoinsResponse>({
    queryKey: ["coins"],
    queryFn: () => client.getCoins(),
  });
}

export function useCoin(id: number) {
  return useQuery({
    queryKey: ["coin", id],
    queryFn: () => client.getCoin(id),
    enabled: !!id,
  });
}

export function useCreateCoin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: client.createCoin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
    onError: (error: Error) => {
      // Error handling - consumers should use toast or other UI notification
      if (import.meta.env.DEV) {
        console.error('Create coin failed:', error.message);
      }
    },
  });
}

export function useUpdateCoin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Omit<Coin, 'id'> }) => client.updateCoin(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
      queryClient.invalidateQueries({ queryKey: ["coin", id] });
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Update coin failed:', error.message);
      }
    },
  });
}

export function useDeleteCoin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: client.deleteCoin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Delete coin failed:', error.message);
      }
    },
  });
}

function mapCategoryToKey(cat: string): string {
  const c = cat.toLowerCase();
  if (c.includes('provincial')) return 'provincial';
  if (c.includes('imperial')) return 'imperial';
  if (c.includes('republic')) return 'republic';
  if (c.includes('greek')) return 'greek';
  if (c.includes('byzantine')) return 'byzantine';
  if (c.includes('judaea') || c.includes('judea')) return 'judaea';
  if (c.includes('celtic')) return 'celtic';
  if (c.includes('eastern')) return 'eastern';
  return c;
}

/**
 * Collection statistics hook
 * Fetches real aggregated stats from the backend
 */
export function useCollectionStats() {
  const { toParams } = useFilterStore();
  // Get reactive params
  const params = toParams();

  return useQuery({
    queryKey: ["collection-stats", params],
    queryFn: async () => {
      const data = await client.getStatsSummary(params);

      const metal_counts = data.by_metal.reduce((acc, curr) => ({ ...acc, [curr.metal.toLowerCase()]: curr.count }), {});

      const category_counts: Record<string, number> = {};
      data.by_category.forEach(c => {
        const key = mapCategoryToKey(c.category);
        category_counts[key] = (category_counts[key] || 0) + c.count;
      });

      // Aggregate Grades into Tiers (shared tier logic from gradeUtils)
      const grade_counts: Record<string, number> = {};
      data.by_grade.forEach(g => {
        const tier = getGradeTier(g.grade);
        grade_counts[tier] = (grade_counts[tier] || 0) + g.count;
      });

      // Rarity: backend returns canonical lowercase (c, s, r1, r2, r3, u); normalize key for legacy/uppercase
      const rarityKey = (r: string) => (r ?? '').toLowerCase().trim();
      const rarity_counts = (data.by_rarity || []).reduce(
        (acc, curr) => {
          const key = rarityKey(curr.rarity);
          if (key) acc[key] = (acc[key] ?? 0) + curr.count;
          return acc;
        },
        {} as Record<string, number>
      );

      const top_rulers = data.by_ruler.map(r => ({ ruler: r.ruler, count: r.count }));

      const years = data.by_year.map(y => y.year);
      const minYear = years.length ? Math.min(...years) : null;
      const maxYear = years.length ? Math.max(...years) : null;

      const year_distribution = data.by_year.map(y => ({
        start: y.year,
        end: y.year,
        count: y.count,
        label: y.year < 0 ? `${Math.abs(y.year)} BC` : `${y.year}`
      }));

      // Calculate unknown counts
      const total = data.total_coins;
      const knownYearCount = data.by_year.reduce((sum, y) => sum + y.count, 0);
      const gradedSum = data.by_grade.reduce((sum, g) => sum + g.count, 0);

      const knownRulerCount = data.health.with_attribution;
      const knownRarityCount = (data.by_rarity || []).reduce((sum, r) => sum + r.count, 0);

      const unknown_counts = {
        grade: Math.max(0, total - gradedSum),
        year: Math.max(0, total - knownYearCount),
        ruler: Math.max(0, total - knownRulerCount),
        mint: 0,
        denomination: 0,
        rarity: Math.max(0, total - knownRarityCount),
      };

      return {
        total_coins: data.total_coins,
        total_value: data.total_value_usd || 0,
        average_price: 0,
        median_price: 0,
        highest_value_coin: 0,
        lowest_value_coin: 0,
        metal_counts,
        category_counts,
        grade_counts,
        rarity_counts,
        ruler_counts: {}, // Not really used if we have top_rulers
        top_rulers,
        year_range: { min: minYear, max: maxYear, unknown_count: unknown_counts.year },
        year_distribution,
        unknown_counts,
      };
    },
    // Keep data fresh but allow some caching (e.g. 1 minute)
    staleTime: 60 * 1000,
  });
}