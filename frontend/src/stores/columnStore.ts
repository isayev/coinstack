/**
 * Column visibility and ordering store for the coin table
 * 
 * Manages which columns are visible in the table view and their order.
 * Persisted to localStorage for user preferences.
 * 
 * @module stores/columnStore
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { SortField } from "./filterStore";

// ============================================================================
// TYPES
// ============================================================================

export interface ColumnConfig {
  id: string;
  label: string;
  visible: boolean;
  sortable: boolean;
  sortField?: SortField;
  width: string;
}

export interface ColumnStore {
  columns: ColumnConfig[];
  setColumnVisibility: (columnId: string, visible: boolean) => void;
  toggleColumn: (columnId: string) => void;
  reorderColumns: (fromIndex: number, toIndex: number) => void;
  resetToDefaults: () => void;
  getVisibleColumns: () => ColumnConfig[];
}

// ============================================================================
// DEFAULT COLUMNS
// ============================================================================

const DEFAULT_COLUMNS: ColumnConfig[] = [
  // Structural columns (always first)
  { id: "category", label: "Category", visible: true, sortable: true, sortField: "category", width: "4px" },
  { id: "checkbox", label: "Select", visible: true, sortable: false, width: "32px" },
  
  // New order: image, metal, grade, ruler, date, denomination, obverse, reverse, mint, then others
  { id: "thumbnail", label: "Image", visible: true, sortable: false, width: "40px" },
  { id: "metal", label: "Metal", visible: true, sortable: true, sortField: "metal", width: "40px" },
  { id: "grade", label: "Grade", visible: true, sortable: true, sortField: "grade", width: "50px" },
  { id: "ruler", label: "Ruler", visible: true, sortable: true, sortField: "name", width: "160px" },
  { id: "date", label: "Date", visible: true, sortable: true, sortField: "year", width: "90px" },
  { id: "denomination", label: "Denom", visible: true, sortable: true, sortField: "denomination", width: "90px" },
  { id: "obverse", label: "Obverse", visible: true, sortable: false, width: "150px" },
  { id: "reverse", label: "Reverse", visible: true, sortable: false, width: "150px" },
  { id: "mint", label: "Mint", visible: true, sortable: false, width: "80px" },
  
  // Other visible columns
  { id: "reference", label: "Reference", visible: true, sortable: false, width: "100px" },
  { id: "rarity", label: "Rarity", visible: true, sortable: true, sortField: "rarity", width: "50px" },
  { id: "value", label: "Value", visible: true, sortable: true, sortField: "price", width: "80px" },
  
  // Optional columns (hidden by default)
  { id: "weight", label: "Weight", visible: false, sortable: true, sortField: "weight", width: "60px" },
  { id: "diameter", label: "Diameter", visible: false, sortable: false, width: "60px" },
  { id: "dieAxis", label: "Die Axis", visible: false, sortable: false, width: "50px" },
  { id: "acquired", label: "Acquired", visible: false, sortable: true, sortField: "acquired", width: "100px" },
  { id: "provenance", label: "Provenance", visible: false, sortable: false, width: "150px" },
];

// ============================================================================
// STORE
// ============================================================================

/**
 * Merge stored columns with defaults, adding any missing columns
 * and updating the order to match defaults
 */
function mergeColumnsWithDefaults(storedColumns: ColumnConfig[]): ColumnConfig[] {
  const defaultIds = new Set(DEFAULT_COLUMNS.map((c) => c.id));
  
  // Start with default order
  const merged: ColumnConfig[] = [];
  
  for (const defaultCol of DEFAULT_COLUMNS) {
    const stored = storedColumns.find((c) => c.id === defaultCol.id);
    if (stored) {
      // Use stored visibility but update other properties from defaults
      merged.push({
        ...defaultCol,
        visible: stored.visible,
      });
    } else {
      // New column - use defaults
      merged.push(defaultCol);
    }
  }
  
  // Add any custom columns that aren't in defaults (shouldn't happen but be safe)
  for (const stored of storedColumns) {
    if (!defaultIds.has(stored.id)) {
      merged.push(stored);
    }
  }
  
  return merged;
}

export const useColumnStore = create<ColumnStore>()(
  persist(
    (set, get) => ({
      columns: DEFAULT_COLUMNS,

      setColumnVisibility: (columnId: string, visible: boolean) => {
        set((state) => ({
          columns: state.columns.map((col) =>
            col.id === columnId ? { ...col, visible } : col
          ),
        }));
      },

      toggleColumn: (columnId: string) => {
        set((state) => ({
          columns: state.columns.map((col) =>
            col.id === columnId ? { ...col, visible: !col.visible } : col
          ),
        }));
      },

      reorderColumns: (fromIndex: number, toIndex: number) => {
        set((state) => {
          const newColumns = [...state.columns];
          const [removed] = newColumns.splice(fromIndex, 1);
          newColumns.splice(toIndex, 0, removed);
          return { columns: newColumns };
        });
      },

      resetToDefaults: () => {
        set({ columns: DEFAULT_COLUMNS });
      },

      getVisibleColumns: () => {
        return get().columns.filter((col) => col.visible);
      },
    }),
    {
      name: "coinstack-columns",
      version: 2, // Incremented to trigger migration
      migrate: (persistedState: unknown, version: number) => {
        const state = persistedState as { columns?: ColumnConfig[] };
        
        if (version < 2 && state.columns) {
          // Migrate from v1: merge with defaults to add new columns (obverse, reverse)
          return {
            ...state,
            columns: mergeColumnsWithDefaults(state.columns),
          };
        }
        
        return state;
      },
    }
  )
);

// ============================================================================
// SELECTORS
// ============================================================================

/**
 * Get columns that can be toggled (excludes structural columns)
 */
export function getToggleableColumns(columns: ColumnConfig[]): ColumnConfig[] {
  const nonToggleable = ["category", "checkbox", "thumbnail"];
  return columns.filter((col) => !nonToggleable.includes(col.id));
}

/**
 * Get count of visible optional columns
 */
export function getVisibleOptionalCount(columns: ColumnConfig[]): number {
  const optionalColumns = ["weight", "diameter", "dieAxis", "acquired", "provenance"];
  return columns.filter((col) => optionalColumns.includes(col.id) && col.visible).length;
}
