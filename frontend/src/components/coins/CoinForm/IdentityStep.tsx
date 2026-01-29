
import { useState } from "react"
import { UseFormReturn, Controller } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { VocabAutocomplete } from "../VocabAutocomplete"
import { ReferenceSuggest } from "../ReferenceSuggest"
import { CoinFormData } from "./schema"
import { Category, IssueStatus } from "@/domain/schemas"
import { cn } from "@/lib/utils"

interface IdentityStepProps {
    form: UseFormReturn<CoinFormData>
    onReferenceSelect: (s: any) => void
    tentativeFields?: Set<string>
}

export function IdentityStep({ form, onReferenceSelect, tentativeFields }: IdentityStepProps) {
    const { register, control, watch, setValue } = form
    const [lookupQuery, setLookupQuery] = useState("")
    const category = watch("category")
    const issueStatus = watch("issue_status")
    const issuer = watch("attribution.issuer")
    const mint = watch("attribution.mint")

    const isTentative = (field: string) => tentativeFields?.has(field)
    const tentativeClass = "input-tentative"

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardContent className="p-0 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                    <div className="space-y-2">
                        <label htmlFor="category-select" className="text-sm font-semibold">Category *</label>
                        <Select value={category} onValueChange={(v) => setValue("category", v as Category)}>
                            <SelectTrigger id="category-select" className="h-11"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="roman_imperial">Roman Imperial</SelectItem>
                                <SelectItem value="roman_republic">Roman Republic</SelectItem>
                                <SelectItem value="roman_provincial">Roman Provincial</SelectItem>
                                <SelectItem value="greek">Greek</SelectItem>
                                <SelectItem value="byzantine">Byzantine</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-semibold">Series</label>
                        <Input {...register("series")} placeholder="e.g. Severan Dynasty" className="h-11" />
                    </div>

                    <div className="space-y-2 p-4 bg-muted/20 border rounded-lg">
                        <label className="text-sm font-semibold flex items-center gap-2">
                            Quick Lookup (Populate)
                        </label>
                        <ReferenceSuggest
                            value={lookupQuery}
                            onChange={setLookupQuery}
                            onSelectSuggestion={(s) => {
                                onReferenceSelect(s)
                            }}
                            coinContext={issuer || mint ? { ruler: issuer ?? undefined, mint: mint ?? undefined } : undefined}
                            placeholder="Type catalog ID (e.g. RIC III 712, RPC I 4374)..."
                        />
                        <p className="text-xs text-muted-foreground italic">
                            Select a match to auto-fill Issuer, Mint, Date, and Metal.
                        </p>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="issue-status-select" className="text-sm font-semibold">Issue Status</label>
                        <Select value={issueStatus || "official"} onValueChange={(v) => setValue("issue_status", v as IssueStatus)}>
                            <SelectTrigger id="issue-status-select" className="h-11"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="official">Official Mint Product</SelectItem>
                                <SelectItem value="fourree">Fourrée (Ancient Forgery)</SelectItem>
                                <SelectItem value="imitation">Contemporary Imitation</SelectItem>
                                <SelectItem value="barbarous">Barbarous Radiate</SelectItem>
                                <SelectItem value="modern_fake">Modern Counterfeit</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="space-y-2">
                        <label htmlFor="issuer-autocomplete" className="text-sm font-semibold flex justify-between">
                            Issuer / Authority *
                            {isTentative("attribution.issuer") && <span className="text-xs text-yellow-600 font-normal animate-pulse">Auto-Populated</span>}
                        </label>
                        <Controller
                            control={control}
                            name="attribution.issuer_id"
                            render={({ field }) => (
                                <VocabAutocomplete
                                    vocabType="issuer"
                                    value={field.value ?? null}
                                    displayValue={issuer ?? undefined}
                                    onChange={(id, display) => {
                                        field.onChange(id)
                                        setValue("attribution.issuer", display, { shouldDirty: true, shouldTouch: true, shouldValidate: true })
                                    }}
                                    className={cn("h-11", isTentative("attribution.issuer") && tentativeClass)}
                                />
                            )}
                        />
                        {form.formState.errors.attribution?.issuer && (
                            <p className="text-destructive text-sm font-bold mt-1">Issuer is required</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="denomination" className="text-sm font-semibold">Denomination</label>
                        <Input
                            id="denomination"
                            {...register("denomination")}
                            placeholder="e.g. Denarius, Aureus, Sestertius, Follis"
                            className="h-11 bg-background"
                        />
                        <p className="text-xs text-muted-foreground">Coin type (official mint product).</p>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="portrait-subject" className="text-sm font-semibold">Portrait Subject</label>
                        <Input
                            id="portrait-subject"
                            {...register("portrait_subject")}
                            placeholder="Person/deity on obverse (e.g. Faustina the Elder, DIVVS ANTONINVS)"
                            className="h-11 bg-background"
                        />
                        <p className="text-xs text-muted-foreground">When the obverse portrait is not the issuing ruler (empress, deified predecessor, deity).</p>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="mint-autocomplete" className="text-sm font-semibold flex justify-between">
                            Mint
                            {isTentative("attribution.mint") && <span className="text-xs text-yellow-600 font-normal animate-pulse">Auto-Populated</span>}
                        </label>
                        <Controller
                            control={control}
                            name="attribution.mint_id"
                            render={({ field }) => (
                                <VocabAutocomplete
                                    vocabType="mint"
                                    value={field.value ?? null}
                                    displayValue={mint ?? undefined}
                                    onChange={(id, display) => {
                                        field.onChange(id)
                                        setValue("attribution.mint", display, { shouldDirty: true, shouldTouch: true, shouldValidate: true })
                                    }}
                                    className={cn("h-11", isTentative("attribution.mint") && tentativeClass)}
                                />
                            )}
                        />
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                        <div className="space-y-1">
                            <label className="text-xs font-semibold">Mintmark</label>
                            <Input {...register("mintmark")} placeholder="CONOB" className="h-9 text-xs" />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-semibold">Officina</label>
                            <Input {...register("officina")} placeholder="A" className="h-9 text-xs" />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs font-semibold">Field Marks</label>
                            <Input {...register("field_marks")} placeholder="Star" className="h-9 text-xs" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label htmlFor="year-start-input" className="text-sm font-semibold flex justify-between">
                                Start
                                {isTentative("attribution.year_start") && <span className="text-xs text-yellow-600 animate-pulse">●</span>}
                            </label>
                            <Input
                                id="year-start-input"
                                type="number"
                                {...register("attribution.year_start", {
                                    valueAsNumber: true,
                                    setValueAs: (v) => v === "" ? null : parseInt(v, 10)
                                })}
                                placeholder="-27"
                                className={cn("h-11", isTentative("attribution.year_start") && tentativeClass)}
                            />
                            {form.formState.errors.attribution?.year_start && (
                                <p className="text-destructive text-sm font-bold mt-1">{form.formState.errors.attribution.year_start.message}</p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <label htmlFor="year-end-input" className="text-sm font-semibold flex justify-between">
                                End
                                {isTentative("attribution.year_end") && <span className="text-xs text-yellow-600 animate-pulse">●</span>}
                            </label>
                            <Input
                                id="year-end-input"
                                type="number"
                                {...register("attribution.year_end", {
                                    valueAsNumber: true,
                                    setValueAs: (v) => v === "" ? null : parseInt(v, 10)
                                })}
                                placeholder="14"
                                className={cn("h-11", isTentative("attribution.year_end") && tentativeClass)}
                            />
                            {form.formState.errors.attribution?.year_end && (
                                <p className="text-destructive text-sm font-bold mt-1">{form.formState.errors.attribution.year_end.message}</p>
                            )}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
