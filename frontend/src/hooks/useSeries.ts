import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { client } from "@/api/client"

export function useSeries() {
  return useQuery({
    queryKey: ["series"],
    queryFn: client.getSeries
  })
}

export function useSeriesDetail(id: number) {
  return useQuery({
    queryKey: ["series", id],
    queryFn: () => client.getSeriesDetail(id),
    enabled: !!id
  })
}

export function useCreateSeries() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: client.createSeries,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["series"] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Create series failed:', error.message)
      }
    },
  })
}

export function useAddCoinToSeries() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ seriesId, coinId, slotId }: { seriesId: number; coinId: number; slotId?: number }) =>
      client.addCoinToSeries(seriesId, coinId, slotId),
    onSuccess: (_, { seriesId }) => {
      queryClient.invalidateQueries({ queryKey: ["series", seriesId] })
    },
    onError: (error: Error) => {
      if (import.meta.env.DEV) {
        console.error('Add coin to series failed:', error.message)
      }
    },
  })
}