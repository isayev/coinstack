import { UseFormReturn } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { LegendInput } from "../LegendInput"
import { CoinFormData } from "./schema"
import { cn } from "@/lib/utils"

interface DesignStepProps {
    form: UseFormReturn<CoinFormData>
    tentativeFields?: Set<string>
}

export function DesignStep({ form, tentativeFields }: DesignStepProps) {
    const { register, watch, setValue } = form
    const design = watch("design")

    const isTentative = (field: string) => tentativeFields?.has(field)
    const tentativeClass = "input-tentative"

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardContent className="p-0 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                        <div className={cn("rounded-md transition-all", isTentative("design.obverse_legend") && "ring-2 ring-yellow-400/50 bg-yellow-50/10")}>
                            <LegendInput
                                label="Obverse Legend"
                                value={design?.obverse_legend || ""}
                                side="obverse"
                                onChange={(v) => setValue("design.obverse_legend", v)}
                                placeholder="IMP CAES DOMIT AVG..."
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold flex justify-between">
                                Obverse Description
                                {isTentative("design.obverse_description") && <span className="text-xs text-yellow-600 animate-pulse">Auto-Populated</span>}
                            </label>
                            <Input
                                {...register("design.obverse_description")}
                                placeholder="Laureate head right"
                                className={cn(isTentative("design.obverse_description") && tentativeClass)}
                            />
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div className={cn("rounded-md transition-all", isTentative("design.reverse_legend") && "ring-2 ring-yellow-400/50 bg-yellow-50/10")}>
                            <LegendInput
                                label="Reverse Legend"
                                value={design?.reverse_legend || ""}
                                side="reverse"
                                onChange={(v) => setValue("design.reverse_legend", v)}
                                placeholder="MONETA AVGVSTI"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold flex justify-between">
                                Reverse Description
                                {isTentative("design.reverse_description") && <span className="text-xs text-yellow-600 animate-pulse">Auto-Populated</span>}
                            </label>
                            <Input
                                {...register("design.reverse_description")}
                                placeholder="Moneta standing left holding scales"
                                className={cn(isTentative("design.reverse_description") && tentativeClass)}
                            />
                        </div>
                    </div>
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-semibold">Exergue</label>
                    <Input {...register("design.exergue")} placeholder="CONOB" className="font-serif w-full" />
                </div>
            </CardContent>
        </Card>
    )
}
