import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { CoinDetail, CoinCreate, CoinUpdate, PaginatedCoins } from "@/types/coin";
import { useFilterStore } from "@/stores/filterStore";

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
