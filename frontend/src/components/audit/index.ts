/**
 * Audit components index
 */

// Core components
export { FieldDiff } from "./FieldDiff";
export { DiscrepancyCard } from "./DiscrepancyCard";
export { EnrichmentCard } from "./EnrichmentCard";
export { AuditSummaryStats } from "./AuditSummaryStats";
export { AuditProgress } from "./AuditProgress";
export { AutoMergeTab } from "./AutoMergeTab";

// Coin preview and source badges
export { AuditCoinPreview, AuditCoinPreviewMinimal } from "./AuditCoinPreview";
export { SourceBadge, TrustIndicator } from "./SourceBadge";
export type { AuditCoinPreviewProps } from "./AuditCoinPreview";
export type { SourceBadgeProps, TrustLevel } from "./SourceBadge";

// Triage and overview
export { ConflictTriageView } from "./ConflictTriageView";

// Trust visualization
export { TrustComparisonBar, TrustIndicatorInline } from "./TrustComparisonBar";

// Field-specific comparators
export { 
  WeightComparison,
  GradeComparison,
  ReferencesComparison,
  MeasurementComparison,
  getFieldComparator,
} from "./FieldComparators";

// Decision support
export { DecisionContext, FIELD_GUIDANCE } from "./DecisionContext";
export type { DecisionContextData, AuctionValue, StatisticalAnalysis } from "./DecisionContext";

// Quick actions
export { QuickActionsToolbar } from "./QuickActionsToolbar";
export type { QuickAction } from "./QuickActionsToolbar";

// Enhanced conflict card
export { EnhancedConflictCard } from "./EnhancedConflictCard";

// Image review
export { ImageReviewTab } from "./ImageReviewTab";

// LLM review
export { LLMReviewTab } from "./LLMReviewTab";
