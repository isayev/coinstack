/**
 * EnhancedConflictCard - Complete redesign with inline resolution workflow
 * 
 * Features:
 * - Coin preview with category border
 * - Trust comparison visualization
 * - Field-specific comparators
 * - Decision context (collapsible)
 * - Inline custom value input
 * - Mark as verified option
 * - Resolution notes
 * - Keyboard shortcut support
 */

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import type { Discrepancy, TrustLevel as AuditTrustLevel } from "@/types/audit";
import { SourceBadge } from "./SourceBadge";
import { TrustComparisonBar } from "./TrustComparisonBar";
import { DecisionContext, DecisionContextData } from "./DecisionContext";
import { getFieldComparator } from "./FieldComparators";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Check,
  Shield,
  X,
  ChevronDown,
  ChevronUp,
  Edit,
  ShieldCheck,
  Loader2,
} from "lucide-react";
import { MetalBadge } from "@/components/design-system";

// Trust level to numeric
const TRUST_NUMERIC: Record<AuditTrustLevel, number> = {
  authoritative: 95,
  high: 80,
  medium: 60,
  low: 40,
  untrusted: 20,
};

// Field labels
const FIELD_LABELS: Record<string, string> = {
  weight_g: "Weight",
  diameter_mm: "Diameter",
  thickness_mm: "Thickness",
  die_axis: "Die Axis",
  grade: "Grade",
  grade_service: "Grading Service",
  certification_number: "Cert Number",
  strike_score: "Strike Score",
  surface_score: "Surface Score",
  obverse_legend: "Obverse Legend",
  reverse_legend: "Reverse Legend",
  obverse_description: "Obverse Description",
  reverse_description: "Reverse Description",
  exergue: "Exergue",
  ruler: "Ruler",
  denomination: "Denomination",
  mint: "Mint",
  primary_reference: "Reference",
};

interface CoinData {
  primaryImage?: string | null;
  ruler?: string | null;
  denomination?: string | null;
  metal?: string | null;
  grade?: string | null;
  category?: string | null;
  mintYearStart?: number | null;
  mintYearEnd?: number | null;
}

interface Resolution {
  action: "accept" | "keep" | "custom" | "skip";
  value?: string | number | null;
  markAsVerified?: boolean;
  notes?: string;
}

interface EnhancedConflictCardProps {
  conflict: Discrepancy;
  coinData?: CoinData;
  decisionContext?: DecisionContextData;
  currentSourceTrust?: number;  // Trust level for current value source
  onResolve: (resolution: Resolution) => Promise<void>;
  isProcessing?: boolean;
  isFocused?: boolean;
  isSelected?: boolean;
  onSelect?: (selected: boolean) => void;
  className?: string;
}

export function EnhancedConflictCard({
  conflict,
  coinData,
  decisionContext,
  currentSourceTrust = 50,
  onResolve,
  isProcessing = false,
  isFocused = false,
  isSelected = false,
  onSelect,
  className,
}: EnhancedConflictCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [customValue, setCustomValue] = useState<string>("");
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [markAsVerified, setMarkAsVerified] = useState(false);
  const [notes, setNotes] = useState("");
  const cardRef = useRef<HTMLDivElement>(null);
  
  // Scroll into view when focused
  useEffect(() => {
    if (isFocused && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [isFocused]);
  
  const auctionTrust = TRUST_NUMERIC[conflict.trust_level] || 60;
  const trustWinner = auctionTrust > currentSourceTrust ? "auction" :
                      currentSourceTrust > auctionTrust ? "current" : "tie";
  
  // Determine conflict severity
  const similarity = conflict.similarity ?? 0;
  const getConflictType = () => {
    if (similarity >= 0.9) return "tolerance";
    if (similarity >= 0.5) return "minor";
    return "major";
  };
  const conflictType = getConflictType();
  
  // Get field-specific comparator if available
  const FieldComparator = getFieldComparator(conflict.field_name);
  
  // Get recommendation
  const getRecommendation = () => {
    if (conflict.auto_acceptable) {
      return { label: "Recommended: Accept", variant: "success" as const };
    }
    if (trustWinner === "auction" && auctionTrust >= 80) {
      return { label: "Higher trust", variant: "default" as const };
    }
    if (conflictType === "tolerance") {
      return { label: "Within tolerance", variant: "secondary" as const };
    }
    return null;
  };
  const recommendation = getRecommendation();
  
  const handleResolve = async (action: Resolution["action"], value?: string | number | null) => {
    await onResolve({
      action,
      value,
      markAsVerified,
      notes: notes || undefined,
    });
    setNotes("");
    setCustomValue("");
    setShowCustomInput(false);
  };
  
  const isResolved = conflict.status !== "pending";
  const fieldLabel = FIELD_LABELS[conflict.field_name] || conflict.field_name.replace(/_/g, ' ');
  
  return (
    <Card
      ref={cardRef}
      className={cn(
        "overflow-hidden transition-all duration-200",
        isFocused && "ring-2 ring-primary",
        isSelected && "ring-2 ring-blue-500",
        isResolved && "opacity-60",
        conflictType === "major" && "border-l-4 border-l-red-500",
        conflictType === "minor" && "border-l-4 border-l-amber-500",
        conflictType === "tolerance" && "border-l-4 border-l-emerald-500",
        className
      )}
    >
      {/* Compact Header - Always Visible */}
      <div
        className={cn(
          "p-4 cursor-pointer hover:bg-muted/30 transition-colors",
          expanded && "bg-muted/20"
        )}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-4">
          {/* Selection checkbox */}
          {onSelect && (
            <div onClick={(e) => e.stopPropagation()}>
              <Checkbox
                checked={isSelected}
                onCheckedChange={(checked) => onSelect(!!checked)}
                className="mt-1"
              />
            </div>
          )}
          
          {/* Coin preview */}
          <div className="w-16 h-16 rounded overflow-hidden flex-shrink-0 border">
            {coinData?.primaryImage ? (
              <img
                src={`/api${coinData.primaryImage}`}
                alt=""
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-muted flex items-center justify-center">
                <span className="text-xs text-muted-foreground">No image</span>
              </div>
            )}
          </div>
          
          {/* Conflict summary */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              {coinData?.metal && <MetalBadge metal={coinData.metal} size="xs" />}
              <span className="font-medium text-sm truncate">
                {coinData?.ruler || coinData?.denomination || `Coin #${conflict.coin_id}`}
              </span>
              {recommendation && (
                <Badge 
                  variant="outline" 
                  className={cn(
                    "text-xs",
                    recommendation.variant === "success" && "bg-emerald-500/10 text-emerald-600 border-emerald-500/30",
                    recommendation.variant === "default" && "bg-blue-500/10 text-blue-600 border-blue-500/30",
                    recommendation.variant === "secondary" && "bg-gray-500/10 text-gray-600 border-gray-500/30"
                  )}
                >
                  {recommendation.label}
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-2 text-sm flex-wrap">
              <Badge variant="outline" className="text-xs">
                {fieldLabel}
              </Badge>
              <span className="text-muted-foreground truncate max-w-[100px]">
                {formatValue(conflict.field_name, conflict.current_value)}
              </span>
              <span className="text-muted-foreground">→</span>
              <span className={cn(
                "font-medium truncate max-w-[100px]",
                trustWinner === "auction" && "text-emerald-600"
              )}>
                {formatValue(conflict.field_name, conflict.auction_value)}
              </span>
              <SourceBadge source={conflict.source_house} size="sm" />
            </div>
          </div>
          
          {/* Quick actions */}
          <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50"
                    onClick={() => handleResolve("accept", conflict.auction_value)}
                    disabled={isProcessing || isResolved}
                  >
                    {isProcessing ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Check className="h-4 w-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Accept auction value (A)</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                    onClick={() => handleResolve("keep", conflict.current_value)}
                    disabled={isProcessing || isResolved}
                  >
                    <Shield className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Keep current value (Shift+K)</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleResolve("skip")}
                    disabled={isProcessing || isResolved}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Dismiss (S)</TooltipContent>
              </Tooltip>
            </TooltipProvider>
            
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(!expanded);
              }}
            >
              {expanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
      
      {/* Expanded Content */}
      {expanded && !isResolved && (
        <CardContent className="border-t pt-4 space-y-4">
          {/* Trust comparison */}
          <div className="px-2 py-3 bg-muted/30 rounded-lg">
            <TrustComparisonBar
              current={{ source: "Current value", level: currentSourceTrust }}
              auction={{ source: conflict.source_house, level: auctionTrust }}
            />
          </div>
          
          {/* Field-specific comparison */}
          {FieldComparator && (
            <div className="p-4 border rounded-lg">
              <FieldComparator
                current={conflict.current_value}
                auction={conflict.auction_value}
                context={decisionContext ? {
                  strikeScore: undefined,
                  surfaceScore: undefined,
                  otherValues: decisionContext.otherAuctionValues?.map(v => ({
                    source: v.source,
                    value: v.value,
                  })),
                } : undefined}
              />
            </div>
          )}
          
          {/* Decision context */}
          <DecisionContext
            fieldName={conflict.field_name}
            currentValue={conflict.current_value}
            auctionValue={conflict.auction_value}
            context={decisionContext}
          />
          
          {/* Custom value input */}
          <Collapsible open={showCustomInput} onOpenChange={setShowCustomInput}>
            <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
              <Edit className="w-4 h-4" />
              Enter a different value
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-3">
              <div className="flex gap-2">
                <Input
                  value={customValue}
                  onChange={(e) => setCustomValue(e.target.value)}
                  placeholder={`Enter custom ${fieldLabel.toLowerCase()}`}
                  className="flex-1"
                />
                <Button
                  disabled={!customValue.trim() || isProcessing}
                  onClick={() => handleResolve("custom", customValue)}
                >
                  Apply
                </Button>
              </div>
            </CollapsibleContent>
          </Collapsible>
          
          {/* Mark as verified */}
          <div className="flex items-center gap-2">
            <Checkbox
              id={`verify-${conflict.id}`}
              checked={markAsVerified}
              onCheckedChange={(checked) => setMarkAsVerified(!!checked)}
            />
            <label
              htmlFor={`verify-${conflict.id}`}
              className="text-sm text-muted-foreground cursor-pointer flex items-center gap-1"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Mark as verified (prevents future auto-updates to this field)
            </label>
          </div>
          
          {/* Resolution notes */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              Resolution notes (optional)
            </label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add a note about this resolution..."
              className="h-20 text-sm"
            />
          </div>
          
          {/* Action buttons */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleResolve("skip")}
              disabled={isProcessing}
            >
              <X className="w-4 h-4 mr-2" />
              Dismiss
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleResolve("keep", conflict.current_value)}
              disabled={isProcessing}
            >
              <Shield className="w-4 h-4 mr-2" />
              Keep Current
            </Button>
            <Button
              size="sm"
              onClick={() => handleResolve("accept", conflict.auction_value)}
              disabled={isProcessing}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Check className="w-4 h-4 mr-2" />
              )}
              Accept Auction
            </Button>
          </div>
        </CardContent>
      )}
      
      {/* Resolved state */}
      {isResolved && (
        <CardContent className="border-t pt-3">
          <div className="flex items-center gap-2">
            <Badge
              variant={
                conflict.status === "accepted" ? "default" :
                conflict.status === "rejected" ? "destructive" : "secondary"
              }
            >
              {conflict.status}
            </Badge>
            {conflict.resolution_notes && (
              <span className="text-sm text-muted-foreground">
                {conflict.resolution_notes}
              </span>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

function formatValue(field: string, value: string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '(empty)';
  
  if (field.includes('weight')) {
    const num = parseFloat(value);
    return isNaN(num) ? value : `${num.toFixed(2)}g`;
  }
  
  if (field.includes('diameter') || field.includes('thickness')) {
    const num = parseFloat(value);
    return isNaN(num) ? value : `${num.toFixed(1)}mm`;
  }
  
  if (field === 'die_axis') {
    return `${value}h`;
  }
  
  // Truncate long values
  if (value.length > 30) {
    return value.substring(0, 27) + '...';
  }
  
  return value;
}

export default EnhancedConflictCard;
