import { CoinListItem } from "@/types/coin";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";

interface CoinCardProps {
  coin: CoinListItem;
}

export function CoinCard({ coin }: CoinCardProps) {
  const navigate = useNavigate();
  
  const metalColors: Record<string, string> = {
    gold: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
    silver: "bg-slate-500/10 text-slate-600 border-slate-500/20",
    bronze: "bg-orange-500/10 text-orange-600 border-orange-500/20",
    billon: "bg-zinc-500/10 text-zinc-600 border-zinc-500/20",
  };

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
          <div className="flex items-center justify-center h-full text-muted-foreground">
            No Image
          </div>
        )}
        
        <Badge 
          variant="outline" 
          className={cn("absolute top-2 right-2", metalColors[coin.metal] || "")}
        >
          {coin.metal}
        </Badge>
      </div>
      
      <CardContent className="p-3">
        <div className="font-medium truncate">{coin.issuing_authority}</div>
        <div className="text-sm text-muted-foreground truncate">
          {coin.denomination}
          {coin.mint_name && ` • ${coin.mint_name}`}
        </div>
        <div className="flex justify-between items-center mt-2">
          <span className="text-xs text-muted-foreground">{coin.grade || "—"}</span>
          {coin.acquisition_price && (
            <span className="text-sm font-medium">
              ${Number(coin.acquisition_price).toLocaleString()}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
