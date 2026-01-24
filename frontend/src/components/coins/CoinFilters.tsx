import { useState } from "react";
import { useFilterStore } from "@/stores/filterStore";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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

// All metal options from expanded enum - with badge class references
const METALS = [
  { value: "gold", label: "Au", fullLabel: "Gold", badgeClass: "badge-metal-gold" },
  { value: "electrum", label: "El", fullLabel: "Electrum", badgeClass: "badge-metal-electrum" },
  { value: "silver", label: "Ar", fullLabel: "Silver", badgeClass: "badge-metal-silver" },
  { value: "billon", label: "Bil", fullLabel: "Billon", badgeClass: "badge-metal-billon" },
  { value: "potin", label: "Pot", fullLabel: "Potin", badgeClass: "badge-metal-potin" },
  { value: "orichalcum", label: "Or", fullLabel: "Orichalcum", badgeClass: "badge-metal-orichalcum" },
  { value: "bronze", label: "Æ", fullLabel: "Bronze", badgeClass: "badge-metal-bronze" },
  { value: "copper", label: "Cu", fullLabel: "Copper", badgeClass: "badge-metal-copper" },
  { value: "lead", label: "Pb", fullLabel: "Lead", badgeClass: "badge-metal-lead" },
  { value: "ae", label: "AE", fullLabel: "AE", badgeClass: "badge-metal-ae" },
];

// Rarity options
const RARITIES = [
  { value: "common", label: "Common" },
  { value: "uncommon", label: "Uncommon" },
  { value: "scarce", label: "Scarce" },
  { value: "rare", label: "Rare" },
  { value: "very_rare", label: "Very Rare" },
  { value: "extremely_rare", label: "Extremely Rare" },
  { value: "unique", label: "Unique" },
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
    <div className="border-b border-border/50 pb-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full py-2 text-sm font-medium hover:text-primary transition-colors"
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
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
  
  return (
    <div className="w-72 border-r bg-card/50 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b sticky top-0 bg-card/95 backdrop-blur z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4" />
            <h3 className="font-semibold">Filters</h3>
            {activeFilterCount > 0 && (
              <Badge variant="secondary" className="h-5 px-1.5 text-xs">
                {activeFilterCount}
              </Badge>
            )}
          </div>
          {activeFilterCount > 0 && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={filters.reset}
              className="h-8 px-2 text-muted-foreground hover:text-foreground"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" />
              Reset
            </Button>
          )}
        </div>
      </div>
      
      {/* Filter sections */}
      <div className="flex-1 overflow-auto p-4 space-y-1">
        {/* Category */}
        <FilterSection 
          title="Category" 
          badge={filters.category && (
            <Badge variant="outline" className="text-xs capitalize">
              {filters.category.replace("_", " ")}
            </Badge>
          )}
        >
          <Select 
            value={filters.category || "all"} 
            onValueChange={(v) => filters.setCategory(v === "all" ? null : v)}
          >
            <SelectTrigger className="h-9">
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {CATEGORIES.map((cat) => (
                <SelectItem key={cat.value} value={cat.value}>
                  {cat.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FilterSection>
        
        {/* Metal */}
        <FilterSection 
          title="Metal"
          badge={filters.metal && (
            <Badge variant="outline" className={cn(
              "text-xs capitalize",
              METALS.find(m => m.value === filters.metal)?.badgeClass
            )}>
              {METALS.find(m => m.value === filters.metal)?.fullLabel || filters.metal}
            </Badge>
          )}
        >
          <div className="flex flex-wrap gap-1.5">
            {METALS.map((metal) => (
              <button
                key={metal.value}
                onClick={() => filters.setMetal(filters.metal === metal.value ? null : metal.value)}
                className={cn(
                  "h-7 px-2.5 text-xs rounded-md border transition-all font-medium",
                  filters.metal === metal.value
                    ? cn(metal.badgeClass, "ring-1 ring-offset-1 ring-primary/50")
                    : "border-border/50 hover:border-border hover:bg-muted/50 text-muted-foreground hover:text-foreground"
                )}
                title={metal.fullLabel}
              >
                {metal.label}
              </button>
            ))}
          </div>
        </FilterSection>
        
        {/* Year Range */}
        <FilterSection 
          title="Year Range"
          badge={(filters.mint_year_gte !== null || filters.mint_year_lte !== null) && (
            <Badge variant="outline" className="text-xs">
              <Calendar className="w-3 h-3 mr-1" />
              Set
            </Badge>
          )}
        >
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-xs text-muted-foreground block mb-1">From</span>
                <Input
                  type="number"
                  placeholder="-44 BCE"
                  value={filters.mint_year_gte ?? ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    filters.setMintYearGte(val ? parseInt(val) : null);
                  }}
                  className="h-8 text-sm"
                />
              </div>
              <div>
                <span className="text-xs text-muted-foreground block mb-1">To</span>
                <Input
                  type="number"
                  placeholder="476 CE"
                  value={filters.mint_year_lte ?? ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    filters.setMintYearLte(val ? parseInt(val) : null);
                  }}
                  className="h-8 text-sm"
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Use negative numbers for BCE dates
            </p>
          </div>
        </FilterSection>
        
        {/* Ruler / Authority */}
        <FilterSection 
          title="Ruler"
          badge={filters.issuing_authority && (
            <Badge variant="outline" className="text-xs truncate max-w-[100px]">
              {filters.issuing_authority}
            </Badge>
          )}
          defaultOpen={false}
        >
          <Input
            placeholder="Search rulers..."
            value={filters.issuing_authority || ""}
            onChange={(e) => filters.setIssuingAuthority(e.target.value || null)}
            className="h-9"
          />
        </FilterSection>
        
        {/* Mint */}
        <FilterSection 
          title="Mint" 
          badge={filters.mint_name && (
            <Badge variant="outline" className="text-xs">
              <MapPin className="w-3 h-3 mr-1" />
              Set
            </Badge>
          )}
          defaultOpen={false}
        >
          <Input
            placeholder="Search mints..."
            value={filters.mint_name || ""}
            onChange={(e) => filters.setMintName(e.target.value || null)}
            className="h-9"
          />
        </FilterSection>
        
        {/* Rarity */}
        <FilterSection 
          title="Rarity"
          badge={filters.rarity && (
            <Badge variant="outline" className="text-xs capitalize">
              {filters.rarity.replace("_", " ")}
            </Badge>
          )}
          defaultOpen={false}
        >
          <Select 
            value={filters.rarity || "all"} 
            onValueChange={(v) => filters.setRarity(v === "all" ? null : v)}
          >
            <SelectTrigger className="h-9">
              <SelectValue placeholder="Any rarity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Any Rarity</SelectItem>
              {RARITIES.map((r) => (
                <SelectItem key={r.value} value={r.value}>
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FilterSection>
        
        {/* Grade */}
        <FilterSection 
          title="Grade"
          badge={filters.grade && (
            <Badge variant="outline" className="text-xs">
              {filters.grade}
            </Badge>
          )}
          defaultOpen={false}
        >
          <Input
            placeholder="VF, EF, MS..."
            value={filters.grade || ""}
            onChange={(e) => filters.setGrade(e.target.value || null)}
            className="h-9"
          />
        </FilterSection>
        
        {/* Storage Location */}
        <FilterSection 
          title="Storage"
          badge={filters.storage_location && (
            <Badge variant="outline" className="text-xs">
              {filters.storage_location}
            </Badge>
          )}
          defaultOpen={false}
        >
          <Select 
            value={filters.storage_location || "all"} 
            onValueChange={(v) => filters.setStorageLocation(v === "all" ? null : v)}
          >
            <SelectTrigger className="h-9">
              <SelectValue placeholder="All locations" />
            </SelectTrigger>
            <SelectContent>
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
            <Badge variant="outline" className="text-xs">
              <Sparkles className="w-3 h-3 mr-1" />
              Set
            </Badge>
          )}
          defaultOpen={false}
        >
          <div className="space-y-3">
            {/* Is Circa */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm">Circa Dating</span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={filters.is_circa === true ? "default" : "outline"}
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={() => filters.setIsCirca(filters.is_circa === true ? null : true)}
                >
                  Yes
                </Button>
                <Button
                  variant={filters.is_circa === false ? "default" : "outline"}
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={() => filters.setIsCirca(filters.is_circa === false ? null : false)}
                >
                  No
                </Button>
              </div>
            </div>
            
            {/* Is Test Cut */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scissors className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm">Test Cut</span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={filters.is_test_cut === true ? "default" : "outline"}
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={() => filters.setIsTestCut(filters.is_test_cut === true ? null : true)}
                >
                  Yes
                </Button>
                <Button
                  variant={filters.is_test_cut === false ? "default" : "outline"}
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={() => filters.setIsTestCut(filters.is_test_cut === false ? null : false)}
                >
                  No
                </Button>
              </div>
            </div>
          </div>
        </FilterSection>
      </div>
    </div>
  );
}
