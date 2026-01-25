import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { v2 } from "@/api/v2"
import { Series } from "@/domain/schemas"

export function useSeries() {
  return useQuery({
    queryKey: ["series"],
    queryFn: v2.getSeries
  })
}

export function useSeriesDetail(id: number) {
  return useQuery({
    queryKey: ["series", id],
    queryFn: () => v2.getSeriesDetail(id),
    enabled: !!id
  })
}

export function useCreateSeries() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: v2.createSeries,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["series"] })
    }
  })
}

export function useAddCoinToSeries() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ seriesId, coinId, slotId }: { seriesId: number; coinId: number; slotId?: number }) => 
      v2.addCoinToSeries(seriesId, coinId, slotId),
    onSuccess: (_, { seriesId }) => {
      queryClient.invalidateQueries({ queryKey: ["series", seriesId] })
    }
  })
}