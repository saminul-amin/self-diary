import React, { useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, RefreshControl, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useEntries } from '@/hooks/use-entries';
import { formatDate, moodEmoji, moodColor } from '@/lib/utils';
import TagBadge from '@/components/ui/TagBadge';
import type { Entry } from '@/types/api';

export default function EntriesScreen() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const { data, isLoading, refetch } = useEntries({ page, per_page: 20 });

  const entries = data?.data ?? [];
  const meta = data?.meta;
  const hasMore = meta ? page < Math.ceil(meta.total / meta.per_page) : false;

  const onRefresh = useCallback(() => {
    setPage(1);
    refetch();
  }, [refetch]);

  const renderItem = ({ item }: { item: Entry }) => {
    const mc = item.mood ? moodColor[item.mood] : null;

    return (
      <TouchableOpacity
        style={styles.card}
        activeOpacity={0.7}
        onPress={() => router.push(`/entry/${item.id}`)}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle} numberOfLines={1}>
            {item.title || 'Untitled'}
          </Text>
          <View style={styles.cardMeta}>
            {item.is_favorite && <Text style={styles.star}>★</Text>}
            {item.mood && mc && (
              <View style={[styles.moodBadge, { backgroundColor: mc.bg }]}>
                <Text style={{ color: mc.text, fontSize: 12, fontWeight: '500' }}>
                  {moodEmoji[item.mood]} {item.mood}
                </Text>
              </View>
            )}
          </View>
        </View>
        <Text style={styles.body} numberOfLines={2}>
          {item.body}
        </Text>
        <View style={styles.cardFooter}>
          <View style={styles.tags}>
            {item.tags.slice(0, 3).map((tag) => (
              <TagBadge key={tag.id} tag={tag} />
            ))}
            {item.tags.length > 3 && <Text style={styles.moreText}>+{item.tags.length - 3}</Text>}
          </View>
          <Text style={styles.date}>{formatDate(item.created_at)}</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={entries}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        refreshControl={
          <RefreshControl refreshing={isLoading && page === 1} onRefresh={onRefresh} />
        }
        onEndReached={() => {
          if (hasMore) setPage((p) => p + 1);
        }}
        onEndReachedThreshold={0.5}
        contentContainerStyle={entries.length === 0 ? styles.empty : styles.list}
        ListEmptyComponent={
          !isLoading ? (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No entries yet.</Text>
              <Text style={styles.emptySubtext}>Tap + to write your first entry.</Text>
            </View>
          ) : null
        }
      />
      <TouchableOpacity
        style={styles.fab}
        activeOpacity={0.8}
        onPress={() => router.push('/entry/new')}
      >
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  list: {
    padding: 16,
    gap: 12,
  },
  empty: {
    flexGrow: 1,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 14,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
  },
  cardMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  star: {
    fontSize: 16,
    color: '#f59e0b',
  },
  moodBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  body: {
    marginTop: 6,
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
  },
  tags: {
    flexDirection: 'row',
    gap: 4,
    flexWrap: 'wrap',
    flex: 1,
  },
  moreText: {
    fontSize: 12,
    color: '#9ca3af',
    alignSelf: 'center',
  },
  date: {
    fontSize: 12,
    color: '#9ca3af',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyText: {
    fontSize: 17,
    color: '#6b7280',
    fontWeight: '500',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#4f46e5',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#4f46e5',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  fabText: {
    fontSize: 28,
    color: '#ffffff',
    fontWeight: '300',
    marginTop: -2,
  },
});
