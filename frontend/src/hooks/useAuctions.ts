import { useQuery } from "@tanstack/react-query";
import api from "@/api/api"; // Using base api for custom endpoints
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

interface AuctionResponse {
  items: AuctionListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export function useAuctions(
  filters: AuctionFilters, 
  page: number, 
  perPage: number, 
  sortBy: string, 
  sortOrder: "asc" | "desc"
) {
  return useQuery({
    queryKey: ["auctions", filters, page, perPage, sortBy, sortOrder],
    queryFn: async () => {
      // For now, mock the response until backend endpoint exists
      // return { items: [], total: 0, page: 1, per_page: 20, pages: 1 };
      
      // Real implementation would be:
      const params = {
        ...filters,
        page,
        per_page: perPage,
        sort_by: sortBy,
        sort_dir: sortOrder
      };
      // Endpoint to be created in backend
      const response = await api.get<AuctionResponse>("/api/v2/auctions", { params });
      return response.data; 
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