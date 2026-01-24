/**
 * Pagination - Modern pagination controls
 * 
 * Features:
 * - Page numbers with smart ellipsis
 * - Prev/Next navigation
 * - Per-page selector (20, 50, 100, All)
 * - "Showing X-Y of Z" display
 * - Jump to page input
 * 
 * @module components/ui/Pagination
 */

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { PerPageOption } from "@/stores/filterStore";

// ============================================================================
// TYPES
// ============================================================================

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  perPage: PerPageOption;
  onPageChange: (page: number) => void;
  onPerPageChange: (perPage: PerPageOption) => void;
  className?: string;
}

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Generate page numbers to display with ellipsis
 */
function getPageNumbers(currentPage: number, totalPages: number): (number | "ellipsis")[] {
  const pages: (number | "ellipsis")[] = [];
  
  if (totalPages <= 7) {
    // Show all pages if 7 or fewer
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }
  } else {
    // Always show first page
    pages.push(1);
    
    if (currentPage > 3) {
      pages.push("ellipsis");
    }
    
    // Show pages around current
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    if (currentPage < totalPages - 2) {
      pages.push("ellipsis");
    }
    
    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }
  }
  
  return pages;
}

/**
 * Calculate the range of items being shown
 */
function getItemRange(currentPage: number, perPage: PerPageOption, totalItems: number): { start: number; end: number } {
  const effectivePerPage = perPage === "all" ? totalItems : perPage;
  const start = (currentPage - 1) * effectivePerPage + 1;
  const end = Math.min(currentPage * effectivePerPage, totalItems);
  return { start, end };
}

// ============================================================================
// PER PAGE OPTIONS
// ============================================================================

const PER_PAGE_OPTIONS: { value: PerPageOption; label: string }[] = [
  { value: 20, label: "20 per page" },
  { value: 50, label: "50 per page" },
  { value: 100, label: "100 per page" },
  { value: "all", label: "Show all" },
];

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  perPage,
  onPageChange,
  onPerPageChange,
  className,
}: PaginationProps) {
  const pageNumbers = getPageNumbers(currentPage, totalPages);
  const { start, end } = getItemRange(currentPage, perPage, totalItems);
  
  // Don't show pagination if no items or only one page with few items
  if (totalItems === 0) return null;
  
  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row items-center justify-between gap-4 py-3 px-4 rounded-lg",
        className
      )}
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      {/* Left: Item count */}
      <div className="flex items-center gap-4">
        <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Showing{" "}
          <span className="font-medium tabular-nums" style={{ color: "var(--text-primary)" }}>
            {start}–{end}
          </span>{" "}
          of{" "}
          <span className="font-medium tabular-nums" style={{ color: "var(--text-primary)" }}>
            {totalItems}
          </span>
        </span>
        
        {/* Per page selector */}
        <Select
          value={perPage.toString()}
          onValueChange={(v) => onPerPageChange(v === "all" ? "all" : (parseInt(v) as PerPageOption))}
        >
          <SelectTrigger
            className="w-[130px] h-8 text-xs"
            style={{ background: "var(--bg-card)", borderColor: "var(--border-subtle)" }}
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent style={{ background: "var(--bg-card)", borderColor: "var(--border-subtle)" }}>
            {PER_PAGE_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value.toString()} className="text-xs">
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Right: Page navigation */}
      {totalPages > 1 && (
        <div className="flex items-center gap-1">
          {/* First page */}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            disabled={!canGoPrev}
            onClick={() => onPageChange(1)}
            title="First page"
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          
          {/* Previous page */}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            disabled={!canGoPrev}
            onClick={() => onPageChange(currentPage - 1)}
            title="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          {/* Page numbers */}
          <div className="flex items-center gap-1 mx-1">
            {pageNumbers.map((page, index) =>
              page === "ellipsis" ? (
                <span
                  key={`ellipsis-${index}`}
                  className="w-8 text-center text-sm"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  ...
                </span>
              ) : (
                <Button
                  key={page}
                  variant={page === currentPage ? "default" : "ghost"}
                  size="sm"
                  className="h-8 w-8 p-0 text-xs font-medium"
                  style={
                    page === currentPage
                      ? { background: "var(--metal-au)", color: "var(--bg-base)" }
                      : {}
                  }
                  onClick={() => onPageChange(page)}
                >
                  {page}
                </Button>
              )
            )}
          </div>

          {/* Next page */}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            disabled={!canGoNext}
            onClick={() => onPageChange(currentPage + 1)}
            title="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          
          {/* Last page */}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            disabled={!canGoNext}
            onClick={() => onPageChange(totalPages)}
            title="Last page"
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// COMPACT VERSION
// ============================================================================

interface CompactPaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function CompactPagination({
  currentPage,
  totalPages,
  totalItems,
  onPageChange,
  className,
}: CompactPaginationProps) {
  if (totalItems === 0 || totalPages <= 1) return null;
  
  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Button
        variant="ghost"
        size="sm"
        className="h-7 px-2 text-xs"
        disabled={!canGoPrev}
        onClick={() => onPageChange(currentPage - 1)}
      >
        <ChevronLeft className="h-3.5 w-3.5 mr-1" />
        Prev
      </Button>
      
      <span className="text-xs tabular-nums" style={{ color: "var(--text-secondary)" }}>
        {currentPage} / {totalPages}
      </span>
      
      <Button
        variant="ghost"
        size="sm"
        className="h-7 px-2 text-xs"
        disabled={!canGoNext}
        onClick={() => onPageChange(currentPage + 1)}
      >
        Next
        <ChevronRight className="h-3.5 w-3.5 ml-1" />
      </Button>
    </div>
  );
}
