import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2, Check, X, AlertTriangle } from "lucide-react";
import { useEnrichCoin, EnrichmentDiff, Conflict } from "@/hooks/useCatalog";

interface CompareDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  coinId: number;
  diff: EnrichmentDiff | null;
  onApply: (applyConflicts: string[]) => void;
  isApplying: boolean;
}

export function CompareDrawer({
  open,
  onOpenChange,
  coinId,
  diff,
  onApply,
  isApplying,
}: CompareDrawerProps) {
  const [selectedConflicts, setSelectedConflicts] = useState<string[]>([]);
  
  const toggleConflict = (field: string) => {
    setSelectedConflicts(prev => 
      prev.includes(field) 
        ? prev.filter(f => f !== field)
        : [...prev, field]
    );
  };
  
  const handleApply = () => {
    onApply(selectedConflicts);
  };
  
  if (!diff) return null;
  
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[600px] sm:max-w-[600px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Compare with Catalog</SheetTitle>
          <SheetDescription>
            Review changes from catalog data before applying
          </SheetDescription>
        </SheetHeader>
        
        <div className="mt-6 space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-4 p-4 rounded-lg bg-muted">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{diff.fill_count}</div>
              <div className="text-sm text-muted-foreground">To fill</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{diff.conflict_count}</div>
              <div className="text-sm text-muted-foreground">Conflicts</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-muted-foreground">{diff.unchanged_count}</div>
              <div className="text-sm text-muted-foreground">Unchanged</div>
            </div>
          </div>
          
          {/* Fills section */}
          {diff.fill_count > 0 && (
            <div>
              <h3 className="font-semibold text-green-600 mb-3 flex items-center gap-2">
                <Check className="w-4 h-4" />
                Fields to fill (auto-applied)
              </h3>
              <div className="space-y-2">
                {Object.entries(diff.fills).map(([field, value]) => (
                  <div 
                    key={field}
                    className="grid grid-cols-2 gap-4 p-3 rounded-lg border"
                  >
                    <div>
                      <div className="text-sm font-medium">{formatFieldName(field)}</div>
                      <div className="text-sm text-muted-foreground">—</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium">Catalog</div>
                      <div className="text-sm text-green-600">{String(value)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Conflicts section */}
          {diff.conflict_count > 0 && (
            <div>
              <h3 className="font-semibold text-yellow-600 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Conflicts (select to override)
              </h3>
              <div className="space-y-2">
                {Object.entries(diff.conflicts).map(([field, conflict]) => (
                  <ConflictRow
                    key={field}
                    field={field}
                    conflict={conflict as Conflict}
                    selected={selectedConflicts.includes(field)}
                    onToggle={() => toggleConflict(field)}
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* Unchanged section */}
          {diff.unchanged_count > 0 && (
            <div>
              <h3 className="font-semibold text-muted-foreground mb-3 flex items-center gap-2">
                <Check className="w-4 h-4" />
                Already matching
              </h3>
              <div className="flex flex-wrap gap-2">
                {diff.unchanged.map(field => (
                  <Badge key={field} variant="outline">
                    {formatFieldName(field)}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          
          {/* No changes */}
          {!diff.has_changes && (
            <div className="text-center p-8 text-muted-foreground">
              <Check className="w-12 h-12 mx-auto mb-4 text-green-500" />
              <p>Your data already matches the catalog.</p>
              <p className="text-sm">No changes needed.</p>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            {diff.has_changes && (
              <Button
                className="flex-1"
                onClick={handleApply}
                disabled={isApplying}
              >
                {isApplying ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : null}
                Apply {diff.fill_count + selectedConflicts.length} changes
              </Button>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

// Conflict row component
function ConflictRow({
  field,
  conflict,
  selected,
  onToggle,
}: {
  field: string;
  conflict: Conflict;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <div 
      className={`grid grid-cols-[auto_1fr_1fr] gap-4 p-3 rounded-lg border cursor-pointer transition-colors ${
        selected ? "border-yellow-500 bg-yellow-50 dark:bg-yellow-950" : ""
      }`}
      onClick={onToggle}
    >
      <div className="flex items-center">
        <Checkbox checked={selected} />
      </div>
      <div>
        <div className="text-sm font-medium">{formatFieldName(field)}</div>
        <div className="text-sm">
          <span className="text-muted-foreground">Current: </span>
          {String(conflict.current)}
        </div>
      </div>
      <div>
        <div className="text-sm font-medium">Catalog</div>
        <div className="text-sm text-yellow-600">
          {String(conflict.catalog)}
        </div>
        {conflict.note && (
          <div className="text-xs text-muted-foreground mt-1">
            {conflict.note}
          </div>
        )}
      </div>
    </div>
  );
}

// Helper to format field names
function formatFieldName(field: string): string {
  return field
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());
}
