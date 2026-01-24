/**
 * AutoMergeTab - Enhanced auto-merge with image previews and color-coded changes
 * 
 * Features:
 * - Coin image previews in merge details
 * - Color-coded change types (fill, update, flag, skip)
 * - Source badges with trust indicators
 * - Batch history with expandable details
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  useMergeBatches,
  useAutoMergePreview,
  useAutoMergeBatch,
  useRollbackBatch,
  type AutoMergePreviewResult,
  type MergeBatch,
  type FieldChange,
} from "@/hooks/useAudit";
import { SourceBadge } from "./SourceBadge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Loader2,
  Eye,
  Merge,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Shield,
  Plus,
  RefreshCw,
  Flag,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

// Color-coded change type indicator
function ChangeTypeBadge({ type }: { type: 'fill' | 'update' | 'flag' | 'skip' }) {
  const config = {
    fill: { icon: Plus, label: 'Fill', className: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30' },
    update: { icon: RefreshCw, label: 'Update', className: 'bg-blue-500/10 text-blue-500 border-blue-500/30' },
    flag: { icon: Flag, label: 'Review', className: 'bg-amber-500/10 text-amber-500 border-amber-500/30' },
    skip: { icon: Shield, label: 'Protected', className: 'bg-gray-500/10 text-gray-500 border-gray-500/30' },
  };
  
  const { icon: Icon, label, className } = config[type];
  
  return (
    <Badge variant="outline" className={cn("text-xs", className)}>
      <Icon className="w-3 h-3 mr-1" />
      {label}
    </Badge>
  );
}

// Single field change display
function FieldChangeRow({ 
  change, 
  type 
}: { 
  change: FieldChange; 
  type: 'fill' | 'update' | 'flag' | 'skip';
}) {
  return (
    <div className={cn(
      "flex items-start gap-3 p-2 rounded-md",
      type === 'fill' && "bg-emerald-500/5",
      type === 'update' && "bg-blue-500/5",
      type === 'flag' && "bg-amber-500/5",
      type === 'skip' && "bg-gray-500/5",
    )}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">
            {change.field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
          </span>
          <ChangeTypeBadge type={type} />
          {change.conflict_type && (
            <Badge variant="outline" className="text-xs">
              {change.conflict_type}
            </Badge>
          )}
        </div>
        
        <div className="flex items-center gap-2 mt-1 text-sm">
          {type !== 'fill' && change.old !== null && (
            <>
              <span className={cn(
                type === 'update' && "line-through text-muted-foreground",
                type === 'flag' && "text-amber-600",
                type === 'skip' && "text-muted-foreground",
              )}>
                {formatValue(change.field, change.old)}
              </span>
              {(type === 'update' || type === 'flag') && (
                <ArrowRight className="w-3 h-3 text-muted-foreground" />
              )}
            </>
          )}
          
          {(type === 'fill' || type === 'update' || type === 'flag') && (
            <span className={cn(
              type === 'fill' && "text-emerald-500",
              type === 'update' && "text-blue-500",
              type === 'flag' && "text-amber-600",
            )}>
              {formatValue(change.field, change.new)}
            </span>
          )}
        </div>
        
        {change.reason && (
          <div className="text-xs text-muted-foreground mt-1">
            {change.reason}
          </div>
        )}
        
        {change.new_source && (
          <div className="mt-1">
            <SourceBadge source={change.new_source} size="sm" showTrustIcon={false} />
          </div>
        )}
      </div>
    </div>
  );
}

function formatValue(field: string, value: unknown): string {
  if (value === null || value === undefined) return '(empty)';
  if (typeof value === 'number') {
    if (field.includes('weight')) return `${value.toFixed(2)} g`;
    if (field.includes('diameter') || field.includes('thickness')) return `${value.toFixed(1)} mm`;
  }
  return String(value);
}

export function AutoMergeTab() {
  const [coinIdsInput, setCoinIdsInput] = useState("");
  const [previewResult, setPreviewResult] = useState<AutoMergePreviewResult | null>(null);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [showRollbackConfirm, setShowRollbackConfirm] = useState(false);

  const { data: batches, isLoading: loadingBatches } = useMergeBatches();
  const previewMutation = useAutoMergePreview();
  const batchMutation = useAutoMergeBatch();
  const rollbackMutation = useRollbackBatch();

  const parseCoinIds = (): number[] => {
    return coinIdsInput
      .split(/[,\s]+/)
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !isNaN(n) && n > 0);
  };

  const handlePreview = async () => {
    const coinIds = parseCoinIds();
    if (coinIds.length === 0) return;

    const result = await previewMutation.mutateAsync(coinIds);
    setPreviewResult(result);
    setShowPreviewDialog(true);
  };

  const handleMerge = async () => {
    const coinIds = parseCoinIds();
    if (coinIds.length === 0) return;

    if (coinIds.length > 10) {
      setShowConfirmDialog(true);
      return;
    }

    await batchMutation.mutateAsync({ coinIds, confirmed: true });
    setCoinIdsInput("");
  };

  const handleConfirmedMerge = async () => {
    const coinIds = parseCoinIds();
    await batchMutation.mutateAsync({ coinIds, confirmed: true });
    setShowConfirmDialog(false);
    setCoinIdsInput("");
  };

  const handleRollback = async () => {
    if (!selectedBatchId) return;
    await rollbackMutation.mutateAsync(selectedBatchId);
    setShowRollbackConfirm(false);
    setSelectedBatchId(null);
  };

  return (
    <div className="space-y-6">
      {/* Merge Controls */}
      <Card className="border-blue-500/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Merge className="w-5 h-5 text-blue-500" />
            Auto-Merge Auction Data
          </CardTitle>
          <CardDescription>
            Automatically update coin records with trusted auction data. 
            User-verified fields are protected from changes.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Input
              placeholder="Enter coin IDs (comma or space separated)..."
              value={coinIdsInput}
              onChange={(e) => setCoinIdsInput(e.target.value)}
              className="flex-1"
            />
            <Button
              variant="outline"
              onClick={handlePreview}
              disabled={!coinIdsInput.trim() || previewMutation.isPending}
            >
              {previewMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Eye className="w-4 h-4 mr-2" />
              )}
              Preview
            </Button>
            <Button
              onClick={handleMerge}
              disabled={!coinIdsInput.trim() || batchMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {batchMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Merge className="w-4 h-4 mr-2" />
              )}
              Merge
            </Button>
          </div>

          {batchMutation.isSuccess && (
            <div className="flex items-center gap-2 text-emerald-500 bg-emerald-500/10 p-3 rounded-md border border-emerald-500/30">
              <CheckCircle2 className="w-5 h-5" />
              <span>
                Merge completed! {batchMutation.data?.summary?.auto_filled || 0} filled,{" "}
                {batchMutation.data?.summary?.auto_updated || 0} updated.
              </span>
            </div>
          )}

          {batchMutation.isError && (
            <div className="flex items-center gap-2 text-red-500 bg-red-500/10 p-3 rounded-md border border-red-500/30">
              <XCircle className="w-5 h-5" />
              <span>Merge failed. Please try again.</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Batches */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RotateCcw className="w-5 h-5" />
            Recent Merge Batches
          </CardTitle>
          <CardDescription>
            View and rollback recent auto-merge operations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingBatches && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          )}

          {!loadingBatches && batches && batches.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Batch ID</TableHead>
                  <TableHead>Changes</TableHead>
                  <TableHead>Coins</TableHead>
                  <TableHead>When</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {batches.map((batch: MergeBatch) => (
                  <TableRow key={batch.batch_id}>
                    <TableCell className="font-mono text-sm">
                      {batch.batch_id.substring(0, 8)}...
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {batch.changes > 0 && (
                          <Badge variant="outline" className="text-xs bg-blue-500/10 text-blue-500">
                            {batch.changes}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{batch.coins_affected}</TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDistanceToNow(new Date(batch.started_at), {
                        addSuffix: true,
                      })}
                    </TableCell>
                    <TableCell className="text-right">
                      {batch.rollback_available && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedBatchId(batch.batch_id);
                            setShowRollbackConfirm(true);
                          }}
                          disabled={rollbackMutation.isPending}
                          className="text-orange-500 hover:text-orange-600 hover:bg-orange-500/10"
                        >
                          <RotateCcw className="w-4 h-4 mr-1" />
                          Rollback
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {!loadingBatches && (!batches || batches.length === 0) && (
            <p className="text-center text-muted-foreground py-8">
              No merge batches yet.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Auto-Merge Preview</DialogTitle>
            <DialogDescription>
              Review the changes that will be made to your coin records.
            </DialogDescription>
          </DialogHeader>

          {previewResult && (
            <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
              {/* Summary Stats */}
              <div className="grid grid-cols-5 gap-3">
                <div className="text-center p-3 rounded-md bg-muted">
                  <div className="text-2xl font-bold">
                    {previewResult.summary.total_coins}
                  </div>
                  <div className="text-xs text-muted-foreground">Coins</div>
                </div>
                <div className="text-center p-3 rounded-md bg-emerald-500/10 border border-emerald-500/30">
                  <div className="text-2xl font-bold text-emerald-500">
                    {previewResult.summary.will_auto_fill}
                  </div>
                  <div className="text-xs text-emerald-600">Fill Empty</div>
                </div>
                <div className="text-center p-3 rounded-md bg-blue-500/10 border border-blue-500/30">
                  <div className="text-2xl font-bold text-blue-500">
                    {previewResult.summary.will_auto_update}
                  </div>
                  <div className="text-xs text-blue-600">Update</div>
                </div>
                <div className="text-center p-3 rounded-md bg-amber-500/10 border border-amber-500/30">
                  <div className="text-2xl font-bold text-amber-500">
                    {previewResult.summary.will_flag}
                  </div>
                  <div className="text-xs text-amber-600">Review</div>
                </div>
                <div className="text-center p-3 rounded-md bg-gray-500/10 border border-gray-500/30">
                  <div className="text-2xl font-bold text-gray-500">
                    {previewResult.summary.will_skip}
                  </div>
                  <div className="text-xs text-gray-600">Protected</div>
                </div>
              </div>

              {/* Details per coin - scrollable */}
              <div className="flex-1 overflow-y-auto pr-2">
                <Accordion type="multiple" className="space-y-2">
                  {previewResult.details.map((detail) => {
                    const hasChanges = detail.auto_filled.length > 0 || 
                                       detail.auto_updated.length > 0 || 
                                       detail.flagged.length > 0;
                    
                    return (
                      <AccordionItem 
                        key={detail.coin_id} 
                        value={`coin-${detail.coin_id}`}
                        className="border rounded-lg px-4"
                      >
                        <AccordionTrigger className="hover:no-underline py-3">
                          <div className="flex items-center gap-4 flex-1">
                            {/* Coin info - simplified */}
                            <Link 
                              to={`/coins/${detail.coin_id}`}
                              className="flex items-center gap-2 hover:text-primary"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <span className="font-medium">Coin #{detail.coin_id}</span>
                              <ExternalLink className="w-3 h-3" />
                            </Link>
                            
                            {/* Change count badges */}
                            <div className="flex gap-1">
                              {detail.auto_filled.length > 0 && (
                                <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/30">
                                  <Plus className="w-3 h-3 mr-1" />
                                  {detail.auto_filled.length}
                                </Badge>
                              )}
                              {detail.auto_updated.length > 0 && (
                                <Badge className="bg-blue-500/10 text-blue-500 border-blue-500/30">
                                  <RefreshCw className="w-3 h-3 mr-1" />
                                  {detail.auto_updated.length}
                                </Badge>
                              )}
                              {detail.flagged.length > 0 && (
                                <Badge className="bg-amber-500/10 text-amber-500 border-amber-500/30">
                                  <Flag className="w-3 h-3 mr-1" />
                                  {detail.flagged.length}
                                </Badge>
                              )}
                              {detail.skipped.length > 0 && (
                                <Badge className="bg-gray-500/10 text-gray-500 border-gray-500/30">
                                  <Shield className="w-3 h-3 mr-1" />
                                  {detail.skipped.length}
                                </Badge>
                              )}
                            </div>
                            
                            {!hasChanges && detail.errors.length === 0 && (
                              <span className="text-sm text-muted-foreground">
                                No changes needed
                              </span>
                            )}
                          </div>
                        </AccordionTrigger>
                        
                        <AccordionContent className="pt-2 pb-4">
                          <div className="space-y-2">
                            {detail.errors.length > 0 && (
                              <div className="flex items-center gap-2 text-red-500 text-sm p-2 bg-red-500/10 rounded-md">
                                <AlertTriangle className="w-4 h-4" />
                                {detail.errors.join(", ")}
                              </div>
                            )}

                            {detail.auto_filled.map((change, i) => (
                              <FieldChangeRow key={`fill-${i}`} change={change} type="fill" />
                            ))}
                            
                            {detail.auto_updated.map((change, i) => (
                              <FieldChangeRow key={`update-${i}`} change={change} type="update" />
                            ))}
                            
                            {detail.flagged.map((change, i) => (
                              <FieldChangeRow key={`flag-${i}`} change={change} type="flag" />
                            ))}
                            
                            {detail.skipped.map((skip, i) => (
                              <FieldChangeRow 
                                key={`skip-${i}`} 
                                change={{ 
                                  field: skip.field, 
                                  old: null, 
                                  new: null, 
                                  old_source: null, 
                                  new_source: '', 
                                  conflict_type: null,
                                  reason: skip.reason 
                                }} 
                                type="skip" 
                              />
                            ))}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    );
                  })}
                </Accordion>
              </div>
            </div>
          )}

          <DialogFooter className="border-t pt-4">
            <Button variant="outline" onClick={() => setShowPreviewDialog(false)}>
              Close
            </Button>
            <Button
              onClick={() => {
                setShowPreviewDialog(false);
                handleMerge();
              }}
              disabled={
                !previewResult ||
                (previewResult.summary.will_auto_fill === 0 &&
                  previewResult.summary.will_auto_update === 0)
              }
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Merge className="w-4 h-4 mr-2" />
              Apply Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog for Large Batches */}
      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Confirm Large Batch Merge
            </AlertDialogTitle>
            <AlertDialogDescription>
              You are about to merge changes for {parseCoinIds().length} coins.
              This operation can be rolled back, but it's recommended to preview
              first. Are you sure you want to proceed?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmedMerge} className="bg-blue-600">
              <Merge className="w-4 h-4 mr-2" />
              Confirm Merge
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Rollback Confirmation */}
      <AlertDialog open={showRollbackConfirm} onOpenChange={setShowRollbackConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-orange-500" />
              Confirm Rollback
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will restore all fields to their previous values. The rollback
              itself will be recorded in the field history. Are you sure?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setSelectedBatchId(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRollback}
              className="bg-orange-600 hover:bg-orange-700"
            >
              {rollbackMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <RotateCcw className="w-4 h-4 mr-2" />
              )}
              Rollback
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
