/**
 * RarityIndicator - Gemstone-inspired rarity display
 * 
 * Uses gemstone metaphor for intuitive rarity understanding:
 * - Common (Quartz) → Scarce (Amethyst) → Rare (Sapphire) 
 * - Very Rare (Emerald) → Extremely Rare (Ruby) → Unique (Diamond)
 * 
 * @module design-system/RarityIndicator
 */

import { cn } from '@/lib/utils';
import { parseRarity, RARITY_CONFIG, RarityType } from './colors';

export interface RarityIndicatorProps {
  /** Rarity value */
  rarity: string | null | undefined;
  /** Display variant */
  variant?: 'dot' | 'badge' | 'full';
  /** Show tooltip */
  showTooltip?: boolean;
  /** Additional className */
  className?: string;
}

export function RarityIndicator({ 
  rarity, 
  variant = 'dot',
  showTooltip = true,
  className 
}: RarityIndicatorProps) {
  const rarityType = parseRarity(rarity);
  if (!rarityType) return null;
  
  const config = RARITY_CONFIG[rarityType];
  
  // Dot variant - minimal
  if (variant === 'dot') {
    return (
      <span 
        className={cn(
          'w-2 h-2 rounded-full inline-block',
          rarityType === 'u' && 'animate-pulse',
          className
        )}
        style={{ background: `var(--rarity-${rarityType})` }}
        title={showTooltip ? `${config.label} (${config.gem})` : undefined}
      />
    );
  }
  
  // Badge variant - code only
  if (variant === 'badge') {
    return (
      <span 
        className={cn(
          'px-1.5 py-0.5 rounded text-[10px] font-semibold',
          rarityType === 'u' && 'border border-white/20',
          className
        )}
        style={{
          background: `var(--rarity-${rarityType}-bg)`,
          color: `var(--rarity-${rarityType})`,
        }}
        title={showTooltip ? `${config.label} (${config.gem})` : undefined}
      >
        {config.code}
      </span>
    );
  }
  
  // Full variant - dot + code + label
  return (
    <div 
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded',
        className
      )}
      style={{
        background: `var(--rarity-${rarityType}-bg)`,
      }}
    >
      <span 
        className={cn(
          'w-2 h-2 rounded-full',
          rarityType === 'u' && 'animate-pulse'
        )}
        style={{ background: `var(--rarity-${rarityType})` }}
      />
      <span 
        className="text-xs font-semibold"
        style={{ color: `var(--rarity-${rarityType})` }}
      >
        {config.code}
      </span>
      <span 
        className="text-xs opacity-70"
        style={{ color: `var(--rarity-${rarityType})` }}
      >
        {config.label}
      </span>
    </div>
  );
}

/**
 * RarityLegend - Shows all rarity levels
 */
export function RarityLegend({ compact = false }: { compact?: boolean }) {
  const rarities: RarityType[] = ['c', 's', 'r1', 'r2', 'r3', 'u'];
  
  return (
    <div className={cn('flex gap-2', compact ? 'flex-wrap' : 'flex-col')}>
      {rarities.map((r) => (
        <RarityIndicator 
          key={r} 
          rarity={r} 
          variant={compact ? 'badge' : 'full'} 
          showTooltip={false}
        />
      ))}
    </div>
  );
}
