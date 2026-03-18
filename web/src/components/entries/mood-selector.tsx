'use client';

import { cn, moodEmoji, moodColor } from '@/lib/utils';
import type { Mood } from '@/types/api';

const moods: Mood[] = ['great', 'good', 'neutral', 'bad', 'terrible'];

interface MoodSelectorProps {
  value: Mood | null;
  onChange: (mood: Mood | null) => void;
}

export default function MoodSelector({ value, onChange }: MoodSelectorProps) {
  return (
    <div className="flex gap-2">
      {moods.map((mood) => (
        <button
          key={mood}
          type="button"
          onClick={() => onChange(value === mood ? null : mood)}
          className={cn(
            'rounded-lg px-3 py-1.5 text-sm font-medium transition-all',
            value === mood
              ? moodColor[mood] + ' ring-2 ring-offset-1 ring-indigo-400'
              : 'bg-gray-50 text-gray-500 hover:bg-gray-100',
          )}
          title={mood}
        >
          {moodEmoji[mood]} {mood}
        </button>
      ))}
    </div>
  );
}
