'use client';

import TagBadge from './tag-badge';
import type { Tag } from '@/types/api';

interface TagPickerProps {
  allTags: Tag[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

export default function TagPicker({ allTags, selectedIds, onChange }: TagPickerProps) {
  const toggle = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter((t) => t !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  if (allTags.length === 0) {
    return <p className="text-sm text-gray-400">No tags yet</p>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {allTags.map((tag) => (
        <TagBadge
          key={tag.id}
          tag={tag}
          selected={selectedIds.includes(tag.id)}
          onClick={() => toggle(tag.id)}
        />
      ))}
    </div>
  );
}
