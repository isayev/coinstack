import { useState } from "react"
import { UseFormReturn, Controller } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

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
    const { register, control, watch, setValue } = form
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

                    {/* Phase 1: Die Study Enhancements */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-dashed">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Obverse Die State</label>
                            <Select
                                value={watch("die_study.obverse_die_state") || ""}
                                onValueChange={(v) => setValue("die_study.obverse_die_state", v || null)}
                            >
                                <SelectTrigger className="h-10">
                                    <SelectValue placeholder="Select state" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="fresh">Fresh</SelectItem>
                                    <SelectItem value="early">Early</SelectItem>
                                    <SelectItem value="middle">Middle</SelectItem>
                                    <SelectItem value="late">Late</SelectItem>
                                    <SelectItem value="worn">Worn</SelectItem>
                                    <SelectItem value="broken">Broken</SelectItem>
                                    <SelectItem value="repaired">Repaired</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Reverse Die State</label>
                            <Select
                                value={watch("die_study.reverse_die_state") || ""}
                                onValueChange={(v) => setValue("die_study.reverse_die_state", v || null)}
                            >
                                <SelectTrigger className="h-10">
                                    <SelectValue placeholder="Select state" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="fresh">Fresh</SelectItem>
                                    <SelectItem value="early">Early</SelectItem>
                                    <SelectItem value="middle">Middle</SelectItem>
                                    <SelectItem value="late">Late</SelectItem>
                                    <SelectItem value="worn">Worn</SelectItem>
                                    <SelectItem value="broken">Broken</SelectItem>
                                    <SelectItem value="repaired">Repaired</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Die Break Description</label>
                            <Input
                                {...register("die_study.die_break_description")}
                                placeholder="e.g., Cud at 2:00"
                                className="h-10"
                            />
                        </div>
                    </div>
                </div>

                {/* Phase 1: Chronology Enhancements */}
                <div className="space-y-4 pt-6 border-t">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Chronology</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Date Period Notation</label>
                            <Input
                                {...register("chronology.date_period_notation")}
                                placeholder="e.g., c. 150-100 BC"
                                className="h-11"
                            />
                            <p className="text-xs text-muted-foreground">Human-readable date expression</p>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Emission Phase</label>
                            <Input
                                {...register("chronology.emission_phase")}
                                placeholder="e.g., First Issue, Reform Coinage"
                                className="h-11"
                            />
                        </div>
                    </div>
                </div>

                {/* Phase 1: Attribution Enhancements */}
                <div className="space-y-4 pt-6 border-t">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Attribution Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Secondary Authority</label>
                            <Input
                                {...register("secondary_authority.name")}
                                placeholder="Magistrate, Satrap, etc."
                                className="h-11"
                            />
                            <p className="text-xs text-muted-foreground">Greek magistrates, provincial governors</p>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Authority Type</label>
                            <Select
                                value={watch("secondary_authority.authority_type") || ""}
                                onValueChange={(v) => setValue("secondary_authority.authority_type", v || null)}
                            >
                                <SelectTrigger className="h-11">
                                    <SelectValue placeholder="Select type" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="magistrate">Magistrate</SelectItem>
                                    <SelectItem value="satrap">Satrap</SelectItem>
                                    <SelectItem value="dynast">Dynast</SelectItem>
                                    <SelectItem value="strategos">Strategos</SelectItem>
                                    <SelectItem value="archon">Archon</SelectItem>
                                    <SelectItem value="epistates">Epistates</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Moneyer (Gens)</label>
                            <Input
                                {...register("moneyer_gens")}
                                placeholder="e.g., Calpurnius"
                                className="h-11"
                            />
                            <p className="text-xs text-muted-foreground">Republican moneyer family</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Co-Ruler</label>
                            <Input
                                {...register("co_ruler.name")}
                                placeholder="Byzantine/Imperial co-ruler"
                                className="h-11"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Portrait Relationship</label>
                            <Select
                                value={watch("co_ruler.portrait_relationship") || ""}
                                onValueChange={(v) => setValue("co_ruler.portrait_relationship", v || null)}
                            >
                                <SelectTrigger className="h-11">
                                    <SelectValue placeholder="Select relationship" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="self">Self</SelectItem>
                                    <SelectItem value="consort">Consort</SelectItem>
                                    <SelectItem value="heir">Heir</SelectItem>
                                    <SelectItem value="parent">Parent</SelectItem>
                                    <SelectItem value="predecessor">Predecessor</SelectItem>
                                    <SelectItem value="commemorative">Commemorative</SelectItem>
                                    <SelectItem value="divus">Divus</SelectItem>
                                    <SelectItem value="diva">Diva</SelectItem>
                                </SelectContent>
                            </Select>
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
