import { formatDate, formatDateTime, cn, moodEmoji, moodColor } from '@/lib/utils';

describe('cn', () => {
  it('joins strings', () => {
    expect(cn('a', 'b', 'c')).toBe('a b c');
  });

  it('filters out falsy values', () => {
    expect(cn('a', false, undefined, null, 'b')).toBe('a b');
  });

  it('returns empty string for no truthy values', () => {
    expect(cn(false, undefined)).toBe('');
  });
});

describe('formatDate', () => {
  it('formats ISO date string', () => {
    const result = formatDate('2024-06-15T10:30:00Z');
    expect(result).toContain('2024');
    expect(result).toContain('Jun');
    expect(result).toContain('15');
  });
});

describe('formatDateTime', () => {
  it('includes time in output', () => {
    const result = formatDateTime('2024-06-15T14:30:00Z');
    expect(result).toContain('2024');
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });
});

describe('moodEmoji', () => {
  it('maps all moods to emojis', () => {
    expect(moodEmoji.great).toBe('😄');
    expect(moodEmoji.good).toBe('🙂');
    expect(moodEmoji.neutral).toBe('😐');
    expect(moodEmoji.bad).toBe('😞');
    expect(moodEmoji.terrible).toBe('😢');
  });
});

describe('moodColor', () => {
  it('maps all moods to color classes', () => {
    expect(moodColor.great).toContain('bg-green');
    expect(moodColor.terrible).toContain('bg-red');
  });
});
