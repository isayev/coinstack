/**
 * ImageUploadWithSplit - Upload coin images with 2:1/1:2 auto-split and obv/rev assignment.
 * Shared by Coin Edit (FinalizeStep) and Add Images dialog (card/table).
 */

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Image as ImageIcon, Upload, Scissors, Trash2, Maximize2 } from "lucide-react";
import { toast } from "sonner";

export interface ImageEntry {
    url: string;
    image_type: string;
    is_primary: boolean;
}

interface ImageUploadWithSplitProps {
    images: ImageEntry[];
    onImagesChange: (images: ImageEntry[]) => void;
}

export function ImageUploadWithSplit({ images, onImagesChange }: ImageUploadWithSplitProps) {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [splitCandidates, setSplitCandidates] = useState<{ obverse: string; reverse: string } | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        if (files.length === 0) return;
        e.target.value = "";

        files.forEach((file) => {
            const reader = new FileReader();
            reader.onload = (event) => {
                const result = event.target?.result as string;
                if (files.length === 1) {
                    checkImageDimensions(result);
                } else {
                    addSingleImage(result);
                }
            };
            reader.readAsDataURL(file);
        });
    };

    const checkImageDimensions = (dataUrl: string) => {
        const img = new Image();
        img.onload = () => {
            const ratio = img.width / img.height;
            if (ratio > 1.8 && ratio < 2.2) {
                toast.info("Detected 2:1 image. Suggesting auto-split.", {
                    action: { label: "Split", onClick: () => performSplit(img, "horizontal") },
                });
                setSplitCandidates(generateSplits(img, "horizontal"));
            } else if (ratio > 0.45 && ratio < 0.55) {
                toast.info("Detected 1:2 image. Suggesting auto-split.", {
                    action: { label: "Split", onClick: () => performSplit(img, "vertical") },
                });
                setSplitCandidates(generateSplits(img, "vertical"));
            } else {
                addSingleImage(dataUrl);
            }
        };
        img.src = dataUrl;
    };

    const generateSplits = (img: HTMLImageElement, mode: "horizontal" | "vertical") => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        if (!ctx) return null;
        const w = mode === "horizontal" ? img.width / 2 : img.width;
        const h = mode === "horizontal" ? img.height : img.height / 2;
        canvas.width = w;
        canvas.height = h;
        ctx.drawImage(img, 0, 0, w, h, 0, 0, w, h);
        const obverse = canvas.toDataURL("image/jpeg", 0.9);
        const sx = mode === "horizontal" ? w : 0;
        const sy = mode === "horizontal" ? 0 : h;
        ctx.drawImage(img, sx, sy, w, h, 0, 0, w, h);
        const reverse = canvas.toDataURL("image/jpeg", 0.9);
        return { obverse, reverse };
    };

    const performSplit = (img: HTMLImageElement, mode: "horizontal" | "vertical") => {
        const splits = generateSplits(img, mode);
        if (splits) {
            onImagesChange([
                ...images,
                { url: splits.obverse, is_primary: true, image_type: "obverse" },
                { url: splits.reverse, is_primary: false, image_type: "reverse" },
            ]);
            setSplitCandidates(null);
            toast.success("Image split and added successfully");
        }
    };

    const addSingleImage = (url: string) => {
        onImagesChange([
            ...images,
            { url, is_primary: images.length === 0, image_type: "general" },
        ]);
    };

    const removeImage = (index: number) => {
        onImagesChange(images.filter((_, i) => i !== index));
    };

    const setPrimary = (index: number) => {
        onImagesChange(
            images.map((img, i) => ({ ...img, is_primary: i === index }))
        );
    };

    const setObverse = (index: number) => {
        onImagesChange(
            images.map((x, i) =>
                i === index ? { ...x, image_type: "obverse", is_primary: true } : { ...x, is_primary: false }
            )
        );
    };

    const setReverse = (index: number) => {
        onImagesChange(
            images.map((x, i) => (i === index ? { ...x, image_type: "reverse" } : x))
        );
    };

    const confirmSplit = () => {
        if (!splitCandidates) return;
        onImagesChange([
            ...images,
            { url: splitCandidates.obverse, is_primary: true, image_type: "obverse" },
            { url: splitCandidates.reverse, is_primary: false, image_type: "reverse" },
        ]);
        setSplitCandidates(null);
    };

    return (
        <div className="space-y-6">
            <div className="border-2 border-dashed border-muted-foreground/25 rounded-xl p-8 text-center space-y-4 hover:bg-muted/50 transition-colors">
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="image/*"
                    className="hidden"
                    multiple
                />
                <div className="flex justify-center">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                        <Upload className="h-6 w-6 text-primary" />
                    </div>
                </div>
                <div>
                    <h3 className="text-lg font-medium">Upload Coin Images</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                        Drag & drop or click to upload. <br />
                        <span className="text-xs text-blue-500 font-medium">
                            Auto-detects 2:1 side-by-side images for splitting.
                        </span>
                    </p>
                </div>
                <Button
                    type="button"
                    variant="secondary"
                    onClick={(e) => {
                        e.preventDefault();
                        fileInputRef.current?.click();
                    }}
                >
                    Select File
                </Button>
            </div>

            {splitCandidates && (
                <div className="p-4 border rounded-lg bg-blue-50 dark:bg-blue-900/10 space-y-4">
                    <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
                        <Scissors className="h-4 w-4" />
                        <span className="font-semibold text-sm">Smart Split Suggestion</span>
                    </div>
                    <div className="flex gap-4">
                        <div className="space-y-1">
                            <span className="text-xs font-medium text-muted-foreground">Obverse</span>
                            <img src={splitCandidates.obverse} className="h-24 w-auto rounded border" alt="Obverse" />
                        </div>
                        <div className="space-y-1">
                            <span className="text-xs font-medium text-muted-foreground">Reverse</span>
                            <img src={splitCandidates.reverse} className="h-24 w-auto rounded border" alt="Reverse" />
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button size="sm" onClick={confirmSplit}>
                            Confirm Split
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setSplitCandidates(null)}>
                            Cancel
                        </Button>
                    </div>
                </div>
            )}

            {images.length > 0 && (
                <div className="space-y-3">
                    <label className="text-sm font-semibold flex items-center gap-2">
                        <ImageIcon className="h-4 w-4" />
                        Gallery ({images.length})
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {images.map((img, i) => (
                            <div key={i} className="group relative aspect-square rounded-lg border overflow-hidden bg-muted">
                                <img src={img.url} className="w-full h-full object-cover" alt="Coin" />
                                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 p-2">
                                    <div className="flex gap-2">
                                        <Button
                                            type="button"
                                            size="sm"
                                            variant={img.image_type === "obverse" ? "default" : "secondary"}
                                            className="h-7 text-xs px-2"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                setObverse(i);
                                            }}
                                        >
                                            Obv
                                        </Button>
                                        <Button
                                            type="button"
                                            size="sm"
                                            variant={img.image_type === "reverse" ? "default" : "secondary"}
                                            className="h-7 text-xs px-2"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                setReverse(i);
                                            }}
                                        >
                                            Rev
                                        </Button>
                                    </div>
                                    <div className="flex gap-2 mt-1">
                                        <Button
                                            type="button"
                                            size="icon"
                                            variant="secondary"
                                            className="h-8 w-8"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                setPrimary(i);
                                            }}
                                            title="Set Primary"
                                        >
                                            <Maximize2 className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            type="button"
                                            size="icon"
                                            variant="destructive"
                                            className="h-8 w-8"
                                            onClick={(e) => {
                                                e.preventDefault();
                                                e.stopPropagation();
                                                removeImage(i);
                                            }}
                                            title="Remove"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                                {img.is_primary && (
                                    <div className="absolute top-2 right-2 bg-primary text-primary-foreground text-[10px] px-2 py-0.5 rounded-full font-bold shadow-sm">
                                        PRIMARY
                                    </div>
                                )}
                                {img.image_type && (
                                    <div className="absolute bottom-2 left-2 bg-black/50 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full font-medium">
                                        {img.image_type.toUpperCase()}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
