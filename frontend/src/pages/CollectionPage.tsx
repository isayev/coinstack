import { useCoins } from "@/hooks/useCoins";
import { CoinCard } from "@/components/coins/CoinCard";
import { CoinFilters } from "@/components/coins/CoinFilters";
import { useUIStore } from "@/stores/uiStore";
import { useFilterStore, SortField } from "@/stores/filterStore";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Grid3x3, ArrowUp, ArrowDown, LayoutGrid,
  Calendar, User, Coins, CircleDot, Award, DollarSign, Clock, Scale, Sparkles, List
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";

const SORT_OPTIONS: { value: SortField; label: string; icon: React.ReactNode }[] = [
  { value: "year", label: "Year", icon: <Calendar className="w-3.5 h-3.5" /> },
  { value: "name", label: "Ruler", icon: <User className="w-3.5 h-3.5" /> },
  { value: "category", label: "Category", icon: <Grid3x3 className="w-3.5 h-3.5" /> },
  { value: "denomination", label: "Denomination", icon: <Coins className="w-3.5 h-3.5" /> },
  { value: "metal", label: "Metal", icon: <CircleDot className="w-3.5 h-3.5" /> },
  { value: "weight", label: "Weight", icon: <Scale className="w-3.5 h-3.5" /> },
  { value: "grade", label: "Grade", icon: <Award className="w-3.5 h-3.5" /> },
  { value: "rarity", label: "Rarity", icon: <Sparkles className="w-3.5 h-3.5" /> },
  { value: "price", label: "Cost", icon: <DollarSign className="w-3.5 h-3.5" /> },
  { value: "acquired", label: "Acquired", icon: <Clock className="w-3.5 h-3.5" /> },
  { value: "created", label: "Added", icon: <Clock className="w-3.5 h-3.5" /> },
];

// Helper to format year display
function formatYear(year: number | null | undefined, isCirca?: boolean): string {
  if (!year) return "—";
  const yearStr = year < 0 ? `${Math.abs(year)} BC` : `${year} AD`;
  return isCirca ? `c. ${yearStr}` : yearStr;
}

// Format year range
function formatYearRange(start: number | null | undefined, end: number | null | undefined, isCirca?: boolean): string {
  if (!start && !end) return "—";
  const prefix = isCirca ? "c. " : "";
  
  if (start && end && start !== end) {
    const startStr = start < 0 ? `${Math.abs(start)}` : `${start}`;
    const endStr = end < 0 ? `${Math.abs(end)} BC` : `${end} AD`;
    const startSuffix = start < 0 && end >= 0 ? " BC" : "";
    return `${prefix}${startStr}${startSuffix}–${endStr}`;
  }
  
  return formatYear(start || end, isCirca);
}

// Get metal badge class for table
function getMetalClass(metal: string): string {
  const metalMap: Record<string, string> = {
    gold: "badge-metal-gold",
    electrum: "badge-metal-electrum",
    silver: "badge-metal-silver",
    bronze: "badge-metal-bronze",
    copper: "badge-metal-copper",
    billon: "badge-metal-billon",
    orichalcum: "badge-metal-orichalcum",
    lead: "badge-metal-lead",
    potin: "badge-metal-potin",
    ae: "badge-metal-ae",
  };
  return metalMap[metal?.toLowerCase()] || "";
}

export function CollectionPage() {
  const { data, isLoading, error } = useCoins();
  const { viewMode, setViewMode } = useUIStore();
  const { sortBy, sortDir, setSort, toggleSortDir, getActiveFilterCount } = useFilterStore();
  const navigate = useNavigate();

  const activeFilters = getActiveFilterCount();

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)]">
        <CoinFilters />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-muted-foreground text-sm">Loading collection...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)]">
        <CoinFilters />
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-destructive bg-destructive/10 px-4 py-3 rounded-lg">
            Error loading coins: {error.message}
          </div>
        </div>
      </div>
    );
  }

  const currentSortOption = SORT_OPTIONS.find(o => o.value === sortBy);

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      <CoinFilters />
      <div className="flex-1 overflow-auto scrollbar-thin">
        {/* Header bar */}
        <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b px-4 py-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            {/* Left: Title and count */}
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-xl font-bold tracking-tight">Collection</h1>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span className="tabular-nums font-medium">{data?.total || 0}</span>
                  <span>{data?.total === 1 ? "coin" : "coins"}</span>
                  {activeFilters > 0 && (
                    <Badge variant="secondary" className="text-[10px] h-5 px-1.5">
                      {activeFilters} filter{activeFilters > 1 ? "s" : ""}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            
            {/* Right: Controls */}
            <div className="flex items-center gap-2">
              {/* Sort control */}
              <div className="flex items-center gap-1.5">
                <Select value={sortBy} onValueChange={(v) => setSort(v as SortField)}>
                  <SelectTrigger className="w-[130px] h-8 text-xs">
                    <div className="flex items-center gap-1.5">
                      {currentSortOption?.icon}
                      <SelectValue />
                    </div>
                  </SelectTrigger>
                  <SelectContent>
                    {SORT_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value} className="text-xs">
                        <div className="flex items-center gap-2">
                          {option.icon}
                          <span>{option.label}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                <Button
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={toggleSortDir}
                  title={sortDir === "asc" ? "Oldest first" : "Newest first"}
                >
                  {sortDir === "asc" ? (
                    <ArrowUp className="w-3.5 h-3.5" />
                  ) : (
                    <ArrowDown className="w-3.5 h-3.5" />
                  )}
                </Button>
              </div>
              
              {/* Divider */}
              <div className="w-px h-5 bg-border" />
              
              {/* View mode toggle */}
              <div className="flex items-center rounded-md border bg-muted/50 p-0.5">
                <Button
                  variant={viewMode === "grid" ? "default" : "ghost"}
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setViewMode("grid")}
                  title="Grid view"
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                </Button>
                <Button
                  variant={viewMode === "table" ? "default" : "ghost"}
                  size="sm"
                  className="h-7 w-7 p-0"
                  onClick={() => setViewMode("table")}
                  title="Table view"
                >
                  <List className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {/* Grid View - More columns on larger screens */}
          {viewMode === "grid" ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-3">
              {data?.items.map((coin) => (
                <CoinCard key={coin.id} coin={coin} />
              ))}
            </div>
          ) : (
            /* Table View - Refined styling */
            <div className="border rounded-lg overflow-hidden bg-card">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/30">
                    <TableHeader field="name" currentSort={sortBy} sortDir={sortDir} onSort={setSort}>
                      Ruler
                    </TableHeader>
                    <TableHeader field="denomination" currentSort={sortBy} sortDir={sortDir} onSort={setSort}>
                      Denomination
                    </TableHeader>
                    <TableHeader field="metal" currentSort={sortBy} sortDir={sortDir} onSort={setSort}>
                      Metal
                    </TableHeader>
                    <TableHeader field="year" currentSort={sortBy} sortDir={sortDir} onSort={setSort}>
                      Date
                    </TableHeader>
                    <TableHeader field="grade" currentSort={sortBy} sortDir={sortDir} onSort={setSort}>
                      Grade
                    </TableHeader>
                    <TableHeader field="price" currentSort={sortBy} sortDir={sortDir} onSort={setSort} className="text-right">
                      Price
                    </TableHeader>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((coin, index) => (
                    <tr 
                      key={coin.id} 
                      className={cn(
                        "border-b last:border-0 hover:bg-muted/40 cursor-pointer transition-colors",
                        index % 2 === 0 ? "bg-transparent" : "bg-muted/10"
                      )}
                      onClick={() => navigate(`/coins/${coin.id}`)}
                    >
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{coin.issuing_authority}</span>
                          {coin.is_test_cut && (
                            <Badge variant="outline" className="badge-test-cut text-[9px] px-1 py-0 h-4">
                              TC
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">{coin.denomination}</td>
                      <td className="px-4 py-2.5">
                        <Badge variant="outline" className={cn("text-[10px] capitalize", getMetalClass(coin.metal))}>
                          {coin.metal}
                        </Badge>
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground tabular-nums text-xs">
                        {formatYearRange(coin.mint_year_start, coin.mint_year_end, coin.is_circa)}
                      </td>
                      <td className="px-4 py-2.5 text-xs">{coin.grade || "—"}</td>
                      <td className="px-4 py-2.5 text-right font-medium tabular-nums">
                        {coin.acquisition_price
                          ? `$${Number(coin.acquisition_price).toLocaleString()}`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Empty State */}
          {data && data.items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
                <Coins className="w-8 h-8 text-muted-foreground/50" />
              </div>
              <h3 className="text-lg font-semibold mb-1">No coins found</h3>
              <p className="text-muted-foreground text-sm max-w-xs">
                {activeFilters > 0 
                  ? "Try adjusting your filters to see more results."
                  : "Add your first coin to start building your collection."}
              </p>
              {activeFilters === 0 && (
                <Button className="mt-4" onClick={() => navigate("/coins/new")}>
                  Add Your First Coin
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Sortable table header component
function TableHeader({ 
  field, 
  currentSort, 
  sortDir, 
  onSort, 
  children,
  className 
}: { 
  field: SortField;
  currentSort: SortField;
  sortDir: "asc" | "desc";
  onSort: (field: SortField, dir?: "asc" | "desc") => void;
  children: React.ReactNode;
  className?: string;
}) {
  const isActive = currentSort === field;
  
  return (
    <th 
      className={cn(
        "text-left px-4 py-2.5 font-medium text-xs text-muted-foreground select-none cursor-pointer hover:text-foreground hover:bg-muted/30 transition-colors",
        className
      )}
      onClick={() => {
        if (isActive) {
          onSort(field, sortDir === "asc" ? "desc" : "asc");
        } else {
          onSort(field, "asc");
        }
      }}
    >
      <div className={cn("flex items-center gap-1", className?.includes("text-right") && "justify-end")}>
        <span>{children}</span>
        {isActive && (
          sortDir === "asc" ? (
            <ArrowUp className="w-3 h-3 text-primary" />
          ) : (
            <ArrowDown className="w-3 h-3 text-primary" />
          )
        )}
      </div>
    </th>
  );
}
