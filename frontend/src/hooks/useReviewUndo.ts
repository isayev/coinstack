import { useState, useCallback } from "react";
import { toast } from "sonner";

export interface UndoAction {
  type: "approve" | "reject";
  itemIds: number[];
  tab: "vocabulary" | "ai" | "images" | "data";
  timestamp: number;
  undoFn: () => Promise<void>;
}

/**
 * useReviewUndo - Per-tab undo stack for review actions
 * 
 * Maintains a stack of the last 3 actions per tab.
 * Provides toast notifications with undo buttons.
 */
export function useReviewUndo() {
  const [undoStacks, setUndoStacks] = useState<Record<string, UndoAction[]>>({});

  const pushAction = useCallback(
    (action: Omit<UndoAction, "timestamp">) => {
      const tab = action.tab;
      const newAction: UndoAction = {
        ...action,
        timestamp: Date.now(),
      };

      setUndoStacks((prev) => {
        const tabStack = prev[tab] || [];
        const newStack = [newAction, ...tabStack].slice(0, 3); // Keep last 3
        return { ...prev, [tab]: newStack };
      });

      // Show toast with undo button
      const actionLabel = action.type === "approve" ? "Approved" : "Rejected";
      const count = action.itemIds.length;
      const itemLabel = count === 1 ? "item" : "items";

      toast.success(`${actionLabel} ${count} ${itemLabel}`, {
        action: {
          label: "Undo",
          onClick: () => undoLast(tab),
        },
        duration: 5000,
      });
    },
    []
  );

  const undoLast = useCallback(async (tab: string) => {
    setUndoStacks((prev) => {
      const tabStack = prev[tab] || [];
      if (tabStack.length === 0) {
        toast.error("Nothing to undo");
        return prev;
      }

      const [lastAction, ...rest] = tabStack;
      
      // Execute undo function
      lastAction.undoFn().catch((error) => {
        console.error("Undo failed:", error);
        toast.error("Failed to undo action");
      });

      toast.info(`Undone: ${lastAction.type} ${lastAction.itemIds.length} item(s)`);

      return { ...prev, [tab]: rest };
    });
  }, []);

  const clearStack = useCallback((tab: string) => {
    setUndoStacks((prev) => {
      const { [tab]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  return {
    pushAction,
    undoLast,
    clearStack,
    hasUndo: (tab: string) => (undoStacks[tab]?.length || 0) > 0,
  };
}
