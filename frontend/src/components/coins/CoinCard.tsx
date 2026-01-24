import { CoinListItem } from "@/types/coin";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import { Scissors, Calendar } from "lucide-react";

interface CoinCardProps {
  coin: CoinListItem;
}

// Metal badge colors for all metals in expanded enum
const metalColors: Record<string, string> = {
  gold: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
  electrum: "bg-amber-400/10 text-amber-600 border-amber-400/20",
  silver: "bg-slate-500/10 text-slate-600 border-slate-500/20",
  billon: "bg-zinc-500/10 text-zinc-600 border-zinc-500/20",
  potin: "bg-stone-500/10 text-stone-600 border-stone-500/20",
  orichalcum: "bg-yellow-600/10 text-yellow-700 border-yellow-600/20",
  bronze: "bg-orange-500/10 text-orange-600 border-orange-500/20",
  copper: "bg-orange-700/10 text-orange-700 border-orange-700/20",
  lead: "bg-slate-600/10 text-slate-700 border-slate-600/20",
  ae: "bg-neutral-500/10 text-neutral-600 border-neutral-500/20",
  uncertain: "bg-gray-400/10 text-gray-600 border-gray-400/20",
};

// Format year display
function formatYear(start: number | null | undefined, end: number | null | undefined, isCirca?: boolean): string {
  if (!start && !end) return "";
  
  const prefix = isCirca ? "c. " : "";
  
  if (start && end && start !== end) {
    const startStr = start < 0 ? `${Math.abs(start)}` : `${start}`;
    const endStr = end < 0 ? `${Math.abs(end)} BCE` : `${end} CE`;
    return `${prefix}${startStr}–${endStr}`;
  }
  
  const year = start || end;
  if (!year) return "";
  const yearStr = year < 0 ? `${Math.abs(year)} BCE` : `${year} CE`;
  return `${prefix}${yearStr}`;
}

export function CoinCard({ coin }: CoinCardProps) {
  const navigate = useNavigate();
  
  const yearDisplay = formatYear(coin.mint_year_start, coin.mint_year_end, coin.is_circa);

  return (
    <Card 
      className="group cursor-pointer transition-all hover:shadow-lg hover:border-accent/50"
      onClick={() => navigate(`/coins/${coin.id}`)}
    >
      <div className="aspect-square bg-muted relative overflow-hidden">
        {coin.primary_image ? (
          <img 
            src={`/api${coin.primary_image}`} 
            alt={`${coin.issuing_authority} ${coin.denomination}`}
            className="object-cover w-full h-full group-hover:scale-105 transition-transform"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            No Image
          </div>
        )}
        
        {/* Top badges */}
        <div className="absolute top-2 right-2 flex flex-col gap-1 items-end">
          <Badge 
            variant="outline" 
            className={cn("capitalize text-xs", metalColors[coin.metal] || "")}
          >
            {coin.metal}
          </Badge>
          
          {coin.is_test_cut && (
            <Badge 
              variant="destructive" 
              className="text-[10px] px-1.5 py-0 h-5 flex items-center gap-0.5"
            >
              <Scissors className="w-3 h-3" />
              TC
            </Badge>
          )}
        </div>
        
        {/* Bottom left - circa indicator */}
        {coin.is_circa && (
          <div className="absolute bottom-2 left-2">
            <Badge 
              variant="secondary" 
              className="text-[10px] px-1.5 py-0 h-5 flex items-center gap-0.5 bg-background/80 backdrop-blur-sm"
            >
              <Calendar className="w-3 h-3" />
              circa
            </Badge>
          </div>
        )}
      </div>
      
      <CardContent className="p-3">
        <div className="font-medium truncate">{coin.issuing_authority}</div>
        <div className="text-sm text-muted-foreground truncate">
          {coin.denomination}
          {coin.mint_name && ` • ${coin.mint_name}`}
        </div>
        
        {/* Year display */}
        {yearDisplay && (
          <div className="text-xs text-muted-foreground mt-1 tabular-nums">
            {yearDisplay}
          </div>
        )}
        
        <div className="flex justify-between items-center mt-2">
          <span className="text-xs text-muted-foreground">{coin.grade || "—"}</span>
          {coin.acquisition_price && (
            <span className="text-sm font-medium tabular-nums">
              ${Number(coin.acquisition_price).toLocaleString()}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
