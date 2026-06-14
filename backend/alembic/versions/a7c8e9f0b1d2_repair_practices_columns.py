"""ensure the practices table has every model column (repair create_all drift)

Revision ID: a7c8e9f0b1d2
Revises: f5a6b7c8d9e0
Create Date: 2026-06-14 10:00:00.000000

Production's `practices` table was created by an old `create_all` bootstrap that
predates several columns the Practice model now declares (e.g. `description`,
`pathways`, `from_level`). The report renderer and recommendations engine select
all of them, so a missing column raised `UndefinedColumn: practices.description`
and failed report generation. This adds any missing column idempotently — a
no-op on databases built correctly from the baseline migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c8e9f0b1d2"
down_revision: Union[str, Sequence[str], None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Column name -> type, for every Practice column beyond the baseline identifiers.
_COLUMNS = {
    "description": sa.Text(),
    "pathways": sa.JSON(),
    "references": sa.JSON(),
    "industry_variations": sa.JSON(),
    "tools": sa.JSON(),
    "from_level": sa.Integer(),
    "to_level": sa.Integer(),
    "priority_rank": sa.Integer(),
    "impact_rating": sa.String(length=10),
    "effort_rating": sa.String(length=10),
    "timeline": sa.String(length=30),
    "success_metrics": sa.JSON(),
    "resources": sa.JSON(),
    "iso_55001_clause": sa.String(length=20),
    "is_critical_path": sa.Boolean(),
    "version": sa.String(length=10),
    "is_active": sa.Boolean(),
    "created_at": sa.DateTime(),
}


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if "practices" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("practices")}
    for name, type_ in _COLUMNS.items():
        if name not in existing:
            op.add_column("practices", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    # Non-destructive forward-fix; these columns belong in the baseline schema.
    pass
