/**
 * Provenance Form Schema (V3)
 *
 * Zod validation schema for provenance entry forms.
 * Supports progressive disclosure with type-aware validation.
 */

import { z } from 'zod';

// =============================================================================
// Event Types
// =============================================================================

export const PROVENANCE_EVENT_TYPES = [
  { value: 'auction', label: 'Auction', icon: 'Gavel' },
  { value: 'dealer', label: 'Dealer', icon: 'Store' },
  { value: 'collection', label: 'Collection', icon: 'Library' },
  { value: 'private_sale', label: 'Private Sale', icon: 'Handshake' },
  { value: 'publication', label: 'Publication', icon: 'BookOpen' },
  { value: 'hoard_find', label: 'Hoard/Find', icon: 'Map' },
  { value: 'estate', label: 'Estate', icon: 'Home' },
  { value: 'acquisition', label: 'My Purchase', icon: 'ShoppingBag' },
] as const;

export type ProvenanceEventTypeValue = (typeof PROVENANCE_EVENT_TYPES)[number]['value'];

// =============================================================================
// Common Auction Houses (for suggestions)
// =============================================================================

export const COMMON_AUCTION_HOUSES = [
  { name: 'Heritage Auctions', currency: 'USD' },
  { name: 'CNG', currency: 'USD' },
  { name: 'Roma Numismatics', currency: 'GBP' },
  { name: 'Nomos AG', currency: 'CHF' },
  { name: 'Leu Numismatik', currency: 'CHF' },
  { name: 'Numismatica Ars Classica', currency: 'CHF' },
  { name: 'Gorny & Mosch', currency: 'EUR' },
  { name: 'Künker', currency: 'EUR' },
  { name: 'Stack\'s Bowers', currency: 'USD' },
  { name: 'Goldberg Auctions', currency: 'USD' },
  { name: 'Harlan J. Berk', currency: 'USD' },
  { name: "Freeman & Sear", currency: 'USD' },
  { name: 'Triton', currency: 'USD' },
  { name: 'NYINC', currency: 'USD' },
];

// =============================================================================
// Form Schema
// =============================================================================

export const ProvenanceFormSchema = z.object({
  // Required fields (Level 1 - always visible)
  event_type: z.enum([
    'auction', 'dealer', 'collection', 'private_sale',
    'publication', 'hoard_find', 'estate', 'acquisition', 'unknown'
  ]),
  source_name: z.string().min(1, 'Source name is required'),

  // Dates (flexible - Level 1)
  event_date: z.string().nullable().optional(),  // ISO date string
  date_string: z.string().nullable().optional(), // "1920s", "circa 1840"

  // Auction details (Level 2 - visible for auction/dealer)
  sale_name: z.string().nullable().optional(),
  sale_number: z.string().nullable().optional(),
  lot_number: z.string().nullable().optional(),
  catalog_reference: z.string().nullable().optional(),

  // Pricing (Level 2)
  hammer_price: z.coerce.number().positive().nullable().optional(),
  buyers_premium_pct: z.coerce.number().min(0).max(100).nullable().optional(),
  total_price: z.coerce.number().positive().nullable().optional(),
  currency: z.string().length(3).default('USD'),

  // Documentation (Level 3 - "More details")
  url: z.string().url().nullable().optional().or(z.literal('')),
  receipt_available: z.boolean().default(false),
  notes: z.string().nullable().optional(),

  // Internal
  sort_order: z.number().default(0),
}).refine(
  (data) => {
    // Require at least one date field for auction/dealer types
    if (['auction', 'dealer'].includes(data.event_type)) {
      return data.event_date || data.date_string;
    }
    return true;
  },
  {
    message: 'Date is required for auction/dealer entries',
    path: ['date_string'],
  }
).refine(
  (data) => {
    // If total_price is set, currency must be set
    if (data.total_price && !data.currency) {
      return false;
    }
    return true;
  },
  {
    message: 'Currency is required when price is specified',
    path: ['currency'],
  }
);

export type ProvenanceFormData = z.infer<typeof ProvenanceFormSchema>;

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get default currency for an auction house.
 */
export function getDefaultCurrency(sourceName: string): string {
  const house = COMMON_AUCTION_HOUSES.find(
    (h) => sourceName.toLowerCase().includes(h.name.toLowerCase())
  );
  return house?.currency ?? 'USD';
}

/**
 * Auto-detect event type from source name.
 */
export function detectEventType(sourceName: string): ProvenanceEventTypeValue {
  const lowerName = sourceName.toLowerCase();

  // Check for auction houses
  if (COMMON_AUCTION_HOUSES.some((h) => lowerName.includes(h.name.toLowerCase()))) {
    return 'auction';
  }

  // Check for auction keywords
  if (lowerName.includes('auction') || lowerName.includes('sale') || lowerName.includes('lot')) {
    return 'auction';
  }

  // Check for collection keywords
  if (lowerName.includes('collection') || lowerName.includes('museum')) {
    return 'collection';
  }

  // Check for dealer keywords
  if (lowerName.includes('numismatic') || lowerName.includes('coins') || lowerName.includes('dealer')) {
    return 'dealer';
  }

  // Check for estate
  if (lowerName.includes('estate') || lowerName.includes('inheritance')) {
    return 'estate';
  }

  // Check for hoard/find
  if (lowerName.includes('hoard') || lowerName.includes('find') || lowerName.includes('excavation')) {
    return 'hoard_find';
  }

  // Default to collection for "Ex" prefix
  if (lowerName.startsWith('ex ')) {
    return 'collection';
  }

  return 'collection'; // Default
}

/**
 * Format provenance entry for display.
 */
export function formatProvenanceDisplay(entry: ProvenanceFormData): string {
  const parts: string[] = [];

  if (entry.source_name) {
    parts.push(entry.source_name);
  }

  if (entry.event_date) {
    const date = new Date(entry.event_date);
    parts.push(date.getFullYear().toString());
  } else if (entry.date_string) {
    parts.push(entry.date_string);
  }

  if (entry.sale_name) {
    parts.push(entry.sale_name);
  }

  if (entry.lot_number) {
    parts.push(`lot ${entry.lot_number}`);
  }

  return parts.join(', ');
}

/**
 * Get empty form defaults.
 */
export function getDefaultFormValues(eventType: ProvenanceEventTypeValue = 'auction'): Partial<ProvenanceFormData> {
  return {
    event_type: eventType,
    source_name: '',
    event_date: null,
    date_string: null,
    sale_name: null,
    sale_number: null,
    lot_number: null,
    catalog_reference: null,
    hammer_price: null,
    buyers_premium_pct: null,
    total_price: null,
    currency: 'USD',
    url: null,
    receipt_available: false,
    notes: null,
    sort_order: 0,
  };
}
