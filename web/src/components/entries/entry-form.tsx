'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/ui/button';
import Input from '@/components/ui/input';
import MoodSelector from '@/components/entries/mood-selector';
import TagPicker from '@/components/tags/tag-picker';
import { useTags } from '@/hooks/use-tags';
import { useCreateEntry, useUpdateEntry } from '@/hooks/use-entries';
import type { Entry, Mood } from '@/types/api';

interface EntryFormProps {
  entry?: Entry;
}

export default function EntryForm({ entry }: EntryFormProps) {
  const router = useRouter();
  const { data: tags } = useTags();
  const createEntry = useCreateEntry();
  const updateEntry = useUpdateEntry();

  const [title, setTitle] = useState(entry?.title ?? '');
  const [body, setBody] = useState(entry?.body ?? '');
  const [mood, setMood] = useState<Mood | null>(entry?.mood ?? null);
  const [isFavorite, setIsFavorite] = useState(entry?.is_favorite ?? false);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>(
    entry?.tags.map((t) => t.id) ?? [],
  );
  const [error, setError] = useState('');

  useEffect(() => {
    if (entry) {
      setTitle(entry.title ?? '');
      setBody(entry.body);
      setMood(entry.mood);
      setIsFavorite(entry.is_favorite);
      setSelectedTagIds(entry.tags.map((t) => t.id));
    }
  }, [entry]);

  const isSubmitting = createEntry.isPending || updateEntry.isPending;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!body.trim()) {
      setError('Entry body is required.');
      return;
    }

    const payload = {
      title: title.trim() || undefined,
      body: body.trim(),
      mood,
      is_favorite: isFavorite,
      tag_ids: selectedTagIds,
    };

    try {
      if (entry) {
        await updateEntry.mutateAsync({ id: entry.id, ...payload });
      } else {
        await createEntry.mutateAsync(payload);
      }
      router.push('/entries');
    } catch {
      setError('Failed to save entry. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <Input
        label="Title"
        placeholder="Give your entry a title (optional)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Entry</label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={8}
          className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="Write your thoughts…"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Mood</label>
        <MoodSelector value={mood} onChange={setMood} />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
        <TagPicker allTags={tags ?? []} selectedIds={selectedTagIds} onChange={setSelectedTagIds} />
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setIsFavorite(!isFavorite)}
          className={`text-xl transition-colors ${isFavorite ? 'text-amber-500' : 'text-gray-300 hover:text-amber-400'}`}
        >
          ★
        </button>
        <span className="text-sm text-gray-600">Mark as favorite</span>
      </div>

      <div className="flex gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : entry ? 'Update Entry' : 'Create Entry'}
        </Button>
        <Button type="button" variant="secondary" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
