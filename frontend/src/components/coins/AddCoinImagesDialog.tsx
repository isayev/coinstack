/**
 * AddCoinImagesDialog - Add or replace obv/rev images for a coin from card or table.
 * Uses ImageUploadWithSplit (same logic as Coin Edit Finalize step), then updateCoin.
 */

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ImageUploadWithSplit, ImageEntry } from "./ImageUploadWithSplit";
import { Coin } from "@/domain/schemas";
import { client } from "@/api/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

interface AddCoinImagesDialogProps {
    coin: Coin | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess?: () => void;
}

function normalizeImages(coin: Coin | null): ImageEntry[] {
    if (!coin?.images?.length) return [];
    return coin.images.map((img) => ({
        url: img.url ?? "",
        image_type: img.image_type ?? "general",
        is_primary: img.is_primary ?? false,
    }));
}

export function AddCoinImagesDialog({ coin, open, onOpenChange, onSuccess }: AddCoinImagesDialogProps) {
    const queryClient = useQueryClient();
    const [images, setImages] = useState<ImageEntry[]>([]);

    useEffect(() => {
        if (open && coin) {
            setImages(normalizeImages(coin));
        }
    }, [open, coin]);

    const updateMutation = useMutation({
        mutationFn: ({ id, payload }: { id: number; payload: Omit<Coin, "id"> }) =>
            client.updateCoin(id, payload),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["coin", variables.id] });
            queryClient.invalidateQueries({ queryKey: ["coins"] });
            toast.success("Images saved");
            onSuccess?.();
            onOpenChange(false);
        },
        onError: (error: Error) => {
            toast.error(error.message || "Failed to save images");
        },
    });

    const handleSave = () => {
        if (!coin?.id) return;
        const { id: _id, ...rest } = coin;
        const payload: Omit<Coin, "id"> = { ...rest, images };
        updateMutation.mutate({ id: coin.id, payload });
    };

    const handleOpenChange = (newOpen: boolean) => {
        if (!newOpen) setImages([]);
        onOpenChange(newOpen);
    };

    if (!coin) return null;

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Add images</DialogTitle>
                </DialogHeader>
                <div className="py-4 space-y-4">
                    <p className="text-sm text-muted-foreground">
                        {coin.attribution?.issuer ?? "Unknown"} · {coin.denomination ?? ""}
                    </p>
                    <ImageUploadWithSplit images={images} onImagesChange={setImages} />
                    <div className="flex justify-end gap-2 pt-4">
                        <Button variant="outline" onClick={() => handleOpenChange(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSave}
                            disabled={updateMutation.isPending}
                        >
                            {updateMutation.isPending ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Saving…
                                </>
                            ) : (
                                "Save"
                            )}
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
