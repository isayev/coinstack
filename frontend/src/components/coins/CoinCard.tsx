import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
  CardDescription
} from "@/components/ui/card"
import { Coin } from "@/domain/schemas"
import { MetalBadge } from "./MetalBadge"
import { GradeBadge } from "./GradeBadge"
import { Separator } from "@/components/ui/separator"
import { Scale, Ruler, Coins } from "lucide-react"
import { formatYear } from "@/lib/formatters"

interface CoinCardProps {
  coin: Coin
  onClick?: (coin: Coin) => void
}

export function CoinCard({ coin, onClick }: CoinCardProps) {
  const handleClick = () => {
    if (onClick) onClick(coin)
  }

  // Format year range
  const displayYear = () => {
    const { year_start, year_end } = coin.attribution
    if (year_start === null || year_start === undefined) return "Date Unknown"
    if (year_end === null || year_end === undefined || year_start === year_end) {
      return formatYear(year_start)
    }
    return `${formatYear(year_start)}–${formatYear(year_end)}`
  }

  return (
    <Card
      className="coin-card cursor-pointer hover:shadow-md transition-shadow h-full flex flex-col overflow-hidden"
      onClick={handleClick}
    >
      {/* Primary Image */}
      <div className="aspect-[4/3] bg-muted relative overflow-hidden border-b">
        {coin.images && coin.images.length > 0 ? (
          <img
            src={coin.images.find((img: any) => img.is_primary)?.url || coin.images[0].url}
            alt={coin.attribution.issuer || "Coin Image"}
            className="object-cover w-full h-full transition-transform hover:scale-105"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground/40">
            <Coins className="w-12 h-12" />
          </div>
        )}
      </div>

      <CardHeader className="pb-3 pt-4">
        <div className="flex justify-between items-start gap-2">
          <div className="space-y-1">
            <CardTitle className="text-lg font-bold leading-tight">
              {coin.attribution.issuer}
            </CardTitle>
            <CardDescription className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              {coin.attribution.mint || "Uncertain Mint"} • {displayYear()}
            </CardDescription>
          </div>
          {coin.metal && <MetalBadge metal={coin.metal} />}
        </div>
      </CardHeader>

      <CardContent className="pb-3 flex-grow space-y-4">
        {/* Physics Grid */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Scale className="w-4 h-4" />
            <span>{coin.dimensions.weight_g}g</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Ruler className="w-4 h-4" />
            <span>{coin.dimensions.diameter_mm}mm</span>
          </div>
        </div>

        {/* Category Chip */}
        <div className="flex flex-wrap gap-2">
          <div className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border opacity-70
             ${getCategoryStyle(coin.category)}`}>
            {coin.category.replace('_', ' ')}
          </div>
        </div>
      </CardContent>

      <Separator className="bg-border/50" />

      <CardFooter className="pt-3 pb-3 flex justify-between items-center bg-muted/20">
        <GradeBadge
          grade={coin.grading.grade || "Ungraded"}
          service={coin.grading.service || undefined}
        />

        {coin.acquisition?.price && (
          <div className="font-mono text-sm font-medium text-muted-foreground">
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: coin.acquisition.currency || 'USD'
            }).format(coin.acquisition.price)}
          </div>
        )}
      </CardFooter>
    </Card>
  )
}

function getCategoryStyle(category: string): string {
  // Map category to our tailwind-config colors (via inline styles or utility classes if generated)
  // For now using borders/text colors based on the design tokens we added
  switch (category) {
    case 'roman_imperial': return 'border-category-imperial text-category-imperial'
    case 'roman_republic': return 'border-category-republic text-category-republic'
    case 'greek': return 'border-category-greek text-category-greek'
    case 'byzantine': return 'border-category-byzantine text-category-byzantine'
    case 'roman_provincial': return 'border-category-provincial text-category-provincial'
    default: return 'border-muted-foreground text-muted-foreground'
  }
}