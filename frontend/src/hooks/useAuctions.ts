import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ============================================================================
// Types
// ============================================================================

export interface AuctionData {
  id: number;
  auction_house: string;
  sale_name?: string;
  lot_number?: string;
  auction_date?: string;
  url: string;
  estimate_low?: number;
  estimate_high?: number;
  hammer_price?: number;
  total_price?: number;
  currency?: string;
  sold?: boolean;
  grade?: string;
  grade_service?: string;
  certification_number?: string;
  title?: string;
  description?: string;
  weight_g?: number;
  diameter_mm?: number;
  photos?: string[];
  primary_photo_url?: string;
  coin_id?: number;
  reference_type_id?: number;
  created_at: string;
  updated_at: string;
}

export interface AuctionListItem {
  id: number;
  auction_house: string;
  sale_name?: string;
  lot_number?: string;
  auction_date?: string;
  url: string;
  hammer_price?: number;
  currency?: string;
  sold?: boolean;
  grade?: string;
  title?: string;
  primary_photo_url?: string;
  coin_id?: number;
}

export interface PaginatedAuctions {
  items: AuctionListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface AuctionFilters {
  auction_house?: string;
  coin_id?: number;
  reference_type_id?: number;
  sold?: boolean;
  min_price?: number;
  max_price?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface ScrapeResult {
  status: "success" | "partial" | "not_found" | "error" | "rate_limited";
  url: string;
  house?: string;
  error_message?: string;
  auction_id?: number;
  elapsed_ms?: number;
  title?: string;
  hammer_price?: number;
  sold?: boolean;
}

export interface ScrapeJobStatus {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  total_urls: number;
  completed_urls: number;
  failed_urls: number;
  results: ScrapeResult[];
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface DetectHouseResponse {
  url: string;
  house?: string;
  supported: boolean;
}

// ============================================================================
// Auction Queries
// ============================================================================

export function useAuctions(
  filters: AuctionFilters = {},
  page: number = 1,
  perPage: number = 20,
  sortBy: string = "auction_date",
  sortOrder: string = "desc"
) {
  return useQuery({
    queryKey: ["auctions", filters, page, perPage, sortBy, sortOrder],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      params.set("sort_by", sortBy);
      params.set("sort_order", sortOrder);

      if (filters.auction_house) params.set("auction_house", filters.auction_house);
      if (filters.coin_id) params.set("coin_id", String(filters.coin_id));
      if (filters.reference_type_id) params.set("reference_type_id", String(filters.reference_type_id));
      if (filters.sold !== undefined) params.set("sold", String(filters.sold));
      if (filters.min_price) params.set("min_price", String(filters.min_price));
      if (filters.max_price) params.set("max_price", String(filters.max_price));
      if (filters.date_from) params.set("date_from", filters.date_from);
      if (filters.date_to) params.set("date_to", filters.date_to);
      if (filters.search) params.set("search", filters.search);

      const { data } = await api.get<PaginatedAuctions>(`/auctions?${params.toString()}`);
      return data;
    },
  });
}

export function useAuction(auctionId: number | undefined) {
  return useQuery({
    queryKey: ["auction", auctionId],
    queryFn: async () => {
      const { data } = await api.get<AuctionData>(`/auctions/${auctionId}`);
      return data;
    },
    enabled: !!auctionId,
  });
}

export function useCoinAuctions(coinId: number | undefined) {
  return useQuery({
    queryKey: ["auctions", "coin", coinId],
    queryFn: async () => {
      const { data } = await api.get<AuctionData[]>(`/auctions/coin/${coinId}`);
      return data;
    },
    enabled: !!coinId,
  });
}

export function useComparables(referenceTypeId: number | undefined, limit: number = 50) {
  return useQuery({
    queryKey: ["auctions", "comparables", referenceTypeId, limit],
    queryFn: async () => {
      const { data } = await api.get<AuctionListItem[]>(
        `/auctions/comparables/${referenceTypeId}?limit=${limit}`
      );
      return data;
    },
    enabled: !!referenceTypeId,
  });
}

export function useAuctionHouses() {
  return useQuery({
    queryKey: ["auction-houses"],
    queryFn: async () => {
      const { data } = await api.get<string[]>("/auctions/houses");
      return data;
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

export function usePriceStats(
  referenceTypeId: number | undefined,
  dateFrom?: string,
  dateTo?: string
) {
  return useQuery({
    queryKey: ["auctions", "stats", referenceTypeId, dateFrom, dateTo],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      const queryString = params.toString();
      const { data } = await api.get(
        `/auctions/stats/${referenceTypeId}${queryString ? `?${queryString}` : ""}`
      );
      return data;
    },
    enabled: !!referenceTypeId,
  });
}

// ============================================================================
// Auction Mutations
// ============================================================================

export function useCreateAuction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (auctionData: Partial<AuctionData>) => {
      const { data } = await api.post<AuctionData>("/auctions", auctionData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auctions"] });
    },
  });
}

export function useUpdateAuction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...data }: Partial<AuctionData> & { id: number }) => {
      const { data: result } = await api.put<AuctionData>(`/auctions/${id}`, data);
      return result;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["auctions"] });
      queryClient.invalidateQueries({ queryKey: ["auction", data.id] });
    },
  });
}

export function useDeleteAuction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (auctionId: number) => {
      await api.delete(`/auctions/${auctionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auctions"] });
    },
  });
}

export function useLinkAuctionToCoin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ auctionId, coinId }: { auctionId: number; coinId: number }) => {
      const { data } = await api.post<AuctionData>(`/auctions/${auctionId}/link/${coinId}`);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["auctions"] });
      queryClient.invalidateQueries({ queryKey: ["auction", data.id] });
      if (data.coin_id) {
        queryClient.invalidateQueries({ queryKey: ["coin", data.coin_id] });
      }
    },
  });
}

// ============================================================================
// Scrape Mutations & Queries
// ============================================================================

export function useScrapeUrl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      url,
      coinId,
      referenceTypeId,
    }: {
      url: string;
      coinId?: number;
      referenceTypeId?: number;
    }) => {
      const { data } = await api.post<{ job_id: string; status: string }>("/scrape/url", {
        url,
        coin_id: coinId,
        reference_type_id: referenceTypeId,
      });
      return data;
    },
    onSuccess: () => {
      // Invalidate after scrape completes (via polling)
    },
  });
}

export function useScrapeBatch() {
  return useMutation({
    mutationFn: async ({
      urls,
      coinId,
    }: {
      urls: string[];
      coinId?: number;
    }) => {
      const { data } = await api.post<{ job_id: string; status: string; total_urls: number }>(
        "/scrape/batch",
        {
          urls,
          coin_id: coinId,
        }
      );
      return data;
    },
  });
}

export function useRefreshCoinAuctions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (coinId: number) => {
      const { data } = await api.post<{ job_id: string; status: string; total_urls: number }>(
        `/scrape/coin/${coinId}/refresh`
      );
      return data;
    },
    onSuccess: (_, coinId) => {
      queryClient.invalidateQueries({ queryKey: ["auctions", "coin", coinId] });
    },
  });
}

export function useScrapeJobStatus(jobId: string | undefined) {
  return useQuery({
    queryKey: ["scrape-job", jobId],
    queryFn: async () => {
      const { data } = await api.get<ScrapeJobStatus>(`/scrape/status/${jobId}`);
      return data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Poll every 2 seconds while processing
      const data = query.state.data;
      if (data && (data.status === "pending" || data.status === "processing")) {
        return 2000;
      }
      return false;
    },
  });
}

export function useDetectHouse() {
  return useMutation({
    mutationFn: async (url: string) => {
      const { data } = await api.post<DetectHouseResponse>(`/scrape/detect?url=${encodeURIComponent(url)}`);
      return data;
    },
  });
}

// ============================================================================
// Polling Hook for Scrape Jobs
// ============================================================================

export function useScrapeWithPolling() {
  const queryClient = useQueryClient();
  const scrapeUrl = useScrapeUrl();

  const scrapeAndPoll = async (
    url: string,
    coinId?: number,
    referenceTypeId?: number,
    onComplete?: (result: ScrapeJobStatus) => void
  ) => {
    const job = await scrapeUrl.mutateAsync({ url, coinId, referenceTypeId });
    
    // Poll for completion
    const pollInterval = setInterval(async () => {
      try {
        const { data: status } = await api.get<ScrapeJobStatus>(`/scrape/status/${job.job_id}`);
        
        if (status.status === "completed" || status.status === "failed") {
          clearInterval(pollInterval);
          queryClient.invalidateQueries({ queryKey: ["auctions"] });
          if (coinId) {
            queryClient.invalidateQueries({ queryKey: ["auctions", "coin", coinId] });
            queryClient.invalidateQueries({ queryKey: ["coin", coinId] });
          }
          onComplete?.(status);
        }
      } catch (error) {
        clearInterval(pollInterval);
        console.error("Error polling scrape status:", error);
      }
    }, 2000);

    return job;
  };

  return {
    scrapeAndPoll,
    isPending: scrapeUrl.isPending,
  };
}
