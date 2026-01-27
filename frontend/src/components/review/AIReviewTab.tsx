import { useState, useMemo } from "react";
import { useLLMSuggestions, useDismissLLMSuggestion } from "@/hooks/useAudit";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, ArrowUpDown, Loader2, Sparkles, BookOpen, Gem } from "lucide-react";
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

  // Sorted items
  const sortedItems = useMemo(() => {
    const sorted = [...items].sort((a, b) => {
      let comparison = 0;
      if (sortField === "coin_id") {
        comparison = a.coin_id - b.coin_id;
      } else {
        // For confidence, use a heuristic based on number of suggestions
        const aConf = a.suggested_references.length + (a.rarity_info ? 1 : 0);
        const bConf = b.suggested_references.length + (b.rarity_info ? 1 : 0);
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
          // Note: Dismiss is not reversible via API, so undo is limited
          toast.info("Dismiss action cannot be undone");
        },
      });
    } catch {
      toast.error("Failed to dismiss suggestions");
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
            Review catalog references and rarity assessments suggested by AI. Click "Approve" to view
            the coin detail page where you can add these suggestions to your collection.
          </p>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 gap-4">
        {sortedItems.map((item) => {
          const coin = coinsData?.[item.coin_id];
          const hasReferences = item.suggested_references.length > 0;
          const hasRarity = item.rarity_info !== null;
          
          // Build suggested value string
          const suggestedParts: string[] = [];
          if (hasReferences) {
            suggestedParts.push(`${item.suggested_references.length} reference(s)`);
          }
          if (hasRarity && item.rarity_info) {
            suggestedParts.push(`Rarity: ${item.rarity_info.rarity_code || item.rarity_info.rarity_description || "Unknown"}`);
          }
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
                confidence={hasReferences || hasRarity ? 0.85 : null}
                method="llm"
                source="AI Analysis"
                isSelected={selectedIds.has(item.coin_id)}
                onSelect={() => toggleSelect(item.coin_id)}
                onApprove={() => navigate(`/coins/${item.coin_id}`)}
                onReject={() => handleDismiss(item.coin_id)}
                onViewCoin={() => navigate(`/coins/${item.coin_id}`)}
              />
              
              {/* Expanded Details */}
              {(hasReferences || hasRarity) && (
                <div className="mt-2 ml-20 pl-4 border-l-2 border-muted space-y-2">
                  {hasReferences && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                        <BookOpen className="w-3 h-3" />
                        Suggested References:
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {item.suggested_references.map((ref, idx) => (
                          <Badge key={idx} variant="outline" className="bg-blue-500/10 text-blue-700 dark:text-blue-400">
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
                      <Badge variant="outline" className="bg-purple-500/10 text-purple-700 dark:text-purple-400">
                        {item.rarity_info.rarity_code || "?"} - {item.rarity_info.rarity_description || "Unknown"}
                      </Badge>
                      {item.rarity_info.source && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Source: {item.rarity_info.source}
                        </p>
                      )}
                    </div>
                  )}
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
        onApproveAll={() => {
          const ids = Array.from(selectedIds);
          ids.forEach((id) => navigate(`/coins/${id}`));
          setSelectedIds(new Set());
        }}
        onRejectAll={handleBulkDismiss}
        isLoading={dismissMutation.isPending}
      />
    </div>
  );
}
