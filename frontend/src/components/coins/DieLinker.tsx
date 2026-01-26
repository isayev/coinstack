import { useState } from 'react';
import { useQuery } from "@tanstack/react-query";
import { v2 } from "@/api/v2";
import { Coin } from "@/domain/schemas";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Microscope, Link as LinkIcon, ExternalLink, ChevronUp, ChevronDown, AlertCircle } from "lucide-react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface DieLinkerProps {
  dieId: string | null | undefined;
  side: 'obverse' | 'reverse';
  className?: string;
}

export function DieLinker({ dieId, side, className }: DieLinkerProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const queryKey = ['coins', 'die-link', side, dieId];

  const { data, isLoading, error } = useQuery<Coin[], Error>({
    queryKey: queryKey,
    queryFn: async () => {
      if (!dieId || dieId.length < 3) return [];
      
      const params: Record<string, any> = {};
      if (side === 'obverse') {
        params.obverse_die_id = dieId;
      } else {
        params.reverse_die_id = dieId;
      }
      params.limit = 10;
      
      const response = await v2.getCoins(params);
      return response.items;
    },
    enabled: !!dieId && dieId.length >= 3,
  });

  const hasError = error !== null;

  if (!dieId || dieId.length < 3) return null;

  return (
    <Card className={cn('relative rounded-xl overflow-hidden mt-2', className)}>
      <div 
        className="p-3 pl-4 cursor-pointer hover:bg-muted/50 transition-colors flex items-center justify-between"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          <Microscope className="h-3 w-3" />
          <span>Linked Coins ({data?.length || 0})</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-3 w-3 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        )}
      </div>

      {isExpanded && (
        <CardContent className="p-3 pt-0">
          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground py-2">
              <Loader2 className="h-3 w-3 animate-spin" /> Searching collection...
            </div>
          )}
          
          {hasError && (
            <div className="text-xs text-red-500 flex items-center gap-2 py-2">
              <AlertCircle className="h-3 w-3" /> Error loading linked coins.
            </div>
          )}

          {!isLoading && !hasError && data && data.length > 0 && (
            <div className="grid grid-cols-4 gap-2 pt-2">
              {data.map((coin) => (
                <div key={coin.id} className="relative group aspect-square rounded border overflow-hidden bg-muted">
                  {coin.images?.[0]?.url ? (
                    <img src={coin.images[0].url} className="w-full h-full object-cover" alt={`Coin ${coin.id}`} />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-[10px] text-muted-foreground">
                      #{coin.id}
                    </div>
                  )}
                  <a 
                    href={`/coins/${coin.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer"
                    title={`View Coin #${coin.id}`}
                  >
                    <ExternalLink className="h-4 w-4 text-white" />
                  </a>
                </div>
              ))}
            </div>
          )}
          
          {!isLoading && !hasError && data && data.length === 0 && (
            <p className="text-xs text-muted-foreground italic py-2">
              No other coins found with this die ID.
            </p>
          )}
        </CardContent>
      )}
    </Card>
  );
}
