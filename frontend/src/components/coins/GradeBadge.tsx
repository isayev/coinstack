import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { getGradeTier } from '@/utils/gradeUtils'

interface GradeBadgeProps {
  grade: string
  service?: string | null
  className?: string
}

/** Badge variant: grade-{tier} for known tiers, outline for unknown */
const TIER_TO_VARIANT: Record<string, string> = {
  ms: 'grade-ms',
  au: 'grade-au',
  ef: 'grade-ef',
  fine: 'grade-fine',
  good: 'grade-good',
  poor: 'grade-poor',
  unknown: 'outline',
}

export function GradeBadge({ grade, service, className }: GradeBadgeProps) {
  const tier = getGradeTier(grade)
  const variant = TIER_TO_VARIANT[tier] ?? 'outline'

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <Badge variant={variant} className="font-mono font-bold tracking-tight">
        {grade}
      </Badge>
      {service && service !== 'none' && (
        <Badge variant="secondary" className="text-[10px] h-5 px-1.5 opacity-80">
          {service.toUpperCase()}
        </Badge>
      )}
    </div>
  )
}
