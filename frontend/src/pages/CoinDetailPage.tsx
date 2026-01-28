import { useState, useEffect, useCallback } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { client } from "@/api/client"
import { CoinDetail } from "@/features/collection/CoinDetail"
import { AddCoinImagesDialog } from "@/components/coins/AddCoinImagesDialog"
import { AuditPanel } from "@/features/audit/AuditPanel"
import { Button } from "@/components/ui/button"
import { ArrowLeft, AlertCircle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useExpandLegendV2, useGenerateHistoricalContext, useTranscribeLegendForCoin, useIdentifyCoinForCoin } from "@/hooks/useLLM"
import { toast } from "sonner"
import { Link } from "react-router-dom"
import { ScrollText, Search, Sparkles } from "lucide-react"

export function CoinDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Safely parse coin ID with validation
  const coinId = id ? parseInt(id, 10) : NaN

  // Handle invalid ID early
  if (!id || isNaN(coinId)) {
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
            Invalid Coin ID
          </h2>
          <p
            className="text-sm mb-4"
            style={{ color: 'var(--text-muted)' }}
          >
            The URL contains an invalid coin identifier.
          </p>
          <Button variant="outline" onClick={() => navigate('/')}>
            Back to Collection
          </Button>
        </div>
      </div>
    )
  }

  const { data: coin, isLoading, error } = useQuery({
    queryKey: ['coin', coinId],
    queryFn: () => client.getCoin(coinId),
    enabled: !!id
  })

  // Add/attach images dialog
  const [addImagesOpen, setAddImagesOpen] = useState(false)

  // LLM legend expansion
  const [enrichingSide, setEnrichingSide] = useState<'obverse' | 'reverse' | null>(null)
  const [isGeneratingContext, setIsGeneratingContext] = useState(false)
  const expandLegend = useExpandLegendV2()
  const generateContext = useGenerateHistoricalContext()
  const transcribeForCoin = useTranscribeLegendForCoin()
  const identifyForCoin = useIdentifyCoinForCoin()

  const handleGenerateContext = async () => {
    if (!coin) return

    setIsGeneratingContext(true)

    try {
      // Backend fetches full coin data from DB for comprehensive context generation
      const result = await generateContext.mutateAsync({
        coin_id: coin.id!,
      })

      // Update the coin in cache with historical context
      queryClient.setQueryData(['coin', coinId], (oldData: any) => ({
        ...oldData,
        historical_significance: result.raw_content,
        llm_enriched_at: new Date().toISOString(),
      }))

      toast.success(`Historical context generated (${(result.confidence * 100).toFixed(0)}% confidence)`)
    } catch (err: any) {
      toast.error(`Failed to generate context: ${err.message || 'Unknown error'}`)
    } finally {
      setIsGeneratingContext(false)
    }
  }

  const handleEnrichLegend = async (side: 'obverse' | 'reverse') => {
    if (!coin) return

    const legend = side === 'obverse'
      ? (coin.design?.obverse_legend || coin.obverse_legend)
      : (coin.design?.reverse_legend || coin.reverse_legend)

    if (!legend) {
      toast.error(`No ${side} legend to expand`)
      return
    }

    setEnrichingSide(side)

    try {
      const result = await expandLegend.mutateAsync({ abbreviation: legend })

      // Update the coin in cache with expanded legend
      queryClient.setQueryData(['coin', coinId], (oldData: any) => ({
        ...oldData,
        [`${side}_legend_expanded`]: result.expanded,
      }))

      toast.success(`Legend expanded (${(result.confidence * 100).toFixed(0)}% confidence)`)
    } catch (err: any) {
      toast.error(`Failed to expand legend: ${err.message || 'Unknown error'}`)
    } finally {
      setEnrichingSide(null)
    }
  }

  // Navigation handlers for side arrows
  const handleNavigatePrev = useCallback(() => {
    if (coin?.prev_id) {
      navigate(`/coins/${coin.prev_id}`)
    }
  }, [coin?.prev_id, navigate])

  const handleNavigateNext = useCallback(() => {
    if (coin?.next_id) {
      navigate(`/coins/${coin.next_id}`)
    }
  }, [coin?.next_id, navigate])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't interfere with input fields
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return
      }

      if (e.key === 'ArrowLeft' && coin?.prev_id) {
        e.preventDefault()
        handleNavigatePrev()
      } else if (e.key === 'ArrowRight' && coin?.next_id) {
        e.preventDefault()
        handleNavigateNext()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [coin?.prev_id, coin?.next_id, handleNavigatePrev, handleNavigateNext])

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
      {/* Navigation Header */}
      <div
        className="border-b px-6 py-3 flex items-center"
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
          Back to Collection
        </Button>
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
              {(() => {
                const c = coin as { llm_suggested_design?: unknown; llm_suggested_attribution?: unknown } | undefined
                const hasPending = !!c?.llm_suggested_design || !!c?.llm_suggested_attribution
                return (
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center gap-2 rounded-lg border p-3" style={{ background: 'var(--bg-muted)', borderColor: 'var(--border-subtle)' }}>
                        {hasPending && (
                          <Link
                            to="/review?tab=ai"
                            className="inline-flex items-center gap-1.5 text-sm font-medium"
                            style={{ color: 'var(--accent-ai)' }}
                          >
                            <Sparkles className="h-4 w-4" />
                            Pending AI suggestions — Review in AI Suggestions →
                          </Link>
                        )}
                        <div className="flex flex-wrap gap-2 ml-auto">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={transcribeForCoin.isPending || identifyForCoin.isPending}
                            onClick={async () => {
                              try {
                                await transcribeForCoin.mutateAsync(coinId)
                                queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
                                toast.success("Legends transcribed; suggestions saved. Review in AI Suggestions.")
                              } catch {
                                toast.error("Transcribe failed (coin may have no primary image)")
                              }
                            }}
                          >
                            {transcribeForCoin.isPending ? "..." : <><ScrollText className="h-4 w-4 mr-1" /> Transcribe legends</>}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={transcribeForCoin.isPending || identifyForCoin.isPending}
                            onClick={async () => {
                              try {
                                await identifyForCoin.mutateAsync(coinId)
                                queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
                                toast.success("Coin identified; suggestions saved. Review in AI Suggestions.")
                              } catch {
                                toast.error("Identify failed (coin may have no primary image)")
                              }
                            }}
                          >
                            {identifyForCoin.isPending ? "..." : <><Search className="h-4 w-4 mr-1" /> Identify from image</>}
                          </Button>
                        </div>
                    </div>
                    <CoinDetail
                      coin={coin}
                      onEdit={() => navigate(`/coins/${id}/edit`)}
                      onNavigatePrev={handleNavigatePrev}
                      onNavigateNext={handleNavigateNext}
                      hasPrev={!!coin?.prev_id}
                      hasNext={!!coin?.next_id}
                      onOpenAddImages={() => setAddImagesOpen(true)}
                      onEnrichLegend={handleEnrichLegend}
                      isEnrichingObverse={enrichingSide === 'obverse'}
                      isEnrichingReverse={enrichingSide === 'reverse'}
                      onGenerateContext={handleGenerateContext}
                      isGeneratingContext={isGeneratingContext}
                    />
                    <AddCoinImagesDialog
                      coin={coin}
                      open={addImagesOpen}
                      onOpenChange={setAddImagesOpen}
                      onSuccess={() => queryClient.invalidateQueries({ queryKey: ['coin', coinId] })}
                    />
                  </div>
                );
              })()}
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