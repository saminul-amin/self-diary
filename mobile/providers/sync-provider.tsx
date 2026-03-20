/**
 * SyncProvider — exposes sync status, triggers queue processing,
 * and handles delta sync on app foreground.
 *
 * Wraps the app and provides:
 *  - isSyncing: whether a sync operation is in progress
 *  - pendingCount: number of items in the offline queue
 *  - lastSyncedAt: ISO timestamp of last successful sync
 *  - conflicts: unresolved conflicts requiring user input
 *  - triggerSync(): manually trigger a sync cycle
 *  - resolveConflict(): resolve a specific conflict
 *  - isOnline: current network status
 */
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNetworkStatus } from '@/lib/network-status';
import {
  processOfflineQueue,
  fetchDeltaEntries,
  resolveConflict as resolveConflictAction,
  type SyncConflict,
} from '@/lib/sync-manager';
import { getOfflineQueue, getLastSyncedAt } from '@/lib/offline-storage';

interface SyncContextType {
  isSyncing: boolean;
  pendingCount: number;
  lastSyncedAt: string | null;
  conflicts: SyncConflict[];
  isOnline: boolean;
  triggerSync: () => Promise<void>;
  resolveConflict: (
    conflict: SyncConflict,
    strategy: 'keep-mine' | 'keep-server' | 'keep-both',
  ) => Promise<void>;
  dismissConflicts: () => void;
}

const SyncContext = createContext<SyncContextType | null>(null);

export function useSync(): SyncContextType {
  const ctx = useContext(SyncContext);
  if (!ctx) throw new Error('useSync must be used within SyncProvider');
  return ctx;
}

export default function SyncProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [isSyncing, setIsSyncing] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  const [conflicts, setConflicts] = useState<SyncConflict[]>([]);

  const networkStatus = useNetworkStatus(
    // Called when app comes to foreground while online
    () => {
      triggerSync();
    },
  );

  // Load initial state
  useEffect(() => {
    (async () => {
      const queue = await getOfflineQueue();
      setPendingCount(queue.length);
      const ts = await getLastSyncedAt();
      setLastSyncedAt(ts);
    })();
  }, []);

  const triggerSync = useCallback(async () => {
    if (isSyncing) return;
    setIsSyncing(true);

    try {
      // 1. Process offline queue
      const result = await processOfflineQueue();

      if (result.conflicts.length > 0) {
        setConflicts((prev) => [...prev, ...result.conflicts]);
      }

      // 2. Delta sync — fetch updated entries from server
      const deltaEntries = await fetchDeltaEntries();

      // 3. Invalidate TanStack Query cache so UI picks up changes
      if (result.succeeded > 0 || deltaEntries.length > 0) {
        await queryClient.invalidateQueries({ queryKey: ['entries'] });
      }

      // 4. Update local state
      const remainingQueue = await getOfflineQueue();
      setPendingCount(remainingQueue.length);
      const ts = await getLastSyncedAt();
      setLastSyncedAt(ts);
    } finally {
      setIsSyncing(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSyncing, queryClient]);

  // Auto-sync when coming back online
  useEffect(() => {
    if (networkStatus.isOnline && pendingCount > 0) {
      triggerSync();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [networkStatus.isOnline]);

  const handleResolveConflict = useCallback(
    async (conflict: SyncConflict, strategy: 'keep-mine' | 'keep-server' | 'keep-both') => {
      await resolveConflictAction(conflict, strategy);
      setConflicts((prev) => prev.filter((c) => c.offlineEntry.id !== conflict.offlineEntry.id));
      // Refresh entries after resolution
      await queryClient.invalidateQueries({ queryKey: ['entries'] });
      const remainingQueue = await getOfflineQueue();
      setPendingCount(remainingQueue.length);
    },
    [queryClient],
  );

  const dismissConflicts = useCallback(() => {
    setConflicts([]);
  }, []);

  return (
    <SyncContext.Provider
      value={{
        isSyncing,
        pendingCount,
        lastSyncedAt,
        conflicts,
        isOnline: networkStatus.isOnline,
        triggerSync,
        resolveConflict: handleResolveConflict,
        dismissConflicts,
      }}
    >
      {children}
    </SyncContext.Provider>
  );
}
