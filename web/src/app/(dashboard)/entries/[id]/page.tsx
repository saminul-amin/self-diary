'use client';

import { use } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/ui/button';
import EntryForm from '@/components/entries/entry-form';
import { useEntry, useDeleteEntry } from '@/hooks/use-entries';
import { formatDateTime, moodEmoji } from '@/lib/utils';

export default function EntryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { data: entry, isLoading } = useEntry(id);
  const deleteEntry = useDeleteEntry();

  const handleDelete = async () => {
    if (!confirm('Delete this entry? This cannot be undone.')) return;
    await deleteEntry.mutateAsync(id);
    router.push('/entries');
  };

  if (isLoading) {
    return <div className="text-center py-12 text-gray-400">Loading…</div>;
  }

  if (!entry) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">Entry not found.</p>
        <Button variant="secondary" onClick={() => router.push('/entries')}>
          Back to entries
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {entry.title || 'Untitled'}
            {entry.mood && <span className="ml-2">{moodEmoji[entry.mood]}</span>}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {formatDateTime(entry.created_at)}
            {entry.is_favorite && <span className="ml-2 text-amber-500">★</span>}
          </p>
        </div>
        <Button variant="danger" size="sm" onClick={handleDelete}>
          Delete
        </Button>
      </div>
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
        <EntryForm entry={entry} />
      </div>
    </div>
  );
}
