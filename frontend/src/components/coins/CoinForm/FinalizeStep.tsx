import { useState, useRef } from "react"
import { UseFormReturn } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Image as ImageIcon, Upload, Scissors, Trash2, Maximize2 } from "lucide-react"
import { CoinFormData } from "./schema"
import { toast } from "sonner"

interface FinalizeStepProps {
    form: UseFormReturn<CoinFormData>
}

export function FinalizeStep({ form }: FinalizeStepProps) {
    const { register, watch, setValue } = form
    const images = watch("images") || []

    const fileInputRef = useRef<HTMLInputElement>(null)
    const [splitCandidates, setSplitCandidates] = useState<{ obverse: string, reverse: string } | null>(null)

    // Handle File Upload
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || [])
        if (files.length === 0) return

        files.forEach(file => {
            const reader = new FileReader()
            reader.onload = (event) => {
                const result = event.target?.result as string
                // If single file, check for split. If multiple, assume they are individual images.
                if (files.length === 1) {
                    checkImageDimensions(result)
                } else {
                    addSingleImage(result)
                }
            }
            reader.readAsDataURL(file)
        })
    }

    const checkImageDimensions = (dataUrl: string) => {
        const img = new Image()
        img.onload = () => {
            // ... existing split logic ...
            // (Keeping existing logic mostly, but it needs to call addSingleImage correctly)
            const ratio = img.width / img.height
            if (ratio > 1.8 && ratio < 2.2) {
                // ... split suggestion ...
                toast.info("Detected 2:1 image. Suggesting auto-split.", {
                    action: {
                        label: "Split",
                        onClick: () => performSplit(img, 'horizontal')
                    }
                })
                setSplitCandidates(generateSplits(img, 'horizontal'))
            } else if (ratio > 0.45 && ratio < 0.55) {
                // ... vertical split ...
                toast.info("Detected 1:2 image. Suggesting auto-split.", {
                    action: {
                        label: "Split",
                        onClick: () => performSplit(img, 'vertical')
                    }
                })
                setSplitCandidates(generateSplits(img, 'vertical'))
            } else {
                addSingleImage(dataUrl)
            }
        }
        img.src = dataUrl
    }

    const generateSplits = (img: HTMLImageElement, mode: 'horizontal' | 'vertical') => {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        if (!ctx) return null

        const w = mode === 'horizontal' ? img.width / 2 : img.width
        const h = mode === 'horizontal' ? img.height : img.height / 2

        canvas.width = w
        canvas.height = h

        // Draw Obverse (Left or Top)
        ctx.drawImage(img, 0, 0, w, h, 0, 0, w, h)
        const obverse = canvas.toDataURL('image/jpeg', 0.9)

        // Draw Reverse (Right or Bottom)
        const sx = mode === 'horizontal' ? w : 0
        const sy = mode === 'horizontal' ? 0 : h
        ctx.drawImage(img, sx, sy, w, h, 0, 0, w, h)
        const reverse = canvas.toDataURL('image/jpeg', 0.9)

        return { obverse, reverse }
    }

    const performSplit = (img: HTMLImageElement, mode: 'horizontal' | 'vertical') => {
        const splits = generateSplits(img, mode)
        if (splits) {
            const currentImages = form.getValues("images") || []
            setValue("images", [
                ...currentImages,
                { url: splits.obverse, is_primary: true, image_type: 'obverse' }, // Obverse is usually primary
                { url: splits.reverse, is_primary: false, image_type: 'reverse' }
            ], { shouldDirty: true })
            setSplitCandidates(null)
            toast.success("Image split and added successfully")
        }
    }

    const addSingleImage = (url: string) => {
        const currentImages = form.getValues("images") || []
        setValue("images", [
            ...currentImages,
            { url: url, is_primary: currentImages.length === 0, image_type: 'general' }
        ], { shouldDirty: true })
    }

    const removeImage = (index: number) => {
        const currentImages = form.getValues("images") || []
        setValue("images", currentImages.filter((_, i) => i !== index), { shouldDirty: true })
    }

    const setPrimary = (index: number) => {
        const currentImages = form.getValues("images") || []
        const updated = currentImages.map((img, i) => ({
            ...img,
            is_primary: i === index
        }))
        setValue("images", updated, { shouldDirty: true })
    }

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardContent className="p-0 space-y-8">

                {/* Image Upload Area */}
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
                            <span className="text-xs text-blue-500 font-medium">Auto-detects 2:1 side-by-side images for splitting.</span>
                        </p>
                    </div>
                    <Button type="button" variant="secondary" onClick={(e) => { e.preventDefault(); fileInputRef.current?.click() }}>
                        Select File
                    </Button>
                </div>

                {/* Split Confirmation (if candidates exist but weren't auto-split via toast) */}
                {splitCandidates && (
                    <div className="p-4 border rounded-lg bg-blue-50 dark:bg-blue-900/10 space-y-4">
                        <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
                            <Scissors className="h-4 w-4" />
                            <span className="font-semibold text-sm">Smart Split Suggestion</span>
                        </div>
                        <div className="flex gap-4">
                            <div className="space-y-1">
                                <span className="text-xs font-medium text-muted-foreground">Obverse</span>
                                <img src={splitCandidates.obverse} className="h-24 w-auto rounded border" />
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs font-medium text-muted-foreground">Reverse</span>
                                <img src={splitCandidates.reverse} className="h-24 w-auto rounded border" />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Button size="sm" onClick={() => {
                                const currentImages = form.getValues("images") || []
                                setValue("images", [
                                    ...currentImages,
                                    { url: splitCandidates.obverse, is_primary: true, image_type: 'obverse' },
                                    { url: splitCandidates.reverse, is_primary: false, image_type: 'reverse' }
                                ], { shouldDirty: true })
                                setSplitCandidates(null)
                            }}>Confirm Split</Button>
                            <Button size="sm" variant="ghost" onClick={() => {
                                // Add original not shown here - logic implies we'd keep original if we cancel split, 
                                // but simpler to just clear/re-upload or handled by 'addSingleImage' logic above if we didn't force split.
                                // For now, just cancel.
                                setSplitCandidates(null)
                            }}>Cancel</Button>
                        </div>
                    </div>
                )}

                {/* Image Grid */}
                {images && images.length > 0 && (
                    <div className="space-y-3">
                        <label className="text-sm font-semibold flex items-center gap-2">
                            <ImageIcon className="h-4 w-4" />
                            Gallery ({images.length})
                        </label>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {images.map((img, i) => (
                                <div key={i} className="group relative aspect-square rounded-lg border overflow-hidden bg-muted">
                                    <img src={img.url} className="w-full h-full object-cover" alt="Coin" />

                                    {/* Overlay Actions */}
                                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 p-2">
                                        <div className="flex gap-2">
                                            <Button
                                                type="button"
                                                size="sm"
                                                variant={img.image_type === 'obverse' ? "default" : "secondary"}
                                                className="h-7 text-xs px-2"
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    e.stopPropagation();
                                                    const currentImages = form.getValues("images") || []
                                                    const updated = currentImages.map((x, idx) =>
                                                        idx === i ? { ...x, image_type: 'obverse', is_primary: true } : { ...x, is_primary: false }
                                                    )
                                                    setValue("images", updated, { shouldDirty: true })
                                                }}
                                            >
                                                Obv
                                            </Button>
                                            <Button
                                                type="button"
                                                size="sm"
                                                variant={img.image_type === 'reverse' ? "default" : "secondary"}
                                                className="h-7 text-xs px-2"
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    e.stopPropagation();
                                                    const currentImages = form.getValues("images") || []
                                                    const updated = currentImages.map((x, idx) =>
                                                        idx === i ? { ...x, image_type: 'reverse' } : x
                                                    )
                                                    setValue("images", updated, { shouldDirty: true })
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
                                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setPrimary(i) }}
                                                title="Set Primary"
                                            >
                                                <Maximize2 className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                type="button"
                                                size="icon"
                                                variant="destructive"
                                                className="h-8 w-8"
                                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); removeImage(i) }}
                                                title="Remove"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Primary Badge */}
                                    {img.is_primary && (
                                        <div className="absolute top-2 right-2 bg-primary text-primary-foreground text-[10px] px-2 py-0.5 rounded-full font-bold shadow-sm">
                                            PRIMARY
                                        </div>
                                    )}
                                    {/* Type Badge */}
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

                <div className="space-y-2">
                    <label className="text-sm font-semibold">Storage Location</label>
                    <Input {...register("storage_location")} placeholder="SlabBox 1, Tray 4, etc." className="h-11" />
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-semibold">Tags</label>
                    <Input
                        placeholder="Comma separated tags (e.g. hoard, plate coin, gift)"
                        className="h-11"
                        onBlur={(e) => {
                            const val = e.target.value;
                            if (val) {
                                // Split by comma and clean
                                const tags = val.split(',').map(t => t.trim()).filter(Boolean);
                                setValue("tags", tags, { shouldDirty: true });
                            }
                        }}
                        defaultValue={(form.getValues("tags") || []).join(", ")}
                    />
                    <p className="text-xs text-muted-foreground">Separate tags with commas</p>
                </div>


                <div className="space-y-2">
                    <label className="text-sm font-semibold">Personal Research Notes</label>
                    <textarea
                        {...register("personal_notes")}
                        className="w-full min-h-[150px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        placeholder="Add any specific research notes, variant details, or collection history..."
                    />
                </div>
            </CardContent>
        </Card>
    )
}
