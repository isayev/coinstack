/**
 * CertLookupPopover - Popover for NGC/PCGS certificate lookup
 * 
 * Allows users to look up graded coin certificates by number
 * and potentially import the data into their collection.
 */

import { useState, ReactNode } from "react";
import { Loader2, ExternalLink, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface CertLookupPopoverProps {
  children: ReactNode;
}

// NGC and PCGS verification URLs
const CERT_URLS = {
  NGC: (certNumber: string) => 
    `https://www.ngccoin.com/certlookup/${certNumber}/`,
  PCGS: (certNumber: string) => 
    `https://www.pcgs.com/cert/${certNumber}`,
};

export function CertLookupPopover({ children }: CertLookupPopoverProps) {
  const [open, setOpen] = useState(false);
  const [service, setService] = useState<"NGC" | "PCGS">("NGC");
  const [certNumber, setCertNumber] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (!certNumber.trim()) return;
    
    setIsLoading(true);
    
    // Open the verification URL in a new tab
    const url = CERT_URLS[service](certNumber.trim());
    window.open(url, "_blank", "noopener,noreferrer");
    
    // Reset after a short delay
    setTimeout(() => {
      setIsLoading(false);
    }, 500);
  };

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
    if (!newOpen) {
      setCertNumber("");
    }
  };

  // Format cert number as user types (NGC format: XXXXXXX-XXX)
  const handleCertNumberChange = (value: string) => {
    // Remove non-alphanumeric characters except hyphens
    const cleaned = value.replace(/[^a-zA-Z0-9-]/g, "");
    setCertNumber(cleaned);
  };

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        {children}
      </PopoverTrigger>
      <PopoverContent 
        className="w-80" 
        align="start"
        style={{
          background: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)'
        }}
      >
        <form onSubmit={handleLookup}>
          <div className="space-y-4">
            <div className="space-y-2">
              <h4 
                className="font-medium leading-none"
                style={{ color: 'var(--text-primary)' }}
              >
                Certificate Lookup
              </h4>
              <p 
                className="text-sm"
                style={{ color: 'var(--text-muted)' }}
              >
                Verify NGC or PCGS certification
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Grading Service</Label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setService("NGC")}
                  className={cn(
                    "flex-1 transition-all",
                    service === "NGC" && "ring-2"
                  )}
                  style={{
                    background: service === "NGC" ? "var(--cert-ngc)" : "var(--bg-elevated)",
                    color: service === "NGC" ? "#fff" : "var(--text-muted)",
                    borderColor: service === "NGC" ? "var(--cert-ngc)" : "var(--border-subtle)",
                    ringColor: "var(--cert-ngc)"
                  }}
                >
                  NGC
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setService("PCGS")}
                  className={cn(
                    "flex-1 transition-all",
                    service === "PCGS" && "ring-2"
                  )}
                  style={{
                    background: service === "PCGS" ? "var(--cert-pcgs)" : "var(--bg-elevated)",
                    color: service === "PCGS" ? "#fff" : "var(--text-muted)",
                    borderColor: service === "PCGS" ? "var(--cert-pcgs)" : "var(--border-subtle)",
                    ringColor: "var(--cert-pcgs)"
                  }}
                >
                  PCGS
                </Button>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="cert-number">Certificate Number</Label>
              <Input
                id="cert-number"
                type="text"
                placeholder={service === "NGC" ? "5788692-014" : "12345678"}
                value={certNumber}
                onChange={(e) => handleCertNumberChange(e.target.value)}
                disabled={isLoading}
                style={{
                  background: 'var(--bg-elevated)',
                  borderColor: 'var(--border-subtle)'
                }}
              />
              <p 
                className="text-xs"
                style={{ color: 'var(--text-ghost)' }}
              >
                {service === "NGC" 
                  ? "Format: XXXXXXX-XXX (e.g., 5788692-014)"
                  : "Format: 8-digit number (e.g., 12345678)"
                }
              </p>
            </div>
            
            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isLoading || !certNumber.trim()}
                style={{
                  background: service === "NGC" ? "var(--cert-ngc)" : "var(--cert-pcgs)",
                  color: '#fff'
                }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Looking up...
                  </>
                ) : (
                  <>
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Lookup
                  </>
                )}
              </Button>
            </div>
            
            <p 
              className="text-xs text-center pt-2"
              style={{ color: 'var(--text-ghost)' }}
            >
              Opens {service} verification page in a new tab
            </p>
          </div>
        </form>
      </PopoverContent>
    </Popover>
  );
}
