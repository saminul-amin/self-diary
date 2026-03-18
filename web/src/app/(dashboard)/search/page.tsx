'use client';

import { useState } from 'react';
import EntryCard from '@/components/entries/entry-card';
import { useSearchEntries } from '@/hooks/use-entries';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const { data, isLoading } = useSearchEntries(query);
  const entries = data?.data ?? [];

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Search</h1>

      <div className="relative mb-6">
        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">🔍</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search your entries…"
          className="block w-full rounded-lg border border-gray-300 py-3 pl-10 pr-4 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      {query.length < 2 ? (
        <div className="text-center py-12 text-gray-400">Type at least 2 characters to search</div>
      ) : isLoading ? (
        <div className="text-center py-12 text-gray-400">Searching…</div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No entries match &quot;{query}&quot;</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {entries.map((entry) => (
            <EntryCard key={entry.id} entry={entry} />
          ))}
        </div>
      )}
    </div>
  );
}
