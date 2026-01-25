import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { v2 } from "@/api/v2";
import { Coin } from "@/domain/schemas";

export interface YearBucket {
  start: number;
  end: number;
  count: number;
  label: string;
}

export interface CollectionStats {
  total_coins: number;
  total_value: number;
  average_price: number;
  median_price: number;
  highest_value_coin: number;
  lowest_value_coin: number;
}

export function useCoins() {
  return useQuery({
    queryKey: ["coins"],
    queryFn: v2.getCoins,
  });
}

export function useCoin(id: number) {
  return useQuery({
    queryKey: ["coin", id],
    queryFn: () => v2.getCoin(id),
    enabled: !!id,
  });
}

export function useCreateCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: v2.createCoin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useUpdateCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Omit<Coin, 'id'> }) => v2.updateCoin(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
      queryClient.invalidateQueries({ queryKey: ["coin", id] });
    },
  });
}

export function useDeleteCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: v2.deleteCoin,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useCollectionStats() {
  return useQuery({
    queryKey: ["collection-stats"],
    queryFn: async () => {
      // Return minimal stats for sidebar to prevent crash
      return {
        total_coins: 0,
        total_value: 0,
        average_price: 0,
        median_price: 0,
        highest_value_coin: 0,
        lowest_value_coin: 0,
        metal_counts: {},
        category_counts: {},
        grade_counts: {},
        rarity_counts: {},
        year_range: { min: null, max: null, unknown_count: 0 },
        year_distribution: [],
        unknown_counts: { grade: 0, year: 0, ruler: 0, mint: 0, denomination: 0, rarity: 0 }
      };
    },
  });
}