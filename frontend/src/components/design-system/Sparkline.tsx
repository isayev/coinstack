/**
 * Sparkline - Mini trend chart using Unicode blocks
 * 
 * Creates a simple bar chart using Unicode block characters.
 * Useful for showing trends in tight spaces like sidebars and cards.
 * 
 * @module design-system/Sparkline
 */

import { cn } from '@/lib/utils';
import { useMemo } from 'react';

export interface SparklineProps {
  /** Data points (numbers) */
  data: number[];
  /** Width in characters */
  width?: number;
  /** Height variant */
  height?: 'xs' | 'sm' | 'md';
  /** Show as positive (green) or calculate from trend */
  trend?: 'up' | 'down' | 'neutral' | 'auto';
  /** Additional className */
  className?: string;
}

// Unicode block characters for different heights
const BLOCKS = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];

const HEIGHT_CONFIG = {
  xs: { fontSize: 'text-[8px]', lineHeight: 'leading-none' },
  sm: { fontSize: 'text-xs', lineHeight: 'leading-none' },
  md: { fontSize: 'text-sm', lineHeight: 'leading-tight' },
};

export function Sparkline({ 
  data, 
  width,
  height = 'sm',
  trend = 'auto',
  className 
}: SparklineProps) {
  const normalized = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    
    // Normalize to 0-8 range for block characters
    return data.map(v => Math.round(((v - min) / range) * 8));
  }, [data]);
  
  // Determine trend color
  const trendColor = useMemo(() => {
    if (trend === 'up') return 'var(--price-up)';
    if (trend === 'down') return 'var(--price-down)';
    if (trend === 'neutral') return 'var(--text-tertiary)';
    
    // Auto: compare first and last
    if (data.length >= 2) {
      const first = data[0];
      const last = data[data.length - 1];
      if (last > first) return 'var(--price-up)';
      if (last < first) return 'var(--price-down)';
    }
    return 'var(--text-tertiary)';
  }, [data, trend]);
  
  // Sample data if width specified
  const displayData = useMemo(() => {
    if (!width || normalized.length <= width) return normalized;
    
    // Sample evenly across the data
    const step = normalized.length / width;
    return Array.from({ length: width }, (_, i) => 
      normalized[Math.floor(i * step)]
    );
  }, [normalized, width]);
  
  if (displayData.length === 0) return null;
  
  const config = HEIGHT_CONFIG[height];
  
  return (
    <span 
      className={cn(
        'font-mono inline-block whitespace-nowrap',
        config.fontSize,
        config.lineHeight,
        className
      )}
      style={{ color: trendColor }}
      aria-label={`Trend: ${displayData.map(v => BLOCKS[v]).join('')}`}
    >
      {displayData.map((v) => BLOCKS[v]).join('')}
    </span>
  );
}

/**
 * SparklineWithLabel - Sparkline with trend label
 */
export interface SparklineWithLabelProps extends SparklineProps {
  /** Label text */
  label?: string;
  /** Change value */
  changeValue?: string;
}

export function SparklineWithLabel({ 
  label, 
  changeValue,
  ...sparklineProps 
}: SparklineWithLabelProps) {
  return (
    <div className="flex items-center gap-2">
      {label && (
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          {label}
        </span>
      )}
      <Sparkline {...sparklineProps} />
      {changeValue && (
        <span className="text-[10px] font-medium" style={{ color: 'var(--text-tertiary)' }}>
          {changeValue}
        </span>
      )}
    </div>
  );
}

/**
 * PlaceholderSparkline - Shows placeholder when no data
 */
export function PlaceholderSparkline({ 
  width = 12,
  height = 'sm',
  className 
}: { 
  width?: number; 
  height?: 'xs' | 'sm' | 'md';
  className?: string;
}) {
  // Generate random-ish placeholder
  const placeholderData = useMemo(() => 
    Array.from({ length: width }, () => Math.floor(Math.random() * 8)),
  [width]);
  
  const config = HEIGHT_CONFIG[height];
  
  return (
    <span 
      className={cn(
        'font-mono inline-block whitespace-nowrap opacity-20',
        config.fontSize,
        config.lineHeight,
        className
      )}
      style={{ color: 'var(--text-tertiary)' }}
    >
      {placeholderData.map(v => BLOCKS[v]).join('')}
    </span>
  );
}
