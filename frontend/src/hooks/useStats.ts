import { useQuery } from "@tanstack/react-query";


export interface StatItem {
  name: string;
  count: number;
  total_weight?: number;
  total_value: number; // Added to match Recharts expectations in StatsPage
}

export interface MetalStat extends StatItem {
  metal: string;
}

export interface CategoryStat extends StatItem {
  category: string;
}

export interface StorageStat {
  location: string;
  count: number;
}

export interface RulerStat {
  ruler: string;
  count: number;
  total_value: number;
}

export interface PriceDistribution {
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
  by_metal: MetalStat[];
  by_category: CategoryStat[];
  by_storage: StorageStat[];
  top_rulers: RulerStat[];
  price_distribution: PriceDistribution[];
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: async () => {
      const mockStats: CollectionStats = {
        total_coins: 110,
        total_value: 15420,
        average_price: 140,
        median_price: 85,
        highest_value_coin: 2160,
        lowest_value_coin: 15,
        by_metal: [
          { name: "Silver", metal: "silver", count: 45, total_weight: 150.5, total_value: 6000 },
          { name: "Bronze", metal: "bronze", count: 30, total_weight: 320.2, total_value: 1500 },
          { name: "Gold", metal: "gold", count: 2, total_weight: 16.8, total_value: 4500 },
          { name: "Billon", metal: "billon", count: 33, total_weight: 110.0, total_value: 3420 },
        ],
        by_category: [
          { name: "Roman Imperial", category: "roman_imperial", count: 85, total_value: 12000 },
          { name: "Roman Republic", category: "roman_republic", count: 10, total_value: 2000 },
          { name: "Greek", category: "greek", count: 15, total_value: 1420 },
        ],
        by_storage: [
          { location: "Velv1", count: 40 },
          { location: "Velv2", count: 40 },
          { location: "SlabBox1", count: 10 },
        ],
        top_rulers: [
          { ruler: "Augustus", count: 12, total_value: 5000 },
          { ruler: "Trajan", count: 8, total_value: 2000 },
          { ruler: "Hadrian", count: 7, total_value: 1500 },
          { ruler: "Constantine I", count: 6, total_value: 800 },
          { ruler: "Gallienus", count: 15, total_value: 1200 },
        ],
        price_distribution: [
          { range: "0-50", count: 30 },
          { range: "50-100", count: 40 },
          { range: "100-200", count: 25 },
          { range: "200-500", count: 10 },
          { range: "500+", count: 5 },
        ],
      };
      return mockStats;
    },
    staleTime: 5 * 60 * 1000,
  });
}
