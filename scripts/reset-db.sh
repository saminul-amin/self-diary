#!/usr/bin/env bash
# ──────────────────────────────────────────────
# reset-db.sh — Drop and recreate the local database
# ──────────────────────────────────────────────
# Usage:
#   ./scripts/reset-db.sh
#
# WARNING: This destroys all local data.
# ──────────────────────────────────────────────

set -euo pipefail

echo "Stopping containers..."
docker compose down -v

echo "Starting PostgreSQL..."
docker compose up -d postgres

echo "Waiting for PostgreSQL to accept connections..."
sleep 3

echo "Running migrations..."
cd backend && alembic upgrade head

echo "Database reset complete."
