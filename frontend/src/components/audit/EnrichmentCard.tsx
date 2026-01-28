/**
 * EnrichmentCard - Enhanced enrichment display with coin preview
 * 
 * Features:
 * - Coin image thumbnail
 * - Auction image preview with download capability
 * - Source badge with trust indicator and external link
 * - Source-specific metadata display (Heritage grades, CNG refs, eBay seller)
 * - Confidence indicator
 */

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { Enrichment } from "@/types/audit";
import { useApplyEnrichment, useRejectEnrichment, useDownloadCoinImages } from "@/hooks/useAudit";
import { AuditCoinPreview } from "./AuditCoinPreview";
import { SourceBadge, TrustLevel } from "./SourceBadge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { 
  Check, 
  X, 
  Loader2, 
  Sparkles, 
  Plus,
  CheckCircle2,
  ArrowRight,
  ExternalLink,
  Download,
  ImageIcon,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface EnrichmentCardProps {
  enrichment: Enrichment;
  onResolved?: () => void;
  showCoinLink?: boolean;
  // Extended coin data for preview (optional)
  coinData?: {
    primaryImage?: string | null;
    ruler?: string | null;
    denomination?: string | null;
    metal?: string | null;
    grade?: string | null;
    category?: string | null;
    mintYearStart?: number | null;
    mintYearEnd?: number | null;
  };
  // Source-specific metadata (optional)
  sourceMetadata?: {
    // Heritage
    strikeScore?: string | null;
    surfaceScore?: string | null;
    // Biddr
    subHouse?: string | null;
    // eBay
    sellerUsername?: string | null;
    sellerFeedbackScore?: number | null;
    sellerFeedbackPct?: number | null;
    sellerIsTopRated?: boolean;
  };
}

export function EnrichmentCard({
  enrichment,
  onResolved,
  showCoinLink = true,
  coinData,
  sourceMetadata,
}: EnrichmentCardProps) {
  const [expanded, setExpanded] = useState(false);
  const applyMutation = useApplyEnrichment();
  const rejectMutation = useRejectEnrichment();
  const downloadImagesMutation = useDownloadCoinImages();

  const handleApply = async () => {
    await applyMutation.mutateAsync({
      coin_id: enrichment.coin_id,
      field_name: enrichment.field_name,
      value: enrichment.suggested_value,
    });
    onResolved?.();
  };

  const handleReject = async () => {
    await rejectMutation.mutateAsync({ id: enrichment.id });
    onResolved?.();
  };

  const handleDownloadImages = async () => {
    await downloadImagesMutation.mutateAsync({
      coinId: enrichment.coin_id,
      auctionDataId: enrichment.auction_data_id ?? undefined,
    });
  };

  const isResolved = enrichment.status !== "pending";
  const isPending = applyMutation.isPending || rejectMutation.isPending;
  const isDownloading = downloadImagesMutation.isPending;
  const confidence = enrichment.confidence ?? 0.8;
  
  // Map trust level string to type
  const trustLevel = (enrichment.trust_level || 'medium') as TrustLevel;
  
  // Determine if this is a high-value enrichment
  const isHighValue = ['grade', 'certification_number', 'weight_g', 'primary_reference'].includes(enrichment.field_name);
  
  // Auction image data
  const auctionImages = enrichment.auction_images ?? [];
  const hasAuctionImages = auctionImages.length > 0;
  const sourceUrl = enrichment.source_url;

  return (
    <div
      className={cn(
        "rounded-lg border-2 transition-all",
        "bg-card",
        isResolved ? "opacity-60 border-muted" : "border-blue-500/30",
        enrichment.auto_applicable && !isResolved && "border-blue-500/60 bg-blue-500/5"
      )}
    >
      {/* Main content grid */}
      <div className="grid grid-cols-[auto_1fr] gap-4 p-4">
        {/* Coin Preview Column */}
        {showCoinLink && (
          <div className="flex flex-col items-center gap-2">
            <AuditCoinPreview
              coinId={enrichment.coin_id}
              primaryImage={coinData?.primaryImage ?? enrichment.coin_primary_image}
              ruler={coinData?.ruler ?? enrichment.coin_ruler}
              denomination={coinData?.denomination ?? enrichment.coin_denomination}
              metal={coinData?.metal ?? enrichment.coin_metal}
              grade={coinData?.grade ?? enrichment.coin_grade}
              category={coinData?.category ?? enrichment.coin_category}
              mintYearStart={coinData?.mintYearStart ?? enrichment.coin_mint_year_start}
              mintYearEnd={coinData?.mintYearEnd ?? enrichment.coin_mint_year_end}
              isCirca={enrichment.coin_is_circa}
              compact
            />
          </div>
        )}

        {/* Content Column */}
        <div className="space-y-3 min-w-0">
          {/* Header Row */}
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-1">
              {/* Field name and status */}
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-500 flex-shrink-0" />
                <span className="font-medium text-sm">
                  {formatFieldName(enrichment.field_name)}
                </span>
                {enrichment.auto_applicable && !isResolved && (
                  <Badge 
                    variant="secondary" 
                    className="text-xs bg-blue-500/10 text-blue-500 border-blue-500/30"
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    Auto-fill
                  </Badge>
                )}
                {isHighValue && !isResolved && (
                  <Badge 
                    variant="secondary" 
                    className="text-xs bg-amber-500/10 text-amber-500 border-amber-500/30"
                  >
                    Key field
                  </Badge>
                )}
                {isResolved && (
                  <Badge
                    variant={
                      enrichment.status === "applied" ? "default" :
                      enrichment.status === "rejected" ? "destructive" : "secondary"
                    }
                    className="text-xs"
                  >
                    {enrichment.status === "applied" ? (
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                    ) : (
                      <X className="w-3 h-3 mr-1" />
                    )}
                    {enrichment.status}
                  </Badge>
                )}
              </div>

              {/* Source and confidence */}
              <div className="flex items-center gap-2 flex-wrap">
                <SourceBadge 
                  source={enrichment.source_house} 
                  trustLevel={trustLevel}
                  subHouse={sourceMetadata?.subHouse}
                  sellerUsername={sourceMetadata?.sellerUsername}
                  sellerFeedbackScore={sourceMetadata?.sellerFeedbackScore}
                  sellerFeedbackPct={sourceMetadata?.sellerFeedbackPct}
                  sellerIsTopRated={sourceMetadata?.sellerIsTopRated}
                  size="sm"
                />
                
                {/* Direct link to auction source */}
                {sourceUrl && (
                  <a
                    href={sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    View on {enrichment.source_house.split('/')[0]}
                  </a>
                )}
                
                {/* Image count badge */}
                {hasAuctionImages && (
                  <Badge 
                    variant="outline" 
                    className="text-xs gap-1 border-sky-500/40 text-sky-600 dark:text-sky-400"
                  >
                    <ImageIcon className="w-3 h-3" />
                    {auctionImages.length}
                  </Badge>
                )}
                
                {/* Confidence indicator */}
                <div className="flex items-center gap-1.5">
                  <Progress 
                    value={confidence * 100} 
                    className={cn(
                      "w-12 h-1.5",
                      confidence >= 0.8 ? "[&>div]:bg-emerald-500" :
                      confidence >= 0.5 ? "[&>div]:bg-amber-500" : "[&>div]:bg-orange-500"
                    )}
                  />
                  <span className="text-xs text-muted-foreground">
                    {Math.round(confidence * 100)}%
                  </span>
                </div>
              </div>
            </div>
            
            {/* Expand/collapse button for images */}
            {hasAuctionImages && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(!expanded)}
                className="flex-shrink-0"
              >
                {expanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </Button>
            )}
          </div>

          {/* Suggested value display */}
          <div className="rounded-md border border-sky-500/30 p-3 bg-sky-500/5 dark:bg-sky-500/10">
            <div className="flex items-center gap-3">
              {/* Empty indicator */}
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="text-sm italic px-2 py-1 bg-muted/60 rounded">(empty)</span>
                <ArrowRight className="w-4 h-4" />
              </div>
              
              {/* Suggested value */}
              <div className="flex-1 px-2 py-1 rounded bg-sky-500/10 border border-sky-500/30">
                <span className="text-sm font-semibold text-sky-700 dark:text-sky-300">
                  {formatValue(enrichment.field_name, enrichment.suggested_value)}
                </span>
              </div>
            </div>
            
            {/* Source-specific metadata */}
            {renderSourceMetadata(enrichment.source_house, sourceMetadata)}
          </div>

          {/* Expanded auction image preview */}
          {expanded && hasAuctionImages && (
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">
                Auction Images ({auctionImages.length})
              </label>
              <div className="flex gap-2 flex-wrap">
                {auctionImages.slice(0, 4).map((imageUrl, idx) => (
                  <a
                    key={idx}
                    href={imageUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="relative w-16 h-16 rounded border border-border/50 overflow-hidden hover:border-primary/50 transition-colors group"
                  >
                    <img
                      src={imageUrl}
                      alt={`Auction image ${idx + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <ExternalLink className="w-4 h-4 text-white" />
                    </div>
                  </a>
                ))}
                {auctionImages.length > 4 && (
                  <div className="w-16 h-16 rounded border border-border/50 flex items-center justify-center text-xs text-muted-foreground">
                    +{auctionImages.length - 4}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Resolved notes */}
          {isResolved && enrichment.rejection_reason && (
            <div className="text-sm text-muted-foreground border-t pt-2">
              {enrichment.rejection_reason}
            </div>
          )}

          {/* Actions */}
          {!isResolved && (
            <div className="flex items-center gap-2 pt-2 border-t border-border/50">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleApply}
                      disabled={isPending}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      {applyMutation.isPending ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Check className="w-3.5 h-3.5 mr-1" />
                      )}
                      Apply
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Apply this value to the coin</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleReject}
                      disabled={isPending}
                    >
                      {rejectMutation.isPending ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <X className="w-3.5 h-3.5 mr-1" />
                      )}
                      Skip
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Reject this suggestion</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {/* Download Images Button */}
              {hasAuctionImages && (
                <>
                  <div className="flex-1" />
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleDownloadImages}
                          disabled={isDownloading}
                          className="text-sky-600 dark:text-sky-400 border-sky-500/30 hover:bg-sky-500/10"
                        >
                          {isDownloading ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                          ) : (
                            <Download className="w-3.5 h-3.5 mr-1" />
                          )}
                          {auctionImages.length} {auctionImages.length === 1 ? 'Image' : 'Images'}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        Download auction images to coin record
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatFieldName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(fieldName: string, value: string | null | undefined): string {
  if (!value) return "(empty)";
  
  // Format specific field types
  if (fieldName === "weight_g") {
    const num = parseFloat(value);
    return isNaN(num) ? value : `${num.toFixed(2)} g`;
  }
  if (fieldName === "diameter_mm") {
    const num = parseFloat(value);
    return isNaN(num) ? value : `${num.toFixed(1)} mm`;
  }
  if (fieldName === "die_axis") {
    return `${value}h`;
  }
  
  return value;
}

function renderSourceMetadata(
  source: string, 
  metadata?: EnrichmentCardProps['sourceMetadata']
): React.ReactNode {
  if (!metadata) return null;
  
  const normalizedSource = source.toLowerCase();
  
  // Heritage-specific: NGC scores
  if (normalizedSource.includes('heritage')) {
    if (metadata.strikeScore || metadata.surfaceScore) {
      return (
        <div className="mt-2 pt-2 border-t border-border/50 text-xs text-muted-foreground">
          <span className="font-medium">NGC Scores:</span>
          {metadata.strikeScore && <span className="ml-2">Strike: {metadata.strikeScore}</span>}
          {metadata.surfaceScore && <span className="ml-2">Surface: {metadata.surfaceScore}</span>}
        </div>
      );
    }
  }
  
  // Biddr-specific: Sub-house
  if (normalizedSource.includes('biddr') && metadata.subHouse) {
    return (
      <div className="mt-2 pt-2 border-t border-border/50 text-xs text-muted-foreground">
        <span className="font-medium">Via:</span> {metadata.subHouse}
      </div>
    );
  }
  
  // eBay-specific: Seller info
  if (normalizedSource.includes('ebay') && metadata.sellerUsername) {
    return (
      <div className="mt-2 pt-2 border-t border-border/50 text-xs text-muted-foreground">
        <span className="font-medium">Seller:</span> {metadata.sellerUsername}
        {metadata.sellerFeedbackPct !== undefined && metadata.sellerFeedbackPct !== null && (
          <span className={cn(
            "ml-2",
            metadata.sellerFeedbackPct >= 99 ? "text-emerald-400" :
            metadata.sellerFeedbackPct >= 95 ? "text-amber-400" : "text-red-400"
          )}>
            ({metadata.sellerFeedbackPct.toFixed(1)}% positive)
          </span>
        )}
      </div>
    );
  }
  
  return null;
}

export default EnrichmentCard;
