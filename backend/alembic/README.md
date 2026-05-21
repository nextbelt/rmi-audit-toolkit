# Alembic migrations

This is the single source of truth for the schema. The previous ad-hoc
`run_migrations()` function in `main.py` only added missing columns — it
never dropped, changed types, or modified constraints. Alembic now owns all
schema changes.

## Day-to-day

```bash
# After editing a model:
alembic revision --autogenerate -m "add evidence verifier columns"

# Review the generated file in alembic/versions/ before committing.
# Then apply:
alembic upgrade head

# Roll back one step:
alembic downgrade -1

# See where the DB is:
alembic current
alembic history
```

## First deploy of these changes against an existing populated DB

The Railway Postgres already has all the tables from the column-add migrator.
To switch it to Alembic without losing data, run **once**:

```bash
alembic stamp ac8ed3c6f884
```

This tells Alembic "the DB is at the baseline revision" without applying any
DDL. After that, normal `alembic upgrade head` runs at deploy will apply only
**new** migrations.

`backend/railway.json` and `Procfile` already run `alembic upgrade head` as
the release/start hook, so future deploys are automatic.

## Local dev

A fresh SQLite DB at `backend/rmi_audit.db` will be auto-created by main.py
at startup if no tables exist. Prefer `alembic upgrade head` for parity with
production.
