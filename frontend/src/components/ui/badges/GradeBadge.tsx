/**
 * GradeBadge - Temperature scale badge for coin grades
 * 
 * Uses a cold-to-hot color scale where:
 * - Poor/Fair = Cold blue (low quality)
 * - Fine/VF = Green/Yellow (medium quality)
 * - EF/AU/MS = Orange/Red (high quality)
 */

import { cn } from "@/lib/utils";

type GradeTier = 'poor' | 'good' | 'fine' | 'ef' | 'au' | 'ms' | 'unknown';

interface GradeConfig {
  tier: GradeTier;
  label: string;
  cssVar: string;
  numeric?: number;
}

const GRADE_CONFIG: Record<string, GradeConfig> = {
  // Poor tier (cold)
  'P': { tier: 'poor', label: 'Poor', cssVar: 'poor', numeric: 1 },
  'FR': { tier: 'poor', label: 'Fair', cssVar: 'poor', numeric: 2 },
  'AG': { tier: 'poor', label: 'About Good', cssVar: 'poor', numeric: 3 },
  
  // Good tier (cool)
  'G': { tier: 'good', label: 'Good', cssVar: 'good', numeric: 6 },
  'VG': { tier: 'good', label: 'Very Good', cssVar: 'good', numeric: 10 },
  
  // Fine tier (neutral)
  'F': { tier: 'fine', label: 'Fine', cssVar: 'fine', numeric: 15 },
  'VF': { tier: 'fine', label: 'Very Fine', cssVar: 'fine', numeric: 30 },
  
  // EF tier (warm)
  'EF': { tier: 'ef', label: 'Extremely Fine', cssVar: 'ef', numeric: 45 },
  'XF': { tier: 'ef', label: 'Extremely Fine', cssVar: 'ef', numeric: 45 },
  
  // AU tier (hot)
  'AU': { tier: 'au', label: 'About Uncirculated', cssVar: 'au', numeric: 55 },
  
  // MS tier (fire)
  'MS': { tier: 'ms', label: 'Mint State', cssVar: 'ms', numeric: 65 },
  'FDC': { tier: 'ms', label: 'Fleur de Coin', cssVar: 'ms', numeric: 70 },
  'BU': { tier: 'ms', label: 'Brilliant Uncirculated', cssVar: 'ms', numeric: 63 },
  'UNC': { tier: 'ms', label: 'Uncirculated', cssVar: 'ms', numeric: 60 },
};

/**
 * Parse a grade string to extract the base grade and numeric value
 * Examples: "VF 35" -> { base: "VF", numeric: 35 }
 *           "VF" -> { base: "VF", numeric: undefined }
 *           "MS 65" -> { base: "MS", numeric: 65 }
 */
function parseGrade(grade: string): { base: string; numeric?: number } {
  const normalized = grade.toUpperCase().trim();
  
  // Try to match "BASE NUMERIC" pattern
  const match = normalized.match(/^([A-Z]+)\s*(\d+)?$/);
  if (match) {
    return {
      base: match[1],
      numeric: match[2] ? parseInt(match[2], 10) : undefined,
    };
  }
  
  return { base: normalized };
}

interface GradeBadgeProps {
  grade: string;
  score?: number; // Optional explicit numeric grade
  size?: 'sm' | 'md' | 'lg';
  showNumeric?: boolean;
  interactive?: boolean;
  active?: boolean;
  onClick?: () => void;
  className?: string;
}

export function GradeBadge({
  grade,
  score,
  size = 'md',
  showNumeric = true,
  interactive = false,
  active = false,
  onClick,
  className,
}: GradeBadgeProps) {
  const parsed = parseGrade(grade);
  const config = GRADE_CONFIG[parsed.base] || {
    tier: 'unknown' as GradeTier,
    label: grade,
    cssVar: 'unknown',
  };
  
  const numericValue = score ?? parsed.numeric;
  const displayGrade = parsed.base;

  const sizeClasses = {
    sm: 'min-w-[32px] h-[22px] text-[10px] px-1.5 gap-0.5',
    md: 'min-w-[40px] h-[28px] text-xs px-2 gap-1',
    lg: 'min-w-[52px] h-[36px] text-sm px-3 gap-1.5',
  };

  return (
    <div
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? onClick : undefined}
      onKeyDown={interactive ? (e) => e.key === 'Enter' && onClick?.() : undefined}
      className={cn(
        'inline-flex items-center justify-center rounded font-bold',
        'transition-all duration-200',
        sizeClasses[size],
        interactive && 'cursor-pointer hover:scale-105',
        active && 'ring-2 ring-offset-1 ring-offset-[var(--bg-card)]',
        className
      )}
      style={{
        background: `var(--grade-${config.cssVar}-bg)`,
        color: `var(--grade-${config.cssVar})`,
        border: `1px solid var(--grade-${config.cssVar})`,
        ringColor: active ? `var(--grade-${config.cssVar})` : undefined,
      }}
      title={config.label}
    >
      <span>{displayGrade}</span>
      {showNumeric && numericValue !== undefined && (
        <span className="opacity-80 font-normal">{numericValue}</span>
      )}
    </div>
  );
}

/**
 * GradeSpectrum - Horizontal bar showing grade distribution
 */
interface GradeDistribution {
  grade: string;
  count: number;
}

interface GradeSpectrumProps {
  grades: GradeDistribution[];
  activeGrades?: string[];
  onGradeClick?: (grade: string) => void;
  showCounts?: boolean;
  className?: string;
}

export function GradeSpectrum({
  grades,
  activeGrades = [],
  onGradeClick,
  showCounts = true,
  className,
}: GradeSpectrumProps) {
  const total = grades.reduce((sum, g) => sum + g.count, 0);
  
  // Sort grades by numeric value
  const sortedGrades = [...grades].sort((a, b) => {
    const aConfig = GRADE_CONFIG[parseGrade(a.grade).base];
    const bConfig = GRADE_CONFIG[parseGrade(b.grade).base];
    return (aConfig?.numeric || 0) - (bConfig?.numeric || 0);
  });

  return (
    <div className={cn('space-y-2', className)}>
      {/* Spectrum bar */}
      <div className="flex h-6 rounded overflow-hidden">
        {sortedGrades.map(({ grade, count }) => {
          const parsed = parseGrade(grade);
          const config = GRADE_CONFIG[parsed.base] || { cssVar: 'unknown' };
          const width = total > 0 ? (count / total) * 100 : 0;
          const isActive = activeGrades.includes(grade.toLowerCase());
          
          if (width < 1) return null;
          
          return (
            <div
              key={grade}
              role={onGradeClick ? 'button' : undefined}
              tabIndex={onGradeClick ? 0 : undefined}
              onClick={() => onGradeClick?.(grade)}
              className={cn(
                'flex items-center justify-center transition-all',
                onGradeClick && 'cursor-pointer hover:brightness-110',
                isActive && 'ring-2 ring-white ring-inset'
              )}
              style={{
                width: `${width}%`,
                background: `var(--grade-${config.cssVar})`,
                minWidth: width > 0 ? '20px' : 0,
              }}
              title={`${grade}: ${count}`}
            >
              {width > 8 && (
                <span className="text-[10px] font-bold text-white/90 truncate px-1">
                  {parsed.base}
                </span>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Labels */}
      {showCounts && (
        <div className="flex justify-between text-[10px]" style={{ color: 'var(--text-muted)' }}>
          <span>P/F</span>
          <span>VF</span>
          <span>EF</span>
          <span>MS</span>
        </div>
      )}
    </div>
  );
}
