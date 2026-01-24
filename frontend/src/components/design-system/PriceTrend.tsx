/**
 * PriceTrend - Price change indicator with trend arrow
 * 
 * Shows current price with change percentage and direction arrow.
 * Green for up, red for down.
 * 
 * @module design-system/PriceTrend
 */

import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface PriceTrendProps {
  /** Current/latest price */
  currentPrice?: number | string | null;
  /** Previous price for comparison */
  previousPrice?: number | string | null;
  /** Pre-calculated change percentage */
  changePercent?: number | null;
  /** Show previous price */
  showPrevious?: boolean;
  /** Size variant */
  size?: 'xs' | 'sm' | 'md';
  /** Additional className */
  className?: string;
}

const SIZE_CONFIG = {
  xs: { text: 'text-[10px]', icon: 'w-2.5 h-2.5' },
  sm: { text: 'text-xs', icon: 'w-3 h-3' },
  md: { text: 'text-sm', icon: 'w-3.5 h-3.5' },
};

export function PriceTrend({ 
  currentPrice, 
  previousPrice,
  changePercent,
  showPrevious = false,
  size = 'sm',
  className 
}: PriceTrendProps) {
  const current = typeof currentPrice === 'string' ? parseFloat(currentPrice) : currentPrice;
  const previous = typeof previousPrice === 'string' ? parseFloat(previousPrice) : previousPrice;
  
  if (!current) return null;
  
  // Calculate change if not provided
  let change = changePercent;
  if (change === undefined && previous && previous > 0) {
    change = ((current - previous) / previous) * 100;
  }
  
  const isUp = change !== undefined && change !== null && change > 0;
  const isFlat = change === 0 || change === undefined || change === null;
  
  const sizeConfig = SIZE_CONFIG[size];
  
  return (
    <div className={cn('inline-flex items-center gap-1', className)}>
      {/* Previous price with arrow */}
      {showPrevious && previous && (
        <>
          <span 
            className={cn(sizeConfig.text, 'tabular-nums opacity-50 line-through')}
            style={{ color: 'var(--text-tertiary)' }}
          >
            ${previous.toLocaleString()}
          </span>
          <span style={{ color: 'var(--text-tertiary)' }}>→</span>
        </>
      )}
      
      {/* Current price */}
      <span 
        className={cn(sizeConfig.text, 'tabular-nums font-semibold')}
        style={{ color: 'var(--text-primary)' }}
      >
        ${current.toLocaleString()}
      </span>
      
      {/* Trend indicator */}
      {!isFlat && (
        <span 
          className={cn('inline-flex items-center gap-0.5', sizeConfig.text)}
          style={{ color: isUp ? 'var(--price-up)' : 'var(--price-down)' }}
        >
          {isUp ? (
            <TrendingUp className={sizeConfig.icon} />
          ) : (
            <TrendingDown className={sizeConfig.icon} />
          )}
          <span className="tabular-nums">
            {isUp ? '+' : ''}{change?.toFixed(0)}%
          </span>
        </span>
      )}
      
      {/* Flat indicator */}
      {isFlat && changePercent === 0 && (
        <span 
          className={cn('inline-flex items-center', sizeConfig.text)}
          style={{ color: 'var(--text-tertiary)' }}
        >
          <Minus className={sizeConfig.icon} />
        </span>
      )}
    </div>
  );
}

/**
 * SimplePriceTrend - Compact version for tight spaces
 */
export function SimplePriceTrend({ 
  changePercent,
  className 
}: { 
  changePercent?: number | null;
  className?: string;
}) {
  if (changePercent === undefined || changePercent === null) return null;
  
  const isUp = changePercent > 0;
  const isDown = changePercent < 0;
  
  return (
    <span 
      className={cn('text-[10px] font-semibold tabular-nums', className)}
      style={{ 
        color: isUp ? 'var(--price-up)' : isDown ? 'var(--price-down)' : 'var(--text-tertiary)' 
      }}
    >
      {isUp ? '▲' : isDown ? '▼' : '—'}
      {isUp ? '+' : ''}{changePercent.toFixed(0)}%
    </span>
  );
}
