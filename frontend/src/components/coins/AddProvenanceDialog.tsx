import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Coin } from "@/domain/schemas";
import { useUpdateCoin } from "@/hooks/useCoins";
import { toast } from "sonner";

// Schema for the form - simpler than full ProvenanceEvent
const AddProvenanceSchema = z.object({
  event_type: z.string().min(1, "Type is required"),
  source_name: z.string().min(1, "Source name is required"),
  date_string: z.string().optional(), // "1995", "1920s", "May 2000"
  lot_number: z.string().optional(),
  price: z.string().optional(), // Parse to number on submit
  currency: z.string().default("USD"),
  notes: z.string().optional(),
});

type AddProvenanceForm = z.infer<typeof AddProvenanceSchema>;

interface AddProvenanceDialogProps {
  coin: Coin;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entryToEdit?: any; // ProvenanceEvent
}

export function AddProvenanceDialog({
  coin,
  open,
  onOpenChange,
  entryToEdit,
}: AddProvenanceDialogProps) {
  const updateCoin = useUpdateCoin();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<AddProvenanceForm>({
    resolver: zodResolver(AddProvenanceSchema),
    defaultValues: {
      event_type: "auction",
      currency: "USD",
    },
  });

  const eventType = watch("event_type");

  useEffect(() => {
    if (open && entryToEdit) {
      // Pre-fill form
      setValue("event_type", entryToEdit.event_type || "auction");
      const source = entryToEdit.source_name || entryToEdit.auction_house || entryToEdit.dealer_name || entryToEdit.collection_name || "";
      setValue("source_name", source);
      setValue("date_string", entryToEdit.date_string || entryToEdit.event_date || "");
      setValue("lot_number", entryToEdit.lot_number || "");
      
      const priceVal = entryToEdit.price ?? entryToEdit.total_price ?? entryToEdit.hammer_price;
      setValue("price", priceVal !== null && priceVal !== undefined ? String(priceVal) : "");
      
      setValue("currency", entryToEdit.currency || "USD");
      setValue("notes", entryToEdit.notes || "");
    } else if (open && !entryToEdit) {
      // Reset form for add mode
      reset({
        event_type: "auction",
        currency: "USD",
        source_name: "",
        date_string: "",
        lot_number: "",
        price: "",
        notes: "",
      });
    }
  }, [open, entryToEdit, setValue, reset]);

  const onSubmit = async (data: AddProvenanceForm) => {
    if (!coin.id) return;
    setIsSubmitting(true);

    try {
      // 1. Construct entry data
      const entryData = {
        id: entryToEdit?.id, // Preserve ID if editing
        event_type: data.event_type,
        source_name: data.source_name,
        date_string: data.date_string || null,
        lot_number: data.lot_number || null,
        total_price: data.price ? parseFloat(data.price) : null,
        currency: data.currency,
        notes: data.notes || null,
        
        // Backward compatibility
        auction_house: data.event_type === 'auction' ? data.source_name : null,
        dealer_name: data.event_type === 'dealer' ? data.source_name : null,
        collection_name: data.event_type === 'collection' ? data.source_name : null,
      };

      // 2. Merge with existing
      const currentProvenance = coin.provenance || [];
      let updatedProvenance;

      if (entryToEdit) {
        // Edit Mode: Replace the entry
        updatedProvenance = currentProvenance.map(p => {
          // Robust matching
          const matchesId = entryToEdit.id && p.id === entryToEdit.id;
          // Fallback: loose comparison of key properties if ID is missing (unlikely but safe)
          const matchesProps = !entryToEdit.id && 
                               p.event_type === entryToEdit.event_type && 
                               (p.source_name === entryToEdit.source_name || p.auction_house === entryToEdit.auction_house); // Simplified check
          
          // Use original object reference check as final fallback
          if (matchesId || matchesProps || p === entryToEdit) {
            return { ...p, ...entryData };
          }
          return p;
        });
      } else {
        // Add Mode: Append
        updatedProvenance = [...currentProvenance, entryData];
      }

      // 3. Send update
      await updateCoin.mutateAsync({
        id: coin.id,
        data: {
          ...coin,
          provenance: updatedProvenance as any,
        },
      });

      toast.success(entryToEdit ? "Provenance updated" : "Provenance added");
      reset();
      onOpenChange(false);
    } catch (e) {
      console.error(e);
      toast.error("Failed to add provenance");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{entryToEdit ? "Edit Provenance" : "Add Provenance History"}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Source Type</Label>
              <Select
                onValueChange={(val) => setValue("event_type", val)}
                defaultValue={eventType}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auction">Auction</SelectItem>
                  <SelectItem value="dealer">Dealer</SelectItem>
                  <SelectItem value="collection">Collection</SelectItem>
                  <SelectItem value="private_sale">Private Sale</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Source Name</Label>
              <Input
                {...register("source_name")}
                placeholder={
                  eventType === "auction"
                    ? "e.g. Heritage Auctions"
                    : eventType === "collection"
                    ? "e.g. The Hunt Collection"
                    : "e.g. H.J. Berk"
                }
              />
              {errors.source_name && (
                <p className="text-xs text-destructive">
                  {errors.source_name.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Date (Flexible)</Label>
              <Input
                {...register("date_string")}
                placeholder="e.g. 2024, Jan 2020, 1990s"
              />
              <p className="text-[10px] text-muted-foreground">
                Year, month/year, or approx.
              </p>
            </div>

            <div className="space-y-2">
              <Label>Lot Number</Label>
              <Input {...register("lot_number")} placeholder="Optional" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-2 space-y-2">
              <Label>Price</Label>
              <Input
                type="number"
                step="0.01"
                {...register("price")}
                placeholder="0.00"
              />
            </div>
            <div className="space-y-2">
              <Label>Currency</Label>
              <Select
                onValueChange={(val) => setValue("currency", val)}
                defaultValue="USD"
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="GBP">GBP</SelectItem>
                  <SelectItem value="CHF">CHF</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Notes</Label>
            <Textarea
              {...register("notes")}
              placeholder="Sale details, pedigree notes, etc."
              className="resize-none h-20"
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (entryToEdit ? "Saving..." : "Adding...") : (entryToEdit ? "Save Changes" : "Add Entry")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
