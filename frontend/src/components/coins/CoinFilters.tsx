import { useState } from "react";
import { useFilterStore } from "@/stores/filterStore";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { 
  ChevronDown, ChevronRight, Filter, RotateCcw,
  Calendar, MapPin, Sparkles, Scissors
} from "lucide-react";
import { cn } from "@/lib/utils";

// All category options from expanded enum
const CATEGORIES = [
  { value: "greek", label: "Greek" },
  { value: "celtic", label: "Celtic" },
  { value: "republic", label: "Republic" },
  { value: "imperial", label: "Imperial" },
  { value: "provincial", label: "Provincial" },
  { value: "judaean", label: "Judaean" },
  { value: "byzantine", label: "Byzantine" },
  { value: "migration", label: "Migration" },
  { value: "pseudo_roman", label: "Pseudo-Roman" },
  { value: "other", label: "Other" },
];

// Metal options with element symbols and badge classes
const METALS = [
  { value: "gold", symbol: "Au", label: "Gold", badge: "metal-badge-au" },
  { value: "electrum", symbol: "EL", label: "Electrum", badge: "metal-badge-el" },
  { value: "silver", symbol: "Ag", label: "Silver", badge: "metal-badge-ag" },
  { value: "orichalcum", symbol: "Or", label: "Orichalcum", badge: "metal-badge-or" },
  { value: "bronze", symbol: "Cu", label: "Bronze", badge: "metal-badge-cu" },
  { value: "ae", symbol: "Æ", label: "AE", badge: "metal-badge-ae" },
  { value: "billon", symbol: "Bi", label: "Billon", badge: "metal-badge-bi" },
  { value: "copper", symbol: "Cu", label: "Copper", badge: "metal-badge-copper" },
  { value: "potin", symbol: "Po", label: "Potin", badge: "metal-badge-po" },
  { value: "lead", symbol: "Pb", label: "Lead", badge: "metal-badge-pb" },
];

// Rarity options (standard numismatic: C→S→R1→R2→R3→U)
const RARITIES = [
  { value: "common", code: "C", label: "Common" },
  { value: "scarce", code: "S", label: "Scarce" },
  { value: "rare", code: "R1", label: "Rare" },
  { value: "very_rare", code: "R2", label: "Very Rare" },
  { value: "extremely_rare", code: "R3", label: "Extremely Rare" },
  { value: "unique", code: "U", label: "Unique" },
];

// Storage locations
const STORAGE_LOCATIONS = [
  { value: "SlabBox1", label: "Slab Box 1" },
  { value: "Velv1", label: "Velvet Tray 1" },
  { value: "Velv2", label: "Velvet Tray 2" },
  { value: "Velv3", label: "Velvet Tray 3" },
];

// Collapsible section component
function FilterSection({ 
  title, 
  children, 
  defaultOpen = true,
  badge
}: { 
  title: string; 
  children: React.ReactNode;
  defaultOpen?: boolean;
  badge?: React.ReactNode;
}) {
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
        {badge}
      </button>
      {isOpen && <div className="pt-2 space-y-3">{children}</div>}
    </div>
  );
}

export function CoinFilters() {
  const filters = useFilterStore();
  const activeFilterCount = filters.getActiveFilterCount();
  
  const selectedMetal = METALS.find(m => m.value === filters.metal);
  
  return (
    <div 
      className="w-72 flex flex-col h-full"
      style={{ 
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)'
      }}
    >
      {/* Header */}
      <div 
        className="p-4 sticky top-0 z-10"
        style={{ 
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)'
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
            <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Filters</h3>
            {activeFilterCount > 0 && (
              <span 
                className="h-5 px-1.5 text-xs rounded flex items-center justify-center font-medium"
                style={{ 
                  background: 'var(--metal-au-subtle)', 
                  color: 'var(--metal-au-text)',
                  border: '1px solid var(--metal-au-border)'
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
              className="h-8 px-2"
              style={{ color: 'var(--text-tertiary)' }}
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" />
              Reset
            </Button>
          )}
        </div>
      </div>
      
      {/* Filter sections */}
      <div className="flex-1 overflow-auto p-4 space-y-1 scrollbar-thin">
        {/* Category */}
        <FilterSection title="Category">
          <Select 
            value={filters.category || "all"} 
            onValueChange={(v) => filters.setCategory(v === "all" ? null : v)}
          >
            <SelectTrigger 
              className="h-9"
              style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
            >
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}>
              <SelectItem value="all">All Categories</SelectItem>
              {CATEGORIES.map((cat) => (
                <SelectItem key={cat.value} value={cat.value}>
                  {cat.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FilterSection>
        
        {/* Metal - Element chips */}
        <FilterSection 
          title="Metal"
          badge={selectedMetal && (
            <span 
              className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold"
              style={{ 
                background: `var(--metal-${selectedMetal.value === 'gold' ? 'au' : selectedMetal.value === 'silver' ? 'ag' : selectedMetal.value}-subtle)`,
                color: `var(--metal-${selectedMetal.value === 'gold' ? 'au' : selectedMetal.value === 'silver' ? 'ag' : selectedMetal.value}-text)`,
                border: `1px solid var(--metal-${selectedMetal.value === 'gold' ? 'au' : selectedMetal.value === 'silver' ? 'ag' : selectedMetal.value}-border)`
              }}
            >
              {selectedMetal.symbol}
            </span>
          )}
        >
          <div className="flex flex-wrap gap-1.5">
            {METALS.map((metal) => (
              <button
                key={metal.value}
                onClick={() => filters.setMetal(filters.metal === metal.value ? null : metal.value)}
                className={cn(
                  "metal-badge w-8 h-8 text-xs transition-all",
                  metal.badge,
                  filters.metal === metal.value && "ring-2 ring-[var(--metal-au)] ring-offset-1 ring-offset-[var(--bg-surface)]"
                )}
                title={metal.label}
              >
                {metal.symbol}
              </button>
            ))}
          </div>
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
                  onChange={(e) => {
                    const val = e.target.value;
                    filters.setMintYearGte(val ? parseInt(val) : null);
                  }}
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
                  onChange={(e) => {
                    const val = e.target.value;
                    filters.setMintYearLte(val ? parseInt(val) : null);
                  }}
                  className="h-8 text-sm"
                  style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
                />
              </div>
            </div>
            <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
              Use negative numbers for BC dates
            </p>
          </div>
        </FilterSection>
        
        {/* Ruler / Authority */}
        <FilterSection 
          title="Ruler"
          defaultOpen={false}
        >
          <Input
            placeholder="Search rulers..."
            value={filters.issuing_authority || ""}
            onChange={(e) => filters.setIssuingAuthority(e.target.value || null)}
            className="h-9"
            style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
          />
        </FilterSection>
        
        {/* Mint */}
        <FilterSection 
          title="Mint" 
          badge={filters.mint_name && (
            <MapPin className="w-3.5 h-3.5" style={{ color: 'var(--metal-au)' }} />
          )}
          defaultOpen={false}
        >
          <Input
            placeholder="Search mints..."
            value={filters.mint_name || ""}
            onChange={(e) => filters.setMintName(e.target.value || null)}
            className="h-9"
            style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
          />
        </FilterSection>
        
        {/* Rarity */}
        <FilterSection 
          title="Rarity"
          defaultOpen={false}
        >
          <Select 
            value={filters.rarity || "all"} 
            onValueChange={(v) => filters.setRarity(v === "all" ? null : v)}
          >
            <SelectTrigger 
              className="h-9"
              style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
            >
              <SelectValue placeholder="Any rarity" />
            </SelectTrigger>
            <SelectContent style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}>
              <SelectItem value="all">Any Rarity</SelectItem>
              {RARITIES.map((r) => (
                <SelectItem key={r.value} value={r.value}>
                  <span className="flex items-center gap-2">
                    <span className="font-mono text-xs">{r.code}</span>
                    <span>{r.label}</span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FilterSection>
        
        {/* Grade */}
        <FilterSection 
          title="Grade"
          defaultOpen={false}
        >
          <Input
            placeholder="VF, EF, MS..."
            value={filters.grade || ""}
            onChange={(e) => filters.setGrade(e.target.value || null)}
            className="h-9"
            style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
          />
        </FilterSection>
        
        {/* Storage Location */}
        <FilterSection 
          title="Storage"
          defaultOpen={false}
        >
          <Select 
            value={filters.storage_location || "all"} 
            onValueChange={(v) => filters.setStorageLocation(v === "all" ? null : v)}
          >
            <SelectTrigger 
              className="h-9"
              style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}
            >
              <SelectValue placeholder="All locations" />
            </SelectTrigger>
            <SelectContent style={{ background: 'var(--bg-card)', borderColor: 'var(--border-subtle)' }}>
              <SelectItem value="all">All Locations</SelectItem>
              {STORAGE_LOCATIONS.map((loc) => (
                <SelectItem key={loc.value} value={loc.value}>
                  {loc.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FilterSection>
        
        {/* Special Attributes */}
        <FilterSection 
          title="Attributes"
          badge={(filters.is_circa !== null || filters.is_test_cut !== null) && (
            <Sparkles className="w-3.5 h-3.5" style={{ color: 'var(--metal-au)' }} />
          )}
          defaultOpen={false}
        >
          <div className="space-y-3">
            {/* Is Circa */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
                <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Circa Dating</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  className={cn(
                    "h-6 px-2 text-xs rounded transition-colors",
                    filters.is_circa === true ? "font-medium" : ""
                  )}
                  style={{
                    background: filters.is_circa === true ? 'var(--grade-fine-bg)' : 'var(--bg-card)',
                    color: filters.is_circa === true ? 'var(--grade-fine)' : 'var(--text-tertiary)',
                    border: `1px solid ${filters.is_circa === true ? 'var(--grade-fine)' : 'var(--border-subtle)'}`
                  }}
                  onClick={() => filters.setIsCirca(filters.is_circa === true ? null : true)}
                >
                  Yes
                </button>
                <button
                  className={cn(
                    "h-6 px-2 text-xs rounded transition-colors",
                    filters.is_circa === false ? "font-medium" : ""
                  )}
                  style={{
                    background: filters.is_circa === false ? 'var(--rarity-r3-bg)' : 'var(--bg-card)',
                    color: filters.is_circa === false ? 'var(--rarity-r3)' : 'var(--text-tertiary)',
                    border: `1px solid ${filters.is_circa === false ? 'var(--rarity-r3)' : 'var(--border-subtle)'}`
                  }}
                  onClick={() => filters.setIsCirca(filters.is_circa === false ? null : false)}
                >
                  No
                </button>
              </div>
            </div>
            
            {/* Is Test Cut */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scissors className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
                <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Test Cut</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  className={cn(
                    "h-6 px-2 text-xs rounded transition-colors",
                    filters.is_test_cut === true ? "font-medium" : ""
                  )}
                  style={{
                    background: filters.is_test_cut === true ? 'var(--grade-fine-bg)' : 'var(--bg-card)',
                    color: filters.is_test_cut === true ? 'var(--grade-fine)' : 'var(--text-tertiary)',
                    border: `1px solid ${filters.is_test_cut === true ? 'var(--grade-fine)' : 'var(--border-subtle)'}`
                  }}
                  onClick={() => filters.setIsTestCut(filters.is_test_cut === true ? null : true)}
                >
                  Yes
                </button>
                <button
                  className={cn(
                    "h-6 px-2 text-xs rounded transition-colors",
                    filters.is_test_cut === false ? "font-medium" : ""
                  )}
                  style={{
                    background: filters.is_test_cut === false ? 'var(--rarity-r3-bg)' : 'var(--bg-card)',
                    color: filters.is_test_cut === false ? 'var(--rarity-r3)' : 'var(--text-tertiary)',
                    border: `1px solid ${filters.is_test_cut === false ? 'var(--rarity-r3)' : 'var(--border-subtle)'}`
                  }}
                  onClick={() => filters.setIsTestCut(filters.is_test_cut === false ? null : false)}
                >
                  No
                </button>
              </div>
            </div>
          </div>
        </FilterSection>
      </div>
    </div>
  );
}
