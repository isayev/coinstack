/**
 * MetalBadge - Periodic table style badge for coin metals
 * 
 * Displays the element symbol (Au, Ag, AE, etc.) with
 * color-coded background based on metal type.
 */

import { cn } from "@/lib/utils";

export type MetalType = 
  | 'gold' | 'silver' | 'bronze' | 'copper' | 'billon' 
  | 'electrum' | 'orichalcum' | 'brass' | 'ae' | 'lead' | 'potin';

interface MetalConfig {
  symbol: string;
  label: string;
  cssVar: string;
}

const METAL_CONFIG: Record<string, MetalConfig> = {
  gold: { symbol: 'Au', label: 'Gold', cssVar: 'au' },
  silver: { symbol: 'Ag', label: 'Silver', cssVar: 'ag' },
  bronze: { symbol: 'AE', label: 'Bronze', cssVar: 'cu' },
  copper: { symbol: 'Cu', label: 'Copper', cssVar: 'copper' },
  billon: { symbol: 'BI', label: 'Billon', cssVar: 'bi' },
  electrum: { symbol: 'EL', label: 'Electrum', cssVar: 'el' },
  orichalcum: { symbol: 'OR', label: 'Orichalcum', cssVar: 'or' },
  brass: { symbol: 'BR', label: 'Brass', cssVar: 'br' },
  ae: { symbol: 'Æ', label: 'AE', cssVar: 'ae' },
  lead: { symbol: 'Pb', label: 'Lead', cssVar: 'pb' },
  potin: { symbol: 'Po', label: 'Potin', cssVar: 'po' },
  // Fallback aliases
  ar: { symbol: 'Ag', label: 'Silver', cssVar: 'ag' },
  au: { symbol: 'Au', label: 'Gold', cssVar: 'au' },
};

interface MetalBadgeProps {
  metal: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showGlow?: boolean;
  count?: number;
  interactive?: boolean;
  active?: boolean;
  onClick?: () => void;
  className?: string;
}

export function MetalBadge({
  metal,
  size = 'md',
  showLabel = false,
  showGlow = false,
  count,
  interactive = false,
  active = false,
  onClick,
  className,
}: MetalBadgeProps) {
  const config = METAL_CONFIG[metal.toLowerCase()] || {
    symbol: metal.slice(0, 2).toUpperCase(),
    label: metal,
    cssVar: 'ae',
  };

  // Size classes - lg meets 44px touch target for mobile accessibility
  // Use sm/md only in desktop contexts
  const sizeClasses = {
    sm: 'min-w-[28px] h-[22px] text-[10px] px-1.5',  // Desktop only
    md: 'min-w-[36px] h-[28px] text-xs px-2',        // Desktop only
    lg: 'min-w-[44px] h-[44px] text-sm px-3',        // Mobile-safe touch target
  };

  return (
    <div
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? onClick : undefined}
      onKeyDown={interactive ? (e) => e.key === 'Enter' && onClick?.() : undefined}
      className={cn(
        'inline-flex items-center justify-center gap-1 rounded font-bold font-mono',
        'transition-all duration-200',
        sizeClasses[size],
        interactive && 'cursor-pointer hover:scale-105',
        (interactive || showGlow) && 'metal-badge-glow',
        showGlow && 'shadow-lg',
        active && 'ring-2 ring-offset-1 ring-offset-[var(--bg-card)]',
        className
      )}
      style={{
        background: `var(--metal-${config.cssVar}-subtle)`,
        color: `var(--metal-${config.cssVar}-text)`,
        border: `1px solid var(--metal-${config.cssVar}-border)`,
        '--tw-ring-color': active ? `var(--metal-${config.cssVar})` : undefined,
        '--metal-glow-color': `var(--metal-${config.cssVar})`,
      } as React.CSSProperties}
      title={config.label}
    >
      <span>{config.symbol}</span>
      {count !== undefined && (
        <span className="opacity-70 font-normal">{count}</span>
      )}
      {showLabel && (
        <span className="font-normal text-[0.85em] opacity-80">{config.label}</span>
      )}
    </div>
  );
}

/**
 * MetalBadgeGroup - Interactive metal filter badges with counts
 */
interface MetalBadgeGroupProps {
  metals: { metal: string; count: number }[];
  activeMetals?: string[];
  onMetalClick?: (metal: string) => void;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function MetalBadgeGroup({
  metals,
  activeMetals = [],
  onMetalClick,
  size = 'md',
  className,
}: MetalBadgeGroupProps) {
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {metals.map(({ metal, count }) => (
        <MetalBadge
          key={metal}
          metal={metal}
          count={count}
          size={size}
          interactive={!!onMetalClick}
          active={activeMetals.includes(metal.toLowerCase())}
          onClick={() => onMetalClick?.(metal)}
          className={count === 0 ? 'opacity-40 pointer-events-none' : ''}
        />
      ))}
    </div>
  );
}
