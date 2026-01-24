/**
 * ColumnConfig - Column visibility toggle UI
 * 
 * Chip-style toggles for showing/hiding table columns.
 * Persisted via columnStore to localStorage.
 * 
 * @module components/coins/ColumnConfig
 */

import { cn } from "@/lib/utils";
import { useColumnStore, getToggleableColumns } from "@/stores/columnStore";
import { Check, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

// ============================================================================
// TYPES
// ============================================================================

interface ColumnConfigProps {
  className?: string;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function ColumnConfig({ className }: ColumnConfigProps) {
  const { columns, toggleColumn, resetToDefaults } = useColumnStore();
  const toggleableColumns = getToggleableColumns(columns);

  return (
    <div
      className={cn(
        "rounded-lg p-3",
        className
      )}
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <span
          className="text-[11px] font-semibold uppercase tracking-wide"
          style={{ color: "var(--text-tertiary)" }}
        >
          Visible Columns
        </span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-[11px]"
          style={{ color: "var(--text-tertiary)" }}
          onClick={resetToDefaults}
          title="Reset to default columns"
        >
          <RotateCcw className="w-3 h-3 mr-1" />
          Reset
        </Button>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {toggleableColumns.map((column) => (
          <button
            key={column.id}
            onClick={() => toggleColumn(column.id)}
            className={cn(
              "px-2.5 py-1 rounded text-[11px] font-medium transition-colors",
              "border cursor-pointer"
            )}
            style={
              column.visible
                ? {
                    background: "rgba(255, 215, 0, 0.15)",
                    borderColor: "rgba(255, 215, 0, 0.3)",
                    color: "var(--metal-au)",
                  }
                : {
                    background: "var(--bg-card)",
                    borderColor: "var(--border-subtle)",
                    color: "var(--text-secondary)",
                  }
            }
          >
            {column.visible && <Check className="w-3 h-3 inline mr-1" />}
            {column.label}
          </button>
        ))}
      </div>
    </div>
  );
}
