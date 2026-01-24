import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface CategoryStat {
  category: string;
  count: number;
  total_value: number;
}

export interface MetalStat {
  metal: string;
  count: number;
  total_value: number;
}

export interface RulerStat {
  ruler: string;
  count: number;
  total_value: number;
}

export interface StorageStat {
  location: string;
  count: number;
}

export interface PriceRangeStat {
  range: string;
  count: number;
}

export interface CollectionStats {
  total_coins: number;
  total_value: number;
  average_price: number;
  median_price: number;
  highest_value_coin: number;
  lowest_value_coin: number;
  by_category: CategoryStat[];
  by_metal: MetalStat[];
  top_rulers: RulerStat[];
  by_storage: StorageStat[];
  price_distribution: PriceRangeStat[];
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: async () => {
      const response = await api.get<CollectionStats>("/api/stats");
      return response.data;
    },
  });
}
