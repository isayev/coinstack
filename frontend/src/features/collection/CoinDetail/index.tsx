/**
 * CoinDetail - Main coin detail page component
 * 
 * Orchestrates the scholarly numismatic detail view with:
 * - Identity header with category bar
 * - Side-by-side obverse/reverse panels
 * - Secondary data cards (physical specs, references, etc.)
 * - Provenance timeline
 * - Historical context (LLM-generated)
 * - Die study section
 * 
 * @module features/collection/CoinDetail
 */

export { IdentityHeader } from './IdentityHeader';
export { ObverseReversePanel } from './ObverseReversePanel';
export { CoinSidePanel } from './CoinSidePanel';
export { ReferencesCard } from './ReferencesCard';
export { ProvenanceTimeline } from './ProvenanceTimeline';
export { HistoricalContextCard } from './HistoricalContextCard';
export { EnrichmentToolbar, useCoinEnrichmentActions } from './EnrichmentToolbar';
export { DieStudyCard } from './DieStudyCard';
export { IconographySection, IconographyInline } from './IconographySection';
export { DataCard, DataField, DataFieldRow } from './DataCard';
export { SpecificationsCard } from './SpecificationsCard';
