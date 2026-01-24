import { create } from "zustand";
import { persist } from "zustand/middleware";

interface FilterState {
  category: string | null;
  metal: string | null;
  issuing_authority: string | null;
  mint_name: string | null;
  denomination: string | null;
  priceRange: [number, number];
  reign_start_gte: number | null;
  reign_end_lte: number | null;
  grade_service: string | null;
  storage_location: string | null;
  for_sale: boolean | null;
  
  // Actions
  setCategory: (v: string | null) => void;
  setMetal: (v: string | null) => void;
  setIssuingAuthority: (v: string | null) => void;
  setMintName: (v: string | null) => void;
  setPriceRange: (v: [number, number]) => void;
  setReignStart: (v: number | null) => void;
  setReignEnd: (v: number | null) => void;
  setStorageLocation: (v: string | null) => void;
  setFilter: (key: string, value: any) => void;
  reset: () => void;
  toParams: () => Record<string, any>;
}

const initialState = {
  category: null,
  metal: null,
  issuing_authority: null,
  mint_name: null,
  denomination: null,
  priceRange: [0, 5000] as [number, number],
  reign_start_gte: null,
  reign_end_lte: null,
  grade_service: null,
  storage_location: null,
  for_sale: null,
};

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setCategory: (category) => set({ category }),
      setMetal: (metal) => set({ metal }),
      setIssuingAuthority: (issuing_authority) => set({ issuing_authority }),
      setMintName: (mint_name) => set({ mint_name }),
      setPriceRange: (priceRange) => set({ priceRange }),
      setReignStart: (reign_start_gte) => set({ reign_start_gte }),
      setReignEnd: (reign_end_lte) => set({ reign_end_lte }),
      setStorageLocation: (storage_location) => set({ storage_location }),
      
      setFilter: (key, value) => set({ [key]: value }),
      
      reset: () => set(initialState),
      
      toParams: () => {
        const state = get();
        const params: Record<string, any> = {};
        
        Object.entries(state).forEach(([key, value]) => {
          if (typeof value === "function") return;
          if (value === null || value === undefined) return;
          if (key === "priceRange") {
            if (value[0] > 0) params.acquisition_price_gte = value[0];
            if (value[1] < 5000) params.acquisition_price_lte = value[1];
            return;
          }
          params[key] = value;
        });
        
        return params;
      },
    }),
    { name: "coinstack-filters" }
  )
);
