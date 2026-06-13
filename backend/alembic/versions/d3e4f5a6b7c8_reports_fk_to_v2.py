"""repoint reports.assessment_id FK from v1 assessments to assessments_v2

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-06-13 13:00:00.000000

The legacy v1 pillar schema is retired; reports now belong to v2 assessments.
The reports table was never populated (report download was not wired into the
v1 UI), so a drop + recreate is safe and avoids fragile in-place FK surgery on
SQLite. Also adds indexes used by the latest-report download query.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_reports(fk_target: str) -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("generated_by", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], [fk_target], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("reports", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_reports_id"), ["id"], unique=False)
        batch_op.create_index("ix_reports_assessment_id", ["assessment_id"], unique=False)
        batch_op.create_index("ix_reports_generated_at", ["generated_at"], unique=False)


def upgrade() -> None:
    op.drop_table("reports")
    _create_reports("assessments_v2.id")


def downgrade() -> None:
    op.drop_table("reports")
    # Recreate with the original v1 FK + original (single) index.
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("generated_by", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("reports", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_reports_id"), ["id"], unique=False)
