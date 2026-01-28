import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { ArrowLeft, Check, X, Loader2, RefreshCw, ExternalLink } from "lucide-react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { api } from "@/lib/api"

interface ReviewQueueItem {
  id: number
  coin_id: number
  field_name: string
  raw_value: string
  vocab_term_id: number | null
  confidence: number | null
  method: string | null
  suggested_name: string | null
}

export function ReviewQueuePage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState("pending_review")
  
  // Fetch review queue
  const { data: items, isLoading, refetch } = useQuery({
    queryKey: ['vocab', 'review', statusFilter],
    queryFn: async () => {
      const response = await api.get('/api/v2/vocab/review', {
        params: { status: statusFilter, limit: 100 }
      })
      return response.data as ReviewQueueItem[]
    },
  })
  
  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await api.post(`/api/v2/vocab/review/${id}/approve`, {})
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vocab', 'review'] })
      toast.success("Assignment approved")
    },
    onError: (err: Error) => {
      toast.error(err?.message ?? "Failed to approve")
    },
  })

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await api.post(`/api/v2/vocab/review/${id}/reject`, {})
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vocab', 'review'] })
      toast.success("Assignment rejected")
    },
    onError: (err: Error) => {
      toast.error(err?.message ?? "Failed to reject")
    },
  })
  
  const getConfidenceBadge = (confidence: number | null) => {
    if (confidence === null) return <Badge variant="outline">Unknown</Badge>
    if (confidence >= 0.92) return <Badge variant="default" className="bg-green-500">High ({(confidence * 100).toFixed(0)}%)</Badge>
    if (confidence >= 0.80) return <Badge variant="secondary" className="bg-yellow-500">Medium ({(confidence * 100).toFixed(0)}%)</Badge>
    return <Badge variant="destructive">Low ({(confidence * 100).toFixed(0)}%)</Badge>
  }
  
  const getMethodBadge = (method: string | null) => {
    if (!method) return null
    const variants: Record<string, string> = {
      'exact': 'bg-green-100 text-green-800',
      'exact_ci': 'bg-green-100 text-green-800',
      'fts': 'bg-blue-100 text-blue-800',
      'nomisma': 'bg-purple-100 text-purple-800',
      'llm': 'bg-orange-100 text-orange-800',
      'manual': 'bg-gray-100 text-gray-800',
    }
    return (
      <Badge variant="outline" className={variants[method] || ''}>
        {method.toUpperCase()}
      </Badge>
    )
  }

  return (
    <div className="container py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/settings">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">Review Queue</h1>
          <p className="text-sm text-muted-foreground">
            Review and approve vocabulary assignments
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Pending Assignments</CardTitle>
              <CardDescription>
                These vocabulary assignments need your review
              </CardDescription>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pending_review">Pending Review</SelectItem>
                <SelectItem value="assigned">Assigned</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : items && items.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No items in the review queue.</p>
              <p className="text-sm mt-1">Run bulk normalization from the Collection page to populate.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Coin</TableHead>
                  <TableHead>Field</TableHead>
                  <TableHead>Raw Value</TableHead>
                  <TableHead>Suggested</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items?.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Link 
                        to={`/coins/${item.coin_id}`}
                        className="flex items-center gap-1 text-primary hover:underline"
                      >
                        #{item.coin_id}
                        <ExternalLink className="h-3 w-3" />
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {item.field_name}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate font-mono text-sm">
                      {item.raw_value}
                    </TableCell>
                    <TableCell className="font-medium">
                      {item.suggested_name || <span className="text-muted-foreground">None</span>}
                    </TableCell>
                    <TableCell>
                      {getConfidenceBadge(item.confidence)}
                    </TableCell>
                    <TableCell>
                      {getMethodBadge(item.method)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="min-h-[44px] min-w-[44px] h-11 w-11 hover:opacity-90 [color:var(--text-success)] hover:bg-[var(--bg-success)]"
                          onClick={() => approveMutation.mutate(item.id)}
                          disabled={approveMutation.isPending || rejectMutation.isPending}
                          title="Approve"
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="min-h-[44px] min-w-[44px] h-11 w-11 hover:opacity-90 [color:var(--text-error)] hover:bg-[var(--bg-error)]"
                          onClick={() => rejectMutation.mutate(item.id)}
                          disabled={approveMutation.isPending || rejectMutation.isPending}
                          title="Reject"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
