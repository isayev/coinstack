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

import { DieInfo, Monogram } from '@/domain/schemas';

interface DieStudyCardProps {
  /** Die axis value (0-12 clock hours) */
  dieAxis?: number | null;
  /** Die match information (Research Grade) */
  dieInfo?: DieInfo | null;
  /** Monograms */
  monograms?: Monogram[] | null;
  /** Legacy Die match information (deprecated but kept for compatibility) */
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
  dieInfo,
  monograms,
  dieMatch,
  controlMarks,
  dieStats,
  categoryType = 'imperial',
  defaultExpanded = false,
  className,
}: DieStudyCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Use dieInfo if available, otherwise fall back to dieMatch
  const displayObverseDie = dieInfo?.obverse_die_id ?? dieMatch?.obverseDie;
  const displayReverseDie = dieInfo?.reverse_die_id ?? dieMatch?.reverseDie;

  // Check if there's any meaningful data to show
  const hasData = dieAxis != null || displayObverseDie || displayReverseDie || (controlMarks && controlMarks.length > 0) || (monograms && monograms.length > 0) || dieStats;

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
          {(displayObverseDie || displayReverseDie) && (
            <div className="pt-2">
              <span
                className="text-[10px] font-bold uppercase tracking-wider block mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                Die Identification
              </span>
              <div className="grid grid-cols-2 gap-4">
                {displayObverseDie && (
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
                      {displayObverseDie}
                    </span>
                  </div>
                )}
                {displayReverseDie && (
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
                      {displayReverseDie}
                    </span>
                  </div>
                )}
              </div>
              {dieMatch?.matchingCoins && dieMatch.matchingCoins > 1 && (
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

          {/* Monograms Section */}
          {monograms && monograms.length > 0 && (
            <div className="pt-2">
              <span
                className="text-[10px] font-bold uppercase tracking-wider block mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                Monograms
              </span>
              <div className="flex flex-wrap gap-3">
                {monograms.map((m, i) => (
                  <div
                    key={m.id || i}
                    className="flex flex-col items-center justify-center p-2 rounded w-16 h-16 h-auto min-h-[64px]"
                    style={{
                      background: 'var(--bg-subtle)',
                      border: '1px solid var(--border-subtle)'
                    }}
                    title={m.label}
                  >
                    {m.image_url ? (
                      <img src={m.image_url} alt={m.label} className="h-8 w-8 object-contain mb-1 opacity-80" />
                    ) : (
                      <Hash size={20} style={{ color: 'var(--text-muted)' }} className="mb-1" />
                    )}
                    <span
                      className="text-[10px] font-mono text-center leading-tight truncate w-full px-1"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {m.label}
                    </span>
                  </div>
                ))}
              </div>
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
