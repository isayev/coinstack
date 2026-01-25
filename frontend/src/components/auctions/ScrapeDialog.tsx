import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScraperForm } from "@/features/scraper/ScraperForm";

interface ScrapeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: () => void;
}

export function ScrapeDialog({ open, onOpenChange, onComplete }: ScrapeDialogProps) {
  const handleSuccess = (_data: any) => {
    // In a real app, this might show a preview or save to DB
    // For now, we just close and refresh
    onComplete();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Scrape Auction Lot</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <ScraperForm onScrapeSuccess={handleSuccess} />
        </div>
      </DialogContent>
    </Dialog>
  );
}