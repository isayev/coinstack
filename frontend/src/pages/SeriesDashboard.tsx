import { useSeries } from "@/hooks/useSeries"
import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Plus, LayoutGrid, AlertCircle } from "lucide-react"

export function SeriesDashboard() {
  const { data, isLoading, isError, error, refetch } = useSeries()

  if (isLoading) return <div>Loading series...</div>

  if (isError && error) {
    const status = (error as { response?: { status?: number } })?.response?.status
    if (status === 404) {
      return (
        <div className="container py-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Series unavailable</AlertTitle>
            <AlertDescription>
              The series service could not be reached. Check that the backend is running (e.g. <code className="text-xs bg-muted px-1 rounded">uv run run_server.py</code>).
            </AlertDescription>
          </Alert>
        </div>
      )
    }
    return (
      <div className="container py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error loading series</AlertTitle>
          <AlertDescription>{String(error)}</AlertDescription>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </Alert>
      </div>
    )
  }

  const series = data?.items || []
  
  return (
    <div className="container py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Series</h1>
          <p className="text-muted-foreground">Manage your canonical and custom coin collections.</p>
        </div>
        <Button asChild>
          <Link to="/series/new">
            <Plus className="mr-2 h-4 w-4" />
            Create Series
          </Link>
        </Button>
      </div>
      
      {series.length === 0 ? (
        <Card className="flex flex-col items-center justify-center p-12 text-center">
          <LayoutGrid className="h-12 w-12 text-muted-foreground mb-4 opacity-20" />
          <h3 className="text-lg font-medium">No series created yet</h3>
          <p className="text-sm text-muted-foreground mb-6">Start by creating a custom series or using a template.</p>
          <Button asChild variant="outline">
            <Link to="/series/new">Create your first series</Link>
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {series.map((s) => (
            <SeriesCard key={s.id} series={s} />
          ))}
        </div>
      )}
    </div>
  )
}

function SeriesCard({ series }: { series: any }) {
  // Calculate completion
  const filledCount = series.slots?.filter((sl: any) => sl.status === 'filled').length || 0
  const targetCount = series.target_count || series.slots?.length || 0
  const progress = targetCount > 0 ? (filledCount / targetCount) * 100 : 0
  
  return (
    <Link to={`/series/${series.id}`}>
      <Card className="hover:border-primary transition-colors h-full">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-start">
            <CardTitle className="text-xl font-bold">{series.name}</CardTitle>
            <Badge variant="secondary" className="capitalize">
              {series.series_type.replace('_', ' ')}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">{filledCount} / {targetCount}</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
          
          <div className="flex gap-2">
            {series.is_complete && (
              <Badge className="bg-green-500 hover:bg-green-600">Completed</Badge>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
