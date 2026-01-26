import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ReviewCounts {
  vocabulary: number;
  ai: number;
  images: number;
  discrepancies: number;
  enrichments: number;
  data: number;
  total: number;
}

/**
 * Hook for real-time review counts with 5-second polling.
 * 
 * Updates automatically every 5 seconds to show live badge counts in sidebar.
 * Invalidates on any review action mutation.
 */
export function useReviewCountsRealtime() {
  return useQuery({
    queryKey: ["review", "counts"],
    queryFn: async (): Promise<ReviewCounts> => {
      const response = await api.get("/api/v2/review/counts");
      return response.data;
    },
    refetchInterval: 5000, // 5 seconds for real-time updates
    staleTime: 0, // Always consider stale to ensure fresh data
  });
}
