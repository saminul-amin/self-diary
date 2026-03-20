/**
 * Offline storage abstraction over AsyncStorage.
 *
 * Stores a queue of pending offline operations (create/update entries)
 * and the last-synced timestamp for delta sync.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Mood } from '@/types/api';

const QUEUE_KEY = 'selfdiary_offline_queue';
const LAST_SYNCED_KEY = 'selfdiary_last_synced';

export type OfflineAction = 'create' | 'update';

export interface OfflineEntry {
  /** Locally generated UUID for idempotent create or server entry ID for update */
  id: string;
  action: OfflineAction;
  /** For create: used as client_id for idempotency. For update: the server entry ID */
  payload: OfflineEntryPayload;
  /** ISO timestamp of when the operation was queued */
  queued_at: string;
  /** Number of sync attempts so far */
  attempts: number;
}

export interface OfflineEntryPayload {
  title?: string;
  body: string;
  mood?: Mood | null;
  is_favorite?: boolean;
  tag_ids?: string[];
  /** client_id for create dedup on the server */
  client_id?: string;
  /** expected_version for optimistic concurrency on update */
  expected_version?: number;
}

/**
 * Read the entire offline queue.
 */
export async function getOfflineQueue(): Promise<OfflineEntry[]> {
  const raw = await AsyncStorage.getItem(QUEUE_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as OfflineEntry[];
  } catch {
    return [];
  }
}

/**
 * Replace the entire offline queue.
 */
export async function setOfflineQueue(queue: OfflineEntry[]): Promise<void> {
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

/**
 * Append an entry to the offline queue.
 */
export async function enqueueOfflineEntry(entry: OfflineEntry): Promise<void> {
  const queue = await getOfflineQueue();
  queue.push(entry);
  await setOfflineQueue(queue);
}

/**
 * Remove a specific entry from the queue by id + action.
 */
export async function dequeueOfflineEntry(id: string, action: OfflineAction): Promise<void> {
  const queue = await getOfflineQueue();
  const filtered = queue.filter((e) => !(e.id === id && e.action === action));
  await setOfflineQueue(filtered);
}

/**
 * Clear the entire offline queue.
 */
export async function clearOfflineQueue(): Promise<void> {
  await AsyncStorage.removeItem(QUEUE_KEY);
}

/**
 * Get the last-synced ISO timestamp for delta sync.
 */
export async function getLastSyncedAt(): Promise<string | null> {
  return AsyncStorage.getItem(LAST_SYNCED_KEY);
}

/**
 * Set the last-synced ISO timestamp.
 */
export async function setLastSyncedAt(ts: string): Promise<void> {
  await AsyncStorage.setItem(LAST_SYNCED_KEY, ts);
}
