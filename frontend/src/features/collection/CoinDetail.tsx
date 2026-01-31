/**
 * CoinDetailV3 - Scholarly numismatic coin detail view
 *
 * Layout (UX Overhaul):
 * - Identity header with side navigation arrows + provenance preview
 * - Side-by-side obverse/reverse panels
 * - Combined Specifications card (Physical + Condition)
 * - Horizontal References + Market Data cards
 * - Provenance timeline
 * - Historical context (collapsible)
 *
 * Design principle: Headers identify, cards detail.
 *
 * @module features/collection/CoinDetailV3
 */

import { Coin } from '@/domain/schemas';
import { parseCategory } from '@/components/design-system/colors';
import { ExternalLink } from 'lucide-react';
import {
  IdentityHeader,
  ObverseReversePanel,
  ReferencesCard,
  ProvenanceTimeline,
  HistoricalContextCard,
  DieStudyCard,
  IconographySection,
  DataCard,
  SpecificationsCard
} from './CoinDetail/index';
import { parseIconography, parseControlMarks } from '@/lib/parsers';
import { AddProvenanceDialog } from '@/components/coins/AddProvenanceDialog';
import { useState } from 'react';
import { useUpdateCoin } from '@/hooks/useCoins';
import { toast } from 'sonner';

interface CoinDetailV3Props {
  coin: Coin;
  onEdit?: () => void;
  onDelete?: () => void;
  onNavigatePrev?: () => void;
  onNavigateNext?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
  /** Opens add/attach images dialog */
  onOpenAddImages?: () => void;
  onEnrichLegend?: (side: 'obverse' | 'reverse') => void;
  isEnrichingObverse?: boolean;
  isEnrichingReverse?: boolean;
  onGenerateContext?: () => Promise<void>;
  isGeneratingContext?: boolean;
}

export function CoinDetail({
  coin,
  onEdit,
  onDelete,
  onNavigatePrev,
  onNavigateNext,
  hasPrev = false,
  hasNext = false,
  onOpenAddImages,
  onEnrichLegend,
  isEnrichingObverse = false,
  isEnrichingReverse = false,
  onGenerateContext,
  isGeneratingContext = false,
}: CoinDetailV3Props) {
  const categoryType = parseCategory(coin.category);

  // Calculate performance
  const marketValue = coin.market_value;
  const currentValue = marketValue || coin.acquisition?.price;
  const paidPrice = coin.acquisition?.price;
  const performance = currentValue && paidPrice && currentValue !== paidPrice
    ? ((currentValue - paidPrice) / paidPrice) * 100
    : null;

  const [isAddProvenanceOpen, setIsAddProvenanceOpen] = useState(false);
  const [provenanceToEdit, setProvenanceToEdit] = useState<any>(undefined);
  const updateCoin = useUpdateCoin();

  const handleEditProvenance = (entry: any) => {
    setProvenanceToEdit(entry);
    setIsAddProvenanceOpen(true);
  };

  const handleDeleteProvenance = async (entryToDelete: any) => {
    if (!coin.id) return;
    
    // Filter out the entry
    // If entry has ID, filter by ID. If not (optimistic or legacy), use index?
    // ProvenanceTimeline passes the entry object back.
    // If we rely on object reference equality, it might be tricky if data refreshed.
    // Best to filter by ID if present, otherwise match properties.
    
    const newProvenance = (coin.provenance || []).filter(p => {
      if (entryToDelete.id && p.id) {
        return p.id !== entryToDelete.id;
      }
      // Fallback: match all fields (unlikely collisions)
      return p !== entryToDelete && JSON.stringify(p) !== JSON.stringify(entryToDelete);
    });

    try {
      await updateCoin.mutateAsync({
        id: coin.id,
        data: {
          ...coin,
          provenance: newProvenance as any
        }
      });
      toast.success("Provenance record deleted");
    } catch (e) {
      console.error(e);
      toast.error("Failed to delete provenance");
    }
  };

  return (
    <div className="coin-detail flex flex-col gap-6 max-w-[1400px] mx-auto px-8">
      {/* Identity Header with Side Navigation */}
      <IdentityHeader
        coin={coin}
        onEdit={onEdit || (() => { })}
        onDelete={onDelete}
        onNavigatePrev={onNavigatePrev}
        onNavigateNext={onNavigateNext}
        hasPrev={hasPrev}
        hasNext={hasNext}
        onOpenAddImages={onOpenAddImages}
      />

      {/* Obverse/Reverse Panels - Side by side on desktop */}
      <ObverseReversePanel
        coin={coin}
        onOpenAddImages={onOpenAddImages}
        onEnrichLegend={onEnrichLegend}
        isEnrichingObverse={isEnrichingObverse}
        isEnrichingReverse={isEnrichingReverse}
      />

      {/* Combined Specifications Card (Physical + Condition) */}
      <SpecificationsCard
        coin={coin}
        categoryType={categoryType}
      />

      {/* Horizontal References + Market Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* References Card */}
        <ReferencesCard
          references={coin.references?.filter((r): r is NonNullable<typeof r> => r != null)}
          categoryType={categoryType}
        />

        {/* Market Data Card */}
        <DataCard categoryType={categoryType} title="Market Data">
          <div className="space-y-4">
            {/* Paid */}
            {paidPrice && (
              <div className="flex items-center justify-between">
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Paid</span>
                <span
                  className="text-lg font-bold tabular-nums"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: coin.acquisition?.currency || 'USD',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  }).format(paidPrice)}
                </span>
              </div>
            )}

            {/* Source */}
            {coin.acquisition?.source && (
              <div className="flex items-center justify-between">
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Source</span>
                <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                  {coin.acquisition.source}
                </span>
              </div>
            )}

            {/* Date */}
            {coin.acquisition?.date && (
              <div className="flex items-center justify-between">
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Acquired</span>
                <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                  {coin.acquisition.date}
                </span>
              </div>
            )}

            {/* View Purchase Link */}
            {coin.acquisition?.url && (
              <div className="pt-2">
                <a
                  href={coin.acquisition.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
                  style={{
                    background: 'var(--bg-subtle)',
                    color: 'var(--text-link)',
                    border: '1px solid var(--border-subtle)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'var(--bg-hover)';
                    e.currentTarget.style.color = 'var(--text-link-hover)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'var(--bg-subtle)';
                    e.currentTarget.style.color = 'var(--text-link)';
                  }}
                >
                  <ExternalLink size={14} />
                  View Purchase
                </a>
              </div>
            )}

            {/* Performance */}
            {performance !== null && (
              <div className="flex items-center justify-between pt-3 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Est. Performance</span>
                <span
                  className="text-sm font-bold tabular-nums"
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
                </span>
              </div>
            )}

            {/* Market Value if different from paid */}
            {marketValue && marketValue !== paidPrice && (
              <div className="flex items-center justify-between">
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Est. Value</span>
                <span
                  className="text-sm font-semibold tabular-nums"
                  style={{ color: 'var(--text-primary)' }}
                >
                  {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  }).format(marketValue)}
                </span>
              </div>
            )}

            {!paidPrice && !coin.acquisition?.source && (
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                No acquisition data recorded
              </p>
            )}
          </div>
        </DataCard>
      </div>

      {/* Provenance Timeline with Gap Handling */}
      <ProvenanceTimeline
        provenance={coin.provenance}
        categoryType={categoryType}
        onAddProvenance={() => {
          setProvenanceToEdit(undefined);
          setIsAddProvenanceOpen(true);
        }}
        onEditProvenance={handleEditProvenance}
        onDeleteProvenance={handleDeleteProvenance}
      />

      {/* Historical Context - AI Generated */}
      <HistoricalContextCard
        context={coin.historical_significance}
        analysisSections={coin.llm_analysis_sections}
        generatedAt={coin.llm_enriched_at}
        coinMetadata={{
          coinId: coin.id ?? 0, // Safe fallback instead of non-null assertion
          issuer: coin.attribution?.issuer || coin.issuing_authority,
          denomination: coin.denomination,
          yearStart: coin.attribution?.year_start || coin.mint_year_start,
          yearEnd: coin.attribution?.year_end || coin.mint_year_end,
          category: coin.category,
        }}
        onGenerateContext={onGenerateContext}
        isGenerating={isGeneratingContext}
        categoryType={categoryType}
      />

      {/* Die Study Section (collapsible) */}
      <DieStudyCard
        dieAxis={coin.dimensions?.die_axis}
        dieInfo={coin.die_info}
        monograms={coin.monograms}
        controlMarks={parseControlMarks(coin.control_marks)}
        categoryType={categoryType}
      />

      {/* Iconography Section */}
      <IconographySection
        obverseIconography={parseIconography(coin.obverse_iconography)}
        reverseIconography={parseIconography(coin.reverse_iconography)}
        categoryType={categoryType}
      />

      {/* Personal Notes */}
      {coin.personal_notes && (
        <DataCard categoryType={categoryType} title="Notes">
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            {coin.personal_notes}
          </p>
        </DataCard>
      )}

      {/* Dialogs */}
      <AddProvenanceDialog 
        coin={coin}
        open={isAddProvenanceOpen}
        onOpenChange={(open) => {
          setIsAddProvenanceOpen(open);
          if (!open) setProvenanceToEdit(undefined);
        }}
        entryToEdit={provenanceToEdit}
      />
    </div>
  );
}
