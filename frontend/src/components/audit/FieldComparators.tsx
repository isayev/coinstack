/**
 * Field-Specific Comparators
 * 
 * Specialized comparison views for different field types:
 * - WeightComparison: Visual scale with tolerance bands
 * - GradeComparison: Grade scale with position markers
 * - ReferencesComparison: Diff view showing added/removed/modified
 * - MeasurementComparison: Generic for diameter, thickness
 */

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { GradeBadge } from "@/components/design-system";
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Plus,
  Minus,
  Scale,
  Ruler,
} from "lucide-react";

// ============================================================================
// Types
// ============================================================================

interface ComparisonProps {
  current: string | number | null;
  auction: string | number | null;
  context?: {
    strikeScore?: string | null;
    surfaceScore?: string | null;
    otherValues?: Array<{ source: string; value: string | number }>;
  };
}

// ============================================================================
// Weight Comparison
// ============================================================================

interface WeightComparisonProps extends ComparisonProps {
  tolerance?: number;  // Default 5% tolerance
}

export function WeightComparison({ 
  current, 
  auction, 
  tolerance = 0.05,
  context,
}: WeightComparisonProps) {
  const currentNum = typeof current === 'number' ? current : parseFloat(current || '0');
  const auctionNum = typeof auction === 'number' ? auction : parseFloat(auction || '0');
  
  const diff = Math.abs(currentNum - auctionNum);
  const diffPct = currentNum > 0 ? (diff / currentNum) * 100 : 0;
  const withinTolerance = diffPct <= (tolerance * 100);
  
  // Calculate visual scale positions (centered on current value)
  const minScale = currentNum * 0.9;
  const maxScale = currentNum * 1.1;
  const range = maxScale - minScale;
  const currentPos = ((currentNum - minScale) / range) * 100;
  const auctionPos = ((auctionNum - minScale) / range) * 100;
  const toleranceLeft = ((currentNum * (1 - tolerance) - minScale) / range) * 100;
  const toleranceRight = ((currentNum * (1 + tolerance) - minScale) / range) * 100;
  
  return (
    <div className="space-y-4">
      {/* Value cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 border rounded-lg text-center bg-muted/30">
          <div className="flex items-center justify-center gap-2 mb-1">
            <Scale className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Current</span>
          </div>
          <div className="text-2xl font-mono font-bold">
            {currentNum ? `${currentNum.toFixed(2)}g` : '—'}
          </div>
        </div>
        <div className="p-4 border rounded-lg text-center bg-muted/30">
          <div className="flex items-center justify-center gap-2 mb-1">
            <Scale className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Auction</span>
          </div>
          <div className="text-2xl font-mono font-bold">
            {auctionNum ? `${auctionNum.toFixed(2)}g` : '—'}
          </div>
        </div>
      </div>
      
      {/* Difference indicator */}
      <Alert variant={withinTolerance ? "default" : "destructive"} className={cn(
        withinTolerance ? "bg-emerald-500/10 border-emerald-500/30" : "bg-amber-500/10 border-amber-500/30"
      )}>
        <div className="flex items-center gap-2">
          {withinTolerance ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          )}
          <AlertDescription className={cn(
            "text-sm",
            withinTolerance ? "text-emerald-700" : "text-amber-700"
          )}>
            {withinTolerance 
              ? `Difference of ${diff.toFixed(3)}g (${diffPct.toFixed(1)}%) is within normal tolerance`
              : `Difference of ${diff.toFixed(3)}g (${diffPct.toFixed(1)}%) exceeds ${tolerance * 100}% tolerance`
            }
          </AlertDescription>
        </div>
      </Alert>
      
      {/* Visual scale */}
      {currentNum > 0 && auctionNum > 0 && (
        <div className="space-y-2">
          <div className="relative h-6 bg-muted rounded-full overflow-hidden">
            {/* Tolerance band */}
            <div 
              className="absolute inset-y-0 bg-emerald-200/50"
              style={{
                left: `${Math.max(0, toleranceLeft)}%`,
                width: `${Math.min(100, toleranceRight) - Math.max(0, toleranceLeft)}%`,
              }}
            />
            
            {/* Current marker */}
            <div 
              className="absolute top-0 bottom-0 w-1 bg-blue-600 z-10"
              style={{ left: `${Math.min(100, Math.max(0, currentPos))}%` }}
              title={`Current: ${currentNum.toFixed(2)}g`}
            />
            
            {/* Auction marker */}
            <div 
              className="absolute top-0 bottom-0 w-1 bg-orange-500 z-10"
              style={{ left: `${Math.min(100, Math.max(0, auctionPos))}%` }}
              title={`Auction: ${auctionNum.toFixed(2)}g`}
            />
          </div>
          
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{minScale.toFixed(2)}g</span>
            <span className="text-blue-600">{currentNum.toFixed(2)}g (current)</span>
            <span>{maxScale.toFixed(2)}g</span>
          </div>
          
          <div className="flex justify-center gap-4 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-blue-600 rounded" />
              Current
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-orange-500 rounded" />
              Auction
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-emerald-200/50 rounded" />
              Tolerance
            </span>
          </div>
        </div>
      )}
      
      {/* Other auction values if available */}
      {context?.otherValues && context.otherValues.length > 0 && (
        <div className="pt-2 border-t">
          <p className="text-xs font-medium text-muted-foreground mb-2">
            Other auction records:
          </p>
          <div className="flex gap-2 flex-wrap">
            {context.otherValues.map((v, i) => (
              <Badge 
                key={i}
                variant={v.value === auction ? "default" : "outline"}
                className="text-xs"
              >
                {v.source}: {typeof v.value === 'number' ? v.value.toFixed(2) : v.value}g
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Grade Comparison
// ============================================================================

const GRADE_SCALE = [
  { abbr: "P", name: "Poor", position: 0 },
  { abbr: "FR", name: "Fair", position: 8 },
  { abbr: "AG", name: "About Good", position: 15 },
  { abbr: "G", name: "Good", position: 22 },
  { abbr: "VG", name: "Very Good", position: 30 },
  { abbr: "F", name: "Fine", position: 38 },
  { abbr: "VF", name: "Very Fine", position: 50 },
  { abbr: "EF", name: "Extremely Fine", position: 62 },
  { abbr: "AU", name: "About Uncirculated", position: 75 },
  { abbr: "MS", name: "Mint State", position: 90 },
  { abbr: "FDC", name: "Fleur de Coin", position: 100 },
];

function parseGradePosition(grade: string): number {
  const upper = grade.toUpperCase().trim();
  
  // Check for exact matches
  for (const g of GRADE_SCALE) {
    if (upper.startsWith(g.abbr) || upper.includes(g.name.toUpperCase())) {
      // Look for modifiers like + or -
      if (upper.includes('+') || upper.includes('CHOICE')) {
        return Math.min(100, g.position + 5);
      }
      if (upper.includes('-')) {
        return Math.max(0, g.position - 5);
      }
      return g.position;
    }
  }
  
  // Check for NGC/PCGS numeric grades (1-70)
  const numMatch = upper.match(/\b(\d{1,2})\b/);
  if (numMatch) {
    const num = parseInt(numMatch[1], 10);
    if (num >= 1 && num <= 70) {
      return (num / 70) * 100;
    }
  }
  
  return 50; // Default middle if unknown
}

function extractGradingService(grade: string): string | null {
  const upper = grade.toUpperCase();
  if (upper.includes('NGC')) return 'NGC';
  if (upper.includes('PCGS')) return 'PCGS';
  if (upper.includes('ANACS')) return 'ANACS';
  return null;
}

export function GradeComparison({ 
  current, 
  auction,
  context,
}: ComparisonProps) {
  const currentStr = String(current || '');
  const auctionStr = String(auction || '');
  
  const currentPos = parseGradePosition(currentStr);
  const auctionPos = parseGradePosition(auctionStr);
  const currentService = extractGradingService(currentStr);
  const auctionService = extractGradingService(auctionStr);
  
  const diff = Math.abs(currentPos - auctionPos);
  const isSignificant = diff > 15;
  
  return (
    <div className="space-y-4">
      {/* Grade badges */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 border rounded-lg">
          <div className="text-xs text-muted-foreground mb-2">Current Grade</div>
          <GradeBadge grade={currentStr} size="md" />
          {currentService && (
            <Badge variant="outline" className="mt-2 text-xs">
              {currentService}
            </Badge>
          )}
        </div>
        <div className="p-4 border rounded-lg">
          <div className="text-xs text-muted-foreground mb-2">Auction Grade</div>
          <GradeBadge grade={auctionStr} size="md" />
          {auctionService && (
            <Badge variant="outline" className="mt-2 text-xs">
              {auctionService}
            </Badge>
          )}
          {/* NGC scores if available */}
          {context?.strikeScore && context?.surfaceScore && (
            <div className="mt-2 flex gap-2">
              <Badge variant="outline" className="text-xs">
                Strike: {context.strikeScore}
              </Badge>
              <Badge variant="outline" className="text-xs">
                Surface: {context.surfaceScore}
              </Badge>
            </div>
          )}
        </div>
      </div>
      
      {/* Grade scale visualization */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground px-1">
          {GRADE_SCALE.filter((_, i) => i % 2 === 0).map(g => (
            <span key={g.abbr}>{g.abbr}</span>
          ))}
        </div>
        
        <div className="relative h-5 rounded-full overflow-hidden bg-gradient-to-r from-red-500 via-yellow-500 to-green-500">
          {/* Current position marker */}
          <div 
            className="absolute top-0 bottom-0 w-2 bg-blue-600 border-2 border-white rounded-full shadow-md z-10"
            style={{ left: `calc(${currentPos}% - 4px)` }}
            title={`Current: ${currentStr}`}
          />
          
          {/* Auction position marker */}
          <div 
            className="absolute top-0 bottom-0 w-2 bg-orange-500 border-2 border-white rounded-full shadow-md z-10"
            style={{ left: `calc(${auctionPos}% - 4px)` }}
            title={`Auction: ${auctionStr}`}
          />
        </div>
        
        <div className="flex justify-center gap-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-blue-600 rounded-full" />
            Current
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-orange-500 rounded-full" />
            Auction
          </span>
        </div>
      </div>
      
      {/* Analysis */}
      <Alert variant={isSignificant ? "destructive" : "default"} className={cn(
        isSignificant 
          ? "bg-amber-500/10 border-amber-500/30" 
          : "bg-muted/50"
      )}>
        <AlertDescription className="text-sm">
          {isSignificant ? (
            <>
              <AlertTriangle className="w-4 h-4 inline mr-2 text-amber-500" />
              Significant grade difference detected. 
              {auctionService && ` ${auctionService} grades are generally reliable.`}
            </>
          ) : (
            <>
              <CheckCircle2 className="w-4 h-4 inline mr-2 text-emerald-500" />
              Grade difference is minor or within expected variation.
            </>
          )}
        </AlertDescription>
      </Alert>
    </div>
  );
}

// ============================================================================
// References Comparison
// ============================================================================

interface ParsedReference {
  catalog: string;
  number: string;
  normalized: string;
  raw: string;
}

function parseReference(ref: string): ParsedReference {
  const trimmed = ref.trim();
  
  // Common patterns: "RIC II 45", "RSC 123", "Sear 5432"
  const match = trimmed.match(/^([A-Za-z]+)\s*(\d+(?:\.\d+)?(?:\s*\w+)?)/);
  
  if (match) {
    return {
      catalog: match[1].toUpperCase(),
      number: match[2],
      normalized: `${match[1].toUpperCase()} ${match[2]}`.trim(),
      raw: trimmed,
    };
  }
  
  return {
    catalog: '',
    number: '',
    normalized: trimmed,
    raw: trimmed,
  };
}

function diffReferences(
  current: string[], 
  auction: string[]
): {
  added: ParsedReference[];
  removed: ParsedReference[];
  modified: Array<{ current: string; auction: string }>;
  unchanged: ParsedReference[];
} {
  const currentParsed = current.map(parseReference);
  const auctionParsed = auction.map(parseReference);
  
  const added: ParsedReference[] = [];
  const removed: ParsedReference[] = [];
  const modified: Array<{ current: string; auction: string }> = [];
  const unchanged: ParsedReference[] = [];
  
  // Find matches and differences
  for (const ap of auctionParsed) {
    const match = currentParsed.find(cp => 
      cp.catalog === ap.catalog && cp.number === ap.number
    );
    
    if (match) {
      unchanged.push(ap);
    } else {
      // Check if same catalog but different number
      const catalogMatch = currentParsed.find(cp => cp.catalog === ap.catalog);
      if (catalogMatch) {
        modified.push({ current: catalogMatch.raw, auction: ap.raw });
      } else {
        added.push(ap);
      }
    }
  }
  
  // Find removed (in current but not in auction)
  for (const cp of currentParsed) {
    const inAuction = auctionParsed.some(ap => 
      ap.catalog === cp.catalog
    );
    if (!inAuction) {
      removed.push(cp);
    }
  }
  
  return { added, removed, modified, unchanged };
}

export function ReferencesComparison({
  current,
  auction,
}: ComparisonProps) {
  // Parse references (could be string or JSON array)
  const currentRefs: string[] = useMemo(() => {
    if (!current) return [];
    if (Array.isArray(current)) return current;
    try {
      const parsed = JSON.parse(String(current));
      return Array.isArray(parsed) ? parsed : [String(current)];
    } catch {
      return String(current).split(/[,;]/).map(s => s.trim()).filter(Boolean);
    }
  }, [current]);
  
  const auctionRefs: string[] = useMemo(() => {
    if (!auction) return [];
    if (Array.isArray(auction)) return auction;
    try {
      const parsed = JSON.parse(String(auction));
      return Array.isArray(parsed) ? parsed : [String(auction)];
    } catch {
      return String(auction).split(/[,;]/).map(s => s.trim()).filter(Boolean);
    }
  }, [auction]);
  
  const diff = useMemo(() => 
    diffReferences(currentRefs, auctionRefs),
    [currentRefs, auctionRefs]
  );
  
  return (
    <div className="space-y-4">
      {/* Current vs Auction side by side */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-3 border rounded-lg">
          <div className="text-xs text-muted-foreground mb-2">Current References</div>
          <div className="flex flex-wrap gap-1">
            {currentRefs.length > 0 ? currentRefs.map((ref, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                {ref}
              </Badge>
            )) : (
              <span className="text-sm text-muted-foreground italic">None</span>
            )}
          </div>
        </div>
        <div className="p-3 border rounded-lg">
          <div className="text-xs text-muted-foreground mb-2">Auction References</div>
          <div className="flex flex-wrap gap-1">
            {auctionRefs.length > 0 ? auctionRefs.map((ref, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                {ref}
              </Badge>
            )) : (
              <span className="text-sm text-muted-foreground italic">None</span>
            )}
          </div>
        </div>
      </div>
      
      {/* Diff breakdown */}
      <div className="space-y-3">
        {diff.unchanged.length > 0 && (
          <div>
            <h5 className="text-xs font-medium text-muted-foreground mb-1.5 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-500" />
              Matching
            </h5>
            <div className="flex flex-wrap gap-1">
              {diff.unchanged.map((ref, i) => (
                <Badge key={i} variant="outline" className="text-xs bg-emerald-500/10 border-emerald-500/30">
                  {ref.normalized}
                </Badge>
              ))}
            </div>
          </div>
        )}
        
        {diff.added.length > 0 && (
          <div>
            <h5 className="text-xs font-medium text-emerald-600 mb-1.5 flex items-center gap-1">
              <Plus className="w-3 h-3" />
              Would Add
            </h5>
            <div className="flex flex-wrap gap-1">
              {diff.added.map((ref, i) => (
                <Badge key={i} className="text-xs bg-emerald-100 text-emerald-800">
                  + {ref.normalized}
                </Badge>
              ))}
            </div>
          </div>
        )}
        
        {diff.modified.length > 0 && (
          <div>
            <h5 className="text-xs font-medium text-amber-600 mb-1.5 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Different Attribution
            </h5>
            {diff.modified.map((mod, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="line-through text-muted-foreground">{mod.current}</span>
                <ArrowRight className="w-3 h-3" />
                <span className="text-amber-600 font-medium">{mod.auction}</span>
              </div>
            ))}
          </div>
        )}
        
        {diff.removed.length > 0 && (
          <div>
            <h5 className="text-xs font-medium text-red-600 mb-1.5 flex items-center gap-1">
              <Minus className="w-3 h-3" />
              Not in Auction
            </h5>
            <div className="flex flex-wrap gap-1">
              {diff.removed.map((ref, i) => (
                <Badge key={i} variant="outline" className="text-xs text-muted-foreground">
                  {ref.normalized}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Generic Measurement Comparison (Diameter, Thickness)
// ============================================================================

export function MeasurementComparison({
  current,
  auction,
  unit = "mm",
  fieldName = "Measurement",
  tolerance = 0.03,
}: ComparisonProps & {
  unit?: string;
  fieldName?: string;
  tolerance?: number;
}) {
  const currentNum = typeof current === 'number' ? current : parseFloat(current || '0');
  const auctionNum = typeof auction === 'number' ? auction : parseFloat(auction || '0');
  
  const diff = Math.abs(currentNum - auctionNum);
  const diffPct = currentNum > 0 ? (diff / currentNum) * 100 : 0;
  const withinTolerance = diffPct <= (tolerance * 100);
  
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 border rounded-lg text-center bg-muted/30">
          <div className="flex items-center justify-center gap-2 mb-1">
            <Ruler className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Current</span>
          </div>
          <div className="text-2xl font-mono font-bold">
            {currentNum ? `${currentNum.toFixed(1)}${unit}` : '—'}
          </div>
        </div>
        <div className="p-4 border rounded-lg text-center bg-muted/30">
          <div className="flex items-center justify-center gap-2 mb-1">
            <Ruler className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Auction</span>
          </div>
          <div className="text-2xl font-mono font-bold">
            {auctionNum ? `${auctionNum.toFixed(1)}${unit}` : '—'}
          </div>
        </div>
      </div>
      
      <Alert variant={withinTolerance ? "default" : "destructive"} className={cn(
        withinTolerance ? "bg-emerald-500/10 border-emerald-500/30" : "bg-amber-500/10 border-amber-500/30"
      )}>
        <div className="flex items-center gap-2">
          {withinTolerance ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          )}
          <AlertDescription className={cn(
            "text-sm",
            withinTolerance ? "text-emerald-700" : "text-amber-700"
          )}>
            {withinTolerance 
              ? `${fieldName} difference of ${diff.toFixed(2)}${unit} (${diffPct.toFixed(1)}%) is within tolerance`
              : `${fieldName} difference of ${diff.toFixed(2)}${unit} (${diffPct.toFixed(1)}%) exceeds tolerance`
            }
          </AlertDescription>
        </div>
      </Alert>
    </div>
  );
}

// ============================================================================
// Field Comparator Selector
// ============================================================================

export function getFieldComparator(fieldName: string): React.FC<ComparisonProps> | null {
  switch (fieldName) {
    case 'weight_g':
      return WeightComparison;
    case 'grade':
      return GradeComparison;
    case 'primary_reference':
    case 'references':
    case 'catalog_references':
      return ReferencesComparison;
    case 'diameter_mm':
      return (props) => <MeasurementComparison {...props} fieldName="Diameter" unit="mm" tolerance={0.03} />;
    case 'thickness_mm':
      return (props) => <MeasurementComparison {...props} fieldName="Thickness" unit="mm" tolerance={0.1} />;
    default:
      return null;
  }
}
