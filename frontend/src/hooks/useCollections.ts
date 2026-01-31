/**
 * Collections Hooks
 *
 * TanStack Query hooks for managing coin collections.
 * Supports custom (manual) and smart (dynamic) collections with
 * hierarchical nesting and batch operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/api/api';
import type {
  Collection,
  CollectionCoin,
  CollectionStatistics,
  SmartCriteria,
} from '@/domain/schemas';

// =============================================================================
// Types
// =============================================================================

interface CollectionFilters {
  parent_id?: number | null;
  collection_type?: string;
  purpose?: string;
  include_hidden?: boolean;
  skip?: number;
  limit?: number;
}

interface CollectionListResponse {
  collections: Collection[];
  total: number;
  skip: number;
  limit: number;
}

interface CollectionCoinsResponse {
  collection_id: number;
  coins: CollectionCoin[];
  total: number;
  skip: number;
  limit: number;
}

interface CreateCollectionInput {
  name: string;
  description?: string | null;
  slug?: string | null;
  collection_type?: string;
  purpose?: string;
  smart_criteria?: SmartCriteria | null;
  is_type_set?: boolean;
  type_set_definition?: string | null;
  cover_image_url?: string | null;
  cover_coin_id?: number | null;
  color?: string | null;
  icon?: string | null;
  parent_id?: number | null;
  display_order?: number;
  default_sort?: string;
  default_view?: string | null;
  is_favorite?: boolean;
  storage_location?: string | null;
  notes?: string | null;
}

interface UpdateCollectionInput extends Partial<CreateCollectionInput> {
  is_hidden?: boolean;
  is_public?: boolean;
}

interface UpdateMembershipInput {
  notes?: string | null;
  is_featured?: boolean | null;
  is_placeholder?: boolean | null;
  position?: number | null;
  fulfills_type?: string | null;
  exclude_from_stats?: boolean | null;
}

// =============================================================================
// Query Keys
// =============================================================================

export const collectionKeys = {
  all: ['collections'] as const,
  lists: () => [...collectionKeys.all, 'list'] as const,
  list: (filters: CollectionFilters) => [...collectionKeys.lists(), filters] as const,
  tree: () => [...collectionKeys.all, 'tree'] as const,
  details: () => [...collectionKeys.all, 'detail'] as const,
  detail: (id: number) => [...collectionKeys.details(), id] as const,
  coins: (id: number) => [...collectionKeys.all, 'coins', id] as const,
  stats: (id: number) => [...collectionKeys.all, 'stats', id] as const,
  forCoin: (coinId: number) => [...collectionKeys.all, 'for-coin', coinId] as const,
};

// =============================================================================
// Collection CRUD Hooks
// =============================================================================

/**
 * Fetch paginated list of collections with optional filters.
 */
export function useCollections(filters: CollectionFilters = {}) {
  return useQuery({
    queryKey: collectionKeys.list(filters),
    queryFn: async (): Promise<CollectionListResponse> => {
      const params = new URLSearchParams();
      if (filters.parent_id !== undefined) {
        params.set('parent_id', filters.parent_id === null ? '' : String(filters.parent_id));
      }
      if (filters.collection_type) params.set('collection_type', filters.collection_type);
      if (filters.purpose) params.set('purpose', filters.purpose);
      if (filters.include_hidden) params.set('include_hidden', 'true');
      if (filters.skip) params.set('skip', String(filters.skip));
      if (filters.limit) params.set('limit', String(filters.limit));

      const response = await api.get(`/api/v2/collections?${params.toString()}`);
      return response.data;
    },
  });
}

/**
 * Fetch collection tree (all collections in hierarchical order).
 */
export function useCollectionTree() {
  return useQuery({
    queryKey: collectionKeys.tree(),
    queryFn: async (): Promise<Collection[]> => {
      const response = await api.get('/api/v2/collections/tree');
      return response.data;
    },
  });
}

/**
 * Fetch a single collection by ID.
 */
export function useCollection(id: number | undefined) {
  return useQuery({
    queryKey: collectionKeys.detail(id!),
    queryFn: async (): Promise<Collection> => {
      const response = await api.get(`/api/v2/collections/${id}`);
      return response.data;
    },
    enabled: id !== undefined,
  });
}

/**
 * Create a new collection.
 */
export function useCreateCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: CreateCollectionInput): Promise<Collection> => {
      const response = await api.post('/api/v2/collections', input);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.all });
    },
  });
}

/**
 * Update an existing collection.
 */
export function useUpdateCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      ...input
    }: UpdateCollectionInput & { id: number }): Promise<Collection> => {
      const response = await api.put(`/api/v2/collections/${id}`, input);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.lists() });
      queryClient.invalidateQueries({ queryKey: collectionKeys.tree() });
    },
  });
}

/**
 * Delete a collection.
 */
export function useDeleteCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      promoteChildren = true,
    }: {
      id: number;
      promoteChildren?: boolean;
    }): Promise<void> => {
      await api.delete(`/api/v2/collections/${id}?promote_children=${promoteChildren}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.all });
    },
  });
}

// =============================================================================
// Coin Membership Hooks
// =============================================================================

/**
 * Get coins in a collection with membership details.
 */
export function useCollectionCoins(collectionId: number | undefined, skip = 0, limit = 50) {
  return useQuery({
    queryKey: collectionKeys.coins(collectionId!),
    queryFn: async (): Promise<CollectionCoinsResponse> => {
      const response = await api.get(
        `/api/v2/collections/${collectionId}/coins?skip=${skip}&limit=${limit}`
      );
      return response.data;
    },
    enabled: collectionId !== undefined,
  });
}

/**
 * Add coins to a collection (batch operation).
 */
export function useAddCoinsToCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      collectionId,
      coinIds,
    }: {
      collectionId: number;
      coinIds: number[];
    }): Promise<{ added: number; collection_id: number }> => {
      const response = await api.post(`/api/v2/collections/${collectionId}/coins`, {
        coin_ids: coinIds,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.coins(variables.collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(variables.collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.stats(variables.collectionId) });
      // Invalidate for-coin queries for all added coins
      variables.coinIds.forEach((coinId) => {
        queryClient.invalidateQueries({ queryKey: collectionKeys.forCoin(coinId) });
      });
    },
  });
}

/**
 * Remove a coin from a collection.
 */
export function useRemoveCoinFromCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      collectionId,
      coinId,
    }: {
      collectionId: number;
      coinId: number;
    }): Promise<void> => {
      await api.delete(`/api/v2/collections/${collectionId}/coins/${coinId}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.coins(variables.collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(variables.collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.stats(variables.collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.forCoin(variables.coinId) });
    },
  });
}

/**
 * Update a coin's membership details in a collection.
 */
export function useUpdateCoinMembership() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      collectionId,
      coinId,
      ...input
    }: UpdateMembershipInput & {
      collectionId: number;
      coinId: number;
    }): Promise<CollectionCoin> => {
      const response = await api.put(
        `/api/v2/collections/${collectionId}/coins/${coinId}`,
        input
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.coins(variables.collectionId) });
    },
  });
}

/**
 * Reorder coins within a collection.
 */
export function useReorderCollectionCoins() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      collectionId,
      coinOrder,
    }: {
      collectionId: number;
      coinOrder: number[];
    }): Promise<{ success: boolean }> => {
      const response = await api.put(`/api/v2/collections/${collectionId}/coins/order`, {
        coin_order: coinOrder,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.coins(variables.collectionId) });
    },
  });
}

// =============================================================================
// Statistics Hooks
// =============================================================================

/**
 * Get statistics for a collection.
 */
export function useCollectionStats(collectionId: number | undefined) {
  return useQuery({
    queryKey: collectionKeys.stats(collectionId!),
    queryFn: async (): Promise<CollectionStatistics> => {
      const response = await api.get(`/api/v2/collections/${collectionId}/stats`);
      return response.data;
    },
    enabled: collectionId !== undefined,
  });
}

/**
 * Refresh cached statistics for a collection.
 */
export function useRefreshCollectionStats() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (collectionId: number): Promise<{ success: boolean }> => {
      const response = await api.post(`/api/v2/collections/${collectionId}/refresh-stats`);
      return response.data;
    },
    onSuccess: (_, collectionId) => {
      queryClient.invalidateQueries({ queryKey: collectionKeys.stats(collectionId) });
      queryClient.invalidateQueries({ queryKey: collectionKeys.detail(collectionId) });
    },
  });
}

// =============================================================================
// Reverse Lookup Hooks
// =============================================================================

/**
 * Get all collections containing a specific coin.
 */
export function useCollectionsForCoin(coinId: number | undefined) {
  return useQuery({
    queryKey: collectionKeys.forCoin(coinId!),
    queryFn: async (): Promise<Collection[]> => {
      const response = await api.get(`/api/v2/collections/by-coin/${coinId}`);
      return response.data;
    },
    enabled: coinId !== undefined,
  });
}
