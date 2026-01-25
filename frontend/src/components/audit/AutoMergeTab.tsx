import { useState } from "react";
import {
  useMergeBatches,
  useAutoMergePreview,
  useAutoMergeBatch,
  useRollbackBatch,
} from "@/hooks/useAudit";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Merge, 
  History, 
  Loader2,
} from "lucide-react";
import { toast } from "sonner";

export function AutoMergeTab() {
  const [isPreviewing, setIsPreviewing] = useState(false);
  const { data: batches, isLoading: loadingBatches } = useMergeBatches();
  const previewMutation = useAutoMergePreview();
  const batchMutation = useAutoMergeBatch();
  const rollbackMutation = useRollbackBatch();

  const handlePreview = async () => {
    setIsPreviewing(true);
    await previewMutation.mutateAsync({ dry_run: true });
  };

  const handleRun = async () => {
    const result = await batchMutation.mutateAsync({ dry_run: false });
    if (result) {
      toast.success("Auto-merge batch completed");
      setIsPreviewing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Card */}
      {!isPreviewing ? (
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Merge className="w-5 h-5" />
                  Auto-Merge System
                </CardTitle>
                <CardDescription>
                  Automatically resolve high-confidence discrepancies using trust-based logic
                </CardDescription>
              </div>
              <Button onClick={handlePreview} disabled={previewMutation.isPending}>
                {previewMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Analyze Collection
              </Button>
            </div>
          </CardHeader>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Merge Preview</h2>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsPreviewing(false)}>Cancel</Button>
              <Button onClick={handleRun} disabled={batchMutation.isPending}>
                {batchMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Execute Merge
              </Button>
            </div>
          </div>
          
          {previewMutation.data && (
            <Card>
              <CardContent className="py-6">
                <div className="flex items-center gap-8">
                  <div>
                    <div className="text-3xl font-bold">{previewMutation.data.total_coins}</div>
                    <div className="text-sm text-muted-foreground">Coins Impacted</div>
                  </div>
                  <div className="w-px h-12 bg-border" />
                  <div>
                    <div className="text-3xl font-bold text-primary">{previewMutation.data.changes}</div>
                    <div className="text-sm text-muted-foreground">Automatic Changes</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* History */}
      <div className="space-y-4">
        <h3 className="font-semibold flex items-center gap-2">
          <History className="w-4 h-4" />
          Recent Batches
        </h3>
        
        {loadingBatches ? (
          <div className="py-8 text-center text-muted-foreground">Loading history...</div>
        ) : (
          <div className="grid gap-2">
            {batches?.map((batch) => (
              <Card key={batch.id} className="bg-card/50">
                <CardContent className="py-3 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Badge variant="outline" className="font-mono">{batch.id.substring(0, 8)}</Badge>
                    <div className="text-sm">
                      <span className="text-muted-foreground">{new Date(batch.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => rollbackMutation.mutate(batch.id)}>
                    Rollback
                  </Button>
                </CardContent>
              </Card>
            ))}
            {batches?.length === 0 && (
              <div className="py-12 border-2 border-dashed rounded-lg text-center text-muted-foreground">
                No merge history found.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
