/**
 * ImagePreviewGrid - Display and manage coin images during import.
 * 
 * Features:
 * - Grid display of coin images
 * - Source badges (Heritage, NGC, etc.)
 * - Image type indicators (obverse/reverse)
 * - Primary image selection
 * - Remove/reorder capability
 */
import { useState } from "react";
import { Image as ImageIcon, Star, Trash2, GripVertical, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ImagePreview, SOURCE_CONFIG } from "@/hooks/useImport";
import { cn } from "@/lib/utils";

interface ImagePreviewGridProps {
  images: ImagePreview[];
  onImagesChange?: (images: ImagePreview[]) => void;
  editable?: boolean;
}

export function ImagePreviewGrid({
  images,
  onImagesChange,
  editable = true,
}: ImagePreviewGridProps) {
  const [loadErrors, setLoadErrors] = useState<Set<string>>(new Set());
  
  if (images.length === 0) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-muted-foreground">
            <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No images available</p>
            <p className="text-sm">Images will be fetched from the source</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  const handleSetPrimary = (index: number) => {
    if (!onImagesChange || !editable) return;
    
    // Move selected image to front
    const newImages = [...images];
    const [selected] = newImages.splice(index, 1);
    newImages.unshift(selected);
    onImagesChange(newImages);
  };
  
  const handleRemove = (index: number) => {
    if (!onImagesChange || !editable) return;
    
    const newImages = images.filter((_, i) => i !== index);
    onImagesChange(newImages);
  };
  
  const handleImageError = (url: string) => {
    setLoadErrors((prev) => new Set([...prev, url]));
  };
  
  const getSourceBadge = (source: string) => {
    const config = SOURCE_CONFIG[source];
    if (!config) return null;
    
    return (
      <Badge
        variant="outline"
        className={cn(
          "text-xs py-0 px-1.5",
          config.color,
          config.bgColor,
          config.borderColor
        )}
      >
        {config.label}
      </Badge>
    );
  };
  
  const getTypeBadge = (type: string) => {
    const labels: Record<string, string> = {
      obverse: "Obv",
      reverse: "Rev",
      slab_front: "Slab",
      slab_back: "Slab Back",
      detail: "Detail",
      combined: "Combined",
    };
    
    return labels[type] || type;
  };
  
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <ImageIcon className="h-4 w-4" />
          Images ({images.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {images.map((image, index) => {
            const hasError = loadErrors.has(image.url);
            const isPrimary = index === 0;
            
            return (
              <div
                key={image.url}
                className={cn(
                  "relative group rounded-lg overflow-hidden border",
                  isPrimary && "ring-2 ring-primary ring-offset-2",
                  hasError && "bg-muted"
                )}
              >
                {/* Image */}
                {!hasError ? (
                  <img
                    src={image.url}
                    alt={`Coin ${image.image_type}`}
                    className="w-full aspect-square object-cover"
                    onError={() => handleImageError(image.url)}
                  />
                ) : (
                  <div className="w-full aspect-square flex items-center justify-center bg-muted">
                    <ImageIcon className="h-8 w-8 text-muted-foreground" />
                  </div>
                )}
                
                {/* Overlay badges */}
                <div className="absolute top-1 left-1 flex flex-col gap-1">
                  {isPrimary && (
                    <Badge className="text-xs py-0 px-1.5 bg-primary">
                      <Star className="h-3 w-3 mr-0.5" />
                      Primary
                    </Badge>
                  )}
                  <Badge variant="secondary" className="text-xs py-0 px-1.5">
                    {getTypeBadge(image.image_type)}
                  </Badge>
                </div>
                
                {/* Source badge */}
                <div className="absolute bottom-1 left-1">
                  {getSourceBadge(image.source)}
                </div>
                
                {/* Hover actions */}
                {editable && (
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    {!isPrimary && (
                      <Button
                        size="sm"
                        variant="secondary"
                        className="h-7 text-xs"
                        onClick={() => handleSetPrimary(index)}
                      >
                        <Star className="h-3 w-3 mr-1" />
                        Primary
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="destructive"
                      className="h-7 text-xs"
                      onClick={() => handleRemove(index)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      className="h-7 text-xs"
                      onClick={() => window.open(image.url, "_blank")}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
