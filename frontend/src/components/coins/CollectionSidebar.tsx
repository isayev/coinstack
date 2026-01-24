/**
 * CollectionSidebar - Unified sidebar with stats, filters, and alerts
 * 
 * Design spec includes:
 * - Search with keyboard shortcut
 * - Collection stats with real data
 * - Metal chips with counts
 * - Category bars with distribution
 * - Grade bars with temperature colors
 * - Year range slider with histogram
 * - Alerts section (muted placeholders)
 * 
 * @module coins/CollectionSidebar
 */

import { useState } from 'react';
import { useFilterStore } from "@/stores/filterStore";
import { useUIStore } from "@/stores/uiStore";
import { useCollectionStats } from "@/hooks/useCoins";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { 
  Search, ChevronDown, ChevronRight, RotateCcw, Bell,
  Calendar, Scissors
} from "lucide-react";
import { cn } from "@/lib/utils";
import { 
  MetalChip,
  PlaceholderSparkline,
  MetalType,
  CATEGORY_CONFIG,
  CategoryType,
  GradeTier,
} from "@/components/design-system";

// ============================================================================
// GRADE CONFIGURATION (Temperature Scale)
// ============================================================================

interface GradeFilterConfig {
  tier: GradeTier;
  label: string;
  cssVar: string;
}

const GRADE_FILTER_CONFIG: GradeFilterConfig[] = [
  { tier: 'poor', label: 'Poor', cssVar: 'poor' },
  { tier: 'good', label: 'Good', cssVar: 'good' },
  { tier: 'fine', label: 'Fine', cssVar: 'fine' },
  { tier: 'ef', label: 'EF', cssVar: 'ef' },
  { tier: 'au', label: 'AU', cssVar: 'au' },
  { tier: 'ms', label: 'MS', cssVar: 'ms' },
  { tier: 'unknown', label: 'Unknown', cssVar: 'unknown' },
];

// ============================================================================
// STATS SECTION
// ============================================================================

interface CollectionStatsProps {
  totalCoins: number;
  totalValue: number;
  isLoading?: boolean;
}

function CollectionStats({ 
  totalCoins, 
  totalValue,
  isLoading = false,
}: CollectionStatsProps) {
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
          {isLoading ? '...' : `${totalCoins} coins`}
        </span>
      </div>
      
      {/* Value */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-lg font-bold tabular-nums" style={{ color: 'var(--text-primary)' }}>
            ${isLoading ? '...' : totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </span>
          {/* Muted placeholder for future market data */}
          <span 
            className="ml-1 text-xs opacity-30"
            style={{ color: 'var(--text-tertiary)' }}
            title="Market trends coming soon"
          >
            — MoM
          </span>
        </div>
        {/* Muted placeholder sparkline */}
        <PlaceholderSparkline width={10} height="sm" className="opacity-20" />
      </div>
      
      {/* Muted secondary stats placeholder */}
      <div 
        className="mt-2 pt-2 text-xs flex items-center gap-3 opacity-30"
        style={{ borderTop: '1px solid var(--border-subtle)', color: 'var(--text-tertiary)' }}
        title="Analytics coming soon"
      >
        <span>Avg: <strong>—</strong></span>
        <span>·</span>
        <span>Best ROI: <strong>—</strong></span>
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
  counts: Record<string, number>;
}

const DISPLAY_METALS: MetalType[] = ['gold', 'silver', 'ae', 'bronze', 'billon', 'copper', 'orichalcum', 'lead'];

function MetalFilter({ selected, onSelect, counts }: MetalFilterProps) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {DISPLAY_METALS.map((metal) => {
        const count = counts[metal] || 0;
        if (count === 0 && selected !== metal) return null; // Hide metals with no coins
        return (
          <MetalChip
            key={metal}
            metal={metal}
            count={count}
            selected={selected === metal}
            onClick={() => onSelect(selected === metal ? null : metal)}
          />
        );
      })}
    </div>
  );
}

// ============================================================================
// CATEGORY FILTER WITH DISTRIBUTION BARS
// ============================================================================

interface CategoryFilterProps {
  selected: string | null;
  onSelect: (category: string | null) => void;
  counts: Record<string, number>;
}

const DISPLAY_CATEGORIES: CategoryType[] = ['imperial', 'provincial', 'republic', 'greek', 'celtic', 'byzantine', 'late', 'judaea', 'eastern'];

function CategoryFilter({ selected, onSelect, counts }: CategoryFilterProps) {
  const maxCount = Math.max(...Object.values(counts), 1);
  
  // Filter to only show categories with coins
  const activeCategories = DISPLAY_CATEGORIES.filter(cat => counts[cat] > 0 || selected === cat);
  
  return (
    <div className="space-y-1.5">
      {activeCategories.map((cat) => {
        const config = CATEGORY_CONFIG[cat];
        const count = counts[cat] || 0;
        const barWidth = maxCount > 0 ? (count / maxCount) * 100 : 0;
        const isSelected = selected === cat;
        
        return (
          <button
            key={cat}
            onClick={() => onSelect(isSelected ? null : cat)}
            className={cn(
              "w-full flex items-center gap-2 py-1.5 px-2 rounded transition-all",
              isSelected && "ring-1"
            )}
            style={{
              background: isSelected ? `var(--category-${config.cssVar}-subtle)` : 'transparent',
            }}
          >
            {/* Color indicator */}
            <div 
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ 
                background: `var(--category-${config.cssVar})`,
                opacity: isSelected ? 1 : 0.7,
              }}
            />
            
            {/* Label */}
            <span 
              className="text-sm flex-1 text-left"
              style={{ color: isSelected ? `var(--category-${config.cssVar})` : 'var(--text-secondary)' }}
            >
              {config.label}
            </span>
            
            {/* Count */}
            <span 
              className="text-xs tabular-nums"
              style={{ color: 'var(--text-tertiary)' }}
            >
              {count}
            </span>
            
            {/* Distribution bar */}
            <div 
              className="w-16 h-1.5 rounded-full overflow-hidden flex-shrink-0"
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
      {activeCategories.length === 0 && (
        <p className="text-xs text-center py-2" style={{ color: 'var(--text-tertiary)' }}>
          No categories found
        </p>
      )}
    </div>
  );
}

// ============================================================================
// GRADE FILTER WITH TEMPERATURE BARS (Similar to Category)
// ============================================================================

interface GradeFilterProps {
  selected: string | null;
  onSelect: (grade: string | null) => void;
  counts: Record<string, number>;
}

function GradeFilter({ selected, onSelect, counts }: GradeFilterProps) {
  const maxCount = Math.max(...Object.values(counts), 1);
  
  // Filter to only show grades with coins
  const activeGrades = GRADE_FILTER_CONFIG.filter(g => counts[g.tier] > 0 || selected === g.tier);
  
  return (
    <div className="space-y-1.5">
      {activeGrades.map(({ tier, label, cssVar }) => {
        const count = counts[tier] || 0;
        const barWidth = maxCount > 0 ? (count / maxCount) * 100 : 0;
        const isSelected = selected === tier;
        
        return (
          <button
            key={tier}
            onClick={() => onSelect(isSelected ? null : tier)}
            className={cn(
              "w-full flex items-center gap-2 py-1.5 px-2 rounded transition-all",
              isSelected && "ring-1"
            )}
            style={{
              background: isSelected ? `var(--grade-${cssVar}-bg)` : 'transparent',
            }}
          >
            {/* Temperature color indicator */}
            <div 
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ 
                background: `var(--grade-${cssVar})`,
                opacity: isSelected ? 1 : 0.7,
              }}
            />
            
            {/* Label */}
            <span 
              className="text-sm flex-1 text-left"
              style={{ color: isSelected ? `var(--grade-${cssVar})` : 'var(--text-secondary)' }}
            >
              {label}
            </span>
            
            {/* Count */}
            <span 
              className="text-xs tabular-nums"
              style={{ color: 'var(--text-tertiary)' }}
            >
              {count}
            </span>
            
            {/* Distribution bar */}
            <div 
              className="w-16 h-1.5 rounded-full overflow-hidden flex-shrink-0"
              style={{ background: 'var(--bg-surface)' }}
            >
              <div 
                className="h-full rounded-full transition-all"
                style={{ 
                  width: `${barWidth}%`,
                  background: `var(--grade-${cssVar})`
                }}
              />
            </div>
          </button>
        );
      })}
      {activeGrades.length === 0 && (
        <p className="text-xs text-center py-2" style={{ color: 'var(--text-tertiary)' }}>
          No graded coins
        </p>
      )}
    </div>
  );
}

// ============================================================================
// RARITY FILTER
// ============================================================================

interface RarityFilterProps {
  selected: string | null;
  onSelect: (rarity: string | null) => void;
  counts: Record<string, number>;
}

const RARITY_OPTIONS = [
  { value: 'common', label: 'Common', code: 'C', cssVar: 'c' },
  { value: 'scarce', label: 'Scarce', code: 'S', cssVar: 's' },
  { value: 'rare', label: 'Rare', code: 'R1', cssVar: 'r1' },
  { value: 'very_rare', label: 'Very Rare', code: 'R2', cssVar: 'r2' },
  { value: 'extremely_rare', label: 'Extremely Rare', code: 'R3', cssVar: 'r3' },
  { value: 'unique', label: 'Unique', code: 'U', cssVar: 'u' },
];

function RarityFilter({ selected, onSelect, counts }: RarityFilterProps) {
  const maxCount = Math.max(...Object.values(counts), 1);
  
  // Filter to only show rarities with coins
  const activeRarities = RARITY_OPTIONS.filter(r => counts[r.value] > 0 || selected === r.value);
  
  return (
    <div className="space-y-1.5">
      {activeRarities.map(({ value, label, code, cssVar }) => {
        const count = counts[value] || 0;
        const barWidth = maxCount > 0 ? (count / maxCount) * 100 : 0;
        const isSelected = selected === value;
        
        return (
          <button
            key={value}
            onClick={() => onSelect(isSelected ? null : value)}
            className={cn(
              "w-full flex items-center gap-2 py-1.5 px-2 rounded transition-all",
              isSelected && "ring-1"
            )}
            style={{
              background: isSelected ? `var(--rarity-${cssVar}-bg)` : 'transparent',
            }}
          >
            {/* Rarity dot */}
            <div 
              className={cn("w-2 h-2 rounded-full flex-shrink-0", value === 'unique' && 'animate-pulse')}
              style={{ background: `var(--rarity-${cssVar})` }}
            />
            
            {/* Code + Label */}
            <span 
              className="text-sm flex-1 text-left"
              style={{ color: isSelected ? `var(--rarity-${cssVar})` : 'var(--text-secondary)' }}
            >
              <span className="font-semibold">{code}</span> {label}
            </span>
            
            {/* Count */}
            <span 
              className="text-xs tabular-nums"
              style={{ color: 'var(--text-tertiary)' }}
            >
              {count}
            </span>
            
            {/* Distribution bar */}
            <div 
              className="w-16 h-1.5 rounded-full overflow-hidden flex-shrink-0"
              style={{ background: 'var(--bg-surface)' }}
            >
              <div 
                className="h-full rounded-full transition-all"
                style={{ 
                  width: `${barWidth}%`,
                  background: `var(--rarity-${cssVar})`
                }}
              />
            </div>
          </button>
        );
      })}
      {activeRarities.length === 0 && (
        <p className="text-xs text-center py-2" style={{ color: 'var(--text-tertiary)' }}>
          No rarity data
        </p>
      )}
    </div>
  );
}

// ============================================================================
// ALERTS SECTION (Muted placeholder)
// ============================================================================

function AlertsSection() {
  return (
    <div 
      className="rounded-lg p-3 opacity-40"
      style={{ background: 'var(--bg-elevated)' }}
      title="Market alerts coming soon"
    >
      <div className="flex items-center gap-2 mb-2">
        <Bell className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
        <span className="text-sm font-medium" style={{ color: 'var(--text-tertiary)' }}>
          Alerts
        </span>
        <span 
          className="text-[10px] px-1.5 py-0.5 rounded"
          style={{ background: 'var(--bg-surface)', color: 'var(--text-tertiary)' }}
        >
          Soon
        </span>
      </div>
      
      <div className="space-y-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
        <div className="flex items-start gap-2">
          <span>•</span>
          <span>Price alerts for watched coins</span>
        </div>
        <div className="flex items-start gap-2">
          <span>•</span>
          <span>New auction comparables</span>
        </div>
        <div className="flex items-start gap-2">
          <span>•</span>
          <span>Die match notifications</span>
        </div>
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

export function CollectionSidebar({ totalCoins: propTotalCoins }: CollectionSidebarProps) {
  const filters = useFilterStore();
  const { setCommandPaletteOpen } = useUIStore();
  const { data: stats, isLoading: statsLoading } = useCollectionStats();
  const activeFilterCount = filters.getActiveFilterCount();
  
  // Use real stats data
  const totalCoins = stats?.total_coins ?? propTotalCoins ?? 0;
  const totalValue = stats?.total_value ?? 0;
  const metalCounts = stats?.metal_counts ?? {};
  const categoryCounts = stats?.category_counts ?? {};
  const gradeCounts = stats?.grade_counts ?? {};
  const rarityCounts = stats?.rarity_counts ?? {};
  const yearRange = stats?.year_range ?? { min: null, max: null };
  const yearDistribution = stats?.year_distribution ?? [];
  
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
        <CollectionStats 
          totalCoins={totalCoins} 
          totalValue={totalValue}
          isLoading={statsLoading}
        />
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
            counts={metalCounts}
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
            counts={categoryCounts}
          />
        </FilterSection>
        
        {/* Grade - NEW temperature-scale design */}
        <FilterSection 
          title="Grade"
          onClear={filters.grade ? () => filters.setGrade(null) : undefined}
        >
          <GradeFilter 
            selected={filters.grade}
            onSelect={(g) => filters.setGrade(g)}
            counts={gradeCounts}
          />
        </FilterSection>
        
        {/* Rarity */}
        <FilterSection 
          title="Rarity"
          defaultOpen={false}
          onClear={filters.rarity ? () => filters.setRarity(null) : undefined}
        >
          <RarityFilter 
            selected={filters.rarity}
            onSelect={(r) => filters.setRarity(r)}
            counts={rarityCounts}
          />
        </FilterSection>
        
        {/* Year Range */}
        <FilterSection 
          title="Year Range"
          defaultOpen={false}
          badge={(filters.mint_year_gte !== null || filters.mint_year_lte !== null) && (
            <Calendar className="w-3.5 h-3.5" style={{ color: 'var(--metal-au)' }} />
          )}
        >
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-xs block mb-1" style={{ color: 'var(--text-tertiary)' }}>
                  From {yearRange.min !== null && `(${yearRange.min < 0 ? Math.abs(yearRange.min) + ' BC' : yearRange.min + ' AD'})`}
                </span>
                <Input
                  type="number"
                  placeholder={yearRange.min !== null ? String(yearRange.min) : "-44"}
                  value={filters.mint_year_gte ?? ""}
                  onChange={(e) => filters.setMintYearGte(e.target.value ? parseInt(e.target.value) : null)}
                  className="h-8 text-sm"
                  style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
                />
              </div>
              <div>
                <span className="text-xs block mb-1" style={{ color: 'var(--text-tertiary)' }}>
                  To {yearRange.max !== null && `(${yearRange.max < 0 ? Math.abs(yearRange.max) + ' BC' : yearRange.max + ' AD'})`}
                </span>
                <Input
                  type="number"
                  placeholder={yearRange.max !== null ? String(yearRange.max) : "476"}
                  value={filters.mint_year_lte ?? ""}
                  onChange={(e) => filters.setMintYearLte(e.target.value ? parseInt(e.target.value) : null)}
                  className="h-8 text-sm"
                  style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
                />
              </div>
            </div>
            
            {/* Year distribution histogram */}
            {yearDistribution.length > 0 ? (
              <div className="mt-3">
                <div className="flex items-end gap-0.5 h-12">
                  {yearDistribution.map((bucket, idx) => {
                    const maxCount = Math.max(...yearDistribution.map(b => b.count));
                    const height = maxCount > 0 ? (bucket.count / maxCount) * 100 : 0;
                    const isBc = bucket.start < 0;
                    
                    return (
                      <div 
                        key={idx}
                        className="flex-1 rounded-t transition-all hover:opacity-80 cursor-pointer"
                        style={{ 
                          height: `${Math.max(height, 4)}%`,
                          background: isBc ? 'var(--category-republic)' : 'var(--category-imperial)',
                          minWidth: '8px',
                        }}
                        title={`${bucket.label}: ${bucket.count} coins`}
                        onClick={() => {
                          filters.setMintYearGte(bucket.start);
                          filters.setMintYearLte(bucket.end);
                        }}
                      />
                    );
                  })}
                </div>
                <div className="flex justify-between mt-1 text-[9px]" style={{ color: 'var(--text-tertiary)' }}>
                  <span>{yearDistribution[0]?.label.split('-')[0] || ''}</span>
                  <span>{yearDistribution[yearDistribution.length - 1]?.label.split(' ')[0].split('-')[1] || ''} AD</span>
                </div>
                <p className="text-[10px] text-center mt-1" style={{ color: 'var(--text-tertiary)' }}>
                  Click bar to filter by period
                </p>
              </div>
            ) : (
              <div className="flex items-center justify-center py-2 opacity-30">
                <PlaceholderSparkline width={20} height="sm" />
              </div>
            )}
            <p className="text-[10px] text-center mt-1" style={{ color: 'var(--text-tertiary)' }}>
              Negative = BC, Positive = AD
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
      
      {/* Alerts (muted placeholder) */}
      <div className="p-3" style={{ borderTop: '1px solid var(--border-subtle)' }}>
        <AlertsSection />
      </div>
    </div>
  );
}
