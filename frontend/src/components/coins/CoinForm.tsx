import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { DomainCoinSchema, Category, Metal, GradingState, GradeService, Coin } from "@/domain/schemas"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

// The form values follow the V2 nested structure
const CreateCoinSchema = DomainCoinSchema.omit({ id: true });
type CoinFormData = z.infer<typeof CreateCoinSchema>;

interface CoinFormProps {
  coin?: Coin;
  onSubmit: (data: CoinFormData) => void;
  isSubmitting?: boolean;
  defaultValues?: Partial<CoinFormData>;
}

export function CoinForm({ coin, onSubmit, isSubmitting, defaultValues: propDefaultValues }: CoinFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { /* errors */ },
  } = useForm<CoinFormData>({
    resolver: zodResolver(CreateCoinSchema),
    defaultValues: propDefaultValues || {
      category: coin?.category || "roman_imperial",
      metal: coin?.metal || "silver",
      dimensions: {
        weight_g: coin?.dimensions.weight_g || 0,
        diameter_mm: coin?.dimensions.diameter_mm || 0,
        die_axis: coin?.dimensions.die_axis || null,
      },
      attribution: {
        issuer: coin?.attribution.issuer || "",
        mint: coin?.attribution.mint || "",
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
      images: coin?.images || []
    },
  });

  const category = watch("category");
  const metal = watch("metal");
  const gradingState = watch("grading.grading_state");
  const gradeService = watch("grading.service");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Tabs defaultValue="basic" className="w-full">
        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-6">
          <TabsTrigger value="basic">Basic</TabsTrigger>
          <TabsTrigger value="physics">Physics</TabsTrigger>
          <TabsTrigger value="design">Design</TabsTrigger>
          <TabsTrigger value="grading">Grading</TabsTrigger>
          <TabsTrigger value="acquisition">Acquisition</TabsTrigger>
          <TabsTrigger value="images">Images</TabsTrigger>
        </TabsList>

        {/* Basic Info */}
        <TabsContent value="basic">
          <Card>
            <CardHeader><CardTitle>Classification & Attribution</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Category *</label>
                <Select value={category} onValueChange={(v) => setValue("category", v as Category)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="roman_imperial">Roman Imperial</SelectItem>
                    <SelectItem value="roman_republic">Roman Republic</SelectItem>
                    <SelectItem value="greek">Greek</SelectItem>
                    <SelectItem value="byzantine">Byzantine</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Issuer / Authority *</label>
                <Input {...register("attribution.issuer")} placeholder="e.g. Augustus" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Mint</label>
                <Input {...register("attribution.mint")} placeholder="e.g. Rome" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Year Start</label>
                  <Input type="number" {...register("attribution.year_start")} placeholder="-44" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Year End</label>
                  <Input type="number" {...register("attribution.year_end")} placeholder="14" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Physics */}
        <TabsContent value="physics">
          <Card>
            <CardHeader><CardTitle>Physical Measurements</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Metal *</label>
                <Select value={metal} onValueChange={(v) => setValue("metal", v as Metal)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gold">Gold</SelectItem>
                    <SelectItem value="silver">Silver</SelectItem>
                    <SelectItem value="bronze">Bronze</SelectItem>
                    <SelectItem value="billon">Billon</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Weight (g)</label>
                <Input type="number" step="0.01" {...register("dimensions.weight_g")} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Diameter (mm)</label>
                <Input type="number" step="0.1" {...register("dimensions.diameter_mm")} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Grading */}
        <TabsContent value="grading">
          <Card>
            <CardHeader><CardTitle>Grading & Condition</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Grading State</label>
                <Select value={gradingState} onValueChange={(v) => setValue("grading.grading_state", v as GradingState)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="raw">Raw</SelectItem>
                    <SelectItem value="slabbed">Slabbed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Grade</label>
                <Input {...register("grading.grade")} placeholder="e.g. Choice XF" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Service</label>
                <Select value={gradeService || "none"} onValueChange={(v) => setValue("grading.service", v === "none" ? null : v as GradeService)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="ngc">NGC</SelectItem>
                    <SelectItem value="pcgs">PCGS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Cert #</label>
                <Input {...register("grading.certification_number")} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Acquisition */}
        <TabsContent value="acquisition">
          <Card>
            <CardHeader><CardTitle>Acquisition Details</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Price</label>
                <Input type="number" step="0.01" {...register("acquisition.price")} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Source</label>
                <Input {...register("acquisition.source")} placeholder="Heritage, CNG, etc." />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">URL</label>
                <Input {...register("acquisition.url")} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-end gap-4">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
          {coin ? "Update Coin" : "Add Coin"}
        </Button>
      </div>
    </form>
  );
}