# SelfDiary — Web Client

Next.js 15 application with React 19, TypeScript, Tailwind CSS 4, TanStack Query 5, and Axios.

## Setup

```bash
npm install
cp .env.local.example .env.local  # adjust API_BASE_URL if needed
npm run dev
```

The app runs on `http://localhost:3000` and expects the backend API at `http://localhost:8000`.

## Architecture

- **App Router** with route groups: `(auth)` for login/register, `(dashboard)` for authenticated views
- **In-memory JWT** — tokens are never stored in localStorage; silent refresh via Axios interceptor
- **TanStack Query** — all server state fetched/cached via custom hooks in `src/hooks/`
- **Tailwind CSS 4** — utility-first styling with indigo accent color

## Routes

| Route           | Description                                          |
| --------------- | ---------------------------------------------------- |
| `/login`        | Sign in                                              |
| `/register`     | Create account                                       |
| `/entries`      | Entry list with mood/favorite filters and pagination |
| `/entries/new`  | Create a new diary entry                             |
| `/entries/[id]` | View and edit an existing entry                      |
| `/tags`         | Tag management with color picker                     |
| `/search`       | Full-text search across entries                      |
| `/settings`     | Profile info and sign out                            |

## Key Directories

```
src/
├── app/            # Next.js App Router pages & layouts
├── components/     # Reusable UI, entries, tags, auth, layout components
├── hooks/          # TanStack Query hooks (useEntries, useTags)
├── lib/            # API client, auth helpers, utilities
├── providers/      # React context providers (Query, Auth)
└── types/          # TypeScript API interfaces
```
