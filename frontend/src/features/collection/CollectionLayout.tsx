import { ReactNode, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { CollectionSidebar } from "@/components/coins/CollectionSidebar";
import { CollectionToolbar } from "./CollectionToolbar";
import { useFilterStore } from "@/stores/filterStore";

interface CollectionLayoutProps {
    children: ReactNode;
}

export function CollectionLayout({ children }: CollectionLayoutProps) {
    const [searchParams] = useSearchParams();
    const setSearch = useFilterStore((s) => s.setSearch);

    // Sync URL ?search= into filterStore so list uses it (Option B: issuer)
    useEffect(() => {
        const q = searchParams.get("search");
        setSearch(q && q.trim() ? q.trim() : null);
    }, [searchParams, setSearch]);

    return (
        <div className="flex h-[calc(100vh-3.5rem)]"> {/* Full height minus header */}
            {/* Filter Sidebar */}
            <div className="w-[280px] flex-shrink-0 border-r border-[var(--border-subtle)] bg-[var(--bg-elevated)/50] overflow-y-auto hidden lg:block">
                <CollectionSidebar />
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                <div className="px-6">
                    <CollectionToolbar />
                </div>
                <div className="flex-1 overflow-y-auto px-6 py-4">
                    {children}
                </div>
            </div>
        </div>
    );
}
