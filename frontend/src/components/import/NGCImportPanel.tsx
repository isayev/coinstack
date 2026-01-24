/**
 * NGCImportPanel - Import from NGC Ancients certificate lookup.
 * 
 * Features:
 * - Certificate number validation (7-10 digits)
 * - Loading skeleton
 * - Error states with retry
 * - NGC branding
 */
import { useState, useEffect } from "react";
import { Shield, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useNgcImport, ImportPreviewResponse } from "@/hooks/useImport";
import { cn } from "@/lib/utils";

interface NGCImportPanelProps {
  onPreviewReady: (data: ImportPreviewResponse) => void;
}

export function NGCImportPanel({ onPreviewReady }: NGCImportPanelProps) {
  const [certNumber, setCertNumber] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [retryCountdown, setRetryCountdown] = useState(0);
  
  const { mutate: fetchNgc, isPending, error, data, reset } = useNgcImport();
  
  // Validate certificate format
  const validateCert = (value: string): boolean => {
    const cleaned = value.replace(/\D/g, "");
    if (cleaned.length === 0) {
      setValidationError(null);
      return false;
    }
    if (cleaned.length < 7) {
      setValidationError("Certificate number must be at least 7 digits");
      return false;
    }
    if (cleaned.length > 10) {
      setValidationError("Certificate number must be at most 10 digits");
      return false;
    }
    setValidationError(null);
    return true;
  };
  
  const isValidCert = certNumber.length >= 7 && certNumber.length <= 10 && !validationError;
  
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
  
  const handleInputChange = (value: string) => {
    // Only allow digits
    const cleaned = value.replace(/\D/g, "");
    setCertNumber(cleaned);
    validateCert(cleaned);
    if (error) reset();
  };
  
  const handleFetch = () => {
    if (isValidCert) {
      reset();
      fetchNgc(certNumber);
    }
  };
  
  const handleRetry = () => {
    reset();
    fetchNgc(certNumber);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Shield className="h-5 w-5 text-red-500" />
          Import from NGC Certificate
        </CardTitle>
        <CardDescription>
          Enter an NGC Ancients certification number to fetch coin data and images
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Certificate Input */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Input
              placeholder="e.g., 4938475"
              value={certNumber}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && isValidCert && !isPending) {
                  handleFetch();
                }
              }}
              className={cn(
                "font-mono",
                validationError && "border-destructive focus-visible:ring-destructive"
              )}
              maxLength={10}
            />
            {isValidCert && !isPending && !error && (
              <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-green-500" />
            )}
          </div>
          <Button
            onClick={handleFetch}
            disabled={!isValidCert || isPending || retryCountdown > 0}
            className="bg-red-600 hover:bg-red-700"
          >
            {isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Lookup"
            )}
          </Button>
        </div>
        
        {/* Validation Error */}
        {validationError && (
          <p className="text-sm text-destructive">{validationError}</p>
        )}
        
        {/* Valid Badge */}
        {isValidCert && !isPending && !error && (
          <Badge
            variant="outline"
            className="gap-1.5 text-red-500 bg-red-500/10 border-red-500/30"
          >
            <Shield className="h-3 w-3" />
            NGC Ancients Certificate
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
              Looking up NGC certificate...
            </div>
          </div>
        )}
        
        {/* Error State */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Lookup Failed</AlertTitle>
            <AlertDescription className="mt-1">
              {error.message}
            </AlertDescription>
            <div className="flex gap-2 mt-3">
              <Button
                size="sm"
                variant="outline"
                onClick={handleRetry}
                disabled={retryCountdown > 0}
              >
                {retryCountdown > 0 ? `Retry (${retryCountdown}s)` : "Try Again"}
              </Button>
            </div>
          </Alert>
        )}
        
        {/* Info */}
        {!isPending && !error && !data && (
          <div className="text-xs text-muted-foreground space-y-1">
            <p>
              The certificate number is found on the NGC slab label, typically 7-10 digits.
            </p>
            <p>
              Data includes: grade, strike/surface scores, PhotoVision images, and coin description.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
