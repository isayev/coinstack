import { CoinListItem } from "@/types/coin";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import { Scissors } from "lucide-react";

interface CoinCardProps {
  coin: CoinListItem;
}

// Metal configuration - element symbols and badge classes
const METAL_CONFIG: Record<string, { symbol: string; badge: string }> = {
  gold: { symbol: "Au", badge: "metal-badge-au" },
  electrum: { symbol: "EL", badge: "metal-badge-el" },
  silver: { symbol: "Ag", badge: "metal-badge-ag" },
  orichalcum: { symbol: "Or", badge: "metal-badge-or" },
  brass: { symbol: "Br", badge: "metal-badge-br" },
  bronze: { symbol: "Cu", badge: "metal-badge-cu" },
  copper: { symbol: "Cu", badge: "metal-badge-copper" },
  ae: { symbol: "Æ", badge: "metal-badge-ae" },
  billon: { symbol: "Bi", badge: "metal-badge-bi" },
  potin: { symbol: "Po", badge: "metal-badge-po" },
  lead: { symbol: "Pb", badge: "metal-badge-pb" },
};

// Category border classes
const CATEGORY_BORDERS: Record<string, string> = {
  republic: "category-border-republic",
  imperial: "category-border-imperial",
  provincial: "category-border-provincial",
  late: "category-border-late",
  greek: "category-border-greek",
  celtic: "category-border-celtic",
  judaea: "category-border-judaea",
  judaean: "category-border-judaea",
  eastern: "category-border-eastern",
  byzantine: "category-border-byzantine",
  other: "category-border-other",
};

// Rarity dot classes (C→S→R1→R2→R3→U)
function getRarityDotClass(rarity: string | null | undefined): string {
  if (!rarity) return "";
  const r = rarity.toLowerCase().trim();
  
  if (r === "u" || r === "unique") return "rarity-dot-u";
  if (r === "r3" || r.includes("extremely")) return "rarity-dot-r3";
  if (r === "r2" || r.includes("very")) return "rarity-dot-r2";
  if (r === "r1" || r === "rare" || r === "r") return "rarity-dot-r1";
  if (r === "s" || r.includes("scarce")) return "rarity-dot-s";
  if (r === "c" || r.includes("common")) return "rarity-dot-c";
  
  return "rarity-dot-c";
}

// Grade badge class (temperature scale)
function getGradeBadgeClass(grade: string | null | undefined): string {
  if (!grade) return "";
  const g = grade.toUpperCase();
  
  if (g.includes("MS") || g.includes("FDC") || g.includes("MINT")) return "grade-badge-ms";
  if (g.includes("AU") || g.includes("ABOUT UNC")) return "grade-badge-au";
  if (g.includes("EF") || g.includes("XF") || g.includes("EXTREMELY")) return "grade-badge-ef";
  if (g.includes("VF") || g.includes("VERY FINE") || g.includes("FINE")) return "grade-badge-fine";
  if (g.includes("VG") || g.includes("VERY GOOD") || g.includes("GOOD")) return "grade-badge-good";
  if (g.includes("NGC")) return "grade-badge-ngc";
  if (g.includes("PCGS")) return "grade-badge-pcgs";
  
  return "grade-badge-poor";
}

// Format year display
function formatYear(start: number | null | undefined, end: number | null | undefined, isCirca?: boolean): string {
  if (!start && !end) return "";
  
  const prefix = isCirca ? "c. " : "";
  
  if (start && end && start !== end) {
    const startStr = start < 0 ? `${Math.abs(start)}` : `${start}`;
    const endStr = end < 0 ? `${Math.abs(end)} BC` : `${end} AD`;
    const startSuffix = start < 0 && end > 0 ? " BC" : "";
    return `${prefix}${startStr}${startSuffix}–${endStr}`;
  }
  
  const year = start || end;
  if (!year) return "";
  return `${prefix}${Math.abs(year)} ${year < 0 ? "BC" : "AD"}`;
}

export function CoinCard({ coin }: CoinCardProps) {
  const navigate = useNavigate();
  
  const yearDisplay = formatYear(coin.mint_year_start, coin.mint_year_end, coin.is_circa);
  const metalConfig = METAL_CONFIG[coin.metal?.toLowerCase()] || { symbol: "?", badge: "metal-badge-ae" };
  const categoryBorder = CATEGORY_BORDERS[coin.category?.toLowerCase()] || "category-border-other";
  const rarityDot = getRarityDotClass(coin.rarity);
  const gradeBadge = getGradeBadgeClass(coin.grade);

  return (
    <div 
      className={cn(
        "coin-card cursor-pointer",
        categoryBorder
      )}
      onClick={() => navigate(`/coins/${coin.id}`)}
    >
      {/* Image container */}
      <div className="aspect-[4/3] relative overflow-hidden" style={{ background: 'var(--bg-surface)' }}>
        {coin.primary_image ? (
          <img 
            src={`/api${coin.primary_image}`} 
            alt={`${coin.issuing_authority} ${coin.denomination}`}
            className="object-cover w-full h-full transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            {/* Coin silhouette placeholder */}
            <div 
              className="w-20 h-20 rounded-full opacity-10"
              style={{ background: `var(--metal-${metalConfig.symbol.toLowerCase() === 'au' ? 'au' : metalConfig.symbol.toLowerCase() === 'ag' ? 'ag' : 'ae'})` }}
            />
          </div>
        )}
        
        {/* Top badges row */}
        <div className="absolute top-2 right-2 flex items-center gap-1.5">
          {/* Metal badge - element style */}
          <div className={cn(
            "metal-badge w-7 h-7 text-[10px]",
            metalConfig.badge
          )}>
            {metalConfig.symbol}
          </div>
          
          {/* Rarity dot */}
          {rarityDot && (
            <div className={cn("rarity-dot", rarityDot)} />
          )}
          
          {/* Grade badge */}
          {coin.grade && (
            <div className={cn("grade-badge text-[10px] py-0.5 px-1.5", gradeBadge)}>
              {coin.grade}
            </div>
          )}
        </div>
        
        {/* Test cut indicator */}
        {coin.is_test_cut && (
          <div className="absolute bottom-2 left-2 flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium"
               style={{ background: 'rgba(255, 69, 58, 0.2)', color: '#FF453A' }}>
            <Scissors className="w-3 h-3" />
            TC
          </div>
        )}
      </div>
      
      {/* Content section */}
      <div className="p-3" style={{ background: 'var(--bg-card)' }}>
        {/* Ruler name */}
        <div className="font-semibold text-sm leading-tight truncate" style={{ color: 'var(--text-primary)' }}>
          {coin.issuing_authority}
        </div>
        
        {/* Denomination + Mint + Year */}
        <div className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-secondary)' }}>
          {coin.denomination}
          {coin.mint_name && ` · ${coin.mint_name}`}
          {yearDisplay && ` · ${yearDisplay}`}
        </div>
        
        {/* Footer: Price */}
        {coin.acquisition_price && (
          <div className="flex items-center justify-end mt-2 pt-2" style={{ borderTop: '1px solid var(--border-subtle)' }}>
            <span className="text-xs font-medium tabular-nums" style={{ color: 'var(--text-primary)' }}>
              ${Number(coin.acquisition_price).toLocaleString()}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
