# Self Diary — Implementation Plan

> **Version:** 1.0
> **Date:** March 14, 2026
> **Reference:** [ARCHITECTURE.md](ARCHITECTURE.md)
> **Status:** Approved for Development

---

## Table of Contents

1. [Development Phases](#1-development-phases)
2. [Milestones](#2-milestones)
3. [Task Breakdown](#3-task-breakdown)
4. [Suggested Development Order](#4-suggested-development-order)
5. [Dependencies Between Modules](#5-dependencies-between-modules)
6. [Estimated Complexity](#6-estimated-complexity)

---

## 1. Development Phases

The project is divided into **11 phases**, organized to allow incremental delivery and parallel workstreams where possible. Each phase produces a testable, demonstrable increment.

| Phase | Name | Summary |
|-------|------|---------|
| P1 | Project Setup | Monorepo scaffolding, tooling, CI pipeline, local dev environment |
| P2 | Backend Core | FastAPI skeleton, database connection, config, error handling, migrations |
| P3 | Authentication | Registration, login, JWT access/refresh tokens, session management |
| P4 | Diary Entries Module | Full CRUD, pagination, filtering, soft delete, full-text search |
| P5 | Tagging System | Tag CRUD, many-to-many entry-tag linking, tag-based filtering |
| P6 | Attachments | File upload/download via S3/Minio, pre-signed URLs, metadata storage |
| P7 | Web Client | Next.js application — auth flows, entry management, search, tags |
| P8 | Mobile Client | React Native (Expo) application — auth, entries, tags, search |
| P9 | Sync & Offline Support | Offline queue, conflict resolution, delta sync, idempotent writes |
| P10 | Testing & Quality | Unit tests, integration tests, E2E tests, load testing, security audit |
| P11 | Deployment | Containerization, CI/CD pipelines, staging/production environments |

---

## 2. Milestones

Each milestone is a gate that must be passed before dependent work proceeds. Milestones are verified by the criteria listed below.

| ID | Milestone | Depends On | Acceptance Criteria |
|----|-----------|------------|---------------------|
| **M1** | Backend API skeleton running | P1 | FastAPI serves `/health` on local Docker Compose; PostgreSQL connected; Alembic runs first migration |
| **M2** | Authentication complete | M1 | Register, login, refresh, logout endpoints pass integration tests; JWT validation works on protected routes |
| **M3** | Diary entry CRUD working | M2 | All entry endpoints pass tests; pagination, filtering by date/mood, soft delete, and full-text search functional via API |
| **M4** | Tags & attachments complete | M3 | Tag CRUD, entry-tag linking, attachment upload/download all verified via API tests |
| **M5** | Web app functional | M3 | User can register, log in, create/edit/delete entries, search, and manage tags through the browser |
| **M6** | Mobile app functional | M3 | Same capabilities as M5 on iOS and Android simulators via Expo Go |
| **M7** | Offline sync implemented | M5, M6 | Mobile user can create/edit entries offline; entries sync correctly on reconnect; conflicts handled |
| **M8** | Production deployment | M7 | Application running on staging environment; CI/CD pipeline green; monitoring active |

```
M1 ──► M2 ──► M3 ──► M4
                │
                ├──► M5 ──┐
                │         ├──► M7 ──► M8
                └──► M6 ──┘
```

---

## 3. Task Breakdown

### Phase 1 — Project Setup

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 1.1 | Initialize monorepo structure (`/backend`, `/web`, `/mobile`) | Small | Root directory with three project folders |
| 1.2 | Set up Git repository, `.gitignore`, branch strategy (`main`, `develop`, feature branches) | Small | Initialized repo with protection rules |
| 1.3 | Create `docker-compose.yml` with PostgreSQL 16, Minio (S3-compatible), and backend service | Medium | `docker compose up` starts full local stack |
| 1.4 | Initialize FastAPI project (`pyproject.toml`, virtual env, dev dependencies) | Small | `uvicorn app.main:app` starts server |
| 1.5 | Initialize Next.js project with TypeScript, Tailwind CSS, ESLint, Prettier | Small | `npm run dev` serves web app |
| 1.6 | Initialize Expo project with TypeScript, Expo Router | Small | `npx expo start` opens app in simulator |
| 1.7 | Configure shared TypeScript types package or replicated type files | Small | Shared API types available in both clients |
| 1.8 | Set up GitHub Actions CI: lint + type-check for all three projects | Medium | PRs run checks automatically |
| 1.9 | Write `README.md` with setup instructions for new developers | Small | Onboarding runbook |

---

### Phase 2 — Backend Core

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 2.1 | Implement `app/config.py` with Pydantic Settings (env-based configuration) | Small | Config object with DB URL, JWT secret, S3 credentials |
| 2.2 | Set up async SQLAlchemy engine and session factory (`app/db/database.py`) | Medium | `get_db` dependency yields async sessions |
| 2.3 | Configure Alembic for async migrations | Medium | `alembic upgrade head` runs against local PostgreSQL |
| 2.4 | Implement global exception handlers and error response envelope (`app/core/exceptions.py`) | Small | Consistent `{ data, meta, error }` responses |
| 2.5 | Add CORS middleware with configurable origins (`app/core/middleware.py`) | Small | Cross-origin requests allowed from web client origin |
| 2.6 | Add request logging middleware (structured JSON logs) | Small | Every request logged with method, path, status, duration |
| 2.7 | Add rate limiting middleware via `slowapi` | Medium | Auth endpoints limited to 5 req/s per IP |
| 2.8 | Create API versioning structure (`/api/v1/router.py`) | Small | All routes mounted under `/v1` prefix |
| 2.9 | Add `/health` and `/readiness` endpoints | Small | Load balancer health check target |

---

### Phase 3 — Authentication

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 3.1 | Create `users` table SQLAlchemy model and Alembic migration | Small | `users` table with schema per ARCHITECTURE.md |
| 3.2 | Create `sessions` table SQLAlchemy model and migration | Small | `sessions` table for refresh token storage |
| 3.3 | Implement password hashing utilities (`app/core/security.py`) using bcrypt | Small | `hash_password()` and `verify_password()` functions |
| 3.4 | Implement JWT encode/decode utilities (access token + refresh token) | Medium | `create_access_token()`, `create_refresh_token()`, `decode_token()` |
| 3.5 | Implement `get_current_user` dependency (decode JWT from `Authorization` header) | Medium | FastAPI dependency that returns authenticated user or 401 |
| 3.6 | Build `POST /auth/register` endpoint with Pydantic validation | Medium | User created with hashed password; returns user profile |
| 3.7 | Build `POST /auth/login` endpoint with credential verification | Medium | Returns access + refresh tokens; creates session record |
| 3.8 | Build `POST /auth/refresh` endpoint with token rotation | Medium | Old refresh token revoked; new pair issued |
| 3.9 | Build `POST /auth/logout` endpoint (revoke session) | Small | Session marked as revoked in database |
| 3.10 | Build `GET /auth/me` endpoint | Small | Returns current user profile |
| 3.11 | Write integration tests for all auth endpoints | Medium | Full happy-path + error-case coverage |

---

### Phase 4 — Diary Entries Module

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 4.1 | Create `entries` table SQLAlchemy model and migration (including `search_vector` column) | Medium | `entries` table with full-text search vector and indexes |
| 4.2 | Implement Pydantic schemas for entry create/update/response | Small | Request and response models with validation |
| 4.3 | Build `POST /entries` endpoint with `client_id` idempotency | Medium | Creates entry; deduplicates on `client_id` |
| 4.4 | Build `GET /entries` with pagination, date/mood/tag filtering, and `updated_since` | Large | Paginated list with query parameter filtering |
| 4.5 | Build `GET /entries/{id}` with tags and attachment count | Small | Full entry detail response |
| 4.6 | Build `PUT /entries/{id}` with optimistic concurrency (`expected_version`) | Medium | Updates entry; returns 409 on version conflict |
| 4.7 | Build `DELETE /entries/{id}` with soft delete | Small | Sets `deleted_at`; returns 204 |
| 4.8 | Build `GET /entries/search` with PostgreSQL full-text search and `ts_headline` snippets | Large | Search results with highlighted snippets |
| 4.9 | Implement entry service layer (`app/services/entry_service.py`) | Medium | Business logic separated from route handlers |
| 4.10 | Write integration tests for all entry endpoints | Medium | CRUD, pagination, search, version conflict tests |

---

### Phase 5 — Tagging System

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 5.1 | Create `tags` and `entry_tags` SQLAlchemy models and migration | Small | Both tables with foreign keys and indexes |
| 5.2 | Build `GET /tags` endpoint (list user's tags with `entry_count`) | Medium | Aggregated tag list |
| 5.3 | Build `POST /tags` endpoint | Small | Creates tag for current user |
| 5.4 | Build `PUT /tags/{id}` endpoint | Small | Updates tag name/color |
| 5.5 | Build `DELETE /tags/{id}` endpoint (cascade removal from `entry_tags`) | Small | Deletes tag and all associations |
| 5.6 | Integrate tag assignment into `POST /entries` and `PUT /entries/{id}` via `tag_ids` field | Medium | Entries reference tags in create/update flows |
| 5.7 | Include tag data in entry list and detail responses | Small | Tags embedded in entry response |
| 5.8 | Write integration tests for tag endpoints and entry-tag linking | Medium | Full coverage |

---

### Phase 6 — Attachments

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 6.1 | Create `attachments` SQLAlchemy model and migration | Small | `attachments` table |
| 6.2 | Implement S3/Minio client wrapper (`app/services/attachment_service.py`) | Medium | Upload, download, delete operations via `boto3` |
| 6.3 | Build `POST /entries/{id}/attachments` (multipart file upload) | Large | File stored in S3; metadata saved in DB |
| 6.4 | Build `GET /entries/{id}/attachments` (list with pre-signed download URLs) | Medium | Returns list with time-limited download links |
| 6.5 | Build `DELETE /attachments/{id}` | Small | Removes from S3 and DB |
| 6.6 | Add file type validation (allowlist: images, PDF) and size limits (10 MB) | Small | Rejects invalid uploads with 422 |
| 6.7 | Write integration tests for attachment endpoints (using Minio in tests) | Medium | Upload, list, delete tested |

---

### Phase 7 — Web Client (Next.js)

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 7.1 | Set up Axios instance with base URL, interceptors, and token injection (`lib/api-client.ts`) | Medium | Configured HTTP client with auto-refresh on 401 |
| 7.2 | Set up TanStack Query client with defaults (`lib/query-client.ts`) and `QueryProvider` | Small | Query client with staleTime, gcTime, retry config |
| 7.3 | Implement `AuthProvider` with context (user state, login, logout, silent refresh) | Large | Auth state managed in React context; tokens in memory |
| 7.4 | Build login page and `LoginForm` component | Medium | Email/password form with validation and error display |
| 7.5 | Build register page and `RegisterForm` component | Medium | Registration form with password strength feedback |
| 7.6 | Build dashboard layout (sidebar, header, mobile nav) | Medium | Responsive shell for authenticated pages |
| 7.7 | Build entry list page with `useEntries` hook, pagination, and filters (date, mood, tag) | Large | Paginated entry list with working filters |
| 7.8 | Build entry detail/edit page with `EntryForm`, mood selector, tag picker | Large | Create and edit entries with full form |
| 7.9 | Build tag management page (list, create, edit, delete tags) | Medium | Tag CRUD UI |
| 7.10 | Build search page with live search results and highlighted snippets | Medium | Full-text search UI |
| 7.11 | Build settings page (profile display, logout) | Small | Basic user settings |
| 7.12 | Implement protected route middleware (redirect unauthenticated users to login) | Medium | Route guard via Next.js middleware |
| 7.13 | Responsive design pass — ensure all pages work on mobile viewport | Medium | Consistent UX from 375px to 1920px |
| 7.14 | Build reusable UI components (Button, Input, Modal, TagBadge, MoodSelector) | Medium | Component library with Tailwind styling |

---

### Phase 8 — Mobile Client (React Native / Expo)

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 8.1 | Set up Axios instance and TanStack Query client (same config pattern as web) | Medium | Mobile HTTP client with token handling |
| 8.2 | Implement `AuthProvider` with `expo-secure-store` for token persistence | Large | Auth state persisted across app restarts |
| 8.3 | Build login and register screens | Medium | Native forms with validation |
| 8.4 | Build tab navigator layout (Entries, Search, Settings) | Medium | Bottom tab navigation via Expo Router |
| 8.5 | Build entry list screen with pull-to-refresh and infinite scroll | Large | Paginated list with FlatList |
| 8.6 | Build entry detail/edit screen with mood selector and tag picker | Large | Full entry form with native inputs |
| 8.7 | Build search screen | Medium | Full-text search with result list |
| 8.8 | Build settings screen (profile, logout) | Small | Basic settings |
| 8.9 | Build reusable UI components (Button, TextInput, BottomSheet, TagBadge) | Medium | Native component library |
| 8.10 | Implement navigation guards (redirect to login if unauthenticated) | Medium | Auth-gated routing |

---

### Phase 9 — Sync & Offline Support

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 9.1 | Implement offline storage abstraction over AsyncStorage (`lib/offline-storage.ts`) | Medium | Read/write/delete functions for offline entries queue |
| 9.2 | Build sync manager (`lib/sync-manager.ts`) — queue processing, retry logic | Large | Processes offline queue on reconnect; retries with exponential backoff |
| 9.3 | Implement network status detection and `AppState` listener | Medium | App detects online/offline transitions |
| 9.4 | Wire offline entry creation — save to queue when offline, POST on reconnect | Large | Create entry works without network |
| 9.5 | Wire offline entry update — save to queue, PUT with version check on reconnect | Large | Update entry works without network |
| 9.6 | Implement conflict resolution UI (keep mine / keep server / keep both) | Large | User prompted on 409 conflict after sync |
| 9.7 | Implement delta sync — `GET /entries?updated_since=<ts>` on app foreground | Medium | Only fetch changed entries, not full list |
| 9.8 | Build `SyncProvider` to expose sync status (syncing, pending count, last synced) | Medium | Sync status indicator in mobile UI |
| 9.9 | Invalidate TanStack Query cache after sync completes | Small | UI reflects latest data after sync |
| 9.10 | Write integration tests for sync scenarios (offline create, version conflict) | Large | Automated tests for critical sync paths |

---

### Phase 10 — Testing & Quality

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 10.1 | Write unit tests for backend service layer (auth, entries, tags) | Medium | pytest coverage for business logic |
| 10.2 | Write API integration tests with test database (using `httpx` + `pytest-asyncio`) | Large | Full endpoint coverage |
| 10.3 | Write frontend component tests (React Testing Library) for web client | Medium | Key component behavior tested |
| 10.4 | Write E2E tests for web client critical flows (Playwright) | Large | Login → create entry → search → delete |
| 10.5 | Write mobile E2E tests for critical flows (Detox or Maestro) | Large | Login → create entry → verify list |
| 10.6 | Load testing with Locust — verify 100 req/s target on staging | Medium | Locust report showing P95 < 200ms |
| 10.7 | Security audit — OWASP checklist, dependency vulnerability scan | Medium | No critical/high vulnerabilities |
| 10.8 | Accessibility audit (web) — WCAG 2.1 AA on main flows | Medium | Color contrast, keyboard nav, screen reader support |

---

### Phase 11 — Deployment

| # | Task | Complexity | Deliverable |
|---|------|:----------:|-------------|
| 11.1 | Write `Dockerfile` for FastAPI backend (multi-stage build) | Medium | Optimized production image |
| 11.2 | Write `Dockerfile` for Next.js web app (standalone output mode) | Medium | Optimized production image |
| 11.3 | Provision PostgreSQL on cloud (RDS / Cloud SQL) with backups enabled | Medium | Managed database instance |
| 11.4 | Provision S3 bucket with private access and lifecycle rules | Small | Media storage ready |
| 11.5 | Set up container orchestration (ECS Fargate / Cloud Run) with auto-scaling | Large | API running with 2+ replicas |
| 11.6 | Deploy Next.js to Vercel or containerized behind ALB | Medium | Web app live on staging domain |
| 11.7 | Set up secrets management (AWS Secrets Manager / env injection) | Small | No secrets in code or environment files |
| 11.8 | Configure GitHub Actions CI/CD: test → build → push image → deploy to staging | Large | Automated deploy on merge to `develop` |
| 11.9 | Configure production deploy pipeline: tag → deploy to production | Medium | Automated deploy on version tag |
| 11.10 | Set up monitoring: Sentry (error tracking), CloudWatch/Datadog (metrics) | Medium | Dashboards for API latency, error rate, DB connections |
| 11.11 | Set up Cloudflare CDN / WAF in front of production | Medium | DDoS protection, TLS termination, static asset caching |
| 11.12 | Configure Expo EAS Build for iOS and Android binary builds | Medium | App builds submitted to TestFlight / Google Play internal testing |
| 11.13 | Configure Expo OTA updates for JS bundle updates without store release | Small | `expo-updates` push channel configured |

---

## 4. Suggested Development Order

The implementation follows a **backend-first, vertical-slice** approach. The API is built and tested before any frontend work begins, ensuring clients always integrate against a stable, verified backend.

### Execution Timeline

```
Week 1–2     ┃ P1: Project Setup
              ┃ P2: Backend Core
              ┃
Week 3–4     ┃ P3: Authentication
              ┃ P4: Diary Entries Module
              ┃
Week 5       ┃ P5: Tagging System
              ┃ P6: Attachments
              ┃
Week 6–8     ┃ P7: Web Client          ← can start once M3 is reached
              ┃ P8: Mobile Client       ← parallel with web if 2+ devs
              ┃
Week 9–10    ┃ P9: Sync & Offline Support
              ┃
Week 11      ┃ P10: Testing & Quality
              ┃
Week 12      ┃ P11: Deployment
```

### Rationale

1. **Backend first (P1–P6).** Every feature is usable and testable via API before any UI exists. This eliminates "works in UI but API isn't ready" blockers.

2. **Auth before entries.** Protected routes are the foundation — nothing meaningful can be built without user identity.

3. **Entries before tags.** Tags are linked to entries. The entry CRUD must exist first. Attachments also depend on entries.

4. **Web and mobile in parallel (P7 + P8).** Both clients consume the same API. With the API stable at M3, two frontend developers can work simultaneously.

5. **Offline sync last (P9).** This is the most complex feature. It depends on both clients being functional and the entry API being stable. Building it on top of working clients minimizes rework.

6. **Testing throughout, hardened at the end (P10).** Unit and integration tests are written during each phase. Phase 10 adds E2E tests, load tests, and security audits.

7. **Deployment last (P11).** Infrastructure is provisioned only when the application is feature-complete and tested.

### Team Allocation (Recommended for 3-person team)

| Developer | Week 1–5 | Week 6–8 | Week 9–10 | Week 11–12 |
|-----------|----------|----------|-----------|------------|
| **Backend** | P1–P6 (all backend) | API refinements, bug fixes | P9 backend support (delta sync, conflict endpoints) | P10 backend tests, P11 infra |
| **Web** | P1 setup, component prototypes | P7 (full web client) | P10 web E2E tests | P11 web deployment |
| **Mobile** | P1 setup, component prototypes | P8 (full mobile client) | P9 (offline sync, conflict UI) | P10 mobile tests, P11 EAS builds |

---

## 5. Dependencies Between Modules

The dependency graph below defines the strict ordering constraints. An arrow means "must be completed before."

```
P1: Project Setup
 │
 └──► P2: Backend Core
       │
       └──► P3: Authentication
             │
             └──► P4: Diary Entries
                   │
                   ├──► P5: Tagging System
                   │
                   ├──► P6: Attachments
                   │
                   ├──► P7: Web Client ──────────┐
                   │                              │
                   └──► P8: Mobile Client ────────┤
                                                  │
                                                  └──► P9: Sync & Offline
                                                        │
                                                        └──► P10: Testing
                                                              │
                                                              └──► P11: Deployment
```

### Detailed Dependency Matrix

| Module | Hard Dependencies | Soft Dependencies |
|--------|-------------------|-------------------|
| P1: Project Setup | — | — |
| P2: Backend Core | P1 | — |
| P3: Authentication | P2 (DB, config, middleware) | — |
| P4: Diary Entries | P3 (protected routes, `get_current_user`) | — |
| P5: Tagging System | P4 (entries exist to link tags to) | — |
| P6: Attachments | P4 (entries exist to attach files to), P2 (S3 config) | — |
| P7: Web Client | P3 (auth API), P4 (entries API) | P5 (tags API), P6 (attachments API) |
| P8: Mobile Client | P3 (auth API), P4 (entries API) | P5 (tags API), P6 (attachments API) |
| P9: Sync & Offline | P7, P8 (both clients functional) | P4 (`updated_since`, `client_id`, `version`) |
| P10: Testing | P7, P8, P9 (features complete) | All modules |
| P11: Deployment | P10 (tests passing) | — |

### Key Constraint Notes

- **P5 and P6 are independent of each other.** They can be developed in parallel by different developers.
- **P7 and P8 are independent of each other.** Web and mobile can be built simultaneously against the same backend.
- **P7 and P8 can start before P5 and P6 are complete.** The core auth + entries API (M3) is sufficient. Tags and attachments can be integrated into the UI incrementally.
- **P9 requires both P7 and P8.** Offline sync is a mobile-specific feature but must be tested against the same API the web client uses. Both clients should be stable before adding sync complexity.

---

## 6. Estimated Complexity

Complexity reflects implementation effort, testing surface, and risk — not just lines of code.

| Rating | Definition |
|--------|------------|
| **Small** | Straightforward implementation. Well-understood patterns. < 1 day for an experienced developer. |
| **Medium** | Moderate complexity. May involve integration points or non-trivial logic. 1–3 days. |
| **Large** | Significant complexity. Multiple moving parts, edge cases, or unfamiliar territory. 3–5 days. |

### Phase-Level Complexity Summary

| Phase | Overall | Justification |
|-------|:-------:|---------------|
| P1: Project Setup | Small | Boilerplate scaffolding, well-documented tools |
| P2: Backend Core | Medium | Async SQLAlchemy, Alembic, and middleware require careful configuration |
| P3: Authentication | Medium | JWT with refresh token rotation is a common but nuanced pattern |
| P4: Diary Entries | Large | Pagination, filtering, full-text search, version control, idempotency — many intersecting concerns |
| P5: Tagging System | Small | Simple CRUD with a join table |
| P6: Attachments | Medium | S3 integration, pre-signed URLs, file validation add integration complexity |
| P7: Web Client | Large | Full SPA with auth flow, protected routes, multiple pages, responsive design |
| P8: Mobile Client | Large | React Native has platform-specific quirks; navigation, secure storage, native UX patterns |
| P9: Sync & Offline | Large | Most complex phase — network detection, queue management, conflict resolution, state reconciliation |
| P10: Testing | Large | E2E and load testing require infrastructure and realistic test data |
| P11: Deployment | Large | Cloud provisioning, CI/CD, monitoring, and security hardening across multiple services |

### Full Task Complexity Matrix

| Task | Complexity | Risk Factor |
|------|:----------:|-------------|
| 1.1 Initialize monorepo | Small | Low |
| 1.2 Git repository setup | Small | Low |
| 1.3 Docker Compose (Postgres, Minio, API) | Medium | Low — standard Docker patterns |
| 1.4 FastAPI project init | Small | Low |
| 1.5 Next.js project init | Small | Low |
| 1.6 Expo project init | Small | Low — `create-expo-app` handles most setup |
| 1.7 Shared TypeScript types | Small | Low |
| 1.8 GitHub Actions CI | Medium | Medium — matrix builds for three projects |
| 1.9 Developer README | Small | Low |
| 2.1 Pydantic Settings config | Small | Low |
| 2.2 Async SQLAlchemy setup | Medium | Medium — async session lifecycle is tricky |
| 2.3 Alembic async configuration | Medium | Medium — async Alembic env requires specific setup |
| 2.4 Global exception handlers | Small | Low |
| 2.5 CORS middleware | Small | Low |
| 2.6 Request logging | Small | Low |
| 2.7 Rate limiting (`slowapi`) | Medium | Low |
| 2.8 API versioning router | Small | Low |
| 2.9 Health/readiness endpoints | Small | Low |
| 3.1 Users model + migration | Small | Low |
| 3.2 Sessions model + migration | Small | Low |
| 3.3 Password hashing (bcrypt) | Small | Low |
| 3.4 JWT utilities | Medium | Medium — token expiry, claims, secret management |
| 3.5 `get_current_user` dependency | Medium | Medium — must handle expired, malformed, revoked tokens |
| 3.6 Register endpoint | Medium | Low |
| 3.7 Login endpoint | Medium | Low |
| 3.8 Token refresh with rotation | Medium | Medium — must revoke old token atomically |
| 3.9 Logout endpoint | Small | Low |
| 3.10 Profile endpoint | Small | Low |
| 3.11 Auth integration tests | Medium | Low |
| 4.1 Entries model + FTS migration | Medium | Medium — generated `tsvector` column config |
| 4.2 Entry Pydantic schemas | Small | Low |
| 4.3 Create entry (idempotent) | Medium | Medium — `client_id` dedup logic |
| 4.4 List entries (paginated, filtered) | Large | Medium — multiple filters, sort, pagination |
| 4.5 Get entry detail | Small | Low |
| 4.6 Update entry (version check) | Medium | Medium — optimistic concurrency |
| 4.7 Delete entry (soft) | Small | Low |
| 4.8 Full-text search with snippets | Large | Medium — PostgreSQL FTS tuning |
| 4.9 Entry service layer | Medium | Low |
| 4.10 Entry integration tests | Medium | Low |
| 5.1 Tags + entry_tags models | Small | Low |
| 5.2 List tags with count | Medium | Low — aggregate query |
| 5.3 Create tag | Small | Low |
| 5.4 Update tag | Small | Low |
| 5.5 Delete tag (cascade) | Small | Low |
| 5.6 Tag integration in entries | Medium | Medium — transactional tag assignment |
| 5.7 Tags in entry responses | Small | Low |
| 5.8 Tag tests | Medium | Low |
| 6.1 Attachments model | Small | Low |
| 6.2 S3/Minio client service | Medium | Medium — credential handling, error mapping |
| 6.3 File upload endpoint | Large | Medium — multipart parsing, streaming, size limits |
| 6.4 List attachments with pre-signed URLs | Medium | Low |
| 6.5 Delete attachment | Small | Low |
| 6.6 File type/size validation | Small | Low |
| 6.7 Attachment tests | Medium | Medium — requires Minio in test env |
| 7.1 Axios client + interceptors | Medium | Medium — silent 401 refresh without race conditions |
| 7.2 TanStack Query setup | Small | Low |
| 7.3 AuthProvider (web) | Large | High — token lifecycle, redirect logic, refresh timing |
| 7.4 Login page | Medium | Low |
| 7.5 Register page | Medium | Low |
| 7.6 Dashboard layout | Medium | Low |
| 7.7 Entry list page | Large | Medium — pagination, filters, query state |
| 7.8 Entry detail/edit page | Large | Medium — form state, tag picker, mood selector |
| 7.9 Tag management page | Medium | Low |
| 7.10 Search page | Medium | Low |
| 7.11 Settings page | Small | Low |
| 7.12 Route protection middleware | Medium | Medium — Next.js middleware edge cases |
| 7.13 Responsive design pass | Medium | Low |
| 7.14 UI component library | Medium | Low |
| 8.1 Axios + Query setup (mobile) | Medium | Low |
| 8.2 AuthProvider (mobile, SecureStore) | Large | High — token persistence, app restart auth |
| 8.3 Login/register screens | Medium | Low |
| 8.4 Tab navigator | Medium | Low |
| 8.5 Entry list (FlatList, infinite scroll) | Large | Medium — virtualized list performance |
| 8.6 Entry detail/edit screen | Large | Medium — keyboard handling, native form UX |
| 8.7 Search screen | Medium | Low |
| 8.8 Settings screen | Small | Low |
| 8.9 Mobile UI components | Medium | Low |
| 8.10 Auth navigation guard | Medium | Low |
| 9.1 Offline storage abstraction | Medium | Low |
| 9.2 Sync manager (queue, retry) | Large | High — most complex piece; ordering, idempotency |
| 9.3 Network status detection | Medium | Medium — `NetInfo` edge cases |
| 9.4 Offline create flow | Large | High — must queue, dedup, handle errors |
| 9.5 Offline update flow | Large | High — version tracking across offline edits |
| 9.6 Conflict resolution UI | Large | High — diff display, user decision handling |
| 9.7 Delta sync (`updated_since`) | Medium | Medium — timestamp tracking, cache merge |
| 9.8 SyncProvider (status UI) | Medium | Low |
| 9.9 Cache invalidation after sync | Small | Low |
| 9.10 Sync integration tests | Large | High — simulating offline scenarios is complex |
| 10.1 Backend unit tests | Medium | Low |
| 10.2 Backend integration tests | Large | Medium — test DB setup, fixtures |
| 10.3 Web component tests | Medium | Low |
| 10.4 Web E2E tests (Playwright) | Large | Medium — browser automation flakiness |
| 10.5 Mobile E2E tests | Large | High — device/simulator test tooling maturity |
| 10.6 Load testing (Locust) | Medium | Low |
| 10.7 Security audit | Medium | Medium — requires expertise |
| 10.8 Accessibility audit | Medium | Low |
| 11.1 Backend Dockerfile | Medium | Low |
| 11.2 Web Dockerfile | Medium | Low |
| 11.3 Provision PostgreSQL | Medium | Medium — production config, backups, networking |
| 11.4 Provision S3 bucket | Small | Low |
| 11.5 Container orchestration (ECS/Cloud Run) | Large | High — networking, scaling, health checks |
| 11.6 Web deployment (Vercel or container) | Medium | Low |
| 11.7 Secrets management | Small | Low |
| 11.8 CI/CD staging pipeline | Large | Medium — multi-service, multi-stage pipeline |
| 11.9 CI/CD production pipeline | Medium | Medium — gated deploy, rollback strategy |
| 11.10 Monitoring setup | Medium | Medium — instrumentation, dashboard design |
| 11.11 CDN / WAF configuration | Medium | Low |
| 11.12 Expo EAS Build config | Medium | Medium — Apple/Google signing and submission |
| 11.13 Expo OTA updates config | Small | Low |

### Aggregate Complexity Distribution

```
Small:  34 tasks  ██████████████████████████████████░░░░░░░░░░  33%
Medium: 46 tasks  ██████████████████████████████████████████████  45%
Large:  23 tasks  ██████████████████████████░░░░░░░░░░░░░░░░░░  22%
                  ─────────────────────────────────────────────
Total: 103 tasks
```

---

## Appendix A: Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Offline sync produces data corruption | High | Medium | Idempotent `client_id`, version checks, conflict UI — never auto-merge without user intent |
| JWT secret leak | Critical | Low | Secret in managed vault, not in env files; token rotation; short access token TTL |
| React Native performance on entry list | Medium | Medium | Virtualized FlatList, query pagination, avoid re-renders with `React.memo` |
| Alembic migration conflicts in team | Medium | Medium | One developer owns migration creation; squash on release |
| S3 upload failure leaves orphaned metadata | Low | Medium | Transaction: write DB record only after S3 upload confirms; cleanup job for orphans |
| Full-text search too slow at scale | Medium | Low | PostgreSQL GIN index handles < 500K entries; plan to Elasticsearch migration path at scale |

## Appendix B: Definition of Done

A task is considered **done** when:

1. Code is implemented and compiles without warnings.
2. Unit or integration tests are written and passing.
3. Code has been reviewed by at least one other developer.
4. No new lint or type-check errors are introduced.
5. The feature is demonstrable (via API test, browser, or simulator).
6. Documentation is updated if the change affects API contracts or setup instructions.
