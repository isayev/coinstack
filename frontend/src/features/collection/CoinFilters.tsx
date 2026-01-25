import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { useFilterStore } from "@/stores/filterStore"
import { X } from "lucide-react"

export function CoinFilters() {
    const {
        // Strings
        category,
        metal,
        issuing_authority,
        denomination,
        grade,
        rarity,
        mint_name,

        // Ranges
        priceRange,
        mint_year_gte,
        mint_year_lte,

        // Actions
        setCategory,
        setMetal,
        setIssuingAuthority,
        setDenomination,
        setGrade,
        setRarity,
        setMintName,
        setPriceRange,
        setMintYearGte,
        setMintYearLte,
        reset
    } = useFilterStore()

    // Helper for dealing with "all" vs specific values in Select
    const wrapValue = (val: string | null) => val || "all"
    const unwrapValue = (val: string) => (val === "all" ? null : val)

    return (
        <div className="flex flex-col h-full bg-card border-r w-80">
            <div className="p-4 border-b flex items-center justify-between">
                <h2 className="font-semibold">Filters</h2>
                <Button variant="ghost" size="sm" onClick={reset} className="h-8 px-2 text-muted-foreground">
                    Reset
                    <X className="ml-2 h-3 w-3" />
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto">
                <div className="p-4 space-y-6">

                    {/* Classification */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Classification</h3>

                        <div className="space-y-2">
                            <Label>Category</Label>
                            <Select value={wrapValue(category)} onValueChange={(v) => setCategory(unwrapValue(v))}>
                                <SelectTrigger>
                                    <SelectValue placeholder="All Categories" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Categories</SelectItem>
                                    <SelectItem value="imperial">Roman Imperial</SelectItem>
                                    <SelectItem value="republic">Roman Republic</SelectItem>
                                    <SelectItem value="provincial">Roman Provincial</SelectItem>
                                    <SelectItem value="byzantine">Byzantine</SelectItem>
                                    <SelectItem value="greek">Greek</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Metal</Label>
                            <div className="flex flex-wrap gap-2">
                                {[
                                    { id: 'gold', label: 'Gold', color: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20' },
                                    { id: 'silver', label: 'Silver', color: 'bg-slate-500/10 text-slate-600 border-slate-500/20' },
                                    { id: 'bronze', label: 'Bronze', color: 'bg-orange-700/10 text-orange-700 border-orange-700/20' },
                                    { id: 'copper', label: 'Copper', color: 'bg-orange-800/10 text-orange-800 border-orange-800/20' }
                                ].map((m) => (
                                    <Badge
                                        key={m.id}
                                        variant="outline"
                                        className={`cursor-pointer transition-colors ${metal === m.id
                                                ? m.color + ' ring-1 ring-offset-1'
                                                : 'hover:bg-muted text-muted-foreground'
                                            }`}
                                        onClick={() => setMetal(metal === m.id ? null : m.id)}
                                    >
                                        {m.label}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Denomination</Label>
                            <Input
                                placeholder="e.g. Denarius"
                                value={denomination || ""}
                                onChange={(e) => setDenomination(e.target.value || null)}
                            />
                        </div>
                    </div>

                    <Separator />

                    {/* Attribution */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Attribution</h3>

                        <div className="space-y-2">
                            <Label>Ruler / Issuer</Label>
                            <Input
                                placeholder="e.g. Augustus"
                                value={issuing_authority || ""}
                                onChange={(e) => setIssuingAuthority(e.target.value || null)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Mint</Label>
                            <Input
                                placeholder="e.g. Rome"
                                value={mint_name || ""}
                                onChange={(e) => setMintName(e.target.value || null)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Year Range</Label>
                            <div className="flex items-center gap-2">
                                <Input
                                    type="number"
                                    placeholder="From"
                                    value={mint_year_gte || ""}
                                    onChange={(e) => setMintYearGte(e.target.value ? parseInt(e.target.value) : null)}
                                />
                                <span className="text-muted-foreground">-</span>
                                <Input
                                    type="number"
                                    placeholder="To"
                                    value={mint_year_lte || ""}
                                    onChange={(e) => setMintYearLte(e.target.value ? parseInt(e.target.value) : null)}
                                />
                            </div>
                        </div>
                    </div>

                    <Separator />

                    {/* Grading & Value */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Details</h3>

                        <div className="space-y-2">
                            <Label>Grade</Label>
                            <Select value={wrapValue(grade)} onValueChange={(v) => setGrade(unwrapValue(v))}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Any Grade" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">Any Grade</SelectItem>
                                    <SelectItem value="XF">XF (Extremely Fine)</SelectItem>
                                    <SelectItem value="VF">VF (Very Fine)</SelectItem>
                                    <SelectItem value="F">F (Fine)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Rarity</Label>
                            <Select value={wrapValue(rarity)} onValueChange={(v) => setRarity(unwrapValue(v))}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Any Rarity" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">Any Rarity</SelectItem>
                                    <SelectItem value="common">Common</SelectItem>
                                    <SelectItem value="scarce">Scarce</SelectItem>
                                    <SelectItem value="rare">Rare</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Price Paid (USD)</Label>
                            <div className="flex items-center gap-2">
                                <Input
                                    type="number"
                                    placeholder="Min"
                                    value={priceRange[0] > 0 ? priceRange[0] : ""}
                                    onChange={(e) => setPriceRange([e.target.value ? parseInt(e.target.value) : 0, priceRange[1]])}
                                />
                                <span className="text-muted-foreground">-</span>
                                <Input
                                    type="number"
                                    placeholder="Max"
                                    value={priceRange[1] < 5000 ? priceRange[1] : ""}
                                    onChange={(e) => setPriceRange([priceRange[0], e.target.value ? parseInt(e.target.value) : 5000])}
                                />
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    )
}
