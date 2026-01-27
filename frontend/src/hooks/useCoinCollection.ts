import { useInfiniteQuery } from '@tanstack/react-query';
import { client, type PaginatedCoinsResponse } from '@/api/client';
import { useFilterStore } from '@/stores/filterStore';
import { useSelection } from '@/stores/selectionStore';
import { useEffect, useRef } from 'react';

export function useCoinCollection() {
    const { toParams } = useFilterStore();
    const { selectedIds, toggle, selectAll, clear, isSelected } = useSelection();

    // Use generic for the observer ref to avoid TS errors
    const observerTarget = useRef<HTMLDivElement>(null);

    // Get current params directly from store state (component re-renders on store update)
    const queryParams = toParams();

    // Fetch with infinite query
    const {
        data,
        error,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        status,
        refetch
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
    }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

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

    return {
        coins,
        total,
        status,
        error,
        observerTarget,
        isFetchingNextPage,
        hasNextPage,
        selectedIds,
        allSelected,
        handleSelect,
        handleSelectAll,
        isSelected,
        refetch
    };
}
