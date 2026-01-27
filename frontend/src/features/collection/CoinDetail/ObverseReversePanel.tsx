/**
 * ObverseReversePanel - Side-by-side obverse/reverse display
 * 
 * Layout:
 * - Side-by-side on desktop (>= 1024px)
 * - Stacked on mobile (< 1024px)
 * 
 * @module features/collection/CoinDetail/ObverseReversePanel
 */

import { memo } from 'react';
import { Coin, Image } from '@/domain/schemas';
import { CoinSidePanel } from './CoinSidePanel';
import { cn } from '@/lib/utils';
import { parseIconography } from '@/lib/parsers';
import { CoinGallery } from './CoinGallery';

interface ObverseReversePanelProps {
  coin: Coin;
  onEnrichLegend?: (side: 'obverse' | 'reverse') => void;
  isEnrichingObverse?: boolean;
  isEnrichingReverse?: boolean;
  className?: string;
}

export const ObverseReversePanel = memo(function ObverseReversePanel({
  coin,
  onEnrichLegend,
  isEnrichingObverse = false,
  isEnrichingReverse = false,
  className,
}: ObverseReversePanelProps) {
  // Get images by type with fallback logic
  const allImages = coin.images || [];

  // 1. Try to find explicit matches
  let obvImg = allImages.find(img => img.image_type?.toLowerCase() === 'obverse');
  let revImg = allImages.find(img => img.image_type?.toLowerCase() === 'reverse');

  // 2. Fallback: If no explicit obverse, use the first image (primary)
  if (!obvImg && allImages.length > 0) {
    obvImg = allImages[0];
  }

  // 3. Fallback: If no explicit reverse, use the second image (if it exists and is different/untagged)
  if (!revImg && allImages.length > 1) {
    // Avoid re-using the obverse image
    const candidate = allImages.find(img => img !== obvImg && (!img.image_type || img.image_type === 'general'));
    if (candidate) {
      revImg = candidate;
    } else if (allImages[1] !== obvImg) {
      // Just take the second one if we can't find a clean 'general' one
      revImg = allImages[1];
    }
  }

  const obverseImage = obvImg?.url || obvImg?.file_path;
  const reverseImage = revImg?.url || revImg?.file_path;

  // Get legend data - check both nested design object and flat fields
  const obverseLegend = coin.design?.obverse_legend || coin.obverse_legend;
  const reverseLegend = coin.design?.reverse_legend || coin.reverse_legend;
  const obverseDescription = coin.design?.obverse_description || coin.obverse_description;
  const reverseDescription = coin.design?.reverse_description || coin.reverse_description;
  const exergue = coin.design?.exergue;

  // Get expanded legends from backend (if available)
  const obverseLegendExpanded = coin.obverse_legend_expanded;
  const reverseLegendExpanded = coin.reverse_legend_expanded;

  // Get iconography (stored as JSON arrays)
  const obverseIconography = parseIconography(coin.obverse_iconography);
  const reverseIconography = parseIconography(coin.reverse_iconography);

  return (
    <div
      className={cn(
        'obv-rev-panels grid gap-6',
        // Side-by-side on desktop, stacked on mobile
        'grid-cols-1 lg:grid-cols-2',
        className
      )}
    >
      {/* Obverse Panel */}
      <CoinSidePanel
        side="obverse"
        image={obverseImage}
        legend={obverseLegend}
        legendExpanded={obverseLegendExpanded}
        description={obverseDescription}
        iconography={obverseIconography}
        metal={coin.metal}
        onEnrichLegend={onEnrichLegend ? () => onEnrichLegend('obverse') : undefined}
        isEnriching={isEnrichingObverse}
      />

      {/* Reverse Panel */}
      <CoinSidePanel
        side="reverse"
        image={reverseImage}
        legend={reverseLegend}
        legendExpanded={reverseLegendExpanded}
        description={reverseDescription}
        iconography={reverseIconography}
        exergue={exergue}
        onEnrichLegend={onEnrichLegend ? () => onEnrichLegend('reverse') : undefined}
        isEnriching={isEnrichingReverse}
      />

      {/* Gallery Trigger (if multiple images exist) - Spans full width */}
      {coin.images && coin.images.length > 0 && (
        <div className="flex justify-center mt-2 lg:col-span-2">
          <CoinGallery images={coin.images} />
        </div>
      )}
    </div>
  );
});
