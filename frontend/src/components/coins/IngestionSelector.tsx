import { useState } from "react"
import { 
  Search, 
  Upload, 
  Link as LinkIcon, 
  FileText, 
  Loader2, 
  Sparkles,
  ChevronRight,
  History
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useSmartIngest } from "@/hooks/useSmartIngest"

interface IngestionSelectorProps {
  onDataLoaded: (data: any) => void
  onManualStart: () => void
}

export function IngestionSelector({ onDataLoaded, onManualStart }: IngestionSelectorProps) {
  const [url, setUrl] = useState("")
  const [reference, setReference] = useState("")
  const { scrape, isScraping, lookupReference, isLookingUp, identify, isIdentifying } = useSmartIngest()

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url) return
    try {
      const data = await scrape(url)
      console.log("Scrape result:", data)
      if (data) onDataLoaded(data)
    } catch (error) {
      console.error("Scrape failed in handler:", error)
      // Toast is handled by mutation onError
    }
  }

  const handleReferenceSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reference) return
    
    // Improved parser for "RIC I 207", "RPC III 3201", "Crawford 335/1c"
    // Heuristic: Last part is number, First part is Catalog, Middle is Volume
    const parts = reference.trim().split(/\s+/)
    
    if (parts.length < 2) {
      // Try fuzzy lookup if simple string
      const results = await lookupReference({ catalog: reference, number: "" })
      if (results?.length) onDataLoaded(results[0])
      return
    }

    const catalog = parts[0]
    const number = parts[parts.length - 1]
    const volume = parts.slice(1, parts.length - 1).join(" ") || undefined
    
    const results = await lookupReference({ catalog, number, volume })
    if (results && results.length > 0) {
      onDataLoaded(results[0])
    }
  }

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onloadend = async () => {
      const base64 = reader.result as string
      const result = await identify(base64.split(",")[1])
      if (result) onDataLoaded(result)
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Add New Coin</h1>
        <p className="text-muted-foreground text-lg">
          Choose how you'd like to start cataloging your specimen.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Method 1: URL Scraper */}
        <Card className="relative overflow-hidden group hover:border-primary/50 transition-colors">
          <CardHeader>
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <LinkIcon className="h-5 w-5 text-primary" />
            </div>
            <CardTitle>Auction Import</CardTitle>
            <CardDescription>
              Paste a URL from Heritage, CNG, or eBay to auto-fill details.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUrlSubmit} className="flex gap-2">
              <Input 
                placeholder="https://coins.ha.com/itm/..." 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isScraping}
              />
              <Button type="submit" disabled={!url || isScraping}>
                {isScraping ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronRight className="h-4 w-4" />}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Method 2: Visual ID */}
        <Card className="relative overflow-hidden group hover:border-primary/50 transition-colors">
          <CardHeader>
            <div className="h-10 w-10 rounded-lg bg-purple-500/10 flex items-center justify-center mb-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
            </div>
            <CardTitle>Visual Identification</CardTitle>
            <CardDescription>
              Upload a photo and let AI identify the ruler and denomination.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <Input 
                type="file" 
                accept="image/*" 
                onChange={handleImageUpload}
                className="opacity-0 absolute inset-0 cursor-pointer z-10"
                disabled={isIdentifying}
              />
              <Button variant="outline" className="w-full gap-2" disabled={isIdentifying}>
                {isIdentifying ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="h-4 w-4" />
                )}
                {isIdentifying ? "Identifying..." : "Upload Image"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Method 3: Reference Lookup */}
        <Card className="relative overflow-hidden group hover:border-primary/50 transition-colors">
          <CardHeader>
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center mb-2">
              <Search className="h-5 w-5 text-blue-500" />
            </div>
            <CardTitle>Catalog Reference</CardTitle>
            <CardDescription>
              Start from a standard catalog ID (e.g. RIC II 207).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleReferenceSubmit} className="flex gap-2">
              <Input 
                placeholder="RIC I 207" 
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                disabled={isLookingUp}
              />
              <Button type="submit" disabled={!reference || isLookingUp}>
                {isLookingUp ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronRight className="h-4 w-4" />}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Method 4: Manual Start */}
        <Card className="relative overflow-hidden group hover:border-primary/50 transition-colors cursor-pointer" onClick={onManualStart}>
          <CardHeader>
            <div className="h-10 w-10 rounded-lg bg-orange-500/10 flex items-center justify-center mb-2">
              <FileText className="h-5 w-5 text-orange-500" />
            </div>
            <CardTitle>Manual Entry</CardTitle>
            <CardDescription>
              Start with an empty form and enter details manually.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-end">
            <div className="text-orange-500 group-hover:translate-x-1 transition-transform">
              <ChevronRight className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="pt-8 border-t flex justify-center">
        <Button variant="ghost" className="gap-2 text-muted-foreground" onClick={() => {/* TODO: Recent Drafts */}}>
          <History className="h-4 w-4" />
          View Recent Drafts
        </Button>
      </div>
    </div>
  )
}
