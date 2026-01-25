/**
 * CoinCard V3.0 - Modern Professional Design
 * Now with responsive layout for mobile, tablet, and desktop
 */

import React, { useMemo, memo } from 'react';
import { Coins } from 'lucide-react';
import { Coin } from '@/domain/schemas';
import { parseCategory } from '@/components/design-system/colors';
import { RarityIndicator } from '@/components/design-system/RarityIndicator';
import { formatYear } from '@/lib/formatters';
import { useUIStore } from '@/stores/uiStore';

// ============================================================================
// Constants (moved outside component to prevent recreation)
// ============================================================================

const GRADE_COLORS: Record<string, string> = {
  'MS': 'var(--grade-ms)',
  'AU': 'var(--grade-au)',
  'XF': 'var(--grade-xf)',
  'EF': 'var(--grade-xf)',
  'VF': 'var(--grade-vf)',
  'F': 'var(--grade-f)',
  'VG': 'var(--grade-vg)',
  'G': 'var(--grade-g)',
  'AG': 'var(--grade-ag)',
  'FR': 'var(--grade-fr)',
  'P': 'var(--grade-fr)',
  'CHOICE': 'var(--grade-au)',
};

function getGradeColor(grade: string | null | undefined): string {
  if (!grade) return 'var(--text-secondary)';
  const prefix = grade.toString().replace(/[0-9\s]/g, '').toUpperCase();
  return GRADE_COLORS[prefix] || 'var(--text-secondary)';
}

// ============================================================================
// CoinContent - Extracted component (memoized to prevent recreation)
// ============================================================================

interface CoinContentProps {
  coin: Coin;
  displayYear: string;
  reference: string | null;
  currentValue: number | null | undefined;
  paidPrice: number | null | undefined;
  performance: number | null;
  isMobile: boolean;
  compact?: boolean;
}

const CoinContent = memo(function CoinContent({
  coin,
  displayYear,
  reference,
  currentValue,
  paidPrice,
  performance,
  isMobile,
  compact = false,
}: CoinContentProps) {
  return (
    <>
      {/* Ruler Name - Design spec: 17px */}
      <h3
        style={{
          fontSize: compact ? '15px' : '17px',
          fontWeight: 700,
          lineHeight: 1.2,
          color: 'var(--text-primary)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
        title={coin.attribution.issuer || undefined}
      >
        {coin.attribution.issuer || 'Unknown Ruler'}
      </h3>

      {/* Denomination, Mint, Date - Design spec: 13px */}
      <div
        style={{
          fontSize: compact ? '12px' : '13px',
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
                fontSize: compact ? '10px' : '11px',
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
                fontSize: compact ? '10px' : '11px',
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

        {/* Catalog Reference - Always shown if available */}
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
            {reference}
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
                fontSize: compact ? '14px' : '16px',
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

        {/* Right: Compact Badges - Certification, Grade, Metal */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '3px',
          flexShrink: 0,
        }}>
          {/* Certification Service Badge */}
          {coin.grading.service && coin.grading.service !== 'none' && (
            <div
              style={{
                fontSize: '8px',
                fontWeight: 700,
                padding: '2px 5px',
                borderRadius: '2px',
                color: '#fff',
                background: `var(--cert-${coin.grading.service.toLowerCase()})`,
                textTransform: 'uppercase',
              }}
            >
              {coin.grading.service}
            </div>
          )}

          {/* Grade Badge */}
          {coin.grading.grade && (
            <div
              style={{
                fontSize: '8px',
                fontWeight: 700,
                padding: '2px 5px',
                borderRadius: '2px',
                border: `1px solid ${getGradeColor(coin.grading.grade)}`,
                color: getGradeColor(coin.grading.grade),
              }}
            >
              {coin.grading.grade}
            </div>
          )}

          {/* Metal Badge */}
          {coin.metal && (
            <div
              style={{
                fontSize: '8px',
                fontWeight: 700,
                padding: '2px 5px',
                borderRadius: '2px',
                color: `var(--metal-${coin.metal.toLowerCase()})`,
                background: `var(--metal-${coin.metal.toLowerCase()}-subtle)`,
                textTransform: 'uppercase',
              }}
            >
              {coin.metal}
            </div>
          )}

          {/* Rarity Dot */}
          {coin.rarity && (
            <RarityIndicator rarity={coin.rarity} variant="dot" />
          )}
        </div>
      </div>
    </>
  );
});

// ============================================================================
// Main Component
// ============================================================================

export interface CoinCardV3Props {
  coin: Coin;
  onClick?: (coin: Coin) => void;
}

export function CoinCardV3({ coin, onClick }: CoinCardV3Props) {
  const categoryType = parseCategory(coin.category);
  const [isFlipped, setIsFlipped] = React.useState(false);
  const screenSize = useUIStore((s) => s.screenSize);
  const isMobile = screenSize === 'mobile';

  // Memoize images
  const images = useMemo(() => ({
    obverse: coin.images?.find(img => img.image_type === 'obverse')?.url || coin.images?.[0]?.url,
    reverse: coin.images?.find(img => img.image_type === 'reverse')?.url || coin.images?.[1]?.url,
  }), [coin.images]);

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

  // Memoize reference
  const reference = useMemo(() => {
    const references = coin.references;
    return references?.[0]
      ? `${references[0].catalog || 'Ref'} ${references[0].number || ''}`
      : null;
  }, [coin.references]);

  // Create a render helper that uses the extracted CoinContent component
  const renderCoinContent = (compact = false) => (
    <CoinContent
      coin={coin}
      displayYear={displayYear}
      reference={reference}
      currentValue={currentValue}
      paidPrice={paidPrice}
      performance={performance}
      isMobile={isMobile}
      compact={compact}
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
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
      }}
      onMouseEnter={(e) => {
        if (!isMobile) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.4)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isMobile) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.3)';
        }
      }}
    >
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
                    <div style={{ 
                      width: '100%', 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center' 
                    }}>
                      <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
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
                    <div style={{ 
                      width: '100%', 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center' 
                    }}>
                      <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
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
              <div style={{ 
                width: '100%', 
                height: '100%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center' 
              }}>
                <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
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
                  width: imageWidth,
                  height: imageHeight,
                  perspective: '1000px',
                  overflow: 'hidden',
                  background: 'var(--bg-elevated)',
                }}
                onMouseEnter={() => images.reverse && setIsFlipped(true)}
                onMouseLeave={() => setIsFlipped(false)}
              >
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
                        <div style={{ 
                          width: '100%', 
                          height: '100%', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center' 
                        }}>
                          <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
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
                        <div style={{ 
                          width: '100%', 
                          height: '100%', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center' 
                        }}>
                          <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
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
                  <div style={{ 
                    width: '100%', 
                    height: '100%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center' 
                  }}>
                    <Coins style={{ width: '64px', height: '64px', color: 'var(--text-ghost)' }} />
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

      {/* Category Label - Subtle Badge */}
      <div
        style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          padding: '2px 6px',
          borderRadius: '3px',
          fontSize: '8px',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.3px',
          background: 'rgba(0, 0, 0, 0.5)',
          color: `var(--cat-${categoryType})`,
          backdropFilter: 'blur(4px)',
        }}
      >
        {coin.category.replace('_', ' ').replace('roman ', '')}
      </div>
    </div>
  );
}

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
