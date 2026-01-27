import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
// import api from "@/api/api"; // Using base api for custom endpoints
import { z } from "zod";

// Schema for Auction Data
export const AuctionSchema = z.object({
  id: z.number(),
  coin_id: z.number().nullable(),
  auction_house: z.string(),
  sale_name: z.string().nullable(),
  lot_number: z.string().nullable(),
  auction_date: z.string().nullable(),
  hammer_price: z.number().nullable(),
  estimate_low: z.number().nullable(),
  estimate_high: z.number().nullable(),
  currency: z.string(),
  url: z.string(),
  thumbnail: z.string().nullable().optional(), // For grid view
});

export type AuctionListItem = z.infer<typeof AuctionSchema>;

export interface AuctionFilters {
  auction_house?: string;
  sold?: string; // "true" | "false"
  search?: string;
}

// interface AuctionResponse {
//   items: AuctionListItem[];
//   total: number;
//   page: number;
//   per_page: number;
//   pages: number;
// }

export function useAuctions(
  filters: AuctionFilters,
  perPage: number,
  sortBy: string,
  sortOrder: "asc" | "desc"
) {
  return useInfiniteQuery({
    queryKey: ["auctions", filters, sortBy, sortOrder],
    queryFn: async ({ pageParam = 1 }) => {
      // Mock until backend endpoint exists
      return {
        items: [
          {
            id: 1,
            coin_id: null,
            auction_house: "Heritage Auctions",
            sale_name: "Signature Sale 3096",
            lot_number: "30045",
            auction_date: "2024-01-15",
            hammer_price: 1250,
            estimate_low: 1000,
            estimate_high: 1500,
            currency: "USD",
            url: "https://example.com/lot/1",
            thumbnail: null
          },
          {
            id: 2,
            coin_id: null,
            auction_house: "CNG",
            sale_name: "Electronic Auction 555",
            lot_number: "452",
            auction_date: "2024-02-01",
            hammer_price: 850,
            estimate_low: 600,
            estimate_high: 900,
            currency: "USD",
            url: "https://example.com/lot/2",
            thumbnail: null
          }
        ],
        total: 2,
        page: pageParam as number,
        per_page: perPage,
        pages: 1
      };

      /*
      const params = {
        ...filters,
        page: pageParam,
        per_page: perPage,
        sort_by: sortBy,
        sort_dir: sortOrder
      };
      
      // Endpoint to be created in backend
      const response = await api.get<AuctionResponse>("/api/v2/auctions", { params });
      return response.data; 
      */
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.page < lastPage.pages) {
        return lastPage.page + 1;
      }
      return undefined;
    },
    // Keep data fresh for 5 minutes
    staleTime: 5 * 60 * 1000,
  });
}

export function useAuctionHouses() {
  return useQuery({
    queryKey: ["auction-houses"],
    queryFn: async () => {
      // Mock for now
      return ["Heritage", "CNG", "Leu", "Roma", "Naville"];

      // Real: await api.get<string[]>("/api/v2/auctions/houses")
    }
  });
}