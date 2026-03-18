/**
 * Shared utility helpers.
 */

/** Format an ISO date string for display. */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/** Format an ISO date string with time. */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Combine Tailwind class names, filtering out falsy values. */
export function cn(...classes: (string | false | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}

/** Mood to emoji mapping. */
export const moodEmoji: Record<string, string> = {
  great: '😄',
  good: '🙂',
  neutral: '😐',
  bad: '😞',
  terrible: '😢',
};

/** Mood to color mapping for badges. */
export const moodColor: Record<string, string> = {
  great: 'bg-green-100 text-green-800',
  good: 'bg-blue-100 text-blue-800',
  neutral: 'bg-gray-100 text-gray-800',
  bad: 'bg-orange-100 text-orange-800',
  terrible: 'bg-red-100 text-red-800',
};
