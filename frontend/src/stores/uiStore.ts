import { create } from "zustand";

const BREAKPOINTS = {
  mobile: 640,
  tablet: 1024,
  desktop: 1280
} as const;

function getScreenSize(): 'mobile' | 'tablet' | 'desktop' {
  if (typeof window === 'undefined') return 'desktop';
  const width = window.innerWidth;
  if (width < BREAKPOINTS.mobile) return 'mobile';
  if (width < BREAKPOINTS.desktop) return 'tablet';
  return 'desktop';
}

export type ViewMode = "grid" | "table" | "compact";

interface UIState {
  sidebarOpen: boolean;
  viewMode: ViewMode;
  parseListingOpen: boolean;
  commandPaletteOpen: boolean;
  quickScrapeOpen: boolean;
  screenSize: 'mobile' | 'tablet' | 'desktop';

  toggleSidebar: () => void;
  setViewMode: (mode: ViewMode) => void;
  setParseListingOpen: (open: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setQuickScrapeOpen: (open: boolean) => void;
  setScreenSize: (size: 'mobile' | 'tablet' | 'desktop') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  viewMode: "grid",
  parseListingOpen: false,
  commandPaletteOpen: false,
  quickScrapeOpen: false,
  screenSize: getScreenSize(),

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setViewMode: (viewMode) => set({ viewMode }),
  setParseListingOpen: (parseListingOpen) => set({ parseListingOpen }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
  setQuickScrapeOpen: (quickScrapeOpen) => set({ quickScrapeOpen }),
  setScreenSize: (screenSize) => set({ screenSize }),
}));

export { getScreenSize };
