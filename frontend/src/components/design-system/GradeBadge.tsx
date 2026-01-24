/**
 * GradeBadge - Temperature-scaled grade indicator
 * 
 * Uses cold→hot color scale:
 * - Poor (blue) → Good (teal) → Fine (green) → EF (yellow) → AU (orange) → MS (red)
 * 
 * @module design-system/GradeBadge
 */

import { cn } from '@/lib/utils';
import { parseGrade, GradeTier } from './colors';

export interface GradeBadgeProps {
  /** Grade string (e.g., "VF", "MS65", "NGC AU58") */
  grade: string;
  /** Numeric grade if available (e.g., 65 for MS65) */
  numericGrade?: number;
  /** Certification service */
  service?: 'NGC' | 'PCGS' | null;
  /** Show /10 scale */
  showScale?: boolean;
  /** Size variant */
  size?: 'xs' | 'sm' | 'md';
  /** Additional className */
  className?: string;
}

const SIZE_CLASSES = {
  xs: 'text-[9px] px-1 py-0',
  sm: 'text-[10px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-0.5',
};

export function GradeBadge({ 
  grade, 
  numericGrade, 
  service,
  showScale = false,
  size = 'sm',
  className 
}: GradeBadgeProps) {
  const config = parseGrade(grade);
  const tier: GradeTier = config?.tier || 'fine';
  
  // Check for service in grade string
  const hasNGC = grade?.toUpperCase().includes('NGC') || service === 'NGC';
  const hasPCGS = grade?.toUpperCase().includes('PCGS') || service === 'PCGS';
  
  // Clean grade text (remove service prefix)
  const cleanGrade = grade
    ?.replace(/NGC\s*/i, '')
    .replace(/PCGS\s*/i, '')
    .trim();
  
  return (
    <div 
      className={cn(
        'inline-flex items-center gap-1 rounded font-semibold',
        SIZE_CLASSES[size],
        className
      )}
      style={{
        background: hasNGC 
          ? 'var(--grade-ngc-bg)' 
          : hasPCGS 
            ? 'var(--grade-pcgs-bg)'
            : `var(--grade-${tier}-bg)`,
        color: hasNGC 
          ? 'var(--grade-ngc)' 
          : hasPCGS 
            ? 'var(--grade-pcgs)'
            : `var(--grade-${tier})`,
      }}
    >
      {/* Service badge */}
      {(hasNGC || hasPCGS) && (
        <span className="font-bold">{hasNGC ? 'NGC' : 'PCGS'}</span>
      )}
      
      {/* Grade text */}
      <span>{cleanGrade}</span>
      
      {/* Numeric grade */}
      {numericGrade && (
        <span className="opacity-70">{numericGrade}</span>
      )}
      
      {/* /10 scale */}
      {showScale && config && !numericGrade && (
        <span className="opacity-50 text-[0.8em]">
          {config.numeric}/10
        </span>
      )}
    </div>
  );
}

/**
 * GradeScale - Visual temperature scale showing all grades
 */
export function GradeScale({ highlightTier }: { highlightTier?: GradeTier }) {
  const tiers: { tier: GradeTier; label: string }[] = [
    { tier: 'poor', label: 'Poor' },
    { tier: 'good', label: 'Good' },
    { tier: 'fine', label: 'F/VF' },
    { tier: 'ef', label: 'EF' },
    { tier: 'au', label: 'AU' },
    { tier: 'ms', label: 'MS' },
  ];
  
  return (
    <div className="flex rounded overflow-hidden">
      {tiers.map(({ tier, label }) => (
        <div 
          key={tier}
          className={cn(
            'flex-1 py-1 px-2 text-center text-[10px] font-semibold transition-opacity',
            highlightTier && highlightTier !== tier && 'opacity-40'
          )}
          style={{
            background: `var(--grade-${tier})`,
            color: tier === 'ef' || tier === 'au' ? 'var(--bg-base)' : 'var(--bg-base)',
          }}
        >
          {label}
        </div>
      ))}
    </div>
  );
}
