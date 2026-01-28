import { ReactNode, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { CollectionSidebar } from "@/components/coins/CollectionSidebar";
import { CollectionToolbar } from "./CollectionToolbar";
import { useFilterStore } from "@/stores/filterStore";

interface CollectionLayoutProps {
    children: ReactNode;
}

export function CollectionLayout({ children }: CollectionLayoutProps) {
    const [searchParams, setSearchParams] = useSearchParams();
    const setSearch = useFilterStore((s) => s.setSearch);
    const setCategory = useFilterStore((s) => s.setCategory);
    const setMetal = useFilterStore((s) => s.setMetal);
    const search = useFilterStore((s) => s.search);
    const category = useFilterStore((s) => s.category);
    const metal = useFilterStore((s) => s.metal);

    // URL → filterStore: on load or back/forward, apply ?search=, ?category=, ?metal=
    useEffect(() => {
        const q = searchParams.get("search");
        const cat = searchParams.get("category");
        const m = searchParams.get("metal");
        setSearch(q && q.trim() ? q.trim() : null);
        setCategory(cat && cat.trim() ? cat.trim() : null);
        setMetal(m && m.trim() ? m.trim() : null);
    }, [searchParams, setSearch, setCategory, setMetal]);

    // filterStore → URL: when filters change in UI, update URL (shareable/bookmarkable)
    useEffect(() => {
        const next = new URLSearchParams();
        if (search?.trim()) next.set("search", search.trim());
        if (category) next.set("category", category);
        if (metal) next.set("metal", metal);
        const nextStr = next.toString();
        const currStr = new URLSearchParams(searchParams).toString();
        if (nextStr !== currStr) {
            setSearchParams(next, { replace: true });
        }
    }, [search, category, metal, searchParams, setSearchParams]);

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
