import { useQuery } from "@tanstack/react-query"
import { v2 } from "@/api/v2"
import { CoinCard } from "@/components/coins/CoinCard"
import { CoinTable } from "@/components/coins/CoinTable"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, LayoutGrid, List, ArrowUp, ArrowDown } from "lucide-react"
import { useUIStore } from "@/stores/uiStore"
import { useFilterStore } from "@/stores/filterStore"
import { Button } from "@/components/ui/button"
import { Pagination } from "@/components/ui/Pagination"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { useNavigate } from "react-router-dom"

export function CoinList() {
  const { viewMode, setViewMode } = useUIStore()
  const { toParams, page, setPage, perPage, setPerPage, sortBy, sortDir, setSort, toggleSortDir } = useFilterStore()
  const navigate = useNavigate()

  // Fetch with filters
  const { data, isLoading, error } = useQuery({
    queryKey: ['coins', toParams()],
    queryFn: () => v2.getCoins(toParams()),
    placeholderData: (previousData) => previousData // Keep prev data while loading new
  })

  // Handle response structure (if paginated it returns PaginatedCoins, but v2.ts schema expects Array... wait)
  // Let's check v2.getCoins return type. It parse Array.
  // BUT the backend returns PaginatedCoins object! { items: [], total: ... }
  // We need to fix v2.ts schema first because backend returns PaginatedCoins.

  const coins = data?.items || []
  const total = data?.total || 0
  const totalPages = data?.pages || 1

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="space-y-3">
            <Skeleton className="h-[125px] w-full rounded-xl" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-[250px]" />
              <Skeleton className="h-4 w-[200px]" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription className="whitespace-pre-wrap font-mono text-xs text-left">
          <p className="font-bold">Failed to load collection.</p>
          <div className="mt-2 p-2 bg-destructive/10 rounded overflow-auto max-h-40">
            {(() => {
              try {
                if (error instanceof Error) return error.message;
                // If it's an object, try to identify it
                if (typeof error === 'object' && error !== null) {
                  // Check for Zod issues specifically
                  if ('issues' in error) {
                    return `Validation Error:\n${JSON.stringify((error as any).issues, null, 2)}`;
                  }
                  return JSON.stringify(error, (key, value) => {
                    if (key === 'request' || key === 'response' || key === 'config') return '[Circular]';
                    return value;
                  }, 2);
                }
                return String(error);
              } catch (e) {
                return `Error stringify failed: ${e}`;
              }
            })()}
          </div>
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex justify-between items-center mb-4">

        {/* Sort Controls */}
        <div className="flex items-center gap-2">
          <Select value={sortBy} onValueChange={(v: any) => setSort(v)}>
            <SelectTrigger className="w-[180px] h-8 text-xs">
              <SelectValue placeholder="Sort by..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="created">Date Added</SelectItem>
              <SelectItem value="year">Mint Year</SelectItem>
              <SelectItem value="price">Price Paid</SelectItem>
              <SelectItem value="grade">Grade</SelectItem>
              <SelectItem value="name">Ruler / Issuer</SelectItem>
              <SelectItem value="value">Est. Value</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={toggleSortDir}
            title={sortDir === 'asc' ? "Ascending" : "Descending"}
          >
            {sortDir === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />}
          </Button>
        </div>

        {/* View Switcher */}
        <div className="flex bg-muted rounded-lg p-1">
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => setViewMode('grid')}
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'table' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => setViewMode('table')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {coins?.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No coins found. Import a collection or add your first coin.
        </div>
      ) : (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {coins?.map((coin: any) => (
                <CoinCard
                  key={coin.id}
                  coin={coin}
                  onClick={() => navigate(`/coins/${coin.id}`)}
                />
              ))}
            </div>
          ) : (
            <CoinTable coins={coins || []} />
          )}

          {/* Pagination Controls */}
          <div className="mt-6 border-t pt-4">
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
              totalItems={total}
              perPage={perPage as any}
              onPerPageChange={(v) => setPerPage(v as any)}
            />
          </div>
        </>
      )}
    </div>
  )
}