import { useState, useEffect } from "react";
import { Loader2, CheckCircle, XCircle, AlertCircle, Link2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  useScrapeUrl,
  useScrapeJobStatus,
  useDetectHouse,
  type ScrapeJobStatus,
} from "@/hooks/useAuctions";

interface ScrapeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  coinId?: number;
  referenceTypeId?: number;
  onComplete?: (result: ScrapeJobStatus) => void;
}

export function ScrapeDialog({
  open,
  onOpenChange,
  coinId,
  referenceTypeId,
  onComplete,
}: ScrapeDialogProps) {
  const [url, setUrl] = useState("");
  const [jobId, setJobId] = useState<string | undefined>();
  const [detectedHouse, setDetectedHouse] = useState<string | undefined>();

  const scrapeUrl = useScrapeUrl();
  const detectHouse = useDetectHouse();
  const { data: jobStatus, isLoading: isPolling } = useScrapeJobStatus(jobId);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setUrl("");
      setJobId(undefined);
      setDetectedHouse(undefined);
    }
  }, [open]);

  // Handle job completion
  useEffect(() => {
    if (jobStatus && (jobStatus.status === "completed" || jobStatus.status === "failed")) {
      onComplete?.(jobStatus);
    }
  }, [jobStatus, onComplete]);

  // Detect house when URL changes
  useEffect(() => {
    if (url && url.startsWith("http")) {
      const timeoutId = setTimeout(() => {
        detectHouse.mutate(url, {
          onSuccess: (data) => {
            setDetectedHouse(data.house || undefined);
          },
        });
      }, 500);
      return () => clearTimeout(timeoutId);
    } else {
      setDetectedHouse(undefined);
    }
  }, [url]);

  const handleScrape = async () => {
    if (!url) return;

    try {
      const result = await scrapeUrl.mutateAsync({
        url,
        coinId,
        referenceTypeId,
      });
      setJobId(result.job_id);
    } catch (error) {
      console.error("Scrape error:", error);
    }
  };

  const isProcessing = jobStatus?.status === "pending" || jobStatus?.status === "processing";
  const isComplete = jobStatus?.status === "completed";
  const isFailed = jobStatus?.status === "failed";

  const getStatusIcon = () => {
    if (isProcessing) return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />;
    if (isComplete) return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (isFailed) return <XCircle className="w-5 h-5 text-red-500" />;
    return null;
  };

  const getHouseBadgeColor = (house: string | undefined) => {
    if (!house) return "bg-gray-500/10 text-gray-700 dark:text-gray-400";
    const colors: Record<string, string> = {
      Heritage: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
      CNG: "bg-green-500/10 text-green-700 dark:text-green-400",
      Biddr: "bg-purple-500/10 text-purple-700 dark:text-purple-400",
      eBay: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400",
      Agora: "bg-red-500/10 text-red-700 dark:text-red-400",
    };
    return colors[house] || "bg-gray-500/10 text-gray-700 dark:text-gray-400";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Link2 className="w-5 h-5" />
            Scrape Auction URL
          </DialogTitle>
          <DialogDescription>
            Enter an auction URL from Heritage, CNG, Biddr, eBay, or Agora to extract lot data.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="https://coins.ha.com/itm/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isProcessing}
                className="flex-1"
              />
              {detectedHouse && (
                <Badge className={getHouseBadgeColor(detectedHouse)}>
                  {detectedHouse}
                </Badge>
              )}
            </div>
            {url && !detectedHouse && !detectHouse.isPending && (
              <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                URL not recognized. Supported: Heritage, CNG, Biddr, eBay, Agora
              </p>
            )}
          </div>

          {jobId && (
            <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Scraping Progress</span>
                {getStatusIcon()}
              </div>

              {isProcessing && (
                <Progress
                  value={
                    jobStatus
                      ? ((jobStatus.completed_urls + jobStatus.failed_urls) / jobStatus.total_urls) * 100
                      : 0
                  }
                  className="h-2"
                />
              )}

              {jobStatus?.results && jobStatus.results.length > 0 && (
                <div className="space-y-2">
                  {jobStatus.results.map((result, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 text-sm"
                    >
                      {result.status === "success" || result.status === "partial" ? (
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
                      )}
                      <div className="min-w-0">
                        {result.title ? (
                          <p className="truncate">{result.title}</p>
                        ) : (
                          <p className="text-muted-foreground truncate">{result.url}</p>
                        )}
                        {result.hammer_price !== undefined && result.hammer_price !== null && (
                          <p className="text-xs text-muted-foreground">
                            Hammer: ${result.hammer_price.toLocaleString()}
                            {result.sold === false && " (Unsold)"}
                          </p>
                        )}
                        {result.error_message && (
                          <p className="text-xs text-red-500">{result.error_message}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {isFailed && jobStatus?.error_message && (
                <p className="text-sm text-red-500">{jobStatus.error_message}</p>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {isComplete ? "Close" : "Cancel"}
          </Button>
          {!isComplete && (
            <Button
              onClick={handleScrape}
              disabled={!url || !detectedHouse || isProcessing || scrapeUrl.isPending}
            >
              {scrapeUrl.isPending || isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Scraping...
                </>
              ) : (
                "Scrape URL"
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ScrapeDialog;
