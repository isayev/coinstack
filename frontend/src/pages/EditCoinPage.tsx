import { useNavigate, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { v2 } from "@/api/v2"
import { CoinForm } from "@/components/coins/CoinForm"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { toast } from "sonner"
import { Skeleton } from "@/components/ui/skeleton"

export function EditCoinPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const coinId = parseInt(id!)

  const { data: coin, isLoading } = useQuery({
    queryKey: ['coin', coinId],
    queryFn: () => v2.getCoin(coinId),
    enabled: !!id
  })

  const mutation = useMutation({
    mutationFn: (data: any) => v2.updateCoin(coinId, data),
    onSuccess: () => {
      toast.success("Coin updated successfully")
      queryClient.invalidateQueries({ queryKey: ['coins'] })
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
      navigate(`/coins/${coinId}`)
    },
    onError: (error) => {
      toast.error(`Failed to update coin: ${error.message}`)
    }
  })

  if (isLoading) {
    return (
      <div
        className="p-6"
        style={{ background: 'var(--bg-app)' }}
      >
        <Skeleton className="h-[600px] w-full" />
      </div>
    )
  }

  if (!coin) {
    return (
      <div
        className="flex items-center justify-center h-full"
        style={{ background: 'var(--bg-app)' }}
      >
        <div
          className="text-xl font-bold"
          style={{ color: 'var(--text-primary)' }}
        >
          Coin not found
        </div>
      </div>
    )
  }

  return (
    <div
      className="container mx-auto p-6 max-w-3xl"
      style={{ background: 'var(--bg-app)' }}
    >
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1
            className="text-2xl font-bold"
            style={{ color: 'var(--text-primary)' }}
          >
            Edit Coin
          </h1>
          <p
            className="text-sm"
            style={{ color: 'var(--text-muted)' }}
          >
            {coin.attribution.issuer} - {coin.grading.grade}
          </p>
        </div>
      </div>

      <CoinForm 
        defaultValues={{
          category: coin.category,
          metal: coin.metal,
          dimensions: coin.dimensions,
          attribution: coin.attribution,
          grading: coin.grading,
          acquisition: coin.acquisition || undefined
        }}
        onSubmit={(data) => mutation.mutate(data)} 
        isSubmitting={mutation.isPending}
      />
    </div>
  )
}