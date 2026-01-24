/**
 * CoinPreviewEditor - Editable form for coin preview data.
 * 
 * Features:
 * - Field confidence indicators (high/medium/low)
 * - Reset-to-original functionality
 * - Tabbed layout matching CoinForm
 * - Low-confidence field highlighting
 */
import { useState, useCallback } from "react";
import { 
  Undo, AlertCircle, Info, CheckCircle2, 
  Coins, Calendar, Scale, Palette, Award, DollarSign, FileText
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { 
  CoinPreviewData, 
  FieldConfidence, 
  CONFIDENCE_CONFIG 
} from "@/hooks/useImport";
import { cn } from "@/lib/utils";

interface CoinPreviewEditorProps {
  data: CoinPreviewData;
  originalData: CoinPreviewData;
  fieldConfidence: Record<string, FieldConfidence>;
  onChange: (data: CoinPreviewData) => void;
}

// Field with confidence indicator component
interface FieldProps {
  label: string;
  field: keyof CoinPreviewData;
  value: string | number | undefined | null;
  originalValue: string | number | undefined | null;
  confidence?: FieldConfidence;
  onChange: (value: string) => void;
  type?: "text" | "number" | "textarea";
  placeholder?: string;
}

function FieldWithConfidence({
  label,
  field,
  value,
  originalValue,
  confidence,
  onChange,
  type = "text",
  placeholder,
}: FieldProps) {
  const stringValue = value?.toString() ?? "";
  const originalStringValue = originalValue?.toString() ?? "";
  const isModified = stringValue !== originalStringValue && originalStringValue !== "";
  
  const config = confidence ? CONFIDENCE_CONFIG[confidence] : CONFIDENCE_CONFIG.high;
  
  return (
    <div className="space-y-1.5">
      <Label className="flex items-center gap-2 text-sm">
        {label}
        {confidence === "low" && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <AlertCircle className="h-3.5 w-3.5 text-amber-500" />
              </TooltipTrigger>
              <TooltipContent>
                <p>{config.tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        {confidence === "medium" && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-3.5 w-3.5 text-yellow-500" />
              </TooltipTrigger>
              <TooltipContent>
                <p>{config.tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        {isModified && (
          <Button
            variant="ghost"
            size="sm"
            className="h-5 px-1.5 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => onChange(originalStringValue)}
          >
            <Undo className="h-3 w-3 mr-1" />
            Reset
          </Button>
        )}
      </Label>
      {type === "textarea" ? (
        <Textarea
          value={stringValue}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={cn(
            "min-h-[80px]",
            config.borderColor,
            config.bgColor,
            isModified && "border-blue-500 bg-blue-500/5"
          )}
        />
      ) : (
        <Input
          type={type}
          value={stringValue}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={cn(
            config.borderColor,
            config.bgColor,
            isModified && "border-blue-500 bg-blue-500/5"
          )}
        />
      )}
    </div>
  );
}

export function CoinPreviewEditor({
  data,
  originalData,
  fieldConfidence,
  onChange,
}: CoinPreviewEditorProps) {
  
  const updateField = useCallback((field: keyof CoinPreviewData, value: any) => {
    onChange({
      ...data,
      [field]: value === "" ? undefined : value,
    });
  }, [data, onChange]);
  
  const getConfidence = (field: string): FieldConfidence | undefined => {
    return fieldConfidence[field];
  };
  
  return (
    <Tabs defaultValue="basic" className="w-full">
      <TabsList className="grid w-full grid-cols-4 lg:grid-cols-7">
        <TabsTrigger value="basic" className="gap-1">
          <Coins className="h-3 w-3 hidden sm:inline" />
          Basic
        </TabsTrigger>
        <TabsTrigger value="dating" className="gap-1">
          <Calendar className="h-3 w-3 hidden sm:inline" />
          Dating
        </TabsTrigger>
        <TabsTrigger value="physical" className="gap-1">
          <Scale className="h-3 w-3 hidden sm:inline" />
          Physical
        </TabsTrigger>
        <TabsTrigger value="design" className="gap-1">
          <Palette className="h-3 w-3 hidden sm:inline" />
          Design
        </TabsTrigger>
        <TabsTrigger value="grading" className="gap-1">
          <Award className="h-3 w-3 hidden sm:inline" />
          Grading
        </TabsTrigger>
        <TabsTrigger value="acquisition" className="gap-1">
          <DollarSign className="h-3 w-3 hidden sm:inline" />
          Acquisition
        </TabsTrigger>
        <TabsTrigger value="notes" className="gap-1">
          <FileText className="h-3 w-3 hidden sm:inline" />
          Notes
        </TabsTrigger>
      </TabsList>
      
      {/* Basic Info */}
      <TabsContent value="basic">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Basic Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Category *</Label>
                <Select
                  value={data.category || ""}
                  onValueChange={(v) => updateField("category", v)}
                >
                  <SelectTrigger className={cn(
                    getConfidence("category") === "low" && "border-amber-500"
                  )}>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="greek">Greek</SelectItem>
                    <SelectItem value="celtic">Celtic</SelectItem>
                    <SelectItem value="republic">Republic</SelectItem>
                    <SelectItem value="imperial">Imperial</SelectItem>
                    <SelectItem value="provincial">Provincial</SelectItem>
                    <SelectItem value="judaean">Judaean</SelectItem>
                    <SelectItem value="byzantine">Byzantine</SelectItem>
                    <SelectItem value="migration">Migration Period</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-1.5">
                <Label>Metal *</Label>
                <Select
                  value={data.metal || ""}
                  onValueChange={(v) => updateField("metal", v)}
                >
                  <SelectTrigger className={cn(
                    getConfidence("metal") === "low" && "border-amber-500"
                  )}>
                    <SelectValue placeholder="Select metal" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gold">Gold</SelectItem>
                    <SelectItem value="electrum">Electrum</SelectItem>
                    <SelectItem value="silver">Silver</SelectItem>
                    <SelectItem value="billon">Billon</SelectItem>
                    <SelectItem value="bronze">Bronze</SelectItem>
                    <SelectItem value="copper">Copper</SelectItem>
                    <SelectItem value="ae">AE (Generic)</SelectItem>
                    <SelectItem value="uncertain">Uncertain</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <FieldWithConfidence
                label="Denomination *"
                field="denomination"
                value={data.denomination}
                originalValue={originalData.denomination}
                confidence={getConfidence("denomination")}
                onChange={(v) => updateField("denomination", v)}
                placeholder="e.g., Denarius, Antoninianus"
              />
              
              <FieldWithConfidence
                label="Issuing Authority *"
                field="issuing_authority"
                value={data.issuing_authority}
                originalValue={originalData.issuing_authority}
                confidence={getConfidence("issuing_authority")}
                onChange={(v) => updateField("issuing_authority", v)}
                placeholder="e.g., Augustus, Trajan"
              />
              
              <FieldWithConfidence
                label="Portrait Subject"
                field="portrait_subject"
                value={data.portrait_subject}
                originalValue={originalData.portrait_subject}
                confidence={getConfidence("portrait_subject")}
                onChange={(v) => updateField("portrait_subject", v)}
                placeholder="e.g., Augustus, Livia"
              />
              
              <FieldWithConfidence
                label="Mint"
                field="mint_name"
                value={data.mint_name}
                originalValue={originalData.mint_name}
                confidence={getConfidence("mint_name")}
                onChange={(v) => updateField("mint_name", v)}
                placeholder="e.g., Rome, Lugdunum"
              />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      
      {/* Dating */}
      <TabsContent value="dating">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Dating Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FieldWithConfidence
                label="Reign Start"
                field="reign_start"
                value={data.reign_start}
                originalValue={originalData.reign_start}
                confidence={getConfidence("reign_start")}
                onChange={(v) => updateField("reign_start", v ? parseInt(v) : undefined)}
                type="number"
                placeholder="e.g., -27 for 27 BC"
              />
              
              <FieldWithConfidence
                label="Reign End"
                field="reign_end"
                value={data.reign_end}
                originalValue={originalData.reign_end}
                confidence={getConfidence("reign_end")}
                onChange={(v) => updateField("reign_end", v ? parseInt(v) : undefined)}
                type="number"
                placeholder="e.g., 14 for AD 14"
              />
              
              <FieldWithConfidence
                label="Mint Year Start"
                field="mint_year_start"
                value={data.mint_year_start}
                originalValue={originalData.mint_year_start}
                confidence={getConfidence("mint_year_start")}
                onChange={(v) => updateField("mint_year_start", v ? parseInt(v) : undefined)}
                type="number"
                placeholder="Year struck"
              />
              
              <FieldWithConfidence
                label="Mint Year End"
                field="mint_year_end"
                value={data.mint_year_end}
                originalValue={originalData.mint_year_end}
                confidence={getConfidence("mint_year_end")}
                onChange={(v) => updateField("mint_year_end", v ? parseInt(v) : undefined)}
                type="number"
                placeholder="If range"
              />
            </div>
            <p className="text-sm text-muted-foreground">
              Use negative numbers for BC dates (e.g., -44 for 44 BC)
            </p>
          </CardContent>
        </Card>
      </TabsContent>
      
      {/* Physical */}
      <TabsContent value="physical">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Physical Attributes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <FieldWithConfidence
                label="Weight (g)"
                field="weight_g"
                value={data.weight_g}
                originalValue={originalData.weight_g}
                confidence={getConfidence("weight_g")}
                onChange={(v) => updateField("weight_g", v ? parseFloat(v) : undefined)}
                type="number"
                placeholder="e.g., 3.45"
              />
              
              <FieldWithConfidence
                label="Diameter (mm)"
                field="diameter_mm"
                value={data.diameter_mm}
                originalValue={originalData.diameter_mm}
                confidence={getConfidence("diameter_mm")}
                onChange={(v) => updateField("diameter_mm", v ? parseFloat(v) : undefined)}
                type="number"
                placeholder="e.g., 19.5"
              />
              
              <FieldWithConfidence
                label="Die Axis (h)"
                field="die_axis"
                value={data.die_axis}
                originalValue={originalData.die_axis}
                confidence={getConfidence("die_axis")}
                onChange={(v) => updateField("die_axis", v ? parseInt(v) : undefined)}
                type="number"
                placeholder="0-12"
              />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      
      {/* Design */}
      <TabsContent value="design">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Design Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <h4 className="font-medium text-sm">Obverse</h4>
              <FieldWithConfidence
                label="Legend"
                field="obverse_legend"
                value={data.obverse_legend}
                originalValue={originalData.obverse_legend}
                confidence={getConfidence("obverse_legend")}
                onChange={(v) => updateField("obverse_legend", v)}
                placeholder="e.g., IMP CAESAR DIVI F AVGVSTVS"
              />
              <FieldWithConfidence
                label="Description"
                field="obverse_description"
                value={data.obverse_description}
                originalValue={originalData.obverse_description}
                confidence={getConfidence("obverse_description")}
                onChange={(v) => updateField("obverse_description", v)}
                type="textarea"
                placeholder="Laureate head right..."
              />
            </div>
            
            <div className="space-y-4">
              <h4 className="font-medium text-sm">Reverse</h4>
              <FieldWithConfidence
                label="Legend"
                field="reverse_legend"
                value={data.reverse_legend}
                originalValue={originalData.reverse_legend}
                confidence={getConfidence("reverse_legend")}
                onChange={(v) => updateField("reverse_legend", v)}
                placeholder="e.g., PONTIF MAXIM"
              />
              <FieldWithConfidence
                label="Description"
                field="reverse_description"
                value={data.reverse_description}
                originalValue={originalData.reverse_description}
                confidence={getConfidence("reverse_description")}
                onChange={(v) => updateField("reverse_description", v)}
                type="textarea"
                placeholder="Livia seated right..."
              />
              <FieldWithConfidence
                label="Exergue"
                field="exergue"
                value={data.exergue}
                originalValue={originalData.exergue}
                confidence={getConfidence("exergue")}
                onChange={(v) => updateField("exergue", v)}
                placeholder="e.g., XXIR"
              />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      
      {/* Grading */}
      <TabsContent value="grading">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Grading Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <Label>Grade Service</Label>
                <Select
                  value={data.grade_service || ""}
                  onValueChange={(v) => updateField("grade_service", v || undefined)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select service" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ngc">NGC</SelectItem>
                    <SelectItem value="pcgs">PCGS</SelectItem>
                    <SelectItem value="self">Self</SelectItem>
                    <SelectItem value="dealer">Dealer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <FieldWithConfidence
                label="Grade"
                field="grade"
                value={data.grade}
                originalValue={originalData.grade}
                confidence={getConfidence("grade")}
                onChange={(v) => updateField("grade", v)}
                placeholder="e.g., VF, Choice XF, MS 63"
              />
              
              <FieldWithConfidence
                label="Certification Number"
                field="certification_number"
                value={data.certification_number}
                originalValue={originalData.certification_number}
                confidence={getConfidence("certification_number")}
                onChange={(v) => updateField("certification_number", v)}
                placeholder="NGC/PCGS cert number"
              />
            </div>
            
            {data.grade_service === "ngc" && (
              <div className="grid grid-cols-2 gap-4">
                <FieldWithConfidence
                  label="Strike Quality (1-5)"
                  field="strike_quality"
                  value={data.strike_quality}
                  originalValue={originalData.strike_quality}
                  confidence={getConfidence("strike_quality")}
                  onChange={(v) => updateField("strike_quality", v ? parseInt(v) : undefined)}
                  type="number"
                  placeholder="1-5"
                />
                
                <FieldWithConfidence
                  label="Surface Quality (1-5)"
                  field="surface_quality"
                  value={data.surface_quality}
                  originalValue={originalData.surface_quality}
                  confidence={getConfidence("surface_quality")}
                  onChange={(v) => updateField("surface_quality", v ? parseInt(v) : undefined)}
                  type="number"
                  placeholder="1-5"
                />
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>
      
      {/* Acquisition */}
      <TabsContent value="acquisition">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Acquisition Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FieldWithConfidence
                label="Acquisition Date"
                field="acquisition_date"
                value={data.acquisition_date}
                originalValue={originalData.acquisition_date}
                confidence={getConfidence("acquisition_date")}
                onChange={(v) => updateField("acquisition_date", v)}
                type="text"
                placeholder="YYYY-MM-DD"
              />
              
              <FieldWithConfidence
                label="Price"
                field="acquisition_price"
                value={data.acquisition_price}
                originalValue={originalData.acquisition_price}
                confidence={getConfidence("acquisition_price")}
                onChange={(v) => updateField("acquisition_price", v ? parseFloat(v) : undefined)}
                type="number"
                placeholder="e.g., 150.00"
              />
              
              <FieldWithConfidence
                label="Source"
                field="acquisition_source"
                value={data.acquisition_source}
                originalValue={originalData.acquisition_source}
                confidence={getConfidence("acquisition_source")}
                onChange={(v) => updateField("acquisition_source", v)}
                placeholder="e.g., Heritage Auctions"
              />
              
              <FieldWithConfidence
                label="Storage Location"
                field="storage_location"
                value={data.storage_location}
                originalValue={originalData.storage_location}
                confidence={getConfidence("storage_location")}
                onChange={(v) => updateField("storage_location", v)}
                placeholder="e.g., SlabBox1"
              />
            </div>
            
            {/* Auction info if available */}
            {data.hammer_price && (
              <div className="border-t pt-4 mt-4">
                <h4 className="font-medium text-sm mb-3">Auction Result</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Hammer:</span>
                    <span className="ml-2 font-medium">
                      ${data.hammer_price?.toLocaleString()}
                    </span>
                  </div>
                  {data.total_price && (
                    <div>
                      <span className="text-muted-foreground">Total:</span>
                      <span className="ml-2 font-medium">
                        ${data.total_price?.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {data.auction_house && (
                    <div>
                      <span className="text-muted-foreground">House:</span>
                      <span className="ml-2">{data.auction_house}</span>
                    </div>
                  )}
                  {data.lot_number && (
                    <div>
                      <span className="text-muted-foreground">Lot:</span>
                      <span className="ml-2">{data.lot_number}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>
      
      {/* Notes */}
      <TabsContent value="notes">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Notes & Research</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label>Rarity</Label>
              <Select
                value={data.rarity || ""}
                onValueChange={(v) => updateField("rarity", v || undefined)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select rarity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="common">Common</SelectItem>
                  <SelectItem value="scarce">Scarce</SelectItem>
                  <SelectItem value="rare">Rare</SelectItem>
                  <SelectItem value="very_rare">Very Rare</SelectItem>
                  <SelectItem value="extremely_rare">Extremely Rare</SelectItem>
                  <SelectItem value="unique">Unique</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <FieldWithConfidence
              label="Historical Significance"
              field="historical_significance"
              value={data.historical_significance}
              originalValue={originalData.historical_significance}
              confidence={getConfidence("historical_significance")}
              onChange={(v) => updateField("historical_significance", v)}
              type="textarea"
              placeholder="Historical context and significance..."
            />
            
            <FieldWithConfidence
              label="Personal Notes"
              field="personal_notes"
              value={data.personal_notes}
              originalValue={originalData.personal_notes}
              confidence={getConfidence("personal_notes")}
              onChange={(v) => updateField("personal_notes", v)}
              type="textarea"
              placeholder="Your personal notes about this coin..."
            />
            
            {/* References */}
            {data.references && data.references.length > 0 && (
              <div className="space-y-1.5">
                <Label>Detected References</Label>
                <div className="flex flex-wrap gap-1.5">
                  {data.references.map((ref, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 bg-muted rounded text-sm"
                    >
                      {ref}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
