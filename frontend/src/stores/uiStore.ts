import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  viewMode: "grid" | "table";
  parseListingOpen: boolean;
  commandPaletteOpen: boolean;
  
  toggleSidebar: () => void;
  setViewMode: (mode: "grid" | "table") => void;
  setParseListingOpen: (open: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  viewMode: "grid",
  parseListingOpen: false,
  commandPaletteOpen: false,
  
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setViewMode: (viewMode) => set({ viewMode }),
  setParseListingOpen: (parseListingOpen) => set({ parseListingOpen }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
}));
