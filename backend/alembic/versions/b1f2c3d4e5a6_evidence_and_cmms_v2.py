"""evidence files + AI analysis + cmms snapshot ingest (v2)

Revision ID: b1f2c3d4e5a6
Revises: ac8ed3c6f884
Create Date: 2026-05-21 09:00:00.000000

Adds:
- Evidence file columns on responses_v2 (file pointer + metadata)
- AI suggestion columns on responses_v2 (score, observations, analyzed_at)
- New table cmms_uploads_v2 to persist CMMS snapshot ingest + computed metrics
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1f2c3d4e5a6"
down_revision: Union[str, Sequence[str], None] = "ac8ed3c6f884"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── responses_v2: evidence + AI columns ──
    with op.batch_alter_table("responses_v2", schema=None) as batch_op:
        batch_op.add_column(sa.Column("evidence_file_path", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("evidence_filename", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("evidence_mime", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("evidence_size_bytes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("evidence_uploaded_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("ai_suggested_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("ai_observations", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("ai_confidence", sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column("ai_analyzed_at", sa.DateTime(), nullable=True))

    # ── cmms_uploads_v2: snapshot ingest + metrics ──
    op.create_table(
        "cmms_uploads_v2",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),  # 'work_orders' | 'pm'
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="processed"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("bad_actors", sa.JSON(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments_v2.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("cmms_uploads_v2", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_cmms_uploads_v2_id"), ["id"], unique=False)
        batch_op.create_index(
            "ix_cmms_uploads_v2_assessment_id", ["assessment_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("cmms_uploads_v2", schema=None) as batch_op:
        batch_op.drop_index("ix_cmms_uploads_v2_assessment_id")
        batch_op.drop_index(batch_op.f("ix_cmms_uploads_v2_id"))
    op.drop_table("cmms_uploads_v2")

    with op.batch_alter_table("responses_v2", schema=None) as batch_op:
        batch_op.drop_column("ai_analyzed_at")
        batch_op.drop_column("ai_confidence")
        batch_op.drop_column("ai_observations")
        batch_op.drop_column("ai_suggested_score")
        batch_op.drop_column("evidence_uploaded_at")
        batch_op.drop_column("evidence_size_bytes")
        batch_op.drop_column("evidence_mime")
        batch_op.drop_column("evidence_filename")
        batch_op.drop_column("evidence_file_path")
