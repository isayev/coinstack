/**
 * ImageManager - Manage coin images with obverse/reverse selection.
 * 
 * Features:
 * - Display all images from auction data
 * - Select obverse and reverse images
 * - Mark additional images as misc/attachments
 * - Save selections to CoinImage table
 */
import { useState, useEffect } from "react";
import { 
  Image as ImageIcon, 
  ExternalLink, 
  Loader2,
  CircleDot,
  RotateCcw,
  Paperclip,
  Save,
  AlertCircle,
  CheckCircle2
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { toast } from "sonner";

interface AuctionImage {
  url: string;
  source: string;
  auction_id: number;
}

interface CoinImage {
  id: number;
  image_type: string;
  file_path: string;
  source_url?: string | null;
  is_primary: boolean;
}

interface ImageSelection {
  url: string;
  type: "obverse" | "reverse" | "other" | null;
  source: string;
  auction_id: number;
}

interface ImageManagerProps {
  coinId: number;
  auctionData: Array<{
    id: number;
    auction_house: string;
    photos?: string[] | null;
    title?: string | null;
  }>;
  existingImages: CoinImage[];
  onImagesUpdated?: () => void;
}

export function ImageManager({ 
  coinId, 
  auctionData, 
  existingImages,
  onImagesUpdated 
}: ImageManagerProps) {
  const [selections, setSelections] = useState<Map<string, ImageSelection>>(new Map());
  const [loadErrors, setLoadErrors] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  
  // Collect all images from auction data
  const allImages: AuctionImage[] = [];
  auctionData?.forEach(auction => {
    if (auction.photos && Array.isArray(auction.photos)) {
      auction.photos.forEach(url => {
        if (url && !url.includes('ajax-loader') && !url.includes('placeholder')) {
          allImages.push({
            url,
            source: auction.auction_house,
            auction_id: auction.id,
          });
        }
      });
    }
  });
  
  // Initialize selections from existing images
  useEffect(() => {
    const initial = new Map<string, ImageSelection>();
    existingImages?.forEach(img => {
      if (img.source_url) {
        initial.set(img.source_url, {
          url: img.source_url,
          type: img.image_type as "obverse" | "reverse" | "other",
          source: img.source_url.includes('ebay') ? 'eBay' : 
                  img.source_url.includes('biddr') ? 'Biddr' :
                  img.source_url.includes('cngcoins') ? 'CNG' : 'Unknown',
          auction_id: 0,
        });
      }
    });
    setSelections(initial);
  }, [existingImages]);
  
  const handleSelect = (image: AuctionImage, type: "obverse" | "reverse" | "other") => {
    const newSelections = new Map(selections);
    
    // If selecting obverse/reverse, clear any existing selection of that type
    if (type === "obverse" || type === "reverse") {
      newSelections.forEach((sel, url) => {
        if (sel.type === type) {
          newSelections.set(url, { ...sel, type: null });
        }
      });
    }
    
    // Toggle or set the selection
    const current = newSelections.get(image.url);
    if (current?.type === type) {
      // Clicking same type again clears it
      newSelections.set(image.url, { ...image, type: null });
    } else {
      newSelections.set(image.url, { ...image, type });
    }
    
    setSelections(newSelections);
    setHasChanges(true);
  };
  
  const handleImageError = (url: string) => {
    setLoadErrors(prev => new Set([...prev, url]));
  };
  
  const handleSave = async () => {
    setSaving(true);
    try {
      const imageSelections = Array.from(selections.values())
        .filter(s => s.type !== null)
        .map(s => ({
          url: s.url,
          image_type: s.type,
          source: s.source,
          auction_id: s.auction_id,
        }));
      
      await api.post(`/api/coins/${coinId}/images`, { images: imageSelections });
      
      toast.success("Images saved successfully");
      setHasChanges(false);
      onImagesUpdated?.();
    } catch (error) {
      toast.error("Failed to save images");
      if (import.meta.env.DEV) {
        console.error("Failed to save images:", error);
      }
    } finally {
      setSaving(false);
    }
  };
  
  const getSelectionForImage = (url: string) => selections.get(url);
  
  const obverseImage = Array.from(selections.values()).find(s => s.type === "obverse");
  const reverseImage = Array.from(selections.values()).find(s => s.type === "reverse");
  const otherImages = Array.from(selections.values()).filter(s => s.type === "other");
  
  if (allImages.length === 0 && (!existingImages || existingImages.length === 0)) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-muted-foreground">
            <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No images available</p>
            <p className="text-sm mt-1">Add auction data to see available images</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Selection Summary */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Current Selection
          </CardTitle>
          <CardDescription>
            Click images below to assign them as obverse, reverse, or misc
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {/* Obverse */}
            <div className="space-y-2">
              <div className="text-sm font-medium flex items-center gap-1">
                <Badge variant="default" className="bg-blue-500">OBV</Badge>
                Obverse
              </div>
              {obverseImage ? (
                <div className="relative aspect-square rounded-lg overflow-hidden border-2 border-blue-500">
                  <img
                    src={obverseImage.url}
                    alt="Obverse"
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="aspect-square rounded-lg border-2 border-dashed border-muted-foreground/25 flex items-center justify-center">
                  <span className="text-xs text-muted-foreground">Not selected</span>
                </div>
              )}
            </div>
            
            {/* Reverse */}
            <div className="space-y-2">
              <div className="text-sm font-medium flex items-center gap-1">
                <Badge variant="default" className="bg-green-500">REV</Badge>
                Reverse
              </div>
              {reverseImage ? (
                <div className="relative aspect-square rounded-lg overflow-hidden border-2 border-green-500">
                  <img
                    src={reverseImage.url}
                    alt="Reverse"
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="aspect-square rounded-lg border-2 border-dashed border-muted-foreground/25 flex items-center justify-center">
                  <span className="text-xs text-muted-foreground">Not selected</span>
                </div>
              )}
            </div>
            
            {/* Misc count */}
            <div className="space-y-2">
              <div className="text-sm font-medium flex items-center gap-1">
                <Badge variant="secondary">MISC</Badge>
                Attachments
              </div>
              <div className="aspect-square rounded-lg border-2 border-dashed border-muted-foreground/25 flex items-center justify-center">
                <div className="text-center">
                  <Paperclip className="h-6 w-6 mx-auto text-muted-foreground mb-1" />
                  <span className="text-sm font-medium">{otherImages.length}</span>
                  <span className="text-xs text-muted-foreground block">images</span>
                </div>
              </div>
            </div>
          </div>
          
          {hasChanges && (
            <div className="mt-4 pt-4 border-t">
              <Button onClick={handleSave} disabled={saving} className="w-full">
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Image Selections
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* All Available Images */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ImageIcon className="h-4 w-4" />
            Available Images ({allImages.length})
          </CardTitle>
          <CardDescription>
            From {auctionData?.length || 0} auction records
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {allImages.map((image, index) => {
              const hasError = loadErrors.has(image.url);
              const selection = getSelectionForImage(image.url);
              
              return (
                <div
                  key={`${image.url}-${index}`}
                  className={cn(
                    "relative group rounded-lg overflow-hidden border-2 transition-all",
                    selection?.type === "obverse" && "border-blue-500 ring-2 ring-blue-500/20",
                    selection?.type === "reverse" && "border-green-500 ring-2 ring-green-500/20",
                    selection?.type === "other" && "border-orange-500 ring-2 ring-orange-500/20",
                    !selection?.type && "border-transparent hover:border-muted-foreground/50"
                  )}
                >
                  {/* Image */}
                  {!hasError ? (
                    <img
                      src={image.url}
                      alt={`Coin image ${index + 1}`}
                      className="w-full aspect-square object-cover"
                      onError={() => handleImageError(image.url)}
                    />
                  ) : (
                    <div className="w-full aspect-square flex items-center justify-center bg-muted">
                      <AlertCircle className="h-8 w-8 text-muted-foreground" />
                    </div>
                  )}
                  
                  {/* Source badge */}
                  <div className="absolute top-1 left-1">
                    <Badge variant="secondary" className="text-xs py-0 px-1.5 bg-black/60 text-white border-0">
                      {image.source}
                    </Badge>
                  </div>
                  
                  {/* Selection indicator */}
                  {selection?.type && (
                    <div className="absolute top-1 right-1">
                      <Badge 
                        className={cn(
                          "text-xs py-0 px-1.5",
                          selection.type === "obverse" && "bg-blue-500",
                          selection.type === "reverse" && "bg-green-500",
                          selection.type === "other" && "bg-orange-500"
                        )}
                      >
                        {selection.type === "obverse" ? "OBV" : 
                         selection.type === "reverse" ? "REV" : "MISC"}
                      </Badge>
                    </div>
                  )}
                  
                  {/* Action buttons overlay */}
                  <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 p-2">
                    <TooltipProvider>
                      <div className="flex gap-1">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              size="sm"
                              variant={selection?.type === "obverse" ? "default" : "secondary"}
                              className={cn(
                                "h-8 w-8 p-0",
                                selection?.type === "obverse" && "bg-blue-500 hover:bg-blue-600"
                              )}
                              onClick={() => handleSelect(image, "obverse")}
                            >
                              <CircleDot className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Set as Obverse</TooltipContent>
                        </Tooltip>
                        
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              size="sm"
                              variant={selection?.type === "reverse" ? "default" : "secondary"}
                              className={cn(
                                "h-8 w-8 p-0",
                                selection?.type === "reverse" && "bg-green-500 hover:bg-green-600"
                              )}
                              onClick={() => handleSelect(image, "reverse")}
                            >
                              <RotateCcw className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Set as Reverse</TooltipContent>
                        </Tooltip>
                        
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              size="sm"
                              variant={selection?.type === "other" ? "default" : "secondary"}
                              className={cn(
                                "h-8 w-8 p-0",
                                selection?.type === "other" && "bg-orange-500 hover:bg-orange-600"
                              )}
                              onClick={() => handleSelect(image, "other")}
                            >
                              <Paperclip className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Add as Misc</TooltipContent>
                        </Tooltip>
                      </div>
                      
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            size="sm"
                            variant="secondary"
                            className="h-7 text-xs"
                            onClick={() => window.open(image.url, "_blank")}
                          >
                            <ExternalLink className="h-3 w-3 mr-1" />
                            Full Size
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Open in new tab</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
      
      {/* Instructions */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>How to use:</strong> Hover over images and click the icons to assign them.
          <span className="inline-flex items-center gap-1 ml-2">
            <CircleDot className="h-3 w-3 text-blue-500" /> = Obverse,
          </span>
          <span className="inline-flex items-center gap-1 ml-2">
            <RotateCcw className="h-3 w-3 text-green-500" /> = Reverse,
          </span>
          <span className="inline-flex items-center gap-1 ml-2">
            <Paperclip className="h-3 w-3 text-orange-500" /> = Misc attachment
          </span>
        </AlertDescription>
      </Alert>
    </div>
  );
}
