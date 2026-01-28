import { UseFormReturn } from "react-hook-form"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ImageUploadWithSplit, type ImageEntry } from "@/components/coins/ImageUploadWithSplit"
import { CoinFormData } from "./schema"

interface FinalizeStepProps {
    form: UseFormReturn<CoinFormData>
}

function toImageEntries(imgs: CoinFormData["images"]): ImageEntry[] {
  const list = imgs ?? []
  return list.map((img) => ({
    url: img?.url ?? "",
    image_type: img?.image_type ?? "general",
    is_primary: !!img?.is_primary,
  }))
}

export function FinalizeStep({ form }: FinalizeStepProps) {
    const { register, watch, setValue } = form
    const rawImages = watch("images") ?? []
    const images = toImageEntries(rawImages)

    return (
        <Card className="border-none shadow-none bg-transparent">
            <CardContent className="p-0 space-y-8">

                <ImageUploadWithSplit
                    images={images}
                    onImagesChange={(imgs) => setValue("images", imgs as CoinFormData["images"], { shouldDirty: true })}
                />

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
