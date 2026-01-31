import { UseFormReturn } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Info, ChevronDown, Wrench, Focus, Layers } from "lucide-react"
import { CoinFormData } from "./schema"
import { Metal } from "@/domain/schemas"
import { cn } from "@/lib/utils"
import { useState } from "react"

interface PhysicalStepProps {
    form: UseFormReturn<CoinFormData>
    tentativeFields?: Set<string>
}

export function PhysicalStep({ form, tentativeFields }: PhysicalStepProps) {
    const { register, watch, setValue } = form
    const metal = watch("metal")
    const [advancedOpen, setAdvancedOpen] = useState(false)
    const [treatmentsOpen, setTreatmentsOpen] = useState(false)

    const isTentative = (field: string) => tentativeFields?.has(field)
    const tentativeClass = "input-tentative"

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardContent className="p-0 grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-semibold flex justify-between">
                            Metal *
                            {isTentative("metal") && <span className="text-xs text-yellow-600 animate-pulse">Auto-Populated</span>}
                        </label>
                        <Select value={metal} onValueChange={(v) => setValue("metal", v as Metal)}>
                            <SelectTrigger className={cn("h-11", isTentative("metal") && tentativeClass)}>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="gold">Gold (AV)</SelectItem>
                                <SelectItem value="silver">Silver (AR)</SelectItem>
                                <SelectItem value="bronze">Bronze (AE)</SelectItem>
                                <SelectItem value="billon">Billon (BI)</SelectItem>
                                <SelectItem value="orichalcum">Orichalcum</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Weight (g)</label>
                            <Input
                                type="number"
                                step="0.01"
                                placeholder="Optional (e.g. slabbed)"
                                {...register("dimensions.weight_g", {
                                    valueAsNumber: true,
                                    setValueAs: (v) => v === "" ? null : parseFloat(v)
                                })}
                                className="h-11 font-mono"
                            />
                            {form.formState.errors.dimensions?.weight_g && (
                                <p className="text-destructive text-sm font-bold mt-1">{form.formState.errors.dimensions.weight_g.message}</p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Diameter (mm) *</label>
                            <Input
                                type="number"
                                step="0.1"
                                {...register("dimensions.diameter_mm", {
                                    valueAsNumber: true,
                                    setValueAs: (v) => v === "" ? null : parseFloat(v)
                                })}
                                className="h-11 font-mono"
                            />
                            {form.formState.errors.dimensions?.diameter_mm && (
                                <p className="text-destructive text-sm font-bold mt-1">{form.formState.errors.dimensions.diameter_mm.message}</p>
                            )}
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-semibold flex items-center gap-2">
                            Specific Gravity
                            <Info className="h-3 w-3 text-muted-foreground" />
                        </label>
                        <Input
                            type="number"
                            step="0.01"
                            {...register("dimensions.specific_gravity", {
                                valueAsNumber: true,
                                setValueAs: (v) => v === "" ? null : parseFloat(v)
                            })}
                            placeholder="e.g. 10.5"
                            className="h-11 font-mono"
                        />
                        {form.formState.errors.dimensions?.specific_gravity && (
                            <p className="text-destructive text-sm font-bold mt-1">{form.formState.errors.dimensions.specific_gravity.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold">Die Axis (0-12h)</label>
                        <Input
                            type="number"
                            min="0"
                            max="12"
                            {...register("dimensions.die_axis", {
                                valueAsNumber: true,
                                setValueAs: (v) => v === "" ? null : parseInt(v, 10)
                            })}
                            placeholder="6"
                            className="h-11 font-mono"
                        />
                        {form.formState.errors.dimensions?.die_axis && (
                            <p className="text-destructive text-sm font-bold mt-1">{form.formState.errors.dimensions.die_axis.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold">Edge Type</label>
                        <Select onValueChange={(v) => setValue("edge_type", v)} defaultValue={watch("edge_type") || ""}>
                            <SelectTrigger className="h-11">
                                <SelectValue placeholder="Select Edge Type" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="plain">Plain</SelectItem>
                                <SelectItem value="reeded">Reeded</SelectItem>
                                <SelectItem value="lettered">Lettered</SelectItem>
                                <SelectItem value="decorated">Decorated</SelectItem>
                                <SelectItem value="serrated">Serrated</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold">Edge Inscription</label>
                        <Input
                            {...register("edge_inscription")}
                            placeholder="e.g. DECVS ET TVTAMEN"
                            className="h-11 font-serif"
                        />
                    </div>
                </div>

                <div className="col-span-1 md:col-span-2 pt-6 border-t">
                    <label className="text-sm font-semibold">Conservation / Cleaning Notes</label>
                    <textarea
                        {...register("conservation_notes")}
                        className="w-full min-h-[80px] mt-2 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        placeholder="Details on cleaning, restoration, or conservation status..."
                    />
                </div>

                {/* Phase 1: Advanced Physical Properties */}
                <div className="col-span-1 md:col-span-2 pt-6 border-t">
                    <Collapsible open={advancedOpen} onOpenChange={setAdvancedOpen}>
                        <CollapsibleTrigger className="flex items-center gap-2 text-sm font-semibold hover:text-primary transition-colors w-full justify-between">
                            <span className="flex items-center gap-2">
                                <Focus className="h-4 w-4" />
                                Advanced Physical Properties
                            </span>
                            <ChevronDown className={cn("h-4 w-4 transition-transform", advancedOpen && "rotate-180")} />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="pt-4 space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Weight Standard</label>
                                    <Select
                                        value={watch("physical_enhancements.weight_standard") || ""}
                                        onValueChange={(v) => setValue("physical_enhancements.weight_standard", v || null)}
                                    >
                                        <SelectTrigger className="h-10">
                                            <SelectValue placeholder="Select standard" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="attic">Attic</SelectItem>
                                            <SelectItem value="aeginetan">Aeginetan</SelectItem>
                                            <SelectItem value="corinthian">Corinthian</SelectItem>
                                            <SelectItem value="phoenician">Phoenician</SelectItem>
                                            <SelectItem value="denarius_early">Denarius (Early)</SelectItem>
                                            <SelectItem value="denarius_reformed">Denarius (Reformed)</SelectItem>
                                            <SelectItem value="antoninianus">Antoninianus</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Expected Weight (g)</label>
                                    <Input
                                        type="number"
                                        step="0.01"
                                        {...register("physical_enhancements.expected_weight_g", {
                                            valueAsNumber: true,
                                            setValueAs: (v) => v === "" ? null : parseFloat(v)
                                        })}
                                        placeholder="Standard weight for type"
                                        className="h-10 font-mono"
                                    />
                                    <p className="text-xs text-muted-foreground">Theoretical weight for comparison</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Flan Shape</label>
                                    <Select
                                        value={watch("physical_enhancements.flan_shape") || ""}
                                        onValueChange={(v) => setValue("physical_enhancements.flan_shape", v || null)}
                                    >
                                        <SelectTrigger className="h-10">
                                            <SelectValue placeholder="Select shape" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="round">Round</SelectItem>
                                            <SelectItem value="irregular">Irregular</SelectItem>
                                            <SelectItem value="oval">Oval</SelectItem>
                                            <SelectItem value="square">Square</SelectItem>
                                            <SelectItem value="scyphate">Scyphate (cup-shaped)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Flan Type</label>
                                    <Select
                                        value={watch("physical_enhancements.flan_type") || ""}
                                        onValueChange={(v) => setValue("physical_enhancements.flan_type", v || null)}
                                    >
                                        <SelectTrigger className="h-10">
                                            <SelectValue placeholder="Select type" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="cast">Cast</SelectItem>
                                            <SelectItem value="struck">Struck</SelectItem>
                                            <SelectItem value="cut_from_bar">Cut from Bar</SelectItem>
                                            <SelectItem value="hammered">Hammered</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Centering</label>
                                    <Select
                                        value={watch("centering_info.centering") || ""}
                                        onValueChange={(v) => setValue("centering_info.centering", v || null)}
                                    >
                                        <SelectTrigger className="h-10">
                                            <SelectValue placeholder="Strike centering" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="well-centered">Well Centered</SelectItem>
                                            <SelectItem value="slightly_off">Slightly Off</SelectItem>
                                            <SelectItem value="off_center">Off Center</SelectItem>
                                            <SelectItem value="significantly_off">Significantly Off</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Centering Notes</label>
                                    <Input
                                        {...register("centering_info.centering_notes")}
                                        placeholder="e.g., Off-center to 7 o'clock"
                                        className="h-10"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Flan Notes</label>
                                <Input
                                    {...register("physical_enhancements.flan_notes")}
                                    placeholder="Edge cracks, planchet flaws, etc."
                                    className="h-10"
                                />
                            </div>
                        </CollapsibleContent>
                    </Collapsible>
                </div>

                {/* Phase 1: Tooling & Repairs */}
                <div className="col-span-1 md:col-span-2 pt-4 border-t">
                    <Collapsible open={treatmentsOpen} onOpenChange={setTreatmentsOpen}>
                        <CollapsibleTrigger className="flex items-center gap-2 text-sm font-semibold hover:text-primary transition-colors w-full justify-between">
                            <span className="flex items-center gap-2">
                                <Wrench className="h-4 w-4" />
                                Tooling, Repairs & Secondary Treatments
                            </span>
                            <ChevronDown className={cn("h-4 w-4 transition-transform", treatmentsOpen && "rotate-180")} />
                        </CollapsibleTrigger>
                        <CollapsibleContent className="pt-4 space-y-4">
                            {/* Tooling Section */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Tooling Extent</label>
                                    <Select
                                        value={watch("tooling_repairs.tooling_extent") || ""}
                                        onValueChange={(v) => setValue("tooling_repairs.tooling_extent", v || null)}
                                    >
                                        <SelectTrigger className="h-10">
                                            <SelectValue placeholder="Select extent" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="none">None</SelectItem>
                                            <SelectItem value="minor">Minor</SelectItem>
                                            <SelectItem value="moderate">Moderate</SelectItem>
                                            <SelectItem value="significant">Significant</SelectItem>
                                            <SelectItem value="extensive">Extensive</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Tooling Details</label>
                                    <Input
                                        {...register("tooling_repairs.tooling_details")}
                                        placeholder="Describe tooling areas"
                                        className="h-10"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center gap-6">
                                <div className="flex items-center gap-2">
                                    <Checkbox
                                        id="ancient_repair"
                                        checked={watch("tooling_repairs.has_ancient_repair") || false}
                                        onCheckedChange={(checked) => setValue("tooling_repairs.has_ancient_repair", !!checked)}
                                    />
                                    <label htmlFor="ancient_repair" className="text-sm">Has Ancient Repair</label>
                                </div>
                            </div>

                            {watch("tooling_repairs.has_ancient_repair") && (
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Ancient Repairs Description</label>
                                    <Input
                                        {...register("tooling_repairs.ancient_repairs")}
                                        placeholder="e.g., Plug, filled hole"
                                        className="h-10"
                                    />
                                </div>
                            )}

                            {/* Secondary Treatments Section */}
                            <div className="pt-4 border-t space-y-3">
                                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                                    <Layers className="h-4 w-4" />
                                    Secondary Treatments
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="flex items-center gap-2">
                                        <Checkbox
                                            id="is_overstrike"
                                            checked={watch("secondary_treatments_v3.is_overstrike") || false}
                                            onCheckedChange={(checked) => setValue("secondary_treatments_v3.is_overstrike", !!checked)}
                                        />
                                        <label htmlFor="is_overstrike" className="text-sm">Overstrike</label>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Checkbox
                                            id="has_test_cut"
                                            checked={watch("secondary_treatments_v3.has_test_cut") || false}
                                            onCheckedChange={(checked) => setValue("secondary_treatments_v3.has_test_cut", !!checked)}
                                        />
                                        <label htmlFor="has_test_cut" className="text-sm">Test Cut</label>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Checkbox
                                            id="has_bankers_marks"
                                            checked={watch("secondary_treatments_v3.has_bankers_marks") || false}
                                            onCheckedChange={(checked) => setValue("secondary_treatments_v3.has_bankers_marks", !!checked)}
                                        />
                                        <label htmlFor="has_bankers_marks" className="text-sm">Banker's Marks</label>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Checkbox
                                            id="was_mounted"
                                            checked={watch("secondary_treatments_v3.was_mounted") || false}
                                            onCheckedChange={(checked) => setValue("secondary_treatments_v3.was_mounted", !!checked)}
                                        />
                                        <label htmlFor="was_mounted" className="text-sm">Was Mounted</label>
                                    </div>
                                </div>

                                {watch("secondary_treatments_v3.is_overstrike") && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4 border-l-2 border-primary/20">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Undertype Visible</label>
                                            <Input
                                                {...register("secondary_treatments_v3.undertype_visible")}
                                                placeholder="Visible traces of host coin"
                                                className="h-10"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Undertype Attribution</label>
                                            <Input
                                                {...register("secondary_treatments_v3.undertype_attribution")}
                                                placeholder="Attribution of host coin"
                                                className="h-10"
                                            />
                                        </div>
                                    </div>
                                )}

                                {watch("secondary_treatments_v3.has_test_cut") && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-4 border-l-2 border-primary/20">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Test Cut Count</label>
                                            <Input
                                                type="number"
                                                {...register("secondary_treatments_v3.test_cut_count", { valueAsNumber: true })}
                                                placeholder="Number of cuts"
                                                className="h-10"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Test Cut Positions</label>
                                            <Input
                                                {...register("secondary_treatments_v3.test_cut_positions")}
                                                placeholder="e.g., Edge at 3 o'clock"
                                                className="h-10"
                                            />
                                        </div>
                                    </div>
                                )}

                                {watch("secondary_treatments_v3.was_mounted") && (
                                    <div className="pl-4 border-l-2 border-primary/20">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Mount Evidence</label>
                                            <Input
                                                {...register("secondary_treatments_v3.mount_evidence")}
                                                placeholder="Loop removed, bezel marks, etc."
                                                className="h-10"
                                            />
                                        </div>
                                    </div>
                                )}

                                <div className="flex items-center gap-2 pt-2">
                                    <Checkbox
                                        id="has_graffiti"
                                        checked={watch("secondary_treatments_v3.has_graffiti") || false}
                                        onCheckedChange={(checked) => setValue("secondary_treatments_v3.has_graffiti", !!checked)}
                                    />
                                    <label htmlFor="has_graffiti" className="text-sm">Has Ancient Graffiti</label>
                                </div>

                                {watch("secondary_treatments_v3.has_graffiti") && (
                                    <div className="pl-4 border-l-2 border-primary/20">
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium">Graffiti Description</label>
                                            <Input
                                                {...register("secondary_treatments_v3.graffiti_description")}
                                                placeholder="Transcription and location"
                                                className="h-10"
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </CollapsibleContent>
                    </Collapsible>
                </div>
            </CardContent>
        </Card>
    )
}
