import { Button } from "@/components/ui/button";
import { X, Check, Eye } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/uiStore";

interface ReviewBulkActionsBarProps {
  selectedCount: number;
  onClearSelection: () => void;
  onApproveAll: () => void;
  onRejectAll: () => void;
  onPreview?: () => void;
  showPreview?: boolean;
  isLoading?: boolean;
}

/**
 * ReviewBulkActionsBar - Fixed bottom bar for bulk review actions
 * 
 * Features:
 * - Shows selected count
 * - Bulk approve/reject actions
 * - Optional preview button (for 5+ items)
 * - Keyboard shortcuts support
 * - Undo integration via toast notifications
 */
export function ReviewBulkActionsBar({
  selectedCount,
  onClearSelection,
  onApproveAll,
  onRejectAll,
  onPreview,
  showPreview = false,
  isLoading = false,
}: ReviewBulkActionsBarProps) {
  const { sidebarOpen } = useUIStore();
  
  if (selectedCount === 0) {
    return null;
  }

  // Match sidebar width from AppShell (ml-48 = 192px, ml-14 = 56px)
  const sidebarMargin = sidebarOpen ? 192 : 56;

  return (
    <div
      className={cn(
        "fixed bottom-0 z-50",
        "bg-background border-t border-border",
        "px-6 py-3 shadow-lg",
        "transition-all duration-200"
      )}
      style={{
        left: `${sidebarMargin}px`,
        right: 0,
      }}
    >
      <div className="container mx-auto flex items-center justify-between max-w-7xl">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded border-2 border-primary bg-primary/10 flex items-center justify-center">
              <span className="text-xs font-semibold text-primary">{selectedCount}</span>
            </div>
            <span className="text-sm font-medium">
              {selectedCount} {selectedCount === 1 ? "item" : "items"} selected
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearSelection}
            className="text-xs"
          >
            <X className="w-3 h-3 mr-1" />
            Clear Selection
          </Button>
        </div>

        <div className="flex items-center gap-2">
          {showPreview && selectedCount >= 5 && onPreview && (
            <Button
              variant="outline"
              size="sm"
              onClick={onPreview}
              disabled={isLoading}
              className="text-xs"
            >
              <Eye className="w-3 h-3 mr-1" />
              Preview Selection
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onRejectAll}
            disabled={isLoading}
            className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            <X className="w-3 h-3 mr-1" />
            Reject All
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={onApproveAll}
            disabled={isLoading}
            className="text-xs bg-green-600 hover:bg-green-700"
          >
            <Check className="w-3 h-3 mr-1" />
            Approve All
          </Button>
        </div>
      </div>
    </div>
  );
}
