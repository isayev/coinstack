import { useState, useMemo } from "react";
import { useLLMSuggestions, useDismissLLMSuggestion, useApproveLLMSuggestion } from "@/hooks/useAudit";
import { useTranscribeLegendForCoin, useIdentifyCoinForCoin } from "@/hooks/useLLM";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, ArrowUpDown, Loader2, Sparkles, BookOpen, Gem, ScrollText, Search } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ReviewCard, ReviewEmptyState, ReviewBulkActionsBar } from "@/components/review";
import { useReviewUndo } from "@/hooks/useReviewUndo";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "sonner";

type SortField = "confidence" | "coin_id";
type SortDirection = "asc" | "desc";

/**
 * AIReviewTab - Review AI suggestions (catalog references & rarity)
 * 
 * Features:
 * - Card-based layout using unified ReviewCard
 * - Default sort: Confidence ASC
 * - Expandable details for references
 * - Batch dismiss functionality
 * - Per-tab undo stack
 */
export function AIReviewTab() {
  const navigate = useNavigate();
  const { pushAction } = useReviewUndo();
  const { data, isLoading, refetch } = useLLMSuggestions();
  const dismissMutation = useDismissLLMSuggestion();
  const approveMutation = useApproveLLMSuggestion();
  const transcribeMutation = useTranscribeLegendForCoin();
  const identifyMutation = useIdentifyCoinForCoin();
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [sortField, setSortField] = useState<SortField>("coin_id");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const items = data?.items || [];
  // Total count available via: data?.total || 0

  // Fetch coin data for previews
  const coinIds = useMemo(() => items.map((item) => item.coin_id), [items]);
  const { data: coinsData } = useQuery({
    queryKey: ["coins", "preview", coinIds],
    queryFn: async () => {
      if (coinIds.length === 0) return {};
      const response = await api.get("/api/v2/coins", {
        params: { ids: coinIds.join(","), limit: 200 },
      });
      const coins = response.data.items || [];
      return Object.fromEntries(coins.map((c: any) => [c.id, c]));
    },
    enabled: coinIds.length > 0,
  });

  const hasDesign = (i: (typeof items)[0]) => {
    const d = i.suggested_design;
    return !!d && [d.obverse_legend, d.reverse_legend, d.exergue, d.obverse_description, d.reverse_description].some((v) => v != null && v !== "");
  };
  const hasAttribution = (i: (typeof items)[0]) => {
    const a = i.suggested_attribution;
    return !!a && (!!a.issuer || !!a.mint || !!a.denomination || a.year_start != null || a.year_end != null);
  };

  // Sorted items
  const sortedItems = useMemo(() => {
    const sorted = [...items].sort((a, b) => {
      let comparison = 0;
      if (sortField === "coin_id") {
        comparison = a.coin_id - b.coin_id;
      } else {
        const aConf = a.suggested_references.length + (a.rarity_info ? 1 : 0) + (hasDesign(a) ? 1 : 0) + (hasAttribution(a) ? 1 : 0);
        const bConf = b.suggested_references.length + (b.rarity_info ? 1 : 0) + (hasDesign(b) ? 1 : 0) + (hasAttribution(b) ? 1 : 0);
        comparison = aConf - bConf;
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });
    return sorted;
  }, [items, sortField, sortDirection]);

  const handleDismiss = async (coinId: number) => {
    try {
      await dismissMutation.mutateAsync({ coinId });
      toast.success(`Dismissed suggestions for coin #${coinId}`);
      pushAction({
        type: "reject",
        itemIds: [coinId],
        tab: "ai",
        undoFn: async () => {
          toast.info("Dismiss action cannot be undone");
        },
      });
    } catch {
      toast.error("Failed to dismiss suggestions");
    }
  };

  const handleApprove = async (coinId: number) => {
    try {
      const res = await approveMutation.mutateAsync({ coinId });
      const parts: string[] = [];
      if (res.applied_rarity) parts.push("rarity");
      if (res.applied_references) parts.push(`${res.applied_references} reference(s)`);
      if (res.applied_design) parts.push("design/legends");
      if (res.applied_attribution) parts.push("attribution");
      toast.success(
        parts.length
          ? `Applied ${parts.join(" and ")} to coin #${coinId}`
          : `Approved suggestions for coin #${coinId}`
      );
      pushAction({
        type: "approve",
        itemIds: [coinId],
        tab: "ai",
        undoFn: async () => {
          toast.info("Approved suggestions cannot be undone");
        },
      });
    } catch {
      toast.error("Failed to apply suggestions");
    }
  };

  const handleBulkDismiss = async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;
    try {
      await Promise.all(ids.map((id) => dismissMutation.mutateAsync({ coinId: id })));
      toast.success(`Dismissed ${ids.length} suggestion(s)`);
      setSelectedIds(new Set());
    } catch {
      toast.error("Failed to dismiss some suggestions");
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (items.length === 0) {
    return <ReviewEmptyState variant="ai" />;
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Select value={sortField} onValueChange={(v) => setSortField(v as SortField)}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="coin_id">Coin ID</SelectItem>
              <SelectItem value="confidence">Suggestion Count</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSortDirection((d) => (d === "asc" ? "desc" : "asc"))}
          >
            <ArrowUpDown className="w-4 h-4 mr-2" />
            {sortDirection === "asc" ? "Asc" : "Desc"}
          </Button>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Info Card */}
      <div className="bg-muted/30 rounded-lg p-4 flex items-start gap-3">
        <Sparkles className="w-5 h-5 text-primary mt-0.5" />
        <div className="text-sm">
          <p className="font-medium">AI Suggestions</p>
          <p className="text-muted-foreground mt-1">
            Review catalog references and rarity assessments suggested by AI. "Approve" applies
            suggested rarity and catalog references to the coin and removes the item from the queue.
            "Reject" dismisses without applying. Use the coin link to open the coin page.
          </p>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 gap-4">
        {sortedItems.map((item) => {
          const coin = coinsData?.[item.coin_id];
          const hasReferences = item.suggested_references.length > 0;
          const hasRarity = item.rarity_info !== null;
          const hasDesignForItem = hasDesign(item);
          const hasAttributionForItem = hasAttribution(item);
          
          // Build suggested value string
          const suggestedParts: string[] = [];
          if (hasReferences) {
            suggestedParts.push(`${item.suggested_references.length} reference(s)`);
          }
          if (hasRarity && item.rarity_info) {
            suggestedParts.push(`Rarity: ${item.rarity_info.rarity_code || item.rarity_info.rarity_description || "Unknown"}`);
          }
          if (hasDesignForItem) suggestedParts.push("Legends/Design");
          if (hasAttributionForItem) suggestedParts.push("Attribution");
          const suggestedValue = suggestedParts.length > 0 ? suggestedParts.join(", ") : null;

          return (
            <div key={item.coin_id} className="relative">
              <ReviewCard
                id={item.coin_id}
                coinId={item.coin_id}
                coinPreview={{
                  image: coin?.images?.[0]?.url || null,
                  denomination: item.denomination || coin?.denomination || null,
                  issuer: item.issuer || coin?.attribution?.issuer || null,
                  category: coin?.category || null,
                }}
                field="AI Suggestions"
                currentValue="None"
                suggestedValue={suggestedValue}
                confidence={hasReferences || hasRarity || hasDesignForItem || hasAttributionForItem ? 0.85 : null}
                method="llm"
                source="AI Analysis"
                isSelected={selectedIds.has(item.coin_id)}
                onSelect={() => toggleSelect(item.coin_id)}
                onApprove={() => handleApprove(item.coin_id)}
                onReject={() => handleDismiss(item.coin_id)}
                onViewCoin={() => navigate(`/coins/${item.coin_id}`)}
              />
              
              {/* Expanded Details */}
              {(hasReferences || hasRarity || hasDesignForItem || hasAttributionForItem) && (
                <div className="mt-2 ml-20 pl-4 border-l-2 border-muted space-y-2">
                  {hasReferences && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                        <BookOpen className="w-3 h-3" />
                        Suggested References:
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {item.suggested_references.map((ref, idx) => (
                          <Badge
                            key={idx}
                            variant="outline"
                            className="border-[var(--text-link)]/40"
                            style={{ background: 'var(--accent-ai-subtle)', color: 'var(--text-link)' }}
                          >
                            {ref}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {hasRarity && item.rarity_info && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                        <Gem className="w-3 h-3" />
                        Suggested Rarity:
                      </div>
                      <Badge
                        variant="outline"
                        className="border-[var(--accent-ai)]/40"
                        style={{ background: 'var(--accent-ai-subtle)', color: 'var(--accent-ai)' }}
                      >
                        {item.rarity_info.rarity_code || "?"} - {item.rarity_info.rarity_description || "Unknown"}
                      </Badge>
                      {item.rarity_info.source && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Source: {item.rarity_info.source}
                        </p>
                      )}
                    </div>
                  )}
                  {hasDesignForItem && item.suggested_design && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1 font-medium">Legends / Design</div>
                      <div className="text-sm space-y-1">
                        {item.suggested_design.obverse_legend && (
                          <div><span className="text-muted-foreground">Obv:</span> {item.suggested_design.obverse_legend}</div>
                        )}
                        {item.suggested_design.reverse_legend && (
                          <div><span className="text-muted-foreground">Rev:</span> {item.suggested_design.reverse_legend}</div>
                        )}
                        {item.suggested_design.exergue && (
                          <div><span className="text-muted-foreground">Exergue:</span> {item.suggested_design.exergue}</div>
                        )}
                        {item.suggested_design.obverse_description && (
                          <div><span className="text-muted-foreground">Obv desc:</span> {item.suggested_design.obverse_description}</div>
                        )}
                        {item.suggested_design.reverse_description && (
                          <div><span className="text-muted-foreground">Rev desc:</span> {item.suggested_design.reverse_description}</div>
                        )}
                      </div>
                    </div>
                  )}
                  {hasAttributionForItem && item.suggested_attribution && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1 font-medium">Attribution</div>
                      <div className="text-sm space-y-1">
                        {item.suggested_attribution.issuer && (
                          <div><span className="text-muted-foreground">Issuer:</span> {item.suggested_attribution.issuer}</div>
                        )}
                        {item.suggested_attribution.mint && (
                          <div><span className="text-muted-foreground">Mint:</span> {item.suggested_attribution.mint}</div>
                        )}
                        {item.suggested_attribution.denomination && (
                          <div><span className="text-muted-foreground">Type:</span> {item.suggested_attribution.denomination}</div>
                        )}
                        {(item.suggested_attribution.year_start != null || item.suggested_attribution.year_end != null) && (
                          <div>
                            <span className="text-muted-foreground">Dates:</span>{" "}
                            {item.suggested_attribution.year_start ?? "?"} – {item.suggested_attribution.year_end ?? "?"}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-border/50">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={transcribeMutation.isPending || identifyMutation.isPending}
                      onClick={async () => {
                        try {
                          await transcribeMutation.mutateAsync(item.coin_id);
                          toast.success("Legends transcribed; suggestions saved. Refresh to see them.");
                          refetch();
                        } catch {
                          toast.error("Transcribe failed (coin may have no primary image)");
                        }
                      }}
                    >
                      {transcribeMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <ScrollText className="h-3 w-3 mr-1" />}
                      Transcribe legends
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={transcribeMutation.isPending || identifyMutation.isPending}
                      onClick={async () => {
                        try {
                          await identifyMutation.mutateAsync(item.coin_id);
                          toast.success("Coin identified; suggestions saved. Refresh to see them.");
                          refetch();
                        } catch {
                          toast.error("Identify failed (coin may have no primary image)");
                        }
                      }}
                    >
                      {identifyMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Search className="h-3 w-3 mr-1" />}
                      Identify from image
                    </Button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bulk Actions Bar */}
      <ReviewBulkActionsBar
        selectedCount={selectedIds.size}
        onClearSelection={() => setSelectedIds(new Set())}
        onApproveAll={async () => {
          const ids = Array.from(selectedIds);
          try {
            await Promise.all(ids.map((id) => approveMutation.mutateAsync({ coinId: id })));
            toast.success(`Applied suggestions for ${ids.length} coin(s)`);
            setSelectedIds(new Set());
          } catch {
            toast.error("Failed to apply some suggestions");
          }
        }}
        onRejectAll={handleBulkDismiss}
        isLoading={dismissMutation.isPending || approveMutation.isPending}
      />
    </div>
  );
}
