/**
 * MetalBadge - Element-style metal indicator
 * 
 * Displays metal type using periodic table-style element symbols.
 * Precious metals (Au, Ag, EL) get a subtle glow on hover.
 * 
 * @module design-system/MetalBadge
 */

import { cn } from '@/lib/utils';
import { METAL_CONFIG, MetalType } from './colors';

export type MetalBadgeSize = 'xs' | 'sm' | 'md' | 'lg';

export interface MetalBadgeProps {
  /** Metal type */
  metal: string;
  /** Size variant */
  size?: MetalBadgeSize;
  /** Show glow effect for precious metals */
  showGlow?: boolean;
  /** Additional className */
  className?: string;
}

const SIZE_CLASSES: Record<MetalBadgeSize, string> = {
  xs: 'w-5 h-5 text-[9px]',
  sm: 'w-6 h-6 text-[10px]',
  md: 'w-7 h-7 text-xs',
  lg: 'w-8 h-8 text-sm',
};

export function MetalBadge({ 
  metal, 
  size = 'md', 
  showGlow = false,
  className 
}: MetalBadgeProps) {
  const metalKey = metal?.toLowerCase() as MetalType;
  const config = METAL_CONFIG[metalKey] || METAL_CONFIG.ae;
  
  return (
    <div 
      className={cn(
        'font-mono font-bold rounded flex items-center justify-center',
        'transition-all duration-200',
        SIZE_CLASSES[size],
        className
      )}
      style={{
        background: `var(--metal-${config.cssVar}-subtle)`,
        color: `var(--metal-${config.cssVar}-text)`,
        border: `1px solid var(--metal-${config.cssVar}-border)`,
        boxShadow: showGlow && config.precious 
          ? `0 0 8px var(--metal-${config.cssVar})`
          : undefined,
      }}
      title={config.name}
    >
      {config.symbol}
    </div>
  );
}

/**
 * MetalChip - Selectable metal filter chip with count.
 * Accepts any string (API metal key); unknown metals fall back to AE styling.
 * Use label="name" in filter sidebars so "ae" displays as "Bronze (AE)".
 */
export interface MetalChipProps {
  metal: string;
  count?: number;
  selected?: boolean;
  onClick?: () => void;
  /** 'symbol' (default) shows e.g. Æ, Au; 'name' shows e.g. Bronze (AE), Gold (for filter sidebar) */
  label?: 'symbol' | 'name';
}

export function MetalChip({ metal, count, selected, onClick, label = 'symbol' }: MetalChipProps) {
  const metalKey = metal?.toLowerCase() as MetalType;
  const config = METAL_CONFIG[metalKey] ?? METAL_CONFIG.ae;
  const displayText = label === 'name' ? config.name : config.symbol;

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-1.5 px-2.5 py-1.5 rounded-md transition-all',
        label === 'name' ? 'text-xs font-semibold' : 'font-mono text-xs font-semibold',
        selected && 'ring-2 ring-offset-2 scale-105'
      )}
      style={{
        background: `var(--metal-${config.cssVar}-subtle)`,
        color: `var(--metal-${config.cssVar}-text)`,
        border: `1px solid var(--metal-${config.cssVar}-border)`,
        // Selected state: gold ring
        boxShadow: selected ? `0 0 0 2px var(--bg-surface), 0 0 0 4px var(--metal-au)` : undefined,
      }}
      title={config.name}
    >
      <span>{displayText}</span>
      {count !== undefined && (
        <span className="opacity-60 tabular-nums">{count}</span>
      )}
    </button>
  );
}
