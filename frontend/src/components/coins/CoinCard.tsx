import { CoinListItem } from "@/types/coin";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import { Scissors, Calendar } from "lucide-react";

interface CoinCardProps {
  coin: CoinListItem;
}

// Get metal badge class
function getMetalBadgeClass(metal: string): string {
  const metalMap: Record<string, string> = {
    gold: "badge-metal-gold",
    electrum: "badge-metal-electrum",
    silver: "badge-metal-silver",
    bronze: "badge-metal-bronze",
    copper: "badge-metal-copper",
    billon: "badge-metal-billon",
    orichalcum: "badge-metal-orichalcum",
    lead: "badge-metal-lead",
    potin: "badge-metal-potin",
    ae: "badge-metal-ae",
  };
  return metalMap[metal?.toLowerCase()] || "badge-metal-ae";
}

// Get grade badge class
function getGradeBadgeClass(grade: string): string {
  if (!grade) return "";
  const gradeLower = grade.toLowerCase();
  
  if (gradeLower.includes("ms") || gradeLower.includes("mint")) return "badge-grade-ms";
  if (gradeLower.includes("au")) return "badge-grade-au";
  if (gradeLower.includes("xf") || gradeLower.includes("ef")) return "badge-grade-xf";
  if (gradeLower.includes("vf")) return "badge-grade-vf";
  if (gradeLower.includes("fine") || gradeLower === "f" || gradeLower.includes(" f")) return "badge-grade-f";
  if (gradeLower.includes("vg")) return "badge-grade-vg";
  if (gradeLower.includes("good") || gradeLower === "g") return "badge-grade-g";
  
  return "";
}

// Get category badge class
function getCategoryBadgeClass(category: string): string {
  const catMap: Record<string, string> = {
    imperial: "badge-cat-imperial",
    republic: "badge-cat-republic",
    provincial: "badge-cat-provincial",
    greek: "badge-cat-greek",
    byzantine: "badge-cat-byzantine",
  };
  return catMap[category?.toLowerCase()] || "";
}

// Get rarity badge class
function getRarityBadgeClass(rarity: string): string {
  if (!rarity) return "";
  const rarityLower = rarity.toLowerCase();
  
  if (rarityLower.includes("extremely") || rarityLower === "rr" || rarityLower === "r3") return "badge-rarity-extremely-rare";
  if (rarityLower.includes("very") || rarityLower === "r2") return "badge-rarity-very-rare";
  if (rarityLower.includes("rare") || rarityLower === "r" || rarityLower === "r1") return "badge-rarity-rare";
  if (rarityLower.includes("scarce") || rarityLower === "s") return "badge-rarity-scarce";
  if (rarityLower.includes("common") || rarityLower === "c") return "badge-rarity-common";
  
  return "";
}

// Format year display
function formatYear(start: number | null | undefined, end: number | null | undefined, isCirca?: boolean): string {
  if (!start && !end) return "";
  
  const prefix = isCirca ? "c. " : "";
  
  if (start && end && start !== end) {
    const startStr = start < 0 ? `${Math.abs(start)}` : `${start}`;
    const endStr = end < 0 ? `${Math.abs(end)} BC` : end.toString();
    const startSuffix = start < 0 ? " BC" : "";
    // If same era, only show suffix once
    if ((start < 0 && end < 0) || (start > 0 && end > 0)) {
      return `${prefix}${startStr}–${endStr}${start < 0 ? "" : " AD"}`;
    }
    return `${prefix}${startStr}${startSuffix}–${endStr} ${end > 0 ? "AD" : ""}`.trim();
  }
  
  const year = start || end;
  if (!year) return "";
  return `${prefix}${Math.abs(year)} ${year < 0 ? "BC" : "AD"}`;
}

// Format display name for metal
function formatMetal(metal: string): string {
  if (!metal) return "";
  const metalNames: Record<string, string> = {
    gold: "Au",
    electrum: "El",
    silver: "Ar",
    bronze: "Æ",
    copper: "Cu",
    billon: "Bil",
    orichalcum: "Or",
    lead: "Pb",
    potin: "Pot",
    ae: "Æ",
  };
  return metalNames[metal.toLowerCase()] || metal;
}

export function CoinCard({ coin }: CoinCardProps) {
  const navigate = useNavigate();
  
  const yearDisplay = formatYear(coin.mint_year_start, coin.mint_year_end, coin.is_circa);
  const hasGrade = coin.grade && coin.grade.trim() !== "";
  const gradeClass = getGradeBadgeClass(coin.grade || "");
  const hasRarity = coin.rarity && coin.rarity.trim() !== "";

  return (
    <Card 
      className={cn(
        "coin-card group cursor-pointer overflow-hidden border",
        "hover:border-primary/30 hover:shadow-md"
      )}
      onClick={() => navigate(`/coins/${coin.id}`)}
    >
      {/* Image container - compact aspect ratio */}
      <div className="aspect-[4/3] bg-muted relative overflow-hidden">
        {coin.primary_image ? (
          <img 
            src={`/api${coin.primary_image}`} 
            alt={`${coin.issuing_authority} ${coin.denomination}`}
            className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="flex items-center justify-center h-full bg-gradient-to-br from-muted to-muted/50">
            <div className="text-muted-foreground/40 text-xs font-medium">No Image</div>
          </div>
        )}
        
        {/* Top-left: Category badge */}
        {coin.category && (
          <div className="absolute top-1.5 left-1.5">
            <Badge 
              variant="outline" 
              className={cn(
                "text-[9px] px-1.5 py-0 h-4 font-medium capitalize backdrop-blur-sm bg-background/80",
                getCategoryBadgeClass(coin.category)
              )}
            >
              {coin.category}
            </Badge>
          </div>
        )}
        
        {/* Top-right: Metal badge */}
        <div className="absolute top-1.5 right-1.5 flex flex-col gap-1 items-end">
          <Badge 
            variant="outline" 
            className={cn(
              "text-[10px] px-1.5 py-0 h-4.5 font-semibold backdrop-blur-sm bg-background/80",
              getMetalBadgeClass(coin.metal)
            )}
          >
            {formatMetal(coin.metal)}
          </Badge>
        </div>
        
        {/* Bottom indicators row */}
        <div className="absolute bottom-1.5 left-1.5 right-1.5 flex justify-between items-end">
          {/* Left: Test cut / Circa */}
          <div className="flex gap-1">
            {coin.is_test_cut && (
              <Badge 
                variant="outline"
                className="badge-test-cut text-[9px] px-1 py-0 h-4 flex items-center gap-0.5 backdrop-blur-sm bg-background/80"
              >
                <Scissors className="w-2.5 h-2.5" />
                TC
              </Badge>
            )}
            {coin.is_circa && (
              <Badge 
                variant="outline"
                className="badge-circa text-[9px] px-1 py-0 h-4 flex items-center gap-0.5 backdrop-blur-sm bg-background/80"
              >
                <Calendar className="w-2.5 h-2.5" />
                c.
              </Badge>
            )}
          </div>
          
          {/* Right: Rarity */}
          {hasRarity && (
            <Badge 
              variant="outline"
              className={cn(
                "text-[9px] px-1.5 py-0 h-4 font-medium backdrop-blur-sm bg-background/80",
                getRarityBadgeClass(coin.rarity || "")
              )}
            >
              {coin.rarity}
            </Badge>
          )}
        </div>
      </div>
      
      {/* Content section - compact */}
      <div className="p-2.5 space-y-1">
        {/* Ruler name */}
        <div className="font-semibold text-sm leading-tight truncate" title={coin.issuing_authority}>
          {coin.issuing_authority}
        </div>
        
        {/* Denomination + Mint */}
        <div className="text-xs text-muted-foreground truncate">
          {coin.denomination}
          {coin.mint_name && (
            <span className="opacity-70"> · {coin.mint_name}</span>
          )}
        </div>
        
        {/* Bottom row: Year, Grade, Price */}
        <div className="flex items-center justify-between pt-1 border-t border-border/50">
          {/* Year */}
          <span className="text-[11px] text-muted-foreground tabular-nums font-medium">
            {yearDisplay || "—"}
          </span>
          
          {/* Grade badge */}
          {hasGrade && (
            <Badge 
              variant="outline"
              className={cn(
                "text-[9px] px-1.5 py-0 h-4 font-medium",
                gradeClass
              )}
            >
              {coin.grade}
            </Badge>
          )}
          
          {/* Price */}
          {coin.acquisition_price && (
            <span className="text-xs font-semibold tabular-nums text-foreground">
              ${Number(coin.acquisition_price).toLocaleString()}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}
