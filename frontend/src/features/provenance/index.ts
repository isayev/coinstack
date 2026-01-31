/**
 * Provenance Feature Module (V3)
 *
 * Unified provenance (pedigree) management for coin ownership history.
 * Supports flexible detail levels from minimal ("Ex Hunt Collection")
 * to complete auction records with full financial data.
 */

// Main Components
export { ProvenanceManager, ProvenanceDialog } from './ProvenanceManager';
export { ProvenanceTimelineV3 } from './ProvenanceTimelineV3';
export { ProvenanceEntryForm } from './ProvenanceEntryForm';

// Hooks
export {
  useProvenanceChain,
  useAddProvenanceEntry,
  useUpdateProvenanceEntry,
  useDeleteProvenanceEntry,
  useReorderProvenance,
} from './useProvenance';

// Schema and validation
export {
  ProvenanceFormSchema,
  PROVENANCE_EVENT_TYPES,
  COMMON_AUCTION_HOUSES,
  getDefaultCurrency,
  detectEventType,
  formatProvenanceDisplay,
  getDefaultFormValues,
  type ProvenanceFormData,
  type ProvenanceEventTypeValue,
} from './schema';
