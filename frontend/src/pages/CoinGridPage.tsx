import { useNavigate } from "react-router-dom";
import { useCoinCollection } from "@/hooks/useCoinCollection";
import { CoinCard, CoinCardV3Skeleton } from "@/components/coins/CoinCard";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, Plus } from "lucide-react";
import { CollectionLayout } from "@/features/collection/CollectionLayout";

export function CoinGridPage() {
    const navigate = useNavigate();

    const {
        coins,
        status,
        error,
        observerTarget,
        isFetchingNextPage,
        hasNextPage,
        total,
        selectedIds,
        handleSelect,
        isSelected
    } = useCoinCollection();

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

    const handleCoinClick = (coinId: number | null) => {
        if (coinId !== null) navigate(`/coins/${coinId}`);
    };

    if (status === 'pending') {
        return (
            <CollectionLayout>
                <div className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 3xl:grid-cols-5 4xl:grid-cols-6 gap-6">
                        {[...Array(10)].map((_, i) => (
                            <CoinCardV3Skeleton key={i} />
                        ))}
                    </div>
                </div>
            </CollectionLayout>
        );
    }

    if (status === 'error') {
        return (
            <CollectionLayout>
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>
                        Failed to load collection: {String(error)}
                    </AlertDescription>
                </Alert>
            </CollectionLayout>
        );
    }

    if (coins.length === 0) {
        return (
            <CollectionLayout>
                <div className="flex flex-col items-center justify-center py-24 px-4 text-center">
                    <div className="text-6xl mb-4 text-[var(--text-ghost)]">📦</div>
                    <h3 className="text-xl font-semibold mb-2">No coins found</h3>
                    <p className="text-muted-foreground mb-4">Add your first coin to start your collection.</p>
                    <Button onClick={() => navigate('/coins/new')}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Coin
                    </Button>
                </div>
            </CollectionLayout>
        );
    }

    return (
        <CollectionLayout>
            <div className="space-y-4">
                {/* Selection Bar (Optional, if needed upon selection) */}
                {selectedIds.size > 0 && (
                    <div className="sticky top-0 z-10 py-2 bg-[var(--bg-app)]/95 backdrop-blur-sm border-b border-[var(--border-subtle)] flex items-center justify-between mb-4">
                        <span className="text-sm font-medium px-2 py-0.5 rounded bg-[var(--bg-elevated)] text-[var(--text-secondary)]">
                            {selectedIds.size} selected
                        </span>
                        {/* Bulk actions could go here */}
                    </div>
                )}

                {/* Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-3 3xl:grid-cols-4 4xl:grid-cols-5 gap-4">
                    {coins.map((coin, index) => (
                        <CoinCard
                            key={`${coin.id}-${index}`}
                            coin={coin}
                            onClick={() => handleCoinClick(coin.id)}
                            selected={coin.id !== null && isSelected(coin.id)}
                            onSelect={handleSelect}
                            gridIndex={index}
                        />
                    ))}
                </div>
                {Sentinel}
            </div>
        </CollectionLayout>
    );
}
