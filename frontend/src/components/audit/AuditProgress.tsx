/**
 * AuditProgress component - Shows progress of running audit.
 */

import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle, XCircle, AlertTriangle, Sparkles } from "lucide-react";
import type { AuditRunProgress, AuditRunStatus } from "@/types/audit";

interface AuditProgressProps {
  progress: AuditRunProgress;
}

function getStatusIcon(status: AuditRunStatus) {
  switch (status) {
    case "running":
      return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    case "completed":
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    case "failed":
      return <XCircle className="w-5 h-5 text-red-500" />;
    case "cancelled":
      return <XCircle className="w-5 h-5 text-orange-500" />;
    default:
      return null;
  }
}

function getStatusBadgeVariant(status: AuditRunStatus) {
  switch (status) {
    case "running":
      return "default" as const;
    case "completed":
      return "secondary" as const;
    case "failed":
      return "destructive" as const;
    default:
      return "outline" as const;
  }
}

export function AuditProgress({ progress }: AuditProgressProps) {
  const isRunning = progress.status === "running";

  return (
    <Card className={isRunning ? "border-blue-200" : ""}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            {getStatusIcon(progress.status)}
            Audit Progress
          </CardTitle>
          <Badge variant={getStatusBadgeVariant(progress.status)}>
            {progress.status.charAt(0).toUpperCase() + progress.status.slice(1)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              {progress.coins_audited} of {progress.total_coins} coins
            </span>
            <span className="font-medium">
              {Math.round(progress.progress_percent)}%
            </span>
          </div>
          <Progress value={progress.progress_percent} className="h-2" />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 pt-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" />
            <div>
              <div className="text-lg font-semibold">
                {progress.discrepancies_found}
              </div>
              <div className="text-xs text-muted-foreground">Discrepancies</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-500" />
            <div>
              <div className="text-lg font-semibold">
                {progress.enrichments_found}
              </div>
              <div className="text-xs text-muted-foreground">Enrichments</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default AuditProgress;
