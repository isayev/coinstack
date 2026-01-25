/**
 * BottomPanel - Collapsible panel for larger visualizations
 * 
 * Features:
 * - Collapsible with smooth animation
 * - Tabs for different views (Year, Acquisitions, etc.)
 * - Resizable height (drag handle)
 */

import { useState, useRef, useEffect, ReactNode } from "react";
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

  // Ref to track event listeners for cleanup on unmount
  const listenersRef = useRef<{
    move?: (e: MouseEvent | TouchEvent) => void;
    end?: () => void;
  }>({});

  // Cleanup event listeners on unmount
  useEffect(() => {
    return () => {
      if (listenersRef.current.move) {
        document.removeEventListener('mousemove', listenersRef.current.move as (e: MouseEvent) => void);
        document.removeEventListener('touchmove', listenersRef.current.move as (e: TouchEvent) => void);
      }
      if (listenersRef.current.end) {
        document.removeEventListener('mouseup', listenersRef.current.end);
        document.removeEventListener('touchend', listenersRef.current.end);
      }
    };
  }, []);

  // Handle resize drag (mouse)
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    startDrag(e.clientY);
  };

  // Handle resize drag (touch)
  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    const touch = e.touches[0];
    startDrag(touch.clientY);
  };

  // Shared drag logic
  const startDrag = (startY: number) => {
    setIsDragging(true);
    const startHeight = height;

    const handleMove = (moveEvent: MouseEvent | TouchEvent) => {
      const clientY = 'touches' in moveEvent 
        ? moveEvent.touches[0].clientY 
        : moveEvent.clientY;
      const deltaY = startY - clientY;
      const newHeight = Math.min(maxHeight, Math.max(minHeight, startHeight + deltaY));
      setHeight(newHeight);
    };

    const handleEnd = () => {
      setIsDragging(false);
      document.removeEventListener('mousemove', handleMove);
      document.removeEventListener('mouseup', handleEnd);
      document.removeEventListener('touchmove', handleMove);
      document.removeEventListener('touchend', handleEnd);
      listenersRef.current = {};
    };

    // Store refs for cleanup
    listenersRef.current = { move: handleMove, end: handleEnd };

    document.addEventListener('mousemove', handleMove);
    document.addEventListener('mouseup', handleEnd);
    document.addEventListener('touchmove', handleMove);
    document.addEventListener('touchend', handleEnd);
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
      {/* Header with tabs and toggle - aligned heights */}
      <div
        className="flex items-center justify-between px-4"
        style={{ 
          height: '40px',
          borderBottom: isOpen ? '1px solid var(--border-subtle)' : 'none' 
        }}
      >
        {/* Tabs */}
        <div className="flex items-center gap-1 h-full">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => {
                setActiveTab(id);
                if (!isOpen) setIsOpen(true);
              }}
              className={cn(
                "flex items-center gap-1.5 px-3 h-8 text-xs font-medium rounded transition-colors",
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

        {/* Toggle button - same height as tabs */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center justify-center w-8 h-8 rounded hover:bg-[var(--bg-hover)] transition-colors"
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
          {/* Resize handle - supports both mouse and touch */}
          <div
            className={cn(
              "h-2 cursor-ns-resize flex items-center justify-center transition-colors touch-none",
              isDragging ? "bg-[var(--cat-imperial)]" : "hover:bg-[var(--bg-hover)]"
            )}
            onMouseDown={handleMouseDown}
            onTouchStart={handleTouchStart}
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
