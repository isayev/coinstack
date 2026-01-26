import { useMutation } from "@tanstack/react-query";
import api from "@/api/api";
import { LegendExpansionRequest, LegendExpansionResponse } from "@/domain/schemas";

export function useExpandLegend() {
  return useMutation({
    mutationFn: async (request: LegendExpansionRequest) => {
      const response = await api.post<{ expanded: string; confidence: number }>(
        "/api/v2/llm/legend/expand",
        { abbreviation: request.text }
      );
      // Map V2 response to expected frontend interface
      return {
        original: request.text,
        expanded: response.data.expanded,
        confidence: response.data.confidence,
        tokens: [] // V2 doesn't return tokens yet
      } as LegendExpansionResponse;
    },
  });
}

export function useLookupAbbreviation() {
  return useMutation({
    mutationFn: async (abbreviation: string) => {
      const response = await api.get<{
        abbreviation: string;
        expansion: string | null;
        found: boolean;
      }>(`/api/legend/lookup/${encodeURIComponent(abbreviation)}`);
      return response.data;
    },
  });
}

export function useSearchAbbreviations() {
  return useMutation({
    mutationFn: async (query: string) => {
      const response = await api.get<{
        query: string;
        results: Array<{ abbreviation: string; expansion: string }>;
        count: number;
      }>(`/api/legend/search?q=${encodeURIComponent(query)}`);
      return response.data;
    },
  });
}