/**
 * EnrichmentPanel - Catalog enrichment for import preview.
 * 
 * Features:
 * - Shows detected references
 * - Fetches enrichment suggestions from OCRE/CRRO/RPC
 * - Displays diff with selective apply
 * - Shows lookup status for each reference
 */
import { useState } from "react";
import { 
  Sparkles, 
  Loader2, 
  Check, 
  X, 
  ExternalLink,
  AlertCircle,
  CheckCircle2,
  HelpCircle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { 
  useEnrichPreview, 
  EnrichmentField,
  CoinPreviewData,
} from "@/hooks/useImport";
import { cn } from "@/lib/utils";

interface EnrichmentPanelProps {
  references: string[];
  currentData: CoinPreviewData;
  onApplyEnrichment: (updates: Partial<CoinPreviewData>) => void;
}

// Field display names
const FIELD_LABELS: Record<string, string> = {
  issuing_authority: "Issuing Authority",
  denomination: "Denomination",
  mint_name: "Mint",
  mint_year_start: "Mint Year Start",
  mint_year_end: "Mint Year End",
  obverse_description: "Obverse Description",
  obverse_legend: "Obverse Legend",
  reverse_description: "Reverse Description",
  reverse_legend: "Reverse Legend",
  metal: "Metal",
};

// Status badge styles
const STATUS_STYLES: Record<string, { color: string; bg: string; border: string }> = {
  success: { color: "text-green-600", bg: "bg-green-500/10", border: "border-green-500/30" },
  ambiguous: { color: "text-yellow-600", bg: "bg-yellow-500/10", border: "border-yellow-500/30" },
  not_found: { color: "text-gray-500", bg: "bg-gray-500/10", border: "border-gray-500/30" },
  error: { color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/30" },
  parse_error: { color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/30" },
};

export function EnrichmentPanel({
  references,
  currentData,
  onApplyEnrichment,
}: EnrichmentPanelProps) {
  const [selectedFields, setSelectedFields] = useState<Set<string>>(new Set());
  const { mutate: enrich, isPending, data, error, reset } = useEnrichPreview();
  
  const handleEnrich = () => {
    // Build context from current data
    const context: Record<string, unknown> = {};
    if (currentData.issuing_authority) context.ruler = currentData.issuing_authority;
    if (currentData.denomination) context.denomination = currentData.denomination;
    if (currentData.mint_name) context.mint = currentData.mint_name;
    
    enrich({ references, context });
  };
  
  const handleToggleField = (field: string) => {
    setSelectedFields((prev) => {
      const next = new Set(prev);
      if (next.has(field)) {
        next.delete(field);
      } else {
        next.add(field);
      }
      return next;
    });
  };
  
  const handleSelectAll = () => {
    if (data?.suggestions) {
      // Filter to only fields that would be fills (current value is empty)
      const fillableFields = Object.keys(data.suggestions).filter((field) => {
        const currentValue = currentData[field as keyof CoinPreviewData];
        return !currentValue;
      });
      setSelectedFields(new Set(fillableFields));
    }
  };
  
  const handleApply = () => {
    if (!data?.suggestions) return;
    
    const updates: Partial<CoinPreviewData> = {};
    for (const field of selectedFields) {
      const suggestion = data.suggestions[field];
      if (suggestion) {
        (updates as any)[field] = suggestion.value;
      }
    }
    
    onApplyEnrichment(updates);
    setSelectedFields(new Set());
  };
  
  // Count fills vs conflicts
  const getFillsAndConflicts = () => {
    if (!data?.suggestions) return { fills: 0, conflicts: 0 };
    
    let fills = 0;
    let conflicts = 0;
    
    for (const [field, suggestion] of Object.entries(data.suggestions)) {
      const currentValue = currentData[field as keyof CoinPreviewData];
      if (!currentValue) {
        fills++;
      } else if (currentValue !== suggestion.value) {
        conflicts++;
      }
    }
    
    return { fills, conflicts };
  };
  
  const { fills, conflicts } = getFillsAndConflicts();
  
  if (references.length === 0) {
    return null;
  }
  
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-yellow-500" />
          Catalog Enrichment
        </CardTitle>
        <CardDescription>
          Look up references in OCRE, CRRO, and RPC databases to auto-fill fields
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* References list */}
        <div>
          <Label className="text-sm mb-2 block">Detected References</Label>
          <div className="flex flex-wrap gap-1.5">
            {references.map((ref, i) => {
              // Find lookup result for this reference
              const result = data?.lookup_results?.find((r) => r.reference === ref);
              const statusStyle = result ? STATUS_STYLES[result.status] || STATUS_STYLES.error : null;
              
              return (
                <TooltipProvider key={i}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge
                        variant="outline"
                        className={cn(
                          "gap-1",
                          statusStyle && statusStyle.color,
                          statusStyle && statusStyle.bg,
                          statusStyle && statusStyle.border
                        )}
                      >
                        {result?.status === "success" && <CheckCircle2 className="h-3 w-3" />}
                        {result?.status === "ambiguous" && <HelpCircle className="h-3 w-3" />}
                        {result?.status === "not_found" && <X className="h-3 w-3" />}
                        {result?.status === "error" && <AlertCircle className="h-3 w-3" />}
                        {ref}
                        {result?.external_url && (
                          <a
                            href={result.external_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ExternalLink className="h-3 w-3 ml-1" />
                          </a>
                        )}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      {result ? (
                        <div className="text-xs">
                          <p>Status: {result.status}</p>
                          {result.system && <p>System: {result.system.toUpperCase()}</p>}
                          {result.confidence && <p>Confidence: {Math.round(result.confidence * 100)}%</p>}
                          {result.error && <p className="text-red-400">{result.error}</p>}
                        </div>
                      ) : (
                        <p>Click "Enrich" to look up this reference</p>
                      )}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              );
            })}
          </div>
        </div>
        
        {/* Enrich button */}
        {!data && (
          <Button
            onClick={handleEnrich}
            disabled={isPending}
            className="w-full"
            variant="secondary"
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Looking up references...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Enrich from Catalog
              </>
            )}
          </Button>
        )}
        
        {/* Error */}
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-600">
            {error.message}
          </div>
        )}
        
        {/* Results */}
        {data && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="flex items-center gap-4 text-sm">
              <span className="text-green-600">
                <Check className="h-4 w-4 inline mr-1" />
                {fills} fields can be filled
              </span>
              {conflicts > 0 && (
                <span className="text-yellow-600">
                  <AlertCircle className="h-4 w-4 inline mr-1" />
                  {conflicts} conflicts
                </span>
              )}
            </div>
            
            {/* Suggestions list */}
            {Object.keys(data.suggestions).length > 0 ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm">Available Fields</Label>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleSelectAll}
                    className="h-7 text-xs"
                  >
                    Select All Fills
                  </Button>
                </div>
                
                <div className="border rounded-lg divide-y">
                  {Object.entries(data.suggestions).map(([field, suggestion]) => {
                    const currentValue = currentData[field as keyof CoinPreviewData];
                    const isFill = !currentValue;
                    const isConflict = currentValue && currentValue !== suggestion.value;
                    
                    return (
                      <div
                        key={field}
                        className={cn(
                          "p-3 flex items-start gap-3",
                          isConflict && "bg-yellow-500/5"
                        )}
                      >
                        <Checkbox
                          id={field}
                          checked={selectedFields.has(field)}
                          onCheckedChange={() => handleToggleField(field)}
                          disabled={isConflict && !selectedFields.has(field)}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <Label htmlFor={field} className="font-medium">
                              {FIELD_LABELS[field] || field}
                            </Label>
                            {isFill && (
                              <Badge variant="outline" className="text-xs text-green-600 bg-green-500/10 border-green-500/30">
                                Fill
                              </Badge>
                            )}
                            {isConflict && (
                              <Badge variant="outline" className="text-xs text-yellow-600 bg-yellow-500/10 border-yellow-500/30">
                                Conflict
                              </Badge>
                            )}
                          </div>
                          
                          <div className="mt-1 text-sm">
                            <span className="text-green-600 font-medium">
                              {String(suggestion.value)}
                            </span>
                          </div>
                          
                          {isConflict && (
                            <div className="mt-1 text-xs text-muted-foreground">
                              Current: <span className="line-through">{String(currentValue)}</span>
                            </div>
                          )}
                          
                          <div className="mt-1 text-xs text-muted-foreground">
                            Source: {suggestion.source}
                            {suggestion.confidence < 1 && (
                              <span className="ml-2">
                                ({Math.round(suggestion.confidence * 100)}% confidence)
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="p-4 text-center text-muted-foreground">
                No enrichment data found for these references
              </div>
            )}
            
            {/* Apply button */}
            {selectedFields.size > 0 && (
              <div className="flex gap-2">
                <Button onClick={handleApply} className="flex-1">
                  <Check className="h-4 w-4 mr-2" />
                  Apply {selectedFields.size} Field{selectedFields.size > 1 ? "s" : ""}
                </Button>
                <Button variant="outline" onClick={() => setSelectedFields(new Set())}>
                  Clear
                </Button>
              </div>
            )}
            
            {/* Reset */}
            <Button variant="ghost" size="sm" onClick={reset} className="w-full">
              Look Up Again
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
