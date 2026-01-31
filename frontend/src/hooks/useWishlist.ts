/**
 * Wishlist management hooks for Phase 5.
 *
 * Provides TanStack Query hooks for:
 * - Wishlist items (acquisition targets)
 * - Wishlist matches (matched lots)
 * - Price alerts
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  WishlistItem,
  WishlistMatch,
  PriceAlert
} from "@/domain/schemas";

// =============================================================================
// API Types
// =============================================================================

interface WishlistItemFilters {
  status?: string;
  priority?: number;
  category?: string;
  skip?: number;
  limit?: number;
}

interface WishlistItemListResponse {
  items: WishlistItem[];
  total: number;
  skip: number;
  limit: number;
}

interface WishlistMatchListResponse {
  wishlist_item_id: number;
  matches: WishlistMatch[];
  total: number;
}

interface PriceAlertFilters {
  status?: string;
  trigger_type?: string;
  skip?: number;
  limit?: number;
}

interface PriceAlertListResponse {
  alerts: PriceAlert[];
  total: number;
  skip: number;
  limit: number;
}

interface MarkAcquiredRequest {
  coin_id: number;
  acquired_price?: number;
}

type WishlistItemCreate = Omit<WishlistItem, 'id' | 'created_at' | 'updated_at' | 'acquired_coin_id' | 'acquired_at' | 'acquired_price' | 'status'>;
type WishlistItemUpdate = Partial<WishlistItemCreate> & { status?: string };
type WishlistMatchCreate = Omit<WishlistMatch, 'id' | 'wishlist_item_id' | 'created_at' | 'notified' | 'notified_at' | 'dismissed' | 'dismissed_at' | 'saved'>;
type WishlistMatchUpdate = Partial<WishlistMatchCreate>;
type PriceAlertCreate = Omit<PriceAlert, 'id' | 'created_at' | 'triggered_at' | 'notification_sent' | 'notification_sent_at' | 'last_triggered_at' | 'status'>;
type PriceAlertUpdate = Partial<PriceAlertCreate> & { status?: string };

// =============================================================================
// API Client Functions
// =============================================================================

const API_BASE = "/api/v2";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// =============================================================================
// Wishlist Item Hooks
// =============================================================================

export function useWishlistItems(filters: WishlistItemFilters = {}) {
  const { status, priority, category, skip = 0, limit = 100 } = filters;

  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (priority !== undefined) params.set("priority", String(priority));
  if (category) params.set("category", category);
  params.set("skip", String(skip));
  params.set("limit", String(limit));

  return useQuery<WishlistItemListResponse>({
    queryKey: ["wishlist-items", filters],
    queryFn: () => fetchJson(`${API_BASE}/wishlist?${params}`),
  });
}

export function useWishlistItem(itemId: number) {
  return useQuery<WishlistItem>({
    queryKey: ["wishlist-item", itemId],
    queryFn: () => fetchJson(`${API_BASE}/wishlist/${itemId}`),
    enabled: !!itemId,
  });
}

export function useCreateWishlistItem() {
  const queryClient = useQueryClient();

  return useMutation<WishlistItem, Error, WishlistItemCreate>({
    mutationFn: (data) => fetchJson(`${API_BASE}/wishlist`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist-items"] });
    },
  });
}

export function useUpdateWishlistItem() {
  const queryClient = useQueryClient();

  return useMutation<WishlistItem, Error, { id: number; data: WishlistItemUpdate }>({
    mutationFn: ({ id, data }) => fetchJson(`${API_BASE}/wishlist/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["wishlist-items"] });
      queryClient.invalidateQueries({ queryKey: ["wishlist-item", id] });
    },
  });
}

export function useDeleteWishlistItem() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: (id) => fetchJson(`${API_BASE}/wishlist/${id}`, {
      method: "DELETE",
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist-items"] });
    },
  });
}

export function useMarkAcquired() {
  const queryClient = useQueryClient();

  return useMutation<WishlistItem, Error, { itemId: number; data: MarkAcquiredRequest }>({
    mutationFn: ({ itemId, data }) => fetchJson(`${API_BASE}/wishlist/${itemId}/mark-acquired`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
    onSuccess: (_, { itemId }) => {
      queryClient.invalidateQueries({ queryKey: ["wishlist-items"] });
      queryClient.invalidateQueries({ queryKey: ["wishlist-item", itemId] });
    },
  });
}

// =============================================================================
// Wishlist Match Hooks
// =============================================================================

export function useWishlistMatches(itemId: number, includeDismissed: boolean = false) {
  const params = new URLSearchParams();
  params.set("include_dismissed", String(includeDismissed));

  return useQuery<WishlistMatchListResponse>({
    queryKey: ["wishlist-matches", itemId, includeDismissed],
    queryFn: () => fetchJson(`${API_BASE}/wishlist/${itemId}/matches?${params}`),
    enabled: !!itemId,
  });
}

export function useCreateWishlistMatch() {
  const queryClient = useQueryClient();

  return useMutation<WishlistMatch, Error, { itemId: number; data: WishlistMatchCreate }>({
    mutationFn: ({ itemId, data }) => fetchJson(`${API_BASE}/wishlist/${itemId}/matches`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
    onSuccess: (_, { itemId }) => {
      queryClient.invalidateQueries({ queryKey: ["wishlist-matches", itemId] });
    },
  });
}

export function useUpdateWishlistMatch() {
  const queryClient = useQueryClient();

  return useMutation<WishlistMatch, Error, { matchId: number; data: WishlistMatchUpdate }>({
    mutationFn: ({ matchId, data }) => fetchJson(`${API_BASE}/wishlist/matches/${matchId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["wishlist-matches", result.wishlist_item_id] });
    },
  });
}

export function useDismissMatch() {
  const queryClient = useQueryClient();

  return useMutation<WishlistMatch, Error, number>({
    mutationFn: (matchId) => fetchJson(`${API_BASE}/wishlist/matches/${matchId}/dismiss`, {
      method: "POST",
    }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["wishlist-matches", result.wishlist_item_id] });
    },
  });
}

export function useSaveMatch() {
  const queryClient = useQueryClient();

  return useMutation<WishlistMatch, Error, number>({
    mutationFn: (matchId) => fetchJson(`${API_BASE}/wishlist/matches/${matchId}/save`, {
      method: "POST",
    }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["wishlist-matches", result.wishlist_item_id] });
    },
  });
}

// =============================================================================
// Price Alert Hooks
// =============================================================================

export function usePriceAlerts(filters: PriceAlertFilters = {}) {
  const { status, trigger_type, skip = 0, limit = 100 } = filters;

  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (trigger_type) params.set("trigger_type", trigger_type);
  params.set("skip", String(skip));
  params.set("limit", String(limit));

  return useQuery<PriceAlertListResponse>({
    queryKey: ["price-alerts", filters],
    queryFn: () => fetchJson(`${API_BASE}/price-alerts?${params}`),
  });
}

export function usePriceAlert(alertId: number) {
  return useQuery<PriceAlert>({
    queryKey: ["price-alert", alertId],
    queryFn: () => fetchJson(`${API_BASE}/price-alerts/${alertId}`),
    enabled: !!alertId,
  });
}

export function useCreatePriceAlert() {
  const queryClient = useQueryClient();

  return useMutation<PriceAlert, Error, PriceAlertCreate>({
    mutationFn: (data) => fetchJson(`${API_BASE}/price-alerts`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["price-alerts"] });
    },
  });
}

export function useUpdatePriceAlert() {
  const queryClient = useQueryClient();

  return useMutation<PriceAlert, Error, { id: number; data: PriceAlertUpdate }>({
    mutationFn: ({ id, data }) => fetchJson(`${API_BASE}/price-alerts/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["price-alerts"] });
      queryClient.invalidateQueries({ queryKey: ["price-alert", id] });
    },
  });
}

export function useDeletePriceAlert() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: (id) => fetchJson(`${API_BASE}/price-alerts/${id}`, {
      method: "DELETE",
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["price-alerts"] });
    },
  });
}

export function useTriggerPriceAlert() {
  const queryClient = useQueryClient();

  return useMutation<PriceAlert, Error, number>({
    mutationFn: (id) => fetchJson(`${API_BASE}/price-alerts/${id}/trigger`, {
      method: "POST",
    }),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["price-alerts"] });
      queryClient.invalidateQueries({ queryKey: ["price-alert", id] });
    },
  });
}
