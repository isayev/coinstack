import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { CoinDetail, CoinCreate, CoinUpdate, PaginatedCoins } from "@/types/coin";
import { useFilterStore } from "@/stores/filterStore";

export interface CollectionStats {
  total_coins: number;
  total_value: number;
  average_price: number;
  median_price: number;
  highest_value_coin: number;
  lowest_value_coin: number;
  metal_counts: Record<string, number>;
  category_counts: Record<string, number>;
  grade_counts: Record<string, number>;
  rarity_counts: Record<string, number>;
  year_range: {
    min: number | null;
    max: number | null;
  };
}

export interface CoinNavigation {
  prev_id: number | null;
  next_id: number | null;
  current_index: number | null;
  total: number;
}

export function useCoins() {
  const filters = useFilterStore();
  
  return useQuery({
    queryKey: ["coins", filters.toParams()],
    queryFn: async () => {
      const params = filters.toParams();
      const response = await api.get<PaginatedCoins>("/api/coins", { params });
      return response.data;
    },
  });
}

export function useCoin(id: number) {
  return useQuery({
    queryKey: ["coin", id],
    queryFn: async () => {
      const response = await api.get<CoinDetail>(`/api/coins/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCoinNavigation(id: number) {
  const filters = useFilterStore();
  
  return useQuery({
    queryKey: ["coin-navigation", id, filters.toParams()],
    queryFn: async () => {
      const params = filters.toParams();
      const response = await api.get<CoinNavigation>(`/api/coins/${id}/navigation`, { params });
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: CoinCreate) => {
      const response = await api.post<CoinDetail>("/api/coins", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useUpdateCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: CoinUpdate }) => {
      const response = await api.put<CoinDetail>(`/api/coins/${id}`, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
      queryClient.invalidateQueries({ queryKey: ["coin", id] });
    },
  });
}

export function useDeleteCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/coins/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useCollectionStats() {
  return useQuery({
    queryKey: ["collection-stats"],
    queryFn: async () => {
      const response = await api.get<CollectionStats>("/api/stats");
      return response.data;
    },
    staleTime: 30000, // Cache for 30 seconds
  });
}
