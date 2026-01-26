/**
 * Selection store for bulk operations on coins
 * 
 * Features:
 * - Toggle individual coin selection
 * - Select/deselect all visible coins
 * - Clear selection
 * - Track selection mode state
 * 
 * @module stores/selectionStore
 */

import { create } from 'zustand';

interface SelectionState {
  // Selected coin IDs
  selectedIds: Set<number>;
  
  // Whether user is in selection mode
  isSelecting: boolean;
  
  // Actions
  toggle: (id: number) => void;
  select: (id: number) => void;
  deselect: (id: number) => void;
  selectAll: (ids: number[]) => void;
  selectRange: (startId: number, endId: number, allIds: number[]) => void;
  clear: () => void;
  setSelecting: (isSelecting: boolean) => void;
  
  // Computed helpers
  isSelected: (id: number) => boolean;
  count: () => number;
  getSelectedIds: () => number[];
}

export const useSelectionStore = create<SelectionState>((set, get) => ({
  selectedIds: new Set(),
  isSelecting: false,
  
  toggle: (id) => set((state) => {
    const newSet = new Set(state.selectedIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    return { 
      selectedIds: newSet,
      isSelecting: newSet.size > 0
    };
  }),
  
  select: (id) => set((state) => {
    const newSet = new Set(state.selectedIds);
    newSet.add(id);
    return { 
      selectedIds: newSet,
      isSelecting: true
    };
  }),
  
  deselect: (id) => set((state) => {
    const newSet = new Set(state.selectedIds);
    newSet.delete(id);
    return { 
      selectedIds: newSet,
      isSelecting: newSet.size > 0
    };
  }),
  
  selectAll: (ids) => set({ 
    selectedIds: new Set(ids),
    isSelecting: ids.length > 0
  }),
  
  selectRange: (startId, endId, allIds) => set((state) => {
    const startIdx = allIds.indexOf(startId);
    const endIdx = allIds.indexOf(endId);
    
    if (startIdx === -1 || endIdx === -1) return state;
    
    const [from, to] = startIdx < endIdx ? [startIdx, endIdx] : [endIdx, startIdx];
    const rangeIds = allIds.slice(from, to + 1);
    
    const newSet = new Set(state.selectedIds);
    rangeIds.forEach(id => newSet.add(id));
    
    return { 
      selectedIds: newSet,
      isSelecting: true
    };
  }),
  
  clear: () => set({ 
    selectedIds: new Set(),
    isSelecting: false
  }),
  
  setSelecting: (isSelecting) => set({ isSelecting }),
  
  // Helper methods
  isSelected: (id) => get().selectedIds.has(id),
  count: () => get().selectedIds.size,
  getSelectedIds: () => Array.from(get().selectedIds),
}));

/**
 * Hook to use selection state with common patterns
 */
export function useSelection() {
  const store = useSelectionStore();
  
  return {
    selectedIds: store.selectedIds,
    isSelecting: store.isSelecting,
    selectedCount: store.count(),
    
    toggle: store.toggle,
    select: store.select,
    deselect: store.deselect,
    selectAll: store.selectAll,
    selectRange: store.selectRange,
    clear: store.clear,
    isSelected: store.isSelected,
    getSelectedIds: store.getSelectedIds,
  };
}
