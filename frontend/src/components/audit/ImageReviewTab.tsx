/**
 * ImageReviewTab - Review and assign images to coins from auction sources
 * 
 * Features:
 * - Grid view of coins needing image assignment
 * - Quick selection of obverse/reverse from auction photos
 * - Filter by image status
 * - Batch operations
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { 
  Image as ImageIcon,
  ImageOff,
  CheckCircle2,
  CircleDot,
  RotateCcw,
  Loader2,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Save,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { MetalBadge } from "@/components/design-system";

interface CoinWithImages {
  id: number;
  issuing_authority: string;
  denomination: string;
  metal: string;
  grade: string | null;
  mint_year_start: number | null;
  mint_year_end: number | null;
  primary_image: string | null;
}

interface AuctionImage {
  url: string;
  source: string;
  auction_id: number;
}

interface ImageAssignment {
  obverse: string | null;
  reverse: string | null;
  misc: string[];
}

export function ImageReviewTab() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [selectedCoin, setSelectedCoin] = useState<CoinWithImages | null>(null);
  const [coinImages, setCoinImages] = useState<AuctionImage[]>([]);
  const [assignment, setAssignment] = useState<ImageAssignment>({
    obverse: null,
    reverse: null,
    misc: [],
  });
  const perPage = 12;

  // Fetch coins with image data
  const { data: coinsData, isLoading } = useQuery({
    queryKey: ["coins-for-images", page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
      });
      const { data } = await api.get(`/api/coins?${params}`);
      return data as {
        items: CoinWithImages[];
        total: number;
        page: number;
        pages: number;
      };
    },
  });

  // Fetch auction images for selected coin
  const { isLoading: loadingImages } = useQuery({
    queryKey: ["coin-auction-images", selectedCoin?.id],
    queryFn: async () => {
      if (!selectedCoin) return [];
      const { data } = await api.get(`/api/coins/${selectedCoin.id}/auction-images`);
      setCoinImages(data.images || []);
      return data.images;
    },
    enabled: !!selectedCoin,
  });

  // Save image assignment
  const saveMutation = useMutation({
    mutationFn: async ({ coinId, images }: { coinId: number; images: { url: string; image_type: string; source: string }[] }) => {
      const { data } = await api.post(`/api/coins/${coinId}/images`, { images });
      return data;
    },
    onSuccess: () => {
      toast.success("Images saved successfully");
      queryClient.invalidateQueries({ queryKey: ["coins-for-images"] });
      setSelectedCoin(null);
      setAssignment({ obverse: null, reverse: null, misc: [] });
    },
    onError: () => {
      toast.error("Failed to save images");
    },
  });

  const handleSelectImage = (url: string, type: "obverse" | "reverse" | "misc") => {
    if (type === "obverse") {
      setAssignment(prev => ({
        ...prev,
        obverse: prev.obverse === url ? null : url,
      }));
    } else if (type === "reverse") {
      setAssignment(prev => ({
        ...prev,
        reverse: prev.reverse === url ? null : url,
      }));
    } else {
      setAssignment(prev => ({
        ...prev,
        misc: prev.misc.includes(url) 
          ? prev.misc.filter(u => u !== url)
          : [...prev.misc, url],
      }));
    }
  };

  const handleSave = () => {
    if (!selectedCoin) return;
    
    const images: { url: string; image_type: string; source: string }[] = [];
    
    if (assignment.obverse) {
      const img = coinImages.find(i => i.url === assignment.obverse);
      if (img) images.push({ url: img.url, image_type: "obverse", source: img.source });
    }
    if (assignment.reverse) {
      const img = coinImages.find(i => i.url === assignment.reverse);
      if (img) images.push({ url: img.url, image_type: "reverse", source: img.source });
    }
    assignment.misc.forEach(url => {
      const img = coinImages.find(i => i.url === url);
      if (img) images.push({ url: img.url, image_type: "other", source: img.source });
    });

    saveMutation.mutate({ coinId: selectedCoin.id, images });
  };

  const getImageStatus = (coin: CoinWithImages): { label: string; color: string } => {
    if (coin.primary_image) {
      return { label: "Has Image", color: "bg-emerald-500/20 text-emerald-600 border-emerald-500/40" };
    }
    return { label: "No Images", color: "bg-slate-500/20 text-slate-600 border-slate-500/40" };
  };

  const formatYear = (start: number | null, end: number | null) => {
    if (!start && !end) return "";
    const year = start || end;
    if (!year) return "";
    return `${Math.abs(year)} ${year < 0 ? "BC" : "AD"}`;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <ImageIcon className="w-4 h-4" />
            Image Review
          </CardTitle>
          <CardDescription>
            Click on a coin to review and assign images from auction sources.
            {coinsData && (
              <span className="ml-2">
                Showing {coinsData.items.length} of {coinsData.total} coins
              </span>
            )}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Coins Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : coinsData && coinsData.items.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {coinsData.items.map((coin) => {
            const status = getImageStatus(coin);
            return (
              <Card 
                key={coin.id}
                className="cursor-pointer hover:border-primary/50 transition-all group"
                onClick={() => setSelectedCoin(coin)}
              >
                <CardContent className="p-3">
                  {/* Coin Image */}
                  <div className="aspect-square rounded-lg overflow-hidden bg-muted mb-3 relative">
                    {coin.primary_image ? (
                      <img 
                        src={`/api${coin.primary_image}`}
                        alt={coin.issuing_authority}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <ImageOff className="w-12 h-12 text-muted-foreground/30" />
                      </div>
                    )}
                    
                    {/* Status overlay */}
                    <div className="absolute top-2 right-2">
                      <Badge variant="outline" className={cn("text-xs", status.color)}>
                        {status.label}
                      </Badge>
                    </div>
                    
                    {/* Hover overlay */}
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <Button size="sm" variant="secondary">
                        <ImageIcon className="w-4 h-4 mr-2" />
                        Manage Images
                      </Button>
                    </div>
                  </div>
                  
                  {/* Coin Info */}
                  <div className="space-y-1">
                    <Link 
                      to={`/coins/${coin.id}`}
                      className="font-medium text-sm truncate block hover:text-primary"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {coin.issuing_authority}
                    </Link>
                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                      <span className="truncate">{coin.denomination}</span>
                      {coin.mint_year_start && (
                        <span className="text-muted-foreground/60">
                          {formatYear(coin.mint_year_start, coin.mint_year_end)}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 mt-2">
                      {coin.metal && <MetalBadge metal={coin.metal} size="xs" />}
                      {coin.grade && (
                        <Badge variant="outline" className="text-xs">
                          {coin.grade}
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <ImageOff className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No coins found matching your filters</p>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {coinsData && coinsData.pages > 1 && (
        <div className="flex items-center justify-between pt-4">
          <span className="text-sm text-muted-foreground">
            Page {coinsData.page} of {coinsData.pages}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= coinsData.pages}
              onClick={() => setPage(p => p + 1)}
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Image Selection Dialog */}
      <Dialog open={!!selectedCoin} onOpenChange={(open) => !open && setSelectedCoin(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <span>Select Images for</span>
              <Link 
                to={`/coins/${selectedCoin?.id}`}
                className="text-primary hover:underline"
              >
                {selectedCoin?.issuing_authority} - {selectedCoin?.denomination}
              </Link>
            </DialogTitle>
          </DialogHeader>
          
          <div className="flex-1 overflow-y-auto space-y-6 py-4">
            {/* Current Selection Summary */}
            <div className="grid grid-cols-3 gap-4">
              <Card className={cn(
                "border-2 transition-colors",
                assignment.obverse ? "border-blue-500" : "border-dashed"
              )}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <CircleDot className="w-4 h-4 text-blue-500" />
                    Obverse
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {assignment.obverse ? (
                    <div className="aspect-square rounded overflow-hidden relative group">
                      <img src={assignment.obverse} alt="Obverse" className="w-full h-full object-cover" />
                      <button
                        onClick={() => setAssignment(prev => ({ ...prev, obverse: null }))}
                        className="absolute top-1 right-1 p-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="w-3 h-3 text-white" />
                      </button>
                    </div>
                  ) : (
                    <div className="aspect-square rounded border-2 border-dashed flex items-center justify-center text-muted-foreground">
                      <span className="text-xs">Click image below</span>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              <Card className={cn(
                "border-2 transition-colors",
                assignment.reverse ? "border-green-500" : "border-dashed"
              )}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <RotateCcw className="w-4 h-4 text-green-500" />
                    Reverse
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {assignment.reverse ? (
                    <div className="aspect-square rounded overflow-hidden relative group">
                      <img src={assignment.reverse} alt="Reverse" className="w-full h-full object-cover" />
                      <button
                        onClick={() => setAssignment(prev => ({ ...prev, reverse: null }))}
                        className="absolute top-1 right-1 p-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X className="w-3 h-3 text-white" />
                      </button>
                    </div>
                  ) : (
                    <div className="aspect-square rounded border-2 border-dashed flex items-center justify-center text-muted-foreground">
                      <span className="text-xs">Click image below</span>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              <Card className="border-2 border-dashed">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <ImageIcon className="w-4 h-4 text-orange-500" />
                    Misc ({assignment.misc.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="aspect-square rounded border-2 border-dashed flex items-center justify-center text-muted-foreground">
                    <span className="text-xs text-center px-2">
                      {assignment.misc.length} additional images
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Available Images */}
            <div>
              <h3 className="font-medium mb-3">Available Auction Images</h3>
              {loadingImages ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              ) : coinImages.length > 0 ? (
                <div className="grid grid-cols-4 gap-3">
                  {coinImages.map((img, idx) => {
                    const isObverse = assignment.obverse === img.url;
                    const isReverse = assignment.reverse === img.url;
                    const isMisc = assignment.misc.includes(img.url);
                    const isSelected = isObverse || isReverse || isMisc;
                    
                    return (
                      <div
                        key={idx}
                        className={cn(
                          "relative rounded-lg overflow-hidden border-2 transition-all group",
                          isObverse && "border-blue-500 ring-2 ring-blue-500/20",
                          isReverse && "border-green-500 ring-2 ring-green-500/20",
                          isMisc && "border-orange-500 ring-2 ring-orange-500/20",
                          !isSelected && "border-transparent hover:border-muted-foreground/50"
                        )}
                      >
                        <img 
                          src={img.url.startsWith('//') ? `https:${img.url}` : img.url}
                          alt={`Auction image ${idx + 1}`}
                          className="w-full aspect-square object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/placeholder.png';
                          }}
                        />
                        
                        {/* Source badge */}
                        <div className="absolute top-1 left-1">
                          <Badge variant="secondary" className="text-xs bg-black/60 text-white border-0">
                            {img.source}
                          </Badge>
                        </div>
                        
                        {/* Selection indicator */}
                        {isSelected && (
                          <div className="absolute top-1 right-1">
                            <Badge className={cn(
                              "text-xs",
                              isObverse && "bg-blue-500",
                              isReverse && "bg-green-500",
                              isMisc && "bg-orange-500"
                            )}>
                              {isObverse ? "OBV" : isReverse ? "REV" : "MISC"}
                            </Badge>
                          </div>
                        )}
                        
                        {/* Action buttons */}
                        <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 p-2">
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant={isObverse ? "default" : "secondary"}
                              className={cn("h-8", isObverse && "bg-blue-500 hover:bg-blue-600")}
                              onClick={() => handleSelectImage(img.url, "obverse")}
                            >
                              <CircleDot className="w-3 h-3 mr-1" />
                              Obv
                            </Button>
                            <Button
                              size="sm"
                              variant={isReverse ? "default" : "secondary"}
                              className={cn("h-8", isReverse && "bg-green-500 hover:bg-green-600")}
                              onClick={() => handleSelectImage(img.url, "reverse")}
                            >
                              <RotateCcw className="w-3 h-3 mr-1" />
                              Rev
                            </Button>
                          </div>
                          <Button
                            size="sm"
                            variant={isMisc ? "default" : "secondary"}
                            className={cn("h-7 text-xs", isMisc && "bg-orange-500 hover:bg-orange-600")}
                            onClick={() => handleSelectImage(img.url, "misc")}
                          >
                            {isMisc ? "Remove from Misc" : "Add to Misc"}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 text-xs text-white"
                            onClick={() => window.open(img.url.startsWith('//') ? `https:${img.url}` : img.url, '_blank')}
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            Full Size
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No auction images available for this coin
                </div>
              )}
            </div>
          </div>
          
          {/* Footer */}
          <div className="flex items-center justify-between pt-4 border-t">
            <div className="text-sm text-muted-foreground">
              {assignment.obverse && assignment.reverse ? (
                <span className="text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  Both sides selected
                </span>
              ) : (
                <span>Select obverse and reverse images</span>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setSelectedCoin(null)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSave}
                disabled={saveMutation.isPending || (!assignment.obverse && !assignment.reverse && assignment.misc.length === 0)}
              >
                {saveMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Images
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
