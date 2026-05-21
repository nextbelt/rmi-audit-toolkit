# RMI Audit Toolkit

NextBelt LLC's internal Reliability Maturity Index (RMI) audit platform.
Used by NextBelt consultants to run scored, evidence-backed reliability
assessments on client sites and produce executive PDF reports.

> **Treat this as a client-facing tool even though it is internal.** It holds
> assessment data tied to named clients. Follow the security policy in
> [SECURITY.md](#security) when touching auth, secrets, or uploads.

## Stack

- **Backend:** FastAPI · SQLAlchemy 2 · Pydantic 2 · bcrypt + JWT
- **Frontend:** React 18 · TypeScript · Vite · Zustand · Recharts
- **Database:** PostgreSQL (Railway) · SQLite (local)
- **Hosting:** Railway (NIXPACKS) — backend via `uvicorn`, frontend via `serve`
- **Reports:** ReportLab + matplotlib

## Architecture

```
┌────────────┐    HTTPS    ┌──────────────────┐    SQL    ┌──────────┐
│  Browser   │ ──────────► │ FastAPI backend  │ ────────► │ Postgres │
│  (React)   │ ◄────────── │  /api/v2/* + auth│ ◄──────── │          │
└────────────┘             └──────────────────┘           └──────────┘
                                  │
                                  ▼
                          ./uploads/assessments/<id>/cmms/...
                          (authenticated downloads only)
```

The product API lives under **`/api/v2/`** (5-domain × 15-subdomain
framework). The legacy `/assessments/{id}/finalize`, `/generate-report`,
`/report/download`, and `/analyze-work-orders` routes still exist for
compatibility with v1 IDs.

## Local setup

### Backend

```powershell
cd backend
pip install -r requirements.txt

# REQUIRED — refuses to boot without a strong key in production
$env:SECRET_KEY = "$(python -c "import secrets; print(secrets.token_urlsafe(48))")"
$env:ENVIRONMENT = "development"

# Optional: seed the first admin user (skip to add users via /register later)
$env:INITIAL_ADMIN_EMAIL = "you@example.com"
$env:INITIAL_ADMIN_PASSWORD = "ALongStrongPassword!2026"

python init_db.py
python -m uvicorn main:app --reload --port 8000
```

API → http://localhost:8000 · Swagger UI → http://localhost:8000/docs ·
Health → http://localhost:8000/healthz

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

UI → http://localhost:3000 (proxies API calls to `http://localhost:8000`).

## Authentication

- `POST /token` — OAuth2 password flow. Rate-limited per IP+email
  (`LOGIN_RATE_LIMIT_PER_MIN`, default 10).
- `GET /users/me` — returns the JWT bearer's user record.
- `POST /password-reset/request` — issues a 30-minute HMAC-signed reset
  token. In `ENVIRONMENT=development` the token is returned in the response
  body; in production it is written to the server log only.
- `POST /password-reset/confirm` — applies a new password (min 12 chars).

There is no `LOCAL_DEV_MODE`; bcrypt is the only password path.

## Security policy

- **`SECRET_KEY` must be set** in any environment with `ENVIRONMENT=production`.
  The app refuses to boot if the key is the default or shorter than 32 chars.
- **No public uploads.** Evidence files are served only via authenticated
  `GET /uploads/{path}`; files under `uploads/assessments/<id>/` are scoped
  by per-assessment membership.
- **Uploads are sanitized.** Filenames are stripped, randomized, and validated
  against an extension allowlist (`csv, xls, xlsx, pdf, png, jpg, jpeg`).
  `MAX_UPLOAD_SIZE` is enforced server-side.
- **Per-assessment RBAC.** A user can read or modify an assessment iff they
  are an admin, the creator, or an explicit member (`assessment_members`).
- **Audit log.** Every login, user mutation, password reset, finalize, and
  scoring call writes to the `audit_log` table.
- **No committed secrets.** `supa_vars.json` was removed; `.gitignore`
  excludes any `*vars*.json`, `*secrets*.json`, `*credentials*.json`, and `.env*`.

If you suspect a secret was committed, rotate it immediately:
1. Railway → Postgres → reset password
2. Railway → backend service → regenerate `SECRET_KEY`
3. Supabase → Project Settings → API → rotate `service_role` and `anon` keys

## Scoring policy

See [SCORING_POLICY.md](SCORING_POLICY.md) — every cap, threshold, and weight
is documented there. The implementation is in
`backend/scoring_engine_v2.py`.

## Testing

```powershell
cd backend
pytest
```

The suite covers:
- Login / wrong-password / unknown-user paths (`tests/test_auth_routes.py`)
- Password reset full flow + token tampering (`tests/test_security_utils.py`,
  `tests/test_auth_routes.py`)
- Per-assessment RBAC (`tests/test_rbac.py`)
- Evidence cap regression (`tests/test_scoring_evidence_cap.py`)
- SECRET_KEY hardening (`tests/test_secret_check.py`)
- Upload sanitization, size, extension allowlist (`tests/test_upload_safety.py`)

CI runs the same set on every push/PR (`.github/workflows/ci.yml`) plus
`pip-audit`, `npm audit`, and a secret-name scan that fails the build if
files matching `supa_vars*.json` / `*credentials*.json` are ever tracked.

## Deployment

- **Backend:** `backend/railway.json` — `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Frontend:** `frontend/railway.json` — builds with `tsc && vite build`,
  serves the static `dist/` with `serve` (NOT `vite preview`).

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full Railway + Supabase setup.

## Maintenance

- `scripts/cleanup_dead_files.sh` — removes dead one-off backend scripts.
- `scripts/rotate_secrets.sh` — rotates `SECRET_KEY` + Supabase keys + Railway
  Postgres password; pushes new values to Railway and redeploys.
- `scripts/setup_supabase_storage.sh` — creates the private `evidence`
  bucket and switches the backend to `STORAGE_BACKEND=supabase`.

### Migrations (Alembic)

Schema is owned by Alembic; see [backend/alembic/README.md](backend/alembic/README.md).
The previous `run_migrations()` shim was removed. On deploy, Railway runs
`alembic upgrade head` before `uvicorn` (see `backend/railway.json`).

```bash
cd backend
alembic revision --autogenerate -m "describe change"   # after editing a model
alembic upgrade head
alembic downgrade -1
```

To switch the existing Railway DB to Alembic without re-applying DDL:

```bash
railway run --service rmi-audit-toolkit-backend alembic stamp ac8ed3c6f884
```

### Storage

`STORAGE_BACKEND=local` (default, dev) or `supabase` (production). See
`backend/storage.py`. Files live under
`assessments/<id>/<kind>/<uuid_filename>` so the per-assessment RBAC in
`GET /uploads/{path}` can enforce ownership at download time.

## Module index

| Module | Purpose |
|---|---|
| `backend/main.py` | App entry, auth, upload download, finalize/report routes |
| `backend/api_v2.py` | v2 product API (`/api/v2/*`) |
| `backend/auth.py` | JWT decode middleware |
| `backend/config.py` | Settings + production secret check |
| `backend/security_utils.py` | Upload sanitization, rate limiter, reset tokens |
| `backend/rbac.py` | Per-assessment ownership checks |
| `backend/audit.py` | Audit log helper |
| `backend/models.py` | v1 SQLAlchemy models (kept for legacy assessment IDs) |
| `backend/models_v2.py` | v2 models (domains, subdomains, etc.) |
| `backend/models_extra.py` | `audit_log` + `assessment_members` |
| `backend/scoring_engine.py` | v1 scoring (legacy reports only) |
| `backend/scoring_engine_v2.py` | v2 scoring (current product) |
| `backend/report_generator.py` | v1 PDF generator (legacy IDs) |
| `backend/report_generator_v2.py` | v2 PDF generator (subdomain-based) |
| `backend/routing_engine.py` | Question routing by assessment mode |
| `backend/benchmarking_engine.py` | Percentile benchmarks |
| `backend/practice_engine.py` | Practice library + recommendations |
| `backend/observation_module.py` | Field observation persistence |
| `backend/data_analysis_module.py` | CMMS work-order analysis |
| `backend/iso14224_module.py` | ISO 14224 hierarchy quality check |
| `backend/ai_scoring.py` | Optional GPT-4o-mini text-response scoring |
| `frontend/src/App.tsx` | Route table + auth header |
| `frontend/src/api/client.ts` | Auth + shared HTTP client |
| `frontend/src/api/clientV2.ts` | v2 API client |
| `frontend/src/api/store.ts` | Auth store (Zustand) |
| `frontend/src/api/storeV2.ts` | Assessment store (Zustand) |
| `frontend/src/views/Login.tsx` | Sign-in + password reset flow |
| `frontend/src/views/DashboardV2.tsx` | Assessment list + create |
| `frontend/src/views/AssessmentV2Detail.tsx` | Interview, scoring, benchmark, practices |
| `frontend/src/views/UserManagement.tsx` | Admin user list |

## Built by

NextBelt LLC · https://next-belt.com · nextbelt@next-belt.com
