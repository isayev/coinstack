/**
 * BottomPanel - Collapsible panel for larger visualizations
 * 
 * Features:
 * - Collapsible with smooth animation
 * - Tabs for different views (Year, Acquisitions, etc.)
 * - Resizable height (drag handle)
 */

import { useState, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { ChevronUp, ChevronDown, Calendar, TrendingUp, MapPin, GripHorizontal } from "lucide-react";

interface Tab {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  content: ReactNode;
}

interface BottomPanelProps {
  tabs: Tab[];
  defaultTab?: string;
  defaultOpen?: boolean;
  defaultHeight?: number;
  minHeight?: number;
  maxHeight?: number;
  className?: string;
}

export function BottomPanel({
  tabs,
  defaultTab,
  defaultOpen = false,
  defaultHeight = 200,
  minHeight = 150,
  maxHeight = 400,
  className,
}: BottomPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);
  const [height, setHeight] = useState(defaultHeight);
  const [isDragging, setIsDragging] = useState(false);

  // Handle resize drag
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);

    const startY = e.clientY;
    const startHeight = height;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaY = startY - moveEvent.clientY;
      const newHeight = Math.min(maxHeight, Math.max(minHeight, startHeight + deltaY));
      setHeight(newHeight);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const activeTabContent = tabs.find(t => t.id === activeTab)?.content;

  return (
    <div
      className={cn(
        "border-t transition-all duration-200",
        isDragging && "select-none",
        className
      )}
      style={{
        background: 'var(--bg-card)',
        borderColor: 'var(--border-subtle)',
      }}
    >
      {/* Header with tabs and toggle */}
      <div
        className="flex items-center justify-between px-4 h-10"
        style={{ borderBottom: isOpen ? '1px solid var(--border-subtle)' : 'none' }}
      >
        {/* Tabs */}
        <div className="flex items-center gap-1">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => {
                setActiveTab(id);
                if (!isOpen) setIsOpen(true);
              }}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors",
                activeTab === id && isOpen
                  ? "bg-[var(--bg-hover)]"
                  : "hover:bg-[var(--bg-hover)]"
              )}
              style={{
                color: activeTab === id && isOpen
                  ? 'var(--text-primary)'
                  : 'var(--text-muted)',
              }}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {/* Toggle button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-1.5 rounded hover:bg-[var(--bg-hover)] transition-colors"
          style={{ color: 'var(--text-muted)' }}
          title={isOpen ? 'Collapse panel' : 'Expand panel'}
        >
          {isOpen ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronUp className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Content */}
      {isOpen && (
        <>
          {/* Resize handle */}
          <div
            className={cn(
              "h-1 cursor-ns-resize flex items-center justify-center transition-colors",
              isDragging ? "bg-[var(--cat-imperial)]" : "hover:bg-[var(--bg-hover)]"
            )}
            onMouseDown={handleMouseDown}
          >
            <GripHorizontal 
              className="w-6 h-3" 
              style={{ color: isDragging ? 'var(--text-primary)' : 'var(--text-ghost)' }}
            />
          </div>

          {/* Panel content */}
          <div
            className="overflow-auto px-4 py-3"
            style={{ height }}
          >
            {activeTabContent}
          </div>
        </>
      )}
    </div>
  );
}

// ============================================================================
// Pre-configured tabs for collection insights
// ============================================================================

export const COLLECTION_INSIGHT_TABS = [
  {
    id: 'timeline',
    label: 'Timeline',
    icon: Calendar,
  },
  {
    id: 'acquisitions',
    label: 'Acquisitions',
    icon: TrendingUp,
  },
  {
    id: 'geography',
    label: 'Geography',
    icon: MapPin,
  },
];
