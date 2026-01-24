/**
 * CoinStack Design System - Color Constants
 * 
 * Centralized color configuration for the entire application.
 * All colors are derived from CSS variables defined in index.css
 * 
 * @module design-system/colors
 */

// ============================================================================
// METAL CONFIGURATION
// ============================================================================

export type MetalType = 
  | 'gold' | 'electrum' | 'silver' | 'orichalcum' | 'brass' 
  | 'bronze' | 'copper' | 'ae' | 'billon' | 'potin' | 'lead';

export interface MetalConfig {
  /** Element symbol (e.g., "Au", "Ag") */
  symbol: string;
  /** Full name */
  name: string;
  /** Atomic number if applicable */
  atomic?: number;
  /** Whether this is a precious metal */
  precious: boolean;
  /** CSS variable prefix (e.g., "au" for --metal-au) */
  cssVar: string;
}

export const METAL_CONFIG: Record<MetalType, MetalConfig> = {
  gold:       { symbol: 'Au', name: 'Gold',       atomic: 79, precious: true,  cssVar: 'au' },
  electrum:   { symbol: 'EL', name: 'Electrum',   atomic: undefined, precious: true,  cssVar: 'el' },
  silver:     { symbol: 'Ag', name: 'Silver',     atomic: 47, precious: true,  cssVar: 'ag' },
  orichalcum: { symbol: 'Or', name: 'Orichalcum', atomic: undefined, precious: false, cssVar: 'or' },
  brass:      { symbol: 'Br', name: 'Brass',      atomic: undefined, precious: false, cssVar: 'br' },
  bronze:     { symbol: 'Cu', name: 'Bronze',     atomic: undefined, precious: false, cssVar: 'cu' },
  copper:     { symbol: 'Cu', name: 'Copper',     atomic: 29, precious: false, cssVar: 'copper' },
  ae:         { symbol: 'Æ',  name: 'AE',         atomic: undefined, precious: false, cssVar: 'ae' },
  billon:     { symbol: 'Bi', name: 'Billon',     atomic: undefined, precious: false, cssVar: 'bi' },
  potin:      { symbol: 'Po', name: 'Potin',      atomic: undefined, precious: false, cssVar: 'po' },
  lead:       { symbol: 'Pb', name: 'Lead',       atomic: 82, precious: false, cssVar: 'pb' },
};

// ============================================================================
// RARITY CONFIGURATION
// ============================================================================

export type RarityType = 'c' | 's' | 'r1' | 'r2' | 'r3' | 'u';

export interface RarityConfig {
  /** Code (e.g., "C", "R1") */
  code: string;
  /** Full label */
  label: string;
  /** Gemstone metaphor */
  gem: string;
  /** Display icon */
  icon: string;
}

export const RARITY_CONFIG: Record<RarityType, RarityConfig> = {
  c:  { code: 'C',  label: 'Common',          gem: 'Quartz',   icon: '●' },
  s:  { code: 'S',  label: 'Scarce',          gem: 'Amethyst', icon: '●' },
  r1: { code: 'R1', label: 'Rare',            gem: 'Sapphire', icon: '●' },
  r2: { code: 'R2', label: 'Very Rare',       gem: 'Emerald',  icon: '●' },
  r3: { code: 'R3', label: 'Extremely Rare',  gem: 'Ruby',     icon: '●' },
  u:  { code: 'U',  label: 'Unique',          gem: 'Diamond',  icon: '◆' },
};

/** Parse rarity string to RarityType */
export function parseRarity(rarity: string | null | undefined): RarityType | null {
  if (!rarity) return null;
  const r = rarity.toLowerCase().trim();
  
  if (r === 'u' || r === 'unique') return 'u';
  if (r === 'r3' || r.includes('extremely')) return 'r3';
  if (r === 'r2' || r.includes('very')) return 'r2';
  if (r === 'r1' || r === 'rare' || r === 'r') return 'r1';
  if (r === 's' || r.includes('scarce')) return 's';
  if (r === 'c' || r.includes('common')) return 'c';
  
  return 'c'; // Default
}

// ============================================================================
// GRADE CONFIGURATION
// ============================================================================

export type GradeTier = 'poor' | 'good' | 'fine' | 'ef' | 'au' | 'ms' | 'unknown';

export interface GradeConfig {
  /** Temperature tier */
  tier: GradeTier;
  /** Numeric value (1-10 scale) */
  numeric: number;
  /** Full label */
  label: string;
}

export const GRADE_MAP: Record<string, GradeConfig> = {
  'P':       { tier: 'poor',    numeric: 1,   label: 'Poor' },
  'FR':      { tier: 'poor',    numeric: 1.5, label: 'Fair' },
  'AG':      { tier: 'poor',    numeric: 2,   label: 'About Good' },
  'G':       { tier: 'good',    numeric: 3,   label: 'Good' },
  'VG':      { tier: 'good',    numeric: 4,   label: 'Very Good' },
  'F':       { tier: 'fine',    numeric: 5,   label: 'Fine' },
  'VF':      { tier: 'fine',    numeric: 6,   label: 'Very Fine' },
  'EF':      { tier: 'ef',      numeric: 7,   label: 'Extremely Fine' },
  'XF':      { tier: 'ef',      numeric: 7,   label: 'Extremely Fine' },
  'AU':      { tier: 'au',      numeric: 8,   label: 'About Uncirculated' },
  'MS':      { tier: 'ms',      numeric: 9,   label: 'Mint State' },
  'FDC':     { tier: 'ms',      numeric: 10,  label: 'Fleur de Coin' },
  'UNKNOWN': { tier: 'unknown', numeric: 0,   label: 'Unknown' },
};

/** Parse grade string to GradeConfig */
export function parseGrade(grade: string | null | undefined): GradeConfig | null {
  if (!grade) return null;
  
  // Clean and uppercase the grade string
  const g = grade.replace(/\d+/g, '').toUpperCase().trim();
  
  // Direct match first
  if (GRADE_MAP[g]) return GRADE_MAP[g];
  
  // Check for grade codes within the string (order matters - check specific first)
  // MS tier
  if (g.includes('MS') || g.includes('FDC') || g.includes('MINT') || g.includes('UNC') || g.includes('BU')) {
    return GRADE_MAP['MS'];
  }
  // AU tier (check before VF to avoid "AU" in "AUGUSTUS" false match)
  if (g.includes('AU') && !g.includes('AUG')) {
    return GRADE_MAP['AU'];
  }
  // EF tier (check before Fine to avoid "F" in "EF/XF" confusion)
  if (g.includes('EF') || g.includes('XF') || g.includes('EXTREMELY')) {
    return GRADE_MAP['EF'];
  }
  // Fine tier (check for F, VF, Fine - but not EF/XF which were caught above)
  // "Choice F", "F+", "VF", "Very Fine", "FV" should all map here
  if (g.includes('VF') || g.includes('FINE') || g === 'FV' || g.startsWith('FV') ||
      /\bF\b/.test(g) || /\bF\+/.test(g) || g.endsWith(' F') || g === 'F' || g === 'F+') {
    return GRADE_MAP['VF'];
  }
  // Good tier (exclude AG which is poor)
  if ((g.includes('VG') || g === 'G' || g.includes('GOOD')) && !g.includes('AG')) {
    return GRADE_MAP['VG'];
  }
  // Poor tier
  if (g.includes('POOR') || g.includes('FAIR') || g.includes('FR') || g.includes('AG')) {
    return GRADE_MAP['AG'];
  }
  
  return null;
}

// ============================================================================
// CATEGORY CONFIGURATION
// ============================================================================

export type CategoryType = 
  | 'republic' | 'imperial' | 'provincial' | 'late' 
  | 'greek' | 'celtic' | 'judaea' | 'eastern' | 'byzantine' | 'other';

export interface CategoryConfig {
  /** Display label */
  label: string;
  /** CSS variable name */
  cssVar: string;
  /** Historical period description */
  period: string;
}

export const CATEGORY_CONFIG: Record<CategoryType, CategoryConfig> = {
  republic:   { label: 'Republic',   cssVar: 'republic',   period: '509-27 BC' },
  imperial:   { label: 'Imperial',   cssVar: 'imperial',   period: '27 BC - 284 AD' },
  provincial: { label: 'Provincial', cssVar: 'provincial', period: 'Greek Imperial' },
  late:       { label: 'Late Roman', cssVar: 'late',       period: '284-491 AD' },
  greek:      { label: 'Greek',      cssVar: 'greek',      period: 'pre-Roman' },
  celtic:     { label: 'Celtic',     cssVar: 'celtic',     period: 'Northern Europe' },
  judaea:     { label: 'Judaean',    cssVar: 'judaea',     period: 'Hasmonean-Roman' },
  eastern:    { label: 'Eastern',    cssVar: 'eastern',    period: 'Parthian/Sasanian' },
  byzantine:  { label: 'Byzantine',  cssVar: 'byzantine',  period: '491+ AD' },
  other:      { label: 'Other',      cssVar: 'other',      period: '' },
};

/** Parse category string to CategoryType */
export function parseCategory(category: string | null | undefined): CategoryType {
  if (!category) return 'other';
  const c = category.toLowerCase().replace(/[_-]/g, '');
  
  if (c.includes('republic')) return 'republic';
  if (c.includes('imperial') && !c.includes('provincial')) return 'imperial';
  if (c.includes('provincial')) return 'provincial';
  if (c.includes('late') || c.includes('dominate')) return 'late';
  if (c.includes('greek')) return 'greek';
  if (c.includes('celtic')) return 'celtic';
  if (c.includes('judae') || c.includes('judea')) return 'judaea';
  if (c.includes('eastern') || c.includes('parthian') || c.includes('sasanian')) return 'eastern';
  if (c.includes('byzant')) return 'byzantine';
  
  return 'other';
}
