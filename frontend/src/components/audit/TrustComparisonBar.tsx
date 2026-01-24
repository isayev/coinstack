/**
 * TrustComparisonBar - Visual comparison of trust levels between current and auction values
 */

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { TrustLevel } from "@/types/audit";

interface TrustSource {
  source: string;
  level: TrustLevel | number;  // Can be TrustLevel string or numeric 0-100
}

interface TrustComparisonBarProps {
  current: TrustSource;
  auction: TrustSource;
  className?: string;
}

// Convert TrustLevel to numeric
const TRUST_TO_NUMERIC: Record<TrustLevel, number> = {
  authoritative: 95,
  high: 80,
  medium: 60,
  low: 40,
  untrusted: 20,
};

function getNumericTrust(level: TrustLevel | number): number {
  if (typeof level === 'number') return level;
  return TRUST_TO_NUMERIC[level] || 50;
}

function getTrustColor(level: number): string {
  if (level >= 80) return "bg-emerald-500 dark:bg-emerald-400";
  if (level >= 60) return "bg-sky-500 dark:bg-sky-400";
  if (level >= 40) return "bg-amber-500 dark:bg-amber-400";
  return "bg-red-500 dark:bg-red-400";
}

function getTrustTextColor(level: number): string {
  if (level >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (level >= 60) return "text-sky-600 dark:text-sky-400";
  if (level >= 40) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

export function TrustComparisonBar({
  current,
  auction,
  className,
}: TrustComparisonBarProps) {
  const currentLevel = getNumericTrust(current.level);
  const auctionLevel = getNumericTrust(auction.level);
  
  const winner = auctionLevel > currentLevel ? "auction" :
                 currentLevel > auctionLevel ? "current" : "tie";
  const difference = Math.abs(auctionLevel - currentLevel);
  
  return (
    <div className={cn("space-y-3", className)}>
      {/* Header with winner indicator */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground font-semibold uppercase tracking-wide">Trust Comparison</span>
        {winner !== "tie" ? (
          <Badge 
            variant="outline" 
            className={cn(
              "text-xs font-medium",
              winner === "auction" 
                ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/40"
                : "bg-sky-500/15 text-sky-700 dark:text-sky-400 border-sky-500/40"
            )}
          >
            {winner === "auction" ? "Auction wins" : "Current wins"}
            {difference > 20 && ` (+${difference})`}
          </Badge>
        ) : (
          <Badge variant="outline" className="text-xs font-medium bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/40">
            Equal trust — needs review
          </Badge>
        )}
      </div>
      
      {/* Comparison bars */}
      <div className="flex items-center gap-4">
        {/* Current source */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-sm font-semibold text-foreground truncate max-w-[120px]">
              {current.source || "User entered"}
            </span>
            <span className={cn("text-xs font-mono font-semibold", getTrustTextColor(currentLevel))}>
              {currentLevel}%
            </span>
          </div>
          <div className="h-2.5 bg-muted rounded-full overflow-hidden border border-border/30">
            <div 
              className={cn(
                "h-full rounded-full transition-all duration-300",
                winner === "current" ? getTrustColor(currentLevel) : "bg-muted-foreground/30"
              )}
              style={{ width: `${currentLevel}%` }}
            />
          </div>
        </div>
        
        <span className="text-muted-foreground text-sm font-semibold">vs</span>
        
        {/* Auction source */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-sm font-semibold text-foreground truncate max-w-[120px]">
              {auction.source}
            </span>
            <span className={cn("text-xs font-mono font-semibold", getTrustTextColor(auctionLevel))}>
              {auctionLevel}%
            </span>
          </div>
          <div className="h-2.5 bg-muted rounded-full overflow-hidden border border-border/30">
            <div 
              className={cn(
                "h-full rounded-full transition-all duration-300",
                winner === "auction" ? getTrustColor(auctionLevel) : "bg-muted-foreground/30"
              )}
              style={{ width: `${auctionLevel}%` }}
            />
          </div>
        </div>
      </div>
      
      {/* Trust explanation */}
      {difference >= 30 && (
        <p className="text-xs text-muted-foreground">
          {winner === "auction" 
            ? `${auction.source} is a significantly more trusted source for this field.`
            : `Current value has higher trust. Review carefully before changing.`
          }
        </p>
      )}
    </div>
  );
}

/**
 * Compact inline trust indicator
 */
export function TrustIndicatorInline({
  level,
  source,
}: {
  level: TrustLevel | number;
  source?: string;
}) {
  const numericLevel = getNumericTrust(level);
  
  return (
    <span className="inline-flex items-center gap-1.5 text-xs">
      <span 
        className={cn(
          "w-2 h-2 rounded-full ring-1 ring-border/30",
          getTrustColor(numericLevel)
        )}
      />
      <span className={cn("font-semibold", getTrustTextColor(numericLevel))}>
        {numericLevel}%
      </span>
      {source && (
        <span className="text-foreground truncate max-w-[80px]">
          {source}
        </span>
      )}
    </span>
  );
}
