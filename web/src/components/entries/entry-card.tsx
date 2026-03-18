import Link from 'next/link';
import { cn, formatDate, moodEmoji, moodColor } from '@/lib/utils';
import TagBadge from '@/components/tags/tag-badge';
import type { Entry } from '@/types/api';

interface EntryCardProps {
  entry: Entry;
}

export default function EntryCard({ entry }: EntryCardProps) {
  return (
    <Link
      href={`/entries/${entry.id}`}
      className="block rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-gray-900 truncate">
            {entry.title || 'Untitled'}
          </h3>
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">{entry.body}</p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {entry.mood && (
            <span
              className={cn('rounded-full px-2 py-0.5 text-xs font-medium', moodColor[entry.mood])}
            >
              {moodEmoji[entry.mood]} {entry.mood}
            </span>
          )}
          {entry.is_favorite && <span className="text-amber-500 text-sm">★</span>}
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <div className="flex flex-wrap gap-1">
          {entry.tags.slice(0, 3).map((tag) => (
            <TagBadge key={tag.id} tag={tag} />
          ))}
          {entry.tags.length > 3 && (
            <span className="text-xs text-gray-400">+{entry.tags.length - 3}</span>
          )}
        </div>
        <time className="text-xs text-gray-400">{formatDate(entry.created_at)}</time>
      </div>
    </Link>
  );
}
