import { ExternalLink, Calendar, DollarSign, Award, ImageOff } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { AuctionListItem } from "@/hooks/useAuctions";

interface AuctionCardProps {
  auction: AuctionListItem;
  onSelect?: (auction: AuctionListItem) => void;
  compact?: boolean;
}

export function AuctionCard({ auction, onSelect, compact = false }: AuctionCardProps) {
  const formatPrice = (price: number | undefined, currency: string = "USD") => {
    if (price === undefined || price === null) return "N/A";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return "Unknown date";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  const getHouseColor = (house: string) => {
    const colors: Record<string, string> = {
      Heritage: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
      CNG: "bg-green-500/10 text-green-700 dark:text-green-400",
      Biddr: "bg-purple-500/10 text-purple-700 dark:text-purple-400",
      eBay: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400",
      Agora: "bg-red-500/10 text-red-700 dark:text-red-400",
    };
    return colors[house] || "bg-gray-500/10 text-gray-700 dark:text-gray-400";
  };

  if (compact) {
    return (
      <div
        className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
        onClick={() => onSelect?.(auction)}
      >
        {auction.primary_photo_url ? (
          <img
            src={auction.primary_photo_url}
            alt={auction.title || "Coin"}
            className="w-10 h-10 object-cover rounded"
          />
        ) : (
          <div className="w-10 h-10 bg-muted rounded flex items-center justify-center">
            <ImageOff className="w-4 h-4 text-muted-foreground" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{auction.title || "Untitled"}</p>
          <p className="text-xs text-muted-foreground">
            {auction.auction_house} - {formatDate(auction.auction_date)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold">
            {formatPrice(auction.hammer_price, auction.currency)}
          </p>
          {auction.sold === false && (
            <Badge variant="outline" className="text-xs">
              Unsold
            </Badge>
          )}
        </div>
      </div>
    );
  }

  return (
    <Card
      className="overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onSelect?.(auction)}
    >
      <div className="aspect-square relative bg-muted">
        {auction.primary_photo_url ? (
          <img
            src={auction.primary_photo_url}
            alt={auction.title || "Coin"}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <ImageOff className="w-12 h-12 text-muted-foreground" />
          </div>
        )}
        <div className="absolute top-2 left-2">
          <Badge className={getHouseColor(auction.auction_house)}>
            {auction.auction_house}
          </Badge>
        </div>
        {auction.sold === false && (
          <div className="absolute top-2 right-2">
            <Badge variant="destructive">Unsold</Badge>
          </div>
        )}
      </div>
      <CardContent className="p-4">
        <h3 className="font-medium text-sm line-clamp-2 mb-2">
          {auction.title || "Untitled Lot"}
        </h3>
        
        <div className="space-y-1.5 text-xs text-muted-foreground">
          {auction.sale_name && (
            <p className="truncate">{auction.sale_name}</p>
          )}
          
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            <span>{formatDate(auction.auction_date)}</span>
          </div>
          
          {auction.lot_number && (
            <p>Lot #{auction.lot_number}</p>
          )}
          
          {auction.grade && (
            <div className="flex items-center gap-1">
              <Award className="w-3 h-3" />
              <span>{auction.grade}</span>
            </div>
          )}
        </div>
        
        <div className="mt-3 pt-3 border-t flex items-center justify-between">
          <div className="flex items-center gap-1 text-lg font-semibold">
            <DollarSign className="w-4 h-4" />
            {auction.hammer_price !== undefined && auction.hammer_price !== null
              ? formatPrice(auction.hammer_price, auction.currency).replace("$", "")
              : "N/A"}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={(e) => {
              e.stopPropagation();
              window.open(auction.url, "_blank");
            }}
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default AuctionCard;
