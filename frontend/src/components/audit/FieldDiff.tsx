/**
 * FieldDiff component - Shows side-by-side comparison with similarity highlighting.
 */

import { cn } from "@/lib/utils";
import type { DifferenceType, TrustLevel } from "@/types/audit";
import { DIFFERENCE_TYPE_LABELS, TRUST_LEVEL_COLORS } from "@/types/audit";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Equal, AlertTriangle, Check, X } from "lucide-react";

interface FieldDiffProps {
  fieldName: string;
  currentValue: string | null;
  auctionValue: string | null;
  normalizedCurrent?: string | null;
  normalizedAuction?: string | null;
  similarity?: number | null;
  differenceType?: DifferenceType | null;
  trustLevel: TrustLevel;
  sourceHouse: string;
  comparisonNotes?: string | null;
  showNormalized?: boolean;
  compact?: boolean;
}

/**
 * Get color classes based on similarity score - dark mode aware
 */
function getSimilarityColors(similarity: number | null | undefined): string {
  if (similarity == null) return "bg-muted/50";
  if (similarity >= 0.9) return "bg-emerald-500/10 border-emerald-500/30 dark:bg-emerald-500/15";
  if (similarity >= 0.7) return "bg-amber-500/10 border-amber-500/30 dark:bg-amber-500/15";
  return "bg-red-500/10 border-red-500/30 dark:bg-red-500/15";
}

/**
 * Get badge variant based on difference type - consistent icon colors
 */
function getDifferenceIcon(type: DifferenceType | null | undefined) {
  switch (type) {
    case "exact":
      return <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />;
    case "equivalent":
    case "format_diff":
    case "within_tolerance":
      return <Equal className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />;
    case "adjacent":
    case "overlapping":
    case "partial":
      return <AlertTriangle className="w-3 h-3 text-amber-600 dark:text-amber-400" />;
    case "mismatch":
    case "missing":
      return <X className="w-3 h-3 text-red-600 dark:text-red-400" />;
    default:
      return null;
  }
}

/**
 * Format field name for display
 */
function formatFieldName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Format similarity as percentage
 */
function formatSimilarity(similarity: number | null | undefined): string {
  if (similarity == null) return "-";
  return `${Math.round(similarity * 100)}%`;
}

export function FieldDiff({
  fieldName,
  currentValue,
  auctionValue,
  normalizedCurrent,
  normalizedAuction,
  similarity,
  differenceType,
  trustLevel,
  sourceHouse,
  comparisonNotes,
  showNormalized = false,
  compact = false,
}: FieldDiffProps) {
  const similarityClass = getSimilarityColors(similarity);
  
  if (compact) {
    return (
      <div className={cn("rounded-md border p-3", similarityClass)}>
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className="text-sm font-semibold text-foreground">{formatFieldName(fieldName)}</span>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={cn("border", TRUST_LEVEL_COLORS[trustLevel])}>
              {trustLevel}
            </Badge>
            <span className={cn(
              "text-xs font-mono font-medium",
              similarity != null && similarity >= 0.9 ? "text-emerald-600 dark:text-emerald-400" :
              similarity != null && similarity >= 0.7 ? "text-amber-600 dark:text-amber-400" :
              "text-red-600 dark:text-red-400"
            )}>
              {formatSimilarity(similarity)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <div className="flex-1 px-2 py-1.5 rounded bg-muted/60 border border-border/50">
            <span className="text-muted-foreground line-through">
              {currentValue || "(empty)"}
            </span>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          <div className={cn(
            "flex-1 px-2 py-1.5 rounded border font-medium",
            "bg-primary/5 border-primary/30 text-foreground"
          )}>
            {auctionValue || "(empty)"}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("rounded-lg border", similarityClass)}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b bg-muted/40">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground">{formatFieldName(fieldName)}</span>
          {differenceType && (
            <Badge variant="secondary" className="gap-1">
              {getDifferenceIcon(differenceType)}
              <span className="text-foreground">{DIFFERENCE_TYPE_LABELS[differenceType]}</span>
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={cn("border", TRUST_LEVEL_COLORS[trustLevel])}>
            {trustLevel}
          </Badge>
          <Badge variant="outline" className="text-foreground">{sourceHouse}</Badge>
          {similarity != null && (
            <span className={cn(
              "text-sm font-mono font-medium",
              similarity >= 0.9 ? "text-emerald-600 dark:text-emerald-400" :
              similarity >= 0.7 ? "text-amber-600 dark:text-amber-400" :
              "text-red-600 dark:text-red-400"
            )}>
              {formatSimilarity(similarity)} match
            </span>
          )}
        </div>
      </div>

      {/* Values comparison */}
      <div className="grid grid-cols-2 gap-4 p-4">
        {/* Current value */}
        <div>
          <div className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
            Current Value
          </div>
          <div
            className={cn(
              "p-3 rounded-md border text-sm bg-card",
              similarity != null && similarity >= 0.9
                ? "border-emerald-500/40"
                : "border-red-500/40"
            )}
          >
            <span className="text-foreground">
              {currentValue || <span className="text-muted-foreground italic">(empty)</span>}
            </span>
          </div>
          {showNormalized && normalizedCurrent && (
            <div className="mt-2 text-xs text-muted-foreground">
              <span className="font-medium">Normalized:</span> {normalizedCurrent}
            </div>
          )}
        </div>

        {/* Auction value */}
        <div>
          <div className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
            Auction Value ({sourceHouse})
          </div>
          <div className={cn(
            "p-3 rounded-md border text-sm",
            "bg-primary/5 border-primary/40"
          )}>
            <span className="text-foreground font-medium">
              {auctionValue || <span className="text-muted-foreground italic">(empty)</span>}
            </span>
          </div>
          {showNormalized && normalizedAuction && (
            <div className="mt-2 text-xs text-muted-foreground">
              <span className="font-medium">Normalized:</span> {normalizedAuction}
            </div>
          )}
        </div>
      </div>

      {/* Notes */}
      {comparisonNotes && (
        <div className="px-4 pb-3">
          <div className="text-xs text-muted-foreground bg-muted/60 rounded-md px-3 py-2 border border-border/50">
            {comparisonNotes}
          </div>
        </div>
      )}
    </div>
  );
}

export default FieldDiff;
