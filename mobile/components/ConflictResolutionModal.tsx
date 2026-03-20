/**
 * Conflict resolution modal — shown when offline edits conflict with server state.
 *
 * For each conflict, the user can:
 *  - Keep Mine: overwrite server with offline version
 *  - Keep Server: discard offline changes
 *  - Keep Both: save offline version as a new entry
 */
import React, { useState } from 'react';
import { View, Text, Modal, ScrollView, StyleSheet } from 'react-native';
import Button from '@/components/ui/Button';
import { useSync } from '@/providers/sync-provider';
import { formatDateTime } from '@/lib/utils';

export default function ConflictResolutionModal() {
  const { conflicts, resolveConflict, dismissConflicts } = useSync();
  const [resolving, setResolving] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  if (conflicts.length === 0) return null;

  const conflict = conflicts[currentIndex] ?? conflicts[0];
  if (!conflict) return null;

  const { offlineEntry, serverEntry } = conflict;

  const handleResolve = async (strategy: 'keep-mine' | 'keep-server' | 'keep-both') => {
    setResolving(true);
    try {
      await resolveConflict(conflict, strategy);
      if (currentIndex >= conflicts.length - 1) {
        setCurrentIndex(0);
        dismissConflicts();
      }
    } finally {
      setResolving(false);
    }
  };

  return (
    <Modal
      visible={conflicts.length > 0}
      transparent
      animationType="slide"
      onRequestClose={dismissConflicts}
    >
      <View style={styles.overlay}>
        <View style={styles.modal}>
          <Text style={styles.title}>Sync Conflict</Text>
          <Text style={styles.subtitle}>
            Conflict {currentIndex + 1} of {conflicts.length}
          </Text>
          <Text style={styles.description}>
            Your offline changes conflict with a newer version on the server.
          </Text>

          <ScrollView style={styles.comparison} nestedScrollEnabled>
            <View style={styles.versionCard}>
              <Text style={styles.versionLabel}>Your Version (Offline)</Text>
              <Text style={styles.versionTitle}>{offlineEntry.payload.title || 'Untitled'}</Text>
              <Text style={styles.versionBody} numberOfLines={4}>
                {offlineEntry.payload.body}
              </Text>
              <Text style={styles.versionMeta}>
                Queued: {formatDateTime(offlineEntry.queued_at)}
              </Text>
            </View>

            <View style={[styles.versionCard, styles.serverCard]}>
              <Text style={styles.versionLabel}>Server Version</Text>
              <Text style={styles.versionTitle}>{serverEntry.title || 'Untitled'}</Text>
              <Text style={styles.versionBody} numberOfLines={4}>
                {serverEntry.body}
              </Text>
              <Text style={styles.versionMeta}>
                Updated: {formatDateTime(serverEntry.updated_at)} (v
                {serverEntry.version})
              </Text>
            </View>
          </ScrollView>

          <View style={styles.actions}>
            <Button
              title="Keep Mine"
              onPress={() => handleResolve('keep-mine')}
              loading={resolving}
            />
            <Button
              title="Keep Server"
              variant="secondary"
              onPress={() => handleResolve('keep-server')}
              loading={resolving}
            />
            <Button
              title="Keep Both"
              variant="ghost"
              onPress={() => handleResolve('keep-both')}
              loading={resolving}
            />
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modal: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    maxHeight: '85%',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 13,
    color: '#9ca3af',
    textAlign: 'center',
    marginTop: 4,
  },
  description: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 16,
  },
  comparison: {
    maxHeight: 300,
    marginBottom: 16,
  },
  versionCard: {
    backgroundColor: '#eff6ff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
  },
  serverCard: {
    backgroundColor: '#fef3c7',
  },
  versionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  versionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
  },
  versionBody: {
    fontSize: 13,
    color: '#374151',
    marginTop: 4,
    lineHeight: 18,
  },
  versionMeta: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 8,
  },
  actions: {
    gap: 10,
  },
});
