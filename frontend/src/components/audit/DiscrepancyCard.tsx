/**
 * DiscrepancyCard - Enhanced discrepancy display with coin preview
 * 
 * Features:
 * - Coin image thumbnail with category-colored border
 * - Auction image preview with download capability
 * - Source badge with trust indicator and external link
 * - Similarity progress ring
 * - Inline actions
 */

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { Discrepancy } from "@/types/audit";
import { useResolveDiscrepancy, useDownloadCoinImages } from "@/hooks/useAudit";
import { FieldDiff } from "./FieldDiff";
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
import { Textarea } from "@/components/ui/textarea";
import {
  Check,
  X,
  SkipForward,
  Loader2,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Zap,
  ExternalLink,
  Download,
  ImageIcon,
} from "lucide-react";

interface DiscrepancyCardProps {
  discrepancy: Discrepancy;
  onResolved?: () => void;
  showCoinLink?: boolean;
  expanded?: boolean;
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
}

export function DiscrepancyCard({
  discrepancy,
  onResolved,
  showCoinLink = true,
  expanded: initialExpanded = false,
  coinData,
}: DiscrepancyCardProps) {
  const [expanded, setExpanded] = useState(initialExpanded);
  const [notes, setNotes] = useState("");
  const resolveMutation = useResolveDiscrepancy();
  const downloadImagesMutation = useDownloadCoinImages();

  const handleResolve = async (
    resolution: "accepted" | "rejected" | "ignored"
  ) => {
    await resolveMutation.mutateAsync({
      id: discrepancy.id,
      request: { resolution, notes: notes || undefined },
    });
    setNotes("");
    onResolved?.();
  };

  const handleDownloadImages = async () => {
    await downloadImagesMutation.mutateAsync({
      coinId: discrepancy.coin_id,
      auctionDataId: discrepancy.auction_data_id ?? undefined,
    });
  };

  const isResolved = discrepancy.status !== "pending";
  const isPending = resolveMutation.isPending;
  const isDownloading = downloadImagesMutation.isPending;
  const similarity = discrepancy.similarity ?? 0;
  
  // Map trust level string to type
  const trustLevel = (discrepancy.trust_level || 'medium') as TrustLevel;
  
  // Auction image data
  const auctionImages = discrepancy.auction_images ?? [];
  const hasAuctionImages = auctionImages.length > 0;
  const sourceUrl = discrepancy.source_url;

  // Determine border color based on severity
  const getBorderColor = () => {
    if (isResolved) return 'border-muted';
    if (similarity >= 0.9) return 'border-emerald-500/50';
    if (similarity >= 0.7) return 'border-amber-500/50';
    return 'border-red-500/50';
  };

  return (
    <div
      className={cn(
        "rounded-lg border-2 transition-all",
        "bg-card",
        getBorderColor(),
        isResolved && "opacity-60"
      )}
    >
      {/* Main content grid */}
      <div className="grid grid-cols-[auto_1fr] gap-4 p-4">
        {/* Coin Preview Column */}
        {showCoinLink && (
          <div className="flex flex-col items-center gap-2">
            <AuditCoinPreview
              coinId={discrepancy.coin_id}
              primaryImage={coinData?.primaryImage ?? discrepancy.coin_primary_image}
              ruler={coinData?.ruler ?? discrepancy.coin_ruler}
              denomination={coinData?.denomination ?? discrepancy.coin_denomination}
              metal={coinData?.metal ?? discrepancy.coin_metal}
              grade={coinData?.grade ?? discrepancy.coin_grade}
              category={coinData?.category ?? discrepancy.coin_category}
              mintYearStart={coinData?.mintYearStart ?? discrepancy.coin_mint_year_start}
              mintYearEnd={coinData?.mintYearEnd ?? discrepancy.coin_mint_year_end}
              isCirca={discrepancy.coin_is_circa}
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
                <span className="font-medium text-sm">
                  {formatFieldName(discrepancy.field_name)}
                </span>
                {discrepancy.auto_acceptable && (
                  <Badge 
                    variant="secondary" 
                    className="text-xs bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                  >
                    <Zap className="w-3 h-3 mr-1" />
                    Auto-merge
                  </Badge>
                )}
                {isResolved && (
                  <Badge
                    variant={
                      discrepancy.status === "accepted" ? "default" :
                      discrepancy.status === "rejected" ? "destructive" : "secondary"
                    }
                    className="text-xs"
                  >
                    {discrepancy.status === "accepted" ? (
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                    ) : (
                      <X className="w-3 h-3 mr-1" />
                    )}
                    {discrepancy.status}
                  </Badge>
                )}
              </div>

              {/* Source and similarity */}
              <div className="flex items-center gap-2 flex-wrap">
                <SourceBadge 
                  source={discrepancy.source_house} 
                  trustLevel={trustLevel}
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
                    View on {discrepancy.source_house.split('/')[0]}
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
                
                {/* Similarity indicator */}
                <div className="flex items-center gap-1.5">
                  <Progress 
                    value={similarity * 100} 
                    className={cn(
                      "w-16 h-1.5",
                      similarity >= 0.9 ? "[&>div]:bg-emerald-500" :
                      similarity >= 0.7 ? "[&>div]:bg-amber-500" : "[&>div]:bg-red-500"
                    )}
                  />
                  <span className={cn(
                    "text-xs font-mono font-semibold",
                    similarity >= 0.9 ? "text-emerald-600 dark:text-emerald-400" :
                    similarity >= 0.7 ? "text-amber-600 dark:text-amber-400" : "text-red-600 dark:text-red-400"
                  )}>
                    {Math.round(similarity * 100)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Expand/collapse button */}
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
          </div>

          {/* Compact diff view */}
          {!expanded && (
            <FieldDiff
              fieldName={discrepancy.field_name}
              currentValue={discrepancy.current_value}
              auctionValue={discrepancy.auction_value}
              similarity={discrepancy.similarity}
              differenceType={discrepancy.difference_type}
              trustLevel={discrepancy.trust_level}
              sourceHouse={discrepancy.source_house}
              compact
            />
          )}

          {/* Expanded diff view */}
          {expanded && (
            <div className="space-y-4">
              <FieldDiff
                fieldName={discrepancy.field_name}
                currentValue={discrepancy.current_value}
                auctionValue={discrepancy.auction_value}
                normalizedCurrent={discrepancy.normalized_current}
                normalizedAuction={discrepancy.normalized_auction}
                similarity={discrepancy.similarity}
                differenceType={discrepancy.difference_type}
                trustLevel={discrepancy.trust_level}
                sourceHouse={discrepancy.source_house}
                comparisonNotes={discrepancy.comparison_notes}
                showNormalized
              />

              {/* Auction Image Preview */}
              {hasAuctionImages && (
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

              {/* Resolution notes */}
              {!isResolved && (
                <div className="space-y-2">
                  <label className="text-xs font-medium text-muted-foreground">
                    Notes (optional)
                  </label>
                  <Textarea
                    placeholder="Add notes about this resolution..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                    className="text-sm"
                  />
                </div>
              )}

              {/* Resolved notes */}
              {isResolved && discrepancy.resolution_notes && (
                <div className="text-sm text-muted-foreground border-t pt-2">
                  {discrepancy.resolution_notes}
                </div>
              )}
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
                      onClick={() => handleResolve("accepted")}
                      disabled={isPending}
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      {isPending ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Check className="w-3.5 h-3.5 mr-1" />
                      )}
                      Accept
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    Accept auction value, update coin record
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleResolve("rejected")}
                      disabled={isPending}
                    >
                      <X className="w-3.5 h-3.5 mr-1" />
                      Reject
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Keep current value</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleResolve("ignored")}
                      disabled={isPending}
                      className="text-muted-foreground"
                    >
                      <SkipForward className="w-3.5 h-3.5 mr-1" />
                      Skip
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Ignore this discrepancy</TooltipContent>
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

export default DiscrepancyCard;
