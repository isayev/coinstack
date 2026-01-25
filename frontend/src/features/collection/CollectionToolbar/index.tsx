/**
 * CollectionToolbar - Filter chips, sort controls, view toggle, and result summary
 * 
 * Features:
 * - Active filter chips (removable)
 * - Sort dropdown with direction toggle
 * - View mode toggle (Grid/Table/Compact)
 * - Result count and filtered value summary
 */

import { cn } from "@/lib/utils";
import { 
  X, 
  ArrowUp, 
  ArrowDown,
  LayoutGrid, 
  List, 
  Grid3X3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ============================================================================
// Active Filters Component
// ============================================================================

interface ActiveFilter {
  field: string;
  value: string;
  label: string;
}

interface ActiveFiltersProps {
  filters: ActiveFilter[];
  onRemove: (field: string) => void;
  onClearAll: () => void;
  className?: string;
}

/**
 * Get semantic color for filter chip based on filter type and value
 */
function getFilterChipColor(field: string, value: string): { bg: string; text: string } {
  // Category filters use category colors
  if (field === 'category') {
    const categoryColors: Record<string, string> = {
      'roman_imperial': 'var(--cat-imperial)',
      'imperial': 'var(--cat-imperial)',
      'roman_republic': 'var(--cat-republic)',
      'republic': 'var(--cat-republic)',
      'roman_provincial': 'var(--cat-provincial)',
      'provincial': 'var(--cat-provincial)',
      'greek': 'var(--cat-greek)',
      'byzantine': 'var(--cat-byzantine)',
      'celtic': 'var(--cat-celtic)',
      'judaean': 'var(--cat-judaean)',
    };
    const color = categoryColors[value.toLowerCase()] || 'var(--cat-imperial)';
    return { bg: color, text: '#fff' };
  }
  
  // Metal filters use metal colors
  if (field === 'metal') {
    return { 
      bg: `var(--metal-${value.toLowerCase()})`, 
      text: value.toLowerCase() === 'gold' || value.toLowerCase() === 'au' ? '#000' : '#fff' 
    };
  }
  
  // Grade filters use grade colors
  if (field === 'grade') {
    const prefix = value.replace(/[0-9\s]/g, '').toUpperCase();
    const gradeColors: Record<string, string> = {
      'MS': 'var(--grade-ms)',
      'AU': 'var(--grade-au)',
      'XF': 'var(--grade-xf)',
      'EF': 'var(--grade-xf)',
      'VF': 'var(--grade-vf)',
      'F': 'var(--grade-f)',
      'VG': 'var(--grade-vg)',
      'G': 'var(--grade-g)',
    };
    return { bg: gradeColors[prefix] || 'var(--grade-vf)', text: '#fff' };
  }
  
  // Certification filters
  if (field === 'grading_service' || field === 'certification') {
    return { bg: `var(--cert-${value.toLowerCase()})`, text: '#fff' };
  }
  
  // Default: subtle neutral chip
  return { bg: 'var(--bg-elevated)', text: 'var(--text-primary)' };
}

export function ActiveFilters({
  filters,
  onRemove,
  onClearAll,
  className,
}: ActiveFiltersProps) {
  if (filters.length === 0) return null;

  return (
    <div className={cn("flex items-center gap-2 flex-wrap", className)}>
      <span 
        className="text-xs font-medium"
        style={{ color: 'var(--text-muted)' }}
      >
        Active:
      </span>
      {filters.map(({ field, value, label }) => {
        const chipColor = getFilterChipColor(field, value);
        return (
          <button
            key={`${field}-${value}`}
            onClick={() => onRemove(field)}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
              "transition-all hover:brightness-110"
            )}
            style={{
              background: chipColor.bg,
              color: chipColor.text,
            }}
            title={`Remove ${label} filter`}
          >
            <span>{label}</span>
            <X className="w-3 h-3" />
          </button>
        );
      })}
      {filters.length > 1 && (
        <button
          onClick={onClearAll}
          className="text-xs font-medium px-2 py-1 rounded hover:bg-[var(--bg-hover)] transition-colors"
          style={{ color: 'var(--text-muted)' }}
        >
          Clear all
        </button>
      )}
    </div>
  );
}

// ============================================================================
// Sort Controls Component
// ============================================================================

interface SortOption {
  value: string;
  label: string;
}

const SORT_OPTIONS: SortOption[] = [
  { value: 'created', label: 'Recently Added' },
  { value: 'year', label: 'Date (Oldest First)' },
  { value: 'price', label: 'Price Paid' },
  { value: 'value', label: 'Value (Highest)' },
  { value: 'grade', label: 'Grade (Best)' },
  { value: 'name', label: 'Ruler (A-Z)' },
  { value: 'weight', label: 'Weight' },
];

interface SortControlsProps {
  sortBy: string;
  sortDir: 'asc' | 'desc';
  onSortChange: (sortBy: string) => void;
  onDirectionToggle: () => void;
  className?: string;
}

export function SortControls({
  sortBy,
  sortDir,
  onSortChange,
  onDirectionToggle,
  className,
}: SortControlsProps) {
  return (
    <div className={cn("flex items-center gap-1", className)}>
      <Select value={sortBy} onValueChange={onSortChange}>
        <SelectTrigger className="h-8 w-[140px] text-xs">
          <SelectValue placeholder="Sort by..." />
        </SelectTrigger>
        <SelectContent>
          {SORT_OPTIONS.map(({ value, label }) => (
            <SelectItem key={value} value={value} className="text-xs">
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        variant="outline"
        size="sm"
        className="h-8 w-8 p-0"
        onClick={onDirectionToggle}
        title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
      >
        {sortDir === 'asc' ? (
          <ArrowUp className="h-3.5 w-3.5" />
        ) : (
          <ArrowDown className="h-3.5 w-3.5" />
        )}
      </Button>
    </div>
  );
}

// ============================================================================
// View Mode Toggle Component
// ============================================================================

import type { ViewMode } from "@/stores/uiStore";

interface ViewModeToggleProps {
  value: ViewMode;
  onChange: (mode: ViewMode) => void;
  className?: string;
}

export function ViewModeToggle({
  value,
  onChange,
  className,
}: ViewModeToggleProps) {
  const modes: { mode: ViewMode; icon: React.ComponentType<{ className?: string }>; label: string }[] = [
    { mode: 'grid', icon: LayoutGrid, label: 'Grid View' },
    { mode: 'table', icon: List, label: 'Table View' },
    { mode: 'compact', icon: Grid3X3, label: 'Compact Grid' },
  ];

  return (
    <div 
      className={cn("flex rounded-lg p-0.5", className)}
      style={{ background: 'var(--bg-elevated)' }}
    >
      {modes.map(({ mode, icon: Icon, label }) => (
        <Button
          key={mode}
          variant={value === mode ? 'secondary' : 'ghost'}
          size="sm"
          className="h-7 w-7 p-0"
          onClick={() => onChange(mode)}
          title={label}
        >
          <Icon className="h-3.5 w-3.5" />
        </Button>
      ))}
    </div>
  );
}

// ============================================================================
// Result Summary Component
// ============================================================================

interface ResultSummaryProps {
  filtered: number;
  total: number;
  filteredValue?: number | null;
  className?: string;
}

export function ResultSummary({
  filtered,
  total,
  filteredValue,
  className,
}: ResultSummaryProps) {
  const isFiltered = filtered !== total;
  
  const formatValue = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className={cn("flex items-center gap-3 text-sm", className)}>
      <span style={{ color: 'var(--text-secondary)' }}>
        {isFiltered ? (
          <>
            <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
              {filtered}
            </span>
            <span> of {total}</span>
          </>
        ) : (
          <>
            <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
              {total}
            </span>
            <span> coins</span>
          </>
        )}
      </span>
      {filteredValue !== null && filteredValue !== undefined && filteredValue > 0 && (
        <span 
          className="font-medium"
          style={{ color: 'var(--metal-au)' }}
        >
          {formatValue(filteredValue)}
        </span>
      )}
    </div>
  );
}

// ============================================================================
// Main CollectionToolbar Component
// ============================================================================

interface CollectionToolbarProps {
  // Filters
  activeFilters: ActiveFilter[];
  onRemoveFilter: (field: string) => void;
  onClearAllFilters: () => void;
  
  // Sorting
  sortBy: string;
  sortDir: 'asc' | 'desc';
  onSortChange: (sortBy: string) => void;
  onSortDirToggle: () => void;
  
  // View
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  
  // Results
  filteredCount: number;
  totalCount: number;
  filteredValue?: number | null;
  
  className?: string;
}

export function CollectionToolbar({
  activeFilters,
  onRemoveFilter,
  onClearAllFilters,
  sortBy,
  sortDir,
  onSortChange,
  onSortDirToggle,
  viewMode,
  onViewModeChange,
  filteredCount,
  totalCount,
  filteredValue,
  className,
}: CollectionToolbarProps) {
  return (
    <div
      className={cn("space-y-3 p-4 rounded-lg", className)}
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Top row: Active filters */}
      <ActiveFilters
        filters={activeFilters}
        onRemove={onRemoveFilter}
        onClearAll={onClearAllFilters}
      />
      
      {/* Bottom row: Controls */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        {/* Left: Sort controls */}
        <div className="flex items-center gap-3">
          <SortControls
            sortBy={sortBy}
            sortDir={sortDir}
            onSortChange={onSortChange}
            onDirectionToggle={onSortDirToggle}
          />
        </div>
        
        {/* Right: View mode + Results */}
        <div className="flex items-center gap-4">
          <ViewModeToggle
            value={viewMode}
            onChange={onViewModeChange}
          />
          <ResultSummary
            filtered={filteredCount}
            total={totalCount}
            filteredValue={filteredValue}
          />
        </div>
      </div>
    </div>
  );
}
