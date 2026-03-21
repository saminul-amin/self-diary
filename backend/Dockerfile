# ──────────────────────────────────────────────
# SelfDiary Backend — Dockerfile
# ──────────────────────────────────────────────
# Multi-stage build for production.
# Dev usage: docker compose up (uses --reload via command override)
# ──────────────────────────────────────────────

# ── Stage 1: Dependencies ──
FROM python:3.12-slim AS deps

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install only production dependencies first (cache layer)
COPY pyproject.toml ./
RUN pip install --no-cache-dir --target=/deps .

# ── Stage 2: Production ──
FROM python:3.12-slim AS production

# Security: install updates and create non-root user
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /deps /usr/local/lib/python3.12/site-packages

# Copy application code
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
