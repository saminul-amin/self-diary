import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { moodEmoji, moodColor } from '@/lib/utils';
import type { Mood } from '@/types/api';

const moods: Mood[] = ['great', 'good', 'neutral', 'bad', 'terrible'];

interface MoodSelectorProps {
  value: Mood | null;
  onChange: (mood: Mood | null) => void;
}

export default function MoodSelector({ value, onChange }: MoodSelectorProps) {
  return (
    <View style={styles.container}>
      {moods.map((mood) => {
        const active = value === mood;
        const c = moodColor[mood];
        return (
          <TouchableOpacity
            key={mood}
            onPress={() => onChange(active ? null : mood)}
            activeOpacity={0.7}
            style={[
              styles.button,
              { backgroundColor: active ? c.bg : '#f9fafb' },
              active && styles.active,
            ]}
          >
            <Text style={styles.emoji}>{moodEmoji[mood]}</Text>
            <Text style={[styles.label, { color: active ? c.text : '#6b7280' }]}>{mood}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    gap: 8,
    flexWrap: 'wrap',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
  },
  active: {
    borderWidth: 2,
    borderColor: '#818cf8',
  },
  emoji: {
    fontSize: 16,
  },
  label: {
    fontSize: 13,
    fontWeight: '500',
  },
});
