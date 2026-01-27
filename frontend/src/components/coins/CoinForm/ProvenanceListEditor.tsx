
import { UseFormReturn, useFieldArray } from "react-hook-form"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Trash2, Plus } from "lucide-react"
import { CoinFormData } from "./schema"
import { ProvenanceEvent } from "@/domain/schemas"

interface ProvenanceListProps {
    form: UseFormReturn<CoinFormData>
}

export function ProvenanceListEditor({ form }: ProvenanceListProps) {
    const { control, register } = form
    const { fields, append, remove } = useFieldArray({
        control,
        name: "provenance"
    })

    const addEvent = () => {
        append({
            event_type: "auction",
            auction_house: "",
            event_date: "",
            lot_number: "",
            hammer_price: null,
            currency: "USD"
        } as ProvenanceEvent)
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Provenance History</h3>
                <Button type="button" variant="outline" size="sm" onClick={addEvent} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Add Event
                </Button>
            </div>

            <div className="space-y-3">
                {fields.map((field, index) => (
                    <div key={field.id} className="relative group border rounded-lg p-4 bg-card hover:bg-muted/30 transition-colors">
                        <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                            <Button type="button" variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground" onClick={() => remove(index)}>
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                            {/* Type */}
                            <div className="md:col-span-3 space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground">Type</label>
                                <Select
                                    onValueChange={(v) => form.setValue(`provenance.${index}.event_type`, v)}
                                    defaultValue={field.event_type}
                                >
                                    <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="auction">Auction</SelectItem>
                                        <SelectItem value="dealer">Dealer</SelectItem>
                                        <SelectItem value="collection">Collection</SelectItem>
                                        <SelectItem value="private_sale">Private Sale</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Name / House */}
                            <div className="md:col-span-4 space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground">Name / House</label>
                                <Input
                                    {...register(`provenance.${index}.auction_house`)}
                                    placeholder="e.g. CNG, Glendining"
                                    className="h-9"
                                />
                            </div>

                            {/* Date */}
                            <div className="md:col-span-3 space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground">Date</label>
                                <Input
                                    type="date"
                                    {...register(`provenance.${index}.event_date`)}
                                    className="h-9"
                                />
                            </div>

                            {/* Lot */}
                            <div className="md:col-span-2 space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground">Lot #</label>
                                <Input
                                    {...register(`provenance.${index}.lot_number`)}
                                    className="h-9"
                                />
                            </div>
                        </div>

                        {/* Expanded details for Auction */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 pt-3 border-t border-dashed">
                            <div className="space-y-1">
                                <label className="text-xs text-muted-foreground">Sale Name/Number</label>
                                <Input {...register(`provenance.${index}.sale_number`)} placeholder="e.g. Auc 114" className="h-7 text-xs" />
                            </div>
                            <div className="space-y-1">
                                <label className="text-xs text-muted-foreground">Price</label>
                                <div className="flex gap-1">
                                    <Input
                                        type="number"
                                        step="0.01"
                                        {...register(`provenance.${index}.hammer_price`, { valueAsNumber: true })}
                                        placeholder="Price"
                                        className="h-7 text-xs"
                                    />
                                    <Input
                                        {...register(`provenance.${index}.currency`)}
                                        defaultValue="USD"
                                        className="h-7 w-12 text-xs"
                                    />
                                </div>
                            </div>
                            <div className="col-span-2 space-y-1">
                                <label className="text-xs text-muted-foreground">Notes</label>
                                <Input {...register(`provenance.${index}.notes`)} placeholder="e.g. Ex. Niggeler Collection" className="h-7 text-xs" />
                            </div>
                        </div>
                    </div>
                ))}

                {fields.length === 0 && (
                    <div className="text-center py-6 border-2 border-dashed rounded-lg text-muted-foreground text-sm">
                        No provenance history added.
                    </div>
                )}
            </div>
        </div>
    )
}
