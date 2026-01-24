/**
 * URLImportPanel - Import from auction URL with auto-detection and error handling.
 * 
 * Features:
 * - Auto-paste detection and fetch trigger
 * - Source detection badge (Heritage, CNG, eBay, etc.)
 * - Loading skeleton
 * - Error states with retry countdown
 * - Manual entry fallback
 */
import { useState, useEffect, useMemo, ClipboardEvent } from "react";
import { Link, Loader2, AlertCircle, ExternalLink, Clipboard } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  useUrlImport, 
  detectAuctionSource, 
  SOURCE_CONFIG,
  ImportPreviewResponse,
  ImportError,
} from "@/hooks/useImport";
import { cn } from "@/lib/utils";

interface URLImportPanelProps {
  onPreviewReady: (data: ImportPreviewResponse) => void;
  onManualEntry?: () => void;
}

export function URLImportPanel({ onPreviewReady, onManualEntry }: URLImportPanelProps) {
  const [url, setUrl] = useState("");
  const [retryCountdown, setRetryCountdown] = useState(0);
  
  const { mutate: fetchUrl, isPending, error, data, reset } = useUrlImport();
  
  // Detect source from URL
  const detectedSource = useMemo(() => detectAuctionSource(url), [url]);
  const sourceConfig = detectedSource ? SOURCE_CONFIG[detectedSource] : null;
  
  // Handle successful fetch
  useEffect(() => {
    if (data?.success) {
      onPreviewReady(data);
    }
  }, [data, onPreviewReady]);
  
  // Countdown timer for rate limit retry
  useEffect(() => {
    if (error?.retryAfter) {
      setRetryCountdown(error.retryAfter);
      const interval = setInterval(() => {
        setRetryCountdown((c) => {
          if (c <= 1) {
            clearInterval(interval);
            return 0;
          }
          return c - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [error?.retryAfter]);
  
  // Auto-trigger on paste
  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    const pastedText = e.clipboardData?.getData("text");
    if (pastedText) {
      const trimmed = pastedText.trim();
      // Check if it looks like a URL
      if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
        setUrl(trimmed);
        reset();
        // Auto-fetch after a short delay to allow state to update
        setTimeout(() => {
          fetchUrl(trimmed);
        }, 100);
      }
    }
  };
  
  const handleFetch = () => {
    if (url) {
      reset();
      fetchUrl(url);
    }
  };
  
  const handleRetry = () => {
    reset();
    fetchUrl(url);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Link className="h-5 w-5" />
          Import from Auction URL
        </CardTitle>
        <CardDescription>
          Paste a listing URL from Heritage, CNG, eBay, Biddr, Roma, or Agora
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* URL Input */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Input
              placeholder="https://coins.ha.com/itm/..."
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                if (error) reset();
              }}
              onPaste={handlePaste}
              onKeyDown={(e) => {
                if (e.key === "Enter" && url && !isPending) {
                  handleFetch();
                }
              }}
              className="pr-10"
            />
            {url && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                onClick={() => {
                  setUrl("");
                  reset();
                }}
              >
                <span className="sr-only">Clear</span>
                ×
              </Button>
            )}
          </div>
          <Button
            onClick={handleFetch}
            disabled={!url || isPending || retryCountdown > 0}
          >
            {isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Fetch"
            )}
          </Button>
        </div>
        
        {/* Source Detection Badge */}
        {detectedSource && !isPending && !error && sourceConfig && (
          <Badge
            variant="outline"
            className={cn(
              "gap-1.5",
              sourceConfig.color,
              sourceConfig.bgColor,
              sourceConfig.borderColor
            )}
          >
            <ExternalLink className="h-3 w-3" />
            {sourceConfig.label} detected
          </Badge>
        )}
        
        {/* Loading State */}
        {isPending && (
          <div className="space-y-3">
            <div className="flex gap-3">
              <Skeleton className="h-24 w-24 rounded-lg" />
              <Skeleton className="h-24 w-24 rounded-lg" />
            </div>
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Fetching from {sourceConfig?.label || "auction site"}...
            </div>
          </div>
        )}
        
        {/* Error State */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Import Failed</AlertTitle>
            <AlertDescription className="mt-1">
              {error.message}
            </AlertDescription>
            <div className="flex gap-2 mt-3">
              {error.retryAfter && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleRetry}
                  disabled={retryCountdown > 0}
                >
                  {retryCountdown > 0 ? `Retry (${retryCountdown}s)` : "Retry"}
                </Button>
              )}
              {!error.retryAfter && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleRetry}
                >
                  Try Again
                </Button>
              )}
              {error.manualEntrySuggested && onManualEntry && (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={onManualEntry}
                >
                  Enter Manually
                </Button>
              )}
            </div>
          </Alert>
        )}
        
        {/* Supported Sources Info */}
        {!isPending && !error && !data && (
          <div className="text-xs text-muted-foreground">
            <p className="font-medium mb-1">Supported auction houses:</p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(SOURCE_CONFIG)
                .filter(([key]) => key !== "ngc")
                .map(([key, config]) => (
                  <Badge
                    key={key}
                    variant="outline"
                    className={cn(
                      "text-xs py-0",
                      config.color,
                      config.bgColor,
                      config.borderColor
                    )}
                  >
                    {config.label}
                  </Badge>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
