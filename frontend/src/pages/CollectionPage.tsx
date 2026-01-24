import { useCoins } from "@/hooks/useCoins";
import { CoinCard } from "@/components/coins/CoinCard";
import { CoinFilters } from "@/components/coins/CoinFilters";
import { useUIStore } from "@/stores/uiStore";
import { useFilterStore, SortField } from "@/stores/filterStore";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Grid3x3, Table2, ArrowUpDown, ArrowUp, ArrowDown,
  Calendar, User, Coins, CircleDot, Award, DollarSign, Clock, Scale, Sparkles
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";

const SORT_OPTIONS: { value: SortField; label: string; icon: React.ReactNode }[] = [
  { value: "year", label: "Year", icon: <Calendar className="w-4 h-4" /> },
  { value: "name", label: "Ruler", icon: <User className="w-4 h-4" /> },
  { value: "category", label: "Category", icon: <Grid3x3 className="w-4 h-4" /> },
  { value: "denomination", label: "Denomination", icon: <Coins className="w-4 h-4" /> },
  { value: "metal", label: "Metal", icon: <CircleDot className="w-4 h-4" /> },
  { value: "weight", label: "Weight", icon: <Scale className="w-4 h-4" /> },
  { value: "grade", label: "Grade", icon: <Award className="w-4 h-4" /> },
  { value: "rarity", label: "Rarity", icon: <Sparkles className="w-4 h-4" /> },
  { value: "price", label: "Cost", icon: <DollarSign className="w-4 h-4" /> },
  { value: "value", label: "Value", icon: <DollarSign className="w-4 h-4" /> },
  { value: "acquired", label: "Acquired", icon: <Clock className="w-4 h-4" /> },
  { value: "created", label: "Added", icon: <Clock className="w-4 h-4" /> },
];

// Helper to format year display
function formatYear(year: number | null | undefined, isCirca?: boolean): string {
  if (!year) return "—";
  const yearStr = year < 0 ? `${Math.abs(year)} BCE` : `${year} CE`;
  return isCirca ? `c. ${yearStr}` : yearStr;
}

// Format year range
function formatYearRange(start: number | null | undefined, end: number | null | undefined, isCirca?: boolean): string {
  if (!start && !end) return "—";
  const prefix = isCirca ? "c. " : "";
  
  if (start && end && start !== end) {
    const startStr = start < 0 ? `${Math.abs(start)} BCE` : `${start}`;
    const endStr = end < 0 ? `${Math.abs(end)} BCE` : `${end} CE`;
    return `${prefix}${startStr}–${endStr}`;
  }
  
  return formatYear(start || end, isCirca);
}

export function CollectionPage() {
  const { data, isLoading, error } = useCoins();
  const { viewMode, setViewMode } = useUIStore();
  const { sortBy, sortDir, setSort, toggleSortDir } = useFilterStore();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-pulse flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-muted-foreground">Loading collection...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-destructive">Error loading coins: {error.message}</div>
      </div>
    );
  }

  const currentSortOption = SORT_OPTIONS.find(o => o.value === sortBy);

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      <CoinFilters />
      <div className="flex-1 overflow-auto p-6">
        {/* Header with count and controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Collection</h1>
            <p className="text-muted-foreground text-sm">
              {data?.total || 0} {data?.total === 1 ? "coin" : "coins"}
            </p>
          </div>
          
          {/* Sort and View Controls */}
          <div className="flex items-center gap-3">
            {/* Sort Dropdown */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground hidden sm:inline">Sort by</span>
              <Select value={sortBy} onValueChange={(v) => setSort(v as SortField)}>
                <SelectTrigger className="w-[140px] h-9">
                  <div className="flex items-center gap-2">
                    {currentSortOption?.icon}
                    <SelectValue />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  {SORT_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      <div className="flex items-center gap-2">
                        {option.icon}
                        <span>{option.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {/* Sort Direction Toggle */}
              <Button
                variant="outline"
                size="icon"
                className="h-9 w-9"
                onClick={toggleSortDir}
                title={sortDir === "asc" ? "Ascending (oldest first)" : "Descending (newest first)"}
              >
                {sortDir === "asc" ? (
                  <ArrowUp className="w-4 h-4" />
                ) : (
                  <ArrowDown className="w-4 h-4" />
                )}
              </Button>
            </div>
            
            {/* Divider */}
            <div className="w-px h-6 bg-border hidden sm:block" />
            
            {/* View Mode Toggle */}
            <div className="flex items-center rounded-lg border bg-muted p-1">
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="sm"
                className="h-7 px-2"
                onClick={() => setViewMode("grid")}
              >
                <Grid3x3 className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === "table" ? "default" : "ghost"}
                size="sm"
                className="h-7 px-2"
                onClick={() => setViewMode("table")}
              >
                <Table2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Grid View */}
        {viewMode === "grid" ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {data?.items.map((coin) => (
              <CoinCard key={coin.id} coin={coin} />
            ))}
          </div>
        ) : (
          /* Table View */
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
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
                    Year
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
                      "border-b hover:bg-muted/50 cursor-pointer transition-colors",
                      index % 2 === 0 ? "bg-background" : "bg-muted/20"
                    )}
                    onClick={() => navigate(`/coins/${coin.id}`)}
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{coin.issuing_authority}</span>
                        {coin.is_test_cut && (
                          <Badge variant="destructive" className="text-[10px] px-1 py-0">
                            TC
                          </Badge>
                        )}
                      </div>
                    </td>
                    <td className="p-4">{coin.denomination}</td>
                    <td className="p-4 capitalize">{coin.metal}</td>
                    <td className="p-4 text-muted-foreground tabular-nums">
                      {formatYearRange(coin.mint_year_start, coin.mint_year_end, coin.is_circa)}
                    </td>
                    <td className="p-4">{coin.grade || "—"}</td>
                    <td className="p-4 text-right font-medium tabular-nums">
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
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
              <Coins className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium mb-1">No coins found</h3>
            <p className="text-muted-foreground text-sm max-w-sm">
              Try adjusting your filters or add your first coin to start building your collection.
            </p>
          </div>
        )}
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
        "text-left p-4 font-medium text-sm select-none cursor-pointer hover:bg-muted/50 transition-colors",
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
        {isActive ? (
          sortDir === "asc" ? (
            <ArrowUp className="w-3.5 h-3.5 text-primary" />
          ) : (
            <ArrowDown className="w-3.5 h-3.5 text-primary" />
          )
        ) : (
          <ArrowUpDown className="w-3.5 h-3.5 text-muted-foreground/50" />
        )}
      </div>
    </th>
  );
}
