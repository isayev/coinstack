import { Coin } from "@/domain/schemas"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { MetalBadge } from "@/components/coins/MetalBadge"
import { GradeBadge } from "@/components/coins/GradeBadge"
import { formatYear } from "@/lib/formatters"

interface CoinDetailProps {
  coin: Coin
}

export function CoinDetail({ coin }: CoinDetailProps) {
  const displayYear = () => {
    const { year_start, year_end } = coin.attribution
    if (year_start === null || year_start === undefined) return "Date Unknown"
    if (year_end === null || year_end === undefined || year_start === year_end) {
      return formatYear(year_start)
    }
    return `${formatYear(year_start)}–${formatYear(year_end)}`
  }

  const primaryImage = coin.images?.find((img: any) => img.is_primary) || (coin.images && coin.images[0])

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Left Column: Image & Quick Stats */}
      <div className="space-y-6">
        <Card className="overflow-hidden">
          <div className="aspect-square bg-muted flex items-center justify-center text-muted-foreground border-b">
            {primaryImage ? (
              <img
                src={primaryImage.url}
                alt={coin.attribution.issuer || "Coin Image"}
                className="object-contain w-full h-full"
              />
            ) : (
              <span className="text-sm">No Image</span>
            )}
          </div>
          {coin.images && coin.images.length > 1 && (
            <div className="p-2 flex gap-2 overflow-x-auto scrollbar-thin">
              {coin.images.map((img: any, idx: number) => (
                <div key={idx} className="w-12 h-12 rounded border bg-muted flex-shrink-0 overflow-hidden">
                  <img src={img.url} className="object-cover w-full h-full" />
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Key Data</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Category</span>
              <span className="font-medium capitalize">{(coin.category || 'unknown').replace('_', ' ')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Metal</span>
              {coin.metal ? <MetalBadge metal={coin.metal} /> : <span className="text-muted-foreground">-</span>}
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Weight</span>
              {coin.dimensions.weight_g ? (
                <span className="font-mono">{coin.dimensions.weight_g} g</span>
              ) : (
                <span className="text-destructive text-xs font-semibold">Missing</span>
              )}
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Diameter</span>
              {coin.dimensions.diameter_mm ? (
                <span className="font-mono">{coin.dimensions.diameter_mm} mm</span>
              ) : (
                <span className="text-destructive text-xs font-semibold">Missing</span>
              )}
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Axis</span>
              {coin.dimensions.die_axis !== null && coin.dimensions.die_axis !== undefined ? (
                <span className="font-mono">{coin.dimensions.die_axis} h</span>
              ) : (
                <span className="text-muted-foreground">-</span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Middle/Right: Detailed Info */}
      <div className="md:col-span-2 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{coin.attribution.issuer}</h1>
          <p className="text-xl text-muted-foreground mt-1">
            {coin.attribution.mint} • {displayYear()}
          </p>
        </div>

        <Separator />

        {/* Grading Section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Grade</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3">
                <GradeBadge grade={coin.grading.grade || "Ungraded"} service={coin.grading.service || undefined} className="text-xl scale-110 origin-left" />
                {coin.grading.grading_state !== 'raw' && (
                  <Badge variant="outline" className="text-xs">{coin.grading.grading_state}</Badge>
                )}
              </div>
              {coin.grading.certification_number && (
                <p className="text-xs text-muted-foreground mt-2 font-mono">
                  Cert: {coin.grading.certification_number}
                </p>
              )}
            </CardContent>
          </Card>

          {coin.acquisition && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Acquisition</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold flex items-center gap-1">
                  <span className="text-muted-foreground text-lg">$</span>
                  {(coin.acquisition.price || 0).toFixed(2)}
                </div>
                <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                  <span>{coin.acquisition.source}</span>
                  <span>•</span>
                  <span>{coin.acquisition.date}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Notes / Description Placeholder */}
        {/* Description Section */}
        <Card>
          <CardHeader>
            <CardTitle>Description</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {coin.description && (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <p>{coin.description}</p>
              </div>
            )}

            {/* Obverse & Reverse Specifics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <h4 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">Obverse</h4>
                {coin.obverse_description ? (
                  <p className="text-sm">{coin.obverse_description}</p>
                ) : <p className="text-sm italic text-muted-foreground">No description</p>}

                {coin.obverse_legend && (
                  <div className="mt-2 bg-muted/50 p-2 rounded text-xs font-mono break-words">
                    {coin.obverse_legend}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <h4 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">Reverse</h4>
                {coin.reverse_description ? (
                  <p className="text-sm">{coin.reverse_description}</p>
                ) : <p className="text-sm italic text-muted-foreground">No description</p>}

                {coin.reverse_legend && (
                  <div className="mt-2 bg-muted/50 p-2 rounded text-xs font-mono break-words">
                    {coin.reverse_legend}
                  </div>
                )}
              </div>
            </div>

            {!coin.description && !coin.obverse_description && !coin.reverse_description && (
              <p className="text-muted-foreground italic">No detailed description available.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
