/**
 * CollectionSidebar - Unified sidebar with stats, filters, and alerts
 * 
 * Design spec includes:
 * - Search with keyboard shortcut
 * - Collection stats with sparklines
 * - Metal chips with counts
 * - Category bars with distribution
 * - Year range slider with histogram
 * - Alerts section
 * 
 * @module coins/CollectionSidebar
 */

import { useState } from 'react';
import { useFilterStore } from "@/stores/filterStore";
import { useUIStore } from "@/stores/uiStore";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { 
  Search, ChevronDown, ChevronRight, RotateCcw, Bell, X,
  Calendar, Scissors
} from "lucide-react";
import { cn } from "@/lib/utils";
import { 
  MetalChip,
  Sparkline,
  PlaceholderSparkline,
  MetalType,
  CATEGORY_CONFIG,
  CategoryType,
} from "@/components/design-system";

// ============================================================================
// STATS SECTION
// ============================================================================

interface CollectionStatsProps {
  totalCoins: number;
  totalValue?: number;
  valueChange?: number;
  avgGrade?: string;
  bestRoi?: { coin: string; percent: number };
}

function CollectionStats({ 
  totalCoins, 
  totalValue = 28450, // Placeholder
  valueChange = 12,   // Placeholder
  avgGrade = "VF",    // Placeholder
  bestRoi = { coin: "Nero denarius", percent: 42 } // Placeholder
}: CollectionStatsProps) {
  // Mock sparkline data
  const valueHistory = [20, 22, 21, 25, 24, 28, 26, 30, 28, 32, 30, 34];
  
  return (
    <div 
      className="rounded-lg p-3"
      style={{ background: 'var(--bg-elevated)' }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          📊 Collection
        </span>
        <span className="text-xs tabular-nums" style={{ color: 'var(--text-secondary)' }}>
          {totalCoins} coins
        </span>
      </div>
      
      {/* Value with sparkline */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-lg font-bold tabular-nums" style={{ color: 'var(--text-primary)' }}>
            ${totalValue.toLocaleString()}
          </span>
          <span 
            className="ml-1 text-xs"
            style={{ color: valueChange > 0 ? 'var(--price-up)' : 'var(--price-down)' }}
          >
            {valueChange > 0 ? '+' : ''}{valueChange}% MoM
          </span>
        </div>
        <Sparkline 
          data={valueHistory} 
          width={10} 
          height="sm" 
          trend={valueChange > 0 ? 'up' : 'down'}
        />
      </div>
      
      {/* Secondary stats */}
      <div 
        className="mt-2 pt-2 text-xs flex items-center gap-3"
        style={{ borderTop: '1px solid var(--border-subtle)', color: 'var(--text-tertiary)' }}
      >
        <span>Avg: <strong style={{ color: 'var(--grade-fine)' }}>{avgGrade}</strong></span>
        <span>·</span>
        <span>
          Best ROI: <strong style={{ color: 'var(--price-up)' }}>+{bestRoi.percent}%</strong> ({bestRoi.coin})
        </span>
      </div>
    </div>
  );
}

// ============================================================================
// FILTER SECTIONS
// ============================================================================

interface FilterSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  badge?: React.ReactNode;
  onClear?: () => void;
}

function FilterSection({ 
  title, 
  children, 
  defaultOpen = true,
  badge,
  onClear
}: FilterSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div style={{ borderBottom: '1px solid var(--border-subtle)' }} className="pb-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full py-2 text-sm font-medium transition-colors"
        style={{ color: 'var(--text-primary)' }}
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
          ) : (
            <ChevronRight className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
          )}
          <span>{title}</span>
        </div>
        <div className="flex items-center gap-2">
          {badge}
          {onClear && (
            <button
              onClick={(e) => { e.stopPropagation(); onClear(); }}
              className="text-xs hover:opacity-80"
              style={{ color: 'var(--text-tertiary)' }}
            >
              Clear
            </button>
          )}
        </div>
      </button>
      {isOpen && <div className="pt-2 space-y-3">{children}</div>}
    </div>
  );
}

// ============================================================================
// METAL FILTER
// ============================================================================

interface MetalFilterProps {
  selected: string | null;
  onSelect: (metal: string | null) => void;
  counts?: Record<string, number>;
}

const DISPLAY_METALS: MetalType[] = ['gold', 'silver', 'ae', 'bronze', 'billon', 'copper', 'orichalcum', 'lead'];

function MetalFilter({ selected, onSelect, counts = {} }: MetalFilterProps) {
  // Mock counts if not provided
  const mockCounts: Record<string, number> = {
    gold: 12, silver: 45, ae: 48, bronze: 15, billon: 5, copper: 3, orichalcum: 2, lead: 1
  };
  const displayCounts = Object.keys(counts).length > 0 ? counts : mockCounts;
  
  return (
    <div className="flex flex-wrap gap-1.5">
      {DISPLAY_METALS.map((metal) => (
        <MetalChip
          key={metal}
          metal={metal}
          count={displayCounts[metal]}
          selected={selected === metal}
          onClick={() => onSelect(selected === metal ? null : metal)}
        />
      ))}
    </div>
  );
}

// ============================================================================
// CATEGORY FILTER WITH DISTRIBUTION BARS
// ============================================================================

interface CategoryFilterProps {
  selected: string | null;
  onSelect: (category: string | null) => void;
  counts?: Record<string, number>;
}

const DISPLAY_CATEGORIES: CategoryType[] = ['imperial', 'provincial', 'republic', 'greek', 'celtic', 'byzantine'];

function CategoryFilter({ selected, onSelect, counts = {} }: CategoryFilterProps) {
  // Mock counts
  const mockCounts: Record<string, number> = {
    imperial: 67, provincial: 28, republic: 12, greek: 8, celtic: 3, byzantine: 2
  };
  const displayCounts = Object.keys(counts).length > 0 ? counts : mockCounts;
  const maxCount = Math.max(...Object.values(displayCounts));
  
  return (
    <div className="space-y-2">
      {DISPLAY_CATEGORIES.map((cat) => {
        const config = CATEGORY_CONFIG[cat];
        const count = displayCounts[cat] || 0;
        const barWidth = maxCount > 0 ? (count / maxCount) * 100 : 0;
        const isSelected = selected === cat;
        
        return (
          <button
            key={cat}
            onClick={() => onSelect(isSelected ? null : cat)}
            className={cn(
              "w-full flex items-center gap-2 py-1 px-2 rounded transition-colors",
              isSelected && "ring-1"
            )}
            style={{
              background: isSelected ? `var(--category-${config.cssVar}-subtle)` : 'transparent',
            }}
          >
            {/* Checkbox-like indicator */}
            <div 
              className="w-4 h-4 rounded-full flex items-center justify-center"
              style={{ 
                background: isSelected ? `var(--category-${config.cssVar})` : 'var(--bg-surface)',
                border: `2px solid var(--category-${config.cssVar})`
              }}
            >
              {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
            </div>
            
            {/* Label and count */}
            <span className="text-sm flex-1 text-left" style={{ color: 'var(--text-secondary)' }}>
              {config.label}
            </span>
            <span className="text-xs tabular-nums" style={{ color: 'var(--text-tertiary)' }}>
              ({count})
            </span>
            
            {/* Distribution bar */}
            <div 
              className="w-20 h-1.5 rounded-full overflow-hidden"
              style={{ background: 'var(--bg-surface)' }}
            >
              <div 
                className="h-full rounded-full transition-all"
                style={{ 
                  width: `${barWidth}%`,
                  background: `var(--category-${config.cssVar})`
                }}
              />
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ============================================================================
// ALERTS SECTION
// ============================================================================

interface Alert {
  id: string;
  type: 'price' | 'comp' | 'match';
  message: string;
  highlight?: string;
}

function AlertsSection() {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  
  // Mock alerts (placeholder)
  const alerts: Alert[] = [
    { id: '1', type: 'comp', message: 'New comp: RIC I 207 sold', highlight: '$420 (+15%)' },
    { id: '2', type: 'price', message: 'Price drop: Nero denarius', highlight: '-8%' },
    { id: '3', type: 'match', message: 'Die match found:', highlight: 'RIC III 61' },
  ];
  
  const visibleAlerts = alerts.filter(a => !dismissed.has(a.id));
  
  if (visibleAlerts.length === 0) return null;
  
  return (
    <div 
      className="rounded-lg p-3"
      style={{ background: 'var(--bg-elevated)' }}
    >
      <div className="flex items-center gap-2 mb-2">
        <Bell className="w-4 h-4" style={{ color: 'var(--metal-au)' }} />
        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
          Alerts
        </span>
        <span 
          className="text-[10px] px-1.5 py-0.5 rounded"
          style={{ background: 'var(--metal-au-subtle)', color: 'var(--metal-au-text)' }}
        >
          {visibleAlerts.length}
        </span>
      </div>
      
      <div className="space-y-2">
        {visibleAlerts.map((alert) => (
          <div 
            key={alert.id}
            className="flex items-start gap-2 text-xs"
            style={{ color: 'var(--text-secondary)' }}
          >
            <span>•</span>
            <span className="flex-1">
              {alert.message}{' '}
              <span 
                className="font-semibold"
                style={{ 
                  color: alert.type === 'price' && alert.highlight?.includes('-') 
                    ? 'var(--price-down)' 
                    : 'var(--price-up)' 
                }}
              >
                {alert.highlight}
              </span>
            </span>
            <button
              onClick={() => setDismissed(prev => new Set([...prev, alert.id]))}
              className="opacity-50 hover:opacity-100"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// MAIN SIDEBAR COMPONENT
// ============================================================================

interface CollectionSidebarProps {
  totalCoins?: number;
}

export function CollectionSidebar({ totalCoins = 0 }: CollectionSidebarProps) {
  const filters = useFilterStore();
  const { setCommandPaletteOpen } = useUIStore();
  const activeFilterCount = filters.getActiveFilterCount();
  
  return (
    <div 
      className="w-72 flex flex-col h-full"
      style={{ 
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)'
      }}
    >
      {/* Search */}
      <div className="p-3" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors"
          style={{ 
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-tertiary)'
          }}
        >
          <Search className="w-4 h-4" />
          <span className="flex-1 text-left">Search coins...</span>
          <kbd 
            className="text-[10px] px-1.5 py-0.5 rounded"
            style={{ background: 'var(--bg-elevated)' }}
          >
            ⌘K
          </kbd>
        </button>
      </div>
      
      {/* Stats */}
      <div className="p-3" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
        <CollectionStats totalCoins={totalCoins} />
      </div>
      
      {/* Filters header */}
      <div 
        className="px-3 py-2 flex items-center justify-between"
        style={{ borderBottom: '1px solid var(--border-subtle)' }}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
            Filters
          </span>
          {activeFilterCount > 0 && (
            <span 
              className="text-[10px] px-1.5 py-0.5 rounded font-medium"
              style={{ 
                background: 'var(--metal-au-subtle)', 
                color: 'var(--metal-au-text)' 
              }}
            >
              {activeFilterCount}
            </span>
          )}
        </div>
        {activeFilterCount > 0 && (
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={filters.reset}
            className="h-7 px-2 text-xs"
            style={{ color: 'var(--text-tertiary)' }}
          >
            <RotateCcw className="w-3 h-3 mr-1" />
            Reset
          </Button>
        )}
      </div>
      
      {/* Filter sections */}
      <div className="flex-1 overflow-auto p-3 space-y-1 scrollbar-thin">
        {/* Metal */}
        <FilterSection 
          title="Metal"
          onClear={filters.metal ? () => filters.setMetal(null) : undefined}
        >
          <MetalFilter 
            selected={filters.metal}
            onSelect={(m) => filters.setMetal(m)}
          />
        </FilterSection>
        
        {/* Category */}
        <FilterSection 
          title="Category"
          onClear={filters.category ? () => filters.setCategory(null) : undefined}
        >
          <CategoryFilter 
            selected={filters.category}
            onSelect={(c) => filters.setCategory(c)}
          />
        </FilterSection>
        
        {/* Year Range */}
        <FilterSection 
          title="Year Range"
          badge={(filters.mint_year_gte !== null || filters.mint_year_lte !== null) && (
            <Calendar className="w-3.5 h-3.5" style={{ color: 'var(--metal-au)' }} />
          )}
        >
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-xs block mb-1" style={{ color: 'var(--text-tertiary)' }}>From</span>
                <Input
                  type="number"
                  placeholder="-44 BC"
                  value={filters.mint_year_gte ?? ""}
                  onChange={(e) => filters.setMintYearGte(e.target.value ? parseInt(e.target.value) : null)}
                  className="h-8 text-sm"
                  style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
                />
              </div>
              <div>
                <span className="text-xs block mb-1" style={{ color: 'var(--text-tertiary)' }}>To</span>
                <Input
                  type="number"
                  placeholder="476 AD"
                  value={filters.mint_year_lte ?? ""}
                  onChange={(e) => filters.setMintYearLte(e.target.value ? parseInt(e.target.value) : null)}
                  className="h-8 text-sm"
                  style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
                />
              </div>
            </div>
            
            {/* Year distribution histogram (placeholder) */}
            <div className="flex items-center justify-center py-2">
              <PlaceholderSparkline width={20} height="sm" />
            </div>
            <p className="text-[10px] text-center" style={{ color: 'var(--text-tertiary)' }}>
              Use negative numbers for BC dates
            </p>
          </div>
        </FilterSection>
        
        {/* Ruler */}
        <FilterSection title="Ruler" defaultOpen={false}>
          <Input
            placeholder="Search rulers..."
            value={filters.issuing_authority || ""}
            onChange={(e) => filters.setIssuingAuthority(e.target.value || null)}
            className="h-8 text-sm"
            style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
          />
        </FilterSection>
        
        {/* Mint */}
        <FilterSection title="Mint" defaultOpen={false}>
          <Input
            placeholder="Search mints..."
            value={filters.mint_name || ""}
            onChange={(e) => filters.setMintName(e.target.value || null)}
            className="h-8 text-sm"
            style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
          />
        </FilterSection>
        
        {/* Grade */}
        <FilterSection title="Grade" defaultOpen={false}>
          <Input
            placeholder="VF, EF, MS..."
            value={filters.grade || ""}
            onChange={(e) => filters.setGrade(e.target.value || null)}
            className="h-8 text-sm"
            style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
          />
        </FilterSection>
        
        {/* Rarity */}
        <FilterSection title="Rarity" defaultOpen={false}>
          <Select 
            value={filters.rarity || "all"} 
            onValueChange={(v) => filters.setRarity(v === "all" ? null : v)}
          >
            <SelectTrigger 
              className="h-8 text-sm"
              style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
            >
              <SelectValue placeholder="Any rarity" />
            </SelectTrigger>
            <SelectContent style={{ background: 'var(--bg-card)' }}>
              <SelectItem value="all">Any Rarity</SelectItem>
              <SelectItem value="common">C - Common</SelectItem>
              <SelectItem value="scarce">S - Scarce</SelectItem>
              <SelectItem value="rare">R1 - Rare</SelectItem>
              <SelectItem value="very_rare">R2 - Very Rare</SelectItem>
              <SelectItem value="extremely_rare">R3 - Extremely Rare</SelectItem>
              <SelectItem value="unique">U - Unique</SelectItem>
            </SelectContent>
          </Select>
        </FilterSection>
        
        {/* Attributes */}
        <FilterSection title="Attributes" defaultOpen={false}>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => filters.setIsCirca(filters.is_circa === true ? null : true)}
              className={cn("px-2 py-1 rounded text-xs transition-colors")}
              style={{
                background: filters.is_circa === true ? 'var(--grade-fine-bg)' : 'var(--bg-card)',
                color: filters.is_circa === true ? 'var(--grade-fine)' : 'var(--text-tertiary)',
                border: `1px solid ${filters.is_circa === true ? 'var(--grade-fine)' : 'var(--border-subtle)'}`
              }}
            >
              <Calendar className="w-3 h-3 inline mr-1" />
              Circa
            </button>
            <button
              onClick={() => filters.setIsTestCut(filters.is_test_cut === true ? null : true)}
              className={cn("px-2 py-1 rounded text-xs transition-colors")}
              style={{
                background: filters.is_test_cut === true ? 'var(--rarity-r3-bg)' : 'var(--bg-card)',
                color: filters.is_test_cut === true ? 'var(--rarity-r3)' : 'var(--text-tertiary)',
                border: `1px solid ${filters.is_test_cut === true ? 'var(--rarity-r3)' : 'var(--border-subtle)'}`
              }}
            >
              <Scissors className="w-3 h-3 inline mr-1" />
              Test Cut
            </button>
          </div>
        </FilterSection>
      </div>
      
      {/* Alerts */}
      <div className="p-3" style={{ borderTop: '1px solid var(--border-subtle)' }}>
        <AlertsSection />
      </div>
    </div>
  );
}
