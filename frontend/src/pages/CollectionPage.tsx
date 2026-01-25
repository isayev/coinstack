/**
 * CollectionPage - Main collection view with dashboard sidebar
 * 
 * Layout:
 * - Left: CollectionDashboard (infographic sidebar)
 * - Center: CollectionToolbar + CoinList/Table
 * - Bottom: Collapsible insights panel
 */

import { useState } from "react";
import { CoinListV3 } from "@/features/collection/CoinListV3";
import { CollectionDashboard } from "@/features/collection/CollectionDashboard";
import { BottomPanel } from "@/components/layout/BottomPanel";
import { YearHistogram } from "@/components/dashboard/YearHistogram";
import { useCollectionStats } from "@/hooks/useCollectionStats";
import { Calendar, TrendingUp, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";

export function CollectionPage() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Fetch stats for dashboard
  const { data: stats } = useCollectionStats();

  // Year histogram data
  const yearData = stats?.by_year?.map(y => ({
    year: y.year,
    count: y.count,
  })) || [];

  // Bottom panel tabs
  const insightTabs = [
    {
      id: 'timeline',
      label: 'Timeline',
      icon: Calendar,
      content: (
        <YearHistogram
          data={yearData}
          height={160}
          showBrush
          onYearClick={(year) => {
            console.log('Year clicked:', year);
          }}
        />
      ),
    },
    {
      id: 'acquisitions',
      label: 'Acquisitions',
      icon: TrendingUp,
      content: (
        <div className="flex items-center justify-center h-full" style={{ color: 'var(--text-muted)' }}>
          <p className="text-sm">Acquisition timeline coming soon</p>
        </div>
      ),
    },
    {
      id: 'geography',
      label: 'Geography',
      icon: MapPin,
      content: (
        <div className="flex items-center justify-center h-full" style={{ color: 'var(--text-muted)' }}>
          <p className="text-sm">Mint map visualization coming soon</p>
        </div>
      ),
    },
  ];

  return (
    <div
      className="flex flex-col h-[calc(100vh-56px)]"
      style={{ background: 'var(--bg-app)' }}
    >
      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar - Dashboard */}
        <aside
          className={cn(
            "border-r flex-shrink-0 transition-all duration-200 overflow-hidden",
            sidebarCollapsed ? "w-0" : "w-72 xl:w-80"
          )}
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          <CollectionDashboard />
        </aside>

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Coin list/table (includes its own toolbar) */}
          <div className="flex-1 overflow-auto p-4">
            <CoinListV3 />
          </div>
        </div>
      </div>

      {/* Bottom panel */}
      <BottomPanel
        tabs={insightTabs}
        defaultTab="timeline"
        defaultOpen={false}
        defaultHeight={180}
        minHeight={120}
        maxHeight={350}
      />
    </div>
  );
}
