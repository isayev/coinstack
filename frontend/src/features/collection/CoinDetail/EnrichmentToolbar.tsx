/**
 * EnrichmentToolbar - Compact toolbar for AI enrichment actions
 * 
 * Features:
 * - Quick access to all LLM capabilities
 * - Progress indicator during enrichment
 * - Shows which fields have been enriched
 * - Collapsible for space saving
 * 
 * @module features/collection/CoinDetail/EnrichmentToolbar
 */

import { useState } from 'react';
import { 
  Sparkles, 
  BookOpen, 
  Eye, 
  FileText, 
  Check, 
  Loader2,
  ChevronDown,
  ChevronRight 
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface EnrichmentAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  description: string;
  isComplete?: boolean;
  isLoading?: boolean;
  onClick?: () => void;
  disabled?: boolean;
}

interface EnrichmentToolbarProps {
  /** Enrichment actions configuration */
  actions: EnrichmentAction[];
  /** Overall loading state */
  isEnriching?: boolean;
  /** Category type for styling */
  categoryType?: string;
  /** Compact/expanded state */
  defaultExpanded?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function EnrichmentToolbar({
  actions,
  isEnriching = false,
  categoryType = 'imperial',
  defaultExpanded = true,
  className,
}: EnrichmentToolbarProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const completedCount = actions.filter(a => a.isComplete).length;
  const totalCount = actions.length;

  return (
    <div
      className={cn('relative rounded-xl overflow-hidden', className)}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Category bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[6px]"
        style={{ background: `var(--cat-${categoryType})` }}
      />

      {/* Header */}
      <button
        className="w-full flex items-center justify-between px-5 py-3 pl-7"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <Sparkles
            size={16}
            className={cn(isEnriching && 'animate-pulse')}
            style={{ color: 'var(--accent-ai, #a855f7)' }}
          />
          <span
            className="text-sm font-medium"
            style={{ color: 'var(--text-primary)' }}
          >
            AI Enrichment
          </span>
          <span
            className="text-xs px-2 py-0.5 rounded"
            style={{
              background: completedCount === totalCount ? 'var(--bg-success, #22c55e20)' : 'var(--bg-subtle)',
              color: completedCount === totalCount ? 'var(--text-success, #22c55e)' : 'var(--text-muted)',
            }}
          >
            {completedCount}/{totalCount} complete
          </span>
        </div>

        {isExpanded ? (
          <ChevronDown size={16} style={{ color: 'var(--text-muted)' }} />
        ) : (
          <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
        )}
      </button>

      {/* Actions grid */}
      {isExpanded && (
        <div
          className="px-5 pb-4 pl-7 grid grid-cols-2 gap-2"
        >
          {actions.map((action) => (
            <EnrichmentButton
              key={action.id}
              action={action}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Individual enrichment action button
 */
interface EnrichmentButtonProps {
  action: EnrichmentAction;
}

function EnrichmentButton({ action }: EnrichmentButtonProps) {
  const { label, icon, description, isComplete, isLoading, onClick, disabled } = action;

  return (
    <button
      className={cn(
        'flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-all',
        'border',
        disabled && 'opacity-50 cursor-not-allowed',
        isComplete && 'bg-[var(--bg-success,#22c55e10)]'
      )}
      style={{
        background: isComplete ? 'var(--bg-success, #22c55e10)' : 'var(--bg-subtle)',
        borderColor: isComplete ? 'var(--border-success, #22c55e40)' : 'var(--border-subtle)',
      }}
      onClick={onClick}
      disabled={disabled || isLoading}
      title={description}
    >
      <div
        className="flex-shrink-0"
        style={{ 
          color: isComplete 
            ? 'var(--text-success, #22c55e)' 
            : isLoading 
              ? 'var(--accent-ai, #a855f7)' 
              : 'var(--text-muted)' 
        }}
      >
        {isLoading ? (
          <Loader2 size={14} className="animate-spin" />
        ) : isComplete ? (
          <Check size={14} />
        ) : (
          icon
        )}
      </div>
      <span
        className="text-xs font-medium truncate"
        style={{ 
          color: isComplete 
            ? 'var(--text-success, #22c55e)' 
            : 'var(--text-secondary)' 
        }}
      >
        {label}
      </span>
    </button>
  );
}

/**
 * Pre-configured enrichment actions for coin detail page
 */
export function useCoinEnrichmentActions(options: {
  onExpandObverse?: () => void;
  onExpandReverse?: () => void;
  onGenerateContext?: () => void;
  onObserveCondition?: () => void;
  hasObverseLegendExpanded?: boolean;
  hasReverseLegendExpanded?: boolean;
  hasHistoricalContext?: boolean;
  hasConditionObservations?: boolean;
  isExpandingObverse?: boolean;
  isExpandingReverse?: boolean;
  isGeneratingContext?: boolean;
  isObservingCondition?: boolean;
}): EnrichmentAction[] {
  return [
    {
      id: 'obverse-legend',
      label: 'Obverse Legend',
      icon: <FileText size={14} />,
      description: 'Expand obverse legend abbreviations',
      isComplete: options.hasObverseLegendExpanded,
      isLoading: options.isExpandingObverse,
      onClick: options.onExpandObverse,
      disabled: !options.onExpandObverse,
    },
    {
      id: 'reverse-legend',
      label: 'Reverse Legend',
      icon: <FileText size={14} />,
      description: 'Expand reverse legend abbreviations',
      isComplete: options.hasReverseLegendExpanded,
      isLoading: options.isExpandingReverse,
      onClick: options.onExpandReverse,
      disabled: !options.onExpandReverse,
    },
    {
      id: 'historical-context',
      label: 'Historical Context',
      icon: <BookOpen size={14} />,
      description: 'Generate historical context',
      isComplete: options.hasHistoricalContext,
      isLoading: options.isGeneratingContext,
      onClick: options.onGenerateContext,
      disabled: !options.onGenerateContext,
    },
    {
      id: 'condition',
      label: 'Condition Notes',
      icon: <Eye size={14} />,
      description: 'Observe wear patterns (not grades)',
      isComplete: options.hasConditionObservations,
      isLoading: options.isObservingCondition,
      onClick: options.onObserveCondition,
      disabled: !options.onObserveCondition,
    },
  ];
}
