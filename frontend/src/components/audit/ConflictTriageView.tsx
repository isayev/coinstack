/**
 * ConflictTriageView - High-level overview of conflicts before diving into details
 * 
 * Categorizes conflicts into:
 * - Auto-resolvable: Higher trust or within tolerance
 * - Needs review: Equal trust, significant difference
 * - Possible errors: Values outside normal range
 * - Low priority: Minor differences from low trust sources
 */

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { Discrepancy, Enrichment, TrustLevel } from "@/types/audit";
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
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle2,
  XCircle,
  Clock,
  ChevronRight,
  Zap,
  Eye,
  Scale,
  BookOpen,
  Hash,
  FileText,
  Ruler,
} from "lucide-react";

// Field icons for visual identification
const FIELD_ICONS: Record<string, React.ElementType> = {
  weight_g: Scale,
  diameter_mm: Ruler,
  grade: BookOpen,
  references: Hash,
  primary_reference: Hash,
  obverse_description: FileText,
  reverse_description: FileText,
  obverse_legend: FileText,
  reverse_legend: FileText,
};

// Field labels for display
const FIELD_LABELS: Record<string, string> = {
  weight_g: "Weight",
  diameter_mm: "Diameter",
  thickness_mm: "Thickness",
  die_axis: "Die Axis",
  grade: "Grade",
  grade_service: "Grading Service",
  certification_number: "Cert Number",
  strike_score: "Strike Score",
  surface_score: "Surface Score",
  obverse_legend: "Obverse Legend",
  reverse_legend: "Reverse Legend",
  obverse_description: "Obverse Description",
  reverse_description: "Reverse Description",
  exergue: "Exergue",
  ruler: "Ruler",
  denomination: "Denomination",
  mint: "Mint",
  primary_reference: "Reference",
};

interface TriageCategory {
  id: string;
  title: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: React.ElementType;
  items: Discrepancy[];
  action: string;
  actionVariant: "default" | "outline" | "secondary" | "destructive";
}

interface GroupedByField {
  field: string;
  total: number;
  autoResolvable: number;
  needsReview: number;
}

interface GroupedBySource {
  source: string;
  total: number;
  avgTrust: number;
}

interface ConflictTriageViewProps {
  discrepancies: Discrepancy[];
  enrichments?: Enrichment[];
  onAutoResolve: (items: Discrepancy[]) => void;
  onStartReview: (items: Discrepancy[]) => void;
  onDismiss: (items: Discrepancy[]) => void;
  onFilterByField: (field: string) => void;
  onFilterBySource: (source: string) => void;
}

// Trust level to numeric value for comparison
const TRUST_NUMERIC: Record<TrustLevel, number> = {
  authoritative: 100,
  high: 80,
  medium: 60,
  low: 40,
  untrusted: 20,
};

// Tolerance thresholds for measurements
const TOLERANCE_THRESHOLDS: Record<string, number> = {
  weight_g: 0.05,      // 5% tolerance
  diameter_mm: 0.03,   // 3% tolerance
  thickness_mm: 0.1,   // 10% tolerance
};

function categorizeDiscrepancy(d: Discrepancy): string {
  const trustScore = TRUST_NUMERIC[d.trust_level] || 60;
  const similarity = d.similarity ?? 0;
  
  // Auto-resolvable: high trust source with good similarity OR auto_acceptable flag
  if (d.auto_acceptable) return "auto";
  if (trustScore >= 80 && similarity >= 0.8) return "auto";
  
  // Check if within tolerance for measurement fields
  if (d.field_name in TOLERANCE_THRESHOLDS) {
    const threshold = TOLERANCE_THRESHOLDS[d.field_name];
    if (similarity >= (1 - threshold)) return "auto";
  }
  
  // Possible errors: low similarity from high trust source (unusual)
  if (trustScore >= 80 && similarity < 0.5) return "error";
  
  // Low priority: low trust source with any difference
  if (trustScore <= 40) return "low";
  
  // Everything else needs review
  return "review";
}

function groupDiscrepancies(discrepancies: Discrepancy[]): TriageCategory[] {
  const auto: Discrepancy[] = [];
  const review: Discrepancy[] = [];
  const errors: Discrepancy[] = [];
  const low: Discrepancy[] = [];
  
  for (const d of discrepancies) {
    const category = categorizeDiscrepancy(d);
    switch (category) {
      case "auto": auto.push(d); break;
      case "review": review.push(d); break;
      case "error": errors.push(d); break;
      case "low": low.push(d); break;
    }
  }
  
  return [
    {
      id: "auto",
      title: "Auto-Resolvable",
      description: "Higher trust or within tolerance",
      color: "text-emerald-500",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/30",
      icon: CheckCircle2,
      items: auto,
      action: "Resolve All",
      actionVariant: "default",
    },
    {
      id: "review",
      title: "Needs Review",
      description: "Equal trust, significant difference",
      color: "text-amber-500",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/30",
      icon: Eye,
      items: review,
      action: "Start Review",
      actionVariant: "outline",
    },
    {
      id: "error",
      title: "Possible Errors",
      description: "Values outside normal range",
      color: "text-red-500",
      bgColor: "bg-red-500/10",
      borderColor: "border-red-500/30",
      icon: XCircle,
      items: errors,
      action: "Investigate",
      actionVariant: "destructive",
    },
    {
      id: "low",
      title: "Low Priority",
      description: "Minor differences, low trust source",
      color: "text-gray-500",
      bgColor: "bg-gray-500/10",
      borderColor: "border-gray-500/30",
      icon: Clock,
      items: low,
      action: "Dismiss All",
      actionVariant: "secondary",
    },
  ];
}

function groupByField(discrepancies: Discrepancy[]): GroupedByField[] {
  const byField: Record<string, { total: number; auto: number; review: number }> = {};
  
  for (const d of discrepancies) {
    if (!byField[d.field_name]) {
      byField[d.field_name] = { total: 0, auto: 0, review: 0 };
    }
    byField[d.field_name].total++;
    
    const category = categorizeDiscrepancy(d);
    if (category === "auto") byField[d.field_name].auto++;
    else if (category === "review") byField[d.field_name].review++;
  }
  
  return Object.entries(byField)
    .map(([field, data]) => ({
      field,
      total: data.total,
      autoResolvable: data.auto,
      needsReview: data.review,
    }))
    .sort((a, b) => b.total - a.total);
}

function groupBySource(discrepancies: Discrepancy[]): GroupedBySource[] {
  const bySource: Record<string, { total: number; trustSum: number }> = {};
  
  for (const d of discrepancies) {
    const source = d.source_house.toLowerCase();
    if (!bySource[source]) {
      bySource[source] = { total: 0, trustSum: 0 };
    }
    bySource[source].total++;
    bySource[source].trustSum += TRUST_NUMERIC[d.trust_level] || 60;
  }
  
  return Object.entries(bySource)
    .map(([source, data]) => ({
      source,
      total: data.total,
      avgTrust: Math.round(data.trustSum / data.total),
    }))
    .sort((a, b) => b.total - a.total);
}

// Triage Card Component
function TriageCard({
  category,
  onAction,
}: {
  category: TriageCategory;
  onAction: () => void;
}) {
  const Icon = category.icon;
  const count = category.items.length;
  
  return (
    <Card className={cn(
      "border-2 transition-all hover:shadow-md",
      category.borderColor,
      count === 0 && "opacity-50"
    )}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className={cn(
            "p-2 rounded-lg",
            category.bgColor
          )}>
            <Icon className={cn("w-5 h-5", category.color)} />
          </div>
          <span className={cn(
            "text-3xl font-bold",
            category.color
          )}>
            {count}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <h3 className="font-semibold">{category.title}</h3>
        <p className="text-sm text-muted-foreground mb-3">
          {category.description}
        </p>
        <Button
          variant={category.actionVariant}
          size="sm"
          className="w-full"
          disabled={count === 0}
          onClick={onAction}
        >
          {category.action}
        </Button>
      </CardContent>
    </Card>
  );
}

export function ConflictTriageView({
  discrepancies,
  enrichments = [],
  onAutoResolve,
  onStartReview,
  onDismiss,
  onFilterByField,
  onFilterBySource,
}: ConflictTriageViewProps) {
  // Memoize groupings
  const categories = useMemo(() => groupDiscrepancies(discrepancies), [discrepancies]);
  const byField = useMemo(() => groupByField(discrepancies), [discrepancies]);
  const bySource = useMemo(() => groupBySource(discrepancies), [discrepancies]);
  
  const handleCategoryAction = (category: TriageCategory) => {
    switch (category.id) {
      case "auto":
        onAutoResolve(category.items);
        break;
      case "review":
        onStartReview(category.items);
        break;
      case "error":
        onStartReview(category.items);
        break;
      case "low":
        onDismiss(category.items);
        break;
    }
  };
  
  const totalConflicts = discrepancies.length;
  const totalEnrichments = enrichments.length;
  
  return (
    <div className="space-y-6">
      {/* Summary Banner */}
      <Card className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-primary/20">
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Audit Summary</h2>
              <p className="text-sm text-muted-foreground">
                {totalConflicts} conflicts • {totalEnrichments} enrichment opportunities
              </p>
            </div>
            <div className="flex items-center gap-4">
              {categories[0].items.length > 0 && (
                <Button
                  onClick={() => onAutoResolve(categories[0].items)}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Quick Resolve {categories[0].items.length} Items
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Category Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {categories.map((category) => (
          <TriageCard
            key={category.id}
            category={category}
            onAction={() => handleCategoryAction(category)}
          />
        ))}
      </div>
      
      {/* Field Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Conflicts by Field</CardTitle>
          <CardDescription>
            Click a field to filter and review those conflicts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {byField.map(({ field, total, autoResolvable, needsReview }) => {
              const Icon = FIELD_ICONS[field] || FileText;
              const label = FIELD_LABELS[field] || field.replace(/_/g, ' ');
              
              return (
                <div
                  key={field}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                  onClick={() => onFilterByField(field)}
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-md bg-muted">
                      <Icon className="w-4 h-4 text-muted-foreground" />
                    </div>
                    <span className="font-medium">{label}</span>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    {/* Mini breakdown badges */}
                    <div className="flex gap-1">
                      {autoResolvable > 0 && (
                        <Badge 
                          variant="outline" 
                          className="text-xs bg-emerald-500/10 text-emerald-600 border-emerald-500/30"
                        >
                          {autoResolvable} auto
                        </Badge>
                      )}
                      {needsReview > 0 && (
                        <Badge 
                          variant="outline" 
                          className="text-xs bg-amber-500/10 text-amber-600 border-amber-500/30"
                        >
                          {needsReview} review
                        </Badge>
                      )}
                    </div>
                    
                    <span className="text-muted-foreground font-medium w-8 text-right">
                      {total}
                    </span>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </div>
                </div>
              );
            })}
            
            {byField.length === 0 && (
              <p className="text-center text-muted-foreground py-4">
                No conflicts to display
              </p>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* Source Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Conflicts by Source</CardTitle>
          <CardDescription>
            See which auction houses have the most conflicts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {bySource.map(({ source, total, avgTrust }) => (
              <div
                key={source}
                className="p-4 border rounded-lg cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => onFilterBySource(source)}
              >
                <SourceBadge source={source} size="md" />
                <div className="mt-3">
                  <div className="text-2xl font-bold">{total}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <Progress 
                      value={avgTrust} 
                      className="h-1.5 flex-1"
                    />
                    <span className="text-xs text-muted-foreground">
                      {avgTrust}%
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    avg trust
                  </div>
                </div>
              </div>
            ))}
            
            {bySource.length === 0 && (
              <p className="col-span-full text-center text-muted-foreground py-4">
                No source data available
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ConflictTriageView;
