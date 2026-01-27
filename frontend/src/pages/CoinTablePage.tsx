import { useNavigate } from "react-router-dom";
import { useCoinCollection } from "@/hooks/useCoinCollection";
import { CoinTableRow, CoinTableHeader } from "@/components/coins/CoinTableRow";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, Plus } from "lucide-react";
import { useFilterStore, SortField } from "@/stores/filterStore";
import { Skeleton } from "@/components/ui/skeleton";
import { CollectionLayout } from "@/features/collection/CollectionLayout";

export function CoinTablePage() {
    const navigate = useNavigate();
    const { sortBy, sortDir, setSort, toggleSortDir } = useFilterStore();

    const {
        coins,
        status,
        error,
        observerTarget,
        isFetchingNextPage,
        hasNextPage,
        total,
        // selectedIds, // Removed unused
        allSelected,
        handleSelect,
        handleSelectAll,
        isSelected
    } = useCoinCollection();


    const handleSort = (column: string) => {
        // Exact mapping to API sort keys
        const sortMap: Record<string, SortField> = {
            id: 'id',
            name: 'name', // Ruler
            denomination: 'denomination',
            year: 'year',
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
            reference: 'reference',
            reign: 'reign_start', // Sort by Reign Start
            storage_location: 'storage_location',
            obverse_legend: 'obverse_legend',
            reverse_legend: 'reverse_legend',
            obverse_description: 'obverse_description',
            reverse_description: 'reverse_description',
        };

        const newSortBy = sortMap[column];
        if (!newSortBy) return;

        if (sortBy === newSortBy) {
            toggleSortDir();
        } else {
            setSort(newSortBy);
        }
    };

    const handleCoinClick = (coinId: number | null) => {
        if (coinId !== null) navigate(`/coins/${coinId}`);
    };

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

    if (status === 'pending') {
        return (
            <CollectionLayout>
                <div className="space-y-4">
                    <div className="h-10 w-full bg-[var(--bg-elevated)] rounded animate-pulse" />
                    {[...Array(10)].map((_, i) => (
                        <Skeleton key={i} className="h-14 w-full" />
                    ))}
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
                <div className="w-full">
                    <CoinTableHeader
                        allSelected={allSelected}
                        onSelectAll={handleSelectAll}
                        sortColumn={sortBy}
                        sortDirection={sortDir as 'asc' | 'desc'}
                        onSort={handleSort}
                    />
                    <div className="pb-20">
                        {coins.map((coin, index) => (
                            <CoinTableRow
                                key={`${coin.id}-${index}`}
                                coin={coin}
                                selected={coin.id !== null && isSelected(coin.id)}
                                onSelect={handleSelect}
                                onClick={() => handleCoinClick(coin.id)}
                            />
                        ))}
                        {Sentinel}
                    </div>
                </div>
            </div>
        </CollectionLayout>
    );
}
