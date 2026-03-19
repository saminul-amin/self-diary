import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
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

export function useCreateEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateEntryInput): Promise<Entry> => {
      const res = await apiClient.post('/entries', input);
      return res.data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['entries'] });
    },
  });
}

interface UpdateEntryInput extends CreateEntryInput {
  id: string;
}

export function useUpdateEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...input }: UpdateEntryInput): Promise<Entry> => {
      const res = await apiClient.put(`/entries/${id}`, input);
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
