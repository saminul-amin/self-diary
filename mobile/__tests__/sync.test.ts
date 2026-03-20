/**
 * Integration tests for sync & offline support.
 *
 * Tests cover:
 *  - Offline storage CRUD operations
 *  - Queue processing (create, update, conflict, transient error)
 *  - Delta sync fetch
 *  - Conflict resolution strategies
 *
 * These tests mock AsyncStorage, network status, and API calls
 * to simulate offline scenarios without a running backend.
 */

// ── Mock setup ──

// Mock AsyncStorage
const mockStorage: Record<string, string> = {};
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn((key: string) => Promise.resolve(mockStorage[key] ?? null)),
  setItem: jest.fn((key: string, value: string) => {
    mockStorage[key] = value;
    return Promise.resolve();
  }),
  removeItem: jest.fn((key: string) => {
    delete mockStorage[key];
    return Promise.resolve();
  }),
}));

// Mock NetInfo
const mockNetInfo = { isConnected: true, isInternetReachable: true };
jest.mock('@react-native-community/netinfo', () => ({
  addEventListener: jest.fn(() => jest.fn()),
  fetch: jest.fn(() => Promise.resolve(mockNetInfo)),
}));

// Mock apiClient
const mockApiClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
};
jest.mock('@/lib/api-client', () => ({
  __esModule: true,
  default: mockApiClient,
}));

import {
  getOfflineQueue,
  setOfflineQueue,
  enqueueOfflineEntry,
  dequeueOfflineEntry,
  clearOfflineQueue,
  getLastSyncedAt,
  setLastSyncedAt,
  type OfflineEntry,
} from '@/lib/offline-storage';

import {
  processOfflineQueue,
  fetchDeltaEntries,
  resolveConflict,
  type SyncConflict,
} from '@/lib/sync-manager';

import type { Entry } from '@/types/api';

// ── Helper ──

function clearStorage() {
  Object.keys(mockStorage).forEach((k) => delete mockStorage[k]);
}

function makeOfflineEntry(overrides: Partial<OfflineEntry> = {}): OfflineEntry {
  return {
    id: 'test-id-1',
    action: 'create',
    payload: {
      body: 'Test body',
      title: 'Test title',
      client_id: 'client-uuid-1',
    },
    queued_at: new Date().toISOString(),
    attempts: 0,
    ...overrides,
  };
}

function makeServerEntry(overrides: Partial<Entry> = {}): Entry {
  return {
    id: 'server-id-1',
    title: 'Server title',
    body: 'Server body',
    mood: null,
    is_favorite: false,
    version: 2,
    tags: [],
    attachment_count: 0,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
    ...overrides,
  };
}

// ── Tests ──

describe('Offline Storage', () => {
  beforeEach(() => clearStorage());

  test('getOfflineQueue returns empty array when no data', async () => {
    const queue = await getOfflineQueue();
    expect(queue).toEqual([]);
  });

  test('enqueueOfflineEntry adds to queue', async () => {
    const entry = makeOfflineEntry();
    await enqueueOfflineEntry(entry);
    const queue = await getOfflineQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].id).toBe('test-id-1');
  });

  test('dequeueOfflineEntry removes specific entry', async () => {
    await enqueueOfflineEntry(makeOfflineEntry({ id: 'a', action: 'create' }));
    await enqueueOfflineEntry(makeOfflineEntry({ id: 'b', action: 'update' }));
    await dequeueOfflineEntry('a', 'create');
    const queue = await getOfflineQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].id).toBe('b');
  });

  test('clearOfflineQueue empties everything', async () => {
    await enqueueOfflineEntry(makeOfflineEntry());
    await clearOfflineQueue();
    const queue = await getOfflineQueue();
    expect(queue).toEqual([]);
  });

  test('setOfflineQueue replaces entire queue', async () => {
    await enqueueOfflineEntry(makeOfflineEntry());
    await setOfflineQueue([]);
    const queue = await getOfflineQueue();
    expect(queue).toEqual([]);
  });

  test('lastSyncedAt read/write', async () => {
    expect(await getLastSyncedAt()).toBeNull();
    await setLastSyncedAt('2026-03-20T12:00:00Z');
    expect(await getLastSyncedAt()).toBe('2026-03-20T12:00:00Z');
  });
});

describe('Sync Manager — processOfflineQueue', () => {
  beforeEach(() => {
    clearStorage();
    jest.clearAllMocks();
    mockNetInfo.isConnected = true;
  });

  test('returns early when offline', async () => {
    mockNetInfo.isConnected = false;
    await enqueueOfflineEntry(makeOfflineEntry());
    const result = await processOfflineQueue();
    expect(result.processed).toBe(0);
    expect(mockApiClient.post).not.toHaveBeenCalled();
  });

  test('successfully processes a create', async () => {
    const entry = makeOfflineEntry({ action: 'create' });
    await enqueueOfflineEntry(entry);
    mockApiClient.post.mockResolvedValueOnce({ data: { data: makeServerEntry() } });

    const result = await processOfflineQueue();
    expect(result.processed).toBe(1);
    expect(result.succeeded).toBe(1);
    expect(result.conflicts).toHaveLength(0);
    expect(mockApiClient.post).toHaveBeenCalledWith(
      '/entries',
      expect.objectContaining({
        body: 'Test body',
        client_id: 'client-uuid-1',
      }),
    );
  });

  test('successfully processes an update', async () => {
    const entry = makeOfflineEntry({
      id: 'server-id-1',
      action: 'update',
      payload: { body: 'Updated body', expected_version: 1 },
    });
    await enqueueOfflineEntry(entry);
    mockApiClient.put.mockResolvedValueOnce({ data: { data: makeServerEntry() } });

    const result = await processOfflineQueue();
    expect(result.processed).toBe(1);
    expect(result.succeeded).toBe(1);
    expect(mockApiClient.put).toHaveBeenCalledWith(
      '/entries/server-id-1',
      expect.objectContaining({
        body: 'Updated body',
        expected_version: 1,
      }),
    );
  });

  test('detects 409 conflict on update', async () => {
    const entry = makeOfflineEntry({
      id: 'server-id-1',
      action: 'update',
      payload: { body: 'My changes', expected_version: 1 },
    });
    await enqueueOfflineEntry(entry);

    const error409 = { response: { status: 409 } };
    mockApiClient.put.mockRejectedValueOnce(error409);
    mockApiClient.get.mockResolvedValueOnce({ data: { data: makeServerEntry({ version: 3 }) } });

    const result = await processOfflineQueue();
    expect(result.conflicts).toHaveLength(1);
    expect(result.conflicts[0].serverEntry.version).toBe(3);
    expect(result.conflicts[0].offlineEntry.payload.body).toBe('My changes');
  });

  test('drops entry on 404 (deleted on server)', async () => {
    const entry = makeOfflineEntry({
      id: 'deleted-id',
      action: 'update',
      payload: { body: 'Gone' },
    });
    await enqueueOfflineEntry(entry);

    const error404 = { response: { status: 404 } };
    mockApiClient.put.mockRejectedValueOnce(error404);

    const result = await processOfflineQueue();
    expect(result.succeeded).toBe(1);
    const remaining = await getOfflineQueue();
    expect(remaining).toHaveLength(0);
  });

  test('retries transient errors up to 5 attempts', async () => {
    const entry = makeOfflineEntry({ action: 'create', attempts: 3 });
    await enqueueOfflineEntry(entry);
    mockApiClient.post.mockRejectedValueOnce(new Error('Network error'));

    const result = await processOfflineQueue();
    expect(result.errors).toBe(1);
    const remaining = await getOfflineQueue();
    expect(remaining).toHaveLength(1);
    expect(remaining[0].attempts).toBe(4);

    // 5th attempt — should be dropped
    remaining[0].attempts = 4;
    await setOfflineQueue(remaining);
    mockApiClient.post.mockRejectedValueOnce(new Error('Network error'));
    const result2 = await processOfflineQueue();
    expect(result2.errors).toBe(1);
    const remaining2 = await getOfflineQueue();
    expect(remaining2).toHaveLength(0);
  });
});

describe('Sync Manager — fetchDeltaEntries', () => {
  beforeEach(() => {
    clearStorage();
    jest.clearAllMocks();
    mockNetInfo.isConnected = true;
  });

  test('fetches all entries when no lastSynced', async () => {
    const entries = [makeServerEntry(), makeServerEntry({ id: 's2' })];
    mockApiClient.get.mockResolvedValueOnce({ data: { entries } });

    const result = await fetchDeltaEntries();
    expect(result).toHaveLength(2);
    expect(mockApiClient.get).toHaveBeenCalledWith(expect.stringContaining('page_size=100'));
    // Should set lastSyncedAt
    expect(await getLastSyncedAt()).toBeTruthy();
  });

  test('passes updated_since when lastSynced exists', async () => {
    await setLastSyncedAt('2026-03-20T10:00:00Z');
    mockApiClient.get.mockResolvedValueOnce({ data: { entries: [] } });

    await fetchDeltaEntries();
    expect(mockApiClient.get).toHaveBeenCalledWith(
      expect.stringContaining('updated_since=2026-03-20T10%3A00%3A00Z'),
    );
  });

  test('returns empty when offline', async () => {
    mockNetInfo.isConnected = false;
    const result = await fetchDeltaEntries();
    expect(result).toEqual([]);
  });
});

describe('Sync Manager — resolveConflict', () => {
  beforeEach(() => {
    clearStorage();
    jest.clearAllMocks();
    mockNetInfo.isConnected = true;
  });

  const conflict: SyncConflict = {
    offlineEntry: makeOfflineEntry({
      id: 'entry-1',
      action: 'update',
      payload: { body: 'Offline body', title: 'Offline title', expected_version: 1 },
    }),
    serverEntry: makeServerEntry({ id: 'entry-1', version: 3 }),
  };

  test('keep-mine overwrites server with current version', async () => {
    await enqueueOfflineEntry(conflict.offlineEntry);
    mockApiClient.put.mockResolvedValueOnce({ data: { data: makeServerEntry() } });

    await resolveConflict(conflict, 'keep-mine');
    expect(mockApiClient.put).toHaveBeenCalledWith(
      '/entries/entry-1',
      expect.objectContaining({
        body: 'Offline body',
        expected_version: 3, // uses server's current version
      }),
    );
  });

  test('keep-server does nothing (just dequeues)', async () => {
    await enqueueOfflineEntry(conflict.offlineEntry);
    await resolveConflict(conflict, 'keep-server');
    expect(mockApiClient.put).not.toHaveBeenCalled();
    expect(mockApiClient.post).not.toHaveBeenCalled();
  });

  test('keep-both creates a new entry with offline copy', async () => {
    await enqueueOfflineEntry(conflict.offlineEntry);
    mockApiClient.post.mockResolvedValueOnce({ data: { data: makeServerEntry() } });

    await resolveConflict(conflict, 'keep-both');
    expect(mockApiClient.post).toHaveBeenCalledWith(
      '/entries',
      expect.objectContaining({
        body: 'Offline body',
        title: 'Offline title (offline copy)',
      }),
    );
  });
});
