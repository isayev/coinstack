import { useState, useEffect } from "react"
import { useNavigate, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { useCreateSeries } from "@/hooks/useSeries"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Loader2, BookOpen, Users } from "lucide-react"
import { api } from "@/lib/api"

interface CanonicalSeriesOption {
  id: number
  vocab_type: string
  canonical_name: string
  nomisma_uri: string | null
  metadata: {
    expected_count?: number
    rulers?: string[]
    category?: string
    description?: string
  }
}

export function CreateSeriesPage() {
  const navigate = useNavigate()
  const createSeries = useCreateSeries()
  
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [seriesType, setSeriesType] = useState("user_defined")
  const [targetCount, setTargetCount] = useState<string>("")
  const [canonicalVocabId, setCanonicalVocabId] = useState<number | null>(null)
  
  // Fetch canonical series definitions from vocab_terms
  const { data: canonicalSeries, isLoading: loadingCanonical } = useQuery({
    queryKey: ['vocab', 'canonical_series'],
    queryFn: async () => {
      const response = await api.get('/api/v2/vocab/terms/canonical_series', {
        params: { limit: 100 }
      })
      return response.data as CanonicalSeriesOption[]
    },
  })
  
  // Get selected canonical series details
  const selectedCanonical = canonicalSeries?.find(s => s.id === canonicalVocabId)
  
  // Auto-populate fields when canonical series is selected
  useEffect(() => {
    if (selectedCanonical) {
      // Suggest name if empty
      if (!name) {
        setName(`My ${selectedCanonical.canonical_name}`)
      }
      // Set target count from canonical definition
      if (selectedCanonical.metadata.expected_count) {
        setTargetCount(selectedCanonical.metadata.expected_count.toString())
      }
      // Set description if empty
      if (!description && selectedCanonical.metadata.description) {
        setDescription(selectedCanonical.metadata.description)
      }
      // Set type to canonical
      setSeriesType("canonical")
    }
  }, [selectedCanonical])
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createSeries.mutate({
      name,
      description,
      series_type: seriesType,
      target_count: targetCount ? parseInt(targetCount) : undefined,
      canonical_vocab_id: canonicalVocabId
    }, {
      onSuccess: (data) => {
        navigate(`/series/${data.id}`)
      }
    })
  }
  
  return (
    <div className="container max-w-2xl py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/series">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">Create Series</h1>
      </div>
      
      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Series Details</CardTitle>
            <CardDescription>Define a new collection goal or thematic grouping.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Canonical Series Template Selector */}
            <div className="space-y-2">
              <Label htmlFor="canonical">Start from Template (Optional)</Label>
              <Select 
                value={canonicalVocabId?.toString() || ""} 
                onValueChange={(val) => setCanonicalVocabId(val ? parseInt(val) : null)}
              >
                <SelectTrigger id="canonical" className="w-full">
                  <SelectValue placeholder="Select a canonical series template..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">None - Start from scratch</SelectItem>
                  {loadingCanonical ? (
                    <SelectItem value="" disabled>Loading...</SelectItem>
                  ) : (
                    canonicalSeries?.map((series) => (
                      <SelectItem key={series.id} value={series.id.toString()}>
                        <div className="flex items-center gap-2">
                          <BookOpen className="h-4 w-4 text-muted-foreground" />
                          <span>{series.canonical_name}</span>
                          {series.metadata.expected_count && (
                            <Badge variant="secondary" className="ml-2">
                              {series.metadata.expected_count} items
                            </Badge>
                          )}
                        </div>
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {selectedCanonical && (
                <div className="mt-2 p-3 rounded-lg bg-muted/50 border">
                  <div className="flex items-start gap-2">
                    <Users className="h-4 w-4 mt-0.5 text-muted-foreground" />
                    <div className="text-sm">
                      <p className="font-medium">{selectedCanonical.canonical_name}</p>
                      {selectedCanonical.metadata.rulers && (
                        <p className="text-muted-foreground mt-1">
                          Rulers: {selectedCanonical.metadata.rulers.join(', ')}
                        </p>
                      )}
                      {selectedCanonical.metadata.description && (
                        <p className="text-muted-foreground mt-1">
                          {selectedCanonical.metadata.description}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="name">Series Name</Label>
              <Input 
                id="name" 
                placeholder="e.g., The Twelve Caesars" 
                value={name} 
                onChange={(e) => setName(e.target.value)}
                required 
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="type">Series Type</Label>
                <Select value={seriesType} onValueChange={setSeriesType}>
                  <SelectTrigger id="type">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="canonical">Canonical</SelectItem>
                    <SelectItem value="user_defined">User Defined</SelectItem>
                    <SelectItem value="thematic">Thematic</SelectItem>
                    <SelectItem value="geographic">Geographic</SelectItem>
                    <SelectItem value="temporal">Temporal</SelectItem>
                    <SelectItem value="dynastic">Dynastic</SelectItem>
                    <SelectItem value="smart">Smart (Dynamic)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="target">Target Count {selectedCanonical ? '(from template)' : '(Optional)'}</Label>
                <Input 
                  id="target" 
                  type="number" 
                  placeholder="e.g., 12" 
                  value={targetCount}
                  onChange={(e) => setTargetCount(e.target.value)}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea 
                id="description" 
                placeholder="Describe the scope and goals of this series..." 
                className="min-h-[100px]"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </CardContent>
          <CardFooter className="flex justify-end gap-2 border-t px-6 py-4">
            <Button variant="outline" type="button" onClick={() => navigate("/series")}>
              Cancel
            </Button>
            <Button type="submit" disabled={createSeries.isPending}>
              {createSeries.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Series
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}
