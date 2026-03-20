/**
 * Sync manager — processes the offline queue and performs delta sync.
 *
 * Queue processing:
 *  - Iterates pending offline entries in FIFO order
 *  - POSTs creates with client_id for idempotency
 *  - PUTs updates with expected_version for optimistic concurrency
 *  - On 409 conflict, marks the entry for user resolution
 *  - Retries transient failures with exponential backoff (max 5 attempts)
 *
 * Delta sync:
 *  - Fetches entries updated since last sync timestamp
 *  - Merges into TanStack Query cache
 */
import apiClient from '@/lib/api-client';
import {
  getOfflineQueue,
  setOfflineQueue,
  dequeueOfflineEntry,
  getLastSyncedAt,
  setLastSyncedAt,
  type OfflineEntry,
} from '@/lib/offline-storage';
import type { Entry } from '@/types/api';
import { isOnline } from '@/lib/network-status';

export interface SyncConflict {
  offlineEntry: OfflineEntry;
  serverEntry: Entry;
}

export interface SyncResult {
  processed: number;
  succeeded: number;
  conflicts: SyncConflict[];
  errors: number;
}

/**
 * Process the offline queue. Returns a result summary.
 * Entries that produce a 409 conflict are collected for user resolution.
 * Transient errors increment the attempt counter; after 5 attempts the entry is dropped.
 */
export async function processOfflineQueue(): Promise<SyncResult> {
  const online = await isOnline();
  if (!online) {
    return { processed: 0, succeeded: 0, conflicts: [], errors: 0 };
  }

  const queue = await getOfflineQueue();
  if (queue.length === 0) {
    return { processed: 0, succeeded: 0, conflicts: [], errors: 0 };
  }

  const result: SyncResult = {
    processed: queue.length,
    succeeded: 0,
    conflicts: [],
    errors: 0,
  };

  const remaining: OfflineEntry[] = [];

  for (const entry of queue) {
    try {
      if (entry.action === 'create') {
        await apiClient.post('/entries', {
          title: entry.payload.title,
          body: entry.payload.body,
          mood: entry.payload.mood,
          is_favorite: entry.payload.is_favorite,
          tag_ids: entry.payload.tag_ids,
          client_id: entry.payload.client_id,
        });
        result.succeeded++;
      } else if (entry.action === 'update') {
        await apiClient.put(`/entries/${entry.id}`, {
          title: entry.payload.title,
          body: entry.payload.body,
          mood: entry.payload.mood,
          is_favorite: entry.payload.is_favorite,
          tag_ids: entry.payload.tag_ids,
          expected_version: entry.payload.expected_version,
        });
        result.succeeded++;
      }
    } catch (error: unknown) {
      if (isAxios409(error) && entry.action === 'update') {
        // Version conflict — fetch server version for resolution
        try {
          const serverRes = await apiClient.get(`/entries/${entry.id}`);
          const serverEntry: Entry = serverRes.data.data;
          result.conflicts.push({ offlineEntry: entry, serverEntry });
        } catch {
          // Can't fetch server entry; keep in queue for retry
          remaining.push({ ...entry, attempts: entry.attempts + 1 });
          result.errors++;
        }
      } else if (isAxios404(error)) {
        // Entry was deleted on server; drop from queue
        result.succeeded++;
      } else {
        // Transient error — retry if under attempt limit
        const next = { ...entry, attempts: entry.attempts + 1 };
        if (next.attempts < 5) {
          remaining.push(next);
        }
        result.errors++;
      }
    }
  }

  // Save remaining items back to queue
  await setOfflineQueue(remaining);

  return result;
}

/**
 * Delta sync: fetch entries updated since last sync.
 * Returns the new entries to merge into the cache.
 */
export async function fetchDeltaEntries(): Promise<Entry[]> {
  const online = await isOnline();
  if (!online) return [];

  const lastSynced = await getLastSyncedAt();
  const params = new URLSearchParams();
  if (lastSynced) {
    params.set('updated_since', lastSynced);
  }
  params.set('page_size', '100');

  const res = await apiClient.get(`/entries?${params.toString()}`);
  const entries: Entry[] = res.data.entries ?? res.data.data ?? [];

  // Update last synced timestamp
  await setLastSyncedAt(new Date().toISOString());

  return entries;
}

/**
 * Resolve a conflict by choosing a resolution strategy.
 */
export async function resolveConflict(
  conflict: SyncConflict,
  strategy: 'keep-mine' | 'keep-server' | 'keep-both',
): Promise<void> {
  const { offlineEntry, serverEntry } = conflict;

  switch (strategy) {
    case 'keep-mine': {
      // Force-update with current server version
      await apiClient.put(`/entries/${offlineEntry.id}`, {
        title: offlineEntry.payload.title,
        body: offlineEntry.payload.body,
        mood: offlineEntry.payload.mood,
        is_favorite: offlineEntry.payload.is_favorite,
        tag_ids: offlineEntry.payload.tag_ids,
        expected_version: serverEntry.version,
      });
      break;
    }
    case 'keep-server': {
      // Do nothing — server version wins, just remove from queue
      break;
    }
    case 'keep-both': {
      // Create the offline version as a new entry
      await apiClient.post('/entries', {
        title: offlineEntry.payload.title
          ? `${offlineEntry.payload.title} (offline copy)`
          : 'Offline copy',
        body: offlineEntry.payload.body,
        mood: offlineEntry.payload.mood,
        is_favorite: offlineEntry.payload.is_favorite,
        tag_ids: offlineEntry.payload.tag_ids,
      });
      break;
    }
  }

  // Remove the conflict from the offline queue
  await dequeueOfflineEntry(offlineEntry.id, offlineEntry.action);
}

function isAxios409(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    (error as { response?: { status?: number } }).response?.status === 409
  );
}

function isAxios404(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    (error as { response?: { status?: number } }).response?.status === 404
  );
}
