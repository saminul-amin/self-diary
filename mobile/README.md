# SelfDiary — Mobile Client

React Native (Expo) application for iOS and Android with TypeScript, Expo Router, TanStack Query, and Expo SecureStore.

## Tech Stack

- **Expo 52** — Managed workflow
- **React Native 0.76** / **React 19**
- **expo-router 4** — File-based routing with route groups
- **expo-secure-store** — Secure token persistence
- **TanStack Query 5** — Server-state management
- **Axios 1.7** — HTTP client with interceptor-based auth

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
│   ├── _layout.tsx          # Root: QueryProvider → AuthProvider → Slot
│   ├── index.tsx            # Redirect → (tabs) or (auth)/login
│   ├── (auth)/
│   │   ├── _layout.tsx      # Stack (no header)
│   │   ├── login.tsx        # Email / password sign-in
│   │   └── register.tsx     # Create account
│   ├── (tabs)/
│   │   ├── _layout.tsx      # Bottom-tab navigator
│   │   ├── index.tsx        # Entries list (FlatList + FAB)
│   │   ├── search.tsx       # Full-text search
│   │   └── settings.tsx     # Profile & sign-out
│   └── entry/
│       ├── [id].tsx         # View / edit / delete entry
│       └── new.tsx          # Create new entry
├── components/ui/           # Reusable branded components
├── hooks/                   # TanStack Query hooks (entries, tags)
├── lib/                     # API client, auth, query-client, utils
├── providers/               # AuthProvider, QueryProvider
└── types/                   # Shared API types
```

## Architecture Notes

- **Authentication** — Tokens stored in `expo-secure-store` with an in-memory cache for synchronous reads. Access tokens are injected via Axios request interceptor; 401s trigger a silent refresh and retry queue.
- **Route Guard** — `AuthProvider` uses `useSegments()` to redirect unauthenticated users to `(auth)/login` and authenticated users away from the auth group.
- **State Management** — All server state managed by TanStack Query; local UI state with `useState`. No global store needed.
