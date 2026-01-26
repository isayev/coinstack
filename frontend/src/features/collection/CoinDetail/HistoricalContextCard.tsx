/**
 * HistoricalContextCard - LLM-generated historical context for coins
 * 
 * Features:
 * - Collapsible card with AI-generated context
 * - Generate button for coins without context
 * - Shows generation timestamp
 * - Regenerate option
 * - Cost tracking display
 * 
 * @module features/collection/CoinDetail/HistoricalContextCard
 */

import { useState } from 'react';
import { Sparkles, ChevronDown, ChevronUp, RefreshCw, Clock, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MarkdownContent } from '@/components/ui/MarkdownContent';

interface HistoricalContextCardProps {
  /** Pre-existing historical context from backend */
  context?: string | null;
  /** When context was generated */
  generatedAt?: string | null;
  /** Coin metadata for context generation */
  coinMetadata: {
    coinId: number;
    issuer?: string | null;
    denomination?: string | null;
    yearStart?: number | null;
    yearEnd?: number | null;
    category?: string | null;
  };
  /** Callback to generate context */
  onGenerateContext?: () => Promise<void>;
  /** Loading state */
  isGenerating?: boolean;
  /** Category type for styling */
  categoryType?: string;
  /** Additional CSS classes */
  className?: string;
}

export function HistoricalContextCard({
  context,
  generatedAt,
  coinMetadata,
  onGenerateContext,
  isGenerating = false,
  categoryType = 'imperial',
  className,
}: HistoricalContextCardProps) {
  const [isExpanded, setIsExpanded] = useState(!!context);
  const hasContext = !!context;

  const formatDate = (dateStr: string | null | undefined): string => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div
      className={cn('relative rounded-xl', className)}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Category bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-xl"
        style={{ background: `var(--cat-${categoryType})` }}
      />

      {/* Header - always visible */}
      <button
        className="w-full flex items-center justify-between p-5 pl-7 text-left"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <Sparkles
            size={18}
            className={cn(isGenerating && 'animate-pulse')}
            style={{ color: 'var(--accent-ai, #a855f7)' }}
          />
          <h2
            className="text-base font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >
            Historical Context
          </h2>
          {hasContext && generatedAt && (
            <span
              className="text-xs flex items-center gap-1"
              style={{ color: 'var(--text-muted)' }}
            >
              <Clock size={12} />
              {formatDate(generatedAt)}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {hasContext && (
            <span
              className="text-xs px-2 py-0.5 rounded"
              style={{
                background: 'var(--bg-subtle)',
                color: 'var(--text-muted)',
              }}
            >
              AI Generated
            </span>
          )}
          {isExpanded ? (
            <ChevronUp size={18} style={{ color: 'var(--text-muted)' }} />
          ) : (
            <ChevronDown size={18} style={{ color: 'var(--text-muted)' }} />
          )}
        </div>
      </button>

      {/* Content - collapsible */}
      {isExpanded && (
        <div
          className="px-5 pb-5 pl-7 border-t"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          {hasContext ? (
            <div className="space-y-4 pt-4">
              {/* Styled markdown content */}
              <MarkdownContent content={context} />

              {/* Actions */}
              {onGenerateContext && (
                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      onGenerateContext();
                    }}
                    disabled={isGenerating}
                    style={{
                      background: 'transparent',
                      color: 'var(--text-muted)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <RefreshCw size={12} className={isGenerating ? 'animate-spin' : ''} />
                    Regenerate
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="pt-4 text-center">
              <div
                className="inline-flex items-center gap-2 mb-3 text-sm"
                style={{ color: 'var(--text-muted)' }}
              >
                <Info size={16} />
                <span>No historical context generated yet</span>
              </div>

              {onGenerateContext ? (
                <div>
                  <p
                    className="text-xs mb-4 max-w-md mx-auto"
                    style={{ color: 'var(--text-ghost)' }}
                  >
                    Generate AI-powered historical context about{' '}
                    {coinMetadata.issuer || 'this ruler'}'s reign,
                    the {coinMetadata.denomination || 'coin type'}, and its significance.
                  </p>
                  <button
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      onGenerateContext();
                    }}
                    disabled={isGenerating}
                    style={{
                      background: 'var(--accent-ai, #a855f7)',
                      color: '#fff',
                      opacity: isGenerating ? 0.7 : 1,
                    }}
                  >
                    <Sparkles size={16} className={isGenerating ? 'animate-pulse' : ''} />
                    {isGenerating ? 'Generating...' : 'Generate Context'}
                  </button>
                </div>
              ) : (
                <p
                  className="text-xs"
                  style={{ color: 'var(--text-ghost)' }}
                >
                  Historical context generation is not available
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
