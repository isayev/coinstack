/**
 * DuplicateAlert - Shows similar coins found during import with merge/skip options.
 * 
 * Features:
 * - Displays similar coins with thumbnails
 * - Shows match reason (exact source, NGC cert, physical match)
 * - View/Merge/Import as New actions
 */
import { AlertTriangle, Eye, Merge, Plus } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CoinSummary, MatchReason } from "@/hooks/useImport";
import { cn } from "@/lib/utils";

interface DuplicateAlertProps {
  similarCoins: CoinSummary[];
  onMerge: (coinId: number) => void;
  onImportAsNew: () => void;
  onViewCoin: (coinId: number) => void;
}

function getMatchReasonLabel(reason: MatchReason): { label: string; variant: "default" | "secondary" | "outline" } {
  switch (reason) {
    case "exact_source":
      return { label: "Exact match", variant: "default" };
    case "ngc_cert":
      return { label: "Same NGC cert", variant: "default" };
    case "physical_match":
      return { label: "Similar specs", variant: "secondary" };
    default:
      return { label: "Match", variant: "outline" };
  }
}

export function DuplicateAlert({
  similarCoins,
  onMerge,
  onImportAsNew,
  onViewCoin,
}: DuplicateAlertProps) {
  if (similarCoins.length === 0) return null;
  
  const hasExactMatch = similarCoins.some(
    (c) => c.match_reason === "exact_source" || c.match_reason === "ngc_cert"
  );
  
  return (
    <Alert className={cn(
      "border-amber-500/50",
      hasExactMatch ? "bg-amber-500/10" : "bg-yellow-500/5"
    )}>
      <AlertTriangle className="h-4 w-4 text-amber-500" />
      <AlertTitle className="text-amber-600">
        {hasExactMatch ? "Duplicate Found" : "Similar Coins Found"}
      </AlertTitle>
      <AlertDescription className="text-muted-foreground">
        {hasExactMatch
          ? "This coin appears to already exist in your collection."
          : "This coin may be similar to existing coins in your collection."}
      </AlertDescription>
      
      <div className="mt-4 space-y-2">
        {similarCoins.map((coin) => {
          const matchInfo = getMatchReasonLabel(coin.match_reason);
          
          return (
            <Card key={coin.id} className="p-3">
              <div className="flex items-center gap-3">
                {/* Thumbnail */}
                {coin.thumbnail ? (
                  <img
                    src={coin.thumbnail}
                    alt=""
                    className="w-14 h-14 rounded-md object-cover bg-muted"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-md bg-muted flex items-center justify-center">
                    <span className="text-2xl text-muted-foreground">🪙</span>
                  </div>
                )}
                
                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{coin.title}</p>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    {coin.grade && <span>{coin.grade}</span>}
                    {coin.weight_g && <span>{coin.weight_g}g</span>}
                    {coin.source_id && (
                      <span className="truncate">#{coin.source_id}</span>
                    )}
                  </div>
                  <Badge
                    variant={matchInfo.variant}
                    className="mt-1 text-xs"
                  >
                    {matchInfo.label}
                    {coin.match_confidence && coin.match_reason === "physical_match" && (
                      <span className="ml-1 opacity-70">
                        ({Math.round(coin.match_confidence * 100)}%)
                      </span>
                    )}
                  </Badge>
                </div>
                
                {/* Actions */}
                <div className="flex flex-col gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs"
                    onClick={() => onViewCoin(coin.id)}
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="default"
                    className="h-7 text-xs"
                    onClick={() => onMerge(coin.id)}
                  >
                    <Merge className="h-3 w-3 mr-1" />
                    Merge
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
      
      <Button
        variant="outline"
        className="mt-4"
        onClick={onImportAsNew}
      >
        <Plus className="h-4 w-4 mr-2" />
        Import as New Coin Anyway
      </Button>
    </Alert>
  );
}
