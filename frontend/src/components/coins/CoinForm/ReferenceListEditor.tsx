
import { UseFormReturn, useFieldArray } from "react-hook-form"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Trash2, Plus } from "lucide-react"
import { CoinFormData } from "./schema"
import { CatalogReference } from "@/domain/schemas"

interface ReferenceListProps {
    form: UseFormReturn<CoinFormData>
}

export function ReferenceListEditor({ form }: ReferenceListProps) {
    const { control, register } = form
    const { fields, append, remove } = useFieldArray({
        control,
        name: "references"
    })

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
                {fields.map((field, index) => (
                    <div key={field.id} className="relative group border rounded-lg p-3 bg-card hover:bg-muted/30 transition-colors flex gap-2 items-start">
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
                        <Button type="button" variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground mt-5" onClick={() => remove(index)}>
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                ))}
            </div>
        </div>
    )
}
