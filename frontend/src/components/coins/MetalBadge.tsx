import { Badge } from '@/components/ui/badge'
import { Metal } from '@/domain/schemas'
import { cn } from '@/lib/utils'

interface MetalBadgeProps {
  metal: Metal
  className?: string
}

const METAL_SYMBOLS: Record<Metal, string> = {
  gold: 'Au',
  silver: 'Ag',
  bronze: 'Ae',
  copper: 'Cu',
  electrum: 'El',
  billon: 'Bi',
  potin: 'Po',
  orichalcum: 'Or',
  lead: 'Pb',
  ae: 'Ae',
}

export function MetalBadge({ metal, className }: MetalBadgeProps) {
  // Use typed variants from Badge
  const variant = (metal === 'gold' || metal === 'silver' || metal === 'bronze') 
    ? metal 
    : 'outline'

  return (
    <Badge 
      variant={variant as any} 
      className={cn("gap-1 font-mono uppercase tracking-wider", className)}
    >
      <span className="opacity-70 text-[10px]">{METAL_SYMBOLS[metal]}</span>
      {metal}
    </Badge>
  )
}
