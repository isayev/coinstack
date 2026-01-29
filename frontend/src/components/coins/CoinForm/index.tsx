
import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import {
    Coin
} from "@/domain/schemas"
import { CreateCoinSchema, CoinFormData } from "./schema"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { toast } from "sonner"
import {
    Loader2,
    ChevronRight,
    ChevronLeft,
    Check,
    Scale,
    Palette,
    Microscope,
    Landmark,
    Image as ImageIcon,
    Search,
    AlertCircle
} from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

// Steps
import { IdentityStep } from "./IdentityStep"
import { PhysicalStep } from "./PhysicalStep"
import { DesignStep } from "./DesignStep"
import { ResearchStep } from "./ResearchStep"
import { CommercialStep } from "./CommercialStep"
import { FinalizeStep } from "./FinalizeStep"

// Schema for form values
// Schema imported from ./schema

interface CoinFormProps {
    coin?: Coin;
    onSubmit: (data: CoinFormData) => void;
    isSubmitting?: boolean;
    defaultValues?: Partial<CoinFormData>;
}

// --- Step Definitions ---
const STEPS = [
    { id: 'identity', title: 'Identity', icon: Landmark, description: 'Issuer, Mint & Dates' },
    { id: 'physical', title: 'Physical', icon: Scale, description: 'Measurements & Metal' },
    { id: 'design', title: 'Design', icon: Palette, description: 'Legends & Type' },
    { id: 'research', title: 'Research', icon: Microscope, description: 'Dies & Find Data' },
    { id: 'commercial', title: 'Commercial', icon: Search, description: 'Purchase & Grade' },
    { id: 'final', title: 'Finalize', icon: ImageIcon, description: 'Photos & Notes' },
]

export function CoinForm({ coin, onSubmit, isSubmitting, defaultValues: propDefaultValues }: CoinFormProps) {
    const [currentStep, setCurrentStep] = useState(0)
    const [tentativeFields, setTentativeFields] = useState<Set<string>>(new Set())

    const form = useForm<CoinFormData>({
        resolver: zodResolver(CreateCoinSchema),
        defaultValues: propDefaultValues || {
            category: coin?.category || "roman_imperial",
            metal: coin?.metal || "silver",
            issue_status: coin?.issue_status || "official",
            series: coin?.series || "",
            dimensions: {
                weight_g: coin?.dimensions?.weight_g ?? null,
                diameter_mm: coin?.dimensions?.diameter_mm ?? null,
                die_axis: coin?.dimensions?.die_axis ?? null,
                specific_gravity: coin?.dimensions?.specific_gravity ?? null,
            },
            die_info: {
                obverse_die_id: coin?.die_info?.obverse_die_id || "",
                reverse_die_id: coin?.die_info?.reverse_die_id || "",
            },
            die_state: coin?.die_state || "",
            die_match_notes: coin?.die_match_notes || "",
            find_data: {
                find_spot: coin?.find_data?.find_spot || "",
                find_date: coin?.find_data?.find_date || "",
            },
            attribution: {
                issuer: coin?.attribution.issuer || "",
                issuer_id: coin?.attribution.issuer_id || null,
                mint: coin?.attribution.mint || "",
                mint_id: coin?.attribution.mint_id || null,
                year_start: coin?.attribution.year_start || null,
                year_end: coin?.attribution.year_end || null,
            },
            grading: {
                grading_state: coin?.grading.grading_state || "raw",
                grade: coin?.grading.grade || "",
                service: coin?.grading.service || null,
                certification_number: coin?.grading.certification_number || "",
                strike: coin?.grading.strike || "",
                surface: coin?.grading.surface || "",
            },
            acquisition: coin?.acquisition || {
                price: 0,
                currency: "USD",
                source: "",
                date: "",
                url: null,
            },

            tags: coin?.tags || [],
            images: coin?.images || [],
            rarity: coin?.rarity || null,
            style_notes: coin?.style_notes || "",
            toning_description: coin?.toning_description || "",
            edge_type: coin?.edge_type || "",
            edge_inscription: coin?.edge_inscription || "",
            mintmark: coin?.mintmark || "",
            officina: coin?.officina || "",
            field_marks: coin?.field_marks || "",
            denomination: coin?.denomination ?? "",
            portrait_subject: coin?.portrait_subject ?? "",
            design: coin?.design || {
                obverse_legend: "",
                obverse_description: "",
                reverse_description: "",
                reverse_legend: "",
                exergue: ""
            },
            monograms: coin?.monograms || [],
            references: coin?.references || [],
            storage_location: coin?.storage_location || "",
            personal_notes: coin?.personal_notes || ""
        },
    })

    const { handleSubmit, trigger, setValue, watch, formState } = form
    const attribution = watch("attribution")

    // Warn on exit if dirty
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (formState.isDirty) {
                e.preventDefault()
                e.returnValue = '' // Chrome requires returnValue to be set
            }
        }
        window.addEventListener('beforeunload', handleBeforeUnload)
        return () => window.removeEventListener('beforeunload', handleBeforeUnload)
    }, [formState.isDirty])

    const nextStep = async () => {
        const fields = getFieldsForStep(currentStep)
        const isValid = await trigger(fields as any)

        if (isValid) {
            setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1))
        } else {
            // Log errors for debugging
            console.warn("Step validation failed", form.formState.errors)

            // Show global error alert
            onError(form.formState.errors)
        }
    }

    const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0))

    const progress = ((currentStep + 1) / STEPS.length) * 100

    const handleReferenceSelect = (suggestion: any) => {
        const payload = suggestion.payload
        const newTentative = new Set(tentativeFields)
        const updateField = (path: any, value: any) => {
            if (value !== undefined && value !== null && value !== "") {
                setValue(path, value, { shouldDirty: true, shouldValidate: true })
                newTentative.add(path)
            }
        }

        if (payload) {
            if (payload.authority) updateField("attribution.issuer", payload.authority)
            if (payload.mint) updateField("attribution.mint", payload.mint)
            if (payload.date_from) updateField("attribution.year_start", payload.date_from)
            if (payload.date_to) updateField("attribution.year_end", payload.date_to)

            // RPC often returns date_string (e.g. "AD 14/15") without date_from/date_to
            if (payload.date_string && payload.date_from == null && payload.date_to == null) {
                const existing = form.getValues("personal_notes") || ""
                const datingNote = `Dating (catalog): ${payload.date_string}`
                setValue("personal_notes", existing ? `${datingNote}\n${existing}` : datingNote, { shouldDirty: true })
                newTentative.add("personal_notes")
            }

            if (payload.metal) {
                const metalMap: any = { 'gold': 'gold', 'silver': 'silver', 'bronze': 'bronze', 'ae': 'bronze', 'billon': 'billon', 'copper': 'copper' }
                if (metalMap[payload.metal.toLowerCase()]) {
                    updateField("metal", metalMap[payload.metal.toLowerCase()])
                }
            }

            if (payload.obverse_description) updateField("design.obverse_description", payload.obverse_description)
            if (payload.reverse_description) updateField("design.reverse_description", payload.reverse_description)
            if (payload.obverse_legend) updateField("design.obverse_legend", payload.obverse_legend)
            if (payload.reverse_legend) updateField("design.reverse_legend", payload.reverse_legend)
        }

        // Add to Reference List (works for success, ambiguous, and deferred e.g. RPC)
        if (suggestion.external_id) {
            const currentRefs = form.getValues("references") || []

            // Parse catalog + number: "RIC III 42" -> catalog="RIC III", number="42"; "rpc-1-4374" -> "RPC I", "4374"
            let catalog: string
            let number: string
            const rpcMatch = suggestion.external_id.match(/^rpc-([IVX\d]+)-(\d+)$/i)
            if (rpcMatch) {
                const vol = rpcMatch[1]
                number = rpcMatch[2]
                catalog = /^\d+$/.test(vol) ? `RPC ${vol}` : `RPC ${vol.toUpperCase()}`
            } else {
                const parts = suggestion.external_id.split(" ")
                number = parts.pop() || ""
                catalog = parts.join(" ") || suggestion.external_id
            }

            const exists = currentRefs.some((r) =>
                r != null &&
                ((r.catalog + " " + r.number).toLowerCase() === (catalog + " " + number).toLowerCase() ||
                (r.catalog === suggestion.external_id))
            )

            if (!exists) {
                const newRef = {
                    catalog: catalog || suggestion.external_id,
                    number: number,
                    is_primary: currentRefs.length === 0,
                    notes: payload ? "Auto-linked" : "Manual lookup"
                } as any

                setValue("references", [...currentRefs, newRef], { shouldDirty: true })
                toast.info(`Added ${catalog} ${number} to references list`)
            }
        }

        if (payload) {
            setTentativeFields(newTentative)
            toast.success(`Populated details from ${suggestion.external_id}`, {
                description: "Fields marked in yellow are tentative suggestions."
            })
            setTimeout(() => setTentativeFields(new Set()), 10000)
        } else if (suggestion.external_id) {
            toast.success(`Added reference ${suggestion.external_id}`, {
                description: "RPC has no API — use the link to look up details manually."
            })
        }
    }

    const [validationErrors, setValidationErrors] = useState<string[]>([])

    const onError = (errors: any) => {
        console.error("Form validation errors:", errors)
        const errorMessages: string[] = []

        // Recursive function to flatten errors
        const extractErrors = (obj: any, path: string = "") => {
            Object.keys(obj).forEach(key => {
                const currentPath = path ? `${path}.${key}` : key
                if (obj[key].message) {
                    errorMessages.push(`${currentPath}: ${obj[key].message}`)
                } else if (typeof obj[key] === 'object') {
                    extractErrors(obj[key], currentPath)
                }
            })
        }
        extractErrors(errors)
        setValidationErrors(errorMessages)

        toast.error("Validation Failed", {
            description: "Please check the errors listed at the top of the form.",
            duration: 5000
        })

        // Scroll to top to show errors
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    return (
        <div className="space-y-6">
            {/* Validation Error Banner */}
            {validationErrors.length > 0 && (
                <Alert variant="destructive" className="mb-6 animate-in slide-in-from-top-2 border-2 border-red-500/50 bg-red-50 dark:bg-red-950/30">
                    <AlertCircle className="h-5 w-5" />
                    <AlertTitle className="text-lg font-bold">Please fix the following errors:</AlertTitle>
                    <AlertDescription>
                        <ul className="list-disc pl-5 mt-2 space-y-1 text-sm font-medium">
                            {validationErrors.map((err, i) => (
                                <li key={i} className="text-red-700 dark:text-red-300">
                                    {err.replace(/_/g, ' ').replace(/\./g, ' > ')}
                                </li>
                            ))}
                        </ul>
                    </AlertDescription>
                </Alert>
            )}

            <div className="space-y-4">
                <div className="flex justify-between items-end">
                    <div className="space-y-1">
                        <h2 className="text-xl font-semibold flex items-center gap-2">
                            {(() => {
                                const Icon = STEPS[currentStep].icon
                                return <Icon className="h-5 w-5 text-primary" />
                            })()}
                            {STEPS[currentStep].title}
                        </h2>
                        <p className="text-sm text-muted-foreground">{STEPS[currentStep].description}</p>
                    </div>
                    <div className="text-sm font-medium text-muted-foreground">
                        Step {currentStep + 1} of {STEPS.length}
                    </div>
                </div>
                <Progress value={progress} className="h-2" />
            </div>

            {/* Navigation Buttons (Moved to Top for Consistency) */}
            <div className="flex justify-between items-center py-2">
                <Button
                    type="button"
                    variant="ghost"
                    onClick={(e) => { e.preventDefault(); prevStep(); }}
                    disabled={currentStep === 0}
                    className="gap-2"
                >
                    <ChevronLeft className="h-4 w-4" />
                    Previous
                </Button>

                {currentStep < STEPS.length - 1 ? (
                    <Button
                        type="button"
                        onClick={(e) => { e.preventDefault(); nextStep(); }}
                        className="gap-2"
                    >
                        Next Step
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                ) : (
                    <Button type="submit" onClick={form.handleSubmit(onSubmit, onError)} disabled={isSubmitting} className="gap-2 min-w-[140px]">
                        {isSubmitting ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Check className="h-4 w-4" />
                        )}
                        {coin ? "Update Specimen" : "Save to Collection"}
                    </Button>
                )}
            </div>

            <form
                onSubmit={(e) => {
                    e.preventDefault(); // Prevent default submission
                    handleSubmit(onSubmit, onError)(e); // Manually handle
                }}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.target instanceof HTMLInputElement && e.target.type !== 'textarea') {
                        e.preventDefault(); // Prevent Enter from submitting
                    }
                }}
                className="space-y-8"
            >
                <div className="min-h-[400px] animate-in fade-in slide-in-from-right-4 duration-300">
                    {currentStep === 0 && <IdentityStep form={form} onReferenceSelect={handleReferenceSelect} tentativeFields={tentativeFields} />}
                    {currentStep === 1 && <PhysicalStep form={form} tentativeFields={tentativeFields} />}
                    {currentStep === 2 && <DesignStep form={form} tentativeFields={tentativeFields} />}
                    {currentStep === 3 && (
                        <ResearchStep
                            form={form}
                            onReferenceSelect={handleReferenceSelect}
                            coinContext={{
                                ruler: attribution.issuer ?? undefined,
                                mint: attribution.mint ?? undefined
                            }}
                        />
                    )}
                    {currentStep === 4 && <CommercialStep form={form} />}
                    {currentStep === 5 && <FinalizeStep form={form} />}
                </div>
            </form>
        </div>


    )
}

// Helper to determine which fields to validate at each step
function getFieldsForStep(step: number): any[] {
    switch (step) {
        case 0: return ['category', 'attribution.issuer', 'attribution.year_start', 'attribution.year_end', 'issue_status']
        case 1: return ['metal', 'dimensions.weight_g', 'dimensions.diameter_mm', 'dimensions.die_axis', 'dimensions.specific_gravity']
        case 2: return ['design.obverse_legend', 'design.reverse_legend']
        case 3: return ['die_info.obverse_die_id', 'die_info.reverse_die_id', 'find_data.find_spot', 'find_data.find_date']
        case 4: return ['acquisition.price', 'acquisition.currency', 'acquisition.source', 'grading.grading_state', 'grading.grade', 'grading.service', 'grading.certification_number']
        default: return []
    }
}
