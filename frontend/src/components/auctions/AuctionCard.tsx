import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Calendar, Gavel } from "lucide-react";
import { AuctionListItem } from "@/hooks/useAuctions";

interface AuctionCardProps {
  auction: AuctionListItem;
  onSelect: (auction: AuctionListItem) => void;
}

export function AuctionCard({ auction, onSelect }: AuctionCardProps) {
  return (
    <Card 
      className="cursor-pointer hover:shadow-md transition-shadow overflow-hidden"
      onClick={() => onSelect(auction)}
    >
      <div className="aspect-square bg-muted relative">
        {auction.thumbnail ? (
          <img src={auction.thumbnail} alt={auction.lot_number || "Lot"} className="w-full h-full object-cover" />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <Gavel className="w-8 h-8 opacity-20" />
          </div>
        )}
        <Badge className="absolute top-2 right-2 shadow-sm" variant="secondary">
          {auction.auction_house}
        </Badge>
      </div>
      
      <CardHeader className="p-3 pb-0">
        <h3 className="font-semibold text-sm truncate">{auction.sale_name || "Unknown Sale"}</h3>
        <p className="text-xs text-muted-foreground">Lot {auction.lot_number}</p>
      </CardHeader>
      
      <CardContent className="p-3 pt-2 space-y-2">
        <div className="flex items-center text-xs text-muted-foreground">
          <Calendar className="w-3 h-3 mr-1" />
          {auction.auction_date || "Date Unknown"}
        </div>
        
        <div className="flex justify-between items-end">
          <div className="text-sm font-bold">
            {auction.hammer_price 
              ? `${auction.currency} ${auction.hammer_price.toLocaleString()}`
              : "Unsold"}
          </div>
          {auction.url && <ExternalLink className="w-3 h-3 text-muted-foreground" />}
        </div>
      </CardContent>
    </Card>
  );
}