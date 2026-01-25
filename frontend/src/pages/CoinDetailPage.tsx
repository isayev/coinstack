import { useNavigate, useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { v2 } from "@/api/v2"
import { CoinDetailV3 } from "@/features/collection/CoinDetailV3"
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
      <div
        className="h-full"
        style={{ background: 'var(--bg-app)' }}
      >
        <div className="container mx-auto p-6 max-w-7xl space-y-6">
          <Skeleton className="h-10 w-32" />
          <div className="flex gap-6">
            <Skeleton className="w-[35%] h-[400px]" />
            <div className="flex-1 space-y-6">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !coin) {
    return (
      <div
        className="flex items-center justify-center h-full"
        style={{ background: 'var(--bg-app)' }}
      >
        <div className="text-center">
          <h2
            className="text-xl font-bold mb-2"
            style={{ color: 'var(--text-primary)' }}
          >
            Coin not found
          </h2>
          <p
            className="text-sm mb-4"
            style={{ color: 'var(--text-muted)' }}
          >
            The coin you're looking for doesn't exist or has been deleted.
          </p>
          <Button variant="outline" onClick={() => navigate('/')}>
            Back to Collection
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div
      className="h-full flex flex-col"
      style={{ background: 'var(--bg-app)' }}
    >
      {/* Header */}
      <div
        className="border-b px-6 py-4 flex items-center justify-between"
        style={{
          background: 'var(--bg-card)',
          borderColor: 'var(--border-subtle)',
        }}
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/')}
          style={{ color: 'var(--text-secondary)' }}
        >
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

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 max-w-7xl">
          <Tabs defaultValue="details" className="space-y-6">
            <TabsList>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="audit" className="relative">
                Data Audit
              </TabsTrigger>
            </TabsList>

            <TabsContent value="details" className="mt-0">
              <CoinDetailV3 coin={coin} />
            </TabsContent>

            <TabsContent value="audit">
              <div className="max-w-2xl">
                <h2
                  className="text-xl font-bold mb-4 flex items-center gap-2"
                  style={{ color: 'var(--text-primary)' }}
                >
                  <AlertCircle className="w-5 h-5 text-destructive" />
                  External Data Comparison
                </h2>
                <p
                  className="text-sm mb-6"
                  style={{ color: 'var(--text-muted)' }}
                >
                  Comparing your local records against scraped auction data to ensure accuracy.
                </p>
                <AuditPanel coinId={coinId} />
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}