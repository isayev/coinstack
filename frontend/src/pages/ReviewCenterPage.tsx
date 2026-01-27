import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { useHotkeys } from "react-hotkeys-hook";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BookOpen, Bot, Image as ImageIcon, Database, AlertTriangle, Sparkles, Merge, History } from "lucide-react";
import {
  ReviewSummaryCards,
  VocabularyReviewTab,
  AIReviewTab,
  DataReviewTab,
  DiscrepanciesReviewTab,
  EnrichmentsReviewTab,
  AutoMergeReviewTab,
  HistoryReviewTab,
} from "@/components/review";
import { ImageReviewTab } from "@/components/audit";
import { useReviewCountsRealtime } from "@/hooks/useReviewCountsRealtime";

type TabId = "vocabulary" | "ai" | "images" | "discrepancies" | "enrichments" | "auto-merge" | "history" | "data";

/**
 * ReviewCenterPage - Unified review center for all review tasks
 * 
 * Features:
 * - 8 tabs: Vocabulary, AI Suggestions, Images, Discrepancies, Enrichments, Auto-Merge, History, Data
 * - Summary cards at top (clickable to switch tabs)
 * - URL-based tab selection (?tab=vocabulary)
 * - Keyboard shortcuts (j/k navigation, 1-8 tab switching, a/r approve/reject, Space select, Escape clear)
 * - Real-time count updates
 */
export function ReviewCenterPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { data: counts } = useReviewCountsRealtime();
  
  // Get active tab from URL or default to first tab with items
  const getInitialTab = (): TabId => {
    const tabParam = searchParams.get("tab") as TabId | null;
    const validTabs: TabId[] = ["vocabulary", "ai", "images", "discrepancies", "enrichments", "auto-merge", "history", "data"];
    if (tabParam && validTabs.includes(tabParam)) {
      return tabParam;
    }
    // Default to first tab with items
    if (counts?.vocabulary && counts.vocabulary > 0) return "vocabulary";
    if (counts?.ai && counts.ai > 0) return "ai";
    if (counts?.images && counts.images > 0) return "images";
    if (counts?.discrepancies && counts.discrepancies > 0) return "discrepancies";
    if (counts?.enrichments && counts.enrichments > 0) return "enrichments";
    return "vocabulary";
  };

  const [activeTab, setActiveTab] = useState<TabId>(getInitialTab());
  const cardRefs = useRef<Map<number, HTMLElement>>(new Map());
  const [_focusedIndex, setFocusedIndex] = useState<number>(-1);

  // Update tab from URL
  useEffect(() => {
    const tabParam = searchParams.get("tab") as TabId | null;
    const validTabs: TabId[] = ["vocabulary", "ai", "images", "discrepancies", "enrichments", "auto-merge", "history", "data"];
    if (tabParam && validTabs.includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  // Update URL when tab changes
  const handleTabChange = useCallback((tab: TabId) => {
    setActiveTab(tab);
    setSearchParams({ tab });
    setFocusedIndex(-1);
  }, [setSearchParams]);

  // Keyboard shortcuts
  // j/k - Navigate cards
  useHotkeys(
    "j",
    (e) => {
      if (isInputFocused()) return;
      e.preventDefault();
      setFocusedIndex((prev) => {
        const next = prev + 1;
        const card = cardRefs.current.get(next);
        if (card) {
          card.scrollIntoView({ behavior: "smooth", block: "nearest" });
          card.focus();
        }
        return next;
      });
    },
    { enabled: activeTab === "vocabulary" || activeTab === "ai" }
  );

  useHotkeys(
    "k",
    (e) => {
      if (isInputFocused()) return;
      e.preventDefault();
      setFocusedIndex((prev) => {
        const next = Math.max(prev - 1, -1);
        const card = cardRefs.current.get(next);
        if (card) {
          card.scrollIntoView({ behavior: "smooth", block: "nearest" });
          card.focus();
        }
        return next;
      });
    },
    { enabled: activeTab === "vocabulary" || activeTab === "ai" }
  );

  // 1-8 - Switch tabs
  useHotkeys("1", () => handleTabChange("vocabulary"), { enabled: !isInputFocused() });
  useHotkeys("2", () => handleTabChange("ai"), { enabled: !isInputFocused() });
  useHotkeys("3", () => handleTabChange("images"), { enabled: !isInputFocused() });
  useHotkeys("4", () => handleTabChange("discrepancies"), { enabled: !isInputFocused() });
  useHotkeys("5", () => handleTabChange("enrichments"), { enabled: !isInputFocused() });
  useHotkeys("6", () => handleTabChange("auto-merge"), { enabled: !isInputFocused() });
  useHotkeys("7", () => handleTabChange("history"), { enabled: !isInputFocused() });
  useHotkeys("8", () => handleTabChange("data"), { enabled: !isInputFocused() });

  // ? - Show keyboard help
  useHotkeys("shift+/", (e) => {
    if (isInputFocused()) return;
    e.preventDefault();
    // TODO: Show keyboard shortcuts modal
    if (import.meta.env.DEV) {
      console.log("Review shortcuts: j/k (navigate), 1-4 (tabs), a (approve), r (reject), Space (select), Escape (clear)");
    }
  });

  const tabs = [
    {
      id: "vocabulary" as TabId,
      label: "Vocabulary",
      icon: BookOpen,
      count: counts?.vocabulary ?? 0,
      content: <VocabularyReviewTab />,
    },
    {
      id: "ai" as TabId,
      label: "AI Suggestions",
      icon: Bot,
      count: counts?.ai ?? 0,
      content: <AIReviewTab />,
    },
    {
      id: "images" as TabId,
      label: "Images",
      icon: ImageIcon,
      count: counts?.images ?? 0,
      content: <ImageReviewTab />,
    },
    {
      id: "discrepancies" as TabId,
      label: "Discrepancies",
      icon: AlertTriangle,
      count: counts?.discrepancies ?? 0,
      content: <DiscrepanciesReviewTab />,
    },
    {
      id: "enrichments" as TabId,
      label: "Enrichments",
      icon: Sparkles,
      count: counts?.enrichments ?? 0,
      content: <EnrichmentsReviewTab />,
    },
    {
      id: "auto-merge" as TabId,
      label: "Auto-Merge",
      icon: Merge,
      count: undefined,
      content: <AutoMergeReviewTab />,
    },
    {
      id: "history" as TabId,
      label: "History",
      icon: History,
      count: undefined,
      content: <HistoryReviewTab />,
    },
    {
      id: "data" as TabId,
      label: "Data",
      icon: Database,
      count: counts?.data ?? 0,
      content: <DataReviewTab />,
    },
  ];

  return (
    <div className="container mx-auto px-4 py-6 space-y-6 max-w-7xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Review Center</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review and approve vocabulary assignments, AI suggestions, and other pending items
        </p>
      </div>

      {/* Summary Cards */}
      <ReviewSummaryCards activeTab={activeTab} onTabChange={(tab) => handleTabChange(tab as TabId)} />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => handleTabChange(v as TabId)}>
        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className="flex items-center gap-2 text-xs"
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs font-semibold rounded-full bg-primary/10 text-primary">
                    {tab.count}
                  </span>
                )}
              </TabsTrigger>
            );
          })}
        </TabsList>

        {tabs.map((tab) => (
          <TabsContent key={tab.id} value={tab.id} className="mt-6">
            {tab.content}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

function isInputFocused(): boolean {
  const active = document.activeElement;
  if (!active) return false;
  return (
    active instanceof HTMLInputElement ||
    active instanceof HTMLTextAreaElement ||
    active.getAttribute("contenteditable") === "true"
  );
}
