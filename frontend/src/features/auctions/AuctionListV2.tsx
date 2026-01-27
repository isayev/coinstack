import { useEffect, useRef } from 'react';
import { AuctionCard } from '@/components/auctions/AuctionCard';
import { AuctionTableRowV2, AuctionTableHeaderV2 } from '@/components/auctions/AuctionTableRowV2';
import { useAuctions, type AuctionFilters } from '@/hooks/useAuctions';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface AuctionListV2Props {
    filters: AuctionFilters;
    viewMode: 'grid' | 'table';
    setViewMode: (mode: 'grid' | 'table') => void;
    sortBy: string;
    setSortBy: (sort: string) => void;
    sortOrder: 'asc' | 'desc';
    setSortOrder: (order: 'asc' | 'desc') => void;
}

export function AuctionListV2({
    filters,
    viewMode,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
}: AuctionListV2Props) {
    const observerTarget = useRef<HTMLDivElement>(null);

    // Fetch with infinite query
    const {
        data,
        error,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        status,
    } = useAuctions(filters, 20, sortBy, sortOrder);

    // Flatten items
    const auctions = data?.pages.flatMap((page) => page.items) || [];
    const total = data?.pages[0]?.total || 0;

    // Intersection Observer
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
    }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

    const handleSort = (column: string) => {
        if (sortBy === column) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(column);
            setSortOrder('desc');
        }
    };

    const handleAuctionClick = (auction: any) => {
        window.open(auction.url, "_blank");
    };

    const Sentinel = (
        <div
            ref={observerTarget}
            className="h-20 flex items-center justify-center p-4 w-full"
        >
            {isFetchingNextPage ? (
                <div className="flex flex-col items-center gap-2 text-sm text-muted-foreground animate-pulse">
                    <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    Loading more records...
                </div>
            ) : hasNextPage ? (
                <span className="text-xs text-muted-foreground">Scroll for more</span>
            ) : auctions.length > 0 ? (
                <span className="text-xs text-muted-foreground">All {total} records loaded</span>
            ) : null}
        </div>
    );

    if (status === 'pending') {
        return (
            <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {[...Array(8)].map((_, i) => (
                        <Skeleton key={i} className="h-[280px] w-full rounded-lg" />
                    ))}
                </div>
            </div>
        );
    }

    if (status === 'error') {
        return (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>
                    Failed to load auctions: {String(error)}
                </AlertDescription>
            </Alert>
        );
    }

    if (auctions.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-24 px-4 text-center">
                <div className="text-6xl mb-4 text-[var(--text-ghost)]">⚖️</div>
                <h3 className="text-xl font-semibold">No auctions found</h3>
                <p className="text-sm text-muted-foreground mt-2">Try adjusting your filters.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {viewMode === 'grid' ? (
                <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4">
                        {auctions.map((auction, i) => (
                            <AuctionCard
                                key={`${auction.id}-${i}`}
                                auction={auction}
                                onSelect={handleAuctionClick}
                            />
                        ))}
                    </div>
                    {Sentinel}
                </>
            ) : (
                <div className="w-full">
                    <AuctionTableHeaderV2
                        sortColumn={sortBy}
                        sortDirection={sortOrder}
                        onSort={handleSort}
                    />
                    <div className="pb-20">
                        {auctions.map((auction, i) => (
                            <AuctionTableRowV2
                                key={`${auction.id}-${i}`}
                                auction={auction}
                                onClick={handleAuctionClick}
                            />
                        ))}
                        {Sentinel}
                    </div>
                </div>
            )}
        </div>
    );
}
