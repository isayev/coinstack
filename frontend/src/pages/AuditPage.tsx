/**
 * AuditPage - Enhanced data audit and enrichment dashboard
 * 
 * Features:
 * - Summary stats with category colors
 * - Sticky bulk action toolbar
 * - Field history tab
 * - Improved filtering and layout
 */

import { useState } from "react";
import {
  useDiscrepancies,
  useEnrichments,
  useAuditWithPolling,
  useBulkResolveDiscrepancies,
  useBulkApplyEnrichments,
  useAutoApplyAllEnrichments,
  useFieldHistory,
} from "@/hooks/useAudit";
import {
  AuditSummaryStats,
  AuditProgress,
  DiscrepancyCard,
  EnrichmentCard,
  AutoMergeTab,
  SourceBadge,
  ImageReviewTab,
} from "@/components/audit";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import {
  AlertTriangle,
  Sparkles,
  PlayCircle,
  Loader2,
  CheckCheck,
  Filter,
  Merge,
  History,
  X,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  ArrowRight,
  Clock,
  Image as ImageIcon,
} from "lucide-react";
import type { DiscrepancyFilters, EnrichmentFilters, TrustLevel, DiscrepancyStatus, EnrichmentStatus } from "@/types/audit";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";

// Field History component for the History tab
function FieldHistoryTab() {
  const [coinId, setCoinId] = useState<string>("");
  const parsedCoinId = parseInt(coinId, 10);
  const { data: history, isLoading } = useFieldHistory(
    !isNaN(parsedCoinId) && parsedCoinId > 0 ? parsedCoinId : 0
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="w-5 h-5" />
          Field Change History
        </CardTitle>
        <CardDescription>
          View all changes made to coin fields through auto-merge
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-4">
          <Input
            placeholder="Enter coin ID to view history..."
            value={coinId}
            onChange={(e) => setCoinId(e.target.value)}
            className="w-48"
            type="number"
          />
          {coinId && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setCoinId("")}
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {!isLoading && history && history.length > 0 && (
          <div className="space-y-2">
            {history.map((entry) => (
              <div 
                key={entry.id}
                className={cn(
                  "flex items-start gap-3 p-3 rounded-md border",
                  entry.change_type === 'auto_fill' && "bg-emerald-500/5 border-emerald-500/20",
                  entry.change_type === 'auto_update' && "bg-blue-500/5 border-blue-500/20",
                  entry.change_type === 'rollback' && "bg-orange-500/5 border-orange-500/20",
                  entry.change_type === 'manual' && "bg-purple-500/5 border-purple-500/20",
                )}
              >
                {/* Icon */}
                <div className={cn(
                  "p-1.5 rounded-full",
                  entry.change_type === 'auto_fill' && "bg-emerald-500/20 text-emerald-500",
                  entry.change_type === 'auto_update' && "bg-blue-500/20 text-blue-500",
                  entry.change_type === 'rollback' && "bg-orange-500/20 text-orange-500",
                  entry.change_type === 'manual' && "bg-purple-500/20 text-purple-500",
                )}>
                  {entry.change_type === 'rollback' ? (
                    <RefreshCw className="w-4 h-4" />
                  ) : (
                    <ArrowRight className="w-4 h-4" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm">
                      {entry.field.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {entry.change_type.replace(/_/g, ' ')}
                    </Badge>
                    {entry.new_source && (
                      <SourceBadge source={entry.new_source} size="sm" showTrustIcon={false} />
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2 mt-1 text-sm">
                    <span className="text-muted-foreground line-through">
                      {entry.old_value !== null ? String(entry.old_value) : '(empty)'}
                    </span>
                    <ArrowRight className="w-3 h-3 text-muted-foreground" />
                    <span className={cn(
                      entry.change_type === 'rollback' ? "text-orange-500" : "text-foreground"
                    )}>
                      {entry.new_value !== null ? String(entry.new_value) : '(empty)'}
                    </span>
                  </div>
                  
                  {entry.reason && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {entry.reason}
                    </div>
                  )}
                  
                  <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    {formatDistanceToNow(new Date(entry.changed_at), { addSuffix: true })}
                    {entry.batch_id && (
                      <span className="font-mono">
                        Batch: {entry.batch_id.substring(0, 8)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!isLoading && coinId && (!history || history.length === 0) && (
          <p className="text-center text-muted-foreground py-8">
            No field history found for this coin.
          </p>
        )}

        {!coinId && (
          <p className="text-center text-muted-foreground py-8">
            Enter a coin ID to view its field change history.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default function AuditPage() {
  // Tab state
  const [activeTab, setActiveTab] = useState("discrepancies");

  // Filters
  const [discrepancyFilters, setDiscrepancyFilters] = useState<DiscrepancyFilters>({
    status: "pending",
    page: 1,
    per_page: 20,
  });
  const [enrichmentFilters, setEnrichmentFilters] = useState<EnrichmentFilters>({
    status: "pending",
    page: 1,
    per_page: 20,
  });

  // Selections for bulk actions
  const [selectedDiscrepancies, setSelectedDiscrepancies] = useState<number[]>([]);
  const [selectedEnrichments, setSelectedEnrichments] = useState<number[]>([]);

  // Data queries
  const { data: discrepanciesData, isLoading: loadingDiscrepancies } =
    useDiscrepancies(discrepancyFilters);
  const { data: enrichmentsData, isLoading: loadingEnrichments } =
    useEnrichments(enrichmentFilters);

  // Mutations
  const bulkResolve = useBulkResolveDiscrepancies();
  const bulkApply = useBulkApplyEnrichments();
  const autoApplyAll = useAutoApplyAllEnrichments();

  // Audit execution
  const {
    start: startAudit,
    progress,
    isStarting,
    isPolling,
    isComplete,
  } = useAuditWithPolling();

  const handleStartFullAudit = () => {
    startAudit({ scope: "all" });
  };

  const handleBulkAccept = async () => {
    if (selectedDiscrepancies.length === 0) return;
    await bulkResolve.mutateAsync({
      discrepancy_ids: selectedDiscrepancies,
      resolution: "accepted",
    });
    setSelectedDiscrepancies([]);
  };

  const handleBulkReject = async () => {
    if (selectedDiscrepancies.length === 0) return;
    await bulkResolve.mutateAsync({
      discrepancy_ids: selectedDiscrepancies,
      resolution: "rejected",
    });
    setSelectedDiscrepancies([]);
  };

  const handleBulkApplyEnrichments = async () => {
    if (selectedEnrichments.length === 0) return;
    await bulkApply.mutateAsync(selectedEnrichments);
    setSelectedEnrichments([]);
  };

  const toggleDiscrepancySelection = (id: number) => {
    setSelectedDiscrepancies((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleEnrichmentSelection = (id: number) => {
    setSelectedEnrichments((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAllDiscrepancies = () => {
    if (!discrepanciesData) return;
    if (
      selectedDiscrepancies.length === discrepanciesData.items.length
    ) {
      setSelectedDiscrepancies([]);
    } else {
      setSelectedDiscrepancies(discrepanciesData.items.map((d) => d.id));
    }
  };

  const selectAllEnrichments = () => {
    if (!enrichmentsData) return;
    if (selectedEnrichments.length === enrichmentsData.items.length) {
      setSelectedEnrichments([]);
    } else {
      setSelectedEnrichments(enrichmentsData.items.map((e) => e.id));
    }
  };

  // Check if bulk actions should show
  const showDiscrepancyBulkBar = selectedDiscrepancies.length > 0 && activeTab === 'discrepancies';
  const showEnrichmentBulkBar = selectedEnrichments.length > 0 && activeTab === 'enrichments';

  return (
    <div className="container mx-auto py-6 space-y-6 pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Audit</h1>
          <p className="text-muted-foreground">
            Review and resolve discrepancies between coin data and auction
            records
          </p>
        </div>
        <Button
          onClick={handleStartFullAudit}
          disabled={isStarting || isPolling}
          className="gap-2"
        >
          {isStarting || isPolling ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <PlayCircle className="w-4 h-4" />
          )}
          Run Full Audit
        </Button>
      </div>

      {/* Audit Progress */}
      {progress && !isComplete && (
        <AuditProgress progress={progress} />
      )}

      {/* Summary Stats */}
      <AuditSummaryStats />

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 max-w-2xl">
          <TabsTrigger value="discrepancies" className="gap-2">
            <AlertTriangle className="w-4 h-4" />
            Discrepancies
            {discrepanciesData && discrepanciesData.total > 0 && (
              <Badge variant="secondary" className="ml-1 text-xs">
                {discrepanciesData.total}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="enrichments" className="gap-2">
            <Sparkles className="w-4 h-4" />
            Enrichments
            {enrichmentsData && enrichmentsData.total > 0 && (
              <Badge variant="secondary" className="ml-1 text-xs">
                {enrichmentsData.total}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="auto-merge" className="gap-2">
            <Merge className="w-4 h-4" />
            Auto-Merge
          </TabsTrigger>
          <TabsTrigger value="images" className="gap-2">
            <ImageIcon className="w-4 h-4" />
            Images
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-2">
            <History className="w-4 h-4" />
            History
          </TabsTrigger>
        </TabsList>

        {/* Discrepancies Tab */}
        <TabsContent value="discrepancies" className="space-y-4">
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
                  value={discrepancyFilters.status || "all"}
                  onValueChange={(v) =>
                    setDiscrepancyFilters({
                      ...discrepancyFilters,
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
                  value={discrepancyFilters.trust_level || "all"}
                  onValueChange={(v) =>
                    setDiscrepancyFilters({
                      ...discrepancyFilters,
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
                  value={discrepancyFilters.source_house || "all"}
                  onValueChange={(v) =>
                    setDiscrepancyFilters({
                      ...discrepancyFilters,
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
                  value={discrepancyFilters.field_name || ""}
                  onChange={(e) =>
                    setDiscrepancyFilters({
                      ...discrepancyFilters,
                      field_name: e.target.value || undefined,
                      page: 1,
                    })
                  }
                  className="w-40"
                />
              </div>
            </CardContent>
          </Card>

          {/* Discrepancies List */}
          <div className="space-y-4">
            {/* Select all */}
            {discrepanciesData && discrepanciesData.items.length > 0 && (
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={
                    selectedDiscrepancies.length ===
                    discrepanciesData.items.length
                  }
                  onCheckedChange={selectAllDiscrepancies}
                />
                <span className="text-sm text-muted-foreground">
                  Select all on this page
                </span>
              </div>
            )}

            {loadingDiscrepancies && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            )}

            {!loadingDiscrepancies &&
              discrepanciesData?.items.map((discrepancy) => (
                <div key={discrepancy.id} className="flex items-start gap-3">
                  <Checkbox
                    checked={selectedDiscrepancies.includes(discrepancy.id)}
                    onCheckedChange={() =>
                      toggleDiscrepancySelection(discrepancy.id)
                    }
                    className="mt-4"
                  />
                  <div className="flex-1">
                    <DiscrepancyCard discrepancy={discrepancy} />
                  </div>
                </div>
              ))}

            {!loadingDiscrepancies && discrepanciesData?.items.length === 0 && (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  No discrepancies found matching your filters.
                </CardContent>
              </Card>
            )}

            {/* Pagination */}
            {discrepanciesData && discrepanciesData.pages > 1 && (
              <div className="flex items-center justify-between pt-4">
                <span className="text-sm text-muted-foreground">
                  Page {discrepanciesData.page} of {discrepanciesData.pages} (
                  {discrepanciesData.total} total)
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={discrepanciesData.page <= 1}
                    onClick={() =>
                      setDiscrepancyFilters({
                        ...discrepancyFilters,
                        page: (discrepancyFilters.page || 1) - 1,
                      })
                    }
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={discrepanciesData.page >= discrepanciesData.pages}
                    onClick={() =>
                      setDiscrepancyFilters({
                        ...discrepancyFilters,
                        page: (discrepancyFilters.page || 1) + 1,
                      })
                    }
                  >
                    Next
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Enrichments Tab */}
        <TabsContent value="enrichments" className="space-y-4">
          {/* Quick Actions */}
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
                    onClick={() => {
                      autoApplyAll.mutate(undefined, {
                        onSuccess: (result) => {
                          toast.success(`Applied ${result.applied} enrichments`, {
                            description: Object.entries(result.applied_by_field)
                              .map(([field, count]) => `${field}: ${count}`)
                              .join(", "),
                          });
                        },
                        onError: () => {
                          toast.error("Failed to apply enrichments");
                        },
                      });
                    }}
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
                  value={enrichmentFilters.status || "all"}
                  onValueChange={(v) =>
                    setEnrichmentFilters({
                      ...enrichmentFilters,
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
                  value={enrichmentFilters.trust_level || "all"}
                  onValueChange={(v) =>
                    setEnrichmentFilters({
                      ...enrichmentFilters,
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
                  </SelectContent>
                </Select>

                <Select
                  value={
                    enrichmentFilters.auto_applicable === true
                      ? "true"
                      : enrichmentFilters.auto_applicable === false
                      ? "false"
                      : "all"
                  }
                  onValueChange={(v) =>
                    setEnrichmentFilters({
                      ...enrichmentFilters,
                      auto_applicable:
                        v === "all" ? undefined : v === "true",
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

          {/* Enrichments List */}
          <div className="space-y-4">
            {/* Select all */}
            {enrichmentsData && enrichmentsData.items.length > 0 && (
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={
                    selectedEnrichments.length === enrichmentsData.items.length
                  }
                  onCheckedChange={selectAllEnrichments}
                />
                <span className="text-sm text-muted-foreground">
                  Select all on this page
                </span>
              </div>
            )}

            {loadingEnrichments && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            )}

            {!loadingEnrichments &&
              enrichmentsData?.items.map((enrichment) => (
                <div key={enrichment.id} className="flex items-start gap-3">
                  <Checkbox
                    checked={selectedEnrichments.includes(enrichment.id)}
                    onCheckedChange={() =>
                      toggleEnrichmentSelection(enrichment.id)
                    }
                    className="mt-4"
                  />
                  <div className="flex-1">
                    <EnrichmentCard enrichment={enrichment} />
                  </div>
                </div>
              ))}

            {!loadingEnrichments && enrichmentsData?.items.length === 0 && (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  No enrichment opportunities found matching your filters.
                </CardContent>
              </Card>
            )}

            {/* Pagination */}
            {enrichmentsData && enrichmentsData.pages > 1 && (
              <div className="flex items-center justify-between pt-4">
                <span className="text-sm text-muted-foreground">
                  Page {enrichmentsData.page} of {enrichmentsData.pages} (
                  {enrichmentsData.total} total)
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={enrichmentsData.page <= 1}
                    onClick={() =>
                      setEnrichmentFilters({
                        ...enrichmentFilters,
                        page: (enrichmentFilters.page || 1) - 1,
                      })
                    }
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={enrichmentsData.page >= enrichmentsData.pages}
                    onClick={() =>
                      setEnrichmentFilters({
                        ...enrichmentFilters,
                        page: (enrichmentFilters.page || 1) + 1,
                      })
                    }
                  >
                    Next
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Auto-Merge Tab */}
        <TabsContent value="auto-merge">
          <AutoMergeTab />
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="images">
          <ImageReviewTab />
        </TabsContent>

        <TabsContent value="history">
          <FieldHistoryTab />
        </TabsContent>
      </Tabs>

      {/* Sticky Bulk Actions Bar */}
      {(showDiscrepancyBulkBar || showEnrichmentBulkBar) && (
        <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-t shadow-lg z-50">
          <div className="container mx-auto py-3 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Badge variant="secondary" className="text-sm">
                {showDiscrepancyBulkBar ? selectedDiscrepancies.length : selectedEnrichments.length} selected
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  if (showDiscrepancyBulkBar) {
                    setSelectedDiscrepancies([]);
                  } else {
                    setSelectedEnrichments([]);
                  }
                }}
              >
                <X className="w-4 h-4 mr-1" />
                Clear
              </Button>
            </div>
            
            <div className="flex gap-2">
              {showDiscrepancyBulkBar && (
                <>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleBulkAccept}
                    disabled={bulkResolve.isPending}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    {bulkResolve.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-1" />
                    ) : (
                      <CheckCheck className="w-4 h-4 mr-1" />
                    )}
                    Accept All
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleBulkReject}
                    disabled={bulkResolve.isPending}
                  >
                    Reject All
                  </Button>
                </>
              )}
              
              {showEnrichmentBulkBar && (
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleBulkApplyEnrichments}
                  disabled={bulkApply.isPending}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {bulkApply.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-1" />
                  ) : (
                    <CheckCheck className="w-4 h-4 mr-1" />
                  )}
                  Apply All
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
