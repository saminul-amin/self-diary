# SelfDiary — Security Audit Report

> **Date:** 2026-03-14
> **Scope:** Full OWASP Top 10 review — Backend API, Web Client, Mobile Client
> **Standard:** OWASP Top 10 (2021), OWASP ASVS L1

---

## Executive Summary

The SelfDiary application demonstrates solid security foundations: parameterized
queries via SQLAlchemy ORM, bcrypt password hashing, JWT with refresh token
rotation, per-endpoint ownership enforcement, and file upload type restrictions.

**Critical findings requiring remediation before production:**

| Severity | Count | Summary |
|----------|:-----:|---------|
| Critical | 1 | Default JWT secret with no production guard |
| High | 1 | No rate limiting on authentication endpoints |
| Medium | 3 | Client-only MIME validation, missing security headers, unmaintained JWT library |
| Low | 2 | Overly permissive CORS methods/headers, in-memory file size check |
| Info | 2 | Swagger disabled in prod, generic error responses |

---

## Dependency Vulnerability Scan

### Backend (Python)

| Package | Version | Status |
|---------|---------|--------|
| fastapi | 0.129.0 | ✅ No known CVEs |
| sqlalchemy | 2.0.46 | ✅ No known CVEs |
| pydantic | 2.12.5 | ✅ No known CVEs |
| bcrypt | 5.0.0 | ✅ No known CVEs |
| python-jose | 3.5.0 | ⚠️ Unmaintained — consider PyJWT or joserfc |
| boto3 | 1.42.68 | ✅ No known CVEs |
| uvicorn | 0.40.0 | ✅ No known CVEs |
| slowapi | 0.1.9 | ✅ No known CVEs (but not integrated!) |
| httpx | 0.28.1 | ✅ No known CVEs |

### Web Client (npm)

| Finding | Severity | Detail |
|---------|----------|--------|
| next (10.0.0–15.5.13) | Moderate | Unbounded `next/image` disk cache growth ([GHSA-3x4c-7xq6-9pq8](https://github.com/advisories/GHSA-3x4c-7xq6-9pq8)). Fix: `npm audit fix` |

### Mobile Client (npm)

| Finding | Severity | Detail |
|---------|----------|--------|
| tar ≤ 7.5.10 | High | Multiple path traversal vulnerabilities via hardlinks/symlinks. Transitive dependency via `@expo/cli → cacache → tar`. Fix: update Expo SDK when patch available |

---

## OWASP Top 10 Assessment

### A01:2021 — Broken Access Control ✅ PASS

| Control | Status | Evidence |
|---------|--------|----------|
| Per-endpoint auth | ✅ | All protected routes use `Depends(get_current_user)` |
| Row-level ownership | ✅ | Entries, tags, and attachments filter by `user_id`; cross-user access returns 403/404 |
| Token type discrimination | ✅ | Access vs refresh tokens have `type` claim; refresh cannot access protected routes |
| Session revocation | ✅ | Refresh token rotation revokes old session; logout invalidates current session |
| Directory traversal | ✅ | Filenames sanitized via `PureWindowsPath(name).name` before S3 upload |

### A02:2021 — Cryptographic Failures ⚠️ NEEDS ATTENTION

| Control | Status | Evidence |
|---------|--------|----------|
| Password hashing | ✅ | bcrypt with 12 rounds (default gensalt) |
| JWT signing | ✅ | HS256 with configurable secret |
| **JWT secret default** | ❌ **CRITICAL** | Defaults to `"dev-secret-change-in-production"` — no startup validation that the secret was changed |
| TLS enforcement | ⚠️ | No HSTS header; relies on deployment infrastructure |
| Secrets in code | ✅ | All secrets sourced from env vars via Pydantic Settings |

**Remediation:**
```python
# app/config.py — add startup validation
@model_validator(mode="after")
def validate_production_secrets(self) -> "Settings":
    if self.environment == "production" and "dev-secret" in self.jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY must be changed for production")
    return self
```

### A03:2021 — Injection ✅ PASS

| Control | Status | Evidence |
|---------|--------|----------|
| SQL injection | ✅ | All queries use SQLAlchemy ORM with parameterized statements; no raw SQL or `text()` calls |
| Command injection | ✅ | No shell command execution in codebase |
| XSS (backend) | ✅ | JSON-only API, `Content-Type: application/json` on all responses |
| XSS (frontend) | ✅ | React auto-escapes JSX expressions; no `dangerouslySetInnerHTML` usage |

### A04:2021 — Insecure Design ⚠️ NEEDS ATTENTION

| Control | Status | Evidence |
|---------|--------|----------|
| Input validation | ✅ | Pydantic schemas enforce types, lengths, formats on all inputs |
| Password policy | ✅ | Min 8 chars, max 128 chars enforced at schema level |
| **Rate limiting** | ❌ **HIGH** | `slowapi` is listed as a dependency but **never integrated** — auth endpoints are unprotected against brute-force |
| Idempotency | ✅ | Entry creation supports `client_id` for idempotent writes |
| Optimistic concurrency | ✅ | Version field prevents lost updates (409 on stale version) |

**Remediation:**
```python
# app/main.py — integrate slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# app/api/v1/endpoints/auth.py — apply to auth routes
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...): ...
```

### A05:2021 — Security Misconfiguration ⚠️ NEEDS ATTENTION

| Control | Status | Evidence |
|---------|--------|----------|
| CORS origins | ✅ | Configured via env var, defaults to `localhost:3000` |
| CORS methods/headers | ⚠️ LOW | `allow_methods=["*"]`, `allow_headers=["*"]` — should scope to actual needs |
| Debug endpoints | ✅ | Swagger/ReDoc disabled when `environment != "development"` |
| **Security headers** | ❌ **MEDIUM** | No HSTS, X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy |
| Error disclosure | ✅ | Unhandled exceptions return generic message, no stack traces |

**Remediation — add security headers middleware:**
```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "0"  # Modern browsers: rely on CSP
    return response
```

### A06:2021 — Vulnerable and Outdated Components ⚠️ NEEDS ATTENTION

| Control | Status | Evidence |
|---------|--------|----------|
| `python-jose` | ⚠️ MEDIUM | Unmaintained since 2022; recommend migrating to `PyJWT>=2.8` or `joserfc` |
| `next` (web) | ⚠️ Moderate | `next/image` disk cache advisory — update to 15.5.14+ |
| `tar` (mobile) | ⚠️ High | Transitive via Expo — monitor for Expo SDK patch |
| Other deps | ✅ | All other packages at current stable versions |

### A07:2021 — Identification and Authentication Failures ✅ PASS (with caveats)

| Control | Status | Evidence |
|---------|--------|----------|
| Password storage | ✅ | bcrypt, 12 rounds |
| Token expiry | ✅ | 15 min access, 30 day refresh |
| Token rotation | ✅ | Refresh token rotation with session revocation |
| Credential stuffing protection | ❌ | No rate limiting (see A04) |
| Multi-factor auth | ⬜ | Not implemented (out of scope for v1) |

### A08:2021 — Software and Data Integrity Failures ✅ PASS

| Control | Status | Evidence |
|---------|--------|----------|
| Dependency integrity | ✅ | `package-lock.json` present for web/mobile; pip uses version pins |
| CI pipeline | ✅ | Pre-commit hooks run linting, type-checking |
| Deserialization | ✅ | Pydantic strict parsing — no pickle/yaml.load usage |

### A09:2021 — Security Logging and Monitoring Failures ⚠️ PARTIAL

| Control | Status | Evidence |
|---------|--------|----------|
| Request logging | ✅ | Structured JSON logs with method, path, status, duration |
| Request ID tracing | ✅ | `X-Request-ID` header set by middleware |
| Auth event logging | ⚠️ | Failed login attempts are not explicitly logged with IP/email |
| Error monitoring | ⬜ | Sentry integration planned for P11 |

### A10:2021 — Server-Side Request Forgery (SSRF) ✅ PASS

| Control | Status | Evidence |
|---------|--------|----------|
| Outbound requests | ✅ | Only outbound calls are to configured S3/Minio endpoint — no user-supplied URLs used in server requests |
| S3 endpoint | ✅ | Configured via env var, not user input |

---

## Remediation Priority

| # | Finding | Severity | Effort | Phase |
|---|---------|----------|--------|-------|
| 1 | Add JWT secret production validation | Critical | Small | Pre-deploy |
| 2 | Integrate slowapi rate limiting on auth endpoints | High | Small | Pre-deploy |
| 3 | Add magic-byte file type validation (e.g., `python-magic`) | Medium | Small | P11 |
| 4 | Add security response headers middleware | Medium | Small | P11 |
| 5 | Migrate from `python-jose` to `PyJWT` | Medium | Medium | P11 |
| 6 | Update `next` to fix image cache advisory | Moderate | Small | P11 |
| 7 | Scope CORS methods/headers | Low | Small | P11 |
| 8 | Add streaming file size enforcement | Low | Small | P11 |
| 9 | Add failed auth attempt logging | Low | Small | P11 |

---

## Conclusion

The application follows secure coding practices at its core — parameterized
queries, proper password hashing, JWT with rotation, and per-row ownership
enforcement. The two items requiring **immediate remediation before production**
are: (1) enforcing a non-default JWT secret, and (2) enabling rate limiting on
authentication endpoints. All other findings are low-to-medium severity and can
be addressed during the deployment phase.
