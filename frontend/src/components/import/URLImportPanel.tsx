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
import { Link, Loader2, AlertCircle, ExternalLink } from "lucide-react";
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
    if (data) {
      console.log("Mutation data received:", data);
      if (data.success) {
        onPreviewReady(data);
      } else {
        // Even if success is false, we might want to show the error
        console.log("Data received but success is false:", data.error);
      }
    }
  }, [data, onPreviewReady]);

  // Log errors for debugging
  useEffect(() => {
    if (error) {
      console.error("URL import error:", error);
    }
  }, [error]);

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
    console.log("Paste detected:", pastedText);
    if (pastedText) {
      const trimmed = pastedText.trim();
      // Check if it looks like a URL
      if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
        // Prevent default paste to avoid double-paste
        e.preventDefault();
        console.log("Setting URL from paste:", trimmed);
        setUrl(trimmed);
        reset();
        // Auto-fetch after a short delay to allow state to update
        setTimeout(() => {
          console.log("Auto-fetching after paste");
          if (trimmed) {
            fetchUrl(trimmed);
          }
        }, 100);
      } else {
        console.log("Pasted text doesn't look like a URL");
      }
    }
  };

  const handleFetch = () => {
    console.log("handleFetch called, url:", url, "url length:", url?.length);
    if (url && url.trim()) {
      console.log("Calling fetchUrl with:", url.trim());
      reset();
      // Just call mutate - errors will be in the error state
      fetchUrl(url.trim());
    } else {
      console.warn("handleFetch called but URL is empty or invalid");
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
                const newUrl = e.target.value;
                console.log("URL input changed:", newUrl);
                setUrl(newUrl);
                if (error) reset();
              }}
              onPaste={handlePaste}
              onKeyDown={(e) => {
                if (e.key === "Enter" && url && !isPending) {
                  console.log("Enter key pressed, triggering fetch");
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
                  console.log("Clear button clicked");
                  setUrl("");
                  reset();
                }}
              >
                <span className="sr-only">Clear</span>
                ×
              </Button>
            )}
          </div>
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log("=== FETCH BUTTON CLICKED ===");
              console.log("URL value:", url);
              console.log("URL length:", url?.length);
              console.log("isPending:", isPending);
              console.log("retryCountdown:", retryCountdown);
              console.log("Button disabled?", !url || isPending || retryCountdown > 0);
              if (!url || isPending || retryCountdown > 0) {
                console.warn("Button is disabled, cannot fetch");
                alert(`Button disabled: url=${!!url}, isPending=${isPending}, retryCountdown=${retryCountdown}`);
                return;
              }
              console.log("Calling handleFetch...");
              handleFetch();
            }}
            disabled={!url || isPending || retryCountdown > 0}
            type="button"
            className={cn(
              "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
              "h-10 px-4 py-2",
              "bg-primary text-primary-foreground hover:bg-primary/90",
              "min-w-[80px]",
              (!url || isPending || retryCountdown > 0) && "opacity-50 cursor-not-allowed"
            )}
          >
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Fetching...
              </>
            ) : (
              "Fetch"
            )}
          </button>
        </div>
        
        {/* Debug info - remove in production */}
        {process.env.NODE_ENV === 'development' && (
          <div className="text-xs text-muted-foreground p-2 bg-muted rounded">
            <div>URL: {url || "(empty)"}</div>
            <div>isPending: {String(isPending)}</div>
            <div>retryCountdown: {retryCountdown}</div>
            <div>Button disabled: {String(!url || isPending || retryCountdown > 0)}</div>
          </div>
        )}

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
