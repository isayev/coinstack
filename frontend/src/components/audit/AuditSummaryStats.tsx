/**
 * AuditSummaryStats component - Summary statistics cards for the audit dashboard.
 */

import { useAuditSummary } from "@/hooks/useAudit";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, Sparkles, CheckCircle, History, TrendingUp } from "lucide-react";

export function AuditSummaryStats() {
  const { data: summary, isLoading } = useAuditSummary();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!summary) return null;

  const totalDiscrepanciesByTrust = Object.values(
    summary.discrepancies_by_trust
  ).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-4">
      {/* Main stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Pending Discrepancies */}
        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Pending Discrepancies
            </CardTitle>
            <AlertTriangle className="w-4 h-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.pending_discrepancies}
            </div>
            <p className="text-xs text-muted-foreground">
              Requires review
            </p>
          </CardContent>
        </Card>

        {/* Pending Enrichments */}
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Enrichment Opportunities
            </CardTitle>
            <Sparkles className="w-4 h-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary.pending_enrichments}
            </div>
            <p className="text-xs text-muted-foreground">
              Data improvements available
            </p>
          </CardContent>
        </Card>

        {/* High Trust Issues */}
        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              High Trust Issues
            </CardTitle>
            <CheckCircle className="w-4 h-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(summary.discrepancies_by_trust.authoritative || 0) +
                (summary.discrepancies_by_trust.high || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              From trusted sources
            </p>
          </CardContent>
        </Card>

        {/* Recent Runs */}
        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Recent Audits</CardTitle>
            <History className="w-4 h-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.recent_runs.length}</div>
            <p className="text-xs text-muted-foreground">
              In last 30 days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Breakdown cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* By Trust Level */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">By Trust Level</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(summary.discrepancies_by_trust)
              .sort((a, b) => b[1] - a[1])
              .map(([trust, count]) => (
                <div
                  key={trust}
                  className="flex items-center justify-between text-sm"
                >
                  <Badge 
                    variant="outline" 
                    className={cn(
                      "capitalize border",
                      trust === 'authoritative' && "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/40",
                      trust === 'high' && "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/40",
                      trust === 'medium' && "bg-sky-500/15 text-sky-700 dark:text-sky-400 border-sky-500/40",
                      trust === 'low' && "bg-orange-500/15 text-orange-700 dark:text-orange-400 border-orange-500/40",
                      trust === 'untrusted' && "bg-slate-500/15 text-slate-700 dark:text-slate-400 border-slate-500/40",
                    )}
                  >
                    {trust}
                  </Badge>
                  <span className="font-semibold text-foreground">{count}</span>
                </div>
              ))}
            {Object.keys(summary.discrepancies_by_trust).length === 0 && (
              <p className="text-sm text-muted-foreground">No discrepancies</p>
            )}
          </CardContent>
        </Card>

        {/* By Field */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">By Field</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(summary.discrepancies_by_field)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 5)
              .map(([field, count]) => (
                <div
                  key={field}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-muted-foreground">
                    {formatFieldName(field)}
                  </span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            {Object.keys(summary.discrepancies_by_field).length === 0 && (
              <p className="text-sm text-muted-foreground">No discrepancies</p>
            )}
          </CardContent>
        </Card>

        {/* By Source */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">By Source</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(summary.discrepancies_by_source)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 5)
              .map(([source, count]) => (
                <div
                  key={source}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-muted-foreground">{source}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            {Object.keys(summary.discrepancies_by_source).length === 0 && (
              <p className="text-sm text-muted-foreground">No discrepancies</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function formatFieldName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default AuditSummaryStats;
