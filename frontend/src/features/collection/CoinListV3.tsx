/**
 * CoinListV3 - Collection list with V3.0 design system components
 *
 * Features:
 * - Grid view with CoinCardV3 (5/4/3/2/1 column responsive)
 * - Table view with CoinTableRowV3 (12-column layout)
 * - Sorting and pagination
 * - View mode toggle (grid/table)
 *
 * @module features/collection/CoinListV3
 */

import { useQuery } from '@tanstack/react-query';
import { v2 } from '@/api/v2';
import { CoinCardV3, CoinCardV3Skeleton } from '@/components/coins/CoinCardV3';
import { CoinTableRowV3, CoinTableHeaderV3 } from '@/components/coins/CoinTableRowV3';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, LayoutGrid, List } from 'lucide-react';
import { SortControl } from '@/components/ui/SortControl';
import { useUIStore } from '@/stores/uiStore';
import { useFilterStore, SortField } from '@/stores/filterStore';
import { useSelection } from '@/stores/selectionStore';
import { Button } from '@/components/ui/button';
import { Pagination } from '@/components/ui/Pagination';
import { useNavigate } from 'react-router-dom';

export function CoinListV3() {
  const { viewMode, setViewMode } = useUIStore();
  const { toParams, page, setPage, perPage, setPerPage, sortBy, sortDir, setSort, toggleSortDir } = useFilterStore();
  const { selectedIds, toggle, selectAll, clear, isSelected } = useSelection();
  const navigate = useNavigate();

  // Fetch with filters
  const { data, isLoading, error } = useQuery({
    queryKey: ['coins', toParams()],
    queryFn: () => v2.getCoins(toParams()),
    placeholderData: (previousData) => previousData,
  });

  const coins = data?.items || [];
  const total = data?.total || 0;
  const totalPages = data?.pages || 1;
  const allIds = coins.map((coin) => coin.id).filter((id): id is number => id !== null);
  const allSelected = coins.length > 0 && allIds.every((id) => selectedIds.has(id));

  // Selection handlers
  const handleSelect = (coinId: number) => {
    toggle(coinId);
  };

  const handleSelectAll = () => {
    if (allSelected) {
      clear();
    } else {
      selectAll(allIds);
    }
  };

  // Sorting handler for table
  const handleSort = (column: string) => {
    // Map column names to API sort keys (only valid SortField values)
    const sortMap: Record<string, SortField> = {
      id: 'id',
      ruler: 'name',
      denomination: 'denomination',
      date: 'year',
      grade: 'grade',
      rarity: 'rarity',
      value: 'value',
      metal: 'metal',
      category: 'category',
      price: 'price',
      acquired: 'acquired',
      created: 'created',
      weight: 'weight',
      mint: 'name', // Mint sorting uses name field
      diameter: 'weight', // Diameter sorting uses weight field (closest available)
      reference: 'name', // Reference sorting uses name field
    };

    const newSortBy = sortMap[column];
    if (!newSortBy) return; // Ignore unsortable columns like script, legends, exergue

    // Toggle direction if clicking same column
    if (sortBy === newSortBy) {
      toggleSortDir();
    } else {
      setSort(newSortBy);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        {/* Toolbar skeleton */}
        <div className="flex justify-between items-center">
          <div className="h-8 w-[220px] bg-[var(--bg-elevated)] rounded animate-pulse" />
          <div className="h-10 w-20 bg-[var(--bg-elevated)] rounded animate-pulse" />
        </div>

        {/* Grid skeleton */}
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 3xl:grid-cols-5 4xl:grid-cols-6 gap-6">
            {[...Array(10)].map((_, i) => (
              <CoinCardV3Skeleton key={i} />
            ))}
          </div>
        ) : (
          // Table skeleton
          <div className="space-y-2">
            <div className="h-12 bg-[var(--bg-elevated)] rounded animate-pulse" />
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-14 bg-[var(--bg-card)] rounded animate-pulse" />
            ))}
          </div>
        )}
      </div>
    );
  }

  // Error state
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
                if (typeof error === 'object' && error !== null) {
                  if ('issues' in error) {
                    return `Validation Error:\n${JSON.stringify((error as any).issues, null, 2)}`;
                  }
                  return JSON.stringify(
                    error,
                    (key, value) => {
                      if (key === 'request' || key === 'response' || key === 'config') return '[Circular]';
                      return value;
                    },
                    2
                  );
                }
                return String(error);
              } catch (e) {
                return `Error stringify failed: ${e}`;
              }
            })()}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Empty state
  if (coins?.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 px-4">
        <div className="text-center space-y-3">
          <div
            className="text-6xl mb-4"
            style={{ color: 'var(--text-ghost)' }}
          >
            📦
          </div>
          <h3
            className="text-xl font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >
            No coins found
          </h3>
          <p
            className="text-sm max-w-md"
            style={{ color: 'var(--text-muted)' }}
          >
            Import a collection or add your first coin to get started.
          </p>
          <div className="pt-4">
            <Button onClick={() => navigate('/coins/new')}>Add Your First Coin</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toolbar - Modern 2026 Design */}
      <div className="flex justify-between items-center gap-4">
        {/* Left: Modern Sort Control */}
        <div className="flex items-center gap-3">
          <SortControl
            sortBy={sortBy}
            sortDir={sortDir}
            onSortChange={(v) => setSort(v as SortField)}
            onDirectionToggle={toggleSortDir}
          />

          {/* Selection indicator */}
          {selectedIds.size > 0 && (
            <div
              className="text-sm font-medium px-3 py-1.5 rounded-md"
              style={{
                background: 'var(--bg-elevated)',
                color: 'var(--text-secondary)',
              }}
            >
              {selectedIds.size} selected
            </div>
          )}
        </div>

        {/* Right: View Switcher */}
        <div 
          className="flex rounded-lg p-1"
          style={{ background: 'var(--bg-elevated)' }}
        >
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => setViewMode('grid')}
            title="Grid View"
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'table' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => setViewMode('table')}
            title="Table View"
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content: Grid or Table */}
      {viewMode === 'grid' ? (
        /* Grid View - Fewer columns for wider cards */
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 4xl:grid-cols-5 gap-4">
          {coins?.map((coin, index) => (
            <CoinCardV3
              key={coin.id}
              coin={coin}
              onClick={() => navigate(`/coins/${coin.id}`)}
              selected={coin.id !== null && isSelected(coin.id)}
              onSelect={handleSelect}
              gridIndex={index}
            />
          ))}
        </div>
      ) : (
        /* Table View - Expanded layout with comprehensive numismatic columns */
        <div
          className="rounded-lg border overflow-x-auto"
          style={{
            borderColor: 'var(--border-subtle)',
            background: 'var(--bg-card)',
          }}
        >
          <div className="min-w-[1600px]">
            <CoinTableHeaderV3
              allSelected={allSelected}
              onSelectAll={handleSelectAll}
              sortColumn={
                sortBy === 'name'
                  ? 'ruler'
                  : sortBy === 'year'
                    ? 'date'
                    : sortBy
              }
              sortDirection={sortDir as 'asc' | 'desc'}
              onSort={handleSort}
            />
            <div className="max-h-[calc(100vh-400px)] overflow-y-auto">
              {coins?.map((coin) => (
                <CoinTableRowV3
                  key={coin.id}
                  coin={coin}
                  selected={coin.id !== null && isSelected(coin.id)}
                  onSelect={handleSelect}
                  onClick={() => navigate(`/coins/${coin.id}`)}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Pagination Controls */}
      <div
        className="mt-6 pt-4 border-t"
        style={{ borderColor: 'var(--border-subtle)' }}
      >
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          onPageChange={setPage}
          totalItems={total}
          perPage={perPage}
          onPerPageChange={setPerPage}
        />
      </div>
    </div>
  );
}
