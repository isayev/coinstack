/**
 * QuickScrapePopover - Popover for quickly scraping auction URLs
 * 
 * Allows users to paste an auction URL and scrape coin data
 * without navigating away from the current page.
 * 
 * Supported sites: Heritage, CNG, eBay, VCoins, Biddr, MA-Shops
 */

import { useState, ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Loader2, ExternalLink, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { api } from "@/lib/api";

const SUPPORTED_SITES = [
  { name: "Heritage Auctions", domain: "ha.com" },
  { name: "CNG", domain: "cngcoins.com" },
  { name: "eBay", domain: "ebay.com" },
  { name: "VCoins", domain: "vcoins.com" },
  { name: "Biddr", domain: "biddr.com" },
  { name: "MA-Shops", domain: "ma-shops.com" },
];

interface QuickScrapePopoverProps {
  children: ReactNode;
}

export function QuickScrapePopover({ children }: QuickScrapePopoverProps) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const scrapeMutation = useMutation({
    mutationFn: async (auctionUrl: string) => {
      const response = await api.post(`/api/v2/scrape?url=${encodeURIComponent(auctionUrl)}`);
      return response.data;
    },
    onSuccess: (data) => {
      setSuccess(true);
      setError(null);
      // Navigate to the scraped coin or edit page
      if (data.coin_id) {
        setTimeout(() => {
          setOpen(false);
          navigate(`/coins/${data.coin_id}`);
        }, 1000);
      } else if (data.auction_data_id) {
        setTimeout(() => {
          setOpen(false);
          navigate(`/auctions`);
        }, 1000);
      }
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Failed to scrape URL. Please check the URL and try again.");
      setSuccess(false);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      setError("Please enter a URL");
      return;
    }
    
    // Basic URL validation
    try {
      new URL(url);
    } catch {
      setError("Please enter a valid URL");
      return;
    }
    
    setError(null);
    setSuccess(false);
    scrapeMutation.mutate(url.trim());
  };

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
    if (!newOpen) {
      // Reset state when closing
      setUrl("");
      setError(null);
      setSuccess(false);
    }
  };

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        {children}
      </PopoverTrigger>
      <PopoverContent 
        className="w-96" 
        align="start"
        style={{
          background: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)'
        }}
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="space-y-2">
              <h4 
                className="font-medium leading-none"
                style={{ color: 'var(--text-primary)' }}
              >
                Paste Auction URL
              </h4>
              <p 
                className="text-sm"
                style={{ color: 'var(--text-muted)' }}
              >
                Scrape coin data from supported auction sites
              </p>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="auction-url">URL</Label>
              <Input
                id="auction-url"
                type="url"
                placeholder="https://www.heritage.com/lot/123..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={scrapeMutation.isPending}
                style={{
                  background: 'var(--bg-elevated)',
                  borderColor: 'var(--border-subtle)'
                }}
              />
            </div>
            
            {error && (
              <div 
                className="flex items-center gap-2 text-sm p-2 rounded"
                style={{ 
                  background: 'var(--perf-negative)',
                  color: '#fff'
                }}
              >
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
            
            {success && (
              <div 
                className="flex items-center gap-2 text-sm p-2 rounded"
                style={{ 
                  background: 'var(--perf-positive)',
                  color: '#fff'
                }}
              >
                <Check className="w-4 h-4 flex-shrink-0" />
                <span>Successfully scraped! Redirecting...</span>
              </div>
            )}
            
            <div className="space-y-2">
              <p 
                className="text-xs"
                style={{ color: 'var(--text-ghost)' }}
              >
                Supported sites:
              </p>
              <div className="flex flex-wrap gap-1">
                {SUPPORTED_SITES.map((site) => (
                  <span
                    key={site.domain}
                    className="inline-flex items-center text-xs px-2 py-0.5 rounded"
                    style={{
                      background: 'var(--bg-elevated)',
                      color: 'var(--text-muted)'
                    }}
                  >
                    {site.name}
                  </span>
                ))}
              </div>
            </div>
            
            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={scrapeMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={scrapeMutation.isPending || !url.trim()}
                style={{
                  background: 'var(--metal-au)',
                  color: '#000'
                }}
              >
                {scrapeMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Scraping...
                  </>
                ) : (
                  <>
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Scrape & Import
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>
      </PopoverContent>
    </Popover>
  );
}
