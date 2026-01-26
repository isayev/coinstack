import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle, BookOpen, Bot, Image as ImageIcon, Database } from "lucide-react";
import { Link } from "react-router-dom";

interface ReviewEmptyStateProps {
  variant: "all-clear" | "vocabulary" | "ai" | "images" | "data";
  onAction?: () => void;
  actionLabel?: string;
}

/**
 * ReviewEmptyState - Empty state component for review tabs
 * 
 * Variants:
 * - all-clear: No items to review (main page)
 * - vocabulary: No vocabulary items
 * - ai: No AI suggestions
 * - images: No images to review
 * - data: No data discrepancies
 */
export function ReviewEmptyState({
  variant,
  onAction,
  actionLabel,
}: ReviewEmptyStateProps) {
  const configs = {
    "all-clear": {
      icon: CheckCircle,
      title: "All caught up!",
      description: "No items need your review at the moment. New items will appear here when coins are imported or AI analysis runs.",
      actionLabel: "View Collection",
      actionPath: "/",
    },
    vocabulary: {
      icon: BookOpen,
      title: "No vocabulary items to review",
      description: "Vocabulary assignments are created when you import coins or run bulk normalization.",
      actionLabel: "Run Bulk Normalize",
      actionPath: null,
    },
    ai: {
      icon: Bot,
      title: "No AI suggestions to review",
      description: "AI suggestions appear after running context generation or catalog parsing on coins.",
      actionLabel: "View Collection",
      actionPath: "/",
    },
    images: {
      icon: ImageIcon,
      title: "No images to review",
      description: "Images from auction lots will appear here for assignment to coins.",
      actionLabel: "View Auctions",
      actionPath: "/auctions",
    },
    data: {
      icon: Database,
      title: "No data discrepancies",
      description: "Discrepancies between coin data and auction information will appear here.",
      actionLabel: "View Collection",
      actionPath: "/",
    },
  };

  const config = configs[variant];
  const Icon = config.icon;
  const finalActionLabel = actionLabel || config.actionLabel;

  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-16 px-8">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold mb-2">{config.title}</h3>
        <p className="text-sm text-muted-foreground text-center max-w-md mb-6">
          {config.description}
        </p>
        {config.actionPath ? (
          <Button asChild variant="outline">
            <Link to={config.actionPath}>{finalActionLabel}</Link>
          </Button>
        ) : onAction ? (
          <Button onClick={onAction} variant="outline">
            {finalActionLabel}
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
