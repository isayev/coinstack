// Coin types
export type Category = "republic" | "imperial" | "provincial" | "byzantine" | "greek" | "other";
export type Metal = "gold" | "silver" | "billon" | "bronze" | "orichalcum" | "copper";

export interface CoinReference {
  id: number;
  system: string;
  volume?: string;
  number: string;
  is_primary: boolean;
  plate_coin: boolean;
}

export interface CoinImage {
  id: number;
  image_type: string;
  file_path: string;
  is_primary: boolean;
}

export interface CoinListItem {
  id: number;
  category: Category;
  denomination: string;
  metal: Metal;
  issuing_authority: string;
  portrait_subject?: string;
  mint_name?: string;
  grade?: string;
  acquisition_price?: string | number;  // Backend returns Decimal as string
  storage_location?: string;
  primary_image?: string;
}

export interface CoinDetail {
  id: number;
  created_at: string;
  updated_at: string;
  category: Category;
  denomination: string;
  metal: Metal;
  series?: string;
  issuing_authority: string;
  portrait_subject?: string;
  status?: string;
  reign_start?: number;
  reign_end?: number;
  mint_year_start?: number;
  mint_year_end?: number;
  weight_g?: number;
  diameter_mm?: number;
  diameter_min_mm?: number;
  thickness_mm?: number;
  die_axis?: number;
  obverse_legend?: string;
  obverse_legend_expanded?: string;
  obverse_description?: string;
  obverse_symbols?: string;
  reverse_legend?: string;
  reverse_legend_expanded?: string;
  reverse_description?: string;
  reverse_symbols?: string;
  exergue?: string;
  mint_id?: number;
  mint_name?: string;
  grade_service?: string;
  grade?: string;
  strike_quality?: number;
  surface_quality?: number;
  certification_number?: string;
  acquisition_date?: string;
  acquisition_price?: number;
  acquisition_currency?: string;
  acquisition_source?: string;
  acquisition_url?: string;
  storage_location?: string;
  for_sale: boolean;
  asking_price?: number;
  rarity?: string;
  rarity_notes?: string;
  historical_significance?: string;
  personal_notes?: string;
  references: CoinReference[];
  images: CoinImage[];
  tags: string[];
}

export interface CoinCreate {
  category: Category;
  denomination: string;
  metal: Metal;
  issuing_authority: string;
  series?: string;
  portrait_subject?: string;
  status?: string;
  reign_start?: number;
  reign_end?: number;
  mint_year_start?: number;
  mint_year_end?: number;
  weight_g?: number;
  diameter_mm?: number;
  diameter_min_mm?: number;
  thickness_mm?: number;
  die_axis?: number;
  obverse_legend?: string;
  obverse_description?: string;
  reverse_legend?: string;
  reverse_description?: string;
  exergue?: string;
  mint_id?: number;
  grade?: string;
  acquisition_date?: string;
  acquisition_price?: number;
  acquisition_currency?: string;
  acquisition_source?: string;
  storage_location?: string;
  references?: Array<{
    system: string;
    volume?: string;
    number: string;
    is_primary?: boolean;
  }>;
  tags?: string[];
}

export interface CoinUpdate {
  category?: Category;
  denomination?: string;
  metal?: Metal;
  issuing_authority?: string;
  series?: string;
  portrait_subject?: string;
  status?: string;
  reign_start?: number;
  reign_end?: number;
  weight_g?: number;
  diameter_mm?: number;
  obverse_legend?: string;
  obverse_description?: string;
  reverse_legend?: string;
  reverse_description?: string;
  grade?: string;
  acquisition_price?: number;
  storage_location?: string;
  personal_notes?: string;
}

export interface PaginatedCoins {
  items: CoinListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}
