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

/** Mood to emoji mapping. */
export const moodEmoji: Record<string, string> = {
  great: '😄',
  good: '🙂',
  neutral: '😐',
  bad: '😞',
  terrible: '😢',
};

/** Mood to color mapping (React Native hex colors). */
export const moodColor: Record<string, { bg: string; text: string }> = {
  great: { bg: '#dcfce7', text: '#166534' },
  good: { bg: '#dbeafe', text: '#1e40af' },
  neutral: { bg: '#f3f4f6', text: '#374151' },
  bad: { bg: '#ffedd5', text: '#9a3412' },
  terrible: { bg: '#fee2e2', text: '#991b1b' },
};
