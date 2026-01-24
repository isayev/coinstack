import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  useBulkEnrich, 
  useJobStatus, 
  BulkEnrichResponse 
} from "@/hooks/useCatalog";
import { 
  Sparkles, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  ArrowLeft,
  RefreshCw
} from "lucide-react";

interface FilterPreset {
  id: string;
  label: string;
  description: string;
  filter: {
    missing_fields?: string[];
    reference_system?: string;
    category?: string;
  };
}

const FILTER_PRESETS: FilterPreset[] = [
  {
    id: "ric-no-ocre",
    label: "RIC without OCRE link",
    description: "Coins with RIC references that haven't been looked up yet",
    filter: {
      reference_system: "ric",
    },
  },
  {
    id: "missing-mint-date",
    label: "Missing mint or date",
    description: "Coins without mint location or minting date",
    filter: {
      missing_fields: ["mint_name", "mint_year_start"],
    },
  },
  {
    id: "missing-legends",
    label: "Missing legends",
    description: "Coins without obverse or reverse legend text",
    filter: {
      missing_fields: ["obverse_legend", "reverse_legend"],
    },
  },
  {
    id: "republic",
    label: "Republic coins",
    description: "All Roman Republic coins",
    filter: {
      category: "republic",
    },
  },
  {
    id: "imperial",
    label: "Imperial coins",
    description: "All Roman Imperial coins",
    filter: {
      category: "imperial",
    },
  },
];

export function BulkEnrichPage() {
  const navigate = useNavigate();
  const [selectedPreset, setSelectedPreset] = useState<FilterPreset | null>(null);
  const [jobResponse, setJobResponse] = useState<BulkEnrichResponse | null>(null);
  const [dryRun, setDryRun] = useState(true);
  
  const [pollingEnabled, setPollingEnabled] = useState(false);
  
  const bulkEnrichMutation = useBulkEnrich();
  const { data: jobStatus } = useJobStatus(
    jobResponse?.job_id || null,
    { refetchInterval: pollingEnabled ? 2000 : undefined }
  );
  
  // Stop polling when job completes
  useEffect(() => {
    if (jobStatus && (jobStatus.status === "completed" || jobStatus.status === "failed")) {
      setPollingEnabled(false);
    }
  }, [jobStatus?.status]);
  
  const handleStartEnrichment = async () => {
    if (!selectedPreset) return;
    
    const result = await bulkEnrichMutation.mutateAsync({
      ...selectedPreset.filter,
      dry_run: dryRun,
      max_coins: 50,
    });
    
    setJobResponse(result);
    if (result.job_id) {
      setPollingEnabled(true);
    }
  };
  
  const progress = jobStatus 
    ? Math.round((jobStatus.progress / jobStatus.total) * 100) 
    : 0;
  
  return (
    <div className="container max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Bulk Catalog Enrichment</h1>
          <p className="text-muted-foreground">
            Enrich multiple coins from OCRE/CRRO catalogs
          </p>
        </div>
      </div>
      
      {/* Filter presets */}
      {!jobResponse && (
        <div className="space-y-4 mb-8">
          <h2 className="text-lg font-semibold">Select Filter</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {FILTER_PRESETS.map((preset) => (
              <Card
                key={preset.id}
                className={`cursor-pointer transition-colors ${
                  selectedPreset?.id === preset.id
                    ? "border-primary bg-primary/5"
                    : "hover:border-muted-foreground/50"
                }`}
                onClick={() => setSelectedPreset(preset)}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{preset.label}</CardTitle>
                  <CardDescription>{preset.description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      )}
      
      {/* Options */}
      {!jobResponse && selectedPreset && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span>Preview only (don't save changes)</span>
              </label>
            </div>
            
            <Button
              onClick={handleStartEnrichment}
              disabled={bulkEnrichMutation.isPending}
              className="w-full"
            >
              {bulkEnrichMutation.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4 mr-2" />
              )}
              Start Enrichment
            </Button>
          </CardContent>
        </Card>
      )}
      
      {/* Progress */}
      {jobResponse && jobStatus && (
        <div className="space-y-6">
          {/* Status card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {jobStatus.status === "running" && (
                  <Loader2 className="w-5 h-5 animate-spin" />
                )}
                {jobStatus.status === "completed" && (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                )}
                {jobStatus.status === "failed" && (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                {jobStatus.status === "queued" && (
                  <RefreshCw className="w-5 h-5" />
                )}
                
                {jobStatus.status === "running" && "Processing..."}
                {jobStatus.status === "completed" && "Completed"}
                {jobStatus.status === "failed" && "Failed"}
                {jobStatus.status === "queued" && "Queued"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Progress bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span>{jobStatus.progress} / {jobStatus.total} coins</span>
                </div>
                <Progress value={progress} />
              </div>
              
              {/* Stats */}
              <div className="grid grid-cols-4 gap-4 pt-4">
                <div className="text-center p-3 rounded-lg bg-green-50 dark:bg-green-950">
                  <div className="text-2xl font-bold text-green-600">{jobStatus.updated}</div>
                  <div className="text-sm text-muted-foreground">Updated</div>
                </div>
                <div className="text-center p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950">
                  <div className="text-2xl font-bold text-yellow-600">{jobStatus.conflicts}</div>
                  <div className="text-sm text-muted-foreground">Conflicts</div>
                </div>
                <div className="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
                  <div className="text-2xl font-bold text-muted-foreground">{jobStatus.not_found}</div>
                  <div className="text-sm text-muted-foreground">Not Found</div>
                </div>
                <div className="text-center p-3 rounded-lg bg-red-50 dark:bg-red-950">
                  <div className="text-2xl font-bold text-red-600">{jobStatus.errors}</div>
                  <div className="text-sm text-muted-foreground">Errors</div>
                </div>
              </div>
              
              {/* Error message */}
              {jobStatus.error_message && (
                <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950 text-red-600">
                  {jobStatus.error_message}
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Recent results */}
          {jobStatus.results && jobStatus.results.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {jobStatus.results.map((result, i) => (
                    <div 
                      key={i}
                      className="flex items-center justify-between p-2 rounded border"
                    >
                      <span>Coin #{result.coin_id}</span>
                      <Badge
                        variant={
                          result.status === "success" ? "default" :
                          result.status === "error" ? "destructive" :
                          "secondary"
                        }
                      >
                        {result.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Actions */}
          {jobStatus.status === "completed" && (
            <div className="flex gap-4">
              <Button
                variant="outline"
                onClick={() => {
                  setJobResponse(null);
                  setSelectedPreset(null);
                }}
              >
                Start Over
              </Button>
              <Button onClick={() => navigate("/")}>
                View Collection
              </Button>
              {jobStatus.conflicts > 0 && (
                <Button variant="secondary">
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Review {jobStatus.conflicts} Conflicts
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
