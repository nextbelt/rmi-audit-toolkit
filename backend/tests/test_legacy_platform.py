"""
Legacy Platform Gate — verifies the v1 data model still round-trips correctly.

Run with:
    pytest tests/test_legacy_platform.py -v
"""
from __future__ import annotations

import datetime

import bcrypt
import pytest


def test_v1_user_and_assessment_round_trip(db_session):
    """Create a v1 User + Assessment via the ORM and verify persistence."""
    from models import Assessment, AssessmentStatus, User

    u = User(
        email="v1gate@ci.test",
        full_name="V1 Gate User",
        role="auditor",
        is_active=True,
        hashed_password=bcrypt.hashpw(b"V1Gate123!", bcrypt.gensalt()).decode("utf-8"),
    )
    db_session.add(u)
    db_session.flush()
    assert u.id is not None, "User did not get a PK after flush"

    a = Assessment(
        client_name="CI Corp",
        site_name="Plant 0",
        assessment_date=datetime.datetime.utcnow(),
        creator_id=u.id,
        status=AssessmentStatus.DRAFT,
    )
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)

    assert a.id is not None, "Assessment did not persist"
    assert a.client_name == "CI Corp"
    assert a.status == AssessmentStatus.DRAFT


def test_v1_assessment_status_enum_values(db_session):
    """Enum values that existed in v1 are still present (no accidental removal)."""
    from models import AssessmentStatus

    assert AssessmentStatus.DRAFT is not None
    assert AssessmentStatus.IN_PROGRESS is not None
    assert AssessmentStatus.COMPLETED is not None
