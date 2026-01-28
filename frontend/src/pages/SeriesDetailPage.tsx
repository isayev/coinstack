import { useParams, Link } from "react-router-dom"
import { useSeriesDetail, useAddCoinToSeries } from "@/hooks/useSeries"
import { useCoins } from "@/hooks/useCoins"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ArrowLeft, Plus, CheckCircle2, Circle } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useState } from "react"

export function SeriesDetailPage() {
  const { id } = useParams<{ id: string }>()
  const seriesId = parseInt(id!)
  const { data: series, isLoading, isError, error, refetch } = useSeriesDetail(seriesId)
  const { data: coinsData } = useCoins()
  const addCoinMutation = useAddCoinToSeries()

  const [, setSelectedSlot] = useState<number | null>(null)

  if (isLoading) return <div className="container py-6">Loading series details...</div>

  if (isError && error) {
    const status = (error as { response?: { status?: number } })?.response?.status
    if (status === 404) {
      return (
        <div className="container py-6">
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <p className="font-medium">Series unavailable</p>
            <p className="text-sm mt-1">The series service could not be reached. Check that the backend is running.</p>
          </div>
        </div>
      )
    }
    return (
      <div className="container py-6">
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <p className="font-medium">Error loading series</p>
          <p className="text-sm mt-1">{String(error)}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    )
  }

  if (!series) return <div className="container py-6">Series not found</div>
  
  const filledCount = series.slots?.filter(sl => sl.status === 'filled').length || 0
  const targetCount = series.target_count || series.slots?.length || 0
  const progress = targetCount > 0 ? (filledCount / targetCount) * 100 : 0
  
  return (
    <div className="container py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/series">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{series.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="secondary" className="capitalize">{series.series_type.replace('_', ' ')}</Badge>
            <span className="text-sm text-muted-foreground">{filledCount} of {targetCount} coins collected</span>
          </div>
        </div>
      </div>
      
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium">Overall Completion</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-3" />
          </div>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {series.slots?.map((slot) => (
          <Card key={slot.id} className={slot.status === 'filled' ? "border-green-500/50 bg-green-500/5" : ""}>
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  {slot.status === 'filled' ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <Circle className="h-5 w-5 text-muted-foreground" />
                  )}
                  <CardTitle className="text-lg">
                    {slot.slot_number}. {slot.name}
                  </CardTitle>
                </div>
                <Badge variant="outline">#{slot.slot_number}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {slot.status === 'filled' ? (
                <div className="text-sm text-muted-foreground">
                  Coin assigned (ID: {slot.coin_id})
                </div>
              ) : (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" className="w-full mt-2" onClick={() => setSelectedSlot(slot.id)}>
                      <Plus className="mr-2 h-4 w-4" />
                      Assign Coin
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>Assign Coin to {slot.name}</DialogTitle>
                    </DialogHeader>
                    <div className="grid gap-2 mt-4">
                      {coinsData?.items?.map((coin) => (
                        <Button
                          key={coin.id}
                          variant="ghost"
                          className="justify-start text-left h-auto p-3"
                          onClick={() => {
                            if (coin.id !== null) {
                              addCoinMutation.mutate({ seriesId, coinId: coin.id, slotId: slot.id })
                            }
                          }}
                        >
                          <div className="flex flex-col">
                            <span className="font-medium">{coin.attribution.issuer}</span>
                            <span className="text-xs text-muted-foreground">
                              {coin.category} • {coin.metal} • {coin.attribution.mint}
                            </span>
                          </div>
                        </Button>
                      ))}
                    </div>
                  </DialogContent>
                </Dialog>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
