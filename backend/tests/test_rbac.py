"""Per-assessment ownership / admin RBAC."""
from datetime import date, datetime

import pytest


def _make_v1_assessment(db_session, creator_id: int):
    from models import Assessment, AssessmentStatus

    a = Assessment(
        client_name="ACME Industrial",
        site_name="Plant A",
        assessment_date=datetime.utcnow(),
        creator_id=creator_id,
        status=AssessmentStatus.DRAFT,
    )
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    return a


def _make_v2_assessment(db_session, creator_id: int):
    from models_v2 import AssessmentMode, AssessmentV2

    a = AssessmentV2(
        client_name="ACME Industrial",
        site_name="Plant A",
        assessment_mode=AssessmentMode.STANDARD,
        assessment_date=date.today(),
        status="in_progress",
        creator_id=creator_id,
    )
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    return a


class TestV1Finalize:
    def test_creator_can_finalize(self, client, db_session, make_user, auth_headers):
        owner = make_user(role="auditor")
        a = _make_v1_assessment(db_session, creator_id=owner[0].id)
        r = client.post(f"/assessments/{a.id}/finalize", headers=auth_headers(owner))
        assert r.status_code == 200

    def test_stranger_cannot_finalize(self, client, db_session, make_user, auth_headers):
        owner = make_user(role="auditor")
        outsider = make_user(role="auditor")
        a = _make_v1_assessment(db_session, creator_id=owner[0].id)
        r = client.post(f"/assessments/{a.id}/finalize", headers=auth_headers(outsider))
        assert r.status_code == 403

    def test_admin_can_finalize_any(self, client, db_session, make_user, auth_headers):
        owner = make_user(role="auditor")
        admin = make_user(role="admin")
        a = _make_v1_assessment(db_session, creator_id=owner[0].id)
        r = client.post(f"/assessments/{a.id}/finalize", headers=auth_headers(admin))
        assert r.status_code == 200


class TestV2Visibility:
    def test_list_only_shows_own_assessments(self, client, db_session, make_user, auth_headers):
        alice = make_user(role="auditor")
        bob = make_user(role="auditor")
        _make_v2_assessment(db_session, creator_id=alice[0].id)
        _make_v2_assessment(db_session, creator_id=bob[0].id)

        r = client.get("/api/v2/assessments", headers=auth_headers(alice))
        assert r.status_code == 200
        ids = r.json()
        # Alice should see exactly one (her own)
        assert isinstance(ids, list)
        assert len(ids) == 1

    def test_admin_sees_all_v2_assessments(self, client, db_session, make_user, auth_headers):
        alice = make_user(role="auditor")
        bob = make_user(role="auditor")
        admin = make_user(role="admin")
        _make_v2_assessment(db_session, creator_id=alice[0].id)
        _make_v2_assessment(db_session, creator_id=bob[0].id)

        r = client.get("/api/v2/assessments", headers=auth_headers(admin))
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_stranger_cannot_read_assessment(self, client, db_session, make_user, auth_headers):
        owner = make_user(role="auditor")
        outsider = make_user(role="auditor")
        a = _make_v2_assessment(db_session, creator_id=owner[0].id)
        r = client.get(f"/api/v2/assessments/{a.id}", headers=auth_headers(outsider))
        assert r.status_code == 403
