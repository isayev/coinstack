/**
 * CoinDetailV3 - V3.0 specification-compliant coin detail view
 *
 * Layout: 35/65 split
 * - Left (35%): Image viewer with tabs + quick stats
 * - Right (65%): 5 data cards with category bars
 *
 * @module features/collection/CoinDetailV3
 */

import { useState } from 'react';
import { Coin } from '@/domain/schemas';
import { MetalBadge } from '@/components/design-system/MetalBadge';
import { GradeBadge } from '@/components/design-system/GradeBadge';
import { RarityIndicator } from '@/components/design-system/RarityIndicator';
import { parseCategory } from '@/components/design-system/colors';
import { formatYear } from '@/lib/formatters';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Coins, Scale, Ruler, Clock } from 'lucide-react';

interface CoinDetailV3Props {
  coin: Coin;
}

export function CoinDetailV3({ coin }: CoinDetailV3Props) {
  const [selectedImageType, setSelectedImageType] = useState<'obverse' | 'reverse' | 'line'>('obverse');
  const categoryType = parseCategory(coin.category);

  // Format year range
  const displayYear = (): string => {
    const { year_start, year_end } = coin.attribution;
    if (year_start === null || year_start === undefined) return 'Unknown';
    if (year_end === null || year_end === undefined || year_start === year_end) {
      return formatYear(year_start);
    }
    return `${formatYear(year_start)}–${formatYear(year_end)}`;
  };

  // Get images by type
  const obverseImage = coin.images?.find((img: any) => img.image_type === 'obverse')?.url;
  const reverseImage = coin.images?.find((img: any) => img.image_type === 'reverse')?.url;
  const lineImage = coin.images?.find((img: any) => img.image_type === 'line')?.url;
  const primaryImage = coin.images?.find((img: any) => img.is_primary)?.url || coin.images?.[0]?.url;

  // Calculate performance
  const marketValue = (coin as any).market_value;
  const currentValue = marketValue || coin.acquisition?.price;
  const paidPrice = coin.acquisition?.price;
  const performance = currentValue && paidPrice && currentValue !== paidPrice
    ? ((currentValue - paidPrice) / paidPrice) * 100
    : null;

  return (
    <div className="flex gap-6 h-full">
      {/* Left Column (35%): Image Viewer + Quick Stats */}
      <div className="w-[35%] flex flex-col gap-6">
        {/* Image Viewer */}
        <div
          className="relative rounded-lg overflow-hidden"
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {/* Metal badge overlay */}
          {coin.metal && (
            <div className="absolute top-3 right-3 z-10">
              <MetalBadge metal={coin.metal} size="md" showGlow />
            </div>
          )}

          {/* Category bar */}
          <div
            className="absolute left-0 top-0 bottom-0 w-[6px] rounded-l-lg"
            style={{
              background: `var(--cat-${categoryType})`,
            }}
          />

          {/* Image tabs */}
          <Tabs value={selectedImageType} onValueChange={(v: any) => setSelectedImageType(v)} className="w-full">
            <div
              className="px-4 pt-3 pb-2 border-b"
              style={{ borderColor: 'var(--border-subtle)' }}
            >
              <TabsList className="w-full grid grid-cols-3 h-9">
                <TabsTrigger value="obverse" className="text-xs">Obverse</TabsTrigger>
                <TabsTrigger value="reverse" className="text-xs">Reverse</TabsTrigger>
                <TabsTrigger value="line" className="text-xs" disabled={!lineImage}>
                  Line
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Image display */}
            <div className="aspect-[5/4] max-h-[320px] bg-[var(--bg-elevated)] flex items-center justify-center p-6">
              <TabsContent value="obverse" className="m-0 w-full h-full flex items-center justify-center">
                {obverseImage || primaryImage ? (
                  <img
                    src={obverseImage || primaryImage}
                    alt="Obverse"
                    className="max-w-full max-h-full object-contain"
                  />
                ) : (
                  <div className="text-center" style={{ color: 'var(--text-ghost)' }}>
                    <Coins className="w-16 h-16 mx-auto mb-2" />
                    <p className="text-sm">No obverse image</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="reverse" className="m-0 w-full h-full flex items-center justify-center">
                {reverseImage ? (
                  <img
                    src={reverseImage}
                    alt="Reverse"
                    className="max-w-full max-h-full object-contain"
                  />
                ) : (
                  <div className="text-center" style={{ color: 'var(--text-ghost)' }}>
                    <Coins className="w-16 h-16 mx-auto mb-2" />
                    <p className="text-sm">No reverse image</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="line" className="m-0 w-full h-full flex items-center justify-center">
                {lineImage ? (
                  <img
                    src={lineImage}
                    alt="Line Drawing"
                    className="max-w-full max-h-full object-contain"
                  />
                ) : (
                  <div className="text-center" style={{ color: 'var(--text-ghost)' }}>
                    <p className="text-sm">No line drawing</p>
                  </div>
                )}
              </TabsContent>
            </div>
          </Tabs>
        </div>

        {/* Quick Stats Card */}
        <div
          className="relative rounded-lg p-4"
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {/* Category bar */}
          <div
            className="absolute left-0 top-0 bottom-0 w-[4px] rounded-l-lg"
            style={{
              background: `var(--cat-${categoryType})`,
            }}
          />

          <h3
            className="text-sm font-semibold uppercase tracking-wider mb-3"
            style={{ color: 'var(--text-secondary)' }}
          >
            Physical Specs
          </h3>

          <div className="space-y-2">
            {/* Weight */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}>
                <Scale className="w-4 h-4" />
                <span className="text-sm">Weight</span>
              </div>
              <span
                className="text-sm font-mono font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                {coin.dimensions.weight_g ? `${coin.dimensions.weight_g} g` : '—'}
              </span>
            </div>

            {/* Diameter */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}>
                <Ruler className="w-4 h-4" />
                <span className="text-sm">Diameter</span>
              </div>
              <span
                className="text-sm font-mono font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                {coin.dimensions.diameter_mm ? `${coin.dimensions.diameter_mm} mm` : '—'}
              </span>
            </div>

            {/* Die Axis */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}>
                <Clock className="w-4 h-4" />
                <span className="text-sm">Die Axis</span>
              </div>
              <span
                className="text-sm font-mono font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                {coin.dimensions.die_axis !== null && coin.dimensions.die_axis !== undefined
                  ? `${coin.dimensions.die_axis} h`
                  : '—'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column (65%): 5 Data Cards */}
      <div className="flex-1 space-y-6 overflow-y-auto pr-2">
        {/* 1. Identity Card */}
        <DataCard categoryType={categoryType} title="Identity">
          <div className="grid grid-cols-2 gap-x-6 gap-y-3">
            <DataField label="Ruler" value={coin.attribution.issuer} />
            <DataField label="Denomination" value={coin.denomination || '—'} />
            <DataField label="Mint" value={coin.attribution.mint || 'Uncertain'} />
            <DataField label="Date" value={displayYear()} />
            <DataField label="Category" value={coin.category.replace('_', ' ')} />
            <DataField
              label="Portrait"
              value={coin.portrait_subject || '—'}
            />
          </div>
        </DataCard>

        {/* 2. Condition Card */}
        <DataCard categoryType={categoryType} title="Condition & Rarity">
          <div className="space-y-4">
            {/* Grade */}
            <div>
              <div
                className="text-xs font-semibold uppercase tracking-wider mb-2"
                style={{ color: 'var(--text-muted)' }}
              >
                Grade
              </div>
              <div className="flex items-center gap-3">
                <GradeBadge
                  grade={coin.grading.grade ?? '?'}
                  service={coin.grading.service === 'none' ? null : (coin.grading.service as any)}
                  size="md"
                />
                {coin.grading.certification_number && (
                  <span
                    className="text-xs font-mono"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Cert: {coin.grading.certification_number}
                  </span>
                )}
              </div>
            </div>

            {/* Rarity */}
            {(coin as any).rarity && (
              <div>
                <div
                  className="text-xs font-semibold uppercase tracking-wider mb-2"
                  style={{ color: 'var(--text-muted)' }}
                >
                  Rarity
                </div>
                <RarityIndicator rarity={(coin as any).rarity} variant="full" />
              </div>
            )}

            {/* Surface & Strike */}
            {(coin.grading.surface || coin.grading.strike) && (
              <div className="grid grid-cols-2 gap-4">
                {coin.grading.surface && (
                  <DataField label="Surface" value={coin.grading.surface} />
                )}
                {coin.grading.strike && (
                  <DataField label="Strike" value={coin.grading.strike} />
                )}
              </div>
            )}
          </div>
        </DataCard>

        {/* 3. References Card */}
        {(coin as any).references && (coin as any).references.length > 0 && (
          <DataCard categoryType={categoryType} title="References">
            <div className="space-y-2">
              {coin.references.map((ref: any, idx: number) => (
                <div
                  key={idx}
                  className="flex items-start justify-between py-2 border-b last:border-0"
                  style={{ borderColor: 'var(--border-subtle)' }}
                >
                  <div>
                    <div
                      className="text-sm font-mono font-semibold"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      {ref.catalog} {ref.number}
                    </div>
                    {ref.notes && (
                      <div
                        className="text-xs mt-1"
                        style={{ color: 'var(--text-muted)' }}
                      >
                        {ref.notes}
                      </div>
                    )}
                  </div>
                  {ref.is_primary && (
                    <span
                      className="text-xs px-2 py-0.5 rounded"
                      style={{
                        background: 'var(--bg-elevated)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      Primary
                    </span>
                  )}
                </div>
              ))}
            </div>
          </DataCard>
        )}

        {/* 4. Market Card */}
        {(currentValue || paidPrice) && (
          <DataCard categoryType={categoryType} title="Market & Valuation">
            <div className="space-y-4">
              {/* Current Value */}
              {currentValue && (
                <div>
                  <div
                    className="text-xs font-semibold uppercase tracking-wider mb-1"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Current Value
                  </div>
                  <div
                    className="text-3xl font-bold tabular-nums"
                    style={{ color: 'var(--text-primary)' }}
                  >
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: coin.acquisition?.currency || 'USD',
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    }).format(currentValue)}
                  </div>
                </div>
              )}

              {/* Acquisition */}
              {paidPrice && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div
                      className="text-xs font-semibold uppercase tracking-wider mb-1"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Paid
                    </div>
                    <div
                      className="text-lg font-semibold tabular-nums"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: coin.acquisition?.currency || 'USD',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0,
                      }).format(paidPrice)}
                    </div>
                  </div>

                  {performance !== null && (
                    <div>
                      <div
                        className="text-xs font-semibold uppercase tracking-wider mb-1"
                        style={{ color: 'var(--text-muted)' }}
                      >
                        Performance
                      </div>
                      <div
                        className="text-lg font-bold tabular-nums"
                        style={{
                          color: performance > 0
                            ? 'var(--perf-positive)'
                            : performance < 0
                              ? 'var(--perf-negative)'
                              : 'var(--perf-neutral)',
                        }}
                      >
                        {performance > 0 ? '▲' : performance < 0 ? '▼' : '●'}{' '}
                        {Math.abs(performance).toFixed(1)}%
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Acquisition details */}
              {coin.acquisition && (
                <div className="grid grid-cols-2 gap-4">
                  <DataField label="Source" value={coin.acquisition.source || '—'} />
                  <DataField label="Date" value={coin.acquisition.date || '—'} />
                </div>
              )}
            </div>
          </DataCard>
        )}

        {/* 5. Description Card */}
        {(coin.description || coin.obverse_description || coin.reverse_description) && (
          <DataCard categoryType={categoryType} title="Description">
            <div className="space-y-4">
              {/* General description */}
              {coin.description && (
                <div>
                  <p
                    className="text-sm leading-relaxed"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    {coin.description}
                  </p>
                </div>
              )}

              {/* Obverse & Reverse */}
              <div className="grid grid-cols-2 gap-6">
                {/* Obverse */}
                <div>
                  <div
                    className="text-xs font-semibold uppercase tracking-wider mb-2"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Obverse
                  </div>
                  {coin.obverse_description && (
                    <p
                      className="text-sm mb-2"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {coin.obverse_description}
                    </p>
                  )}
                  {coin.obverse_legend && (
                    <div
                      className="text-xs font-mono px-2 py-1 rounded"
                      style={{
                        background: 'var(--bg-elevated)',
                        color: 'var(--text-muted)',
                      }}
                    >
                      {coin.obverse_legend}
                    </div>
                  )}
                </div>

                {/* Reverse */}
                <div>
                  <div
                    className="text-xs font-semibold uppercase tracking-wider mb-2"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Reverse
                  </div>
                  {coin.reverse_description && (
                    <p
                      className="text-sm mb-2"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {coin.reverse_description}
                    </p>
                  )}
                  {coin.reverse_legend && (
                    <div
                      className="text-xs font-mono px-2 py-1 rounded"
                      style={{
                        background: 'var(--bg-elevated)',
                        color: 'var(--text-muted)',
                      }}
                    >
                      {coin.reverse_legend}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </DataCard>
        )}
      </div>
    </div>
  );
}

/**
 * DataCard - Card component with category bar
 */
interface DataCardProps {
  categoryType: string;
  title: string;
  children: React.ReactNode;
}

function DataCard({ categoryType, title, children }: DataCardProps) {
  return (
    <div
      className="relative rounded-lg p-6"
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Category bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[4px] rounded-l-lg"
        style={{
          background: `var(--cat-${categoryType})`,
        }}
      />

      {/* Title */}
      <h2
        className="text-lg font-semibold mb-4"
        style={{ color: 'var(--text-primary)' }}
      >
        {title}
      </h2>

      {/* Content */}
      {children}
    </div>
  );
}

/**
 * DataField - Key-value field component
 */
interface DataFieldProps {
  label: string;
  value: string | null | undefined;
}

function DataField({ label, value }: DataFieldProps) {
  return (
    <div>
      <div
        className="text-xs font-semibold uppercase tracking-wider mb-1"
        style={{ color: 'var(--text-muted)' }}
      >
        {label}
      </div>
      <div
        className="text-sm font-medium capitalize"
        style={{ color: value ? 'var(--text-primary)' : 'var(--text-ghost)' }}
      >
        {value || '—'}
      </div>
    </div>
  );
}
