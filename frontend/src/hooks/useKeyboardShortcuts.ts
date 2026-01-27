/**
 * Global keyboard shortcuts for CoinStack
 * 
 * Shortcuts:
 * - Cmd/Ctrl+K: Open command palette
 * - N: New coin (manual entry)
 * - U: Paste URL (quick scrape)
 * - /: Focus search
 * - G C: Go to Collection
 * - G S: Go to Statistics
 * - G E: Go to Settings
 * - Escape: Clear selection, close modals
 * 
 * @module hooks/useKeyboardShortcuts
 */

import { useHotkeys } from 'react-hotkeys-hook';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '@/stores/uiStore';
import { useCallback } from 'react';

/**
 * Check if an input element is currently focused
 */
function isInputFocused(): boolean {
  const active = document.activeElement;
  if (!active) return false;
  
  return (
    active instanceof HTMLInputElement ||
    active instanceof HTMLTextAreaElement ||
    active.getAttribute('contenteditable') === 'true'
  );
}

/**
 * Hook to set up global keyboard shortcuts
 * Call once in the app root (e.g., App.tsx or AppShell)
 */
export function useKeyboardShortcuts() {
  const navigate = useNavigate();
  const { setCommandPaletteOpen, setQuickScrapeOpen, commandPaletteOpen } = useUIStore();

  // Cmd/Ctrl+K - Open command palette (always active)
  useHotkeys('mod+k', (e) => {
    e.preventDefault();
    setCommandPaletteOpen(true);
  }, { enableOnFormTags: true });

  // Escape - Close command palette, clear selection
  useHotkeys('escape', () => {
    if (commandPaletteOpen) {
      setCommandPaletteOpen(false);
    }
    // Future: clear selection
  });

  // N - New coin (only when not in input)
  useHotkeys('n', () => {
    if (!isInputFocused()) {
      navigate('/coins/new');
    }
  }, { enabled: () => !isInputFocused() });

  // U - Paste URL / Quick scrape (only when not in input)
  useHotkeys('u', () => {
    if (!isInputFocused()) {
      setQuickScrapeOpen(true);
    }
  }, { enabled: () => !isInputFocused() });

  // / - Focus search
  useHotkeys('/', (e) => {
    if (!isInputFocused()) {
      e.preventDefault();
      const searchInput = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement;
      if (searchInput) {
        searchInput.focus();
      }
    }
  });

  // G then C - Go to Collection
  useHotkeys('g c', () => {
    if (!isInputFocused()) {
      navigate('/');
    }
  });

  // G then S - Go to Statistics
  useHotkeys('g s', () => {
    if (!isInputFocused()) {
      navigate('/stats');
    }
  });

  // G then E - Go to Settings
  useHotkeys('g e', () => {
    if (!isInputFocused()) {
      navigate('/settings');
    }
  });

  // ? - Show keyboard shortcuts help (future)
  useHotkeys('shift+/', () => {
    if (!isInputFocused()) {
      // TODO: Implement shortcuts help modal
      if (import.meta.env.DEV) {
        console.log('Keyboard shortcuts: Cmd+K (palette), N (new), U (url), / (search), G+C/S/E (navigate)');
      }
    }
  });
}

/**
 * Hook for grid navigation (vim-style)
 * Use in components with grid layouts
 */
export function useGridNavigation(
  itemCount: number,
  columns: number,
  onSelect?: (index: number) => void
) {
  const setFocusIndex = useCallback((index: number) => {
    const element = document.querySelector(`[data-grid-index="${index}"]`) as HTMLElement;
    if (element) {
      element.focus();
      onSelect?.(index);
    }
  }, [onSelect]);

  // J - Move down
  useHotkeys('j', () => {
    if (!isInputFocused()) {
      const current = document.activeElement?.getAttribute('data-grid-index');
      if (current !== null) {
        const newIndex = Math.min(Number(current) + columns, itemCount - 1);
        setFocusIndex(newIndex);
      }
    }
  });

  // K - Move up
  useHotkeys('k', () => {
    if (!isInputFocused()) {
      const current = document.activeElement?.getAttribute('data-grid-index');
      if (current !== null) {
        const newIndex = Math.max(Number(current) - columns, 0);
        setFocusIndex(newIndex);
      }
    }
  });

  // H - Move left
  useHotkeys('h', () => {
    if (!isInputFocused()) {
      const current = document.activeElement?.getAttribute('data-grid-index');
      if (current !== null) {
        const newIndex = Math.max(Number(current) - 1, 0);
        setFocusIndex(newIndex);
      }
    }
  });

  // L - Move right
  useHotkeys('l', () => {
    if (!isInputFocused()) {
      const current = document.activeElement?.getAttribute('data-grid-index');
      if (current !== null) {
        const newIndex = Math.min(Number(current) + 1, itemCount - 1);
        setFocusIndex(newIndex);
      }
    }
  });

  // Home - Go to first
  useHotkeys('home', () => {
    if (!isInputFocused()) {
      setFocusIndex(0);
    }
  });

  // End - Go to last
  useHotkeys('end', () => {
    if (!isInputFocused()) {
      setFocusIndex(itemCount - 1);
    }
  });

  return { setFocusIndex };
}
