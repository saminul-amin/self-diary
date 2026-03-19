import React from 'react';
import { Text, TouchableOpacity, StyleSheet } from 'react-native';
import type { Tag } from '@/types/api';

interface TagBadgeProps {
  tag: Tag;
  selected?: boolean;
  onPress?: () => void;
  onRemove?: () => void;
}

export default function TagBadge({ tag, selected, onPress, onRemove }: TagBadgeProps) {
  const bgColor = tag.color ? `${tag.color}30` : '#e5e7eb';
  const textColor = tag.color ?? '#374151';

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={0.7}
      style={[styles.badge, { backgroundColor: bgColor }, selected && styles.selected]}
    >
      <Text style={[styles.text, { color: textColor }]}>{tag.name}</Text>
      {onRemove && (
        <TouchableOpacity onPress={onRemove} hitSlop={8}>
          <Text style={[styles.remove, { color: textColor }]}>×</Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    gap: 4,
  },
  selected: {
    borderWidth: 2,
    borderColor: '#4f46e5',
  },
  text: {
    fontSize: 13,
    fontWeight: '500',
  },
  remove: {
    fontSize: 16,
    fontWeight: '700',
    marginLeft: 2,
  },
});
