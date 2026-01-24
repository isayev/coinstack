/**
 * AuditCoinPreview - Compact coin preview for audit cards
 * 
 * Shows coin image, ruler/denomination, metal badge, and grade badge
 * in a compact format suitable for audit discrepancy and enrichment cards.
 */

import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { 
  MetalBadge, 
  GradeBadge, 
  parseCategory,
  CATEGORY_CONFIG,
} from "@/components/design-system";
import { ExternalLink, ImageOff } from "lucide-react";

export interface AuditCoinPreviewProps {
  coinId: number;
  primaryImage?: string | null;
  ruler?: string | null;
  denomination?: string | null;
  metal?: string | null;
  grade?: string | null;
  category?: string | null;
  mintYearStart?: number | null;
  mintYearEnd?: number | null;
  isCirca?: boolean;
  compact?: boolean;
  className?: string;
}

function formatYear(
  start: number | null | undefined, 
  end: number | null | undefined, 
  isCirca?: boolean
): string {
  if (!start && !end) return "";
  
  const prefix = isCirca ? "c. " : "";
  
  if (start && end && start !== end) {
    const startStr = start < 0 ? `${Math.abs(start)}` : `${start}`;
    const endStr = end < 0 ? `${Math.abs(end)} BC` : `${end} AD`;
    const startSuffix = start < 0 && end > 0 ? " BC" : "";
    return `${prefix}${startStr}${startSuffix}–${endStr}`;
  }
  
  const year = start || end;
  if (!year) return "";
  return `${prefix}${Math.abs(year)} ${year < 0 ? "BC" : "AD"}`;
}

export function AuditCoinPreview({
  coinId,
  primaryImage,
  ruler,
  denomination,
  metal,
  grade,
  category,
  mintYearStart,
  mintYearEnd,
  isCirca,
  compact = false,
  className,
}: AuditCoinPreviewProps) {
  const yearDisplay = formatYear(mintYearStart, mintYearEnd, isCirca);
  const parsedCategory = parseCategory(category || undefined);
  const categoryConfig = CATEGORY_CONFIG[parsedCategory];
  
  // Fixed width for consistent alignment
  const containerWidth = compact ? "w-20" : "w-28";
  const imageSize = compact ? "w-16 h-16" : "w-24 h-24";
  
  return (
    <div className={cn("flex flex-col items-center", containerWidth, className)}>
      {/* Coin Image */}
      <Link 
        to={`/coins/${coinId}`}
        className={cn(
          "relative rounded-lg overflow-hidden flex-shrink-0",
          "border-2 border-border/50 hover:border-primary/50 transition-colors",
          imageSize
        )}
        style={{ 
          background: 'var(--bg-surface)',
          borderBottomColor: `var(--category-${categoryConfig.cssVar})`,
          borderBottomWidth: '3px',
        }}
      >
        {primaryImage ? (
          <img 
            src={`/api${primaryImage}`}
            alt={`${ruler || ''} ${denomination || ''}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-muted/30">
            <ImageOff className="w-6 h-6 text-muted-foreground/40" />
          </div>
        )}
        
        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/40 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center">
          <ExternalLink className="w-4 h-4 text-white" />
        </div>
      </Link>
      
      {/* Coin Info - Below image */}
      <div className="flex flex-col items-center mt-2 w-full min-w-0 text-center">
        {/* Ruler / Title */}
        <Link 
          to={`/coins/${coinId}`}
          className="font-medium text-xs text-foreground hover:text-primary transition-colors truncate w-full"
          title={ruler || denomination || `Coin #${coinId}`}
        >
          {ruler || denomination || `#${coinId}`}
        </Link>
        
        {/* Denomination & Year */}
        {(denomination || yearDisplay) && (
          <div className="text-[10px] text-muted-foreground truncate w-full" title={`${ruler && denomination ? denomination : ''} ${yearDisplay}`}>
            {ruler && denomination ? denomination : ''}
            {ruler && denomination && yearDisplay ? ', ' : ''}
            {yearDisplay}
          </div>
        )}
        
        {/* Badges */}
        <div className="flex items-center justify-center gap-1 mt-1 flex-wrap">
          {metal && (
            <MetalBadge metal={metal} size="xs" />
          )}
          {grade && (
            <GradeBadge grade={grade} size="sm" />
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Minimal version for tight spaces - just image and basic info
 */
export function AuditCoinPreviewMinimal({
  coinId,
  primaryImage,
  ruler,
  denomination,
  metal,
  className,
}: Pick<AuditCoinPreviewProps, 'coinId' | 'primaryImage' | 'ruler' | 'denomination' | 'metal' | 'className'>) {
  return (
    <Link 
      to={`/coins/${coinId}`}
      className={cn(
        "flex items-center gap-2 group",
        className
      )}
    >
      {/* Tiny thumbnail */}
      <div 
        className="w-10 h-10 rounded overflow-hidden flex-shrink-0 border border-border/50 group-hover:border-primary/50 transition-colors"
        style={{ background: 'var(--bg-surface)' }}
      >
        {primaryImage ? (
          <img 
            src={`/api${primaryImage}`}
            alt=""
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageOff className="w-3 h-3 text-muted-foreground/50" />
          </div>
        )}
      </div>
      
      {/* Name */}
      <span className="text-sm truncate group-hover:text-primary transition-colors">
        {ruler || denomination || `#${coinId}`}
      </span>
      
      {/* Metal badge */}
      {metal && (
        <MetalBadge metal={metal} size="xs" />
      )}
    </Link>
  );
}
