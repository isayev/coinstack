import { useCoins } from "@/hooks/useCoins";
import { CoinCard } from "@/components/coins/CoinCard";
import { CoinFilters } from "@/components/coins/CoinFilters";
import { useUIStore } from "@/stores/uiStore";
import { Button } from "@/components/ui/button";
import { Grid3x3, Table2 } from "lucide-react";

export function CollectionPage() {
  const { data, isLoading, error } = useCoins();
  const { viewMode, setViewMode } = useUIStore();

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading coins...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-destructive">Error loading coins: {error.message}</div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      <CoinFilters />
      <div className="flex-1 overflow-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Collection</h1>
            <p className="text-muted-foreground">
              {data?.total || 0} coins
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={viewMode === "grid" ? "default" : "outline"}
              size="icon"
              onClick={() => setViewMode("grid")}
            >
              <Grid3x3 className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === "table" ? "default" : "outline"}
              size="icon"
              onClick={() => setViewMode("table")}
            >
              <Table2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {viewMode === "grid" ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {data?.items.map((coin) => (
              <CoinCard key={coin.id} coin={coin} />
            ))}
          </div>
        ) : (
          <div className="border rounded-lg">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-4">Ruler</th>
                  <th className="text-left p-4">Denomination</th>
                  <th className="text-left p-4">Metal</th>
                  <th className="text-left p-4">Grade</th>
                  <th className="text-right p-4">Price</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((coin) => (
                  <tr key={coin.id} className="border-b hover:bg-muted/50">
                    <td className="p-4">{coin.issuing_authority}</td>
                    <td className="p-4">{coin.denomination}</td>
                    <td className="p-4 capitalize">{coin.metal}</td>
                    <td className="p-4">{coin.grade || "—"}</td>
                    <td className="p-4 text-right">
                      {coin.acquisition_price
                        ? `$${Number(coin.acquisition_price).toLocaleString()}`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.items.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            No coins found. Try adjusting your filters or add your first coin!
          </div>
        )}
      </div>
    </div>
  );
}
