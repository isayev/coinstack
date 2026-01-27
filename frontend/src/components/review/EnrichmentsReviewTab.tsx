import { useState } from "react";
import {
  useEnrichments,
  useBulkApplyEnrichments,
  useAutoApplyAllEnrichments,
  useAuditWithPolling,
  type EnrichmentFilters,
  type EnrichmentStatus,
  type TrustLevel,
} from "@/hooks/useAudit";
import { EnrichmentCard } from "@/components/audit";
import { AuditProgress } from "@/components/audit";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { ReviewEmptyState, ReviewBulkActionsBar } from "@/components/review";
import { Filter, Loader2, Sparkles, ChevronLeft, ChevronRight, PlayCircle } from "lucide-react";
import { toast } from "sonner";

/**
 * EnrichmentsReviewTab - Review enrichment opportunities (filling empty fields)
 * 
 * Features:
 * - "Run Enrichments" button to discover new enrichment opportunities
 * - Filter by status, trust level, auto-applicable
 * - Bulk selection and actions
 * - "Apply All" quick action
 * - Pagination
 */
export function EnrichmentsReviewTab() {
  const [filters, setFilters] = useState<EnrichmentFilters>({
    status: "pending",
    page: 1,
    per_page: 20,
  });
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const { data: enrichmentsData, isLoading } = useEnrichments(filters);
  const bulkApply = useBulkApplyEnrichments();
  const autoApplyAll = useAutoApplyAllEnrichments();
  
  const {
    start: startAudit,
    progress,
    isStarting,
    isPolling,
    isComplete,
  } = useAuditWithPolling();

  const handleStartEnrichments = () => {
    startAudit({ scope: "enrichments" });
    toast.info("Starting enrichment discovery...");
  };

  const handleBulkApply = async () => {
    if (selectedIds.length === 0) return;
    await bulkApply.mutateAsync(selectedIds);
    setSelectedIds([]);
    toast.success(`Applied ${selectedIds.length} enrichments`);
  };

  const handleApplyAll = async () => {
    if (!enrichmentsData || enrichmentsData.total === 0) return;
    const result = await autoApplyAll.mutateAsync(undefined);
    toast.success(`Applied ${result.applied} enrichments`);
  };

  const toggleSelection = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (!enrichmentsData) return;
    if (selectedIds.length === enrichmentsData.items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(enrichmentsData.items.map((e) => e.id));
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {/* Header with Run Button */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Enrichment Opportunities</h2>
            <p className="text-sm text-muted-foreground">
              Discover and apply enrichment data from auction records
            </p>
          </div>
          <Button
            onClick={handleStartEnrichments}
            disabled={isStarting || isPolling}
            className="gap-2"
          >
            {isStarting || isPolling ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <PlayCircle className="w-4 h-4" />
            )}
            Run Enrichments
          </Button>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (!enrichmentsData || enrichmentsData.items.length === 0) {
    return (
      <div className="space-y-4">
        {/* Header with Run Button */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Enrichment Opportunities</h2>
            <p className="text-sm text-muted-foreground">
              Discover and apply enrichment data from auction records
            </p>
          </div>
          <Button
            onClick={handleStartEnrichments}
            disabled={isStarting || isPolling}
            className="gap-2"
          >
            {isStarting || isPolling ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <PlayCircle className="w-4 h-4" />
            )}
            Run Enrichments
          </Button>
        </div>

        {/* Progress indicator */}
        {progress && !isComplete && (
          <AuditProgress progress={progress} />
        )}

        <ReviewEmptyState variant="data" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Run Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Enrichment Opportunities</h2>
          <p className="text-sm text-muted-foreground">
            Discover and apply enrichment data from auction records
          </p>
        </div>
        <Button
          onClick={handleStartEnrichments}
          disabled={isStarting || isPolling}
          className="gap-2"
        >
          {isStarting || isPolling ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <PlayCircle className="w-4 h-4" />
          )}
          Run Enrichments
        </Button>
      </div>

      {/* Progress indicator */}
      {progress && !isComplete && (
        <AuditProgress progress={progress} />
      )}

      {/* Quick Apply All */}
      {enrichmentsData && enrichmentsData.total > 0 && (
        <Card className="border-emerald-500/30 bg-emerald-500/5">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-sm">Quick Apply All</h3>
                <p className="text-xs text-muted-foreground">
                  Apply all {enrichmentsData.total} pending enrichments to fill empty coin fields
                </p>
              </div>
              <Button
                onClick={handleApplyAll}
                disabled={autoApplyAll.isPending}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {autoApplyAll.isPending ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                Apply All ({enrichmentsData.total})
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Filter className="w-4 h-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Select
              value={filters.status || "all"}
              onValueChange={(v) =>
                setFilters({
                  ...filters,
                  status: v === "all" ? undefined : (v as EnrichmentStatus),
                  page: 1,
                })
              }
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="applied">Applied</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.trust_level || "all"}
              onValueChange={(v) =>
                setFilters({
                  ...filters,
                  trust_level: v === "all" ? undefined : (v as TrustLevel),
                  page: 1,
                })
              }
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Trust Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Trust</SelectItem>
                <SelectItem value="authoritative">Authoritative</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={
                filters.auto_applicable === true
                  ? "true"
                  : filters.auto_applicable === false
                  ? "false"
                  : "all"
              }
              onValueChange={(v) =>
                setFilters({
                  ...filters,
                  auto_applicable: v === "all" ? undefined : v === "true",
                  page: 1,
                })
              }
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Auto-applicable" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="true">Auto-applicable</SelectItem>
                <SelectItem value="false">Requires Review</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Selection header */}
      {enrichmentsData.items.length > 0 && (
        <div className="flex items-center gap-2">
          <Checkbox
            checked={selectedIds.length === enrichmentsData.items.length}
            onCheckedChange={selectAll}
          />
          <span className="text-sm text-muted-foreground">
            Select all on this page ({selectedIds.length} selected)
          </span>
        </div>
      )}

      {/* Enrichment cards */}
      <div className="space-y-4">
        {enrichmentsData.items.map((enrichment) => (
          <div key={enrichment.id} className="flex items-start gap-3">
            <Checkbox
              checked={selectedIds.includes(enrichment.id)}
              onCheckedChange={() => toggleSelection(enrichment.id)}
              className="mt-4"
            />
            <div className="flex-1">
              <EnrichmentCard enrichment={enrichment} />
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {enrichmentsData.pages > 1 && (
        <div className="flex items-center justify-between pt-4">
          <span className="text-sm text-muted-foreground">
            Page {enrichmentsData.page} of {enrichmentsData.pages} ({enrichmentsData.total} total)
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={filters.page! <= 1}
              onClick={() =>
                setFilters({
                  ...filters,
                  page: (filters.page || 1) - 1,
                })
              }
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={filters.page! >= enrichmentsData.pages}
              onClick={() =>
                setFilters({
                  ...filters,
                  page: (filters.page || 1) + 1,
                })
              }
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Bulk actions bar */}
      {selectedIds.length > 0 && (
        <ReviewBulkActionsBar
          selectedCount={selectedIds.length}
          onClearSelection={() => setSelectedIds([])}
          onApproveAll={handleBulkApply}
          onRejectAll={() => {
            // Enrichments don't have reject, just clear selection
            setSelectedIds([]);
          }}
          isLoading={bulkApply.isPending}
        />
      )}
    </div>
  );
}
