'use client';

import { useState } from 'react';
import Button from '@/components/ui/button';
import Input from '@/components/ui/input';
import Modal from '@/components/ui/modal';
import TagBadge from '@/components/tags/tag-badge';
import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from '@/hooks/use-tags';
import type { Tag } from '@/types/api';

const presetColors = [
  '#ef4444',
  '#f97316',
  '#eab308',
  '#22c55e',
  '#06b6d4',
  '#3b82f6',
  '#8b5cf6',
  '#ec4899',
  '#6b7280',
];

export default function TagsPage() {
  const { data: tags, isLoading } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [name, setName] = useState('');
  const [color, setColor] = useState<string>('#3b82f6');
  const [error, setError] = useState('');

  const openCreate = () => {
    setEditingTag(null);
    setName('');
    setColor('#3b82f6');
    setError('');
    setModalOpen(true);
  };

  const openEdit = (tag: Tag) => {
    setEditingTag(tag);
    setName(tag.name);
    setColor(tag.color ?? '#3b82f6');
    setError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Tag name is required.');
      return;
    }

    try {
      if (editingTag) {
        await updateTag.mutateAsync({ id: editingTag.id, name: name.trim(), color });
      } else {
        await createTag.mutateAsync({ name: name.trim(), color });
      }
      setModalOpen(false);
    } catch {
      setError('Failed to save tag. It may already exist.');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this tag? It will be removed from all entries.')) return;
    await deleteTag.mutateAsync(id);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tags</h1>
        <Button onClick={openCreate}>+ New Tag</Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : !tags || tags.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No tags yet.</p>
          <Button onClick={openCreate}>Create your first tag</Button>
        </div>
      ) : (
        <div className="rounded-xl bg-white border border-gray-200 shadow-sm divide-y divide-gray-100">
          {tags.map((tag) => (
            <div key={tag.id} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <TagBadge tag={tag} />
                {tag.entry_count !== undefined && (
                  <span className="text-xs text-gray-400">
                    {tag.entry_count} {tag.entry_count === 1 ? 'entry' : 'entries'}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => openEdit(tag)}>
                  Edit
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(tag.id)}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingTag ? 'Edit Tag' : 'New Tag'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>}
          <Input
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. personal, work"
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
            <div className="flex flex-wrap gap-2">
              {presetColors.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  className={`h-8 w-8 rounded-full border-2 transition-transform ${
                    color === c ? 'border-gray-800 scale-110' : 'border-transparent hover:scale-105'
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={createTag.isPending || updateTag.isPending}>
              {createTag.isPending || updateTag.isPending
                ? 'Saving…'
                : editingTag
                  ? 'Update'
                  : 'Create'}
            </Button>
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
