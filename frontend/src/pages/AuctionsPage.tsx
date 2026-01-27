import { useState } from "react";
import { Plus, Search, Grid, List, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrapeDialog } from "@/components/auctions";
import { AuctionListV2 } from "@/features/auctions/AuctionListV2";
import {
  useAuctionHouses,
  type AuctionFilters,
} from "@/hooks/useAuctions";

type ViewMode = "grid" | "table";

export function AuctionsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [sortBy, setSortBy] = useState("auction_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [scrapeDialogOpen, setScrapeDialogOpen] = useState(false);

  // Filters
  const [filters, setFilters] = useState<AuctionFilters>({});
  const [searchTerm, setSearchTerm] = useState("");

  const { data: auctionHouses } = useAuctionHouses();

  const handleFilterChange = (key: keyof AuctionFilters, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value === "all" ? undefined : value,
    }));
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setFilters(prev => ({ ...prev, search: searchTerm || undefined }));
  };

  const handleScrapeComplete = () => {
    // List will refetch automatically if keys change or via queryClient invalidation
    // For now, just close dialog
    setScrapeDialogOpen(false);
    window.location.reload(); // Simple reload to refresh data
  };



  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Auction Records</h1>
          <p className="text-muted-foreground">
            Track auction appearances and comparable sales
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => setScrapeDialogOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Scrape URL
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <form onSubmit={handleSearch} className="flex-1 min-w-[200px] max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search auctions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </form>

        <Select
          value={filters.auction_house || "all"}
          onValueChange={(v) => handleFilterChange("auction_house", v)}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All Houses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Houses</SelectItem>
            {auctionHouses?.map((house) => (
              <SelectItem key={house} value={house}>
                {house}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.sold === undefined ? "all" : filters.sold ? "sold" : "unsold"}
          onValueChange={(v) =>
            handleFilterChange("sold", v === "all" ? undefined : v === "sold" ? "true" : "false")
          }
        >
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="sold">Sold</SelectItem>
            <SelectItem value="unsold">Unsold</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex items-center border rounded-md">
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="sm"
            className="rounded-r-none"
            onClick={() => setViewMode("grid")}
            title="Grid View"
          >
            <Grid className="w-4 h-4" />
          </Button>
          <Button
            variant={viewMode === "table" ? "secondary" : "ghost"}
            size="sm"
            className="rounded-l-none"
            onClick={() => setViewMode("table")}
            title="Table View"
          >
            <List className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Main Content: AuctionListV2 matches CoinListV3 pattern */}
      <AuctionListV2
        filters={filters}
        viewMode={viewMode}
        setViewMode={setViewMode}
        sortBy={sortBy}
        setSortBy={setSortBy}
        sortOrder={sortOrder}
        setSortOrder={setSortOrder}
      />

      {/* Scrape Dialog */}
      <ScrapeDialog
        open={scrapeDialogOpen}
        onOpenChange={setScrapeDialogOpen}
        onComplete={handleScrapeComplete}
      />
    </div>
  );
}

export default AuctionsPage;
