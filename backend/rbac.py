"""Per-assessment access checks shared by v1 and v2 routers."""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Assessment, User
from models_extra import AssessmentMember
from models_v2 import AssessmentV2


def _is_admin(user: User) -> bool:
    return (user.role or "").lower() == "admin"


def get_v1_assessment_or_403(db: Session, assessment_id: int, user: User) -> Assessment:
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if _is_admin(user) or a.creator_id == user.id:
        return a
    member = (
        db.query(AssessmentMember)
        .filter(
            AssessmentMember.assessment_table == "v1",
            AssessmentMember.assessment_id == assessment_id,
            AssessmentMember.user_id == user.id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to assessment")
    return a


def get_v2_assessment_or_403(db: Session, assessment_id: int, user: User) -> AssessmentV2:
    a = db.query(AssessmentV2).filter(AssessmentV2.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if _is_admin(user) or a.creator_id == user.id:
        return a
    member = (
        db.query(AssessmentMember)
        .filter(
            AssessmentMember.assessment_table == "v2",
            AssessmentMember.assessment_id == assessment_id,
            AssessmentMember.user_id == user.id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to assessment")
    return a


def filter_v1_visible(db: Session, query, user: User):
    if _is_admin(user):
        return query
    member_ids = [
        m.assessment_id
        for m in db.query(AssessmentMember)
        .filter(AssessmentMember.assessment_table == "v1", AssessmentMember.user_id == user.id)
        .all()
    ]
    return query.filter((Assessment.creator_id == user.id) | (Assessment.id.in_(member_ids)))


def filter_v2_visible(db: Session, query, user: User):
    if _is_admin(user):
        return query
    member_ids = [
        m.assessment_id
        for m in db.query(AssessmentMember)
        .filter(AssessmentMember.assessment_table == "v2", AssessmentMember.user_id == user.id)
        .all()
    ]
    return query.filter((AssessmentV2.creator_id == user.id) | (AssessmentV2.id.in_(member_ids)))
