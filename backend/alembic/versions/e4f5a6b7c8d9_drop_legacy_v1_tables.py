"""drop legacy v1 tables (pillar schema retired)

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-06-13 14:00:00.000000

The v1 People/Process/Technology schema is permanently retired (the product is
the 5-domain v2 framework). These tables were emptied/unused; this migration
removes them. The downgrade fully recreates them (DDL copied from the baseline
migration) so the chain stays reversible — but note v1 *data* is not restored.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Child → parent drop order (respect FK constraints).
_DROP_ORDER = [
    "evidence",
    "scores",
    "iso14224_audits",
    "observations",
    "data_analyses",
    "question_responses",
    "assessment_auditors",
    "assessments",
    "question_bank",
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    for table in _DROP_ORDER:
        if table in existing:
            op.drop_table(table)


def downgrade() -> None:
    # Recreate parents → children (DDL verbatim from ac8ed3c6f884 baseline).
    op.create_table(
        "question_bank",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_code", sa.String(length=20), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("pillar", sa.Enum("PEOPLE", "PROCESS", "TECHNOLOGY", name="pillartype"), nullable=False),
        sa.Column("subcategory", sa.String(length=100), nullable=False),
        sa.Column("target_role", sa.Enum("TECHNICIAN", "SUPERVISOR", "MANAGER", "PLANNER", "AUDITOR", name="targetrole"), nullable=False),
        sa.Column("question_type", sa.Enum("LIKERT", "BINARY", "MULTI_SELECT", "DATA_INPUT", "OBSERVATIONAL", name="questiontype"), nullable=False),
        sa.Column("answer_options", sa.JSON(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("evidence_required", sa.Boolean(), nullable=True),
        sa.Column("evidence_description", sa.Text(), nullable=True),
        sa.Column("scoring_logic", sa.JSON(), nullable=True),
        sa.Column("min_score", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.Column("iso_55001_clause", sa.String(length=50), nullable=True),
        sa.Column("iso_55001_mapping", sa.JSON(), nullable=True),
        sa.Column("is_critical", sa.Boolean(), nullable=True),
        sa.Column("framework_version", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("question_bank", schema=None) as b:
        b.create_index(b.f("ix_question_bank_id"), ["id"], unique=False)
        b.create_index(b.f("ix_question_bank_pillar"), ["pillar"], unique=False)
        b.create_index(b.f("ix_question_bank_question_code"), ["question_code"], unique=True)

    op.create_table(
        "assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("site_name", sa.String(length=255), nullable=False),
        sa.Column("asset_class", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("site_criticality", sa.Float(), nullable=True),
        sa.Column("assessment_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "IN_PROGRESS", "REVIEW", "COMPLETED", "ARCHIVED", name="assessmentstatus"), nullable=True),
        sa.Column("framework_version", sa.String(length=20), nullable=True),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("finalized_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("assessments", schema=None) as b:
        b.create_index(b.f("ix_assessments_client_name"), ["client_name"], unique=False)
        b.create_index(b.f("ix_assessments_id"), ["id"], unique=False)

    op.create_table(
        "assessment_auditors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("auditor_id", sa.Integer(), nullable=False),
        sa.Column("role_in_audit", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.ForeignKeyConstraint(["auditor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "question_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("respondent_id", sa.Integer(), nullable=True),
        sa.Column("response_value", sa.String(length=500), nullable=True),
        sa.Column("numeric_score", sa.Float(), nullable=True),
        sa.Column("evidence_provided", sa.Boolean(), nullable=True),
        sa.Column("evidence_notes", sa.Text(), nullable=True),
        sa.Column("is_draft", sa.Boolean(), nullable=True),
        sa.Column("is_na", sa.Boolean(), nullable=True),
        sa.Column("answered_at", sa.DateTime(), nullable=True),
        sa.Column("answered_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["answered_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["question_bank.id"]),
        sa.ForeignKeyConstraint(["respondent_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("question_responses", schema=None) as b:
        b.create_index(b.f("ix_question_responses_id"), ["id"], unique=False)

    op.create_table(
        "data_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("analysis_type", sa.String(length=100), nullable=False),
        sa.Column("data_source", sa.String(length=255), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("sample_method", sa.String(length=100), nullable=True),
        sa.Column("pass_threshold", sa.Float(), nullable=True),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
        sa.Column("analyzed_by", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["analyzed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("data_analyses", schema=None) as b:
        b.create_index(b.f("ix_data_analyses_id"), ["id"], unique=False)

    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("observation_title", sa.String(length=255), nullable=False),
        sa.Column("observation_type", sa.String(length=100), nullable=True),
        sa.Column("pillar", sa.Enum("PEOPLE", "PROCESS", "TECHNOLOGY", name="pillartype"), nullable=False),
        sa.Column("subcategory", sa.String(length=100), nullable=True),
        sa.Column("observation_notes", sa.Text(), nullable=False),
        sa.Column("pass_fail_result", sa.Boolean(), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column("observed_role", sa.String(length=100), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("observer_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.ForeignKeyConstraint(["observer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("observations", schema=None) as b:
        b.create_index(b.f("ix_observations_id"), ["id"], unique=False)

    op.create_table(
        "iso14224_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("check_item", sa.String(length=255), nullable=False),
        sa.Column("check_category", sa.String(length=100), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("evidence_notes", sa.Text(), nullable=True),
        sa.Column("impact_on_score", sa.Float(), nullable=True),
        sa.Column("audited_at", sa.DateTime(), nullable=True),
        sa.Column("audited_by", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.ForeignKeyConstraint(["audited_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("iso14224_audits", schema=None) as b:
        b.create_index(b.f("ix_iso14224_audits_id"), ["id"], unique=False)

    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("pillar", sa.Enum("PEOPLE", "PROCESS", "TECHNOLOGY", name="pillartype"), nullable=True),
        sa.Column("subcategory", sa.String(length=100), nullable=True),
        sa.Column("raw_score", sa.Float(), nullable=False),
        sa.Column("weighted_score", sa.Float(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("max_possible_score", sa.Float(), nullable=True),
        sa.Column("confidence_level", sa.String(length=50), nullable=True),
        sa.Column("calculation_method", sa.Text(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("scores", schema=None) as b:
        b.create_index(b.f("ix_scores_id"), ["id"], unique=False)

    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("response_id", sa.Integer(), nullable=True),
        sa.Column("observation_id", sa.Integer(), nullable=True),
        sa.Column("data_analysis_id", sa.Integer(), nullable=True),
        sa.Column("evidence_type", sa.Enum("PHOTO", "DOCUMENT", "SCREENSHOT", "CMMS_EXPORT", "NOTE", "VIDEO", name="evidencetype"), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["data_analysis_id"], ["data_analyses.id"]),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"]),
        sa.ForeignKeyConstraint(["response_id"], ["question_responses.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("evidence", schema=None) as b:
        b.create_index(b.f("ix_evidence_id"), ["id"], unique=False)
