import { useNavigate, useLocation } from "react-router-dom";
import { LayoutGrid, List, ArrowUp, ArrowDown, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFilterStore, SortField } from "@/stores/filterStore";
import { cn } from "@/lib/utils";

export function CollectionToolbar() {
    const navigate = useNavigate();
    const location = useLocation();
    const { sortBy, sortDir, setSort, toggleSortDir } = useFilterStore();

    const isGridView = location.pathname.includes('/grid') || location.pathname === '/' || location.pathname === '/collection';

    const handleSort = (field: SortField) => {
        if (sortBy === field) {
            toggleSortDir();
        } else {
            setSort(field);
        }
    };

    const SortOption = ({ label, field }: { label: string; field: SortField }) => {
        const isActive = sortBy === field;
        return (
            <button
                onClick={() => handleSort(field)}
                className={cn(
                    "text-sm transition-colors flex items-center gap-1",
                    isActive ? "font-semibold text-foreground" : "text-muted-foreground hover:text-foreground"
                )}
            >
                {label}
                {isActive && (
                    sortDir === 'asc' ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                )}
            </button>
        );
    };

    return (
        <div className="flex items-center justify-between py-3 border-b border-[var(--border-subtle)] bg-[var(--bg-app)]">
            {/* Horizontal Sort Menu */}
            <div className="flex items-center gap-6 overflow-x-auto no-scrollbar flex-1">
                <span className="text-sm font-medium text-muted-foreground mr-2">Sort by:</span>
                <SortOption label="Date" field="year" />
                <SortOption label="Ruler" field="name" />
                <SortOption label="Denom" field="denomination" />
                <SortOption label="Mint" field="mint" />
                <SortOption label="Value" field="value" />
                <SortOption label="Added" field="created" />
            </div>

            <div className="flex items-center gap-3">
                {/* View Toggle */}
                <div className="flex items-center bg-[var(--bg-elevated)] rounded-lg p-0.5 border border-[var(--border-subtle)]">
                    <Button
                        variant={isGridView ? "secondary" : "ghost"}
                        size="sm"
                        className={cn("h-7 w-8 px-0 rounded-md", isGridView && "bg-[var(--bg-card)] shadow-sm")}
                        onClick={() => navigate('/collection/grid')}
                        title="Grid View"
                    >
                        <LayoutGrid className="w-4 h-4" />
                    </Button>
                    <Button
                        variant={!isGridView ? "secondary" : "ghost"}
                        size="sm"
                        className={cn("h-7 w-8 px-0 rounded-md", !isGridView && "bg-[var(--bg-card)] shadow-sm")}
                        onClick={() => navigate('/collection/table')}
                        title="Table View"
                    >
                        <List className="w-4 h-4" />
                    </Button>
                </div>

                <Button onClick={() => navigate('/coins/new')} size="sm" className="h-8">
                    <Plus className="w-4 h-4 mr-2" />
                    Add
                </Button>
            </div>
        </div>
    );
}
