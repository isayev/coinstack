/**
 * SourceBadge - Visual indicator for auction house with trust level
 * 
 * Shows auction house name with color-coded trust indicator:
 * - Heritage: Gold (authoritative for grades)
 * - CNG: Blue (authoritative for references)
 * - Biddr: Teal with sub-house (medium trust)
 * - eBay: Gray with seller score (low trust for metadata)
 */

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { 
  Shield, 
  ShieldCheck, 
  ShieldAlert, 
  ShieldQuestion,
  Star,
  TrendingUp,
  User,
} from "lucide-react";

export type TrustLevel = 'authoritative' | 'high' | 'medium' | 'low' | 'untrusted';

export interface SourceBadgeProps {
  source: string;
  trustLevel?: TrustLevel;
  subHouse?: string | null;  // For Biddr: Savoca, Roma, Leu, etc.
  sellerUsername?: string | null;  // For eBay
  sellerFeedbackScore?: number | null;
  sellerFeedbackPct?: number | null;
  sellerIsTopRated?: boolean;
  showTrustIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// Trust level configuration - dark mode aware
const TRUST_CONFIG: Record<TrustLevel, { 
  color: string; 
  bgColor: string; 
  icon: typeof Shield;
  label: string;
}> = {
  authoritative: {
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-500/15 border-amber-500/40',
    icon: ShieldCheck,
    label: 'Authoritative',
  },
  high: {
    color: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-500/15 border-emerald-500/40',
    icon: ShieldCheck,
    label: 'High Trust',
  },
  medium: {
    color: 'text-sky-600 dark:text-sky-400',
    bgColor: 'bg-sky-500/15 border-sky-500/40',
    icon: Shield,
    label: 'Medium Trust',
  },
  low: {
    color: 'text-orange-600 dark:text-orange-400',
    bgColor: 'bg-orange-500/15 border-orange-500/40',
    icon: ShieldAlert,
    label: 'Low Trust',
  },
  untrusted: {
    color: 'text-slate-600 dark:text-slate-400',
    bgColor: 'bg-slate-500/15 border-slate-500/40',
    icon: ShieldQuestion,
    label: 'Untrusted',
  },
};

// Source-specific configuration - dark mode aware
const SOURCE_CONFIG: Record<string, { 
  displayName: string;
  defaultTrust: TrustLevel;
  color: string;
  description: string;
}> = {
  heritage: {
    displayName: 'Heritage',
    defaultTrust: 'authoritative',
    color: 'text-amber-700 dark:text-amber-300',
    description: 'Authoritative for grades, especially NGC/PCGS slabs',
  },
  cng: {
    displayName: 'CNG',
    defaultTrust: 'authoritative',
    color: 'text-blue-700 dark:text-blue-300',
    description: 'Authoritative for catalog references and die axis',
  },
  biddr: {
    displayName: 'Biddr',
    defaultTrust: 'medium',
    color: 'text-teal-700 dark:text-teal-300',
    description: 'Medium trust, varies by sub-house',
  },
  ebay: {
    displayName: 'eBay',
    defaultTrust: 'low',
    color: 'text-slate-700 dark:text-slate-300',
    description: 'Trust prices and images only; metadata is user-generated',
  },
  roma: {
    displayName: 'Roma',
    defaultTrust: 'high',
    color: 'text-purple-700 dark:text-purple-300',
    description: 'High trust professional auction house',
  },
  agora: {
    displayName: 'Agora',
    defaultTrust: 'medium',
    color: 'text-green-700 dark:text-green-300',
    description: 'Medium trust auction aggregator',
  },
};

function normalizeSource(source: string): string {
  const lower = source.toLowerCase();
  if (lower.includes('heritage') || lower.includes('ha.com')) return 'heritage';
  if (lower.includes('cng') || lower.includes('classical numismatic')) return 'cng';
  if (lower.includes('biddr')) return 'biddr';
  if (lower.includes('ebay')) return 'ebay';
  if (lower.includes('roma')) return 'roma';
  if (lower.includes('agora')) return 'agora';
  return lower;
}

export function SourceBadge({
  source,
  trustLevel,
  subHouse,
  sellerUsername,
  sellerFeedbackScore,
  sellerFeedbackPct,
  sellerIsTopRated,
  showTrustIcon = true,
  size = 'md',
  className,
}: SourceBadgeProps) {
  const normalizedSource = normalizeSource(source);
  const sourceConfig = SOURCE_CONFIG[normalizedSource] || {
    displayName: source,
    defaultTrust: 'medium' as TrustLevel,
    color: 'text-gray-400',
    description: 'Unknown source',
  };
  
  const effectiveTrust = trustLevel || sourceConfig.defaultTrust;
  const trustConfig = TRUST_CONFIG[effectiveTrust];
  const TrustIcon = trustConfig.icon;
  
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  };
  
  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
    lg: 'w-4 h-4',
  };
  
  // Build display name
  let displayName = sourceConfig.displayName;
  if (subHouse && normalizedSource === 'biddr') {
    displayName = `${subHouse}`;
  }
  
  // Build tooltip content
  const tooltipContent = (
    <div className="space-y-1.5 max-w-xs">
      <div className="font-medium">{sourceConfig.displayName}</div>
      {subHouse && normalizedSource === 'biddr' && (
        <div className="text-xs text-muted-foreground">Sub-house: {subHouse}</div>
      )}
      <div className="text-xs text-muted-foreground">{sourceConfig.description}</div>
      <div className={cn("text-xs flex items-center gap-1", trustConfig.color)}>
        <TrustIcon className="w-3 h-3" />
        {trustConfig.label}
      </div>
      
      {/* eBay seller info */}
      {normalizedSource === 'ebay' && sellerUsername && (
        <div className="pt-1 border-t border-border/50 space-y-1">
          <div className="flex items-center gap-1 text-xs">
            <User className="w-3 h-3" />
            <span>{sellerUsername}</span>
            {sellerIsTopRated && (
              <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
            )}
          </div>
          {sellerFeedbackScore !== null && sellerFeedbackScore !== undefined && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <TrendingUp className="w-3 h-3" />
              <span>{sellerFeedbackScore.toLocaleString()} feedback</span>
              {sellerFeedbackPct !== null && sellerFeedbackPct !== undefined && (
                <span className={cn(
                  sellerFeedbackPct >= 99 ? 'text-emerald-400' :
                  sellerFeedbackPct >= 95 ? 'text-amber-400' : 'text-red-400'
                )}>
                  ({sellerFeedbackPct.toFixed(1)}%)
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge 
            variant="outline"
            className={cn(
              "border font-semibold cursor-help",
              trustConfig.bgColor,
              sourceConfig.color,
              sizeClasses[size],
              className
            )}
          >
            {showTrustIcon && (
              <TrustIcon className={cn(iconSizes[size], "mr-1", trustConfig.color)} />
            )}
            <span className="text-foreground">{displayName}</span>
            
            {/* eBay seller score inline */}
            {normalizedSource === 'ebay' && sellerFeedbackPct !== null && sellerFeedbackPct !== undefined && (
              <span className={cn(
                "ml-1 font-mono",
                sellerFeedbackPct >= 99 ? 'text-emerald-600 dark:text-emerald-400' :
                sellerFeedbackPct >= 95 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'
              )}>
                {sellerFeedbackPct.toFixed(0)}%
              </span>
            )}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="bg-popover border">
          {tooltipContent}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Trust level indicator without source name - just the icon
 */
export function TrustIndicator({
  trustLevel,
  size = 'md',
  className,
}: {
  trustLevel: TrustLevel;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const config = TRUST_CONFIG[trustLevel];
  const Icon = config.icon;
  
  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={cn("cursor-help", className)}>
            <Icon className={cn(iconSizes[size], config.color)} />
          </span>
        </TooltipTrigger>
        <TooltipContent side="top">
          {config.label}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
