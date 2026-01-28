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
  | "rarity"
  | "id"
  | "mint"
  | "diameter"
  | "die_axis"
  | "specific_gravity"
  | "issue_status"
  | "reign_start"
  | "reference"
  | "storage_location"
  | "obverse_legend"
  | "reverse_legend"
  | "obverse_description"
  | "reverse_description";

export type SortDirection = "asc" | "desc";

export type PerPageOption = 20 | 50 | 100 | "all";

interface FilterState {
  // Quick search (header/palette). Mapped to issuer in toParams (Option B).
  search: string | null;
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

  // Pagination
  page: number;
  perPage: PerPageOption;

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
  /** Type-safe filter setter - accepts only valid filter keys and appropriate value types */
  setFilter: <K extends keyof FilterStateValues>(key: K, value: FilterStateValues[K]) => void;
  setSearch: (v: string | null) => void;
  setPage: (page: number) => void;
  setPerPage: (perPage: PerPageOption) => void;
  nextPage: () => void;
  prevPage: () => void;
  reset: () => void;
  toParams: () => CoinQueryParams;
  getActiveFilterCount: () => number;
}

/** Filter state values (excluding action methods) for type-safe setFilter */
type FilterStateValues = Omit<FilterState,
  | 'setCategory' | 'setSubCategory' | 'setMetal' | 'setIssuingAuthority'
  | 'setIsRulerUnknown' | 'setMintName' | 'setIsMintUnknown' | 'setDenomination'
  | 'setGrade' | 'setRarity' | 'setPriceRange' | 'setMintYearGte' | 'setMintYearLte'
  | 'setIsYearUnknown' | 'setIsCirca' | 'setIsTestCut' | 'setStorageLocation'
  | 'setSort' | 'toggleSortDir' | 'setFilter' | 'setSearch' | 'setPage' | 'setPerPage'
  | 'nextPage' | 'prevPage' | 'reset' | 'toParams' | 'getActiveFilterCount'
>;

/** Typed query params returned by toParams() */
export interface CoinQueryParams {
  sort_by: SortField;
  sort_dir: SortDirection;
  page: number;
  per_page: number;
  category?: string;
  sub_category?: string;
  metal?: string;
  issuing_authority?: string;
  issuer?: string;
  is_ruler_unknown?: boolean;
  mint_name?: string;
  is_mint_unknown?: boolean;
  denomination?: string;
  grade?: string;
  rarity?: string;
  storage_location?: string;
  acquisition_price_gte?: number;
  acquisition_price_lte?: number;
  mint_year_gte?: number;
  mint_year_lte?: number;
  is_year_unknown?: boolean;
  is_circa?: boolean;
  is_test_cut?: boolean;
}

const initialState = {
  search: null as string | null,
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
  sortBy: "created" as SortField,
  sortDir: "desc" as SortDirection,
  page: 1,
  perPage: 20 as PerPageOption,
};

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setCategory: (category) => set({ category, page: 1 }),
      setSubCategory: (sub_category) => set({ sub_category, page: 1 }),
      setMetal: (metal) => set({ metal, page: 1 }),
      setIssuingAuthority: (issuing_authority) => set({ issuing_authority, page: 1 }),
      setIsRulerUnknown: (is_ruler_unknown) => set({ is_ruler_unknown, page: 1 }),
      setMintName: (mint_name) => set({ mint_name, page: 1 }),
      setIsMintUnknown: (is_mint_unknown) => set({ is_mint_unknown, page: 1 }),
      setDenomination: (denomination) => set({ denomination, page: 1 }),
      setGrade: (grade) => set({ grade, page: 1 }),
      setRarity: (rarity) => set({ rarity, page: 1 }),
      setPriceRange: (priceRange) => set({ priceRange, page: 1 }),
      setMintYearGte: (mint_year_gte) => set({ mint_year_gte, page: 1 }),
      setMintYearLte: (mint_year_lte) => set({ mint_year_lte, page: 1 }),
      setIsYearUnknown: (is_year_unknown) => set({ is_year_unknown, page: 1 }),
      setIsCirca: (is_circa) => set({ is_circa, page: 1 }),
      setIsTestCut: (is_test_cut) => set({ is_test_cut, page: 1 }),
      setStorageLocation: (storage_location) => set({ storage_location, page: 1 }),

      setSort: (field, dir) => set({
        sortBy: field,
        sortDir: dir ?? (field === get().sortBy ? get().sortDir : "asc"),
        page: 1, // Reset to first page on sort change
      }),
      toggleSortDir: () => set({ sortDir: get().sortDir === "asc" ? "desc" : "asc", page: 1 }),

      setFilter: (key, value) => set({ [key]: value, page: 1 }), // Reset page on filter change

      setSearch: (search) => set({ search, page: 1 }),

      setPage: (page) => set({ page }),
      setPerPage: (perPage) => set({ perPage, page: 1 }), // Reset to first page when changing per_page
      nextPage: () => set((state) => ({ page: state.page + 1 })),
      prevPage: () => set((state) => ({ page: Math.max(1, state.page - 1) })),

      reset: () => set(initialState),

      getActiveFilterCount: () => {
        const state = get();
        let count = 0;
        if (state.search?.trim()) count++;
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

      toParams: (): CoinQueryParams => {
        const state = get();
        const params: CoinQueryParams = {
          sort_by: state.sortBy,
          sort_dir: state.sortDir,
          page: state.page,
          per_page: state.perPage === "all" ? 1000 : state.perPage, // Use large number for "all"
        };

        // String filters
        if (state.category) {
          let cat = state.category;
          // Map simple frontend keys to typical backend values
          if (cat === 'imperial') cat = 'roman_imperial';
          if (cat === 'provincial') cat = 'roman_provincial';
          if (cat === 'republic') cat = 'roman_republic';
          params.category = cat;
        }
        if (state.sub_category) params.sub_category = state.sub_category;
        if (state.metal) params.metal = state.metal;

        // Search (header/palette) maps to issuer (Option B). When set, it drives issuer.
        if (state.search?.trim()) {
          params.issuer = state.search.trim();
          params.issuing_authority = state.search.trim();
        } else if (state.issuing_authority) {
          params.issuing_authority = state.issuing_authority;
          params.issuer = state.issuing_authority;
        }

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
