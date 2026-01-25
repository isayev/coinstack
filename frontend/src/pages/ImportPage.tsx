/**
 * ImportPage - Comprehensive coin import with multiple sources.
 * 
 * Features:
 * - Multiple import sources: File upload, Auction URL, NGC Certificate
 * - Preview and edit capabilities
 * - Duplicate detection with merge option
 * - Catalog enrichment integration
 * - Price history tracking
 * - Modern UI with design system
 */
import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  FileSpreadsheet,
  Link,
  Shield,
  CheckCircle2,
  Loader2,
  ArrowLeft,
  Upload,
  XCircle,
  ArrowRight,
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

import { URLImportPanel } from "@/components/import/URLImportPanel";
import { NGCImportPanel } from "@/components/import/NGCImportPanel";
import { DuplicateAlert } from "@/components/import/DuplicateAlert";
import { ImagePreviewGrid } from "@/components/import/ImagePreviewGrid";
import { CoinPreviewEditor } from "@/components/import/CoinPreviewEditor";
import { EnrichmentPanel } from "@/components/import/EnrichmentPanel";
import { BatchImportPanel } from "@/components/import/BatchImportPanel";

import {
  useImportConfirm,
  ImportPreviewResponse,
  CoinPreviewData,
  CoinImportConfirm,
  SOURCE_CONFIG,
} from "@/hooks/useImport";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

// Import types
type ImportStep = "source" | "preview" | "importing" | "complete";
type ImportSource = "file" | "url" | "ngc" | "batch";

interface ImportResult {
  imported: number;
  skipped: number;
  errors: Array<{ row: number; error: string }>;
  warnings: string[];
}

export function ImportPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // State
  const [step, setStep] = useState<ImportStep>("source");
  const [activeSource, setActiveSource] = useState<ImportSource>("url");
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const [editedCoinData, setEditedCoinData] = useState<CoinPreviewData | null>(null);
  const [mergeWithCoinId, setMergeWithCoinId] = useState<number | null>(null);
  const [trackPriceHistory, setTrackPriceHistory] = useState(true);
  const [importedCoinId, setImportedCoinId] = useState<number | null>(null);
  
  // File import state
  const [file, setFile] = useState<File | null>(null);
  const [fileImportResult, setFileImportResult] = useState<ImportResult | null>(null);
  const [isFileImporting, setIsFileImporting] = useState(false);
  
  // Mutations
  const confirmImport = useImportConfirm();
  
  // Handlers
  const handlePreviewReady = useCallback((data: ImportPreviewResponse) => {
    setPreviewData(data);
    setEditedCoinData(data.coin_data ? { ...data.coin_data } : null);
    setMergeWithCoinId(null);
    setStep("preview");
  }, []);
  
  const handleMerge = useCallback((coinId: number) => {
    setMergeWithCoinId(coinId);
    // Scroll to preview editor
    document.getElementById("preview-editor")?.scrollIntoView({ behavior: "smooth" });
  }, []);
  
  const handleImportAsNew = useCallback(() => {
    setMergeWithCoinId(null);
  }, []);
  
  const handleViewCoin = useCallback((coinId: number) => {
    // Open in new tab
    window.open(`/coins/${coinId}`, "_blank");
  }, []);
  
  const handleConfirmImport = async () => {
    if (!previewData || !editedCoinData) return;
    
    setStep("importing");
    
    try {
      const confirmData: CoinImportConfirm = {
        coin_data: editedCoinData,
        source_type: previewData.source_type || "manual",
        source_id: previewData.source_id,
        source_url: previewData.source_url,
        raw_data: previewData.raw_data,
        track_price_history: trackPriceHistory,
        sold_price_usd: editedCoinData.total_price || editedCoinData.hammer_price,
        auction_date: editedCoinData.auction_date,
        auction_house: editedCoinData.auction_house,
        lot_number: editedCoinData.lot_number,
        merge_with_coin_id: mergeWithCoinId ?? undefined,
      };
      
      const result = await confirmImport.mutateAsync(confirmData);
      
      if (result.success && result.coin_id) {
        setImportedCoinId(result.coin_id);
        setStep("complete");
        toast.success(
          result.merged 
            ? "Coin merged successfully!" 
            : "Coin imported successfully!"
        );
      } else {
        throw new Error(result.error || "Import failed");
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to import coin");
      setStep("preview");
    }
  };
  
  const handleReset = () => {
    setStep("source");
    setPreviewData(null);
    setEditedCoinData(null);
    setMergeWithCoinId(null);
    setImportedCoinId(null);
    setFile(null);
    setFileImportResult(null);
  };
  
  // File import handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };
  
  const handleFileImport = async (dryRun: boolean) => {
    if (!file) return;
    
    setIsFileImporting(true);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const { data } = await api.post<ImportResult>(
        `/api/import/collection?dry_run=${dryRun}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      
      setFileImportResult(data);
      
      if (!dryRun && data.imported > 0) {
        queryClient.invalidateQueries({ queryKey: ["coins"] });
        queryClient.invalidateQueries({ queryKey: ["stats"] });
        toast.success(`Successfully imported ${data.imported} coins!`);
      }
    } catch (error: any) {
      toast.error(error.message || "File import failed");
    } finally {
      setIsFileImporting(false);
    }
  };
  
  // Get source config for styling
  const sourceConfig = previewData?.source_type 
    ? SOURCE_CONFIG[previewData.source_type] 
    : null;
  
  return (
    <div className="min-h-screen" style={{ background: "var(--bg-base)" }}>
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-4 mb-2">
            {step !== "source" && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="gap-1"
              >
                <ArrowLeft className="h-4 w-4" />
                Start Over
              </Button>
            )}
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
              Import Coin
            </h1>
          </div>
          <p style={{ color: "var(--text-secondary)" }}>
            Add coins to your collection from auction listings, NGC certificates, or file upload
          </p>
        </div>
        
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-6">
          <Badge variant={step === "source" ? "default" : "secondary"}>
            1. Source
          </Badge>
          <ArrowRight className="w-4 h-4 text-muted-foreground" />
          <Badge variant={step === "preview" ? "default" : "secondary"}>
            2. Preview & Edit
          </Badge>
          <ArrowRight className="w-4 h-4 text-muted-foreground" />
          <Badge variant={step === "complete" || step === "importing" ? "default" : "secondary"}>
            3. Import
          </Badge>
        </div>
        
        {/* Source Selection Step */}
        {step === "source" && (
          <Tabs value={activeSource} onValueChange={(v) => setActiveSource(v as ImportSource)}>
            <TabsList className="grid w-full grid-cols-4 mb-6">
              <TabsTrigger value="url" className="gap-2">
                <Link className="h-4 w-4" />
                Single URL
              </TabsTrigger>
              <TabsTrigger value="batch" className="gap-2">
                <Link className="h-4 w-4" />
                Batch URLs
              </TabsTrigger>
              <TabsTrigger value="ngc" className="gap-2">
                <Shield className="h-4 w-4" />
                NGC Cert
              </TabsTrigger>
              <TabsTrigger value="file" className="gap-2">
                <FileSpreadsheet className="h-4 w-4" />
                File Upload
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="url">
              <URLImportPanel 
                onPreviewReady={handlePreviewReady}
                onManualEntry={() => navigate("/coins/new")}
              />
            </TabsContent>
            
            <TabsContent value="batch">
              <BatchImportPanel
                onSelectItem={(preview) => {
                  handlePreviewReady(preview);
                }}
                onBatchImport={async (items) => {
                  // For now, import items one by one
                  // TODO: Add proper batch confirm endpoint
                  for (const item of items) {
                    if (item.preview?.coin_data) {
                      handlePreviewReady(item.preview);
                      break; // Go to preview for first item
                    }
                  }
                }}
              />
            </TabsContent>
            
            <TabsContent value="ngc">
              <NGCImportPanel onPreviewReady={handlePreviewReady} />
            </TabsContent>
            
            <TabsContent value="file">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <FileSpreadsheet className="h-5 w-5" />
                    Import from File
                  </CardTitle>
                  <CardDescription>
                    Upload an Excel (.xlsx) or CSV file with your coin data
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* File input */}
                  <div
                    className={cn(
                      "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                      file 
                        ? "border-green-500 bg-green-500/5" 
                        : "border-muted-foreground/25 hover:border-primary/50"
                    )}
                    onClick={() => document.getElementById("file-input")?.click()}
                  >
                    <input
                      id="file-input"
                      type="file"
                      accept=".xlsx,.xls,.csv"
                      className="hidden"
                      onChange={handleFileChange}
                    />
                    {file ? (
                      <div className="space-y-2">
                        <FileSpreadsheet className="w-12 h-12 mx-auto text-green-500" />
                        <p className="font-medium">{file.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {(file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="w-12 h-12 mx-auto text-muted-foreground" />
                        <p className="font-medium">Drop your file here or click to browse</p>
                        <p className="text-sm text-muted-foreground">
                          Supports .xlsx, .xls, and .csv
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {/* File import actions */}
                  {file && (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setFile(null)}
                      >
                        Clear
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => handleFileImport(true)}
                        disabled={isFileImporting}
                      >
                        {isFileImporting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                        Preview
                      </Button>
                      {fileImportResult && fileImportResult.imported > 0 && (
                        <Button
                          onClick={() => handleFileImport(false)}
                          disabled={isFileImporting}
                        >
                          Import {fileImportResult.imported} Coins
                        </Button>
                      )}
                    </div>
                  )}
                  
                  {/* File preview result */}
                  {fileImportResult && (
                    <div className="grid grid-cols-3 gap-4 pt-4">
                      <div className="p-4 bg-green-500/10 rounded-lg text-center">
                        <CheckCircle2 className="w-6 h-6 mx-auto mb-2 text-green-500" />
                        <div className="text-2xl font-bold text-green-600">
                          {fileImportResult.imported}
                        </div>
                        <div className="text-sm text-muted-foreground">Ready</div>
                      </div>
                      <div className="p-4 bg-yellow-500/10 rounded-lg text-center">
                        <div className="text-2xl font-bold text-yellow-600">
                          {fileImportResult.skipped}
                        </div>
                        <div className="text-sm text-muted-foreground">Skipped</div>
                      </div>
                      <div className="p-4 bg-red-500/10 rounded-lg text-center">
                        <XCircle className="w-6 h-6 mx-auto mb-2 text-red-500" />
                        <div className="text-2xl font-bold text-red-600">
                          {fileImportResult.errors.length}
                        </div>
                        <div className="text-sm text-muted-foreground">Errors</div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
        
        {/* Preview Step */}
        {step === "preview" && previewData && editedCoinData && (
          <div className="space-y-6">
            {/* Source badge */}
            {sourceConfig && (
              <Badge
                variant="outline"
                className={cn(
                  "text-sm py-1",
                  sourceConfig.color,
                  sourceConfig.bgColor,
                  sourceConfig.borderColor
                )}
              >
                Imported from {sourceConfig.label}
                {previewData.source_id && ` #${previewData.source_id}`}
              </Badge>
            )}
            
            {/* Duplicate alert */}
            {previewData.similar_coins.length > 0 && (
              <DuplicateAlert
                similarCoins={previewData.similar_coins}
                onMerge={handleMerge}
                onImportAsNew={handleImportAsNew}
                onViewCoin={handleViewCoin}
              />
            )}
            
            {/* Merge indicator */}
            {mergeWithCoinId && (
              <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge className="bg-blue-500">Merge Mode</Badge>
                  <span className="text-sm">
                    This data will be merged with coin #{mergeWithCoinId}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setMergeWithCoinId(null)}
                >
                  Cancel Merge
                </Button>
              </div>
            )}
            
            {/* Two-column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left: Images */}
              <div className="space-y-6">
                <ImagePreviewGrid
                  images={editedCoinData.images}
                  onImagesChange={(images) =>
                    setEditedCoinData({ ...editedCoinData, images })
                  }
                />
                
                {/* Enrichment section */}
                {previewData.detected_references.length > 0 && (
                  <EnrichmentPanel
                    references={previewData.detected_references}
                    currentData={editedCoinData}
                    onApplyEnrichment={(updates) => {
                      setEditedCoinData({ ...editedCoinData, ...updates });
                    }}
                  />
                )}
                
                {/* Price tracking option */}
                {editedCoinData.hammer_price && (
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="track-price"
                          checked={trackPriceHistory}
                          onCheckedChange={(checked) =>
                            setTrackPriceHistory(checked as boolean)
                          }
                        />
                        <Label htmlFor="track-price" className="text-sm">
                          Add auction result to price history
                        </Label>
                      </div>
                      {trackPriceHistory && (
                        <p className="text-xs text-muted-foreground mt-2 ml-6">
                          ${editedCoinData.total_price?.toLocaleString() || 
                            editedCoinData.hammer_price?.toLocaleString()} from{" "}
                          {editedCoinData.auction_house} will be recorded
                        </p>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>
              
              {/* Right: Editor */}
              <div id="preview-editor">
                <CoinPreviewEditor
                  data={editedCoinData}
                  originalData={previewData.coin_data!}
                  fieldConfidence={previewData.field_confidence}
                  onChange={setEditedCoinData}
                />
              </div>
            </div>
            
            {/* Action buttons */}
            <Separator className="my-6" />
            <div className="flex justify-between">
              <Button variant="outline" onClick={handleReset}>
                Cancel
              </Button>
              <Button
                onClick={handleConfirmImport}
                disabled={confirmImport.isPending}
              >
                {confirmImport.isPending && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                {mergeWithCoinId ? "Merge & Import" : "Import Coin"}
              </Button>
            </div>
          </div>
        )}
        
        {/* Importing Step */}
        {step === "importing" && (
          <Card>
            <CardContent className="py-12 text-center">
              <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary" />
              <p className="font-medium">
                {mergeWithCoinId ? "Merging coin data..." : "Importing your coin..."}
              </p>
              <p className="text-sm text-muted-foreground">This may take a moment</p>
            </CardContent>
          </Card>
        )}
        
        {/* Complete Step */}
        {step === "complete" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle2 className="w-6 h-6" />
                Import Complete!
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-muted-foreground">
                {mergeWithCoinId
                  ? "Your coin has been successfully merged with the existing record."
                  : "Your coin has been successfully added to your collection."}
              </p>
              
              <div className="flex gap-4">
                <Button variant="outline" onClick={handleReset}>
                  Import Another
                </Button>
                {importedCoinId && (
                  <Button onClick={() => navigate(`/coins/${importedCoinId}`)}>
                    View Coin
                  </Button>
                )}
                <Button variant="secondary" onClick={() => navigate("/")}>
                  Go to Collection
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Help text */}
        {step === "source" && (
          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h4 className="font-medium mb-2">Import Tips</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>
                <strong>Auction URL:</strong> Paste a link from Heritage, CNG, eBay, or other supported sites
              </li>
              <li>
                <strong>NGC Certificate:</strong> Enter the 7-10 digit certification number from an NGC slab
              </li>
              <li>
                <strong>File Upload:</strong> Use for bulk imports with your own spreadsheet data
              </li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
