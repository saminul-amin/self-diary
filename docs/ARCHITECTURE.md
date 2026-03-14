# Diary Application — System Architecture Document

> **Version:** 1.0  
> **Date:** March 14, 2026  
> **Status:** Production Design  

---

## 1. Project Overview

The Diary Application is a cross-platform personal journaling system that enables users to write, organize, and reflect on daily diary entries from any device. It supports rich text entries, mood tracking, tagging, and media attachments — all synchronized in real time between web and mobile clients.

### Core Capabilities

| Capability | Description |
|---|---|
| **Cross-platform writing** | Seamless diary experience on web (Next.js) and mobile (React Native/Expo) |
| **Cloud sync** | Entries written on any device are reflected everywhere within seconds |
| **Offline-first mobile** | Mobile users can write entries without connectivity; changes sync on reconnect |
| **Privacy & security** | JWT-based authentication, bcrypt password hashing, encrypted data at rest |
| **Rich organization** | Tagging, mood tracking, full-text search, and media attachments |

### Target Users

Individual users who want a private, reliable, and portable digital diary.

---

## 2. High-Level Architecture

The system follows a **client-server architecture** with two independent frontend clients consuming a single REST API backend.

```
┌─────────────────────────────────────────────────────────┐
│                      CLIENTS                            │
│                                                         │
│   ┌─────────────────┐       ┌─────────────────────┐    │
│   │  Next.js Web App│       │ React Native Mobile  │    │
│   │  (TypeScript)   │       │ (Expo + TypeScript)  │    │
│   │  Tailwind CSS   │       │ AsyncStorage (offline)│   │
│   │  TanStack Query │       │ TanStack Query       │    │
│   │  Axios          │       │ Axios                │    │
│   └────────┬────────┘       └──────────┬───────────┘    │
│            │                           │                │
└────────────┼───────────────────────────┼────────────────┘
             │         HTTPS/REST        │
             └─────────────┬─────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                     BACKEND                             │
│                          │                              │
│            ┌─────────────▼──────────────┐               │
│            │     FastAPI (Python)       │               │
│            │     JWT Authentication    │               │
│            │     REST API              │               │
│            └─────────────┬──────────────┘               │
│                          │                              │
│            ┌─────────────▼──────────────┐               │
│            │     PostgreSQL Database    │               │
│            └────────────────────────────┘               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Communication Flow

1. **Web App → Backend:** Direct HTTPS calls via Axios. TanStack Query manages caching, deduplication, and background refetching.
2. **Mobile App → Backend:** Same REST API via Axios. AsyncStorage provides an offline write queue. TanStack Query handles cache and sync state.
3. **Backend → Database:** SQLAlchemy ORM over asyncpg driver for async PostgreSQL access.
4. **Authentication:** Stateless JWT tokens issued on login, sent as `Authorization: Bearer <token>` headers on every request.

---

## 3. System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                   │
└──────────────┬───────────────────────────────────┬───────────────────┘
               │                                   │
       ┌───────▼───────┐                   ┌───────▼───────┐
       │   Web Client  │                   │ Mobile Client │
       │   (Next.js)   │                   │ (React Native)│
       │               │                   │               │
       │ ┌───────────┐ │                   │ ┌───────────┐ │
       │ │ TanStack  │ │                   │ │ TanStack  │ │
       │ │  Query    │ │                   │ │  Query    │ │
       │ │  Cache    │ │                   │ │  Cache    │ │
       │ └───────────┘ │                   │ ├───────────┤ │
       │               │                   │ │AsyncStorage│ │
       │ ┌───────────┐ │                   │ │(Offline Q) │ │
       │ │  Axios    │ │                   │ └───────────┘ │
       │ │ HTTP Client│ │                   │ ┌───────────┐ │
       │ └─────┬─────┘ │                   │ │  Axios    │ │
       └───────┼───────┘                   │ └─────┬─────┘ │
               │                           └───────┼───────┘
               │          HTTPS / TLS              │
               └───────────────┬───────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Load Balancer     │
                    │   (Nginx / ALB)     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   FastAPI Backend   │
                    │                     │
                    │  ┌───────────────┐  │
                    │  │ Auth Middleware│  │
                    │  │ (JWT Verify)  │  │
                    │  └───────┬───────┘  │
                    │          │          │
                    │  ┌───────▼───────┐  │
                    │  │ Route Handlers│  │
                    │  │ /auth /entries│  │
                    │  │ /tags         │  │
                    │  └───────┬───────┘  │
                    │          │          │
                    │  ┌───────▼───────┐  │
                    │  │ SQLAlchemy    │  │
                    │  │ ORM + asyncpg │  │
                    │  └───────┬───────┘  │
                    └──────────┼──────────┘
                               │
                ┌──────────────▼──────────────┐
                │                             │
         ┌──────▼──────┐            ┌─────────▼────────┐
         │ PostgreSQL  │            │   Object Storage  │
         │  (Primary)  │            │   (S3 / Minio)    │
         │             │            │   Attachments     │
         │ users       │            └──────────────────┘
         │ entries     │
         │ tags        │
         │ entry_tags  │
         │ attachments │
         │ sessions    │
         └─────────────┘
```

---

## 4. Core Features

### 4.1 Authentication & Account Management

| Feature | Details |
|---|---|
| Registration | Email + password signup with email format validation |
| Login | Returns access token (15 min) + refresh token (30 days) |
| Token refresh | Silent refresh before expiry; mobile stores refresh token in secure storage |
| Password reset | Token-based email flow (future enhancement) |
| Account deletion | GDPR-compliant hard delete of all user data |

### 4.2 Diary Entry CRUD

| Operation | Behavior |
|---|---|
| **Create** | Title, body (Markdown), mood, tags, optional attachments. Server assigns `created_at` in UTC |
| **Read (list)** | Paginated, filterable by date range, mood, tag. Cursor-based pagination |
| **Read (single)** | Full entry with tags and attachment URLs |
| **Update** | Partial update (PATCH semantics via PUT). Server tracks `updated_at` and increments `version` |
| **Delete** | Soft-delete (sets `deleted_at`). Permanent purge after 30 days via background job |

### 4.3 Tagging System

- Users create custom tags (e.g., "travel", "work", "family").
- Many-to-many relationship between entries and tags.
- Tag autocompletion on client side using cached tag list.
- Tag-based filtering on entry list.

### 4.4 Mood Tracking

- Each entry has an optional `mood` field.
- Enum values: `great`, `good`, `neutral`, `bad`, `terrible`.
- Clients render mood as emoji or color.
- Enables mood-over-time analytics (future feature).

### 4.5 Search

- Full-text search over entry `title` and `body` using PostgreSQL `tsvector`/`tsquery`.
- GIN index for performant search.
- Search API supports highlight snippets via `ts_headline`.

### 4.6 Offline Writing (Mobile)

- Entries created offline are stored in AsyncStorage with a `pending_sync` flag.
- On reconnect, a sync manager pushes pending entries to the server.
- Conflict resolution via `version` field and last-write-wins with user prompt on conflict.

### 4.7 Cross-Device Sync

- TanStack Query's `refetchOnWindowFocus` and `refetchOnReconnect` ensure fresh data.
- Mobile app polls on app foreground via `AppState` listener.
- Each entry carries a `version` integer for optimistic concurrency control.

---

## 5. Database Schema Design

### Entity-Relationship Overview

```
users 1──────* entries
users 1──────* tags
users 1──────* sessions
entries *────* tags       (via entry_tags)
entries 1────* attachments
```

### 5.1 `users`

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name  VARCHAR(100),
    avatar_url    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX idx_users_email ON users (email);
```

### 5.2 `entries`

```sql
CREATE TABLE entries (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         VARCHAR(500),
    body          TEXT NOT NULL,
    mood          VARCHAR(20) CHECK (mood IN ('great','good','neutral','bad','terrible')),
    is_favorite   BOOLEAN NOT NULL DEFAULT FALSE,
    version       INTEGER NOT NULL DEFAULT 1,
    client_id     UUID,          -- idempotency key from client
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at    TIMESTAMPTZ,   -- soft delete

    CONSTRAINT uq_entries_client_id UNIQUE (user_id, client_id)
);

-- Query patterns: list by user + date, search, soft-delete filter
CREATE INDEX idx_entries_user_date     ON entries (user_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_entries_user_mood     ON entries (user_id, mood)            WHERE deleted_at IS NULL;
CREATE INDEX idx_entries_deleted       ON entries (deleted_at)               WHERE deleted_at IS NOT NULL;

-- Full-text search
ALTER TABLE entries ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(body, '')),  'B')
    ) STORED;

CREATE INDEX idx_entries_fts ON entries USING GIN (search_vector);
```

### 5.3 `tags`

```sql
CREATE TABLE tags (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name       VARCHAR(100) NOT NULL,
    color      VARCHAR(7),    -- hex color, e.g. #FF5733
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_tags_user_name UNIQUE (user_id, name)
);

CREATE INDEX idx_tags_user ON tags (user_id);
```

### 5.4 `entry_tags`

```sql
CREATE TABLE entry_tags (
    entry_id UUID NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    tag_id   UUID NOT NULL REFERENCES tags(id)    ON DELETE CASCADE,

    PRIMARY KEY (entry_id, tag_id)
);

CREATE INDEX idx_entry_tags_tag ON entry_tags (tag_id);
```

### 5.5 `attachments`

```sql
CREATE TABLE attachments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id     UUID NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
    file_name    VARCHAR(255) NOT NULL,
    file_type    VARCHAR(100) NOT NULL,    -- MIME type
    file_size    BIGINT NOT NULL,          -- bytes
    storage_key  TEXT NOT NULL,            -- S3/Minio object key
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_attachments_entry ON attachments (entry_id);
```

### 5.6 `sessions` (Refresh Tokens)

```sql
CREATE TABLE sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(512) NOT NULL,
    device_info   VARCHAR(255),    -- "iPhone 15 / iOS 19" or "Chrome 130 / Windows"
    ip_address    INET,
    expires_at    TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at    TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user    ON sessions (user_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_sessions_token   ON sessions (refresh_token) WHERE revoked_at IS NULL;
CREATE INDEX idx_sessions_expires ON sessions (expires_at);
```

---

## 6. API Design

**Base URL:** `https://api.diary.app/v1`

All responses follow a consistent envelope:

```json
{
  "data": { ... },
  "meta": { "page": 1, "per_page": 20, "total": 142 },
  "error": null
}
```

### 6.1 Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | Public | Create account |
| `POST` | `/auth/login` | Public | Obtain tokens |
| `POST` | `/auth/refresh` | Refresh Token | Rotate access token |
| `POST` | `/auth/logout` | Bearer | Revoke session |
| `GET`  | `/auth/me` | Bearer | Get current user profile |

#### `POST /auth/register`

```
Request:
{
  "email": "user@example.com",
  "password": "S3cur3P@ss!",       // min 8 chars, 1 upper, 1 digit, 1 special
  "display_name": "Jane"
}

Response 201:
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Jane",
    "created_at": "2026-03-14T10:00:00Z"
  }
}

Error 409: { "error": { "code": "EMAIL_EXISTS", "message": "Email already registered" } }
```

#### `POST /auth/login`

```
Request:
{
  "email": "user@example.com",
  "password": "S3cur3P@ss!",
  "device_info": "Chrome 130 / Windows 11"    // optional
}

Response 200:
{
  "data": {
    "access_token": "eyJhbG...",
    "refresh_token": "dGhpcyBpcyBh...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}

Error 401: { "error": { "code": "INVALID_CREDENTIALS", "message": "Invalid email or password" } }
```

#### `GET /auth/me`

```
Headers: Authorization: Bearer <access_token>

Response 200:
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Jane",
    "avatar_url": null,
    "created_at": "2026-03-14T10:00:00Z"
  }
}
```

### 6.2 Diary Entries

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/entries` | Bearer | List entries (paginated) |
| `POST` | `/entries` | Bearer | Create entry |
| `GET` | `/entries/{id}` | Bearer | Get single entry |
| `PUT` | `/entries/{id}` | Bearer | Update entry |
| `DELETE` | `/entries/{id}` | Bearer | Soft-delete entry |
| `GET` | `/entries/search` | Bearer | Full-text search |

#### `GET /entries`

```
Query Parameters:
  ?page=1
  &per_page=20
  &sort=created_at:desc
  &mood=great
  &tag=travel
  &from=2026-01-01
  &to=2026-03-14
  &updated_since=2026-03-13T00:00:00Z    // for sync delta

Response 200:
{
  "data": [
    {
      "id": "uuid",
      "title": "A wonderful day",
      "body": "Today I visited...",
      "mood": "great",
      "is_favorite": false,
      "version": 1,
      "tags": [
        { "id": "uuid", "name": "travel", "color": "#3B82F6" }
      ],
      "attachment_count": 2,
      "created_at": "2026-03-14T09:30:00Z",
      "updated_at": "2026-03-14T09:30:00Z"
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 142 }
}
```

#### `POST /entries`

```
Request:
{
  "title": "A wonderful day",
  "body": "Today I visited the botanical garden...",
  "mood": "great",
  "is_favorite": false,
  "tag_ids": ["uuid1", "uuid2"],
  "client_id": "uuid"              // idempotency key from client
}

Response 201:
{
  "data": {
    "id": "uuid",
    "title": "A wonderful day",
    "body": "Today I visited the botanical garden...",
    "mood": "great",
    "is_favorite": false,
    "version": 1,
    "tags": [...],
    "created_at": "2026-03-14T09:30:00Z",
    "updated_at": "2026-03-14T09:30:00Z"
  }
}
```

#### `PUT /entries/{id}`

```
Request:
{
  "title": "Updated title",
  "body": "Updated body...",
  "mood": "good",
  "tag_ids": ["uuid1"],
  "expected_version": 1            // optimistic concurrency
}

Response 200: { "data": { ... "version": 2 } }
Error 409:   { "error": { "code": "VERSION_CONFLICT", "message": "Entry was modified. Current version: 3" } }
```

#### `DELETE /entries/{id}`

```
Response 204: No Content
```

#### `GET /entries/search`

```
Query Parameters:
  ?q=botanical+garden
  &page=1
  &per_page=20

Response 200:
{
  "data": [
    {
      "id": "uuid",
      "title": "A wonderful day",
      "snippet": "...visited the <mark>botanical garden</mark> and saw...",
      "mood": "great",
      "created_at": "2026-03-14T09:30:00Z"
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 3 }
}
```

### 6.3 Tags

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/tags` | Bearer | List user's tags |
| `POST` | `/tags` | Bearer | Create tag |
| `PUT` | `/tags/{id}` | Bearer | Update tag |
| `DELETE` | `/tags/{id}` | Bearer | Delete tag |

#### `GET /tags`

```
Response 200:
{
  "data": [
    { "id": "uuid", "name": "travel", "color": "#3B82F6", "entry_count": 12 },
    { "id": "uuid", "name": "work",   "color": "#EF4444", "entry_count": 45 }
  ]
}
```

#### `POST /tags`

```
Request:
{ "name": "fitness", "color": "#10B981" }

Response 201:
{ "data": { "id": "uuid", "name": "fitness", "color": "#10B981", "created_at": "..." } }
```

### 6.4 Attachments

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/entries/{id}/attachments` | Bearer | Upload attachment (multipart) |
| `GET` | `/entries/{id}/attachments` | Bearer | List attachments |
| `DELETE` | `/attachments/{id}` | Bearer | Delete attachment |

---

## 7. Folder Structure

### 7.1 Next.js Web App (`/web`)

```
web/
├── public/
│   ├── favicon.ico
│   └── images/
├── src/
│   ├── app/                           # App Router (Next.js 14+)
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── register/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/
│   │   │   ├── entries/
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx       # Entry detail/edit
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx       # New entry
│   │   │   │   └── page.tsx           # Entry list
│   │   │   ├── tags/
│   │   │   │   └── page.tsx
│   │   │   ├── search/
│   │   │   │   └── page.tsx
│   │   │   ├── settings/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx             # Dashboard shell (sidebar, nav)
│   │   ├── layout.tsx                 # Root layout (providers)
│   │   ├── page.tsx                   # Landing / redirect
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                        # Reusable primitives (Button, Input, Modal)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── modal.tsx
│   │   │   └── index.ts
│   │   ├── entries/
│   │   │   ├── entry-card.tsx
│   │   │   ├── entry-form.tsx
│   │   │   ├── entry-list.tsx
│   │   │   └── mood-selector.tsx
│   │   ├── tags/
│   │   │   ├── tag-badge.tsx
│   │   │   └── tag-picker.tsx
│   │   ├── layout/
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── mobile-nav.tsx
│   │   └── auth/
│   │       ├── login-form.tsx
│   │       └── register-form.tsx
│   ├── hooks/
│   │   ├── use-entries.ts             # TanStack Query hooks for entries
│   │   ├── use-tags.ts
│   │   ├── use-auth.ts
│   │   └── use-search.ts
│   ├── lib/
│   │   ├── api-client.ts             # Axios instance + interceptors
│   │   ├── auth.ts                   # Token storage, refresh logic
│   │   ├── query-client.ts           # TanStack Query client config
│   │   └── utils.ts                  # Date formatting, helpers
│   ├── types/
│   │   ├── entry.ts
│   │   ├── tag.ts
│   │   ├── user.ts
│   │   └── api.ts                    # API response envelope types
│   └── providers/
│       ├── query-provider.tsx
│       └── auth-provider.tsx
├── tailwind.config.ts
├── next.config.ts
├── tsconfig.json
├── package.json
└── .env.local
```

### 7.2 React Native Mobile App (`/mobile`)

```
mobile/
├── app/                               # Expo Router (file-based routing)
│   ├── (auth)/
│   │   ├── login.tsx
│   │   ├── register.tsx
│   │   └── _layout.tsx
│   ├── (tabs)/
│   │   ├── entries/
│   │   │   ├── index.tsx              # Entry list
│   │   │   ├── [id].tsx              # Entry detail
│   │   │   └── new.tsx               # New entry
│   │   ├── search.tsx
│   │   ├── settings.tsx
│   │   └── _layout.tsx               # Tab navigator
│   ├── _layout.tsx                    # Root layout (providers)
│   └── index.tsx                      # Entry point / redirect
├── components/
│   ├── ui/
│   │   ├── Button.tsx
│   │   ├── TextInput.tsx
│   │   ├── BottomSheet.tsx
│   │   └── index.ts
│   ├── entries/
│   │   ├── EntryCard.tsx
│   │   ├── EntryForm.tsx
│   │   ├── EntryList.tsx
│   │   └── MoodSelector.tsx
│   ├── tags/
│   │   ├── TagBadge.tsx
│   │   └── TagPicker.tsx
│   └── layout/
│       └── ScreenHeader.tsx
├── hooks/
│   ├── useEntries.ts
│   ├── useTags.ts
│   ├── useAuth.ts
│   ├── useSearch.ts
│   └── useSync.ts                     # Offline sync hook
├── lib/
│   ├── api-client.ts                  # Axios instance
│   ├── auth.ts                        # SecureStore token management
│   ├── query-client.ts
│   ├── sync-manager.ts               # Offline queue + conflict resolution
│   ├── offline-storage.ts            # AsyncStorage abstraction
│   └── utils.ts
├── types/
│   ├── entry.ts
│   ├── tag.ts
│   ├── user.ts
│   └── api.ts
├── providers/
│   ├── QueryProvider.tsx
│   ├── AuthProvider.tsx
│   └── SyncProvider.tsx
├── constants/
│   └── config.ts                      # API URL, timeouts
├── app.json
├── tsconfig.json
├── package.json
└── .env
```

### 7.3 FastAPI Backend (`/backend`)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI app factory, middleware, lifespan
│   ├── config.py                      # Pydantic Settings (env-based config)
│   ├── dependencies.py                # Dependency injection (get_db, get_current_user)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # Aggregates all v1 routers
│   │   │   ├── auth.py               # /auth endpoints
│   │   │   ├── entries.py            # /entries endpoints
│   │   │   ├── tags.py               # /tags endpoints
│   │   │   └── attachments.py        # /attachments endpoints
│   │   └── deps.py                   # Shared API dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                   # SQLAlchemy User model
│   │   ├── entry.py                  # SQLAlchemy Entry model
│   │   ├── tag.py                    # SQLAlchemy Tag + EntryTag models
│   │   ├── attachment.py
│   │   └── session.py                # SQLAlchemy Session model (refresh tokens)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                   # Pydantic request/response schemas
│   │   ├── entry.py
│   │   ├── tag.py
│   │   ├── attachment.py
│   │   └── auth.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py           # Registration, login, token logic
│   │   ├── entry_service.py          # Entry CRUD business logic
│   │   ├── tag_service.py
│   │   ├── attachment_service.py
│   │   └── search_service.py         # Full-text search logic
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py               # JWT encode/decode, password hashing
│   │   ├── exceptions.py             # Custom HTTP exceptions
│   │   └── middleware.py              # CORS, rate limiting, request logging
│   └── db/
│       ├── __init__.py
│       ├── database.py               # Async engine, sessionmaker
│       └── migrations/               # Alembic
│           ├── env.py
│           ├── alembic.ini
│           └── versions/
├── tests/
│   ├── conftest.py                   # Fixtures (test DB, client, auth)
│   ├── test_auth.py
│   ├── test_entries.py
│   ├── test_tags.py
│   └── test_search.py
├── pyproject.toml
├── Dockerfile
├── .env
└── .env.example
```

---

## 8. Data Synchronization Strategy

### Design Principles

1. **Server is the source of truth.** Clients cache locally but defer to the server on conflict.
2. **Delta sync.** Clients request only entries modified since their last sync timestamp.
3. **Idempotent creates.** Each entry carries a `client_id` (UUID v4 generated on the client). The server uses a unique constraint on `(user_id, client_id)` to deduplicate.
4. **Optimistic concurrency.** Each entry has a `version` integer. Updates require `expected_version`. Mismatches return `409 Conflict`.

### Sync Flow

```
Client                                    Server
  │                                         │
  │  GET /entries?updated_since=<ts>        │
  │ ──────────────────────────────────────► │
  │                                         │  Returns entries modified after <ts>
  │  ◄──────────────────────────────────── │
  │                                         │
  │  Merge server entries into local cache  │
  │                                         │
  │  POST /entries  (for offline entries)   │
  │ ──────────────────────────────────────► │
  │                                         │  Dedup via client_id
  │  ◄──────────────────────────────────── │
  │                                         │
  │  PUT /entries/{id}  (version check)     │
  │ ──────────────────────────────────────► │
  │                                         │  If version matches → update
  │                                         │  If conflict → 409 + current version
  │  ◄──────────────────────────────────── │
  │                                         │
  │  Store new sync timestamp = now()       │
  │                                         │
```

### TanStack Query Configuration (Both Clients)

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,           // 1 minute
      gcTime: 1000 * 60 * 30,         // 30 minutes
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      retry: 3,
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
    },
  },
});
```

---

## 9. Offline Support Strategy (Mobile)

### Architecture

```
┌──────────────────────────────────────────────┐
│                Mobile App                     │
│                                               │
│  ┌──────────┐    ┌──────────┐   ┌──────────┐ │
│  │  UI Layer │───►│  Sync    │──►│  Axios   │─┼──► Server
│  │          │    │  Manager │   │  Client  │ │
│  └──────────┘    └────┬─────┘   └──────────┘ │
│                       │                       │
│                  ┌────▼─────┐                 │
│                  │ Offline  │                 │
│                  │ Queue    │                 │
│                  │(AsyncStr)│                 │
│                  └──────────┘                 │
└──────────────────────────────────────────────┘
```

### Offline Queue Schema (AsyncStorage)

```typescript
interface OfflineEntry {
  client_id: string;            // UUID v4
  action: 'create' | 'update' | 'delete';
  payload: Partial<EntryPayload>;
  created_at: string;           // ISO timestamp
  retry_count: number;
  last_error?: string;
}

// Stored under key: "@diary/offline_queue"
```

### Sync Manager Behavior

```
App starts or network restored
       │
       ▼
  Read offline queue from AsyncStorage
       │
       ▼
  Queue empty? ── Yes ──► Done
       │
      No
       │
       ▼
  Process each item sequentially:
       │
       ├── action = 'create' ──► POST /entries (with client_id)
       │       │
       │       ├── 201 Created ──► Remove from queue
       │       ├── 409 Conflict ──► Already synced, remove from queue
       │       └── 5xx / Network ──► Increment retry_count, keep in queue
       │
       ├── action = 'update' ──► PUT /entries/{id}
       │       │
       │       ├── 200 OK ──► Remove from queue
       │       ├── 409 Version Conflict ──► Prompt user to resolve
       │       └── 5xx / Network ──► Keep in queue
       │
       └── action = 'delete' ──► DELETE /entries/{id}
               │
               ├── 204 / 404 ──► Remove from queue
               └── 5xx ──► Keep in queue
       │
       ▼
  Invalidate TanStack Query cache
  Trigger refetch of entries list
```

### Conflict Resolution

| Scenario | Strategy |
|---|---|
| Create conflict (duplicate `client_id`) | Server returns existing entry; client discards local copy |
| Update conflict (version mismatch) | Client shows diff and lets user choose "Keep mine" / "Keep server" / "Keep both" |
| Delete conflict (entry already deleted) | Silently accept (idempotent) |

---

## 10. Security Design

### 10.1 JWT Authentication

```
Token Architecture:
┌────────────────────────────────────────────────┐
│ Access Token  (short-lived, stateless)         │
│   Algorithm:  HS256                            │
│   Expiry:     15 minutes                       │
│   Payload:    { sub: user_id, exp, iat, jti }  │
│   Storage:    Memory (web), SecureStore (mobile)│
├────────────────────────────────────────────────┤
│ Refresh Token (long-lived, stored in DB)       │
│   Format:     Opaque (random 64-byte hex)      │
│   Expiry:     30 days                          │
│   Storage:    httpOnly cookie (web),           │
│               SecureStore (mobile)             │
│   Rotation:   New refresh token on each use    │
│   Revocation: Stored in sessions table         │
└────────────────────────────────────────────────┘
```

**Key decisions:**
- Access tokens are **never** stored in localStorage (XSS risk). On web, held in React state and refreshed silently.
- Refresh tokens use **rotation**: each use invalidates the old token and issues a new one. If a stolen refresh token is reused, the entire session family is revoked.

### 10.2 Password Security

```python
# Using bcrypt via passlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

- **Bcrypt** with work factor 12 (auto-tuned).
- Password requirements enforced via Pydantic validators: min 8 chars, at least 1 uppercase, 1 digit, 1 special character.
- Passwords are **never** logged or included in API responses.

### 10.3 API Protection

| Layer | Mechanism |
|-------|-----------|
| **Transport** | TLS 1.2+ enforced (HTTPS only) |
| **CORS** | Whitelist: `https://diary.app`, `https://www.diary.app`. Credentials mode enabled |
| **Rate Limiting** | `slowapi` middleware: 5 req/s per IP for auth endpoints, 30 req/s for authenticated endpoints |
| **Input Validation** | Pydantic models validate all request bodies. Path/query params typed |
| **SQL Injection** | SQLAlchemy ORM with parameterized queries. No raw SQL |
| **XSS** | React/Next.js auto-escapes output. CSP headers set |
| **CSRF** | SameSite=Lax cookies + CORS origin check |
| **Authorization** | Every query includes `WHERE user_id = :current_user` — users can only access their own data |

### 10.4 Data Validation (Pydantic Example)

```python
from pydantic import BaseModel, Field, field_validator
import re

class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Must contain at least one special character")
        return v
```

---

## 11. Deployment Architecture

### Production Topology

```
                        ┌─────────────────┐
                        │   Cloudflare     │
                        │   CDN / WAF      │
                        └────────┬────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │   Application Load Balancer │
                   │   (AWS ALB / GCP LB)        │
                   └──────┬──────────────┬──────┘
                          │              │
              ┌───────────▼───┐   ┌──────▼────────────┐
              │  Web (Next.js)│   │  API (FastAPI)     │
              │  Vercel /     │   │  Container Cluster │
              │  Container    │   │  (ECS / Cloud Run) │
              │               │   │                    │
              │  SSR + Static │   │  2+ replicas       │
              │  Assets on CDN│   │  Auto-scaling      │
              └───────────────┘   └──────────┬─────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │      Data Layer             │
                              │                             │
                              │  ┌────────────┐  ┌────────┐ │
                              │  │ PostgreSQL │  │  S3    │ │
                              │  │ (RDS /     │  │ Bucket │ │
                              │  │  Cloud SQL)│  │        │ │
                              │  │  Primary + │  │ Media  │ │
                              │  │  Read      │  │ files  │ │
                              │  │  Replica   │  │        │ │
                              │  └────────────┘  └────────┘ │
                              └─────────────────────────────┘


Mobile App:
  ┌──────────────────┐
  │ App Store / Play │
  │ Store            │
  │                  │
  │ Expo EAS Build   │
  │ + OTA Updates    │
  └──────────────────┘
```

### Component Deployment Details

| Component | Platform | Configuration |
|-----------|----------|---------------|
| **Web Frontend** | Vercel or containerized on ECS | Next.js with SSR. Static assets served via CDN with immutable cache headers |
| **API Backend** | AWS ECS Fargate / GCP Cloud Run | Docker container. Min 2 replicas. Auto-scale on CPU > 60% |
| **PostgreSQL** | AWS RDS / GCP Cloud SQL | `db.r6g.large` start. Automated backups, point-in-time recovery. Read replica for search queries |
| **Object Storage** | AWS S3 | Private bucket. Pre-signed URLs for upload/download. Lifecycle policy: move to IA after 90 days |
| **Mobile** | Expo EAS | OTA updates via `expo-updates`. Binary builds for App Store / Play Store |
| **Secrets** | AWS Secrets Manager / GCP Secret Manager | JWT secret, DB credentials, S3 keys. Rotated quarterly |
| **CI/CD** | GitHub Actions | Lint → Test → Build → Deploy. Staging on PR merge, production on tag |
| **Monitoring** | Datadog / CloudWatch + Sentry | API latency P50/P95/P99, error rates, DB connection pool usage |

### Environment Strategy

| Environment | Purpose | Database |
|-------------|---------|----------|
| `local` | Development | Docker Compose PostgreSQL |
| `staging` | Pre-production testing | Isolated RDS instance |
| `production` | Live users | RDS Multi-AZ |

---

## 12. Scalability Considerations

### Current Design Capacity

The initial architecture (2 API replicas, single RDS instance) comfortably supports **~10,000 daily active users** and **~100 requests/second**.

### Scaling Axes

#### Horizontal API Scaling

```
Current:   2 API containers
Scale to:  N containers behind load balancer

Triggers:  CPU > 60%, request latency P95 > 500ms
Approach:  Stateless JWT auth enables linear horizontal scaling.
           No sticky sessions required.
```

#### Database Scaling

| Stage | Strategy | When |
|-------|----------|------|
| **Stage 1** | Vertical scaling (larger RDS instance) | < 50K users |
| **Stage 2** | Read replicas for search and list queries | 50K–200K users |
| **Stage 3** | Connection pooling via PgBouncer | > 200K users, connection pressure |
| **Stage 4** | Table partitioning on `entries` by `user_id` hash | > 1M users, large table |
| **Stage 5** | Sharding or move to managed distributed DB | > 10M users |

#### Caching Layer (When Needed)

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client   ├────►│  Redis   ├────►│  Postgres │
│  Request  │     │  Cache   │     │  DB       │
└──────────┘     └──────────┘     └──────────┘

Cache targets:
  - User profile (GET /auth/me)     TTL: 5 min
  - Tag list (GET /tags)            TTL: 5 min
  - Entry list first page           TTL: 1 min (invalidate on write)
```

Redis is **not required at launch** — TanStack Query client-side caching handles most read optimization. Add Redis when API database load exceeds 70%.

#### Search Scaling

| Stage | Strategy |
|-------|----------|
| **Stage 1** | PostgreSQL `tsvector` + GIN index (current design) |
| **Stage 2** | Elasticsearch / Meilisearch for advanced full-text search, faceted filtering, typo tolerance |

#### File Upload Scaling

- Pre-signed S3 URLs allow **direct client-to-S3 uploads**, bypassing the API for large files.
- CloudFront CDN for serving attachment thumbnails.
- Lambda/Cloud Function for image resize on upload.

### Performance Budgets

| Metric | Target |
|--------|--------|
| API response time (P95) | < 200ms |
| Time to first byte (web) | < 800ms |
| Mobile app cold start | < 2s |
| Offline sync completion | < 5s for 50 entries |
| Full-text search | < 300ms for 100K entries |

---

## Appendix: Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth tokens | JWT (stateless) | Horizontal scaling without shared session store |
| Soft deletes | `deleted_at` column | Undo support, audit trail, GDPR bulk delete |
| Idempotency | `client_id` unique constraint | Safe offline retry without duplicates |
| Concurrency | Version field + 409 response | Simple, effective for diary use case |
| Search | PostgreSQL FTS (initial) | No extra infra; sufficient for < 500K entries |
| Offline storage | AsyncStorage queue | Native Expo support, simple key-value model |
| File storage | S3 with pre-signed URLs | Decouple uploads from API, cost-effective |
| Migrations | Alembic | Industry standard for SQLAlchemy |
| API versioning | URL prefix (`/v1/`) | Explicit, cacheable, simple routing |
