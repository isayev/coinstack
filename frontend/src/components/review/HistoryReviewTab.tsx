import { useState } from "react";
import { useFieldHistory, type FieldHistoryEntry } from "@/hooks/useAudit";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Loader2, History, X, RefreshCw, ArrowRight, Clock } from "lucide-react";
import { SourceBadge } from "@/components/audit";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

/**
 * HistoryReviewTab - View field change history for coins
 * 
 * Features:
 * - Search by coin ID
 * - Display change history with change type, source, and timestamps
 */
export function HistoryReviewTab() {
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
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCoinId(e.target.value)}
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
            {history.map((entry: FieldHistoryEntry) => (
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
                      <SourceBadge source={entry.new_source} size="sm" />
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
