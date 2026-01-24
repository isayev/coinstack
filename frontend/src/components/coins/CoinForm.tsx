import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CoinDetail, CoinCreate } from "@/types/coin";
import { Loader2 } from "lucide-react";

// Form schema
const coinSchema = z.object({
  category: z.enum(["republic", "imperial", "provincial", "byzantine", "greek", "other"]),
  denomination: z.string().min(1, "Denomination is required"),
  metal: z.enum(["gold", "silver", "billon", "bronze", "orichalcum", "copper"]),
  issuing_authority: z.string().min(1, "Issuing authority is required"),
  series: z.string().optional(),
  portrait_subject: z.string().optional(),
  status: z.string().optional(),
  reign_start: z.coerce.number().optional().nullable(),
  reign_end: z.coerce.number().optional().nullable(),
  mint_year_start: z.coerce.number().optional().nullable(),
  mint_year_end: z.coerce.number().optional().nullable(),
  weight_g: z.coerce.number().optional().nullable(),
  diameter_mm: z.coerce.number().optional().nullable(),
  die_axis: z.coerce.number().min(0).max(12).optional().nullable(),
  obverse_legend: z.string().optional(),
  obverse_description: z.string().optional(),
  reverse_legend: z.string().optional(),
  reverse_description: z.string().optional(),
  exergue: z.string().optional(),
  grade_service: z.enum(["ngc", "pcgs", "self", "dealer"]).optional().nullable(),
  grade: z.string().optional(),
  certification_number: z.string().optional(),
  acquisition_date: z.string().optional(),
  acquisition_price: z.coerce.number().optional().nullable(),
  acquisition_source: z.string().optional(),
  acquisition_url: z.string().optional(),
  storage_location: z.string().optional(),
  rarity: z.enum(["common", "scarce", "rare", "very_rare", "extremely_rare", "unique"]).optional().nullable(),
  personal_notes: z.string().optional(),
  historical_significance: z.string().optional(),
});

type CoinFormData = z.infer<typeof coinSchema>;

interface CoinFormProps {
  coin?: CoinDetail;
  onSubmit: (data: CoinCreate) => void;
  isSubmitting?: boolean;
}

export function CoinForm({ coin, onSubmit, isSubmitting }: CoinFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CoinFormData>({
    resolver: zodResolver(coinSchema),
    defaultValues: {
      category: coin?.category || "imperial",
      denomination: coin?.denomination || "",
      metal: coin?.metal || "silver",
      issuing_authority: coin?.issuing_authority || "",
      series: coin?.series || "",
      portrait_subject: coin?.portrait_subject || "",
      status: coin?.status || "",
      reign_start: coin?.reign_start || null,
      reign_end: coin?.reign_end || null,
      mint_year_start: coin?.mint_year_start || null,
      mint_year_end: coin?.mint_year_end || null,
      weight_g: coin?.weight_g || null,
      diameter_mm: coin?.diameter_mm || null,
      die_axis: coin?.die_axis || null,
      obverse_legend: coin?.obverse_legend || "",
      obverse_description: coin?.obverse_description || "",
      reverse_legend: coin?.reverse_legend || "",
      reverse_description: coin?.reverse_description || "",
      exergue: coin?.exergue || "",
      grade_service: (coin?.grade_service as any) || null,
      grade: coin?.grade || "",
      certification_number: coin?.certification_number || "",
      acquisition_date: coin?.acquisition_date || "",
      acquisition_price: coin?.acquisition_price || null,
      acquisition_source: coin?.acquisition_source || "",
      acquisition_url: coin?.acquisition_url || "",
      storage_location: coin?.storage_location || "",
      rarity: (coin?.rarity as any) || null,
      personal_notes: coin?.personal_notes || "",
      historical_significance: coin?.historical_significance || "",
    },
  });

  const category = watch("category");
  const metal = watch("metal");
  const gradeService = watch("grade_service");
  const rarity = watch("rarity");

  const onFormSubmit = (data: CoinFormData) => {
    // Clean up null/empty values
    const cleaned: any = {};
    Object.entries(data).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") {
        cleaned[key] = value;
      }
    });
    onSubmit(cleaned as CoinCreate);
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      <Tabs defaultValue="basic" className="w-full">
        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-7">
          <TabsTrigger value="basic">Basic</TabsTrigger>
          <TabsTrigger value="dating">Dating</TabsTrigger>
          <TabsTrigger value="physical">Physical</TabsTrigger>
          <TabsTrigger value="design">Design</TabsTrigger>
          <TabsTrigger value="grading">Grading</TabsTrigger>
          <TabsTrigger value="acquisition">Acquisition</TabsTrigger>
          <TabsTrigger value="notes">Notes</TabsTrigger>
        </TabsList>

        {/* Basic Info */}
        <TabsContent value="basic">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Category *</label>
                  <Select value={category} onValueChange={(v) => setValue("category", v as any)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="republic">Republic</SelectItem>
                      <SelectItem value="imperial">Imperial</SelectItem>
                      <SelectItem value="provincial">Provincial</SelectItem>
                      <SelectItem value="byzantine">Byzantine</SelectItem>
                      <SelectItem value="greek">Greek</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.category && <p className="text-sm text-destructive">{errors.category.message}</p>}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Metal *</label>
                  <Select value={metal} onValueChange={(v) => setValue("metal", v as any)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gold">Gold</SelectItem>
                      <SelectItem value="silver">Silver</SelectItem>
                      <SelectItem value="billon">Billon</SelectItem>
                      <SelectItem value="bronze">Bronze</SelectItem>
                      <SelectItem value="orichalcum">Orichalcum</SelectItem>
                      <SelectItem value="copper">Copper</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Denomination *</label>
                  <Input {...register("denomination")} placeholder="e.g., Denarius, Antoninianus" />
                  {errors.denomination && <p className="text-sm text-destructive">{errors.denomination.message}</p>}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Series</label>
                  <Input {...register("series")} placeholder="e.g., CONSECRATIO" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Issuing Authority *</label>
                  <Input {...register("issuing_authority")} placeholder="e.g., Augustus, Trajan" />
                  {errors.issuing_authority && <p className="text-sm text-destructive">{errors.issuing_authority.message}</p>}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Portrait Subject</label>
                  <Input {...register("portrait_subject")} placeholder="e.g., Augustus, Livia" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <Input {...register("status")} placeholder="e.g., As Caesar, As Augustus" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Dating */}
        <TabsContent value="dating">
          <Card>
            <CardHeader>
              <CardTitle>Dating</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Reign Start (Year)</label>
                  <Input type="number" {...register("reign_start")} placeholder="e.g., -27 for 27 BC" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Reign End (Year)</label>
                  <Input type="number" {...register("reign_end")} placeholder="e.g., 14 for AD 14" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Mint Year Start</label>
                  <Input type="number" {...register("mint_year_start")} placeholder="Year coin was minted" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Mint Year End</label>
                  <Input type="number" {...register("mint_year_end")} placeholder="If range" />
                </div>
              </div>
              <p className="text-sm text-muted-foreground">Use negative numbers for BC dates (e.g., -44 for 44 BC)</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Physical */}
        <TabsContent value="physical">
          <Card>
            <CardHeader>
              <CardTitle>Physical Attributes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Weight (g)</label>
                  <Input type="number" step="0.01" {...register("weight_g")} placeholder="e.g., 3.45" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Diameter (mm)</label>
                  <Input type="number" step="0.1" {...register("diameter_mm")} placeholder="e.g., 19.5" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Die Axis (h)</label>
                  <Input type="number" min="0" max="12" {...register("die_axis")} placeholder="0-12" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Design */}
        <TabsContent value="design">
          <Card>
            <CardHeader>
              <CardTitle>Design Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium">Obverse</h4>
                <div className="grid grid-cols-1 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Legend</label>
                    <Input {...register("obverse_legend")} placeholder="e.g., IMP CAESAR DIVI F AVGVSTVS" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Description</label>
                    <textarea 
                      {...register("obverse_description")} 
                      className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      placeholder="Laureate head right..."
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Reverse</h4>
                <div className="grid grid-cols-1 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Legend</label>
                    <Input {...register("reverse_legend")} placeholder="e.g., PONTIF MAXIM" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Description</label>
                    <textarea 
                      {...register("reverse_description")} 
                      className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      placeholder="Livia seated right..."
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Exergue</label>
                    <Input {...register("exergue")} placeholder="e.g., XXIR" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Grading */}
        <TabsContent value="grading">
          <Card>
            <CardHeader>
              <CardTitle>Grading</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Grade Service</label>
                  <Select value={gradeService || "none"} onValueChange={(v) => setValue("grade_service", v === "none" ? null : v as any)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select service" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      <SelectItem value="ngc">NGC</SelectItem>
                      <SelectItem value="pcgs">PCGS</SelectItem>
                      <SelectItem value="self">Self</SelectItem>
                      <SelectItem value="dealer">Dealer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Grade</label>
                  <Input {...register("grade")} placeholder="e.g., VF, Choice XF, MS 63" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Certification Number</label>
                  <Input {...register("certification_number")} placeholder="NGC/PCGS cert number" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Acquisition */}
        <TabsContent value="acquisition">
          <Card>
            <CardHeader>
              <CardTitle>Acquisition Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Acquisition Date</label>
                  <Input type="date" {...register("acquisition_date")} />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Price (USD)</label>
                  <Input type="number" step="0.01" {...register("acquisition_price")} placeholder="e.g., 150.00" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Source</label>
                  <Input {...register("acquisition_source")} placeholder="e.g., CNG, VCoins, Heritage" />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Storage Location</label>
                  <Input {...register("storage_location")} placeholder="e.g., SlabBox1, Velv1-2-3" />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium">Listing URL</label>
                  <Input {...register("acquisition_url")} placeholder="https://..." />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notes */}
        <TabsContent value="notes">
          <Card>
            <CardHeader>
              <CardTitle>Notes & Research</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Rarity</label>
                <Select value={rarity || "none"} onValueChange={(v) => setValue("rarity", v === "none" ? null : v as any)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select rarity" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Not specified</SelectItem>
                    <SelectItem value="common">Common</SelectItem>
                    <SelectItem value="scarce">Scarce</SelectItem>
                    <SelectItem value="rare">Rare</SelectItem>
                    <SelectItem value="very_rare">Very Rare</SelectItem>
                    <SelectItem value="extremely_rare">Extremely Rare</SelectItem>
                    <SelectItem value="unique">Unique</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Historical Significance</label>
                <textarea 
                  {...register("historical_significance")} 
                  className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  placeholder="Historical context and significance..."
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Personal Notes</label>
                <textarea 
                  {...register("personal_notes")} 
                  className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  placeholder="Your personal notes about this coin..."
                />
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
