/**
 * CoinCard - Main collection card component
 * 
 * Design spec: 280×380px card with:
 * - Category-colored left border (4px)
 * - Metal badge (element symbol style)
 * - Rarity dot + Grade badge
 * - Price trend with percentage
 * - Hover state with quick actions
 * 
 * @module coins/CoinCard
 */

import { useState } from 'react';
import { CoinListItem } from "@/types/coin";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import { Edit, Zap, Share2, Scissors } from "lucide-react";
import { 
  MetalBadge, 
  GradeBadge, 
  RarityIndicator, 
  PriceTrend,
  Sparkline,
  parseCategory,
  CATEGORY_CONFIG,
} from "@/components/design-system";

interface CoinCardProps {
  coin: CoinListItem;
}

// Format year display
function formatYear(
  start: number | null | undefined, 
  end: number | null | undefined, 
  isCirca?: boolean
): string {
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

// Mock price trend data (placeholder until real data available)
function getMockPriceTrend(coinId: number): number[] {
  // Generate deterministic "random" data based on coin ID
  const seed = coinId * 7919;
  return Array.from({ length: 12 }, (_, i) => {
    const base = 50 + (seed % 50);
    const noise = Math.sin(i * 0.8 + seed) * 15;
    return Math.round(base + noise + i * 2);
  });
}

// Mock price change (placeholder)
function getMockPriceChange(coinId: number): number {
  return ((coinId * 7) % 30) - 10; // -10% to +20%
}

export function CoinCard({ coin }: CoinCardProps) {
  const navigate = useNavigate();
  const [isHovered, setIsHovered] = useState(false);
  
  const yearDisplay = formatYear(coin.mint_year_start, coin.mint_year_end, coin.is_circa);
  const category = parseCategory(coin.category);
  const categoryConfig = CATEGORY_CONFIG[category];
  
  // Mock data for price trends (will be replaced with real data)
  const priceTrend = getMockPriceTrend(coin.id);
  const priceChange = getMockPriceChange(coin.id);
  
  return (
    <div 
      className={cn(
        "rounded-lg overflow-hidden cursor-pointer transition-all duration-200",
        "hover:shadow-lg"
      )}
      style={{ 
        background: 'var(--bg-card)',
        borderLeft: `4px solid var(--category-${categoryConfig.cssVar})`,
      }}
      onClick={() => navigate(`/coins/${coin.id}`)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Image container */}
      <div 
        className="aspect-[4/3] relative overflow-hidden"
        style={{ background: 'var(--bg-surface)' }}
      >
        {coin.primary_image ? (
          <img 
            src={`/api${coin.primary_image}`} 
            alt={`${coin.issuing_authority} ${coin.denomination}`}
            className={cn(
              "object-cover w-full h-full transition-transform duration-300",
              isHovered && "scale-105"
            )}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            {/* Coin silhouette placeholder */}
            <div 
              className="w-20 h-20 rounded-full opacity-10"
              style={{ background: 'var(--metal-ag)' }}
            />
          </div>
        )}
        
        {/* Top badges row: [Au] ●R2 [VF] */}
        <div className="absolute top-2 right-2 flex items-center gap-1.5">
          <MetalBadge metal={coin.metal} size="sm" showGlow={isHovered} />
          {coin.rarity && <RarityIndicator rarity={coin.rarity} variant="dot" />}
          {coin.grade && <GradeBadge grade={coin.grade} size="sm" />}
        </div>
        
        {/* Test cut indicator */}
        {coin.is_test_cut && (
          <div 
            className="absolute bottom-2 left-2 flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium"
            style={{ background: 'rgba(255, 69, 58, 0.2)', color: '#FF453A' }}
          >
            <Scissors className="w-3 h-3" />
            TC
          </div>
        )}
        
        {/* Hover actions overlay */}
        <div 
          className={cn(
            "absolute inset-0 flex items-end justify-center pb-3",
            "bg-gradient-to-t from-black/60 via-black/20 to-transparent",
            "transition-opacity duration-200",
            isHovered ? "opacity-100" : "opacity-0"
          )}
        >
          <div className="flex gap-2">
            <button
              className="p-2 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/coins/${coin.id}/edit`);
              }}
              title="Edit"
            >
              <Edit className="w-4 h-4 text-white" />
            </button>
            <button
              className="p-2 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                // TODO: Expand legend action
              }}
              title="Expand Legend"
            >
              <Zap className="w-4 h-4 text-white" />
            </button>
            <button
              className="p-2 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                // TODO: Share action
              }}
              title="Share"
            >
              <Share2 className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Content section */}
      <div className="p-3" style={{ background: 'var(--bg-card)' }}>
        {/* Ruler name */}
        <div 
          className="font-semibold text-sm leading-tight truncate"
          style={{ color: 'var(--text-primary)' }}
        >
          {coin.issuing_authority}
        </div>
        
        {/* Denomination + Mint + Year */}
        <div 
          className="text-xs mt-0.5 truncate"
          style={{ color: 'var(--text-secondary)' }}
        >
          {coin.denomination}
          {coin.mint_name && ` · ${coin.mint_name}`}
          {yearDisplay && ` · ${yearDisplay}`}
        </div>
        
        {/* Footer: Price trend + Sparkline */}
        <div 
          className="mt-2 pt-2 flex items-center justify-between"
          style={{ borderTop: '1px solid var(--border-subtle)' }}
        >
          {/* Price with trend */}
          <PriceTrend 
            currentPrice={coin.acquisition_price}
            changePercent={priceChange}
            size="xs"
          />
          
          {/* Mini sparkline */}
          <Sparkline 
            data={priceTrend} 
            width={10} 
            height="xs"
            trend={priceChange > 0 ? 'up' : priceChange < 0 ? 'down' : 'neutral'}
          />
        </div>
      </div>
    </div>
  );
}
