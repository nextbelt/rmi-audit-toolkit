"""
Core SQLAlchemy models still used by the v2 product.

The legacy v1 schema (People/Process/Technology pillars, v1 question bank,
observations, evidence, v1 scores, ISO-14224 audits) has been removed — the
shipping product is the 5-domain v2 framework in models_v2.py. Only `User`
(shared identity) and `Report` (the generated-PDF registry, now keyed to v2
assessments) remain here.
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    """System users (auditors, admins, clients)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, auditor, client
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    """
    Generated report registry — executive PDF exports.

    Keyed to v2 assessments (assessments_v2). The PDF lives on disk / object
    storage at `file_path`; `content` holds a small JSON summary.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(
        Integer,
        ForeignKey("assessments_v2.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    report_type = Column(String(100), nullable=False)  # "executive_v2", ...
    title = Column(String(255), nullable=False)

    content = Column(JSON, nullable=True)
    file_path = Column(String(500), nullable=True)

    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1)

    generator = relationship("User")
