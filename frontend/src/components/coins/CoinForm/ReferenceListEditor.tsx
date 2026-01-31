
import { useState } from "react"
import { UseFormReturn, useFieldArray } from "react-hook-form"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Trash2, Plus, ChevronDown, ChevronRight } from "lucide-react"
import { CoinFormData } from "./schema"
import { CatalogReference } from "@/domain/schemas"
import { cn } from "@/lib/utils"

interface ReferenceListProps {
    form: UseFormReturn<CoinFormData>
}

const ATTRIBUTION_CONFIDENCE_OPTIONS = [
    { value: "certain", label: "Certain" },
    { value: "probable", label: "Probable" },
    { value: "possible", label: "Possible" },
    { value: "tentative", label: "Tentative" },
]

export function ReferenceListEditor({ form }: ReferenceListProps) {
    const { control, register, setValue, watch } = form
    const { fields, append, remove } = useFieldArray({
        control,
        name: "references"
    })
    const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set())

    const toggleExpanded = (index: number) => {
        const newExpanded = new Set(expandedIndices)
        if (newExpanded.has(index)) {
            newExpanded.delete(index)
        } else {
            newExpanded.add(index)
        }
        setExpandedIndices(newExpanded)
    }

    const addReference = () => {
        append({
            catalog: "",
            number: "",
            volume: null,
            is_primary: false,
        } as CatalogReference)
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Catalog References List</h3>
                <Button type="button" variant="outline" size="sm" onClick={addReference} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add Reference
                </Button>
            </div>

            <div className="space-y-3">
                {fields.map((field, index) => {
                    const isExpanded = expandedIndices.has(index)
                    const confidenceValue = watch(`references.${index}.attribution_confidence`)

                    return (
                        <div key={field.id} className="relative group border rounded-lg bg-card hover:bg-muted/30 transition-colors">
                            {/* Main row */}
                            <div className="p-3 flex gap-2 items-start">
                                <div className="grid grid-cols-12 gap-2 flex-1">
                                    <div className="col-span-3 space-y-1">
                                        <label className="text-[10px] uppercase text-muted-foreground font-semibold">Catalog</label>
                                        <Input {...register(`references.${index}.catalog`)} placeholder="e.g. RIC, RPC, RRC" className="h-8 text-sm" />
                                    </div>
                                    <div className="col-span-2 space-y-1">
                                        <label className="text-[10px] uppercase text-muted-foreground font-semibold">Vol</label>
                                        <Input {...register(`references.${index}.volume`)} placeholder="e.g. II, I" className="h-8 text-sm" />
                                    </div>
                                    <div className="col-span-3 space-y-1">
                                        <label className="text-[10px] uppercase text-muted-foreground font-semibold">Number</label>
                                        <Input {...register(`references.${index}.number`)} placeholder="e.g. 756, 44/5" className="h-8 text-sm" />
                                    </div>
                                    <div className="col-span-4 space-y-1">
                                        <label className="text-[10px] uppercase text-muted-foreground font-semibold">Notes</label>
                                        <Input {...register(`references.${index}.notes`)} placeholder="Page, plate, etc." className="h-8 text-sm" />
                                    </div>
                                </div>
                                <div className="flex items-center gap-1 mt-5">
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-muted-foreground"
                                        onClick={() => toggleExpanded(index)}
                                        title={isExpanded ? "Hide advanced options" : "Show advanced options"}
                                    >
                                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                    </Button>
                                    <Button type="button" variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" onClick={() => remove(index)}>
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>

                            {/* Expanded advanced options */}
                            <div className={cn(
                                "overflow-hidden transition-all duration-200",
                                isExpanded ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
                            )}>
                                <div className="px-3 pb-3 pt-0 border-t border-dashed space-y-3">
                                    <div className="grid grid-cols-12 gap-2 pt-3">
                                        <div className="col-span-3 space-y-1">
                                            <label className="text-[10px] uppercase text-muted-foreground font-semibold">Confidence</label>
                                            <Select
                                                value={confidenceValue || ""}
                                                onValueChange={(val) => setValue(`references.${index}.attribution_confidence`, val as "certain" | "probable" | "possible" | "tentative" | null)}
                                            >
                                                <SelectTrigger className="h-8 text-sm">
                                                    <SelectValue placeholder="Select..." />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {ATTRIBUTION_CONFIDENCE_OPTIONS.map((opt) => (
                                                        <SelectItem key={opt.value} value={opt.value}>
                                                            {opt.label}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="col-span-3 space-y-1">
                                            <label className="text-[10px] uppercase text-muted-foreground font-semibold">Rarity</label>
                                            <Input
                                                {...register(`references.${index}.catalog_rarity_note`)}
                                                placeholder="e.g. R2, Very Rare"
                                                className="h-8 text-sm"
                                            />
                                        </div>
                                        <div className="col-span-3 space-y-1">
                                            <label className="text-[10px] uppercase text-muted-foreground font-semibold">Page Ref</label>
                                            <Input
                                                {...register(`references.${index}.page_reference`)}
                                                placeholder="e.g. p. 234, pl. XV.7"
                                                className="h-8 text-sm"
                                            />
                                        </div>
                                        <div className="col-span-3 space-y-1">
                                            <label className="text-[10px] uppercase text-muted-foreground font-semibold">Variant</label>
                                            <Input
                                                {...register(`references.${index}.variant_note`)}
                                                placeholder="e.g. var. b with AVGVSTI"
                                                className="h-8 text-sm"
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-[10px] uppercase text-muted-foreground font-semibold">Disagreement Note</label>
                                        <Textarea
                                            {...register(`references.${index}.disagreement_note`)}
                                            placeholder="e.g. RIC attributes to Nero, but legend style suggests Vespasian"
                                            className="text-sm min-h-[60px] resize-none"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
