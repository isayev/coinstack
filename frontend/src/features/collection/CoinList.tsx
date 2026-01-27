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

import { useInfiniteQuery } from '@tanstack/react-query';
import { client, type PaginatedCoinsResponse } from '@/api/client';
import { CoinCard, CoinCardV3Skeleton } from '@/components/coins/CoinCard';
import { CoinTableRow, CoinTableHeader } from '@/components/coins/CoinTableRow';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, LayoutGrid, List } from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';
import { useFilterStore, SortField } from '@/stores/filterStore';
import { useSelection } from '@/stores/selectionStore';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useEffect, useRef, useMemo, useCallback } from 'react';

export function CoinList() {
  const { viewMode, setViewMode } = useUIStore();
  const { toParams, sortBy, sortDir, setSort, toggleSortDir } = useFilterStore();
  const { selectedIds, toggle, selectAll, clear, isSelected } = useSelection();
  const navigate = useNavigate();

  // Use generic for the observer ref to avoid TS errors
  const observerTarget = useRef<HTMLDivElement>(null);

  // Memoize query params to prevent stale closure issues in queryFn
  const queryParams = useMemo(() => toParams(), [toParams]);

  // Memoize navigation callback for coin cards
  const handleCoinClick = useCallback((coinId: number | null) => {
    if (coinId !== null) {
      navigate(`/coins/${coinId}`);
    }
  }, [navigate]);

  // Fetch with infinite query
  const {
    data,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteQuery<PaginatedCoinsResponse>({
    queryKey: ['coins', queryParams], // Depends on filters
    queryFn: ({ pageParam }) => client.getCoins({ ...queryParams, page: pageParam as number }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      // API returns 'page' and 'pages' (total pages)
      if (lastPage.page < lastPage.pages) {
        return lastPage.page + 1;
      }
      return undefined;
    },
    placeholderData: (previousData) => previousData,
  });

  // Flatten items from all pages
  const coins = data?.pages.flatMap((page) => page.items) || [];
  const total = data?.pages[0]?.total || 0;

  const allIds = coins.map((coin) => coin.id).filter((id): id is number => id !== null);
  const allSelected = coins.length > 0 && allIds.every((id) => selectedIds.has(id));

  // Intersection Observer for Infinite Scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, viewMode]);

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
      mint: 'mint',
      diameter: 'diameter',
      die_axis: 'die_axis',
      specific_gravity: 'specific_gravity',
      issue_status: 'issue_status',
      reference: 'name', // Keep existing fallback or update if needed
    };

    const newSortBy = sortMap[column];
    if (!newSortBy) return;

    if (sortBy === newSortBy) {
      toggleSortDir();
    } else {
      setSort(newSortBy);
    }
  };

  // Shared Sentinel Component
  const Sentinel = (
    <div
      ref={observerTarget}
      className="h-20 flex items-center justify-center p-4 w-full"
    >
      {isFetchingNextPage ? (
        <div className="flex flex-col items-center gap-2 text-sm text-muted-foreground animate-pulse">
          <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          Loading more coins...
        </div>
      ) : hasNextPage ? (
        <span className="text-xs text-muted-foreground">Scroll for more</span>
      ) : coins.length > 0 ? (
        <span className="text-xs text-muted-foreground">All {total} coins loaded</span>
      ) : null}
    </div>
  );

  // Loading state (initial)
  if (status === 'pending') {
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
  if (status === 'error') {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription className="whitespace-pre-wrap font-mono text-xs text-left">
          <p className="font-bold">Failed to load collection.</p>
          <div className="mt-2 p-2 bg-destructive/10 rounded overflow-auto max-h-40">
            {String(error)}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Empty state
  if (coins.length === 0) {
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
        {/* Left: Selection indicator (Sort is now in headers) */}
        <div className="flex items-center gap-3">
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
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 4xl:grid-cols-5 gap-4">
            {coins.map((coin, index) => (
              <CoinCard
                key={`${coin.id}-${index}`} // Use index fallback to prevent duplicate key errors during refetch
                coin={coin}
                onClick={() => handleCoinClick(coin.id)}
                selected={coin.id !== null && isSelected(coin.id)}
                onSelect={handleSelect}
                gridIndex={index}
              />
            ))}
          </div>
          {/* Detailed Sentinel for Grid View */}
          {Sentinel}
        </>
      ) : (
        /* Table View - Clean grid without outer container */
        <div className="w-full">
          <CoinTableHeader
            allSelected={allSelected}
            onSelectAll={handleSelectAll}
            sortColumn={sortBy}
            sortDirection={sortDir as 'asc' | 'desc'}
            onSort={handleSort}
          />
          <div className="pb-20"> {/* Add padding for bottom scroll */}
            {coins.map((coin, index) => (
              <CoinTableRow
                key={`${coin.id}-${index}`}
                coin={coin}
                selected={coin.id !== null && isSelected(coin.id)}
                onSelect={handleSelect}
                onClick={() => handleCoinClick(coin.id)}
              />
            ))}
            {/* Detailed Sentinel inside Table View container */}
            {Sentinel}
          </div>
        </div>
      )}
    </div>
  );
}
