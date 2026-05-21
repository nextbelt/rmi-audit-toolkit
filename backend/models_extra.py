"""
Cross-cutting tables that don't belong to either v1 or v2 domain models:
- AuditLog: append-only record of security-sensitive actions
- AssessmentMember: explicit per-assessment RBAC

Tables are registered on the shared Base.metadata so init_db / run_migrations
will create them.
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from database import Base


class AuditLog(Base):
    """Append-only log of security-relevant events.

    Never mutate or delete rows. Add new ones."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    action = Column(String(80), nullable=False, index=True)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(80), nullable=True)
    ip_address = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)


class AssessmentMember(Base):
    """Per-assessment access list.

    A user can read an assessment iff they are an admin, the creator, or a
    member here. The role string is informational (lead/contributor/viewer).
    """

    __tablename__ = "assessment_members"
    __table_args__ = (
        UniqueConstraint("assessment_id", "user_id", "assessment_table", name="uq_member"),
        Index("ix_assessment_members_lookup", "assessment_table", "assessment_id", "user_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    # "v1" or "v2" — v2 assessments live in assessments_v2 table
    assessment_table = Column(String(8), nullable=False, default="v2")
    assessment_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(32), nullable=False, default="contributor")
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PasswordResetTokenUsage(Base):
    """Records that a particular reset token has already been consumed, so a
    leaked token cannot be replayed within its TTL.
    """

    __tablename__ = "password_reset_used"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
