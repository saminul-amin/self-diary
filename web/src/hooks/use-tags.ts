import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import type { Tag } from '@/types/api';

export function useTags() {
  return useQuery({
    queryKey: ['tags'],
    queryFn: async (): Promise<Tag[]> => {
      const res = await apiClient.get('/tags');
      return res.data.data;
    },
  });
}

export function useTag(id: string | undefined) {
  return useQuery({
    queryKey: ['tags', id],
    queryFn: async (): Promise<Tag> => {
      const res = await apiClient.get(`/tags/${id}`);
      return res.data.data;
    },
    enabled: !!id,
  });
}

interface CreateTagInput {
  name: string;
  color?: string | null;
}

export function useCreateTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateTagInput): Promise<Tag> => {
      const res = await apiClient.post('/tags', input);
      return res.data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tags'] });
    },
  });
}

interface UpdateTagInput {
  id: string;
  name?: string;
  color?: string | null;
}

export function useUpdateTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...input }: UpdateTagInput): Promise<Tag> => {
      const res = await apiClient.put(`/tags/${id}`, input);
      return res.data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tags'] });
    },
  });
}

export function useDeleteTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await apiClient.delete(`/tags/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tags'] });
      qc.invalidateQueries({ queryKey: ['entries'] });
    },
  });
}
