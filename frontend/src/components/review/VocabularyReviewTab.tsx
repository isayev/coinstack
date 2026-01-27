import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RefreshCw, ArrowUpDown, Loader2 } from "lucide-react";
import { ReviewCard, ReviewEmptyState, ReviewBulkActionsBar } from "@/components/review";
import { useReviewUndo } from "@/hooks/useReviewUndo";

interface ReviewQueueItem {
  id: number;
  coin_id: number;
  field_name: string;
  raw_value: string;
  vocab_term_id: number | null;
  confidence: number | null;
  method: string | null;
  suggested_name: string | null;
}

type SortField = "confidence" | "field" | "coin_id";
type SortDirection = "asc" | "desc";

/**
 * VocabularyReviewTab - Review vocabulary assignments (issuer/mint/denomination)
 * 
 * Features:
 * - Card-based layout using unified ReviewCard
 * - Default sort: Confidence ASC (low-confidence first)
 * - Smart Sort button (client-side heuristic)
 * - Bulk selection and actions
 * - Per-tab undo stack
 */
export function VocabularyReviewTab() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { pushAction } = useReviewUndo();
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [sortField, setSortField] = useState<SortField>("confidence");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  // Fetch review queue
  const { data: items, isLoading, refetch } = useQuery({
    queryKey: ["vocab", "review", "pending_review"],
    queryFn: async () => {
      const response = await api.get("/api/v2/vocab/review", {
        params: { status: "pending_review", limit: 200 },
      });
      return response.data as ReviewQueueItem[];
    },
  });

  // Fetch coin data for previews (batch)
  const coinIds = useMemo(() => items?.map((item) => item.coin_id) || [], [items]);
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

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: async (ids: number[]) => {
      await Promise.all(ids.map((id) => api.post(`/api/v2/vocab/review/${id}/approve`)));
    },
    onSuccess: (_, ids) => {
      queryClient.invalidateQueries({ queryKey: ["vocab", "review"] });
      queryClient.invalidateQueries({ queryKey: ["review", "counts"] });
      pushAction({
        type: "approve",
        itemIds: ids,
        tab: "vocabulary",
        undoFn: async () => {
          // TODO: Implement reverse approve (reject)
          await Promise.all(ids.map((id) => api.post(`/api/v2/vocab/review/${id}/reject`)));
          queryClient.invalidateQueries({ queryKey: ["vocab", "review"] });
        },
      });
      setSelectedIds(new Set());
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: async (ids: number[]) => {
      await Promise.all(ids.map((id) => api.post(`/api/v2/vocab/review/${id}/reject`)));
    },
    onSuccess: (_, ids) => {
      queryClient.invalidateQueries({ queryKey: ["vocab", "review"] });
      queryClient.invalidateQueries({ queryKey: ["review", "counts"] });
      pushAction({
        type: "reject",
        itemIds: ids,
        tab: "vocabulary",
        undoFn: async () => {
          // TODO: Implement reverse reject (approve)
          await Promise.all(ids.map((id) => api.post(`/api/v2/vocab/review/${id}/approve`)));
          queryClient.invalidateQueries({ queryKey: ["vocab", "review"] });
        },
      });
      setSelectedIds(new Set());
    },
  });

  // Sorted and filtered items
  const sortedItems = useMemo(() => {
    if (!items) return [];
    const sorted = [...items].sort((a, b) => {
      let comparison = 0;
      if (sortField === "confidence") {
        const aConf = a.confidence ?? 0;
        const bConf = b.confidence ?? 0;
        comparison = aConf - bConf;
      } else if (sortField === "field") {
        comparison = a.field_name.localeCompare(b.field_name);
      } else if (sortField === "coin_id") {
        comparison = a.coin_id - b.coin_id;
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });
    return sorted;
  }, [items, sortField, sortDirection]);

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

  const handleBulkApprove = () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;
    approveMutation.mutate(ids);
  };

  const handleBulkReject = () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;
    rejectMutation.mutate(ids);
  };

  const handleApprove = (id: number) => {
    approveMutation.mutate([id]);
  };

  const handleReject = (id: number) => {
    rejectMutation.mutate([id]);
  };

  const handleSmartSort = () => {
    // Client-side heuristic: sort by confidence ASC, then by field importance
    // Field importance weights for future use:
    // const _fieldImportance = { issuer: 3, mint: 2, denomination: 1 };
    setSortField("confidence");
    setSortDirection("asc");
    // Additional sorting by field importance could be added here
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!items || items.length === 0) {
    return <ReviewEmptyState variant="vocabulary" />;
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
              <SelectItem value="confidence">Confidence</SelectItem>
              <SelectItem value="field">Field</SelectItem>
              <SelectItem value="coin_id">Coin ID</SelectItem>
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
          <Button variant="outline" size="sm" onClick={handleSmartSort}>
            Smart Sort
          </Button>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 gap-4">
        {sortedItems.map((item) => {
          const coin = coinsData?.[item.coin_id];
          return (
            <ReviewCard
              key={item.id}
              id={item.id}
              coinId={item.coin_id}
              coinPreview={{
                image: coin?.images?.[0]?.url || null,
                denomination: coin?.denomination || item.field_name === "denomination" ? item.raw_value : null,
                issuer: coin?.attribution?.issuer || item.field_name === "issuer" ? item.raw_value : null,
                category: coin?.category || null,
              }}
              field={item.field_name}
              currentValue={item.raw_value}
              suggestedValue={item.suggested_name}
              confidence={item.confidence}
              method={item.method}
              source="Vocabulary DB"
              isSelected={selectedIds.has(item.id)}
              onSelect={() => toggleSelect(item.id)}
              onApprove={() => handleApprove(item.id)}
              onReject={() => handleReject(item.id)}
              onViewCoin={() => navigate(`/coins/${item.coin_id}`)}
            />
          );
        })}
      </div>

      {/* Bulk Actions Bar */}
      <ReviewBulkActionsBar
        selectedCount={selectedIds.size}
        onClearSelection={() => setSelectedIds(new Set())}
        onApproveAll={handleBulkApprove}
        onRejectAll={handleBulkReject}
        isLoading={approveMutation.isPending || rejectMutation.isPending}
      />
    </div>
  );
}
