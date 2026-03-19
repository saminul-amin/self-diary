import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import TextInput from '@/components/ui/TextInput';
import TagBadge from '@/components/ui/TagBadge';
import { useSearchEntries } from '@/hooks/use-entries';
import { formatDate, moodEmoji } from '@/lib/utils';
import type { Entry } from '@/types/api';

export default function SearchScreen() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const { data, isLoading } = useSearchEntries(query);
  const entries = data?.data ?? [];

  const renderItem = ({ item }: { item: Entry }) => (
    <TouchableOpacity
      style={styles.card}
      activeOpacity={0.7}
      onPress={() => router.push(`/entry/${item.id}`)}
    >
      <View style={styles.row}>
        <Text style={styles.title} numberOfLines={1}>
          {item.title || 'Untitled'}
        </Text>
        {item.mood && <Text style={styles.mood}>{moodEmoji[item.mood]}</Text>}
      </View>
      <Text style={styles.body} numberOfLines={2}>
        {item.body}
      </Text>
      <View style={styles.footer}>
        <View style={styles.tags}>
          {item.tags.slice(0, 2).map((tag) => (
            <TagBadge key={tag.id} tag={tag} />
          ))}
        </View>
        <Text style={styles.date}>{formatDate(item.created_at)}</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.searchBar}>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search your entries…"
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>

      {query.length < 2 ? (
        <View style={styles.center}>
          <Text style={styles.hint}>Type at least 2 characters to search</Text>
        </View>
      ) : isLoading ? (
        <View style={styles.center}>
          <Text style={styles.hint}>Searching…</Text>
        </View>
      ) : entries.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.hint}>No entries match "{query}"</Text>
        </View>
      ) : (
        <FlatList
          data={entries}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  searchBar: {
    padding: 16,
    paddingBottom: 8,
  },
  list: {
    padding: 16,
    paddingTop: 8,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  hint: {
    fontSize: 15,
    color: '#9ca3af',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
  },
  mood: {
    fontSize: 16,
    marginLeft: 8,
  },
  body: {
    marginTop: 4,
    fontSize: 13,
    color: '#6b7280',
    lineHeight: 18,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 10,
  },
  tags: {
    flexDirection: 'row',
    gap: 4,
  },
  date: {
    fontSize: 12,
    color: '#9ca3af',
  },
});
