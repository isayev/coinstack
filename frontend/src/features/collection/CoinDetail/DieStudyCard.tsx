/**
 * DieStudyCard - Simplified die study information display
 * 
 * Features:
 * - Die axis with clock visualization
 * - Die match indicators
 * - Known die statistics (if available)
 * - Control marks display
 * - Collapsible for space saving
 * 
 * @module features/collection/CoinDetail/DieStudyCard
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp, CircleDot, Hash, Layers } from 'lucide-react';
import { DieAxisClock } from '@/components/coins/DieAxisClock';
import { cn } from '@/lib/utils';

interface DieStudyCardProps {
  /** Die axis value (0-12 clock hours) */
  dieAxis?: number | null;
  /** Die match information */
  dieMatch?: {
    obverseDie?: string | null;
    reverseDie?: string | null;
    isKnownCombination?: boolean;
    matchingCoins?: number;
  } | null;
  /** Control marks on the coin */
  controlMarks?: string[] | null;
  /** Die statistics */
  dieStats?: {
    knownObverseDies?: number;
    knownReverseDies?: number;
    estimatedMintage?: string;
  } | null;
  /** Category type for styling */
  categoryType?: string;
  /** Start collapsed */
  defaultExpanded?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function DieStudyCard({
  dieAxis,
  dieMatch,
  controlMarks,
  dieStats,
  categoryType = 'imperial',
  defaultExpanded = false,
  className,
}: DieStudyCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Check if there's any meaningful data to show
  const hasData = dieAxis != null || dieMatch || (controlMarks && controlMarks.length > 0) || dieStats;

  if (!hasData) {
    return null; // Don't render if no die study data
  }

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

      {/* Header - clickable to expand/collapse */}
      <button
        className="w-full flex items-center justify-between px-5 py-4 pl-7"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <Layers size={18} style={{ color: 'var(--text-muted)' }} />
          <h2
            className="text-base font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >
            Die Study
          </h2>
        </div>

        <div className="flex items-center gap-3">
          {/* Quick die axis preview */}
          {dieAxis != null && !isExpanded && (
            <span
              className="text-xs font-mono"
              style={{ color: 'var(--text-muted)' }}
            >
              ↑{dieAxis}h
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
          className="px-5 pb-5 pl-7 space-y-5 border-t"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          {/* Die Axis Section */}
          {dieAxis != null && (
            <div className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <span
                    className="text-[10px] font-bold uppercase tracking-wider block mb-1"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Die Axis
                  </span>
                  <span
                    className="text-sm font-mono"
                    style={{ color: 'var(--text-primary)' }}
                  >
                    {dieAxis} o'clock ({dieAxis * 30}°)
                  </span>
                </div>
                <DieAxisClock axis={dieAxis} size="lg" />
              </div>
              <p
                className="text-xs mt-2"
                style={{ color: 'var(--text-muted)' }}
              >
                {getDieAxisDescription(dieAxis)}
              </p>
            </div>
          )}

          {/* Die Match Section */}
          {dieMatch && (dieMatch.obverseDie || dieMatch.reverseDie) && (
            <div className="pt-2">
              <span
                className="text-[10px] font-bold uppercase tracking-wider block mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                Die Identification
              </span>
              <div className="grid grid-cols-2 gap-4">
                {dieMatch.obverseDie && (
                  <div>
                    <span
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Obverse Die
                    </span>
                    <span
                      className="text-sm font-mono"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {dieMatch.obverseDie}
                    </span>
                  </div>
                )}
                {dieMatch.reverseDie && (
                  <div>
                    <span
                      className="text-xs block mb-1"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Reverse Die
                    </span>
                    <span
                      className="text-sm font-mono"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {dieMatch.reverseDie}
                    </span>
                  </div>
                )}
              </div>
              {dieMatch.matchingCoins && dieMatch.matchingCoins > 1 && (
                <p
                  className="text-xs mt-2"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  <CircleDot size={12} className="inline mr-1" />
                  {dieMatch.matchingCoins} known specimens from this die combination
                </p>
              )}
            </div>
          )}

          {/* Control Marks Section */}
          {controlMarks && controlMarks.length > 0 && (
            <div className="pt-2">
              <span
                className="text-[10px] font-bold uppercase tracking-wider block mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                Control Marks
              </span>
              <div className="flex flex-wrap gap-2">
                {controlMarks.map((mark, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded"
                    style={{
                      background: 'var(--bg-subtle)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    <Hash size={12} />
                    {mark}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Die Statistics Section */}
          {dieStats && (
            <div className="pt-2">
              <span
                className="text-[10px] font-bold uppercase tracking-wider block mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                Die Statistics
              </span>
              <div className="grid grid-cols-3 gap-4 text-center">
                {dieStats.knownObverseDies && (
                  <div>
                    <span
                      className="text-lg font-bold block"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {dieStats.knownObverseDies}
                    </span>
                    <span
                      className="text-[10px]"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Obv. Dies
                    </span>
                  </div>
                )}
                {dieStats.knownReverseDies && (
                  <div>
                    <span
                      className="text-lg font-bold block"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {dieStats.knownReverseDies}
                    </span>
                    <span
                      className="text-[10px]"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Rev. Dies
                    </span>
                  </div>
                )}
                {dieStats.estimatedMintage && (
                  <div>
                    <span
                      className="text-lg font-bold block"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {dieStats.estimatedMintage}
                    </span>
                    <span
                      className="text-[10px]"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Est. Mintage
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Get human-readable description of die axis
 */
function getDieAxisDescription(axis: number): string {
  if (axis === 6) {
    return 'Medallic alignment (most common for Roman Imperial)';
  }
  if (axis === 12 || axis === 0) {
    return 'Coin alignment (standard for modern coins)';
  }
  if (axis === 5 || axis === 7) {
    return 'Near medallic alignment (slight rotation)';
  }
  if (axis === 11 || axis === 1) {
    return 'Near coin alignment (slight rotation)';
  }
  return 'Irregular die axis (possible die shift or provincial issue)';
}
