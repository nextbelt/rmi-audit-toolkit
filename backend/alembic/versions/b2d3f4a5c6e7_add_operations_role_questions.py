"""add OPERATIONS respondent role + operations-perspective questions

Revision ID: b2d3f4a5c6e7
Revises: a7c8e9f0b1d2
Create Date: 2026-06-15 09:00:00.000000

Adds the OPERATIONS value to the ``targetrolev2`` enum and seeds the
operations-perspective questions (LC.1-OP*, LC.3-OP*) into the existing prod
database. Questions are read from the bundled 04-question-bank.json (the source
of truth) and inserted idempotently by question_code, so this is a no-op on a
database that was already seeded with them.

Postgres forbids using a newly-added enum value in the same transaction that
added it, so the ALTER TYPE runs on a separate AUTOCOMMIT connection.
"""
import json
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2d3f4a5c6e7"
down_revision: Union[str, Sequence[str], None] = "a7c8e9f0b1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _locate_bank() -> Union[str, None]:
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "..", "04-question-bank.json"),  # backend/
        os.path.join(here, "..", "..", "..", "docs", "rmi-vnext", "04-question-bank.json"),
        "/app/04-question-bank.json",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


_QB = sa.table(
    "question_bank_v2",
    sa.column("question_code", sa.String),
    sa.column("question_text", sa.Text),
    sa.column("question_type", sa.String),
    sa.column("domain", sa.String),
    sa.column("subdomain_id", sa.Integer),
    sa.column("target_role", sa.String),
    sa.column("weight", sa.Float),
    sa.column("scoring_rubric", sa.JSON),
    sa.column("assessment_modes", sa.JSON),
    sa.column("evidence_required", sa.Boolean),
    sa.column("evidence_guidance", sa.Text),
    sa.column("calibration_anchor", sa.Text),
    sa.column("is_critical", sa.Boolean),
    sa.column("is_active", sa.Boolean),
)


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Add the enum value. On Postgres this must be committed before it can be
    #    used, so run it on a separate autocommit connection.
    if bind.dialect.name == "postgresql":
        with bind.engine.connect() as c:
            c = c.execution_options(isolation_level="AUTOCOMMIT")
            c.execute(sa.text("ALTER TYPE targetrolev2 ADD VALUE IF NOT EXISTS 'OPERATIONS'"))

    # 2) Insert any operations questions not already present (idempotent).
    path = _locate_bank()
    if not path:
        return
    with open(path, encoding="utf-8") as f:
        bank = json.load(f)

    sd_ids = {code: sid for code, sid in bind.execute(sa.text("SELECT code, id FROM subdomains")).all()}
    existing = {row[0] for row in bind.execute(sa.text("SELECT question_code FROM question_bank_v2")).all()}

    rows = []
    for dom in bank.get("domains", []):
        for sd in dom.get("subdomains", []):
            sd_code = sd["subdomain_code"]
            sid = sd_ids.get(sd_code)
            if sid is None:
                continue
            for q in sd.get("questions", []):
                if (q.get("target_role") or "").upper() != "OPERATIONS":
                    continue
                if q["question_code"] in existing:
                    continue
                rows.append({
                    "question_code": q["question_code"],
                    "question_text": q["question_text"],
                    "question_type": q.get("question_type", "LIKERT"),
                    "domain": sd_code.split(".")[0],
                    "subdomain_id": sid,
                    "target_role": "OPERATIONS",
                    "weight": q.get("weight", 1.5),
                    "scoring_rubric": q.get("scoring_rubric", {}),
                    "assessment_modes": q.get("assessment_mode", ["standard", "deepdive"]),
                    "evidence_required": bool(q.get("evidence_required", False)),
                    "evidence_guidance": q.get("evidence_guidance"),
                    "calibration_anchor": q.get("calibration_anchor"),
                    "is_critical": bool(q.get("is_critical", False)),
                    "is_active": True,
                })

    if rows:
        op.bulk_insert(_QB, rows)


def downgrade() -> None:
    # Forward-only: removing an enum value / questions is unsafe once answered.
    pass
