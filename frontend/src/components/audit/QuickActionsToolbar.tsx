/**
 * QuickActionsToolbar - Sticky bottom bar with smart bulk actions
 * 
 * Features:
 * - Pattern-based action suggestions
 * - Keyboard shortcuts
 * - Selection summary
 */

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { Discrepancy, TrustLevel } from "@/types/audit";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  CheckCheck,
  Shield,
  X,
  TrendingUp,
  MoreHorizontal,
  Flag,
  Download,
  Keyboard,
} from "lucide-react";

// Trust level to numeric
const TRUST_NUMERIC: Record<TrustLevel, number> = {
  authoritative: 100,
  high: 80,
  medium: 60,
  low: 40,
  untrusted: 20,
};

interface SelectionPattern {
  allSameField: boolean;
  field?: string;
  allHigherTrust: boolean;
  allWithinTolerance: boolean;
  count: number;
  highTrustCount: number;
  toleranceCount: number;
}

function analyzeSelectionPatterns(items: Discrepancy[]): SelectionPattern {
  if (items.length === 0) {
    return {
      allSameField: false,
      allHigherTrust: false,
      allWithinTolerance: false,
      count: 0,
      highTrustCount: 0,
      toleranceCount: 0,
    };
  }
  
  const fields = new Set(items.map(d => d.field_name));
  const allSameField = fields.size === 1;
  
  // Count items where auction trust > current (assume current is medium if not specified)
  const higherTrustItems = items.filter(d => 
    (TRUST_NUMERIC[d.trust_level] || 60) >= 80
  );
  
  // Count items within tolerance (similarity >= 0.9)
  const toleranceItems = items.filter(d => 
    (d.similarity ?? 0) >= 0.9
  );
  
  return {
    allSameField,
    field: allSameField ? items[0].field_name : undefined,
    allHigherTrust: higherTrustItems.length === items.length,
    allWithinTolerance: toleranceItems.length === items.length,
    count: items.length,
    highTrustCount: higherTrustItems.length,
    toleranceCount: toleranceItems.length,
  };
}

// Field labels
const FIELD_LABELS: Record<string, string> = {
  weight_g: "Weight",
  diameter_mm: "Diameter",
  grade: "Grade",
  primary_reference: "Reference",
  obverse_legend: "Obverse Legend",
  reverse_legend: "Reverse Legend",
};

export type QuickAction = 
  | "accept-all-auction"
  | "keep-current-all"
  | "accept-higher-trust"
  | "dismiss-tolerance"
  | "flag-for-review"
  | "export-conflicts"
  | "clear-selection";

interface QuickActionsToolbarProps {
  selectedItems: Discrepancy[];
  onAction: (action: QuickAction) => void;
  isProcessing?: boolean;
  className?: string;
}

export function QuickActionsToolbar({
  selectedItems,
  onAction,
  isProcessing = false,
  className,
}: QuickActionsToolbarProps) {
  const patterns = useMemo(() => 
    analyzeSelectionPatterns(selectedItems),
    [selectedItems]
  );
  
  if (selectedItems.length === 0) return null;
  
  const fieldLabel = patterns.field ? (FIELD_LABELS[patterns.field] || patterns.field) : '';
  
  return (
    <div className={cn(
      "fixed bottom-0 left-0 right-0 z-50",
      "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80",
      "border-t shadow-lg",
      className
    )}>
      <div className="container mx-auto py-3 px-4">
        <div className="flex items-center justify-between">
          {/* Selection info */}
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="text-sm font-medium">
              {selectedItems.length} selected
            </Badge>
            
            {patterns.allSameField && (
              <span className="text-sm text-muted-foreground">
                All {fieldLabel} conflicts
              </span>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAction("clear-selection")}
              disabled={isProcessing}
            >
              <X className="w-4 h-4 mr-1" />
              Clear
            </Button>
          </div>
          
          {/* Smart actions */}
          <div className="flex items-center gap-2">
            {/* Pattern-based suggestions */}
            {patterns.allSameField && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onAction("accept-all-auction")}
                      disabled={isProcessing}
                    >
                      <CheckCheck className="w-4 h-4 mr-2" />
                      Accept all {fieldLabel}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    All {patterns.count} items are {fieldLabel} conflicts
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            
            {patterns.highTrustCount > 0 && !patterns.allSameField && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => onAction("accept-higher-trust")}
                      disabled={isProcessing}
                      className="bg-emerald-600 hover:bg-emerald-700"
                    >
                      <TrendingUp className="w-4 h-4 mr-2" />
                      Accept {patterns.highTrustCount} higher-trust
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    Accept values from authoritative/high trust sources
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            
            {patterns.toleranceCount > 0 && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onAction("dismiss-tolerance")}
                      disabled={isProcessing}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Dismiss {patterns.toleranceCount} (within tolerance)
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    Differences are within acceptable tolerance
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            
            {/* Standard actions */}
            {!patterns.allSameField && patterns.highTrustCount === 0 && (
              <>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => onAction("accept-all-auction")}
                  disabled={isProcessing}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  <CheckCheck className="w-4 h-4 mr-2" />
                  Accept All
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onAction("keep-current-all")}
                  disabled={isProcessing}
                >
                  <Shield className="w-4 h-4 mr-2" />
                  Keep All Current
                </Button>
              </>
            )}
            
            {/* More actions dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" disabled={isProcessing}>
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onAction("keep-current-all")}>
                  <Shield className="w-4 h-4 mr-2" />
                  Keep all current values
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onAction("flag-for-review")}>
                  <Flag className="w-4 h-4 mr-2" />
                  Flag all for later review
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onAction("export-conflicts")}>
                  <Download className="w-4 h-4 mr-2" />
                  Export conflicts to CSV
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        
        {/* Keyboard shortcuts hint */}
        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
          <Keyboard className="w-3 h-3" />
          <span><kbd className="px-1 py-0.5 bg-muted rounded text-xs">A</kbd> Accept auction</span>
          <span><kbd className="px-1 py-0.5 bg-muted rounded text-xs">K</kbd> Keep current</span>
          <span><kbd className="px-1 py-0.5 bg-muted rounded text-xs">S</kbd> Skip/dismiss</span>
          <span><kbd className="px-1 py-0.5 bg-muted rounded text-xs">Space</kbd> Toggle select</span>
          <span><kbd className="px-1 py-0.5 bg-muted rounded text-xs">↑↓</kbd> Navigate</span>
          <span><kbd className="px-1 py-0.5 bg-muted rounded text-xs">?</kbd> Help</span>
        </div>
      </div>
    </div>
  );
}

export default QuickActionsToolbar;
