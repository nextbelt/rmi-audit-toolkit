"""peer-segmentation columns + benchmark criteria + hot-path indexes (v2)

Revision ID: c2d3e4f5a6b7
Revises: b1f2c3d4e5a6
Create Date: 2026-06-13 12:00:00.000000

Adds:
- assessments_v2.employee_count / region / lead_assessor (peer segmentation +
  report header). Previously accepted by the API but never persisted.
- benchmark_metadata.peer_group_criteria (JSON) so the engine can record how a
  peer set was selected.
- Indexes on the columns nearly every scoring/benchmark query filters on:
  responses_v2.(assessment_id, question_id), subdomain_scores.assessment_id,
  assessments_v2.(site_name, assessment_date).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1f2c3d4e5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── assessments_v2: peer-segmentation metadata ──
    with op.batch_alter_table("assessments_v2", schema=None) as batch_op:
        batch_op.add_column(sa.Column("employee_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("region", sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column("lead_assessor", sa.String(length=120), nullable=True))
        batch_op.create_index("ix_assessments_v2_site_name", ["site_name"], unique=False)
        batch_op.create_index(
            "ix_assessments_v2_assessment_date", ["assessment_date"], unique=False
        )

    # ── benchmark_metadata: peer-group criteria ──
    with op.batch_alter_table("benchmark_metadata", schema=None) as batch_op:
        batch_op.add_column(sa.Column("peer_group_criteria", sa.JSON(), nullable=True))

    # ── responses_v2 / subdomain_scores: hot-path FK indexes ──
    with op.batch_alter_table("responses_v2", schema=None) as batch_op:
        batch_op.create_index("ix_responses_v2_assessment_id", ["assessment_id"], unique=False)
        batch_op.create_index("ix_responses_v2_question_id", ["question_id"], unique=False)

    with op.batch_alter_table("subdomain_scores", schema=None) as batch_op:
        batch_op.create_index(
            "ix_subdomain_scores_assessment_id", ["assessment_id"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("subdomain_scores", schema=None) as batch_op:
        batch_op.drop_index("ix_subdomain_scores_assessment_id")

    with op.batch_alter_table("responses_v2", schema=None) as batch_op:
        batch_op.drop_index("ix_responses_v2_question_id")
        batch_op.drop_index("ix_responses_v2_assessment_id")

    with op.batch_alter_table("benchmark_metadata", schema=None) as batch_op:
        batch_op.drop_column("peer_group_criteria")

    with op.batch_alter_table("assessments_v2", schema=None) as batch_op:
        batch_op.drop_index("ix_assessments_v2_assessment_date")
        batch_op.drop_index("ix_assessments_v2_site_name")
        batch_op.drop_column("lead_assessor")
        batch_op.drop_column("region")
        batch_op.drop_column("employee_count")
