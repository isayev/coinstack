import { useFilterStore } from "@/stores/filterStore";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

export function CoinFilters() {
  const filters = useFilterStore();
  
  const activeFilterCount = Object.values({
    category: filters.category,
    metal: filters.metal,
    issuing_authority: filters.issuing_authority,
    mint_name: filters.mint_name,
    storage_location: filters.storage_location,
  }).filter(Boolean).length;
  
  return (
    <div className="w-64 border-r bg-card p-4 space-y-4 overflow-auto">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Filters</h3>
        {activeFilterCount > 0 && (
          <Button variant="ghost" size="sm" onClick={filters.reset}>
            <X className="w-4 h-4 mr-1" />
            Clear ({activeFilterCount})
          </Button>
        )}
      </div>
      
      <div className="space-y-2">
        <label className="text-sm font-medium">Category</label>
        <Select value={filters.category || "all"} onValueChange={(v) => filters.setCategory(v === "all" ? null : v)}>
          <SelectTrigger>
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="republic">Republic</SelectItem>
            <SelectItem value="imperial">Imperial</SelectItem>
            <SelectItem value="provincial">Provincial</SelectItem>
            <SelectItem value="byzantine">Byzantine</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div className="space-y-2">
        <label className="text-sm font-medium">Metal</label>
        <div className="flex flex-wrap gap-2">
          {["gold", "silver", "billon", "bronze"].map((metal) => (
            <Button
              key={metal}
              variant={filters.metal === metal ? "default" : "outline"}
              size="sm"
              onClick={() => filters.setMetal(filters.metal === metal ? null : metal)}
              className="capitalize"
            >
              {metal}
            </Button>
          ))}
        </div>
      </div>
      
      <div className="space-y-2">
        <label className="text-sm font-medium">Ruler</label>
        <Input
          placeholder="Search rulers..."
          value={filters.issuing_authority || ""}
          onChange={(e) => filters.setIssuingAuthority(e.target.value || null)}
        />
      </div>
      
      <div className="space-y-2">
        <label className="text-sm font-medium">Mint</label>
        <Input
          placeholder="Search mints..."
          value={filters.mint_name || ""}
          onChange={(e) => filters.setMintName(e.target.value || null)}
        />
      </div>
      
      <div className="space-y-2">
        <label className="text-sm font-medium">Storage Location</label>
        <Select value={filters.storage_location || "all"} onValueChange={(v) => filters.setStorageLocation(v === "all" ? null : v)}>
          <SelectTrigger>
            <SelectValue placeholder="All locations" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="SlabBox1">Slab Box 1</SelectItem>
            <SelectItem value="Velv1">Velvet Tray 1</SelectItem>
            <SelectItem value="Velv2">Velvet Tray 2</SelectItem>
            <SelectItem value="Velv3">Velvet Tray 3</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
