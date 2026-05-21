# Deployment guide

Production runs on Railway: one service for the FastAPI backend, one for the
React frontend (built with Vite, served by `serve`), one for Postgres.
Supabase provides Storage for uploaded evidence (private bucket).

Authoritative module index is in [README.md](README.md). This document is the
operational runbook — secrets, migrations, storage, rotation.

---

## 1. First-time setup

### 1.1 Backend on Railway

Service: **rmi-audit-toolkit-backend**

Required env vars (set in Railway → service → Variables):

| Var | Value |
|---|---|
| `DATABASE_URL` | provided by the Postgres plugin |
| `SECRET_KEY` | output of `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ENVIRONMENT` | `production` (refuses to boot if `SECRET_KEY` is weak) |
| `FRONTEND_URL` | `https://<your-frontend>.up.railway.app` |
| `INITIAL_ADMIN_EMAIL` | one-time seed; remove after the admin user exists |
| `INITIAL_ADMIN_PASSWORD` | ≥12 chars; remove after seed |
| `LOGIN_RATE_LIMIT_PER_MIN` | optional; default 10 |
| `STORAGE_BACKEND` | `supabase` for production, `local` only for dev |
| `SUPABASE_URL` | `https://<ref>.supabase.co` |
| `SUPABASE_SERVICE_KEY` | service_role key — backend only, never frontend |
| `SUPABASE_BUCKET` | `evidence` (or your bucket name) |
| `OPENAI_API_KEY` | optional, for AI-assisted text scoring |

`backend/railway.json` already does the right thing on deploy:

```json
"startCommand": "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT"
```

That runs all pending Alembic migrations before starting uvicorn. The
healthcheck path is `/healthz`.

### 1.2 Frontend on Railway

Service: **rmi-audit-toolkit-frontend**

| Var | Value |
|---|---|
| `VITE_API_URL` | `https://<your-backend>.up.railway.app` |
| `VITE_SUPABASE_URL` | same as backend |
| `VITE_SUPABASE_ANON_KEY` | public anon key (NEVER the service key) |

`frontend/railway.json` builds with `tsc && vite build` and serves the
static `dist/` with `npx serve -s dist`. **It does not use `vite preview`
(that is a dev preview server, not a production server).**

### 1.3 Supabase

The backend does not use Supabase Auth (it has its own JWT + bcrypt path).
Supabase is used for **Storage only** — a private bucket called `evidence`.

To set up the bucket:

```bash
supabase login
supabase link --project-ref <your-ref>
bash scripts/setup_supabase_storage.sh
```

The script creates a private bucket and pushes `STORAGE_BACKEND=supabase`
and `SUPABASE_BUCKET=evidence` to the Railway backend service.

### 1.4 First admin user

After the backend is up and the DB is migrated, seed an initial admin one of
two ways:

**Option A: env-driven seed (recommended)** — set
`INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` (≥12 chars), then run:

```bash
railway run --service rmi-audit-toolkit-backend python init_db.py
```

`init_db.py` skips the admin creation step if those env vars are absent, so
it is safe to redeploy after the admin exists.

**Option B: existing admin promotes a teammate** — admins can hit
`POST /register` from the frontend's user-management UI.

---

## 2. Database migrations (Alembic)

All schema changes go through Alembic. The previous `run_migrations()`
column-add migrator has been removed.

### 2.1 Day-to-day developer workflow

```bash
cd backend

# Edit a model. Then:
alembic revision --autogenerate -m "describe the change"

# Inspect the generated file in alembic/versions/ — autogenerate is good but
# not perfect; review it before committing.
alembic upgrade head           # apply to local DB
alembic current                # see where the DB is
alembic history                # see all revisions
alembic downgrade -1           # roll back one revision (if you must)
```

### 2.2 First Alembic deploy against the existing populated Postgres

The current Railway DB was created by the old `run_migrations()` and already
has every table the baseline migration would create. Tell Alembic "you're
already at the baseline" without re-applying DDL:

```bash
railway run --service rmi-audit-toolkit-backend alembic stamp ac8ed3c6f884
```

(That hash is the baseline revision; it's also visible via
`alembic history`.) After that, every Railway redeploy will only apply
**new** migrations beyond the baseline.

### 2.3 New DB (e.g., a staging environment)

Just deploy. `alembic upgrade head` in the start command creates everything
from scratch.

---

## 3. Storage

| Backend | When to use | Behavior |
|---|---|---|
| `local` (default) | Local dev only | Writes to `backend/uploads/`. Ephemeral on Railway. |
| `supabase` | Production | Writes to the private `evidence` bucket; downloads through `GET /uploads/{path}` stream the bytes via the service-role key, with per-assessment RBAC. |

`backend/storage.py` is the only place the backend talks to either backend.
Swapping to R2/S3 later is a single-file change.

Uploaded files are addressed by `assessments/<id>/<kind>/<uuid_filename>`.
Old Railway local-disk uploads are not migrated automatically — copy them
out before flipping `STORAGE_BACKEND` if you have any worth keeping.

---

## 4. Rotation runbook

If a secret leaks (or you just want a fresh set), run:

```bash
railway login
railway link
supabase login
bash scripts/rotate_secrets.sh
```

That script rotates `SECRET_KEY`, prompts you for the new Supabase keys (which
you generate in the Supabase dashboard since service-role rotation is
dashboard-only), pushes them to Railway, and redeploys both services.

After running:
- All existing JWTs are invalid; users must sign back in.
- The Postgres password change forces the backend's connection pool to
  reconnect — there will be a few seconds of 5xx during redeploy.

---

## 5. CI / pre-merge checks

`.github/workflows/ci.yml` runs on every push and PR:

- **backend**: `pytest` (39 tests at last count) + `pip-audit`
- **frontend**: `npm run typecheck`, `npm run lint`, `vite build`, `npm audit`
- **secret-scan**: fails the build if any file matching
  `supa_vars*.json` / `*credentials*.json` / `*secrets*.json` is tracked.

---

## 6. Smoke checks after a deploy

```bash
# Health
curl https://<backend>.up.railway.app/healthz
# → {"status":"ok"}

# Login
curl -d "username=admin@example.com&password=..." \
     https://<backend>.up.railway.app/token
# → {"access_token": "...", "token_type": "bearer"}

# Authenticated who-am-I
TOKEN=...
curl -H "Authorization: Bearer $TOKEN" https://<backend>.up.railway.app/users/me

# Frontend
curl -I https://<frontend>.up.railway.app
# → HTTP/2 200, served by `serve`
```

---

## 7. Costs (rough)

- **Railway**: backend $5–15/mo, frontend $5/mo, Postgres $5/mo (~$15–25/mo total)
- **Supabase**: free tier covers <1GB of evidence and <50k Storage requests/mo
- **OpenAI** (optional): about $0.002 per text-scored response

---

## 8. Security checklist (kept current)

- [x] `SECRET_KEY` is set in Railway and not the default
- [x] `ENVIRONMENT=production` on the backend service
- [x] No `supa_vars.json`-shape file in the repo (CI enforces)
- [x] `STORAGE_BACKEND=supabase` so uploads survive redeploys
- [x] Bucket is private; signed URLs only for direct browser access
- [x] CORS restricted to the live frontend URL + localhost dev ports
- [x] Per-assessment RBAC (admin / creator / explicit member)
- [x] `/token` rate-limited (10 attempts / min / IP+email)
- [x] Audit log written for login, user mutations, finalize, scoring
- [ ] Configure a Railway PG backup schedule (manual today)
- [ ] Enable 2FA on Railway + Supabase accounts
