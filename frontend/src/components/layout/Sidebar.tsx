import { NavLink, useLocation } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";
import {
  BarChart3, Upload, Settings,
  ChevronLeft, ChevronRight, Sparkles, Library, Gavel, ClipboardCheck, LayoutGrid
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarBadge } from "./SidebarBadge";
import { useReviewCountsRealtime } from "@/hooks/useReviewCountsRealtime";
import { useQuery } from "@tanstack/react-query";
import { client } from "@/api/client";

const navItems = [
  { to: "/", icon: Library, label: "Collection" },
  { to: "/series", icon: LayoutGrid, label: "Series" },
  { to: "/auctions", icon: Gavel, label: "Auctions" },
  { to: "/review", icon: ClipboardCheck, label: "Review Center" },
  { to: "/stats", icon: BarChart3, label: "Statistics" },
  { to: "/import", icon: Upload, label: "Import" },
  { to: "/bulk-enrich", icon: Sparkles, label: "Enrich" },
  { to: "/settings", icon: Settings, label: "Settings" },
];
export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { data: reviewCounts } = useReviewCountsRealtime();
  const location = useLocation();

  return (
    <aside
      className={cn(
        "fixed left-0 top-20 bottom-0 z-40 transition-all duration-200 flex flex-col",
        sidebarOpen ? "w-48" : "w-14"
      )}
      style={{
        background: 'var(--bg-elevated)',
        borderRight: '1px solid var(--border-subtle)'
      }}
    >
      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1 p-2 pt-3">
        {navItems.map(({ to, icon: Icon, label }) => {
          const isReviewCenter = to === "/review";
          const isCollection = to === "/"; // Base path redirects to /collection/grid

          // Count logic
          const badgeCount = isReviewCenter ? reviewCounts?.total : undefined;

          // Use useQuery for collection count (inline for simplicity, can abstract if needed)
          const { data: collectionData } = useQuery({
            queryKey: ['totalCoins'],
            queryFn: () => client.getCoins({ per_page: 1 }),
            enabled: isCollection,
            staleTime: 60000 // 1 minute
          });
          const collectionCount = isCollection ? collectionData?.total : undefined;

          return (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => {
                // Custom active logic for collection
                const active = isCollection
                  ? location.pathname.startsWith('/collection') || location.pathname === '/'
                  : isActive;

                return cn(
                  "flex items-center gap-3 px-2.5 py-2 rounded-md transition-all relative",
                  active
                    ? "font-medium"
                    : "hover:bg-[var(--bg-hover)]"
                )
              }}
              style={({ isActive }) => {
                const active = isCollection
                  ? location.pathname.startsWith('/collection') || location.pathname === '/'
                  : isActive;

                return {
                  color: active ? 'var(--metal-au)' : 'var(--text-secondary)',
                  background: active ? 'var(--metal-au-subtle)' : undefined,
                }
              }}
            >
              {({ isActive }) => {
                const active = isCollection
                  ? location.pathname.startsWith('/collection') || location.pathname === '/'
                  : isActive;

                return (
                  <>
                    {/* Active indicator bar */}
                    {active && (
                      <div
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                        style={{ background: 'var(--metal-au)' }}
                      />
                    )}

                    {/* Icon */}
                    <Icon className="w-5 h-5 flex-shrink-0" />

                    {/* Label */}
                    {sidebarOpen && (
                      <span className="text-sm flex-1">{label}</span>
                    )}

                    {/* Badge for Collection (Counter) */}
                    {isCollection && collectionCount !== undefined && sidebarOpen && (
                      <span className="text-xs text-muted-foreground bg-[var(--bg-card)] px-1.5 py-0.5 rounded-md">
                        {collectionCount}
                      </span>
                    )}

                    {/* Badge for Review Center */}
                    {isReviewCenter && badgeCount !== undefined && (
                      <SidebarBadge count={badgeCount} />
                    )}

                    {/* Collapsed badge (dot indicator) */}
                    {!sidebarOpen && isReviewCenter && badgeCount !== undefined && badgeCount > 0 && (
                      <div className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[var(--error)]" />
                    )}
                  </>
                )
              }}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="p-2" style={{ borderTop: '1px solid var(--border-subtle)' }}>
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "w-full justify-center",
            sidebarOpen ? "px-2" : "px-0"
          )}
          style={{ color: 'var(--text-tertiary)' }}
          onClick={toggleSidebar}
        >
          {sidebarOpen ? (
            <>
              <ChevronLeft className="w-4 h-4 mr-2" />
              <span className="text-xs">Collapse</span>
            </>
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </Button>
      </div>
    </aside>
  );
}
