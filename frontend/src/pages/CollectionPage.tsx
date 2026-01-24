/**
 * CollectionPage - Main coin collection view
 * 
 * Features:
 * - Grid view with hover-interactive cards
 * - Table view with sortable columns
 * - Sidebar with stats, filters, and alerts
 * - 5 columns optimal for desktop
 * 
 * @module pages/CollectionPage
 */

import { useCoins } from "@/hooks/useCoins";
import { CoinCard } from "@/components/coins/CoinCard";
import { CollectionSidebar } from "@/components/coins/CollectionSidebar";
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
import { 
  MetalBadge, 
  GradeBadge,
} from "@/components/design-system";

// ============================================================================
// SORT OPTIONS
// ============================================================================

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

// ============================================================================
// HELPERS
// ============================================================================

function formatYearRange(
  start: number | null | undefined, 
  end: number | null | undefined, 
  isCirca?: boolean
): string {
  if (!start && !end) return "—";
  const prefix = isCirca ? "c. " : "";
  
  if (start && end && start !== end) {
    const startStr = start < 0 ? `${Math.abs(start)}` : `${start}`;
    const endStr = end < 0 ? `${Math.abs(end)} BC` : `${end} AD`;
    const startSuffix = start < 0 && end > 0 ? " BC" : "";
    return `${prefix}${startStr}${startSuffix}–${endStr}`;
  }
  
  const year = start || end;
  if (!year) return "—";
  return `${prefix}${Math.abs(year)} ${year < 0 ? "BC" : "AD"}`;
}

// ============================================================================
// TABLE HEADER
// ============================================================================

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
        "text-left px-4 py-2.5 font-medium text-xs select-none cursor-pointer transition-colors",
        className
      )}
      style={{ color: isActive ? 'var(--metal-au)' : 'var(--text-tertiary)' }}
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
            <ArrowUp className="w-3 h-3" />
          ) : (
            <ArrowDown className="w-3 h-3" />
          )
        )}
      </div>
    </th>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function CollectionPage() {
  const { data, isLoading, error } = useCoins();
  const { viewMode, setViewMode } = useUIStore();
  const { sortBy, sortDir, setSort, toggleSortDir, getActiveFilterCount } = useFilterStore();
  const navigate = useNavigate();

  const activeFilters = getActiveFilterCount();

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)]">
        <CollectionSidebar totalCoins={0} />
        <div 
          className="flex-1 flex items-center justify-center"
          style={{ background: 'var(--bg-base)' }}
        >
          <div className="flex flex-col items-center gap-3">
            <div 
              className="w-10 h-10 border-2 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: 'var(--metal-au)', borderTopColor: 'transparent' }}
            />
            <span style={{ color: 'var(--text-secondary)' }}>Loading collection...</span>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)]">
        <CollectionSidebar totalCoins={0} />
        <div 
          className="flex-1 flex items-center justify-center p-6"
          style={{ background: 'var(--bg-base)' }}
        >
          <div 
            className="px-4 py-3 rounded-lg"
            style={{ background: 'rgba(255, 69, 58, 0.15)', color: '#FF453A' }}
          >
            Error loading coins: {error.message}
          </div>
        </div>
      </div>
    );
  }

  const currentSortOption = SORT_OPTIONS.find(o => o.value === sortBy);

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      {/* Sidebar */}
      <CollectionSidebar totalCoins={data?.total || 0} />
      
      {/* Main content */}
      <div 
        className="flex-1 overflow-auto scrollbar-thin"
        style={{ background: 'var(--bg-base)' }}
      >
        {/* Header bar */}
        <div 
          className="sticky top-0 z-10 backdrop-blur px-4 py-3"
          style={{ 
            background: 'var(--bg-base)/95',
            borderBottom: '1px solid var(--border-subtle)'
          }}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            {/* Left: Title and count */}
            <div>
              <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
                Collection
              </h1>
              <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                <span className="tabular-nums font-medium">{data?.total || 0}</span>
                <span>{data?.total === 1 ? "coin" : "coins"}</span>
                {activeFilters > 0 && (
                  <Badge 
                    className="text-[10px] h-5 px-1.5"
                    style={{ 
                      background: 'var(--metal-au-subtle)', 
                      color: 'var(--metal-au-text)',
                      border: '1px solid var(--metal-au-border)'
                    }}
                  >
                    {activeFilters} filter{activeFilters > 1 ? "s" : ""}
                  </Badge>
                )}
              </div>
            </div>
            
            {/* Right: Controls */}
            <div className="flex items-center gap-2">
              {/* Sort control */}
              <div className="flex items-center gap-1.5">
                <Select value={sortBy} onValueChange={(v) => setSort(v as SortField)}>
                  <SelectTrigger 
                    className="w-[130px] h-8 text-xs"
                    style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
                  >
                    <div className="flex items-center gap-1.5">
                      {currentSortOption?.icon}
                      <SelectValue />
                    </div>
                  </SelectTrigger>
                  <SelectContent style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}>
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
                  style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
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
              <div className="w-px h-5" style={{ background: 'var(--border-subtle)' }} />
              
              {/* View mode toggle */}
              <div 
                className="flex items-center rounded-md p-0.5"
                style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}
              >
                <Button
                  variant={viewMode === "grid" ? "default" : "ghost"}
                  size="sm"
                  className="h-7 w-7 p-0"
                  style={viewMode === "grid" ? { background: 'var(--metal-au)', color: 'var(--bg-base)' } : {}}
                  onClick={() => setViewMode("grid")}
                  title="Grid view"
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                </Button>
                <Button
                  variant={viewMode === "table" ? "default" : "ghost"}
                  size="sm"
                  className="h-7 w-7 p-0"
                  style={viewMode === "table" ? { background: 'var(--metal-au)', color: 'var(--bg-base)' } : {}}
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
          {/* Grid View - 5 columns optimal */}
          {viewMode === "grid" ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-5 gap-4">
              {data?.items.map((coin) => (
                <CoinCard key={coin.id} coin={coin} />
              ))}
            </div>
          ) : (
            /* Table View */
            <div 
              className="rounded-lg overflow-hidden"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)' }}
            >
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-subtle)' }}>
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
                      className="cursor-pointer transition-colors"
                      style={{ 
                        borderBottom: '1px solid var(--border-subtle)',
                        background: index % 2 === 0 ? 'transparent' : 'var(--bg-surface)'
                      }}
                      onClick={() => navigate(`/coins/${coin.id}`)}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-elevated)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = index % 2 === 0 ? 'transparent' : 'var(--bg-surface)'}
                    >
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <span className="font-medium" style={{ color: 'var(--text-primary)' }}>
                            {coin.issuing_authority}
                          </span>
                          {coin.is_test_cut && (
                            <span 
                              className="text-[9px] px-1 py-0 rounded font-medium"
                              style={{ background: 'rgba(255, 69, 58, 0.2)', color: '#FF453A' }}
                            >
                              TC
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-2.5" style={{ color: 'var(--text-secondary)' }}>
                        {coin.denomination}
                      </td>
                      <td className="px-4 py-2.5">
                        <MetalBadge metal={coin.metal} size="xs" />
                      </td>
                      <td className="px-4 py-2.5 tabular-nums text-xs" style={{ color: 'var(--text-tertiary)' }}>
                        {formatYearRange(coin.mint_year_start, coin.mint_year_end, coin.is_circa)}
                      </td>
                      <td className="px-4 py-2.5">
                        {coin.grade ? (
                          <GradeBadge grade={coin.grade} size="xs" />
                        ) : (
                          <span style={{ color: 'var(--text-tertiary)' }}>—</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-right font-medium tabular-nums" style={{ color: 'var(--text-primary)' }}>
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
              <div 
                className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
                style={{ background: 'var(--bg-card)' }}
              >
                <Coins className="w-8 h-8" style={{ color: 'var(--text-tertiary)' }} />
              </div>
              <h3 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
                No coins found
              </h3>
              <p className="text-sm max-w-xs" style={{ color: 'var(--text-secondary)' }}>
                {activeFilters > 0 
                  ? "Try adjusting your filters to see more results."
                  : "Add your first coin to start building your collection."}
              </p>
              {activeFilters === 0 && (
                <Button 
                  className="mt-4" 
                  onClick={() => navigate("/coins/new")}
                  style={{ background: 'var(--metal-au)', color: 'var(--bg-base)' }}
                >
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
