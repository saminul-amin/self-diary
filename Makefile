# ──────────────────────────────────────────────
# SelfDiary — Makefile
# ──────────────────────────────────────────────
# Common development commands.
# Usage: make <target>
# ──────────────────────────────────────────────

.PHONY: help dev stop restart logs migrate seed test lint clean format

# ─── Default ───
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ─── Development ───
dev: ## Start all development services (Postgres, Minio, API)
	docker compose up -d

stop: ## Stop all Docker services
	docker compose down

restart: ## Restart all Docker services
	docker compose down && docker compose up -d

logs: ## Follow backend API logs
	docker compose logs -f api

# ─── Database ───
migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new MSG="add users table")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed database with sample data
	cd backend && python scripts/seed.py

reset-db: ## Drop and recreate the database (DESTRUCTIVE)
	docker compose down -v
	docker compose up -d postgres
	@echo "Waiting for PostgreSQL to start..."
	@sleep 3
	cd backend && alembic upgrade head

# ─── Testing ───
test: ## Run all backend tests
	cd backend && python -m pytest -v

test-cov: ## Run backend tests with coverage report
	cd backend && python -m pytest --cov=app --cov-report=term-missing

# ─── Code Quality ───
lint: ## Lint all projects
	cd backend && ruff check .
	cd web && npx eslint .
	cd mobile && npx eslint .

format: ## Auto-format all projects
	cd backend && ruff format .
	cd web && npx prettier --write "src/**/*.{ts,tsx}"
	cd mobile && npx prettier --write "{app,components,hooks,lib}/**/*.{ts,tsx}"

typecheck: ## Type-check all projects
	cd backend && mypy app/
	cd web && npx tsc --noEmit
	cd mobile && npx tsc --noEmit

# ─── Cleanup ───
clean: ## Remove all containers, volumes, and caches
	docker compose down -v --remove-orphans
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache
	rm -rf web/.next web/node_modules
	rm -rf mobile/.expo mobile/node_modules
