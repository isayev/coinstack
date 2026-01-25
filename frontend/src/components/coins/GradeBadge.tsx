import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface GradeBadgeProps {
  grade: string
  service?: string | null
  className?: string
}

// Map common grade strings to our design system tiers
function getGradeTier(grade: string): string {
  const g = grade.toLowerCase()
  
  if (g.includes('ms') || g.includes('unc') || g.includes('fdc') || g.includes('bu')) return 'grade-ms'
  if (g.includes('au')) return 'grade-au'
  if (g.includes('ef') || g.includes('xf')) return 'grade-ef'
  if (g.includes('vf') || g.includes('f')) return 'grade-fine' // Catch-all for Fine/VF
  if (g.includes('vg') || g.includes('g') || g.includes('good')) return 'grade-good'
  if (g.includes('poor') || g.includes('fair') || g.includes('ag')) return 'grade-poor'
  
  return 'outline'
}

export function GradeBadge({ grade, service, className }: GradeBadgeProps) {
  const tier = getGradeTier(grade)
  
  return (
    <div className={cn("flex items-center gap-1", className)}>
      <Badge variant={tier as any} className="font-mono font-bold tracking-tight">
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
