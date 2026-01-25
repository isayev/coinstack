import { useNavigate, useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { v2 } from "@/api/v2"
import { CoinDetail } from "@/features/collection/CoinDetail"
import { AuditPanel } from "@/features/audit/AuditPanel"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Edit, AlertCircle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function CoinDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const coinId = parseInt(id!)

  const { data: coin, isLoading, error } = useQuery({
    queryKey: ['coin', coinId],
    queryFn: () => v2.getCoin(coinId),
    enabled: !!id
  })

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 max-w-5xl space-y-6">
        <Skeleton className="h-10 w-32" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-[300px]" />
          <div className="md:col-span-2 space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !coin) {
    return (
      <div className="p-12 text-center">
        <h2 className="text-xl font-bold mb-2">Coin not found</h2>
        <Button variant="outline" onClick={() => navigate('/')}>
          Back to Collection
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      {/* Navbar */}
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate(`/coins/${id}/edit`)}>
            <Edit className="w-4 h-4 mr-2" />
            Edit
          </Button>
        </div>
      </div>

      <Tabs defaultValue="details" className="space-y-6">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="audit" className="relative">
            Data Audit
            {/* Simple dot if issues? For now just the tab */}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="details">
          <CoinDetail coin={coin} />
        </TabsContent>

        <TabsContent value="audit">
          <div className="max-w-2xl">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-destructive" />
              External Data Comparison
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Comparing your local records against scraped auction data to ensure accuracy.
            </p>
            <AuditPanel coinId={coinId} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}