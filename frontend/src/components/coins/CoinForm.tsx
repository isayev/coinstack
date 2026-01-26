import { useState } from "react"
import { useForm, Controller, UseFormReturn } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { 
  DomainCoinSchema, 
  Category, 
  Metal, 
  GradingState, 
  GradeService, 
  Coin,
  IssueStatus
} from "@/domain/schemas"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { 
  Loader2, 
  ChevronRight, 
  ChevronLeft, 
  Check, 
  Info, 
  Search,
  Scale,
  Palette,
  Microscope,
  Landmark,
  Image as ImageIcon
} from "lucide-react"
import { VocabAutocomplete } from "./VocabAutocomplete"
import { LegendInput } from "./LegendInput"
import { ReferenceSuggest } from "./ReferenceSuggest"
import { DieLinker } from "./DieLinker"
import { MonogramPicker } from "./MonogramPicker"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { toast } from "sonner"

// Schema for form values
const CreateCoinSchema = DomainCoinSchema.omit({ id: true }).superRefine((data, ctx) => {
  if (data.attribution.year_start != null && data.attribution.year_end != null) {
    if (data.attribution.year_end < data.attribution.year_start) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "End year must be after start year",
        path: ["attribution", "year_end"],
      });
    }
  }
});
type CoinFormData = z.infer<typeof CreateCoinSchema>;

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

  const form = useForm<CoinFormData>({
    resolver: zodResolver(CreateCoinSchema),
    defaultValues: propDefaultValues || {
      category: coin?.category || "roman_imperial",
      metal: coin?.metal || "silver",
      issue_status: coin?.issue_status || "official",
      dimensions: {
        weight_g: coin?.dimensions.weight_g || null,
        diameter_mm: coin?.dimensions.diameter_mm || null,
        die_axis: coin?.dimensions.die_axis || null,
        specific_gravity: coin?.dimensions.specific_gravity || null,
      },
      die_info: {
        obverse_die_id: coin?.die_info?.obverse_die_id || "",
        reverse_die_id: coin?.die_info?.reverse_die_id || "",
      },
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
      images: coin?.images || [],
      design: coin?.design || {
        obverse_legend: "",
        obverse_description: "",
        reverse_legend: "",
        reverse_description: "",
        exergue: ""
      }
    },
  })

  const { handleSubmit, trigger, setValue, watch } = form
  const attribution = watch("attribution")

  const nextStep = async () => {
    const fields = getFieldsForStep(currentStep)
    const isValid = await trigger(fields as any)
    if (isValid) {
      setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1))
    }
  }

  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0))

  const progress = ((currentStep + 1) / STEPS.length) * 100

  const handleReferenceSelect = (suggestion: any) => {
    const payload = suggestion.payload
    if (!payload) return

    if (payload.authority) setValue("attribution.issuer", payload.authority)
    if (payload.mint) setValue("attribution.mint", payload.mint)
    if (payload.date_from) setValue("attribution.year_start", payload.date_from)
    if (payload.date_to) setValue("attribution.year_end", payload.date_to)
    if (payload.metal) {
      const metalMap: any = { 'gold': 'gold', 'silver': 'silver', 'bronze': 'bronze', 'ae': 'bronze' }
      if (metalMap[payload.metal.toLowerCase()]) {
        setValue("metal", metalMap[payload.metal.toLowerCase()])
      }
    }
    if (payload.obverse_description) setValue("design.obverse_description", payload.obverse_description)
    if (payload.reverse_description) setValue("design.reverse_description", payload.reverse_description)
    
    toast.success(`Populated details from ${suggestion.external_id}`)
  }

  return (
    <div className="space-y-6">
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

      <form onSubmit={handleSubmit(onSubmit, (errors) => {
        console.error("Form validation errors:", errors)
        toast.error("Please fix validation errors before saving.")
      })} className="space-y-8">
        <div className="min-h-[400px] animate-in fade-in slide-in-from-right-4 duration-300">
          {currentStep === 0 && <IdentityStep form={form} />}
          {currentStep === 1 && <PhysicalStep form={form} />}
          {currentStep === 2 && <DesignStep form={form} />}
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

        <div className="flex justify-between pt-6 border-t">
          <Button
            type="button"
            variant="ghost"
            onClick={prevStep}
            disabled={currentStep === 0}
            className="gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>

          {currentStep < STEPS.length - 1 ? (
            <Button type="button" onClick={nextStep} className="gap-2">
              Next Step
              <ChevronRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button type="submit" disabled={isSubmitting} className="gap-2 min-w-[140px]">
              {isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Check className="h-4 w-4" />
              )}
              {coin ? "Update Specimen" : "Save to Collection"}
            </Button>
          )}
        </div>
      </form>
    </div>
  )
}

// --- Sub-Step Components ---

function IdentityStep({ form }: { form: UseFormReturn<CoinFormData> }) {
  const { register, control, watch, setValue } = form
  const category = watch("category")
  const issueStatus = watch("issue_status")
  const issuer = watch("attribution.issuer")
  const mint = watch("attribution.mint")

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
            <label htmlFor="issuer-autocomplete" className="text-sm font-semibold">Issuer / Authority *</label>
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
                  className="h-11"
                />
              )}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="mint-autocomplete" className="text-sm font-semibold">Mint</label>
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
                  className="h-11"
                />
              )}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="year-start-input" className="text-sm font-semibold">Year Start</label>
              <Input id="year-start-input" type="number" {...register("attribution.year_start")} placeholder="-27" className="h-11" />
            </div>
            <div className="space-y-2">
              <label htmlFor="year-end-input" className="text-sm font-semibold">Year End</label>
              <Input id="year-end-input" type="number" {...register("attribution.year_end")} placeholder="14" className="h-11" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function PhysicalStep({ form }: { form: UseFormReturn<CoinFormData> }) {
  const { register, watch, setValue } = form
  const metal = watch("metal")

  return (
    <Card className="border-none shadow-none bg-transparent">
      <CardContent className="p-0 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold">Metal *</label>
            <Select value={metal} onValueChange={(v) => setValue("metal", v as Metal)}>
              <SelectTrigger className="h-11"><SelectValue /></SelectTrigger>
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
              <Input type="number" step="0.01" {...register("dimensions.weight_g")} className="h-11 font-mono" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold">Diameter (mm) *</label>
              <Input type="number" step="0.1" {...register("dimensions.diameter_mm")} className="h-11 font-mono" />
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-semibold flex items-center gap-2">
              Specific Gravity
              <Info className="h-3 w-3 text-muted-foreground" />
            </label>
            <Input type="number" step="0.01" {...register("dimensions.specific_gravity")} placeholder="e.g. 10.5" className="h-11 font-mono" />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold">Die Axis (0-12h)</label>
            <Input type="number" min="0" max="12" {...register("dimensions.die_axis")} placeholder="6" className="h-11 font-mono" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function DesignStep({ form }: { form: UseFormReturn<CoinFormData> }) {
  const { register, watch, setValue } = form
  const design = watch("design")

  return (
    <Card className="border-none shadow-none bg-transparent">
      <CardContent className="p-0 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <LegendInput 
              label="Obverse Legend"
              value={design?.obverse_legend || ""}
              side="obverse"
              onChange={(v) => setValue("design.obverse_legend", v)}
              placeholder="IMP CAES DOMIT AVG..."
            />
            <div className="space-y-2">
              <label className="text-sm font-semibold">Obverse Description</label>
              <Input {...register("design.obverse_description")} placeholder="Laureate head right" />
            </div>
          </div>
          <div className="space-y-4">
            <LegendInput 
              label="Reverse Legend"
              value={design?.reverse_legend || ""}
              side="reverse"
              onChange={(v) => setValue("design.reverse_legend", v)}
              placeholder="MONETA AVGVSTI"
            />
            <div className="space-y-2">
              <label className="text-sm font-semibold">Reverse Description</label>
              <Input {...register("design.reverse_description")} placeholder="Moneta standing left holding scales" />
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

function ResearchStep({ 
  form, 
  onReferenceSelect,
  coinContext 
}: { 
  form: UseFormReturn<CoinFormData>, 
  onReferenceSelect: (s: any) => void,
  coinContext: any
}) {
  const { register, control } = form
  return (
    <Card className="border-none shadow-none bg-transparent">
      <CardContent className="p-0 space-y-8">
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Catalog Reference</h3>
          <div className="space-y-2">
            <label className="text-sm font-semibold">Primary Reference (ID Lookup)</label>
            <ReferenceSuggest 
              value="" 
              onChange={() => {}}
              onSelectSuggestion={onReferenceSelect}
              coinContext={coinContext}
              placeholder="Type to search OCRE / RPC / Crawford..."
            />
            <p className="text-xs text-muted-foreground italic">
              Search by catalog ID to auto-populate descriptions, mint, and dates.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Die Identification</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold">Obverse Die ID</label>
              <Input {...register("die_info.obverse_die_id")} placeholder="O-Vesp-71-A" className="h-11 font-mono" />
              <DieLinker dieId={form.watch("die_info.obverse_die_id") || ""} side="obverse" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold">Reverse Die ID</label>
              <Input {...register("die_info.reverse_die_id")} placeholder="R-Pax-04" className="h-11 font-mono" />
              <DieLinker dieId={form.watch("die_info.reverse_die_id") || ""} side="reverse" />
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

function CommercialStep({ form }: { form: UseFormReturn<CoinFormData> }) {
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
              <Input type="number" step="0.01" {...register("acquisition.price")} className="h-11 font-mono" />
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
        </div>
      </CardContent>
    </Card>
  )
}

function FinalizeStep({ form }: { form: UseFormReturn<CoinFormData> }) {
  const { register, watch } = form
  const images = watch("images")

  return (
    <Card className="border-none shadow-none bg-transparent">
      <CardContent className="p-0 space-y-6">
        {/* Scraped Image Preview */}
        {images && images.length > 0 && (
          <div className="space-y-3">
            <label className="text-sm font-semibold flex items-center gap-2">
              <ImageIcon className="h-4 w-4" />
              Ingested Images
            </label>
            <div className="flex gap-4 overflow-x-auto pb-2">
              {images.map((img, i) => (
                <div key={i} className="relative w-32 aspect-square rounded-lg border overflow-hidden bg-muted flex-shrink-0">
                  <img src={img.url} className="w-full h-full object-cover" alt="Scraped" />
                  {img.is_primary && (
                    <div className="absolute top-1 right-1 bg-primary text-[8px] text-white px-1.5 py-0.5 rounded font-bold uppercase">
                      Primary
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-2">
          <label className="text-sm font-semibold">Storage Location</label>
          <Input {...register("storage_location")} placeholder="SlabBox 1, Tray 4, etc." className="h-11" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-semibold">Personal Research Notes</label>
          <textarea 
            {...register("personal_notes")} 
            className="w-full min-h-[150px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Add any specific research notes, variant details, or collection history..."
          />
        </div>
        <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 flex gap-3">
          <ImageIcon className="h-5 w-5 text-blue-500 shrink-0" />
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>Photo Upload:</strong> For this version, please save the coin first, then upload high-resolution photos via the <strong>Image Manager</strong> on the coin detail page.
          </p>
        </div>
      </CardContent>
    </Card>
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