import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { client, Discrepancy } from "@/api/client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, CheckCircle2, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

interface AuditPanelProps {
  coinId: number
}

export function AuditPanel({ coinId }: AuditPanelProps) {
  const queryClient = useQueryClient()
  const { data: audit, isLoading } = useQuery({
    queryKey: ['audit', coinId],
    queryFn: () => client.auditCoin(coinId)
  })

  const applyMutation = useMutation({
    mutationFn: ({ field, value }: { field: string, value: string }) =>
      client.applyEnrichment(coinId, field, value),
    onSuccess: () => {
      toast.success("Data updated successfully")
      queryClient.invalidateQueries({ queryKey: ['audit', coinId] })
      queryClient.invalidateQueries({ queryKey: ['coin', coinId] })
    },
    onError: (error) => {
      toast.error(`Failed to update: ${error.message}`)
    }
  })

  if (isLoading) return <div>Running audit...</div>

  if (!audit || !audit.has_issues) {
    return (
      <div className="flex items-center gap-2 p-4 bg-primary/10 text-primary rounded-lg border border-primary/20">
        <CheckCircle2 className="w-5 h-5" />
        <span className="font-medium">No discrepancies found with external auction data.</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive rounded-lg border border-destructive/20">
        <AlertTriangle className="w-5 h-5" />
        <span className="font-medium">{audit.discrepancies.length} discrepancies detected.</span>
      </div>

      <div className="grid gap-4">
        {audit.discrepancies.map((d, i) => (
          <DiscrepancyCard
            key={i}
            discrepancy={d}
            onApply={() => applyMutation.mutate({ field: d.field, value: d.auction_value })}
            isApplying={applyMutation.isPending}
          />
        ))}
      </div>
    </div>
  )
}

function DiscrepancyCard({
  discrepancy,
  onApply,
  isApplying
}: {
  discrepancy: Discrepancy,
  onApply: () => void,
  isApplying: boolean
}) {
  return (
    <Card className="border-l-4 border-l-destructive">
      <CardHeader className="py-3 px-4 flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
          {discrepancy.field.replace('_', ' ')}
        </CardTitle>
        <Badge variant="outline" className="text-[10px]">Source: {discrepancy.source}</Badge>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1">
            <p className="text-xs text-muted-foreground mb-1">Your Data</p>
            <div className="p-2 bg-muted rounded font-mono text-sm line-through opacity-50">
              {discrepancy.current_value}
            </div>
          </div>

          <ArrowRight className="w-4 h-4 text-muted-foreground mt-4" />

          <div className="flex-1">
            <p className="text-xs text-destructive font-medium mb-1">Auction Data</p>
            <div className="p-2 bg-destructive/10 border border-destructive/20 rounded font-mono text-sm font-bold text-destructive">
              {discrepancy.auction_value}
            </div>
          </div>
        </div>

        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline" size="sm" className="h-8 text-xs">Ignore</Button>
          <Button
            variant="default"
            size="sm"
            className="h-8 text-xs bg-destructive hover:bg-destructive/90"
            onClick={onApply}
            disabled={isApplying}
          >
            {isApplying ? "Updating..." : "Fix / Apply"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
