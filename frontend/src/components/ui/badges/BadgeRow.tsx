/**
 * BadgeRow - Combines Metal, Grade, and Certification badges
 * 
 * Standard layout for displaying coin badges in a row
 */

import { cn } from "@/lib/utils";
import { MetalBadge } from "./MetalBadge";
import { GradeBadge } from "./GradeBadge";
import { CertBadge } from "./CertBadge";

interface BadgeRowProps {
  metal?: string | null;
  grade?: string | null;
  gradeNumeric?: number | null;
  certService?: string | null;
  certNumber?: string | null;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function BadgeRow({
  metal,
  grade,
  gradeNumeric,
  certService,
  certNumber,
  size = 'sm',
  className,
}: BadgeRowProps) {
  const hasAnyBadge = metal || grade || (certService && certService !== 'raw' && certService !== 'self');
  
  if (!hasAnyBadge) {
    return null;
  }

  return (
    <div className={cn('flex items-center gap-1.5 flex-wrap', className)}>
      {metal && (
        <MetalBadge metal={metal} size={size} />
      )}
      {grade && (
        <GradeBadge 
          grade={grade} 
          score={gradeNumeric ?? undefined} 
          size={size}
          showNumeric={!!gradeNumeric}
        />
      )}
      {certService && certService !== 'raw' && certService !== 'self' && (
        <CertBadge 
          service={certService} 
          certNumber={certNumber ?? undefined}
          size={size}
        />
      )}
    </div>
  );
}

// Re-export individual components for convenience
export { MetalBadge, MetalBadgeGroup } from "./MetalBadge";
export { GradeBadge, GradeSpectrum } from "./GradeBadge";
export { CertBadge, CertificationSummary } from "./CertBadge";
