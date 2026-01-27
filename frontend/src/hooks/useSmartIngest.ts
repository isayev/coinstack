import { useMutation } from "@tanstack/react-query"
import { client } from "@/api/client"
import api from "@/api/api"
import { toast } from "sonner"

export interface IdentificationResult {
  ruler?: string
  denomination?: string
  mint?: string
  date_range?: string
  obverse_description?: string
  reverse_description?: string
  suggested_references: string[]
  confidence: number
}

export function useSmartIngest() {
  // 1. Scraper Mutation
  const scrapeMutation = useMutation({
    mutationFn: client.scrapeLot,
    onSuccess: () => toast.success("Auction data retrieved"),
    onError: (error: any) => toast.error(`Scrape failed: ${error.message}`)
  })

  // 2. Reference Lookup Mutation
  const referenceMutation = useMutation({
    mutationFn: async ({ catalog, number, volume }: { catalog: string, number: string, volume?: string }) => {
      return client.getCoinsByReference(catalog, number, volume)
    },
    onSuccess: (data) => {
      if (data.length > 0) {
        toast.success(`Found ${data.length} similar specimens in your collection`)
      } else {
        toast.info("No exact matches found in your collection")
      }
    }
  })

  // 3. Identification (Vision) Mutation
  const identifyMutation = useMutation({
    mutationFn: async (imageB64: string): Promise<IdentificationResult> => {
      const response = await api.post("/api/v2/llm/identify", { image_b64: imageB64 })
      return response.data
    },
    onSuccess: () => toast.success("Visual identification complete"),
    onError: (error: any) => toast.error(`Identification failed: ${error.message}`)
  })

  return {
    scrape: scrapeMutation.mutateAsync,
    isScraping: scrapeMutation.isPending,

    lookupReference: referenceMutation.mutateAsync,
    isLookingUp: referenceMutation.isPending,

    identify: identifyMutation.mutateAsync,
    isIdentifying: identifyMutation.isPending,

    // We can add more helpers here as needed
  }
}
