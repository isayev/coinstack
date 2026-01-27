import { UseFormReturn } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Info } from "lucide-react"
import { CoinFormData } from "./schema"
import { Metal } from "@/domain/schemas"
import { cn } from "@/lib/utils"

interface PhysicalStepProps {
    form: UseFormReturn<CoinFormData>
    tentativeFields?: Set<string>
}

export function PhysicalStep({ form, tentativeFields }: PhysicalStepProps) {
    const { register, watch, setValue } = form
    const metal = watch("metal")

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
                            <label className="text-sm font-semibold">Weight (g) *</label>
                            <Input
                                type="number"
                                step="0.01"
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
            </CardContent>
        </Card>
    )
}
