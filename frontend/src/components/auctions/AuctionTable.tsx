import { ExternalLink, ChevronUp, ChevronDown, ImageOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import type { AuctionListItem } from "@/hooks/useAuctions";

interface AuctionTableProps {
  auctions: AuctionListItem[];
  onSelect?: (auction: AuctionListItem) => void;
  selectedIds?: Set<number>;
  onSelectionChange?: (ids: Set<number>) => void;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  onSort?: (column: string) => void;
  loading?: boolean;
}

type SortableColumn = "auction_date" | "hammer_price" | "auction_house";

export function AuctionTable({
  auctions,
  onSelect,
  selectedIds = new Set(),
  onSelectionChange,
  sortBy = "auction_date",
  sortOrder = "desc",
  onSort,
  loading = false,
}: AuctionTableProps) {
  const formatPrice = (price: number | undefined, currency: string = "USD") => {
    if (price === undefined || price === null) return "-";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return "-";
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
      Heritage: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
      CNG: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
      Biddr: "bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/20",
      eBay: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20",
      Agora: "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20",
    };
    return colors[house] || "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20";
  };

  const toggleAll = () => {
    if (!onSelectionChange) return;
    if (selectedIds.size === auctions.length) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(auctions.map((a) => a.id)));
    }
  };

  const toggleOne = (id: number) => {
    if (!onSelectionChange) return;
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    onSelectionChange(newSet);
  };

  const SortHeader = ({
    column,
    children,
  }: {
    column: SortableColumn;
    children: React.ReactNode;
  }) => (
    <button
      className="flex items-center gap-1 hover:text-foreground transition-colors"
      onClick={() => onSort?.(column)}
    >
      {children}
      {sortBy === column && (
        sortOrder === "asc" ? (
          <ChevronUp className="w-3.5 h-3.5" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5" />
        )
      )}
    </button>
  );

  if (loading) {
    return (
      <div className="rounded-md border">
        <div className="p-8 text-center text-muted-foreground">Loading auctions...</div>
      </div>
    );
  }

  if (auctions.length === 0) {
    return (
      <div className="rounded-md border">
        <div className="p-8 text-center text-muted-foreground">
          No auction records found
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50">
          <tr className="border-b">
            {onSelectionChange && (
              <th className="w-10 p-3">
                <Checkbox
                  checked={selectedIds.size === auctions.length && auctions.length > 0}
                  onCheckedChange={toggleAll}
                />
              </th>
            )}
            <th className="w-12 p-3"></th>
            <th className="p-3 text-left font-medium text-muted-foreground">
              Title
            </th>
            <th className="p-3 text-left font-medium text-muted-foreground">
              <SortHeader column="auction_house">House</SortHeader>
            </th>
            <th className="p-3 text-left font-medium text-muted-foreground">
              <SortHeader column="auction_date">Date</SortHeader>
            </th>
            <th className="p-3 text-left font-medium text-muted-foreground">
              Grade
            </th>
            <th className="p-3 text-right font-medium text-muted-foreground">
              <SortHeader column="hammer_price">Hammer</SortHeader>
            </th>
            <th className="p-3 text-center font-medium text-muted-foreground">
              Status
            </th>
            <th className="w-10 p-3"></th>
          </tr>
        </thead>
        <tbody>
          {auctions.map((auction) => (
            <tr
              key={auction.id}
              className="border-b hover:bg-muted/30 cursor-pointer transition-colors"
              onClick={() => onSelect?.(auction)}
            >
              {onSelectionChange && (
                <td className="p-3" onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={selectedIds.has(auction.id)}
                    onCheckedChange={() => toggleOne(auction.id)}
                  />
                </td>
              )}
              <td className="p-3">
                {auction.primary_photo_url ? (
                  <img
                    src={auction.primary_photo_url}
                    alt=""
                    className="w-8 h-8 object-cover rounded"
                  />
                ) : (
                  <div className="w-8 h-8 bg-muted rounded flex items-center justify-center">
                    <ImageOff className="w-3.5 h-3.5 text-muted-foreground" />
                  </div>
                )}
              </td>
              <td className="p-3">
                <p className="font-medium line-clamp-1">{auction.title || "Untitled"}</p>
                {auction.sale_name && (
                  <p className="text-xs text-muted-foreground line-clamp-1">
                    {auction.sale_name}
                    {auction.lot_number && ` - Lot #${auction.lot_number}`}
                  </p>
                )}
              </td>
              <td className="p-3">
                <Badge variant="outline" className={getHouseColor(auction.auction_house)}>
                  {auction.auction_house}
                </Badge>
              </td>
              <td className="p-3 text-muted-foreground">
                {formatDate(auction.auction_date)}
              </td>
              <td className="p-3 text-muted-foreground">{auction.grade || "-"}</td>
              <td className="p-3 text-right font-medium">
                {formatPrice(auction.hammer_price, auction.currency)}
              </td>
              <td className="p-3 text-center">
                {auction.sold === false ? (
                  <Badge variant="outline" className="text-xs bg-red-500/10 text-red-700 dark:text-red-400">
                    Unsold
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-xs bg-green-500/10 text-green-700 dark:text-green-400">
                    Sold
                  </Badge>
                )}
              </td>
              <td className="p-3" onClick={(e) => e.stopPropagation()}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => window.open(auction.url, "_blank")}
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AuctionTable;
