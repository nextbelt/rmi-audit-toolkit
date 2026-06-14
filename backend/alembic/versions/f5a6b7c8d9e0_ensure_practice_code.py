"""ensure practices.practice_code exists (repair create_all drift)

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-06-13 16:00:00.000000

Production's `practices` table was created by an old `create_all` bootstrap that
predates the `practice_code` column, so the recommendations engine errored. This
adds the column only if it's missing (DB-agnostic, idempotent), so it's a no-op
on databases built correctly from the baseline migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if "practices" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("practices")}
    if "practice_code" not in cols:
        op.add_column("practices", sa.Column("practice_code", sa.String(length=20), nullable=True))
        existing_idx = {i["name"] for i in insp.get_indexes("practices")}
        if "ix_practices_practice_code" not in existing_idx:
            op.create_index("ix_practices_practice_code", "practices", ["practice_code"], unique=False)


def downgrade() -> None:
    # Non-destructive forward-fix; nothing to reverse (the column belongs in the
    # baseline schema anyway).
    pass
