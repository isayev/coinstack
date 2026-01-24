import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { 
  Upload, FileSpreadsheet, CheckCircle2, AlertCircle, 
  XCircle, Loader2, ArrowRight, RefreshCw
} from "lucide-react";

interface ImportResult {
  imported: number;
  skipped: number;
  errors: Array<{ row: number; error: string }>;
  warnings: string[];
}

type ImportStep = "upload" | "preview" | "importing" | "complete";

export function ImportPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [step, setStep] = useState<ImportStep>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [previewResult, setPreviewResult] = useState<ImportResult | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
      setPreviewResult(null);
      setImportResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
      "text/csv": [".csv"],
    },
    maxFiles: 1,
  });

  const handlePreview = async () => {
    if (!file) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await api.post<ImportResult>(
        "/api/import/collection?dry_run=true",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      
      setPreviewResult(response.data);
      setStep("preview");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to preview file");
      toast.error("Preview failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;
    
    setIsLoading(true);
    setStep("importing");
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await api.post<ImportResult>(
        "/api/import/collection?dry_run=false",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      
      setImportResult(response.data);
      setStep("complete");
      
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ["coins"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.invalidateQueries({ queryKey: ["database-info"] });
      
      toast.success(`Successfully imported ${response.data.imported} coins!`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Import failed");
      setStep("preview");
      toast.error("Import failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setStep("upload");
    setFile(null);
    setPreviewResult(null);
    setImportResult(null);
    setError(null);
  };

  return (
    <div className="container mx-auto p-6 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Import Collection</h1>
        <p className="text-muted-foreground">
          Import coins from an Excel (.xlsx) or CSV file
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6">
        <Badge variant={step === "upload" ? "default" : "secondary"}>1. Upload</Badge>
        <ArrowRight className="w-4 h-4 text-muted-foreground" />
        <Badge variant={step === "preview" ? "default" : "secondary"}>2. Preview</Badge>
        <ArrowRight className="w-4 h-4 text-muted-foreground" />
        <Badge variant={step === "complete" || step === "importing" ? "default" : "secondary"}>
          3. Import
        </Badge>
      </div>

      {/* Upload Step */}
      {step === "upload" && (
        <Card>
          <CardHeader>
            <CardTitle>Select File</CardTitle>
            <CardDescription>
              Upload your collection spreadsheet. Supported formats: Excel (.xlsx, .xls) and CSV.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                transition-colors
                ${isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"}
                ${file ? "border-green-500 bg-green-500/5" : ""}
              `}
            >
              <input {...getInputProps()} />
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
                  <p className="font-medium">
                    {isDragActive ? "Drop the file here" : "Drag & drop your file here"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    or click to browse
                  </p>
                </div>
              )}
            </div>

            {error && (
              <div className="flex items-center gap-2 text-destructive">
                <XCircle className="w-4 h-4" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <div className="flex justify-end gap-2">
              {file && (
                <Button variant="outline" onClick={() => setFile(null)}>
                  Clear
                </Button>
              )}
              <Button onClick={handlePreview} disabled={!file || isLoading}>
                {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Preview Import
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview Step */}
      {step === "preview" && previewResult && (
        <Card>
          <CardHeader>
            <CardTitle>Preview Results</CardTitle>
            <CardDescription>
              Review what will be imported before confirming
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-green-500/10 rounded-lg text-center">
                <CheckCircle2 className="w-6 h-6 mx-auto mb-2 text-green-500" />
                <div className="text-2xl font-bold text-green-600">{previewResult.imported}</div>
                <div className="text-sm text-muted-foreground">Ready to import</div>
              </div>
              <div className="p-4 bg-yellow-500/10 rounded-lg text-center">
                <AlertCircle className="w-6 h-6 mx-auto mb-2 text-yellow-500" />
                <div className="text-2xl font-bold text-yellow-600">{previewResult.skipped}</div>
                <div className="text-sm text-muted-foreground">Skipped</div>
              </div>
              <div className="p-4 bg-red-500/10 rounded-lg text-center">
                <XCircle className="w-6 h-6 mx-auto mb-2 text-red-500" />
                <div className="text-2xl font-bold text-red-600">{previewResult.errors.length}</div>
                <div className="text-sm text-muted-foreground">Errors</div>
              </div>
            </div>

            {/* Errors */}
            {previewResult.errors.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium text-destructive">Errors</h4>
                <div className="max-h-40 overflow-auto space-y-1 text-sm">
                  {previewResult.errors.slice(0, 10).map((err, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-muted-foreground">Row {err.row}:</span>
                      <span>{err.error}</span>
                    </div>
                  ))}
                  {previewResult.errors.length > 10 && (
                    <div className="text-muted-foreground">
                      ... and {previewResult.errors.length - 10} more errors
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Warnings */}
            {previewResult.warnings.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium text-yellow-600">Warnings</h4>
                <div className="max-h-40 overflow-auto space-y-1 text-sm text-muted-foreground">
                  {previewResult.warnings
                    .filter(w => !w.includes("Dry run"))
                    .slice(0, 10)
                    .map((warning, i) => (
                      <div key={i}>{warning}</div>
                    ))}
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 text-destructive">
                <XCircle className="w-4 h-4" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <div className="flex justify-between">
              <Button variant="outline" onClick={handleReset}>
                Start Over
              </Button>
              <Button 
                onClick={handleImport} 
                disabled={previewResult.imported === 0 || isLoading}
              >
                {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Import {previewResult.imported} Coins
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Importing Step */}
      {step === "importing" && (
        <Card>
          <CardContent className="py-12 text-center">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-primary" />
            <p className="font-medium">Importing your collection...</p>
            <p className="text-sm text-muted-foreground">This may take a moment</p>
          </CardContent>
        </Card>
      )}

      {/* Complete Step */}
      {step === "complete" && importResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-600">
              <CheckCircle2 className="w-6 h-6" />
              Import Complete!
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-green-500/10 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">{importResult.imported}</div>
                <div className="text-sm text-muted-foreground">Imported</div>
              </div>
              <div className="p-4 bg-yellow-500/10 rounded-lg text-center">
                <div className="text-2xl font-bold text-yellow-600">{importResult.skipped}</div>
                <div className="text-sm text-muted-foreground">Skipped</div>
              </div>
              <div className="p-4 bg-red-500/10 rounded-lg text-center">
                <div className="text-2xl font-bold text-red-600">{importResult.errors.length}</div>
                <div className="text-sm text-muted-foreground">Errors</div>
              </div>
            </div>

            {importResult.errors.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium text-destructive">Errors during import</h4>
                <div className="max-h-40 overflow-auto space-y-1 text-sm">
                  {importResult.errors.map((err, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-muted-foreground">Row {err.row}:</span>
                      <span>{err.error}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-between">
              <Button variant="outline" onClick={handleReset}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Import More
              </Button>
              <Button onClick={() => navigate("/")}>
                View Collection
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Help text */}
      <div className="mt-6 p-4 bg-muted rounded-lg">
        <h4 className="font-medium mb-2">Expected File Format</h4>
        <p className="text-sm text-muted-foreground">
          Your spreadsheet should have columns for coin data such as: Ruler, Denomination, 
          Metal, Category, Obverse, Reverse, Grade, Price, etc. The importer will 
          automatically map common column names to the appropriate fields.
        </p>
      </div>
    </div>
  );
}
