import { Link } from "react-router-dom";
import { useState } from "react";
import {
  useLLMSuggestions,
  useDismissLLMSuggestion,
  type LLMSuggestionItem,
} from "@/hooks/useAudit";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Loader2,
  ExternalLink,
  X,
  Sparkles,
  BookOpen,
  Gem,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  XCircle,
  Calendar,
  MapPin,
  ScrollText,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

function RarityBadge({ code, description }: { code: string | null; description: string | null }) {
  if (!code && !description) return null;
  
  const colors: Record<string, string> = {
    C: "bg-slate-500/15 text-slate-600 dark:text-slate-400",
    S: "bg-blue-500/15 text-blue-600 dark:text-blue-400",
    R1: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
    R2: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
    R3: "bg-orange-500/15 text-orange-600 dark:text-orange-400",
    R4: "bg-red-500/15 text-red-600 dark:text-red-400",
    R5: "bg-red-500/15 text-red-600 dark:text-red-400",
    RR: "bg-purple-500/15 text-purple-600 dark:text-purple-400",
    RRR: "bg-purple-500/15 text-purple-600 dark:text-purple-400",
    UNIQUE: "bg-pink-500/15 text-pink-600 dark:text-pink-400",
  };
  
  const colorClass = code ? colors[code] || colors.C : colors.C;
  
  return (
    <Badge variant="outline" className={colorClass}>
      <Gem className="w-3 h-3 mr-1" />
      {code || "?"} - {description || "Unknown"}
    </Badge>
  );
}

function ValidationBadge({ 
  status, 
  confidence 
}: { 
  status: "matches" | "partial_match" | "mismatch" | "unknown";
  confidence: number;
}) {
  const config = {
    matches: {
      icon: CheckCircle2,
      className: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/40",
      label: "Matches",
    },
    partial_match: {
      icon: AlertCircle,
      className: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/40",
      label: "Partial",
    },
    mismatch: {
      icon: XCircle,
      className: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/40",
      label: "Mismatch",
    },
    unknown: {
      icon: HelpCircle,
      className: "bg-slate-500/15 text-slate-700 dark:text-slate-400 border-slate-500/40",
      label: "Unknown",
    },
  };
  
  const { icon: Icon, className, label } = config[status];
  
  return (
    <Badge variant="outline" className={cn("text-xs", className)}>
      <Icon className="w-3 h-3 mr-1" />
      {label} ({Math.round(confidence * 100)}%)
    </Badge>
  );
}

function ReferenceBadge({ 
  ref, 
  validation 
}: { 
  ref: string;
  validation?: {
    validation_status: "matches" | "partial_match" | "mismatch" | "unknown";
    confidence: number;
    parsed_catalog: string | null;
    match_reason: string | null;
  };
}) {
  const status = validation?.validation_status || "unknown";
  const confidence = validation?.confidence || 0;
  
  const statusColors: Record<string, string> = {
    matches: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/30",
    partial_match: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30",
    mismatch: "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/30",
    unknown: "bg-slate-500/10 text-slate-700 dark:text-slate-400 border-slate-500/30",
  };
  
  return (
    <div className="flex items-center gap-2">
      <Badge 
        variant="outline" 
        className={cn("text-xs", statusColors[status])}
        title={validation?.match_reason || undefined}
      >
        <BookOpen className="w-3 h-3 mr-1" />
        {ref}
      </Badge>
      {validation && (
        <ValidationBadge status={status} confidence={confidence} />
      )}
    </div>
  );
}

function SuggestionRow({ item }: { item: LLMSuggestionItem }) {
  const [isOpen, setIsOpen] = useState(false);
  const dismissMutation = useDismissLLMSuggestion();
  
  const handleDismiss = async () => {
    try {
      await dismissMutation.mutateAsync({ coinId: item.coin_id });
      toast.success(`Dismissed suggestions for coin #${item.coin_id}`);
    } catch {
      toast.error("Failed to dismiss suggestions");
    }
  };
  
  const hasReferences = item.suggested_references.length > 0;
  const hasRarity = item.rarity_info !== null;
  const hasDetails = item.mint || item.year_start || item.obverse_legend || item.reverse_legend;
  
  // Format date range
  const dateRange = item.year_start !== null || item.year_end !== null
    ? `${item.year_start || "?"}${item.year_start !== item.year_end ? ` - ${item.year_end || "?"}` : ""}`
    : null;
  
  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <>
        <TableRow>
          <TableCell className="w-[100px]">
            <div className="flex items-center gap-2">
              {hasDetails && (
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    {isOpen ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </Button>
                </CollapsibleTrigger>
              )}
              <Link
                to={`/coins/${item.coin_id}`}
                className="flex items-center gap-1 text-primary hover:underline font-medium"
              >
                #{item.coin_id}
                <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          </TableCell>
          <TableCell className="max-w-[150px]">
            <div className="space-y-0.5">
              <div className="font-medium truncate">
                {item.issuer || <span className="text-muted-foreground">-</span>}
              </div>
              {item.mint && (
                <div className="text-xs text-muted-foreground flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {item.mint}
                </div>
              )}
            </div>
          </TableCell>
          <TableCell className="max-w-[120px]">
            <div className="space-y-0.5">
              <div className="truncate">
                {item.denomination || <span className="text-muted-foreground">-</span>}
              </div>
              {dateRange && (
                <div className="text-xs text-muted-foreground flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {dateRange}
                </div>
              )}
            </div>
          </TableCell>
          <TableCell className="min-w-[300px]">
            {hasReferences ? (
              <div className="space-y-2">
                {item.suggested_references.map((ref, idx) => {
                  const validation = item.validated_references?.[idx];
                  return (
                    <ReferenceBadge 
                      key={idx} 
                      ref={ref} 
                      validation={validation}
                    />
                  );
                })}
                {item.existing_references.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-border/50">
                    <div className="text-xs text-muted-foreground mb-1">Existing:</div>
                    <div className="flex flex-wrap gap-1">
                      {item.existing_references.map((ref, idx) => (
                        <Badge 
                          key={idx} 
                          variant="outline" 
                          className="text-xs bg-slate-500/5 text-slate-600 dark:text-slate-400"
                        >
                          {ref}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <span className="text-muted-foreground text-sm">None</span>
            )}
          </TableCell>
          <TableCell>
            {hasRarity && item.rarity_info ? (
              <div className="space-y-1">
                <RarityBadge 
                  code={item.rarity_info.rarity_code} 
                  description={item.rarity_info.rarity_description} 
                />
                {item.rarity_info.source && (
                  <div className="text-xs text-muted-foreground truncate max-w-[200px]" title={item.rarity_info.source}>
                    Source: {item.rarity_info.source}
                  </div>
                )}
              </div>
            ) : (
              <span className="text-muted-foreground text-sm">None</span>
            )}
          </TableCell>
          <TableCell className="text-right w-[80px]">
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={handleDismiss}
              disabled={dismissMutation.isPending}
              title="Dismiss all suggestions for this coin"
            >
              {dismissMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <X className="h-4 w-4" />
              )}
            </Button>
          </TableCell>
        </TableRow>
        {hasDetails && (
          <CollapsibleContent asChild>
            <TableRow>
              <TableCell colSpan={6} className="bg-muted/30">
                <div className="py-3 px-4 space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {item.category && (
                      <div>
                        <span className="text-muted-foreground">Category:</span>{" "}
                        <span className="font-medium">{item.category}</span>
                      </div>
                    )}
                    {item.year_start !== null && (
                      <div>
                        <span className="text-muted-foreground">Date Range:</span>{" "}
                        <span className="font-medium">{dateRange}</span>
                      </div>
                    )}
                  </div>
                  {(item.obverse_legend || item.reverse_legend) && (
                    <div className="space-y-2 pt-2 border-t border-border/50">
                      {item.obverse_legend && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                            <ScrollText className="h-3 w-3" />
                            Obverse Legend:
                          </div>
                          <div className="text-sm font-mono bg-background/50 p-2 rounded border border-border/50">
                            {item.obverse_legend}
                          </div>
                        </div>
                      )}
                      {item.reverse_legend && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                            <ScrollText className="h-3 w-3" />
                            Reverse Legend:
                          </div>
                          <div className="text-sm font-mono bg-background/50 p-2 rounded border border-border/50">
                            {item.reverse_legend}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </TableCell>
            </TableRow>
          </CollapsibleContent>
        )}
      </>
    </Collapsible>
  );
}

export function LLMReviewTab() {
  const { data, isLoading, refetch } = useLLMSuggestions();
  
  const items = data?.items || [];
  const total = data?.total || 0;
  
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                LLM Suggestions
              </CardTitle>
              <CardDescription>
                Review AI-suggested catalog references and rarity assessments
              </CardDescription>
            </div>
            <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-30" />
              <p className="text-lg font-medium">No LLM suggestions pending</p>
              <p className="text-sm mt-1">
                Generate historical context for coins to get AI suggestions
              </p>
            </div>
          ) : (
            <>
              <div className="mb-4 text-sm text-muted-foreground">
                {total} coin{total !== 1 ? "s" : ""} with pending suggestions
              </div>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[100px]">Coin</TableHead>
                      <TableHead>Issuer / Mint</TableHead>
                      <TableHead>Type / Date</TableHead>
                      <TableHead className="min-w-[300px]">Suggested References</TableHead>
                      <TableHead>Suggested Rarity</TableHead>
                      <TableHead className="text-right w-[80px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((item) => (
                      <SuggestionRow key={item.coin_id} item={item} />
                    ))}
                  </TableBody>
                </Table>
              </div>
            </>
          )}
        </CardContent>
      </Card>
      
      <Card className="bg-muted/30">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-primary mt-0.5" />
            <div className="text-sm">
              <p className="font-medium">How LLM suggestions work</p>
              <p className="text-muted-foreground mt-1">
                When you generate historical context for a coin, the AI analyzes numismatic 
                catalogs and sources. It identifies catalog references (like RIC, RPC) not 
                yet in your database and assesses coin rarity. Review these suggestions and 
                add them to your coins via the coin detail page, or dismiss them here.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
