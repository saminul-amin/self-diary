import { cn } from '@/lib/utils';
import type { Tag } from '@/types/api';

interface TagBadgeProps {
  tag: Tag;
  onRemove?: () => void;
  onClick?: () => void;
  selected?: boolean;
}

export default function TagBadge({ tag, onRemove, onClick, selected }: TagBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
        selected ? 'ring-2 ring-indigo-500 ring-offset-1' : '',
        onClick ? 'cursor-pointer hover:opacity-80' : '',
      )}
      style={{
        backgroundColor: tag.color ? `${tag.color}20` : '#e5e7eb',
        color: tag.color ?? '#374151',
      }}
      onClick={onClick}
    >
      {tag.name}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 hover:text-red-600"
        >
          &times;
        </button>
      )}
    </span>
  );
}
