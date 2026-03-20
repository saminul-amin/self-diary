/**
 * Sync status bar — displays at the top of the entries screen.
 * Shows offline indicator, pending count, syncing spinner, and last synced time.
 */
import React from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import { useSync } from '@/providers/sync-provider';

export default function SyncStatusBar() {
  const { isOnline, isSyncing, pendingCount, lastSyncedAt, triggerSync } = useSync();

  // Show nothing when online with no pending items and not syncing
  if (isOnline && pendingCount === 0 && !isSyncing) {
    return null;
  }

  return (
    <View
      style={[
        styles.container,
        !isOnline ? styles.offline : isSyncing ? styles.syncing : styles.pending,
      ]}
    >
      <View style={styles.row}>
        {!isOnline && (
          <>
            <Text style={styles.icon}>📡</Text>
            <Text style={styles.text}>Offline</Text>
          </>
        )}
        {isOnline && isSyncing && (
          <>
            <ActivityIndicator size="small" color="#ffffff" />
            <Text style={styles.text}>Syncing…</Text>
          </>
        )}
        {isOnline && !isSyncing && pendingCount > 0 && (
          <>
            <Text style={styles.icon}>⏳</Text>
            <Text style={styles.text}>
              {pendingCount} pending change{pendingCount !== 1 ? 's' : ''}
            </Text>
          </>
        )}

        {isOnline && !isSyncing && pendingCount > 0 && (
          <TouchableOpacity onPress={triggerSync} activeOpacity={0.7}>
            <Text style={styles.syncButton}>Sync now</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  offline: {
    backgroundColor: '#6b7280',
  },
  syncing: {
    backgroundColor: '#4f46e5',
  },
  pending: {
    backgroundColor: '#f59e0b',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  icon: {
    fontSize: 14,
  },
  text: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '500',
    flex: 1,
  },
  syncButton: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '700',
    textDecorationLine: 'underline',
  },
});
