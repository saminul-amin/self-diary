import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { enqueueOfflineEntry } from '@/lib/offline-storage';
import { isOnline } from '@/lib/network-status';
import type { Entry, Mood } from '@/types/api';

interface EntryListParams {
  page?: number;
  per_page?: number;
  mood?: Mood;
  is_favorite?: boolean;
  tag_id?: string;
}

interface EntryListResponse {
  data: Entry[];
  meta: { page: number; per_page: number; total: number } | null;
}

export function useEntries(params: EntryListParams = {}) {
  return useQuery({
    queryKey: ['entries', params],
    queryFn: async (): Promise<EntryListResponse> => {
      const searchParams = new URLSearchParams();
      if (params.page) searchParams.set('page', String(params.page));
      if (params.per_page) searchParams.set('per_page', String(params.per_page));
      if (params.mood) searchParams.set('mood', params.mood);
      if (params.is_favorite) searchParams.set('is_favorite', 'true');
      if (params.tag_id) searchParams.set('tag_id', params.tag_id);
      const res = await apiClient.get(`/entries?${searchParams.toString()}`);
      return res.data;
    },
  });
}

export function useEntry(id: string | undefined) {
  return useQuery({
    queryKey: ['entries', id],
    queryFn: async (): Promise<Entry> => {
      const res = await apiClient.get(`/entries/${id}`);
      return res.data.data;
    },
    enabled: !!id,
  });
}

interface CreateEntryInput {
  title?: string;
  body: string;
  mood?: Mood | null;
  is_favorite?: boolean;
  tag_ids?: string[];
}

/**
 * Create entry — falls back to offline queue when there is no network.
 * Generates a client_id UUID for idempotent server-side dedup.
 */
export function useCreateEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateEntryInput): Promise<Entry | null> => {
      const clientId = crypto.randomUUID();

      const online = await isOnline();
      if (!online) {
        await enqueueOfflineEntry({
          id: clientId,
          action: 'create',
          payload: {
            title: input.title,
            body: input.body,
            mood: input.mood,
            is_favorite: input.is_favorite,
            tag_ids: input.tag_ids,
            client_id: clientId,
          },
          queued_at: new Date().toISOString(),
          attempts: 0,
        });
        return null; // queued for later
      }

      const res = await apiClient.post('/entries', {
        ...input,
        client_id: clientId,
      });
      return res.data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['entries'] });
    },
  });
}

interface UpdateEntryInput extends CreateEntryInput {
  id: string;
  expected_version?: number;
}

/**
 * Update entry — falls back to offline queue when there is no network.
 * Sends expected_version for optimistic concurrency.
 */
export function useUpdateEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      expected_version,
      ...input
    }: UpdateEntryInput): Promise<Entry | null> => {
      const online = await isOnline();
      if (!online) {
        await enqueueOfflineEntry({
          id,
          action: 'update',
          payload: {
            title: input.title,
            body: input.body,
            mood: input.mood,
            is_favorite: input.is_favorite,
            tag_ids: input.tag_ids,
            expected_version,
          },
          queued_at: new Date().toISOString(),
          attempts: 0,
        });
        return null; // queued for later
      }

      const res = await apiClient.put(`/entries/${id}`, {
        ...input,
        expected_version,
      });
      return res.data.data;
    },
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['entries'] });
      qc.invalidateQueries({ queryKey: ['entries', variables.id] });
    },
  });
}

export function useDeleteEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await apiClient.delete(`/entries/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['entries'] });
    },
  });
}

export function useSearchEntries(query: string) {
  return useQuery({
    queryKey: ['entries', 'search', query],
    queryFn: async (): Promise<EntryListResponse> => {
      const res = await apiClient.get(`/entries/search?q=${encodeURIComponent(query)}`);
      return res.data;
    },
    enabled: query.length >= 2,
  });
}
