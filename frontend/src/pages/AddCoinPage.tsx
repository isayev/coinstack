import { useNavigate } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { v2 } from "@/api/v2"
import { CoinForm } from "@/components/coins/CoinForm"
import { ScraperForm } from "@/features/scraper/ScraperForm"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { toast } from "sonner"
import { useState } from "react"
import { ScrapeResult } from "@/api/v2"

export function AddCoinPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [scrapedData, setScrapedData] = useState<ScrapeResult | null>(null)

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

  const getFormDefaults = () => {
    if (!scrapedData) return undefined;

    // Map scrape result to form defaults
    // Explicitly cast to partial form data or ensure all required fields are present
    return {
      category: 'roman_imperial' as const,
      metal: 'silver' as const,
      dimensions: {
        weight_g: null,
        diameter_mm: null,
        thickness_mm: null,
        die_axis: null
      },
      attribution: {
        issuer: scrapedData.issuer || '',
        mint: '',
        year_start: null,
        year_end: null
      },
      grading: {
        grading_state: 'raw' as const,
        grade: scrapedData.grade || '',
        service: null,
        certification_number: '',
        strike: '',
        surface: '',
        eye_appeal: null,
        toning_description: null
      },
      acquisition: {
        price: scrapedData.hammer_price || 0,
        currency: 'USD',
        source: scrapedData.source,
        date: '',
        url: scrapedData.url
      },
      images: [],
      tags: []
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-3xl space-y-8">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Add New Coin</h1>
          <p className="text-muted-foreground">Import from URL or enter manually</p>
        </div>
      </div>

      <ScraperForm onScrapeSuccess={setScrapedData} />

      {scrapedData && (
        <div className="bg-primary/10 text-primary px-4 py-3 rounded-md text-sm mb-4">
          Loaded data from <strong>{scrapedData.source}</strong> for lot <strong>{scrapedData.lot_id}</strong>.
          Please review and fill in missing fields.
        </div>
      )}

      <CoinForm
        key={scrapedData ? scrapedData.url : 'empty'} // Reset form when scrape changes
        defaultValues={getFormDefaults()}
        onSubmit={(data) => mutation.mutate(data as any)}
        isSubmitting={mutation.isPending}
      />
    </div>
  )
}
