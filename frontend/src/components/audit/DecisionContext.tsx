/**
 * DecisionContext - Contextual help panel for conflict resolution
 * 
 * Provides:
 * - Other auction values for the same coin
 * - Catalog reference values (if available)
 * - Statistical analysis for measurement fields
 * - Field-specific guidance text
 */

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  HelpCircle,
  BookOpen,
  BarChart3,
  AlertTriangle,
  History,
  CheckCircle2,
  Info,
} from "lucide-react";

// ============================================================================
// Field Guidance Configuration
// ============================================================================

export const FIELD_GUIDANCE: Record<string, string> = {
  weight_g: "Weight can vary ±0.1g due to measurement conditions. Differences >0.2g may indicate different dies or wear. NGC/PCGS certified weights are most reliable.",
  diameter_mm: "Diameter varies by measurement point on irregular flans. ±0.5mm is normal. Ancient coins were hand-struck and rarely perfectly round.",
  thickness_mm: "Thickness measurements vary significantly depending on method. This is a low-priority field for verification.",
  die_axis: "Die axis is measured in clock hours (6h = 180°). 6h and 12h are most common for Roman Imperial. ±1h variance is acceptable.",
  grade: "Professional grading services (NGC, PCGS) are authoritative. Heritage NGC grades should be trusted. Raw grades from auction houses vary by expertise.",
  grade_service: "Only change grading service if you have documentation of the certified slab.",
  certification_number: "Certification numbers should match exactly. Any difference indicates a different coin or data entry error.",
  strike_score: "NGC strike scores (1-5) assess sharpness of strike. Higher scores indicate better preservation of design detail.",
  surface_score: "NGC surface scores (1-5) assess surface quality. Lower scores may indicate cleaning, scratches, or corrosion.",
  obverse_legend: "Legends can have variant spellings in different references. Check major catalogs (RIC, RSC) for accepted variants.",
  reverse_legend: "Exergue text (below main design) is often abbreviated differently across references.",
  obverse_description: "Descriptions vary by catalog convention. 'Laureate' vs 'Laureated' are equivalent. Focus on substantive differences.",
  reverse_description: "Reverse descriptions can vary significantly. Trust professional auction houses (Heritage, CNG) for accurate attribution.",
  ruler: "Ruler names should match standard forms. 'Antoninus Pius' and 'Antoninus I' refer to the same emperor.",
  denomination: "Denomination names may vary by language/convention. 'Denarius' and 'AR Denarius' are equivalent.",
  mint: "Mint attributions can be uncertain for ancient coins. Trust academic references (RIC) over auction guesses.",
  primary_reference: "CNG has the most reliable reference attribution. RIC volume numbers matter - ensure correct volume for the period.",
  exergue: "Exergue text is critical for mint attribution. Small differences can indicate different emissions.",
};

// ============================================================================
// Types
// ============================================================================

export interface AuctionValue {
  source: string;
  value: string | number;
  date?: string;
  trustLevel?: number;
}

export interface StatisticalAnalysis {
  mean: number;
  stdDev: number;
  min: number;
  max: number;
  sampleSize: number;
  outlierScore: number;  // How many std devs from mean
}

export interface DecisionContextData {
  // Other auction values for this field/coin
  otherAuctionValues?: AuctionValue[];
  // Catalog reference value (from RIC, RSC, etc.)
  catalogValue?: string | number;
  catalogSource?: string;
  // Statistical analysis (for measurement fields)
  stats?: StatisticalAnalysis;
  // Field guidance
  guidance?: string;
  // Whether this is a critical field
  isCritical?: boolean;
  // Historical values for this coin's field
  previousValues?: Array<{
    value: string | number;
    source: string;
    date: string;
  }>;
}

interface DecisionContextProps {
  fieldName: string;
  currentValue?: string | number | null;  // Currently unused but available for future comparisons
  auctionValue: string | number | null;
  context?: DecisionContextData;
  className?: string;
}

// ============================================================================
// Consensus Calculation
// ============================================================================

function calculateConsensus(
  otherValues: AuctionValue[], 
  targetValue: string | number | null
): { text: string; strength: 'strong' | 'moderate' | 'weak' | 'none' } {
  if (!otherValues.length || targetValue === null) {
    return { text: "No other data available for comparison", strength: 'none' };
  }
  
  const targetStr = String(targetValue).toLowerCase().trim();
  const matches = otherValues.filter(v => {
    const vStr = String(v.value).toLowerCase().trim();
    // For numbers, allow small tolerance
    if (!isNaN(Number(targetValue)) && !isNaN(Number(v.value))) {
      const diff = Math.abs(Number(targetValue) - Number(v.value));
      const avg = (Number(targetValue) + Number(v.value)) / 2;
      return diff / avg < 0.05; // 5% tolerance
    }
    return vStr === targetStr || vStr.includes(targetStr) || targetStr.includes(vStr);
  });
  
  const matchPct = (matches.length / otherValues.length) * 100;
  
  if (matchPct >= 80) {
    return { 
      text: `Strong consensus: ${matches.length}/${otherValues.length} sources agree with auction value`,
      strength: 'strong'
    };
  } else if (matchPct >= 50) {
    return { 
      text: `Moderate consensus: ${matches.length}/${otherValues.length} sources agree`,
      strength: 'moderate'
    };
  } else if (matches.length > 0) {
    return { 
      text: `Weak consensus: only ${matches.length}/${otherValues.length} sources agree`,
      strength: 'weak'
    };
  } else {
    return { 
      text: `No consensus: auction value differs from all ${otherValues.length} other sources`,
      strength: 'none'
    };
  }
}

// ============================================================================
// Component
// ============================================================================

export function DecisionContext({
  fieldName,
  currentValue: _currentValue,  // Available for future use
  auctionValue,
  context,
  className,
}: DecisionContextProps) {
  const guidance = context?.guidance || FIELD_GUIDANCE[fieldName] || 
    "No specific guidance available for this field.";
  
  const consensus = context?.otherAuctionValues?.length 
    ? calculateConsensus(context.otherAuctionValues, auctionValue)
    : null;
  
  const hasContext = !!(
    context?.otherAuctionValues?.length ||
    context?.catalogValue ||
    context?.stats ||
    context?.previousValues?.length
  );
  
  return (
    <Collapsible className={className}>
      <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-full">
        <HelpCircle className="w-4 h-4" />
        <span>Help me decide</span>
        {hasContext && (
          <Badge variant="outline" className="ml-auto text-xs">
            Context available
          </Badge>
        )}
      </CollapsibleTrigger>
      
      <CollapsibleContent className="pt-4 space-y-4">
        {/* Other auction values */}
        {context?.otherAuctionValues && context.otherAuctionValues.length > 0 && (
          <div className="space-y-2">
            <h5 className="text-xs font-medium flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" />
              Other auction records for this coin:
            </h5>
            <div className="flex gap-2 flex-wrap">
              {context.otherAuctionValues.map((av, i) => {
                const isMatch = String(av.value) === String(auctionValue);
                return (
                  <Badge 
                    key={i}
                    variant={isMatch ? "default" : "outline"}
                    className={cn(
                      "text-xs",
                      isMatch && "bg-emerald-500/20 text-emerald-700 border-emerald-500/30"
                    )}
                  >
                    {av.source}: {formatValue(fieldName, av.value)}
                    {av.date && <span className="ml-1 opacity-70">({av.date})</span>}
                  </Badge>
                );
              })}
            </div>
            
            {/* Consensus indicator */}
            {consensus && (
              <p className={cn(
                "text-xs flex items-center gap-1",
                consensus.strength === 'strong' && "text-emerald-600",
                consensus.strength === 'moderate' && "text-blue-600",
                consensus.strength === 'weak' && "text-amber-600",
                consensus.strength === 'none' && "text-red-600"
              )}>
                {consensus.strength === 'strong' && <CheckCircle2 className="w-3 h-3" />}
                {consensus.strength === 'moderate' && <Info className="w-3 h-3" />}
                {consensus.strength === 'weak' && <AlertTriangle className="w-3 h-3" />}
                {consensus.strength === 'none' && <AlertTriangle className="w-3 h-3" />}
                {consensus.text}
              </p>
            )}
          </div>
        )}
        
        {/* Catalog reference */}
        {context?.catalogValue && (
          <div className="flex items-center gap-2 p-2.5 rounded-md bg-amber-500/10 border border-amber-500/30">
            <BookOpen className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span className="text-sm">
              {context.catalogSource || "Catalog reference"}:{" "}
              <strong className="text-amber-700">
                {formatValue(fieldName, context.catalogValue)}
              </strong>
            </span>
          </div>
        )}
        
        {/* Statistical analysis */}
        {context?.stats && (
          <div className="space-y-2">
            <h5 className="text-xs font-medium flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5" />
              Statistical Analysis ({context.stats.sampleSize} samples)
            </h5>
            
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="p-2 rounded bg-muted/50 text-center">
                <div className="text-muted-foreground">Mean</div>
                <div className="font-mono font-medium">
                  {formatValue(fieldName, context.stats.mean)}
                </div>
              </div>
              <div className="p-2 rounded bg-muted/50 text-center">
                <div className="text-muted-foreground">Range</div>
                <div className="font-mono font-medium">
                  {formatValue(fieldName, context.stats.min)} – {formatValue(fieldName, context.stats.max)}
                </div>
              </div>
              <div className="p-2 rounded bg-muted/50 text-center">
                <div className="text-muted-foreground">Std Dev</div>
                <div className="font-mono font-medium">
                  ±{context.stats.stdDev.toFixed(2)}
                </div>
              </div>
            </div>
            
            {/* Outlier warning */}
            {context.stats.outlierScore > 2 && (
              <Alert variant="destructive" className="bg-red-500/10 border-red-500/30">
                <AlertTriangle className="w-4 h-4" />
                <AlertDescription className="text-sm text-red-700">
                  The auction value is {context.stats.outlierScore.toFixed(1)} standard 
                  deviations from the mean – this is unusual for this coin type.
                </AlertDescription>
              </Alert>
            )}
            
            <p className="text-xs text-muted-foreground">
              Typical range: {(context.stats.mean - context.stats.stdDev).toFixed(2)} – {(context.stats.mean + context.stats.stdDev).toFixed(2)}
            </p>
          </div>
        )}
        
        {/* Previous values history */}
        {context?.previousValues && context.previousValues.length > 0 && (
          <div className="space-y-2">
            <h5 className="text-xs font-medium">Previous recorded values:</h5>
            <div className="space-y-1">
              {context.previousValues.slice(0, 5).map((pv, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{pv.date}</span>
                  <span>{formatValue(fieldName, pv.value)}</span>
                  <span className="text-muted-foreground">{pv.source}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Field-specific guidance */}
        <div className="space-y-1.5">
          <h5 className="text-xs font-medium flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5" />
            Field Guidance
          </h5>
          <p className="text-xs text-muted-foreground italic leading-relaxed">
            {guidance}
          </p>
        </div>
        
        {/* Critical field warning */}
        {context?.isCritical && (
          <Alert variant="destructive" className="bg-amber-500/10 border-amber-500/30">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <AlertDescription className="text-sm text-amber-700">
              This is a critical identification field. Changes should be verified 
              carefully against primary references.
            </AlertDescription>
          </Alert>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}

// ============================================================================
// Helpers
// ============================================================================

function formatValue(field: string, value: string | number | null): string {
  if (value === null || value === undefined) return '—';
  
  if (field.includes('weight')) {
    const num = typeof value === 'number' ? value : parseFloat(String(value));
    return isNaN(num) ? String(value) : `${num.toFixed(2)}g`;
  }
  
  if (field.includes('diameter') || field.includes('thickness')) {
    const num = typeof value === 'number' ? value : parseFloat(String(value));
    return isNaN(num) ? String(value) : `${num.toFixed(1)}mm`;
  }
  
  if (field === 'die_axis') {
    return `${value}h`;
  }
  
  return String(value);
}

export default DecisionContext;
