/**
 * SpecificationsCard - Combined Physical + Condition specifications
 * 
 * Two-column layout displaying:
 * - Physical: Weight, Diameter, Die Axis, Metal, Die State, Officina, Moneyer
 * - Condition: Grade, Strike, Surface, Eye Appeal, Toning, Attribution
 * 
 * Design principle: Cards detail (complementing the identification header)
 * 
 * @module features/collection/CoinDetail/SpecificationsCard
 */

import { memo } from 'react';
import { Coin } from '@/domain/schemas';
import { CategoryBar } from '@/components/ui/CategoryBar';
import { GradeBadge } from '@/components/design-system/GradeBadge';
import { RarityIndicator } from '@/components/design-system/RarityIndicator';
import { DieAxisClock } from '@/components/coins/DieAxisClock';
import { cn } from '@/lib/utils';

interface SpecificationsCardProps {
  coin: Coin;
  categoryType: string;
  className?: string;
}

/**
 * Individual specification row with label and value
 */
interface SpecRowProps {
  label: string;
  value: React.ReactNode;
  className?: string;
}

function SpecRow({ label, value, className }: SpecRowProps) {
  if (value === null || value === undefined) return null;

  return (
    <div className={cn('flex justify-between items-start gap-4 py-1.5', className)}>
      <span
        className="text-xs font-medium uppercase tracking-wide shrink-0"
        style={{ color: 'var(--text-muted)' }}
      >
        {label}
      </span>
      <span
        className="text-sm font-medium text-right"
        style={{ color: 'var(--text-primary)' }}
      >
        {value}
      </span>
    </div>
  );
}

/**
 * Format metal display with optional badge styling
 */
function formatMetal(metal?: string): string {
  if (!metal) return '—';
  const metalMap: Record<string, string> = {
    'gold': 'AV (Gold)',
    'silver': 'AR (Silver)',
    'bronze': 'AE (Bronze)',
    'billon': 'BI (Billon)',
    'electrum': 'EL (Electrum)',
    'orichalcum': 'Orichalcum',
    'copper': 'Copper',
    'ae': 'AE',
    'ar': 'AR',
    'av': 'AV',
  };
  return metalMap[metal.toLowerCase()] || metal;
}

/**
 * Format attribution confidence with visual indicator
 */
function AttributionBadge({ confidence }: { confidence: string }) {
  const colors: Record<string, { bg: string; text: string }> = {
    'certain': { bg: 'var(--bg-success)', text: 'var(--text-success)' },
    'probable': { bg: 'var(--bg-warning)', text: 'var(--text-warning)' },
    'possible': { bg: 'rgba(234, 179, 8, 0.08)', text: 'var(--text-warning)' },
    'uncertain': { bg: 'var(--bg-error)', text: 'var(--text-error)' },
  };

  const style = colors[confidence.toLowerCase()] || colors['uncertain'];

  return (
    <span
      className="px-2 py-0.5 rounded text-xs font-medium capitalize"
      style={{ background: style.bg, color: style.text }}
    >
      {confidence}
    </span>
  );
}

export const SpecificationsCard = memo(function SpecificationsCard({
  coin,
  categoryType,
  className
}: SpecificationsCardProps) {
  // Get die axis for clock display
  const dieAxis = coin.dimensions?.die_axis;

  return (
    <div
      className={cn(
        'specifications-card relative rounded-xl p-5',
        className
      )}
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Category bar */}
      <CategoryBar categoryType={categoryType} />

      {/* Title */}
      <h2
        className="text-base font-semibold mb-4 pl-2"
        style={{ color: 'var(--text-primary)' }}
      >
        Specifications
      </h2>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pl-2">
        {/* Physical Column */}
        <div className="specs-column">
          <h3
            className="text-xs font-bold uppercase tracking-wider mb-3 pb-2"
            style={{
              color: 'var(--text-muted)',
              borderBottom: '1px solid var(--border-subtle)'
            }}
          >
            Physical
          </h3>

          <div className="space-y-0.5">
            <SpecRow
              label="Weight"
              value={coin.dimensions?.weight_g ? `${coin.dimensions.weight_g}g` : null}
            />
            <SpecRow
              label="Diameter"
              value={coin.dimensions?.diameter_mm ? `${coin.dimensions.diameter_mm}mm` : null}
            />
            {coin.dimensions?.specific_gravity && (
              <SpecRow
                label="Specific Gravity"
                value={coin.dimensions.specific_gravity}
              />
            )}
            <SpecRow
              label="Die Axis"
              value={dieAxis !== null && dieAxis !== undefined ? (
                <div className="flex items-center gap-2">
                  <DieAxisClock axis={dieAxis} size="sm" />
                  <span className="font-mono">↑{dieAxis}h</span>
                </div>
              ) : null}
            />
            <SpecRow
              label="Metal"
              value={formatMetal(coin.metal)}
            />
            {coin.issue_status && coin.issue_status !== 'official' && (
              <SpecRow
                label="Issue Status"
                value={<span className="capitalize font-bold text-red-500">{coin.issue_status.replace('_', ' ')}</span>}
              />
            )}
            {coin.die_state && (
              <SpecRow
                label="Die State"
                value={<span className="capitalize">{coin.die_state}</span>}
              />
            )}
            {coin.officina && (
              <SpecRow
                label="Officina"
                value={coin.officina}
              />
            )}
            {coin.moneyer && (
              <SpecRow
                label="Moneyer"
                value={coin.moneyer}
              />
            )}
            {/* Find Data */}
            {(coin.find_data?.find_spot || coin.find_data?.find_date) && (
              <>
                <div className="my-3 border-t" style={{ borderColor: 'var(--border-subtle)' }} />
                <SpecRow
                  label="Find Spot"
                  value={coin.find_data?.find_spot}
                />
                <SpecRow
                  label="Find Date"
                  value={coin.find_data?.find_date}
                />
              </>
            )}
          </div>
        </div>

        {/* Condition Column */}
        <div className="specs-column">
          <h3
            className="text-xs font-bold uppercase tracking-wider mb-3 pb-2"
            style={{
              color: 'var(--text-muted)',
              borderBottom: '1px solid var(--border-subtle)'
            }}
          >
            Condition
          </h3>

          <div className="space-y-0.5">
            {/* Grade with badge */}
            <SpecRow
              label="Grade"
              value={
                <div className="flex items-center gap-2">
                  <GradeBadge
                    grade={coin.grading?.grade ?? '?'}
                    service={coin.grading?.service === 'none' ? null : (coin.grading?.service?.toUpperCase() as 'NGC' | 'PCGS' | null)}
                    size="sm"
                  />
                  {coin.grading?.certification_number && (
                    <span
                      className="text-xs font-mono"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      #{coin.grading.certification_number}
                    </span>
                  )}
                </div>
              }
            />

            {/* Strike and Surface on same row if both exist */}
            {(coin.grading?.strike || coin.grading?.surface) && (
              <SpecRow
                label="Strike / Surface"
                value={[
                  coin.grading?.strike ? `${coin.grading.strike}/5` : null,
                  coin.grading?.surface ? `${coin.grading.surface}/5` : null
                ].filter(Boolean).join(' · ') || null}
              />
            )}

            {/* Rarity */}
            {coin.rarity && (
              <SpecRow
                label="Rarity"
                value={<RarityIndicator rarity={coin.rarity} variant="badge" />}
              />
            )}

            {/* Eye Appeal */}
            {coin.eye_appeal && (
              <SpecRow
                label="Eye Appeal"
                value={<span className="capitalize">{coin.eye_appeal}</span>}
              />
            )}

            {/* Toning */}
            {coin.toning_description && (
              <SpecRow
                label="Toning"
                value={coin.toning_description}
              />
            )}

            {/* Attribution Confidence */}
            {coin.attribution_confidence && (
              <SpecRow
                label="Attribution"
                value={<AttributionBadge confidence={coin.attribution_confidence} />}
              />
            )}

            {/* Secondary Treatments */}
            {coin.secondary_treatments && Array.isArray(coin.secondary_treatments) && coin.secondary_treatments.length > 0 && (
              <SpecRow
                label="Treatments"
                value={
                  <div className="flex flex-wrap gap-1 justify-end">
                    {coin.secondary_treatments.map((t: any, i) => (
                      <span
                        key={i}
                        className="text-xs px-1.5 py-0.5 rounded font-medium"
                        style={{
                          background: 'rgba(239, 68, 68, 0.05)',
                          color: 'var(--text-error)',
                          border: '1px solid rgba(239, 68, 68, 0.2)'
                        }}
                        title={t.description}
                      >
                        {t.type}
                      </span>
                    ))}
                  </div>
                }
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
});
