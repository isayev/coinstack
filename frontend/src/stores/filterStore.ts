import { create } from "zustand";
import { persist } from "zustand/middleware";

export type SortField = 
  | "year" 
  | "name" 
  | "denomination" 
  | "metal" 
  | "category" 
  | "grade" 
  | "price" 
  | "acquired" 
  | "created" 
  | "value"
  | "weight"
  | "rarity";

export type SortDirection = "asc" | "desc";

interface FilterState {
  // Basic filters
  category: string | null;
  sub_category: string | null;
  metal: string | null;
  issuing_authority: string | null;
  is_ruler_unknown: boolean | null;
  mint_name: string | null;
  is_mint_unknown: boolean | null;
  denomination: string | null;
  grade: string | null;
  rarity: string | null;
  
  // Price filter
  priceRange: [number, number];
  
  // Year range filters
  mint_year_gte: number | null;
  mint_year_lte: number | null;
  is_year_unknown: boolean | null;
  
  // Boolean filters
  is_circa: boolean | null;
  is_test_cut: boolean | null;
  
  // Other filters
  storage_location: string | null;
  for_sale: boolean | null;
  
  // Sorting
  sortBy: SortField;
  sortDir: SortDirection;
  
  // Actions
  setCategory: (v: string | null) => void;
  setSubCategory: (v: string | null) => void;
  setMetal: (v: string | null) => void;
  setIssuingAuthority: (v: string | null) => void;
  setIsRulerUnknown: (v: boolean | null) => void;
  setMintName: (v: string | null) => void;
  setIsMintUnknown: (v: boolean | null) => void;
  setDenomination: (v: string | null) => void;
  setGrade: (v: string | null) => void;
  setRarity: (v: string | null) => void;
  setPriceRange: (v: [number, number]) => void;
  setMintYearGte: (v: number | null) => void;
  setMintYearLte: (v: number | null) => void;
  setIsYearUnknown: (v: boolean | null) => void;
  setIsCirca: (v: boolean | null) => void;
  setIsTestCut: (v: boolean | null) => void;
  setStorageLocation: (v: string | null) => void;
  setSort: (field: SortField, dir?: SortDirection) => void;
  toggleSortDir: () => void;
  setFilter: (key: string, value: any) => void;
  reset: () => void;
  toParams: () => Record<string, any>;
  getActiveFilterCount: () => number;
}

const initialState = {
  category: null,
  sub_category: null,
  metal: null,
  issuing_authority: null,
  is_ruler_unknown: null,
  mint_name: null,
  is_mint_unknown: null,
  denomination: null,
  grade: null,
  rarity: null,
  priceRange: [0, 5000] as [number, number],
  mint_year_gte: null,
  mint_year_lte: null,
  is_year_unknown: null,
  is_circa: null,
  is_test_cut: null,
  storage_location: null,
  for_sale: null,
  sortBy: "year" as SortField,
  sortDir: "asc" as SortDirection,
};

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setCategory: (category) => set({ category }),
      setSubCategory: (sub_category) => set({ sub_category }),
      setMetal: (metal) => set({ metal }),
      setIssuingAuthority: (issuing_authority) => set({ issuing_authority }),
      setIsRulerUnknown: (is_ruler_unknown) => set({ is_ruler_unknown }),
      setMintName: (mint_name) => set({ mint_name }),
      setIsMintUnknown: (is_mint_unknown) => set({ is_mint_unknown }),
      setDenomination: (denomination) => set({ denomination }),
      setGrade: (grade) => set({ grade }),
      setRarity: (rarity) => set({ rarity }),
      setPriceRange: (priceRange) => set({ priceRange }),
      setMintYearGte: (mint_year_gte) => set({ mint_year_gte }),
      setMintYearLte: (mint_year_lte) => set({ mint_year_lte }),
      setIsYearUnknown: (is_year_unknown) => set({ is_year_unknown }),
      setIsCirca: (is_circa) => set({ is_circa }),
      setIsTestCut: (is_test_cut) => set({ is_test_cut }),
      setStorageLocation: (storage_location) => set({ storage_location }),
      
      setSort: (field, dir) => set({ 
        sortBy: field, 
        sortDir: dir ?? (field === get().sortBy ? get().sortDir : "asc")
      }),
      toggleSortDir: () => set({ sortDir: get().sortDir === "asc" ? "desc" : "asc" }),
      
      setFilter: (key, value) => set({ [key]: value }),
      
      reset: () => set(initialState),
      
      getActiveFilterCount: () => {
        const state = get();
        let count = 0;
        if (state.category) count++;
        if (state.sub_category) count++;
        if (state.metal) count++;
        if (state.issuing_authority) count++;
        if (state.is_ruler_unknown !== null) count++;
        if (state.mint_name) count++;
        if (state.is_mint_unknown !== null) count++;
        if (state.denomination) count++;
        if (state.grade) count++;
        if (state.rarity) count++;
        if (state.storage_location) count++;
        if (state.mint_year_gte !== null) count++;
        if (state.mint_year_lte !== null) count++;
        if (state.is_year_unknown !== null) count++;
        if (state.is_circa !== null) count++;
        if (state.is_test_cut !== null) count++;
        if (state.priceRange[0] > 0 || state.priceRange[1] < 5000) count++;
        return count;
      },
      
      toParams: () => {
        const state = get();
        const params: Record<string, any> = {
          sort_by: state.sortBy,
          sort_dir: state.sortDir,
        };
        
        // String filters
        if (state.category) params.category = state.category;
        if (state.sub_category) params.sub_category = state.sub_category;
        if (state.metal) params.metal = state.metal;
        if (state.issuing_authority) params.issuing_authority = state.issuing_authority;
        if (state.is_ruler_unknown !== null) params.is_ruler_unknown = state.is_ruler_unknown;
        if (state.mint_name) params.mint_name = state.mint_name;
        if (state.is_mint_unknown !== null) params.is_mint_unknown = state.is_mint_unknown;
        if (state.denomination) params.denomination = state.denomination;
        if (state.grade) params.grade = state.grade;
        if (state.rarity) params.rarity = state.rarity;
        if (state.storage_location) params.storage_location = state.storage_location;
        
        // Price range
        if (state.priceRange[0] > 0) params.acquisition_price_gte = state.priceRange[0];
        if (state.priceRange[1] < 5000) params.acquisition_price_lte = state.priceRange[1];
        
        // Year range
        if (state.mint_year_gte !== null) params.mint_year_gte = state.mint_year_gte;
        if (state.mint_year_lte !== null) params.mint_year_lte = state.mint_year_lte;
        if (state.is_year_unknown !== null) params.is_year_unknown = state.is_year_unknown;
        
        // Boolean filters
        if (state.is_circa !== null) params.is_circa = state.is_circa;
        if (state.is_test_cut !== null) params.is_test_cut = state.is_test_cut;
        
        return params;
      },
    }),
    { name: "coinstack-filters" }
  )
);
