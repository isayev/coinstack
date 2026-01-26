import { useState } from "react";
import {
  useDiscrepancies,
  useBulkResolveDiscrepancies,
  type DiscrepancyFilters,
  type DiscrepancyStatus,
  type TrustLevel,
} from "@/hooks/useAudit";
import { DiscrepancyCard } from "@/components/audit";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { ReviewEmptyState, ReviewBulkActionsBar } from "@/components/review";
import { Filter, Loader2, CheckCheck, ChevronLeft, ChevronRight } from "lucide-react";
import { toast } from "sonner";

/**
 * DiscrepanciesReviewTab - Review discrepancies between coin data and auction records
 * 
 * Features:
 * - Filter by status, trust level, source, field name
 * - Bulk selection and actions
 * - Pagination
 */
export function DiscrepanciesReviewTab() {
  const [filters, setFilters] = useState<DiscrepancyFilters>({
    status: "pending",
    page: 1,
    per_page: 20,
  });
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const { data: discrepanciesData, isLoading } = useDiscrepancies(filters);
  const bulkResolve = useBulkResolveDiscrepancies();

  const handleBulkAccept = async () => {
    if (selectedIds.length === 0) return;
    await bulkResolve.mutateAsync({
      discrepancy_ids: selectedIds,
      resolution: "accepted",
    });
    setSelectedIds([]);
    toast.success(`Accepted ${selectedIds.length} discrepancies`);
  };

  const handleBulkReject = async () => {
    if (selectedIds.length === 0) return;
    await bulkResolve.mutateAsync({
      discrepancy_ids: selectedIds,
      resolution: "rejected",
    });
    setSelectedIds([]);
    toast.success(`Rejected ${selectedIds.length} discrepancies`);
  };

  const toggleSelection = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (!discrepanciesData) return;
    if (selectedIds.length === discrepanciesData.items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(discrepanciesData.items.map((d) => d.id));
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!discrepanciesData || discrepanciesData.items.length === 0) {
    return <ReviewEmptyState variant="data" />;
  }

  return (
    <div className="space-y-4">
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
                  status: v === "all" ? undefined : (v as DiscrepancyStatus),
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
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="ignored">Ignored</SelectItem>
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
              value={filters.source_house || "all"}
              onValueChange={(v) =>
                setFilters({
                  ...filters,
                  source_house: v === "all" ? undefined : v,
                  page: 1,
                })
              }
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="heritage">Heritage</SelectItem>
                <SelectItem value="cng">CNG</SelectItem>
                <SelectItem value="biddr">Biddr</SelectItem>
                <SelectItem value="ebay">eBay</SelectItem>
              </SelectContent>
            </Select>

            <Input
              placeholder="Field name..."
              value={filters.field_name || ""}
              onChange={(e) =>
                setFilters({
                  ...filters,
                  field_name: e.target.value || undefined,
                  page: 1,
                })
              }
              className="w-40"
            />
          </div>
        </CardContent>
      </Card>

      {/* Selection header */}
      {discrepanciesData.items.length > 0 && (
        <div className="flex items-center gap-2">
          <Checkbox
            checked={selectedIds.length === discrepanciesData.items.length}
            onCheckedChange={selectAll}
          />
          <span className="text-sm text-muted-foreground">
            Select all on this page ({selectedIds.length} selected)
          </span>
        </div>
      )}

      {/* Discrepancy cards */}
      <div className="space-y-4">
        {discrepanciesData.items.map((discrepancy) => (
          <div key={discrepancy.id} className="flex items-start gap-3">
            <Checkbox
              checked={selectedIds.includes(discrepancy.id)}
              onCheckedChange={() => toggleSelection(discrepancy.id)}
              className="mt-4"
            />
            <div className="flex-1">
              <DiscrepancyCard discrepancy={discrepancy} />
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {discrepanciesData.pages > 1 && (
        <div className="flex items-center justify-between pt-4">
          <span className="text-sm text-muted-foreground">
            Page {discrepanciesData.page} of {discrepanciesData.pages} ({discrepanciesData.total} total)
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
              disabled={filters.page! >= discrepanciesData.pages}
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
          onApproveAll={handleBulkAccept}
          onRejectAll={handleBulkReject}
          isLoading={bulkResolve.isPending}
        />
      )}
    </div>
  );
}
