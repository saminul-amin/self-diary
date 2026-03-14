# SelfDiary

A production-grade, cross-platform personal diary application. Write, organize, and reflect on daily entries from any device — with cloud sync, offline support, and full privacy.

---

## Project Overview

SelfDiary lets users maintain a private digital diary that works seamlessly across web browsers and mobile devices. Entries are synchronized in real time via a REST API, while the mobile app supports full offline writing with automatic conflict resolution on reconnect.

### Key Capabilities

- **Cross-platform** — Web (Next.js) and mobile (React Native / Expo) clients
- **Cloud sync** — Entries are available on every device within seconds
- **Offline-first mobile** — Write without connectivity; changes sync automatically
- **Rich organization** — Tags, mood tracking, full-text search, media attachments
- **Secure by default** — JWT authentication, bcrypt password hashing, encrypted transport

---

## Architecture Summary

```
┌─────────────┐     ┌──────────────┐
│  Next.js    │     │ React Native │
│  Web Client │     │ Mobile Client│
└──────┬──────┘     └──────┬───────┘
       │     HTTPS / REST    │
       └──────────┬──────────┘
                  │
        ┌─────────▼─────────┐
        │   FastAPI Backend  │
        │   (Python, JWT)    │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │   PostgreSQL       │
        └────────────────────┘
```

Two independent frontend clients consume a single versioned REST API. The backend handles authentication, business logic, and data persistence. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design and [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for the development roadmap.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Web Frontend** | Next.js (App Router), TypeScript, Tailwind CSS, TanStack Query, Axios |
| **Mobile App** | React Native, Expo (Expo Router), TypeScript, TanStack Query, AsyncStorage |
| **Backend API** | FastAPI, Python 3.12+, SQLAlchemy (async), Pydantic v2 |
| **Database** | PostgreSQL 16 |
| **Auth** | JWT (access + refresh tokens), bcrypt |
| **Object Storage** | S3-compatible (Minio for local dev) |
| **Infrastructure** | Docker, Docker Compose, GitHub Actions CI/CD |

---

## Development Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- [Python 3.12+](https://www.python.org/downloads/)
- [Node.js 20 LTS](https://nodejs.org/)
- [Expo CLI](https://docs.expo.dev/get-started/installation/) (`npm install -g expo-cli`)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd diary
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` to set secrets for local development. The defaults work with Docker Compose out of the box.

### 3. Start Infrastructure Services

```bash
docker compose up -d
```

This starts **PostgreSQL** and **Minio** (S3-compatible storage). The FastAPI backend can be run in Docker or locally.

### 4. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head             # Run database migrations
uvicorn app.main:app --reload    # Start dev server at http://localhost:8000
```

API docs are available at `http://localhost:8000/docs` (Swagger UI).

### 5. Web Client Setup

```bash
cd web
npm install
npm run dev                      # Start dev server at http://localhost:3000
```

### 6. Mobile Client Setup

```bash
cd mobile
npm install
npx expo start                   # Opens Expo dev tools
```

Scan the QR code with Expo Go (iOS/Android) or press `i` / `a` to open in a simulator.

### Quick Start (All Services)

```bash
make dev    # Starts Postgres, Minio, backend, and web client
```

---

## Repository Structure

```
diary/
├── docs/                    # Architecture and planning documents
│   ├── ARCHITECTURE.md      # System design, schema, API contracts
│   └── IMPLEMENTATION_PLAN.md # Development roadmap and task breakdown
│
├── backend/                 # FastAPI backend (Python)
│   ├── app/                 # Application source code
│   │   ├── api/             # Route handlers (versioned)
│   │   ├── core/            # Security, config, middleware
│   │   ├── db/              # Database engine, migrations
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # Business logic layer
│   ├── tests/               # pytest test suite
│   ├── Dockerfile           # Production container image
│   └── pyproject.toml       # Python project config and dependencies
│
├── web/                     # Next.js web client (TypeScript)
│   ├── src/
│   │   ├── app/             # App Router pages and layouts
│   │   ├── components/      # React components
│   │   ├── hooks/           # TanStack Query hooks
│   │   ├── lib/             # Axios client, auth, utilities
│   │   ├── types/           # TypeScript type definitions
│   │   └── providers/       # React context providers
│   └── package.json
│
├── mobile/                  # React Native mobile client (Expo)
│   ├── app/                 # Expo Router screens
│   ├── components/          # React Native components
│   ├── hooks/               # Query hooks + sync hook
│   ├── lib/                 # API client, sync manager, offline storage
│   ├── types/               # TypeScript type definitions
│   └── package.json
│
├── infra/                   # Infrastructure configuration
│   ├── docker/              # Per-service Dockerfiles (if not colocated)
│   └── nginx/               # Nginx reverse proxy config (production)
│
├── scripts/                 # Developer utility scripts
│   ├── seed.py              # Database seed data
│   └── reset-db.sh          # Drop and recreate local database
│
├── docker-compose.yml       # Local development services
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── .editorconfig            # Consistent editor formatting
├── .pre-commit-config.yaml  # Git pre-commit hooks
├── Makefile                 # Common development commands
└── README.md                # This file
```

---

## Common Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all development services |
| `make stop` | Stop all Docker services |
| `make migrate` | Run Alembic database migrations |
| `make seed` | Seed database with sample data |
| `make test` | Run all backend tests |
| `make lint` | Lint and type-check all projects |
| `make clean` | Remove containers, volumes, and caches |

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full system architecture: schema, API design, security, deployment |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | Phased roadmap, milestones, task breakdown, complexity estimates |

---

## License

Private — All rights reserved.
