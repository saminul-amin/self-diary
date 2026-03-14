# ──────────────────────────────────────────────
# SelfDiary Backend — Dockerfile
# ──────────────────────────────────────────────
# Multi-stage build for production.
# Dev usage: docker compose up (uses --reload via command override)
# ──────────────────────────────────────────────

# ── Stage 1: Build ──
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

# ── Stage 2: Production ──
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
