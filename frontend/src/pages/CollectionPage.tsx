import { CoinList } from "@/features/collection/CoinList"
import { CoinFilters } from "@/features/collection/CoinFilters"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { useNavigate } from "react-router-dom"

export function CollectionPage() {
  const navigate = useNavigate()

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="border-b bg-card px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Collection</h1>
          <p className="text-sm text-muted-foreground">
            Manage your numismatic portfolio
          </p>
        </div>
        <Button onClick={() => navigate("/coins/new")}>
          <Plus className="mr-2 h-4 w-4" />
          Add Coin
        </Button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        <CoinFilters />
        <div className="flex-1 overflow-auto p-6">
          <CoinList />
        </div>
      </div>
    </div>
  )
}