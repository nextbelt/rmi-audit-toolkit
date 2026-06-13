"""
Deploy-time migration runner — idempotent and self-healing.

Brings the database up to Alembic head. Crucially, it handles a database that
was originally created with ``Base.metadata.create_all`` (the old bootstrap
path) and therefore has tables but **no ``alembic_version`` table**. Running a
plain ``alembic upgrade head`` against such a DB fails with "relation already
exists" because Alembic tries to replay the baseline migration from scratch.

So before upgrading, if the DB is not under Alembic control yet, we detect which
revision its current schema corresponds to (by probing for marker tables/columns
introduced by each migration) and ``stamp`` it there. After the first successful
run the ``alembic_version`` table exists and this becomes a no-op detection +
normal upgrade on every future deploy.

Invoked by the deploy start command (see backend/railway.json):
    python migrate.py && uvicorn main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import logging
from typing import Optional

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s migrate: %(message)s")
log = logging.getLogger("migrate")


def _detect_stamp(insp) -> Optional[str]:
    """Return the revision that matches the DB's current (pre-Alembic) schema.

    Probes newest → oldest so the most-advanced matching revision wins.
    Returns None for an empty database (let Alembic build it from scratch).
    """
    tables = set(insp.get_table_names())
    if not tables:
        return None

    def cols(table: str) -> set:
        return {c["name"] for c in insp.get_columns(table)} if table in tables else set()

    assessments_v2 = cols("assessments_v2")
    responses_v2 = cols("responses_v2")

    # c2d3e4f5a6b7 added employee_count to assessments_v2
    if "employee_count" in assessments_v2:
        return "c2d3e4f5a6b7"
    # b1f2c3d4e5a6 added cmms_uploads_v2 + evidence file columns on responses_v2
    if "cmms_uploads_v2" in tables or "evidence_file_path" in responses_v2:
        return "b1f2c3d4e5a6"
    # ac8ed3c6f884 is the baseline (v1 + v2 core tables)
    if "assessments_v2" in tables or "domains" in tables:
        return "ac8ed3c6f884"
    return None


def main() -> None:
    engine = create_engine(settings.DATABASE_URL)
    insp = inspect(engine)
    cfg = Config("alembic.ini")

    if "alembic_version" not in set(insp.get_table_names()):
        stamp = _detect_stamp(insp)
        if stamp:
            log.info("DB has tables but is not under Alembic — stamping at %s", stamp)
            command.stamp(cfg, stamp)
        else:
            log.info("Empty database — building schema from the first migration.")
    else:
        log.info("DB already under Alembic control.")

    log.info("Running 'alembic upgrade head'...")
    command.upgrade(cfg, "head")
    log.info("Migrations complete.")


if __name__ == "__main__":
    main()
