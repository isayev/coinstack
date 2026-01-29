/**
 * CoinCard V3.0 - Modern Professional Design
 * Now with responsive layout for mobile, tablet, and desktop
 */

import React, { useMemo, memo } from 'react';
import { Coins, ImagePlus, ExternalLink } from 'lucide-react';
import { Coin } from '@/domain/schemas';
import { parseCategory } from '@/components/design-system/colors';
import { RarityIndicator } from '@/components/design-system/RarityIndicator';
import { formatYear, getAttributionTitle } from '@/lib/formatters';
import { getReferenceUrl } from '@/lib/referenceLinks';
import { useUIStore } from '@/stores/uiStore';
import { getGradeColor } from '@/utils/gradeUtils';

// ============================================================================
// CoinContent - Extracted component (memoized to prevent recreation)
// ============================================================================

interface CoinContentProps {
  coin: Coin;
  displayYear: string;
  reference: string | null;
  referenceUrl: string | null;
  currentValue: number | null | undefined;
  paidPrice: number | null | undefined;
  performance: number | null;
  isMobile: boolean;
  compact?: boolean;
  categoryType: string;
}

const CoinContent = memo(function CoinContent({
  coin,
  displayYear,
  reference,
  referenceUrl,
  currentValue,
  paidPrice,
  performance,
  isMobile,
  compact = false,
  categoryType,
}: CoinContentProps) {
  // Use design tokens where they align; fallback to px for breakpoint-specific tweaks
  const fontSize = {
    title: isMobile ? 'var(--font-size-base)' : compact ? 'var(--font-size-lg)' : 'var(--font-size-lg)',
    subtitle: isMobile ? 'var(--font-size-sm)' : compact ? 'var(--font-size-xs)' : 'var(--font-size-sm)',
    legend: isMobile ? '11px' : compact ? '10px' : '11px',
    price: isMobile ? '15px' : compact ? '14px' : '16px',
  };
  const { primary, secondary } = getAttributionTitle(coin);
  return (
    <>
      {/* Title: portrait subject when present, else issuer (numismatic convention) */}
      <h3
        style={{
          fontSize: fontSize.title,
          fontWeight: 700,
          lineHeight: 1.2,
          color: 'var(--text-primary)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
        title={primary}
      >
        {primary}
      </h3>
      {secondary && (
        <div
          style={{
            fontSize: fontSize.subtitle,
            lineHeight: 1.25,
            color: 'var(--text-muted)',
            fontWeight: 500,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={coin.attribution?.issuer || undefined}
        >
          {secondary}
        </div>
      )}

      {/* Denomination, Mint, Date - Design spec: 13px */}
      <div
        style={{
          fontSize: fontSize.subtitle,
          lineHeight: 1.3,
          color: 'var(--text-secondary)',
          fontWeight: 500,
        }}
      >
        <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{coin.denomination || 'Unknown'}</span>
        {' · '}
        {coin.attribution.mint || 'Uncertain'}
        {' · '}
        {displayYear}
      </div>

      {/* Legends Section - Compact */}
      <div
        style={{
          marginTop: '4px',
          paddingTop: '4px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
          flex: 1,
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        {/* Obverse Legend */}
        {coin.design?.obverse_legend && (
          <div
            style={{
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
              overflow: 'hidden',
            }}
            title={`Obverse: ${coin.design.obverse_legend}`}
          >
            <div
              style={{
                fontSize: '8px',
                fontWeight: 800,
                color: 'var(--text-ghost)',
                textTransform: 'uppercase',
                letterSpacing: '0.8px',
                flexShrink: 0,
                width: '24px',
                opacity: 0.6,
              }}
            >
              OBV
            </div>
            <span
              style={{
                fontSize: fontSize.legend,
                lineHeight: 1.4,
                color: 'var(--text-primary)',
                fontFamily: coin.category.includes('greek')
                  ? '"EB Garamond", Georgia, "Times New Roman", serif'
                  : '"Cinzel", "EB Garamond", Georgia, serif',
                fontWeight: 500,
                letterSpacing: coin.category.includes('greek') ? '0.3px' : '1px',
                fontStyle: coin.category.includes('greek') ? 'italic' : 'normal',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                opacity: 0.85,
              }}
            >
              {coin.design.obverse_legend}
            </span>
          </div>
        )}

        {/* Reverse Legend */}
        {coin.design?.reverse_legend && (
          <div
            style={{
              display: 'flex',
              gap: '8px',
              alignItems: 'center',
              overflow: 'hidden',
            }}
            title={`Reverse: ${coin.design.reverse_legend}`}
          >
            <div
              style={{
                fontSize: '8px',
                fontWeight: 800,
                color: 'var(--text-ghost)',
                textTransform: 'uppercase',
                letterSpacing: '0.8px',
                flexShrink: 0,
                width: '24px',
                opacity: 0.6,
              }}
            >
              REV
            </div>
            <span
              style={{
                fontSize: fontSize.legend,
                lineHeight: 1.4,
                color: 'var(--text-primary)',
                fontFamily: coin.category.includes('greek')
                  ? '"EB Garamond", Georgia, "Times New Roman", serif'
                  : '"Cinzel", "EB Garamond", Georgia, serif',
                fontWeight: 500,
                letterSpacing: coin.category.includes('greek') ? '0.3px' : '1px',
                fontStyle: coin.category.includes('greek') ? 'italic' : 'normal',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                opacity: 0.85,
              }}
            >
              {coin.design.reverse_legend}
            </span>
          </div>
        )}

        {/* Catalog Reference - Always shown if available; link when URL known */}
        {reference && (
          <div
            style={{
              fontSize: '9px',
              fontFamily: 'monospace',
              color: 'var(--text-muted)',
              fontWeight: 600,
              letterSpacing: '0.5px',
            }}
          >
            {referenceUrl ? (
              <a
                href={referenceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-0.5 hover:underline"
              >
                {reference}
                <ExternalLink className="w-2.5 h-2.5 shrink-0" />
              </a>
            ) : (
              reference
            )}
          </div>
        )}
      </div>

      {/* Bottom Section: Price Left, Badges Right */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '8px',
        paddingTop: '6px',
        borderTop: '1px solid var(--border-subtle)',
        marginTop: 'auto',
      }}>
        {/* Left: Current Value */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
          {currentValue && (
            <div
              style={{
                fontSize: fontSize.price,
                fontWeight: 700,
                color: 'var(--text-primary)',
              }}
            >
              {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: coin.acquisition?.currency || 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              }).format(currentValue)}
            </div>
          )}

          {/* Performance */}
          {paidPrice && performance !== null && (
            <div
              style={{
                fontSize: '10px',
                fontWeight: 600,
                color: performance > 0
                  ? 'var(--perf-positive)'
                  : performance < 0
                    ? 'var(--perf-negative)'
                    : 'var(--text-muted)',
              }}
            >
              {performance > 0 ? '↑' : performance < 0 ? '↓' : ''}{Math.abs(performance).toFixed(0)}%
            </div>
          )}
        </div>

        {/* Right: Unified Badge Row - Cert, Grade, Metal, Rarity, Category */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          flexShrink: 0,
        }}>
          {/* Certification Service Badge */}
          {coin.grading.service && coin.grading.service !== 'none' && (
            <div
              style={{
                fontSize: '9px',
                fontWeight: 600,
                padding: '2px 6px',
                borderRadius: '3px',
                height: '18px',
                display: 'flex',
                alignItems: 'center',
                color: '#fff',
                background: `var(--cert-${coin.grading.service.toLowerCase()})`,
                textTransform: 'uppercase',
                letterSpacing: '0.3px',
              }}
            >
              {coin.grading.service}
            </div>
          )}

          {/* Grade Badge */}
          {coin.grading.grade && (
            <div
              style={{
                fontSize: '9px',
                fontWeight: 600,
                padding: '2px 6px',
                borderRadius: '3px',
                height: '18px',
                display: 'flex',
                alignItems: 'center',
                border: `1px solid ${getGradeColor(coin.grading.grade)}`,
                color: getGradeColor(coin.grading.grade),
                letterSpacing: '0.3px',
              }}
            >
              {coin.grading.grade}
            </div>
          )}

          {/* Metal Badge */}
          {coin.metal && (
            <div
              style={{
                fontSize: '9px',
                fontWeight: 600,
                padding: '2px 6px',
                borderRadius: '3px',
                height: '18px',
                display: 'flex',
                alignItems: 'center',
                color: `var(--metal-${coin.metal.toLowerCase()})`,
                background: `var(--metal-${coin.metal.toLowerCase()}-subtle)`,
                textTransform: 'uppercase',
                letterSpacing: '0.3px',
              }}
            >
              {coin.metal}
            </div>
          )}

          {/* Rarity Dot */}
          {coin.rarity && (
            <RarityIndicator rarity={coin.rarity} variant="dot" />
          )}

          {/* Category Badge - Rightmost */}
          <div
            style={{
              fontSize: '9px',
              fontWeight: 600,
              padding: '2px 6px',
              borderRadius: '3px',
              height: '18px',
              display: 'flex',
              alignItems: 'center',
              color: `var(--cat-${categoryType})`,
              background: 'rgba(0, 0, 0, 0.4)',
              textTransform: 'uppercase',
              letterSpacing: '0.3px',
            }}
          >
            {coin.category.replace('_', ' ').replace('roman ', '')}
          </div>
        </div>
      </div>
    </>
  );
});

// ============================================================================
// Main Component
// ============================================================================

export interface CoinCardProps {
  coin: Coin;
  onClick?: (coin: Coin) => void;
  /** Whether the card is selected */
  selected?: boolean;
  /** Callback when selection state changes */
  onSelect?: (id: number, selected: boolean) => void;
  /** Grid index for keyboard navigation */
  gridIndex?: number;
  /** Callback to open add-images dialog when obv/rev missing */
  onAddImages?: (coin: Coin) => void;
}

export const CoinCard = memo(function CoinCard({ coin, onClick, selected, onSelect, gridIndex, onAddImages }: CoinCardProps) {
  const categoryType = parseCategory(coin.category);
  const [isFlipped, setIsFlipped] = React.useState(false);
  const screenSize = useUIStore((s) => s.screenSize);
  const isMobile = screenSize === 'mobile';

  // Handle selection checkbox click
  const handleSelectClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (coin.id !== null) {
      onSelect?.(coin.id, !selected);
    }
  };

  // Memoize images (case-insensitive comparison for image_type)
  const images = useMemo(() => ({
    obverse: coin.images?.find(img => img.image_type?.toLowerCase() === 'obverse')?.url || coin.images?.[0]?.url,
    reverse: coin.images?.find(img => img.image_type?.toLowerCase() === 'reverse')?.url || coin.images?.[1]?.url,
  }), [coin.images]);

  const showAddImages = (!images.obverse || !images.reverse) && !!onAddImages;

  // Memoize year display
  const displayYear = useMemo((): string => {
    const { year_start, year_end } = coin.attribution;
    if (year_start === null || year_start === undefined) return 'Unknown';
    if (year_end === null || year_end === undefined || year_start === year_end) {
      return formatYear(year_start);
    }
    return `${formatYear(year_start)}–${formatYear(year_end)}`;
  }, [coin.attribution.year_start, coin.attribution.year_end]);

  // Memoize financials
  const financials = useMemo(() => {
    const marketValue = coin.market_value;
    const currentValue = marketValue || coin.acquisition?.price;
    const paidPrice = coin.acquisition?.price;
    const performance = currentValue && paidPrice && currentValue !== paidPrice
      ? ((currentValue - paidPrice) / paidPrice) * 100
      : null;
    return { currentValue, paidPrice, performance };
  }, [coin.market_value, coin.acquisition?.price]);

  const { currentValue, paidPrice, performance } = financials;

  // Memoize reference and optional direct type URL
  const { reference, referenceUrl } = useMemo(() => {
    const ref0 = coin.references?.[0];
    if (!ref0) return { reference: null, referenceUrl: null };
    const reference = `${ref0.catalog || 'Ref'} ${ref0.number || ''}`;
    const referenceUrl = getReferenceUrl(ref0);
    return { reference, referenceUrl };
  }, [coin.references]);

  // Create a render helper that uses the extracted CoinContent component
  const renderCoinContent = (compact = false) => (
    <CoinContent
      coin={coin}
      displayYear={displayYear}
      reference={reference}
      referenceUrl={referenceUrl}
      currentValue={currentValue}
      paidPrice={paidPrice}
      performance={performance}
      isMobile={isMobile}
      compact={compact}
      categoryType={categoryType}
    />
  );

  // Responsive dimensions - cards fill their grid cell with min-width
  // Balanced sizing: 160px square images, 170px card height
  const cardWidth = '100%';
  const cardMinWidth = isMobile ? 'auto' : '360px'; // Slightly smaller min-width
  const cardHeight = isMobile ? 'auto' : '170px';
  const imageWidth = isMobile ? '100%' : '160px'; // Square image
  const imageHeight = isMobile ? '180px' : '160px';

  return (
    <div
      onClick={() => onClick?.(coin)}
      data-grid-index={gridIndex}
      tabIndex={0}
      role="button"
      aria-pressed={selected}
      aria-label={`${coin.attribution.issuer || 'Unknown'} ${coin.denomination || ''}`}
      style={{
        position: 'relative',
        width: cardWidth,
        minWidth: cardMinWidth,
        height: cardHeight,
        minHeight: isMobile ? '380px' : cardHeight,
        background: 'var(--bg-card)',
        borderRadius: '8px',
        overflow: 'hidden',
        cursor: 'pointer',
        transition: 'transform 0.2s, box-shadow 0.2s',
        boxShadow: selected
          ? '0 0 0 2px var(--metal-au), 0 4px 12px rgba(0, 0, 0, 0.4)'
          : '0 2px 8px rgba(0, 0, 0, 0.3)',
        outline: 'none',
      }}
      onMouseEnter={(e) => {
        if (!isMobile) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = selected
            ? '0 0 0 2px var(--metal-au), 0 8px 16px rgba(0, 0, 0, 0.4)'
            : '0 8px 16px rgba(0, 0, 0, 0.4)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isMobile) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = selected
            ? '0 0 0 2px var(--metal-au), 0 4px 12px rgba(0, 0, 0, 0.4)'
            : '0 2px 8px rgba(0, 0, 0, 0.3)';
        }
      }}
      onKeyDown={(e) => {
        if (e.key === 'x' || e.key === 'X') {
          e.preventDefault();
          if (coin.id !== null) {
            onSelect?.(coin.id, !selected);
          }
        }
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.(coin);
        }
      }}
    >
      {/* Selection checkbox */}
      {onSelect && (
        <div
          onClick={handleSelectClick}
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            zIndex: 10,
            width: '20px',
            height: '20px',
            borderRadius: '4px',
            background: selected ? 'var(--metal-au)' : 'rgba(0, 0, 0, 0.5)',
            border: selected ? 'none' : '2px solid var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            opacity: selected ? 1 : 0.7,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.opacity = '1';
            if (!selected) {
              e.currentTarget.style.borderColor = 'var(--metal-au)';
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.opacity = selected ? '1' : '0.7';
            if (!selected) {
              e.currentTarget.style.borderColor = 'var(--text-muted)';
            }
          }}
        >
          {selected && (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path
                d="M2 6L5 9L10 3"
                stroke="#000"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </div>
      )}
      {/* Category Bar - 4px left accent */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '4px',
          background: `var(--cat-${categoryType})`,
          borderRadius: '8px 0 0 8px',
          zIndex: 1,
        }}
      />

      {/* RESPONSIVE LAYOUT - Mobile: Vertical Stack, Desktop: Horizontal Table */}
      {isMobile ? (
        // Mobile: Vertical Stack Layout
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Image Section */}
          {/* 3D Flip Container - Mobile */}
          <div
            style={{
              position: 'relative',
              width: '100%',
              height: imageHeight,
              perspective: '1000px',
              overflow: 'hidden',
              background: 'var(--bg-elevated)',
            }}
            onTouchStart={() => images.reverse && setIsFlipped(true)}
            onTouchEnd={() => setIsFlipped(false)}
            onClick={(e) => {
              // Toggle flip on tap for mobile
              if (images.reverse) {
                e.stopPropagation();
                setIsFlipped(!isFlipped);
              }
            }}
          >
            {showAddImages && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onAddImages?.(coin);
                }}
                aria-label="Add images"
                style={{
                  position: 'absolute',
                  inset: 0,
                  zIndex: 10,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  background: 'rgba(0,0,0,0.5)',
                  color: 'var(--text-primary)',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                }}
              >
                <ImagePlus style={{ width: '20px', height: '20px' }} />
                Add images
              </button>
            )}
            {images.obverse || images.reverse ? (
              <div
                style={{
                  position: 'relative',
                  width: '100%',
                  height: '100%',
                  transformStyle: 'preserve-3d',
                  transition: 'transform 0.6s ease-in-out',
                  transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                }}
              >
                {/* Obverse (Front) */}
                <div
                  style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    backfaceVisibility: 'hidden',
                    WebkitBackfaceVisibility: 'hidden',
                  }}
                >
                  {images.obverse ? (
                    <img
                      src={images.obverse}
                      alt={`${coin.attribution.issuer || 'Coin'} obverse`}
                      loading="lazy"
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                      }}
                      aria-label="No obverse image"
                      role="img"
                    >
                      <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
                      <span className="text-[10px] text-muted-foreground">No image</span>
                    </div>
                  )}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '8px',
                      right: '8px',
                      background: 'rgba(0, 0, 0, 0.7)',
                      color: 'var(--text-muted)',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: 700,
                      letterSpacing: '0.5px',
                    }}
                  >
                    OBV
                  </div>
                </div>

                {/* Reverse (Back) */}
                <div
                  style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    backfaceVisibility: 'hidden',
                    WebkitBackfaceVisibility: 'hidden',
                    transform: 'rotateY(180deg)',
                  }}
                >
                  {images.reverse ? (
                    <img
                      src={images.reverse}
                      alt={`${coin.attribution.issuer || 'Coin'} reverse`}
                      loading="lazy"
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                    />
                  ) : images.obverse ? (
                    <img
                      src={images.obverse}
                      alt={`${coin.attribution.issuer || 'Coin'}`}
                      loading="lazy"
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        filter: 'grayscale(20%)',
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                      }}
                      aria-label="No reverse image"
                      role="img"
                    >
                      <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
                      <span className="text-[10px] text-muted-foreground">No image</span>
                    </div>
                  )}
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '8px',
                      right: '8px',
                      background: 'rgba(0, 0, 0, 0.7)',
                      color: 'var(--text-muted)',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: 700,
                      letterSpacing: '0.5px',
                    }}
                  >
                    REV
                  </div>
                </div>
              </div>
            ) : (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                }}
                aria-label="No image"
                role="img"
              >
                <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
                <span className="text-[10px] text-muted-foreground">No image</span>
              </div>
            )}
          </div>

          {/* Content Section - Mobile */}
          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
            {renderCoinContent()}
          </div>
        </div>
      ) : (
        // Desktop/Tablet: Horizontal Table Layout
        <table
          style={{
            width: '100%',
            height: '100%',
            tableLayout: 'fixed',
            borderCollapse: 'collapse',
          }}
        >
          <tbody>
            <tr>
              {/* Image Column - FULL HEIGHT with Flip Effect */}
              <td
                style={{
                  width: imageWidth,
                  padding: 0,
                  verticalAlign: 'middle',
                }}
              >
                {/* 3D Flip Container */}
                <div
                  style={{
                    position: 'relative',
                    width: imageWidth,
                    height: imageHeight,
                    perspective: '1000px',
                    overflow: 'hidden',
                    background: 'var(--bg-elevated)',
                  }}
                  onMouseEnter={() => images.reverse && setIsFlipped(true)}
                  onMouseLeave={() => setIsFlipped(false)}
                >
                  {showAddImages && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onAddImages?.(coin);
                      }}
                      aria-label="Add images"
                      style={{
                        position: 'absolute',
                        inset: 0,
                        zIndex: 10,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        background: 'rgba(0,0,0,0.5)',
                        color: 'var(--text-primary)',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: 600,
                      }}
                    >
                      <ImagePlus style={{ width: '20px', height: '20px' }} />
                      Add images
                    </button>
                  )}
                  {images.obverse || images.reverse ? (
                    <div
                      style={{
                        position: 'relative',
                        width: '100%',
                        height: '100%',
                        transformStyle: 'preserve-3d',
                        transition: 'transform 0.6s ease-in-out',
                        transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                      }}
                    >
                      {/* Obverse (Front) */}
                      <div
                        style={{
                          position: 'absolute',
                          width: '100%',
                          height: '100%',
                          backfaceVisibility: 'hidden',
                          WebkitBackfaceVisibility: 'hidden',
                        }}
                      >
                        {images.obverse ? (
                          <img
                            src={images.obverse}
                            alt={`${coin.attribution.issuer || 'Coin'} obverse`}
                            loading="lazy"
                            style={{
                              width: '100%',
                              height: '100%',
                              objectFit: 'cover',
                            }}
                          />
                        ) : (
                          <div
                            style={{
                              width: '100%',
                              height: '100%',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '4px',
                            }}
                            aria-label="No obverse image"
                            role="img"
                          >
                            <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
                            <span className="text-[10px] text-muted-foreground">No image</span>
                          </div>
                        )}
                        <div
                          style={{
                            position: 'absolute',
                            bottom: '8px',
                            right: '8px',
                            background: 'rgba(0, 0, 0, 0.7)',
                            color: 'var(--text-muted)',
                            padding: '3px 6px',
                            borderRadius: '4px',
                            fontSize: '9px',
                            fontWeight: 700,
                            letterSpacing: '0.5px',
                          }}
                        >
                          OBV
                        </div>
                      </div>

                      {/* Reverse (Back) */}
                      <div
                        style={{
                          position: 'absolute',
                          width: '100%',
                          height: '100%',
                          backfaceVisibility: 'hidden',
                          WebkitBackfaceVisibility: 'hidden',
                          transform: 'rotateY(180deg)',
                        }}
                      >
                        {images.reverse ? (
                          <img
                            src={images.reverse}
                            alt={`${coin.attribution.issuer || 'Coin'} reverse`}
                            loading="lazy"
                            style={{
                              width: '100%',
                              height: '100%',
                              objectFit: 'cover',
                            }}
                          />
                        ) : images.obverse ? (
                          <img
                            src={images.obverse}
                            alt={`${coin.attribution.issuer || 'Coin'}`}
                            loading="lazy"
                            style={{
                              width: '100%',
                              height: '100%',
                              objectFit: 'cover',
                              filter: 'grayscale(20%)',
                            }}
                          />
                        ) : (
                          <div
                            style={{
                              width: '100%',
                              height: '100%',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '4px',
                            }}
                            aria-label="No reverse image"
                            role="img"
                          >
                            <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
                            <span className="text-[10px] text-muted-foreground">No image</span>
                          </div>
                        )}
                        <div
                          style={{
                            position: 'absolute',
                            bottom: '8px',
                            right: '8px',
                            background: 'rgba(0, 0, 0, 0.7)',
                            color: 'var(--text-muted)',
                            padding: '3px 6px',
                            borderRadius: '4px',
                            fontSize: '9px',
                            fontWeight: 700,
                            letterSpacing: '0.5px',
                          }}
                        >
                          REV
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div
                      style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                      }}
                      aria-label="No image"
                      role="img"
                    >
                      <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
                      <span className="text-[10px] text-muted-foreground">No image</span>
                    </div>
                  )}
                </div>
              </td>

              {/* Content Column - Clean Design */}
              <td
                style={{
                  padding: screenSize === 'tablet' ? '10px 10px 10px 14px' : '12px 14px 12px 16px',
                  verticalAlign: 'top',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                    gap: screenSize === 'tablet' ? '4px' : '6px',
                  }}
                >
                  {renderCoinContent(screenSize === 'tablet')}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      )}

    </div>
  );
});

export function CoinCardV3Skeleton() {
  const screenSize = useUIStore((s) => s.screenSize);
  const isMobile = screenSize === 'mobile';
  const cardWidth = isMobile ? '100%' : screenSize === 'tablet' ? '360px' : '440px';
  const cardHeight = isMobile ? 'auto' : '200px';

  return (
    <div style={{
      position: 'relative',
      width: cardWidth,
      height: cardHeight,
      minHeight: isMobile ? '380px' : cardHeight,
      background: 'var(--bg-card)',
      borderRadius: '8px',
      overflow: 'hidden',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
    }}>
      <div style={{
        position: 'absolute',
        left: 0,
        top: 0,
        bottom: 0,
        width: '4px',
        background: 'var(--border-subtle)',
      }} />

      <table style={{
        width: '100%',
        height: '100%',
        tableLayout: 'fixed',
        borderCollapse: 'collapse',
      }}>
        <tbody>
          <tr>
            <td style={{
              width: '200px',
              padding: 0,
            }}>
              <div style={{
                width: '200px',
                height: '200px',
                background: 'var(--bg-elevated)',
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
              }} />
            </td>
            <td style={{
              padding: '16px 16px 16px 20px',
              verticalAlign: 'top',
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', height: '100%' }}>
                <div style={{
                  height: '20px',
                  background: 'var(--bg-elevated)',
                  borderRadius: '4px',
                  width: '85%',
                  animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                }} />
                <div style={{
                  height: '14px',
                  background: 'var(--bg-elevated)',
                  borderRadius: '4px',
                  width: '65%',
                  animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                }} />
                <div style={{
                  height: '12px',
                  background: 'var(--bg-elevated)',
                  borderRadius: '4px',
                  width: '75%',
                  animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                }} />
                <div style={{ flex: 1 }} />
                <div style={{
                  height: '22px',
                  background: 'var(--bg-elevated)',
                  borderRadius: '4px',
                  width: '100%',
                  animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                }} />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
