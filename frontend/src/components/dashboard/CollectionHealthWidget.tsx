/**
 * CollectionHealthWidget - Shows data completeness at a glance
 * 
 * Displays overall collection health percentage and breakdown
 * by category (images, attribution, references, provenance, values)
 */

import { cn } from "@/lib/utils";
import { 
  CheckCircle2, 
  AlertCircle, 
  XCircle, 
  Image, 
  User, 
  BookOpen, 
  History, 
  DollarSign,
  HelpCircle,
  Sparkles,
  ClipboardCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface HealthCategory {
  name: string;
  complete: number;
  total: number;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
}

interface CollectionHealthWidgetProps {
  overallPct: number;
  totalCoins: number;
  withImages: number;
  withAttribution: number;
  withReferences: number;
  withProvenance: number;
  withValues: number;
  onRunAudit?: () => void;
  onEnrichAll?: () => void;
  className?: string;
}

function getStatus(complete: number, total: number): 'good' | 'warning' | 'poor' {
  if (total === 0) return 'good';
  const pct = (complete / total) * 100;
  if (pct >= 80) return 'good';
  if (pct >= 50) return 'warning';
  return 'poor';
}

function StatusIcon({ status }: { status: 'good' | 'warning' | 'poor' }) {
  if (status === 'good') {
    return <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--health-good)' }} />;
  }
  if (status === 'warning') {
    return <AlertCircle className="w-4 h-4" style={{ color: 'var(--health-warning)' }} />;
  }
  return <XCircle className="w-4 h-4" style={{ color: 'var(--health-poor)' }} />;
}

function HealthRow({ 
  icon: Icon, 
  name, 
  complete, 
  total 
}: HealthCategory) {
  const status = getStatus(complete, total);
  const pct = total > 0 ? Math.round((complete / total) * 100) : 0;
  
  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2">
        <StatusIcon status={status} />
        <Icon className="w-3.5 h-3.5" style={{ color: 'var(--text-muted)' }} />
        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          {name}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          {complete}/{total}
        </span>
        <span 
          className="text-xs w-10 text-right"
          style={{ color: `var(--health-${status})` }}
        >
          {pct}%
        </span>
      </div>
    </div>
  );
}

export function CollectionHealthWidget({
  overallPct,
  totalCoins,
  withImages,
  withAttribution,
  withReferences,
  withProvenance,
  withValues,
  onRunAudit,
  onEnrichAll,
  className,
}: CollectionHealthWidgetProps) {
  const categories: HealthCategory[] = [
    { name: 'Images', complete: withImages, total: totalCoins, icon: Image },
    { name: 'Attribution', complete: withAttribution, total: totalCoins, icon: User },
    { name: 'References', complete: withReferences, total: totalCoins, icon: BookOpen },
    { name: 'Provenance', complete: withProvenance, total: totalCoins, icon: History },
    { name: 'Values', complete: withValues, total: totalCoins, icon: DollarSign },
  ];

  const overallStatus = overallPct >= 80 ? 'good' : overallPct >= 50 ? 'warning' : 'poor';

  return (
    <div
      className={cn('rounded-lg p-4', className)}
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 
          className="text-sm font-semibold uppercase tracking-wide"
          style={{ color: 'var(--text-muted)' }}
        >
          Collection Health
        </h3>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="p-1 rounded hover:bg-[var(--bg-hover)]">
                <HelpCircle className="w-4 h-4" style={{ color: 'var(--text-ghost)' }} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="left" className="max-w-xs">
              <p className="text-xs">
                Health score measures data completeness. Higher scores mean better cataloging.
                Images (30%), Attribution (25%), References (20%), Provenance (15%), Values (10%).
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Overall Score */}
      <div className="mb-4">
        <div className="flex items-baseline justify-between mb-2">
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Overall
          </span>
          <span 
            className="text-2xl font-bold"
            style={{ color: `var(--health-${overallStatus})` }}
          >
            {overallPct}%
          </span>
        </div>
        <div 
          className="h-3 rounded-full overflow-hidden"
          style={{ background: 'var(--bg-elevated)' }}
        >
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${overallPct}%`,
              background: `var(--health-${overallStatus})`,
            }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-[10px]" style={{ color: 'var(--text-ghost)' }}>
            Needs Work
          </span>
          <span className="text-[10px]" style={{ color: 'var(--text-ghost)' }}>
            Complete
          </span>
        </div>
      </div>

      {/* Category Breakdown */}
      <div 
        className="rounded-md p-3 mb-4"
        style={{ background: 'var(--bg-elevated)' }}
      >
        {categories.map((category) => (
          <HealthRow key={category.name} {...category} />
        ))}
      </div>

      {/* Action Buttons */}
      {(onRunAudit || onEnrichAll) && (
        <div className="flex gap-2">
          {onRunAudit && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRunAudit}
              className="flex-1 gap-1.5"
            >
              <ClipboardCheck className="w-3.5 h-3.5" />
              Run Audit
            </Button>
          )}
          {onEnrichAll && (
            <Button
              variant="outline"
              size="sm"
              onClick={onEnrichAll}
              className="flex-1 gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5" />
              AI Enrich
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
