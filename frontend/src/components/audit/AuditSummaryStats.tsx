import { useAuditSummary } from "@/hooks/useAudit";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Sparkles, CheckCircle, History } from "lucide-react";

export function AuditSummaryStats() {
  const { data: summary, isLoading } = useAuditSummary();

  if (isLoading || !summary) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="h-24" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pending Discrepancies */}
        <Card className="border-red-500/20 bg-red-500/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Discrepancies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {summary.pending_discrepancies}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Pending resolution</p>
          </CardContent>
        </Card>

        {/* Pending Enrichments */}
        <Card className="border-emerald-500/20 bg-emerald-500/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-500" />
              Enrichments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {summary.pending_enrichments}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Ready to apply</p>
          </CardContent>
        </Card>

        {/* High Confidence */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-primary" />
              High Trust
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.discrepancies_by_trust.high + summary.discrepancies_by_trust.authoritative}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Safe to accept</p>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <History className="w-4 h-4 text-muted-foreground" />
              Audit Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="outline" className="mt-1">
              System Healthy
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">Last run: Just now</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top Issue Fields</CardTitle>
            <CardDescription>Fields with most discrepancies</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(summary.discrepancies_by_field).length > 0 ? (
                Object.entries(summary.discrepancies_by_field)
                  .sort((a: any, b: any) => b[1] - a[1])
                  .slice(0, 5)
                  .map(([field, count]: [string, any]) => (
                    <div key={field} className="flex justify-between items-center text-sm">
                      <span className="capitalize">{field.replace('_', ' ')}</span>
                      <span className="font-bold">{count}</span>
                    </div>
                  ))
              ) : (
                <div className="text-center py-4 text-muted-foreground italic text-sm">No issues found</div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Data Sources</CardTitle>
            <CardDescription>Discrepancies by auction house</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(summary.discrepancies_by_source).length > 0 ? (
                Object.entries(summary.discrepancies_by_source)
                  .sort((a: any, b: any) => b[1] - a[1])
                  .map(([source, count]: [string, any]) => (
                    <div key={source} className="flex justify-between items-center text-sm">
                      <span className="font-medium">{source}</span>
                      <Badge variant="secondary">{count}</Badge>
                    </div>
                  ))
              ) : (
                <div className="text-center py-4 text-muted-foreground italic text-sm">All sources verified</div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}