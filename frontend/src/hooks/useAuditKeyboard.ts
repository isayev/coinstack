/**
 * useAuditKeyboard - Keyboard navigation and shortcuts for audit workflow
 * 
 * Shortcuts:
 * - ↑/↓ or j/k: Navigate through conflicts
 * - a: Accept auction value
 * - k (with shift): Keep current value
 * - s or Escape: Skip/dismiss
 * - Space: Toggle selection
 * - Enter: Expand/collapse
 * - ?: Show keyboard shortcuts help
 */

import { useEffect, useCallback, useState } from "react";

export type AuditAction = 
  | "accept"
  | "keep"
  | "skip"
  | "toggle-select"
  | "expand-toggle"
  | "select-all"
  | "show-help";

interface UseAuditKeyboardOptions {
  /** Total number of items */
  itemCount: number;
  /** Current focused index */
  currentIndex: number;
  /** Callback when navigation changes */
  onNavigate: (index: number) => void;
  /** Callback when action is triggered */
  onAction: (action: AuditAction) => void;
  /** Whether keyboard shortcuts are enabled */
  enabled?: boolean;
}

interface UseAuditKeyboardReturn {
  /** Currently focused index */
  focusedIndex: number;
  /** Whether help modal should be shown */
  showHelp: boolean;
  /** Close help modal */
  closeHelp: () => void;
  /** Navigate to specific index */
  navigateTo: (index: number) => void;
  /** Navigate to next item */
  navigateNext: () => void;
  /** Navigate to previous item */
  navigatePrev: () => void;
}

export function useAuditKeyboard({
  itemCount,
  currentIndex,
  onNavigate,
  onAction,
  enabled = true,
}: UseAuditKeyboardOptions): UseAuditKeyboardReturn {
  const [focusedIndex, setFocusedIndex] = useState(currentIndex);
  const [showHelp, setShowHelp] = useState(false);
  
  // Sync with external index changes
  useEffect(() => {
    setFocusedIndex(currentIndex);
  }, [currentIndex]);
  
  const navigateTo = useCallback((index: number) => {
    const clampedIndex = Math.max(0, Math.min(itemCount - 1, index));
    setFocusedIndex(clampedIndex);
    onNavigate(clampedIndex);
  }, [itemCount, onNavigate]);
  
  const navigateNext = useCallback(() => {
    navigateTo(focusedIndex + 1);
  }, [focusedIndex, navigateTo]);
  
  const navigatePrev = useCallback(() => {
    navigateTo(focusedIndex - 1);
  }, [focusedIndex, navigateTo]);
  
  const closeHelp = useCallback(() => {
    setShowHelp(false);
  }, []);
  
  useEffect(() => {
    if (!enabled) return;
    
    function handleKeyDown(e: KeyboardEvent) {
      // Don't capture if in input/textarea/contenteditable
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.contentEditable === 'true'
      ) {
        return;
      }
      
      // Navigation
      switch (e.key) {
        case "ArrowUp":
        case "k":
          if (!e.shiftKey) {
            e.preventDefault();
            navigatePrev();
          }
          break;
          
        case "ArrowDown":
        case "j":
          e.preventDefault();
          navigateNext();
          break;
          
        case "Home":
          e.preventDefault();
          navigateTo(0);
          break;
          
        case "End":
          e.preventDefault();
          navigateTo(itemCount - 1);
          break;
          
        case "PageUp":
          e.preventDefault();
          navigateTo(Math.max(0, focusedIndex - 10));
          break;
          
        case "PageDown":
          e.preventDefault();
          navigateTo(Math.min(itemCount - 1, focusedIndex + 10));
          break;
      }
      
      // Actions
      switch (e.key.toLowerCase()) {
        case "a":
          e.preventDefault();
          onAction("accept");
          break;
          
        case "k":
          if (e.shiftKey) {
            e.preventDefault();
            onAction("keep");
          }
          break;
          
        case "s":
        case "escape":
          e.preventDefault();
          onAction("skip");
          break;
          
        case " ":
          e.preventDefault();
          onAction("toggle-select");
          break;
          
        case "enter":
          e.preventDefault();
          onAction("expand-toggle");
          break;
          
        case "?":
          e.preventDefault();
          setShowHelp(true);
          onAction("show-help");
          break;
      }
      
      // Ctrl/Cmd shortcuts
      if (e.ctrlKey || e.metaKey) {
        switch (e.key.toLowerCase()) {
          case "a":
            e.preventDefault();
            onAction("select-all");
            break;
        }
      }
    }
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    enabled,
    itemCount,
    focusedIndex,
    navigateTo,
    navigateNext,
    navigatePrev,
    onAction,
  ]);
  
  return {
    focusedIndex,
    showHelp,
    closeHelp,
    navigateTo,
    navigateNext,
    navigatePrev,
  };
}

/**
 * Keyboard shortcuts data for help display
 */
export const KEYBOARD_SHORTCUTS = [
  { keys: ["↑", "k"], description: "Previous item" },
  { keys: ["↓", "j"], description: "Next item" },
  { keys: ["Home"], description: "First item" },
  { keys: ["End"], description: "Last item" },
  { keys: ["PgUp"], description: "Jump 10 items up" },
  { keys: ["PgDn"], description: "Jump 10 items down" },
  { keys: ["a"], description: "Accept auction value" },
  { keys: ["Shift", "k"], description: "Keep current value" },
  { keys: ["s", "Esc"], description: "Skip / dismiss" },
  { keys: ["Space"], description: "Toggle selection" },
  { keys: ["Enter"], description: "Expand / collapse" },
  { keys: ["Ctrl", "a"], description: "Select all" },
  { keys: ["?"], description: "Show this help" },
];

export default useAuditKeyboard;
