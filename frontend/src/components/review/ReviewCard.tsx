import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, X, ExternalLink, SkipForward } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";

export interface ReviewCardProps {
  id: number;
  coinId: number;
  coinPreview: {
    image?: string | null;
    denomination?: string | null;
    issuer?: string | null;
    category?: string | null;
  };
  field: string;
  currentValue: string;
  suggestedValue: string | null;
  confidence: number | null;
  method: string | null;
  source: string;
  isSelected: boolean;
  onSelect: () => void;
  onApprove: () => void;
  onReject: () => void;
  onSkip?: () => void;
  onViewCoin: () => void;
}

/**
 * ReviewCard - Unified card component for all review types
 * 
 * Displays:
 * - Coin preview (image, ID, denomination)
 * - Field being reviewed
 * - Current vs suggested value
 * - Confidence bar with percentage
 * - Method and source badges
 * - Action buttons (Approve/Reject/Skip)
 */
export function ReviewCard({
  id,
  coinId,
  coinPreview,
  field,
  currentValue,
  suggestedValue,
  confidence,
  method,
  source,
  isSelected,
  onSelect,
  onApprove,
  onReject,
  onSkip,
  onViewCoin,
}: ReviewCardProps) {
  const hasMatch = suggestedValue !== null && confidence !== null;
  const confidencePercent = confidence ? Math.round(confidence * 100) : 0;

  const getConfidenceColor = () => {
    if (!confidence) return "var(--text-tertiary)";
    if (confidence >= 0.9) return "var(--success)";
    if (confidence >= 0.7) return "var(--caution)";
    return "var(--error)";
  };

  const getMethodBadgeVariant = () => {
    if (!method) return "outline";
    const methodMap: Record<string, "default" | "secondary" | "outline"> = {
      exact: "default",
      exact_ci: "default",
      alias: "default",
      fts: "secondary",
      nomisma: "secondary",
      llm: "outline",
      manual: "outline",
    };
    return methodMap[method] || "outline";
  };

  return (
    <Card
      className={cn(
        "transition-all duration-200",
        isSelected && "ring-2 ring-primary ring-offset-2",
        !isSelected && "hover:shadow-md"
      )}
      style={{
        borderLeft: isSelected ? "4px solid var(--primary)" : undefined,
        background: isSelected ? "hsl(217, 91%, 97%)" : undefined,
      }}
    >
      <CardContent className="p-4">
        <div className="flex gap-4">
          {/* Coin Preview Image */}
          <div className="flex-shrink-0">
            {coinPreview.image ? (
              <img
                src={coinPreview.image}
                alt={`Coin ${coinId}`}
                className="w-16 h-16 rounded-md object-cover border border-border"
              />
            ) : (
              <div className="w-16 h-16 rounded-md bg-muted flex items-center justify-center border border-border">
                <span className="text-xs text-muted-foreground">#{coinId}</span>
              </div>
            )}
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Header: Coin ID, Denomination, Issuer */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Link
                    to={`/coins/${coinId}`}
                    className="font-semibold text-sm hover:underline flex items-center gap-1"
                    onClick={(e) => {
                      e.preventDefault();
                      onViewCoin();
                    }}
                  >
                    #{coinId}
                    {coinPreview.denomination && ` · ${coinPreview.denomination}`}
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                  {coinPreview.issuer && (
                    <span className="text-xs text-muted-foreground truncate">
                      {coinPreview.issuer}
                    </span>
                  )}
                </div>
              </div>
              <input
                type="checkbox"
                checked={isSelected}
                onChange={onSelect}
                className="w-4 h-4 rounded border-gray-300"
              />
            </div>

            {/* Field Label */}
            <div className="mb-2">
              <Badge variant="outline" className="text-xs capitalize">
                {field}
              </Badge>
            </div>

            {/* Current vs Suggested */}
            <div className="space-y-2 mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-20">Current:</span>
                <span className="text-sm font-mono text-muted-foreground truncate flex-1">
                  {currentValue || <span className="italic">(empty)</span>}
                </span>
              </div>
              {hasMatch ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-20">Suggested:</span>
                  <span className="text-sm font-medium text-primary flex-1 truncate">
                    {suggestedValue}
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground w-20">Match:</span>
                  <Badge variant="outline" className="text-xs">
                    No match found
                  </Badge>
                </div>
              )}
            </div>

            {/* Confidence Bar */}
            {hasMatch && (
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-muted-foreground">Confidence</span>
                  <span
                    className="text-xs font-semibold"
                    style={{ color: getConfidenceColor() }}
                  >
                    {confidencePercent}%
                  </span>
                </div>
                <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full transition-all duration-300 rounded-full"
                    style={{
                      width: `${confidencePercent}%`,
                      backgroundColor: getConfidenceColor(),
                    }}
                  />
                </div>
              </div>
            )}

            {/* Method and Source */}
            <div className="flex items-center gap-2 mb-3 text-xs text-muted-foreground">
              {method && (
                <Badge variant={getMethodBadgeVariant()} className="text-xs">
                  {method.toUpperCase()}
                </Badge>
              )}
              <span>·</span>
              <span>{source}</span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {onSkip && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-xs"
                  onClick={onSkip}
                >
                  <SkipForward className="w-3 h-3 mr-1" />
                  Skip
                </Button>
              )}
              <div className="flex-1" />
              <Button
                variant="ghost"
                size="sm"
                className="h-8 text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={onReject}
              >
                <X className="w-3 h-3 mr-1" />
                Reject
              </Button>
              {hasMatch && (
                <Button
                  variant="default"
                  size="sm"
                  className="h-8 text-xs bg-green-600 hover:bg-green-700"
                  onClick={onApprove}
                >
                  <Check className="w-3 h-3 mr-1" />
                  Approve
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
