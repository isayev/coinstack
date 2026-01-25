/**
 * RulerTimeline - Horizontal bar chart showing coin distribution by ruler
 * 
 * Features:
 * - Sorted by count or reign date
 * - Click to filter by ruler
 * - Hover shows ruler details
 */

import { useState } from "react";
import { cn } from "@/lib/utils";
import { ArrowUpDown, Crown } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RulerData {
  ruler: string;
  rulerId?: number | null;
  count: number;
  reignStart?: number | null;
}

interface RulerTimelineProps {
  data: RulerData[];
  sortBy?: 'count' | 'reign';
  maxVisible?: number;
  onRulerClick?: (ruler: string, rulerId?: number | null) => void;
  activeRuler?: string | null;
  className?: string;
}

export function RulerTimeline({
  data,
  sortBy: initialSortBy = 'count',
  maxVisible = 8,
  onRulerClick,
  activeRuler,
  className,
}: RulerTimelineProps) {
  const [sortBy, setSortBy] = useState<'count' | 'reign'>(initialSortBy);
  const [showAll, setShowAll] = useState(false);

  // Sort data
  const sortedData = [...data].sort((a, b) => {
    if (sortBy === 'count') {
      return b.count - a.count;
    }
    // Sort by reign (oldest first, nulls at end)
    const aStart = a.reignStart ?? Number.MAX_SAFE_INTEGER;
    const bStart = b.reignStart ?? Number.MAX_SAFE_INTEGER;
    return aStart - bStart;
  });

  const visibleData = showAll ? sortedData : sortedData.slice(0, maxVisible);
  const maxCount = Math.max(...data.map(d => d.count), 1);
  const hiddenCount = sortedData.length - maxVisible;

  const toggleSort = () => {
    setSortBy(sortBy === 'count' ? 'reign' : 'count');
  };

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
        <div className="flex items-center gap-2">
          <Crown className="w-4 h-4" style={{ color: 'var(--metal-au)' }} />
          <h3 
            className="text-sm font-semibold uppercase tracking-wide"
            style={{ color: 'var(--text-muted)' }}
          >
            By Ruler
          </h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSort}
          className="h-7 px-2 gap-1"
          title={`Sort by ${sortBy === 'count' ? 'reign date' : 'count'}`}
        >
          <ArrowUpDown className="w-3 h-3" />
          <span className="text-xs">{sortBy === 'count' ? 'Count' : 'Reign'}</span>
        </Button>
      </div>

      {/* Ruler Bars */}
      <div className="space-y-2">
        {visibleData.map(({ ruler, rulerId, count, reignStart }) => {
          const width = (count / maxCount) * 100;
          const isActive = activeRuler === ruler;
          
          return (
            <div
              key={ruler}
              role={onRulerClick ? 'button' : undefined}
              tabIndex={onRulerClick ? 0 : undefined}
              onClick={() => onRulerClick?.(ruler, rulerId)}
              onKeyDown={(e) => e.key === 'Enter' && onRulerClick?.(ruler, rulerId)}
              className={cn(
                'group relative flex items-center gap-3 py-1 rounded transition-all',
                onRulerClick && 'cursor-pointer hover:bg-[var(--bg-hover)]',
                isActive && 'bg-[var(--bg-hover)]'
              )}
              title={reignStart ? `${ruler} (${reignStart > 0 ? reignStart + ' AD' : Math.abs(reignStart) + ' BC'})` : ruler}
            >
              {/* Ruler Name */}
              <span 
                className={cn(
                  'w-24 truncate text-sm',
                  isActive ? 'font-semibold' : 'font-medium'
                )}
                style={{ color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}
              >
                {ruler}
              </span>
              
              {/* Bar */}
              <div className="flex-1 h-4 relative">
                <div 
                  className="absolute inset-y-0 left-0 rounded transition-all duration-300"
                  style={{
                    width: `${width}%`,
                    background: isActive 
                      ? 'var(--cat-imperial)' 
                      : 'linear-gradient(90deg, var(--cat-imperial), var(--cat-imperial-subtle))',
                    opacity: isActive ? 1 : 0.7,
                  }}
                />
              </div>
              
              {/* Count */}
              <span 
                className="w-8 text-right text-sm font-bold"
                style={{ color: 'var(--text-primary)' }}
              >
                {count}
              </span>
            </div>
          );
        })}
      </div>

      {/* Show More */}
      {hiddenCount > 0 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="w-full mt-3 py-2 text-xs font-medium rounded transition-colors hover:bg-[var(--bg-hover)]"
          style={{ color: 'var(--text-muted)' }}
        >
          {showAll ? 'Show less' : `+${hiddenCount} more rulers...`}
        </button>
      )}

      {/* Empty State */}
      {data.length === 0 && (
        <div 
          className="text-center py-4 text-sm"
          style={{ color: 'var(--text-muted)' }}
        >
          No ruler data available
        </div>
      )}
    </div>
  );
}
