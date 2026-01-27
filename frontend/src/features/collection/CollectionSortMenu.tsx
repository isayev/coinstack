import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
    DropdownMenuLabel,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import { ArrowDownWideNarrow, ArrowUpNarrowWide } from "lucide-react";
import { useFilterStore, SortField } from "@/stores/filterStore";
// import { cn } from "@/lib/utils";

export function CollectionSortMenu() {
    const { sortBy, sortDir, setSort, toggleSortDir } = useFilterStore();

    const handleSortChange = (field: SortField) => {
        if (sortBy === field) {
            toggleSortDir();
        } else {
            setSort(field);
        }
    };

    const sortOptions: { label: string; value: SortField }[] = [
        { label: "Date (Minted)", value: "year" },
        { label: "Ruler / Issuer", value: "name" },
        { label: "Denomination", value: "denomination" },
        { label: "Mint", value: "mint" },
        { label: "Value", value: "value" },
        { label: "Acquired Date", value: "acquired" },
        { label: "Added to System", value: "created" },
    ];

    const currentLabel = sortOptions.find((o) => o.value === sortBy)?.label || "Sort By";

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className="h-8 gap-1 bg-[var(--bg-elevated)] border-[var(--border-subtle)]"
                >
                    <span className="text-muted-foreground mr-1">Sort:</span>
                    <span className="font-medium text-foreground">{currentLabel}</span>
                    {sortDir === "asc" ? (
                        <ArrowUpNarrowWide className="h-3.5 w-3.5 ml-1 text-muted-foreground" />
                    ) : (
                        <ArrowDownWideNarrow className="h-3.5 w-3.5 ml-1 text-muted-foreground" />
                    )}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>Sort Coins</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuRadioGroup value={sortBy} onValueChange={(v) => handleSortChange(v as SortField)}>
                    {sortOptions.map((option) => (
                        <DropdownMenuRadioItem key={option.value} value={option.value} className="cursor-pointer">
                            {option.label}
                        </DropdownMenuRadioItem>
                    ))}
                </DropdownMenuRadioGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={toggleSortDir} className="cursor-pointer">
                    <div className="flex items-center justify-between w-full">
                        <span>Direction</span>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            {sortDir === 'asc' ? 'Ascending' : 'Descending'}
                            {sortDir === "asc" ? (
                                <ArrowUpNarrowWide className="h-3 w-3" />
                            ) : (
                                <ArrowDownWideNarrow className="h-3 w-3" />
                            )}
                        </div>
                    </div>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
