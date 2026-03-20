# SelfDiary — Mobile Client

React Native (Expo) application for iOS and Android with TypeScript, Expo Router, TanStack Query, and Expo SecureStore.

## Tech Stack

- **Expo 52** — Managed workflow
- **React Native 0.76** / **React 19**
- **expo-router 4** — File-based routing with route groups
- **expo-secure-store** — Secure token persistence
- **TanStack Query 5** — Server-state management
- **Axios 1.7** — HTTP client with interceptor-based auth
- **@react-native-community/netinfo** — Network status detection

## Setup

```bash
npm install --legacy-peer-deps
npx expo start
```

Create a `.env` file:

```env
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## Project Structure

```
mobile/
├── app/
│   ├── _layout.tsx          # Root: QueryProvider → AuthProvider → SyncProvider → Slot
│   ├── index.tsx            # Redirect → (tabs) or (auth)/login
│   ├── (auth)/
│   │   ├── _layout.tsx      # Stack (no header)
│   │   ├── login.tsx        # Email / password sign-in
│   │   └── register.tsx     # Create account
│   ├── (tabs)/
│   │   ├── _layout.tsx      # Bottom-tab navigator
│   │   ├── index.tsx        # Entries list (FlatList + FAB + SyncStatusBar)
│   │   ├── search.tsx       # Full-text search
│   │   └── settings.tsx     # Profile & sign-out
│   └── entry/
│       ├── [id].tsx         # View / edit / delete entry (with expected_version)
│       └── new.tsx          # Create new entry (with client_id)
├── components/
│   ├── ui/                  # Reusable branded components
│   ├── ConflictResolutionModal.tsx  # Conflict resolution (keep mine / server / both)
│   └── SyncStatusBar.tsx    # Offline/syncing/pending status indicator
├── hooks/                   # TanStack Query hooks (entries, tags) with offline fallback
├── lib/
│   ├── api-client.ts        # Axios with token injection + 401 refresh
│   ├── auth.ts              # SecureStore token persistence
│   ├── network-status.ts    # NetInfo hook + AppState foreground detection
│   ├── offline-storage.ts   # AsyncStorage queue + last-synced timestamp
│   ├── query-client.ts      # TanStack Query client factory
│   ├── sync-manager.ts      # Queue processor, delta sync, conflict resolution
│   └── utils.ts             # Date formatters, mood maps
├── providers/
│   ├── auth-provider.tsx    # AuthProvider with route guard
│   ├── query-provider.tsx   # QueryProvider wrapper
│   └── sync-provider.tsx    # SyncProvider (status, trigger, conflict handling)
├── __tests__/
│   └── sync.test.ts         # Sync integration tests (storage, queue, conflict)
└── types/                   # Shared API types
```

## Architecture Notes

- **Authentication** — Tokens stored in `expo-secure-store` with an in-memory cache for synchronous reads. Access tokens are injected via Axios request interceptor; 401s trigger a silent refresh and retry queue.
- **Route Guard** — `AuthProvider` uses `useSegments()` to redirect unauthenticated users to `(auth)/login` and authenticated users away from the auth group.
- **State Management** — All server state managed by TanStack Query; local UI state with `useState`. No global store needed.

### Offline & Sync

- **Offline Queue** — When the device is offline, entry creates and updates are saved to an AsyncStorage-backed queue with `client_id` (create) or `expected_version` (update) for safe replay.
- **Sync Manager** — Processes the queue in FIFO order on reconnect. Uses exponential backoff with a 5-attempt limit for transient errors. 404s (deleted on server) are silently dropped.
- **Delta Sync** — On app foreground, fetches only entries updated since the last sync timestamp via `GET /entries?updated_since=<ts>`.
- **Conflict Resolution** — 409 version conflicts surface a modal where the user can choose: **Keep Mine** (overwrite server), **Keep Server** (discard local), or **Keep Both** (create a copy).
- **Network Detection** — `@react-native-community/netinfo` monitors connectivity; `AppState` listener triggers sync when the app returns to the foreground while online.
- **SyncProvider** — Exposes `isSyncing`, `pendingCount`, `lastSyncedAt`, `conflicts`, and `triggerSync()` to the entire component tree.
- **SyncStatusBar** — Visual indicator at the top of the entries list showing offline/syncing/pending state.
