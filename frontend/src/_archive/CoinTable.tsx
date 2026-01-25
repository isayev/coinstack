import { useNavigate } from "react-router-dom"
import { Coin } from "@/domain/schemas"
import { MetalBadge } from "@/components/coins/MetalBadge"
import { GradeBadge } from "@/components/coins/GradeBadge"
import { ImageOff, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react"
import { formatYear } from "@/lib/formatters"
import { useFilterStore, SortField } from "@/stores/filterStore"
import { cn } from "@/lib/utils"

interface CoinTableProps {
  coins: Coin[]
  selectedIds?: Set<number>
  onSelectionChange?: (ids: Set<number>) => void
}

export function CoinTable({ coins }: CoinTableProps) {
  const navigate = useNavigate()
  const { sortBy, sortDir, setSort } = useFilterStore()

  const SortHeader = ({ field, label, className }: { field: SortField, label: string, className?: string }) => {
    return (
      <th
        className={cn("px-4 py-3 cursor-pointer hover:bg-muted/80 transition-colors select-none group", className)}
        onClick={() => setSort(field)}
      >
        <div className={cn("flex items-center gap-1", className?.includes("text-right") && "justify-end")}>
          {label}
          <span className="text-muted-foreground/50 group-hover:text-muted-foreground">
            {sortBy === field ? (
              sortDir === "asc" ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
            ) : (
              <ArrowUpDown className="w-3 h-3 opacity-0 group-hover:opacity-100" />
            )}
          </span>
        </div>
      </th>
    )
  }

  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 border-b text-xs uppercase text-muted-foreground font-semibold">
            <tr>
              <th className="px-4 py-3 w-12">Img</th>
              <SortHeader field="name" label="Ruler / Issuer" />
              <SortHeader field="metal" label="Metal" />
              <SortHeader field="denomination" label="Denomination" />
              <SortHeader field="grade" label="Grade" />
              <SortHeader field="weight" label="Weight" />
              <SortHeader field="price" label="Acquisition" className="text-right" />
            </tr>
          </thead>
          <tbody className="divide-y">
            {coins.map((coin) => (
              <tr
                key={coin.id}
                className="hover:bg-muted/30 cursor-pointer transition-colors"
                onClick={() => navigate(`/coins/${coin.id}`)}
              >
                <td className="px-4 py-2">
                  <div className="w-10 h-10 rounded overflow-hidden bg-muted border">
                    {coin.images && coin.images[0] ? (
                      <img src={coin.images[0].url} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center opacity-20">
                        <ImageOff className="w-4 h-4" />
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-2">
                  <div className="font-bold text-foreground">{coin.attribution.issuer}</div>
                  <div className="text-[10px] text-muted-foreground uppercase tracking-tight">
                    {coin.attribution.mint} • {formatYear(coin.attribution.year_start)}
                  </div>
                </td>
                <td className="px-4 py-2">
                  {coin.metal && <MetalBadge metal={coin.metal} className="scale-90 origin-left" />}
                </td>
                <td className="px-4 py-2 capitalize">
                  {(coin.category || 'unknown').replace('_', ' ')}
                </td>
                <td className="px-4 py-2">
                  <GradeBadge grade={coin.grading.grade || "Ungraded"} service={coin.grading.service || undefined} className="scale-90 origin-left" />
                </td>
                <td className="px-4 py-2 font-mono text-xs">
                  {coin.dimensions.weight_g} g
                </td>
                <td className="px-4 py-2 text-right">
                  {coin.acquisition?.price ? (
                    <div className="font-bold">
                      {new Intl.NumberFormat('en-US', { style: 'currency', currency: coin.acquisition.currency || 'USD' }).format(coin.acquisition.price)}
                    </div>
                  ) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}