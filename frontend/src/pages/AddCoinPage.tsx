import { useNavigate } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { v2 } from "@/api/v2"
import { CoinForm } from "@/components/coins/CoinForm"
import { IngestionSelector } from "@/components/coins/IngestionSelector"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Sparkles } from "lucide-react"
import { toast } from "sonner"
import { useState } from "react"

export function AddCoinPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  // States
  const [ingestionMode, setIngestionMode] = useState(true)
  const [initialData, setInitialData] = useState<any>(null)
  const [dataSource, setDataSource] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: v2.createCoin,
    onSuccess: () => {
      toast.success("Coin added successfully")
      queryClient.invalidateQueries({ queryKey: ['coins'] })
      navigate('/')
    },
    onError: (error) => {
      toast.error(`Failed to add coin: ${error.message}`)
    }
  })

  const handleDataLoaded = (data: any) => {
    setInitialData(data)
    
    // Determine source for the banner
    if (data.source) setDataSource(`Auction Import (${data.source})`)
    else if (data.ruler) setDataSource("AI Visual Identification")
    else if (data.id) setDataSource(`Cloned from #${data.id}`)
    
    setIngestionMode(false)
  }

  const getFormDefaults = () => {
    if (!initialData) return undefined;

    // Handle Scrape Result (v2.ScrapeResult)
    if (initialData.source) {
      return {
        category: undefined, // Force user selection or infer if backend provides it
        metal: undefined,    // Force user selection
        dimensions: {
          weight_g: null,
          diameter_mm: null,
          thickness_mm: null,
          die_axis: null
        },
        attribution: {
          issuer: initialData.issuer || '',
          mint: '',
          year_start: null,
          year_end: null
        },
        grading: {
          grading_state: 'raw' as const,
          grade: initialData.grade || '',
          service: null,
          certification_number: '',
          strike: '',
          surface: '',
          eye_appeal: null,
          toning_description: null
        },
        acquisition: {
          price: initialData.hammer_price || 0,
          currency: 'USD',
          source: initialData.source,
          date: '',
          url: initialData.url
        },
        images: initialData.primary_image_url ? [{
          url: initialData.primary_image_url,
          image_type: 'obverse', // Default assumption
          is_primary: true
        }] : [],
        tags: []
      }
    }

    // Handle Identification Result (LLM)
    if (initialData.ruler) {
      return {
        category: undefined,
        metal: undefined,
        attribution: {
          issuer: initialData.ruler || '',
          mint: initialData.mint || '',
          year_start: null,
          year_end: null
        },
        description: `${initialData.obverse_description || ''} ${initialData.reverse_description || ''}`.trim()
      }
    }

    // Handle Existing Coin (Clone)
    if (initialData.id) {
      const clone = { ...initialData }
      delete clone.id
      return clone
    }

    return undefined
  }

  if (ingestionMode) {
    return (
      <div className="container mx-auto p-6 max-w-5xl space-y-8 min-h-screen">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>
        <IngestionSelector 
          onDataLoaded={handleDataLoaded} 
          onManualStart={() => setIngestionMode(false)} 
        />
      </div>
    )
  }

  return (
    <div
      className="container mx-auto p-6 max-w-4xl space-y-8"
      style={{ background: 'var(--bg-app)' }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => setIngestionMode(true)}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1
              className="text-2xl font-bold"
              style={{ color: 'var(--text-primary)' }}
            >
              Add New Coin
            </h1>
            <p
              className="text-sm text-muted-foreground"
            >
              Step 2: Refine and complete specimen data
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={() => setIngestionMode(true)} className="gap-2">
          <Sparkles className="w-4 h-4" />
          Change Method
        </Button>
      </div>

      {dataSource && (
        <div
          className="px-4 py-3 rounded-lg text-sm mb-4 border flex items-center gap-3 bg-primary/5 border-primary/20 text-primary"
        >
          <Sparkles className="w-4 h-4" />
          <p>
            Smart Start active: Data loaded from <strong>{dataSource}</strong>.
            Please review and complete the research-grade fields.
          </p>
        </div>
      )}

      <CoinForm
        key={dataSource || 'manual'} 
        defaultValues={getFormDefaults()}
        onSubmit={(data) => mutation.mutate(data as any)}
        isSubmitting={mutation.isPending}
      />
    </div>
  )
}
