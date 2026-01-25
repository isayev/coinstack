import { useState } from "react";
import { useExpandLegend } from "@/hooks/useLegend";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Loader2, Check, X, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface LegendInputProps {
  value: string;
  expandedValue?: string;
  onChange: (value: string) => void;
  onExpandedChange?: (value: string) => void;
  side: "obverse" | "reverse";
  placeholder?: string;
  label?: string;
  className?: string;
}

export function LegendInput({
  value,
  expandedValue,
  onChange,
  onExpandedChange,
  side,
  placeholder = "Enter legend...",
  label,
  className,
}: LegendInputProps) {
  const [showExpansion, setShowExpansion] = useState(false);
  const [editingExpansion, setEditingExpansion] = useState(false);
  const [localExpansion, setLocalExpansion] = useState(expandedValue || "");
  
  const expandMutation = useExpandLegend();
  
  const handleExpand = async () => {
    if (!value.trim()) return;
    
    try {
      const result = await expandMutation.mutateAsync({
        text: value,
        side: side,
      });
      
      setLocalExpansion(result.expanded);
      setShowExpansion(true);
    } catch (error) {
      console.error("Failed to expand legend:", error);
    }
  };
  
  const handleAccept = () => {
    if (onExpandedChange && localExpansion) {
      onExpandedChange(localExpansion);
    }
    setEditingExpansion(false);
  };
  
  const handleReject = () => {
    setLocalExpansion(expandedValue || "");
    setShowExpansion(false);
  };
  
  const confidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return "bg-green-500/10 text-green-600 border-green-500/20";
    if (confidence >= 0.7) return "bg-yellow-500/10 text-yellow-600 border-yellow-500/20";
    return "bg-red-500/10 text-red-600 border-red-500/20";
  };

  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label className="text-sm font-medium">{label}</label>
      )}
      
      {/* Main input with expand button */}
      <div className="flex gap-2">
        <Input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="font-mono text-sm flex-1"
        />
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={handleExpand}
          disabled={!value.trim() || expandMutation.isPending}
          title="Expand legend abbreviations"
        >
          {expandMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
        </Button>
      </div>
      
      {/* Expansion result */}
      {showExpansion && expandMutation.data && (
        <div className="p-3 bg-muted/50 rounded-lg border space-y-2">
          {/* Header with confidence */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge 
                variant="outline" 
                className={cn("text-xs", confidenceColor(expandMutation.data.confidence))}
              >
                {Math.round(expandMutation.data.confidence * 100)}% confidence
              </Badge>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowExpansion(false)}
              className="h-6 w-6 p-0"
            >
              {showExpansion ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
          </div>
          
          {/* Expanded text */}
          {editingExpansion ? (
            <Input
              value={localExpansion}
              onChange={(e) => setLocalExpansion(e.target.value)}
              className="text-sm"
              autoFocus
            />
          ) : (
            <p 
              className="text-sm cursor-pointer hover:bg-muted/50 p-1 rounded"
              onClick={() => setEditingExpansion(true)}
              title="Click to edit"
            >
              {localExpansion}
            </p>
          )}
          
          {/* Action buttons */}
          <div className="flex gap-2 pt-1">
            <Button
              type="button"
              size="sm"
              onClick={handleAccept}
              className="flex-1"
            >
              <Check className="w-3 h-3 mr-1" />
              Accept
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleReject}
              className="flex-1"
            >
              <X className="w-3 h-3 mr-1" />
              Dismiss
            </Button>
          </div>
        </div>
      )}
      
      {/* Show existing expansion if available */}
      {!showExpansion && expandedValue && (
        <p className="text-xs text-muted-foreground pl-1">
          Expanded: {expandedValue}
        </p>
      )}
    </div>
  );
}