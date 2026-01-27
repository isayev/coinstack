import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScraperForm } from "@/features/scraper/ScraperForm";
import { CoinForm } from "@/components/coins/CoinForm";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { client, ImportPreviewResponse } from "@/api/client";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";

interface ScrapeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: () => void;
}

export function ScrapeDialog({ open, onOpenChange, onComplete }: ScrapeDialogProps) {
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const queryClient = useQueryClient();

  // Reset state when dialog closes
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setPreviewData(null);
    }
    onOpenChange(newOpen);
  };

  const handleScrapeSuccess = (data: ImportPreviewResponse) => {
    setPreviewData(data);
  };

  const confirmMutation = useMutation({
    mutationFn: client.confirmImport,
    onSuccess: (response) => {
      if (response.success) {
        toast.success("Coin saved to collection successfully");
        queryClient.invalidateQueries({ queryKey: ['coins'] });
        onComplete();
        handleOpenChange(false);
      } else {
        toast.error(`Error saving coin: ${response.error}`);
      }
    },
    onError: (error) => {
      toast.error(`Failed to save coin: ${error.message}`);
    }
  });

  const handleConfirm = (formData: any) => {
    if (!previewData) return;

    confirmMutation.mutate({
      coin_data: formData,
      source_type: previewData.source_type || 'unknown',
      source_id: previewData.source_id,
      source_url: previewData.source_url,
      raw_data: previewData.raw_data
    });
  };

  const handleBack = () => {
    setPreviewData(null);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className={previewData ? "max-w-4xl max-h-[90vh] overflow-y-auto" : "sm:max-w-md"}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {previewData && (
              <Button variant="ghost" size="icon" onClick={handleBack} className="h-8 w-8 -ml-2">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            {previewData ? "Review & Edit Coin Details" : "Scrape Auction Lot"}
          </DialogTitle>
        </DialogHeader>

        <div className="py-4">
          {!previewData ? (
            <ScraperForm onScrapeSuccess={handleScrapeSuccess} />
          ) : (
            <div className="space-y-4">
              {previewData.error && (
                <div className="bg-amber-50 text-amber-900 p-3 rounded-md text-sm border border-amber-200">
                  <strong>Note:</strong> {previewData.error}
                </div>
              )}

              <CoinForm
                defaultValues={previewData.coin_data}
                onSubmit={handleConfirm}
                isSubmitting={confirmMutation.isPending}
              />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}