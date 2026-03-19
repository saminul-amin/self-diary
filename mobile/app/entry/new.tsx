import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput as RNTextInput,
  Switch,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useCreateEntry } from '@/hooks/use-entries';
import { useTags } from '@/hooks/use-tags';
import Button from '@/components/ui/Button';
import TextInput from '@/components/ui/TextInput';
import MoodSelector from '@/components/ui/MoodSelector';
import TagBadge from '@/components/ui/TagBadge';
import type { Mood } from '@/types/api';

export default function NewEntryScreen() {
  const router = useRouter();
  const { data: allTags } = useTags();
  const createEntry = useCreateEntry();

  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [mood, setMood] = useState<Mood | undefined>(undefined);
  const [isFavorite, setIsFavorite] = useState(false);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [error, setError] = useState('');

  const toggleTag = (tagId: string) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId) ? prev.filter((i) => i !== tagId) : [...prev, tagId],
    );
  };

  const handleCreate = async () => {
    if (!body.trim()) {
      setError('Body is required');
      return;
    }
    setError('');
    try {
      await createEntry.mutateAsync({
        title: title.trim() || undefined,
        body: body.trim(),
        mood: mood ?? null,
        is_favorite: isFavorite,
        tag_ids: selectedTagIds,
      });
      router.back();
    } catch {
      setError('Failed to create entry');
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {error ? <Text style={styles.error}>{error}</Text> : null}

        <TextInput
          label="Title (optional)"
          value={title}
          onChangeText={setTitle}
          placeholder="Give your entry a title"
        />

        <View style={styles.field}>
          <Text style={styles.label}>Body</Text>
          <RNTextInput
            value={body}
            onChangeText={setBody}
            placeholder="What's on your mind?"
            multiline
            textAlignVertical="top"
            style={styles.bodyInput}
          />
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Mood</Text>
          <MoodSelector value={mood ?? null} onChange={(m) => setMood(m ?? undefined)} />
        </View>

        <View style={styles.field}>
          <View style={styles.switchRow}>
            <Text style={styles.label}>Favorite</Text>
            <Switch
              value={isFavorite}
              onValueChange={setIsFavorite}
              trackColor={{ false: '#d1d5db', true: '#a5b4fc' }}
              thumbColor={isFavorite ? '#4f46e5' : '#f4f3f4'}
            />
          </View>
        </View>

        {(allTags?.length ?? 0) > 0 && (
          <View style={styles.field}>
            <Text style={styles.label}>Tags</Text>
            <View style={styles.tagGrid}>
              {allTags!.map((tag) => (
                <TagBadge
                  key={tag.id}
                  tag={tag}
                  selected={selectedTagIds.includes(tag.id)}
                  onPress={() => toggleTag(tag.id)}
                />
              ))}
            </View>
          </View>
        )}

        <Button title="Create Entry" onPress={handleCreate} loading={createEntry.isPending} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9fafb' },
  content: { padding: 16, gap: 16, paddingBottom: 40 },
  error: {
    backgroundColor: '#fef2f2',
    color: '#dc2626',
    padding: 12,
    borderRadius: 10,
    fontSize: 14,
    overflow: 'hidden',
  },
  field: { gap: 6 },
  label: { fontSize: 14, fontWeight: '500', color: '#374151' },
  bodyInput: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 10,
    padding: 12,
    fontSize: 15,
    color: '#111827',
    minHeight: 160,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tagGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
});
