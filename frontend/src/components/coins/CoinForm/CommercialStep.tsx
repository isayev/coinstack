
import { UseFormReturn } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { CoinFormData } from "./schema"
import { GradingState, GradeService } from "@/domain/schemas"
import { ProvenanceListEditor } from "./ProvenanceListEditor"

interface CommercialStepProps {
    form: UseFormReturn<CoinFormData>
}

export function CommercialStep({ form }: CommercialStepProps) {
    const { register, watch, setValue } = form
    const gradingState = watch("grading.grading_state")
    const gradeService = watch("grading.service")

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardContent className="p-0 grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Acquisition</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Price Paid</label>
                            <Input
                                type="number"
                                step="0.01"
                                {...register("acquisition.price", {
                                    valueAsNumber: true,
                                    setValueAs: (v) => v === "" ? null : parseFloat(v)
                                })}
                                className="h-11 font-mono"
                            />
                            {form.formState.errors.acquisition?.price && (
                                <p className="text-destructive text-sm font-bold mt-1">{form.formState.errors.acquisition.price.message}</p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Currency</label>
                            <Input {...register("acquisition.currency")} placeholder="USD" className="h-11" />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-semibold">Source / Dealer</label>
                        <Input {...register("acquisition.source")} placeholder="Heritage, CNG, etc." className="h-11" />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-blue-500 underline flex items-center gap-2">
                            Lot URL
                        </label>
                        <Input {...register("acquisition.url")} placeholder="https://..." className="h-11" />
                    </div>
                </div>

                <div className="space-y-6">
                    <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Condition</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Grading State</label>
                            <Select value={gradingState} onValueChange={(v) => setValue("grading.grading_state", v as GradingState)}>
                                <SelectTrigger className="h-11"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="raw">Raw (In Flip)</SelectItem>
                                    <SelectItem value="slabbed">Slabbed (NGC/PCGS)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Grade *</label>
                            <Input {...register("grading.grade")} placeholder="Choice XF" className="h-11" />
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Service</label>
                            <Select value={gradeService || "none"} onValueChange={(v) => setValue("grading.service", v === "none" ? null : v as GradeService)}>
                                <SelectTrigger className="h-11"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="none">None</SelectItem>
                                    <SelectItem value="ngc">NGC</SelectItem>
                                    <SelectItem value="pcgs">PCGS</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold">Certification #</label>
                            <Input {...register("grading.certification_number")} className="h-11 font-mono" />
                        </div>
                    </div>
                    {(gradeService === "ngc" || gradeService === "pcgs") && (
                        <div className="grid grid-cols-2 gap-4 pt-2">
                            <div className="space-y-2">
                                <label className="text-sm font-semibold">Strike (1–5)</label>
                                <Select
                                    value={form.watch("grading.strike") ?? "__none__"}
                                    onValueChange={(v) => setValue("grading.strike", v === "__none__" ? null : (v as "1" | "2" | "3" | "4" | "5"))}
                                >
                                    <SelectTrigger className="h-11"><SelectValue placeholder="—" /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="__none__">—</SelectItem>
                                        {['1', '2', '3', '4', '5'].map((n) => (
                                            <SelectItem key={n} value={n}>{n}/5</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-muted-foreground">NGC/PCGS strike quality</p>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-semibold">Surface (1–5)</label>
                                <Select
                                    value={form.watch("grading.surface") ?? "__none__"}
                                    onValueChange={(v) => setValue("grading.surface", v === "__none__" ? null : (v as "1" | "2" | "3" | "4" | "5"))}
                                >
                                    <SelectTrigger className="h-11"><SelectValue placeholder="—" /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="__none__">—</SelectItem>
                                        {['1', '2', '3', '4', '5'].map((n) => (
                                            <SelectItem key={n} value={n}>{n}/5</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-muted-foreground">NGC/PCGS surface quality</p>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>

            <div className="pt-6 border-t">
                <ProvenanceListEditor form={form} />
            </div>
        </Card>
    )
}
