'use client';

import { useState } from 'react';
import Link from 'next/link';
import Button from '@/components/ui/button';
import EntryCard from '@/components/entries/entry-card';
import MoodSelector from '@/components/entries/mood-selector';
import { useEntries } from '@/hooks/use-entries';
import type { Mood } from '@/types/api';

export default function EntriesPage() {
  const [page, setPage] = useState(1);
  const [mood, setMood] = useState<Mood | null>(null);
  const [favOnly, setFavOnly] = useState(false);

  const { data, isLoading } = useEntries({
    page,
    per_page: 12,
    mood: mood ?? undefined,
    is_favorite: favOnly || undefined,
  });

  const entries = data?.data ?? [];
  const meta = data?.meta;
  const totalPages = meta ? Math.ceil(meta.total / meta.per_page) : 1;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Entries</h1>
        <Link href="/entries/new">
          <Button>+ New Entry</Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-3">
        <div className="flex items-center gap-4 flex-wrap">
          <MoodSelector value={mood} onChange={setMood} />
          <button
            type="button"
            onClick={() => setFavOnly(!favOnly)}
            className={`flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              favOnly ? 'bg-amber-100 text-amber-700' : 'bg-gray-50 text-gray-500 hover:bg-gray-100'
            }`}
          >
            ★ Favorites
          </button>
        </div>
      </div>

      {/* List */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No entries yet.</p>
          <Link href="/entries/new">
            <Button>Write your first entry</Button>
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {entries.map((entry) => (
            <EntryCard key={entry.id} entry={entry} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
