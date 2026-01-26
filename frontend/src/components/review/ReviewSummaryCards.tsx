import { useReviewCountsRealtime } from "@/hooks/useReviewCountsRealtime";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BookOpen, Bot, Image as ImageIcon, Database, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReviewSummaryCardsProps {
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

/**
 * ReviewSummaryCards - Clickable stat cards showing review counts by category
 * 
 * Features:
 * - 4 cards: Vocabulary, AI Suggestions, Images, Data
 * - Click to switch tabs
 * - Visual states based on count (muted, default, amber, red)
 * - Real-time count updates
 */
export function ReviewSummaryCards({ activeTab, onTabChange }: ReviewSummaryCardsProps) {
  const { data: counts, isLoading } = useReviewCountsRealtime();

  const cards = [
    {
      id: "vocabulary",
      label: "Vocabulary",
      icon: BookOpen,
      count: counts?.vocabulary ?? 0,
      description: "Issuer/Mint/Denomination assignments",
    },
    {
      id: "ai",
      label: "AI Suggestions",
      icon: Bot,
      count: counts?.ai ?? 0,
      description: "LLM catalog references & rarity",
    },
    {
      id: "images",
      label: "Images",
      icon: ImageIcon,
      count: counts?.images ?? 0,
      description: "Coins needing images from auctions",
    },
    {
      id: "data",
      label: "Data",
      icon: Database,
      count: counts?.data ?? 0,
      description: "Discrepancies & Enrichments",
    },
  ];

  const getCardStyle = (count: number, isActive: boolean) => {
    if (count === 0) {
      return {
        border: "1px solid var(--border-subtle)",
        background: "var(--bg-elevated)",
        opacity: 0.6,
      };
    }
    if (count >= 21) {
      return {
        border: isActive ? "2px solid var(--error)" : "1px solid var(--error)",
        background: isActive ? "var(--error-subtle)" : "var(--bg-elevated)",
        boxShadow: isActive ? "0 0 0 3px var(--error-subtle)" : undefined,
      };
    }
    if (count >= 6) {
      return {
        border: isActive ? "2px solid var(--caution)" : "1px solid var(--caution)",
        background: isActive ? "var(--caution-subtle)" : "var(--bg-elevated)",
        boxShadow: isActive ? "0 0 0 3px var(--caution-subtle)" : undefined,
      };
    }
    return {
      border: isActive ? "2px solid var(--primary)" : "1px solid var(--border-subtle)",
      background: isActive ? "var(--primary-subtle)" : "var(--bg-elevated)",
      boxShadow: isActive ? "0 0 0 3px var(--primary-subtle)" : undefined,
    };
  };

  const getCountColor = (count: number) => {
    if (count === 0) return "var(--text-tertiary)";
    if (count >= 21) return "var(--error)";
    if (count >= 6) return "var(--caution)";
    return "var(--text-primary)";
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="h-32" />
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const isActive = activeTab === card.id;
        const Icon = card.icon;
        const style = getCardStyle(card.count, isActive);

        return (
          <Card
            key={card.id}
            className={cn(
              "cursor-pointer transition-all duration-200 hover:shadow-md",
              isActive && "ring-2 ring-offset-2 ring-primary"
            )}
            style={style}
            onClick={() => onTabChange?.(card.id)}
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Icon className="w-4 h-4" style={{ color: getCountColor(card.count) }} />
                {card.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline justify-between">
                <div>
                  <div
                    className="text-3xl font-bold transition-colors"
                    style={{ color: getCountColor(card.count) }}
                  >
                    {card.count}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">pending</p>
                </div>
                {card.count > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 px-2 text-xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      onTabChange?.(card.id);
                    }}
                  >
                    Review
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-2">{card.description}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
