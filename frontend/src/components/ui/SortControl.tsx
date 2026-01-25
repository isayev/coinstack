/**
 * SortControl - Modern expandable sort selector
 * 
 * Features:
 * - Expandable horizontal pills for sort options
 * - Visual direction indicator
 * - Smooth animations
 * - Rich visual feedback
 */

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  Calendar, 
  Clock, 
  DollarSign, 
  Award, 
  Crown,
  TrendingUp,
  Coins,
  ChevronLeft
} from "lucide-react";

interface SortOption {
  value: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}

const SORT_OPTIONS: SortOption[] = [
  { value: 'created', label: 'Added', icon: Clock, description: 'Date added to collection' },
  { value: 'year', label: 'Year', icon: Calendar, description: 'Mint year' },
  { value: 'price', label: 'Paid', icon: DollarSign, description: 'Acquisition price' },
  { value: 'value', label: 'Value', icon: TrendingUp, description: 'Estimated value' },
  { value: 'grade', label: 'Grade', icon: Award, description: 'Condition grade' },
  { value: 'name', label: 'Ruler', icon: Crown, description: 'Issuing authority' },
  { value: 'weight', label: 'Weight', icon: Coins, description: 'Physical weight' },
];

interface SortControlProps {
  sortBy: string;
  sortDir: 'asc' | 'desc';
  onSortChange: (value: string) => void;
  onDirectionToggle: () => void;
  className?: string;
}

export function SortControl({
  sortBy,
  sortDir,
  onSortChange,
  onDirectionToggle,
  className,
}: SortControlProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsExpanded(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentOption = SORT_OPTIONS.find(o => o.value === sortBy) || SORT_OPTIONS[0];

  return (
    <div 
      ref={containerRef}
      className={cn("relative flex items-center", className)}
    >
      {/* Main sort button / collapsed state */}
      <div
        className={cn(
          "flex items-center rounded-lg transition-all duration-300",
          isExpanded ? "bg-transparent" : "bg-[var(--bg-elevated)]"
        )}
        style={{
          border: isExpanded ? 'none' : '1px solid var(--border-subtle)',
        }}
      >
        {/* Expand/Collapse toggle */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            "flex items-center gap-2 px-3 h-9 rounded-l-lg transition-all",
            "hover:bg-[var(--bg-hover)]",
            isExpanded && "bg-[var(--bg-hover)]"
          )}
          style={{ color: 'var(--text-secondary)' }}
        >
          {isExpanded ? (
            <ChevronLeft className="w-4 h-4" />
          ) : (
            <ArrowUpDown className="w-4 h-4" />
          )}
          {!isExpanded && (
            <span className="text-sm font-medium">{currentOption.label}</span>
          )}
        </button>

        {/* Direction toggle - always visible when collapsed */}
        {!isExpanded && (
          <button
            onClick={onDirectionToggle}
            className="flex items-center justify-center w-9 h-9 rounded-r-lg hover:bg-[var(--bg-hover)] transition-colors"
            style={{ 
              color: 'var(--text-primary)',
              borderLeft: '1px solid var(--border-subtle)',
            }}
            title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
          >
            {sortDir === 'asc' ? (
              <ArrowUp className="w-4 h-4" />
            ) : (
              <ArrowDown className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* Expanded options */}
      {isExpanded && (
        <div 
          className="flex items-center gap-1 ml-1 animate-in fade-in slide-in-from-left-2 duration-200"
          style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '4px',
          }}
        >
          {SORT_OPTIONS.map((option) => {
            const Icon = option.icon;
            const isActive = sortBy === option.value;
            
            return (
              <button
                key={option.value}
                onClick={() => {
                  onSortChange(option.value);
                  // Don't collapse - let user continue to adjust
                }}
                className={cn(
                  "flex items-center gap-1.5 px-3 h-8 rounded-md text-sm font-medium transition-all",
                  isActive 
                    ? "bg-[var(--cat-imperial)] text-white" 
                    : "hover:bg-[var(--bg-hover)]"
                )}
                style={{
                  color: isActive ? '#fff' : 'var(--text-secondary)',
                }}
                title={option.description}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{option.label}</span>
              </button>
            );
          })}
          
          {/* Direction toggle in expanded view */}
          <div 
            className="flex items-center ml-2 pl-2"
            style={{ borderLeft: '1px solid var(--border-subtle)' }}
          >
            <button
              className={cn(
                "flex items-center justify-center w-8 h-8 rounded-md transition-colors",
                sortDir === 'asc' && "bg-[var(--bg-hover)]"
              )}
              style={{ color: sortDir === 'asc' ? 'var(--text-primary)' : 'var(--text-muted)' }}
              onClick={() => {
                if (sortDir !== 'asc') onDirectionToggle();
              }}
              title="Ascending"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
            <button
              className={cn(
                "flex items-center justify-center w-8 h-8 rounded-md transition-colors",
                sortDir === 'desc' && "bg-[var(--bg-hover)]"
              )}
              style={{ color: sortDir === 'desc' ? 'var(--text-primary)' : 'var(--text-muted)' }}
              onClick={() => {
                if (sortDir !== 'desc') onDirectionToggle();
              }}
              title="Descending"
            >
              <ArrowDown className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
