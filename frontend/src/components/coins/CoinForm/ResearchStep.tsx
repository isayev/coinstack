
import { useState } from "react"
import { UseFormReturn, Controller } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

import { ReferenceSuggest } from "../ReferenceSuggest"
import { DieLinker } from "../DieLinker"
import { MonogramPicker } from "../MonogramPicker"
import { CoinFormData } from "./schema"
import { ReferenceListEditor } from "./ReferenceListEditor"

interface ResearchStepProps {
    form: UseFormReturn<CoinFormData>
    onReferenceSelect: (s: any) => void
    coinContext: any
}

export function ResearchStep({
    form,
    onReferenceSelect,
    coinContext
}: ResearchStepProps) {
    const { register, control, watch } = form
    const [lookupQuery, setLookupQuery] = useState("")

    // Watch for die IDs to pass to DieLinker
    const obverseDieId = watch("die_info.obverse_die_id")
    const reverseDieId = watch("die_info.reverse_die_id")

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardContent className="p-0 space-y-8">
                <div className="space-y-4">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Catalog References</h3>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Primary Reference (ID Lookup)</label>
                            <ReferenceSuggest
                                value={lookupQuery}
                                onChange={setLookupQuery}
                                onSelectSuggestion={(s) => {
                                    onReferenceSelect(s)
                                    // Optional: clear query after selection? 
                                    // setLookupQuery("") 
                                }}
                                coinContext={coinContext}
                                placeholder="Type to search OCRE / RPC / Crawford..."
                            />
                            <p className="text-xs text-muted-foreground italic">
                                Search by catalog ID to auto-populate form.
                            </p>
                        </div>

                        <div className="p-4 bg-muted/20 border rounded-lg">
                            <ReferenceListEditor form={form} />
                        </div>
                    </div>
                </div>

                <div className="space-y-4 pt-6 border-t">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Die Identification</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Obverse Die ID</label>
                            <Input {...register("die_info.obverse_die_id")} placeholder="O-Vesp-71-A" className="h-11 font-mono" />
                            <DieLinker dieId={obverseDieId || ""} side="obverse" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Reverse Die ID</label>
                            <Input {...register("die_info.reverse_die_id")} placeholder="R-Pax-04" className="h-11 font-mono" />
                            <DieLinker dieId={reverseDieId || ""} side="reverse" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Die State</label>
                            <Input {...register("die_state")} placeholder="e.g. Early, Clashed, Worn" className="h-11 shadow-sm" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Die Match Notes</label>
                            <Input {...register("die_match_notes")} placeholder="e.g. Matches specimen in BMC 42" className="h-11 shadow-sm" />
                        </div>
                    </div>
                </div>

                <div className="space-y-4 pt-6 border-t">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Advanced Attributes</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Rarity Rating</label>
                            {/* Reverting to Input temporarily to debug visibility */}
                            <Input
                                {...register("rarity")}
                                placeholder="e.g. R, R2, Unique (Enter code or text)"
                                className="h-11"
                            />
                            <p className="text-xs text-muted-foreground">Valid codes: c, s, r1-r5, u. Or leave empty.</p>
                            {/* 
                            <Select value={rarity || "__none__"} onValueChange={(v) => setValue("rarity", v === "__none__" ? null : v as any)}>
                                <SelectTrigger className="h-11">
                                    <SelectValue placeholder="Select Rarity" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="__none__">None / Unspecified</SelectItem>
                                    <SelectItem value="c">Common (C)</SelectItem>
                                    <SelectItem value="s">Scarce (S)</SelectItem>
                                    <SelectItem value="r1">Rare (R1)</SelectItem>
                                    <SelectItem value="r2">Very Rare (R2)</SelectItem>
                                    <SelectItem value="r3">Extremely Rare (R3)</SelectItem>
                                    <SelectItem value="u">Unique (U)</SelectItem>
                                </SelectContent>
                            </Select> 
                            */}
                            {form.formState.errors.rarity && (
                                <p className="text-destructive text-sm font-bold mt-1">{form.formState.errors.rarity.message}</p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Style Notes</label>
                            <Input {...register("style_notes")} placeholder="e.g. Fine Style, Portrait A" className="h-11" />
                        </div>
                        <div className="md:col-span-2 space-y-2">
                            <label className="text-sm font-semibold">Toning</label>
                            <Input {...register("toning_description")} placeholder="e.g. Cabinet toning with iridescence" className="h-11" />
                        </div>
                    </div>
                </div>

                <div className="space-y-4 pt-6 border-t">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Monograms</h3>
                    <Controller
                        control={control}
                        name="monograms"
                        render={({ field }) => (
                            <MonogramPicker value={field.value || []} onChange={field.onChange} />
                        )}
                    />
                </div>

                <div className="space-y-4 pt-6 border-t">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Archaeological Data</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Find Spot</label>
                            <Input {...register("find_data.find_spot")} placeholder="Tetbury Hoard" className="h-11" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Find Date</label>
                            <Input type="date" {...register("find_data.find_date")} className="h-11" />
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
