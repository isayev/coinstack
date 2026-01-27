import { ReactNode } from "react";
import { CollectionSidebar } from "@/components/coins/CollectionSidebar";
import { CollectionToolbar } from "./CollectionToolbar";

interface CollectionLayoutProps {
    children: ReactNode;
}

export function CollectionLayout({ children }: CollectionLayoutProps) {
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
