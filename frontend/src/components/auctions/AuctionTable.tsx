import { AuctionListItem } from "@/hooks/useAuctions";
import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface AuctionTableProps {
  auctions: AuctionListItem[];
  onSelect: (auction: AuctionListItem) => void;
  sortBy: string;
  sortOrder: "asc" | "desc";
  onSort: (column: string) => void;
  loading?: boolean;
}

export function AuctionTable({ auctions, onSelect }: AuctionTableProps) {
  return (
    <div className="rounded-md border">
      <table className="w-full text-sm text-left">
        <thead className="bg-muted/50 text-muted-foreground font-medium">
          <tr>
            <th className="px-4 py-3">Auction House</th>
            <th className="px-4 py-3">Sale</th>
            <th className="px-4 py-3">Lot</th>
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3 text-right">Price</th>
            <th className="px-4 py-3 w-10"></th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {auctions.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                No auctions found
              </td>
            </tr>
          ) : (
            auctions.map((auction) => (
              <tr 
                key={auction.id} 
                className="hover:bg-muted/50 cursor-pointer"
                onClick={() => onSelect(auction)}
              >
                <td className="px-4 py-3 font-medium">{auction.auction_house}</td>
                <td className="px-4 py-3 text-muted-foreground">{auction.sale_name}</td>
                <td className="px-4 py-3 font-mono">{auction.lot_number}</td>
                <td className="px-4 py-3 text-muted-foreground">{auction.auction_date}</td>
                <td className="px-4 py-3 text-right font-bold">
                  {auction.hammer_price 
                    ? `${auction.currency} ${auction.hammer_price.toLocaleString()}`
                    : <Badge variant="outline" className="text-[10px]">Unsold</Badge>
                  }
                </td>
                <td className="px-4 py-3">
                  <ExternalLink className="w-4 h-4 text-muted-foreground" />
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}