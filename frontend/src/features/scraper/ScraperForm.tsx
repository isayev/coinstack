import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { v2 } from "@/api/v2"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Search, Loader2, Link as LinkIcon } from "lucide-react"
import { toast } from "sonner"

interface ScraperFormProps {
  onScrapeSuccess: (data: any) => void
}

export function ScraperForm({ onScrapeSuccess }: ScraperFormProps) {
  const [url, setUrl] = useState("")

  const scrapeMutation = useMutation({
    mutationFn: v2.scrapeLot,
    onSuccess: (data) => {
      toast.success("Lot scraped successfully")
      onScrapeSuccess(data)
    },
    onError: (error) => {
      toast.error(`Scrape failed: ${error.message}`)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!url) return
    scrapeMutation.mutate(url)
  }

  return (
    <Card className="bg-muted/30">
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <LinkIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Paste Heritage or CNG auction URL..." 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="pl-9"
              disabled={scrapeMutation.isPending}
            />
          </div>
          <Button type="submit" disabled={!url || scrapeMutation.isPending}>
            {scrapeMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Search className="h-4 w-4 mr-2" />
            )}
            Scrape
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-2 ml-1">
          Supports coins.ha.com and cngcoins.com
        </p>
      </CardContent>
    </Card>
  )
}
