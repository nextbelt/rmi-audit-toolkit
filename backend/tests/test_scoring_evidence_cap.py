"""
Evidence-policy regression: a response with score >= 4 on an evidence-required
question must not lift the score above the evidence cap unless evidence_status
is ACCEPTED.
"""
from datetime import date


def _make_assessment(db_session, creator_id):
    from models_v2 import AssessmentMode, AssessmentV2

    a = AssessmentV2(
        client_name="ACME", site_name="Plant A",
        assessment_mode=AssessmentMode.STANDARD,
        assessment_date=date.today(), status="in_progress",
        creator_id=creator_id,
    )
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    return a


def _make_domain_subdomain_question(db_session, evidence_required: bool):
    from models_v2 import Domain, DomainType, QuestionV2, Subdomain, TargetRoleV2

    dom = Domain(code="WC", name="Workforce Capability", description="", display_order=1)
    db_session.add(dom)
    db_session.flush()
    sd = Subdomain(domain_id=dom.id, code="WC.1", name="Technical Competency", display_order=1)
    db_session.add(sd)
    db_session.flush()
    q = QuestionV2(
        subdomain_id=sd.id,
        question_code="WC.1-01",
        question_text="Is there an equipment competency program?",
        question_type="likert",
        domain=DomainType.WC,
        target_role=TargetRoleV2.TECHNICIAN,
        weight=1.0,
        scoring_rubric={"1": "no", "5": "yes"},
        is_critical=False,
        evidence_required=evidence_required,
        is_active=True,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)
    return dom, sd, q


def _make_response(db_session, *, assessment_id, question_id, score, evidence_status):
    from models_v2 import EvidenceStatus, ResponseV2, TargetRoleV2

    r = ResponseV2(
        assessment_id=assessment_id,
        question_id=question_id,
        numeric_score=score,
        respondent_role=TargetRoleV2.TECHNICIAN,
        is_draft=False,
        is_na=False,
        evidence_status=EvidenceStatus(evidence_status),
    )
    db_session.add(r)
    db_session.commit()
    return r


class TestEvidenceCap:
    def test_high_score_without_accepted_evidence_is_capped(self, db_session, make_user):
        from scoring_engine_v2 import ScoringEngineV2

        user, _ = make_user()
        a = _make_assessment(db_session, creator_id=user.id)
        _dom, sd, q = _make_domain_subdomain_question(db_session, evidence_required=True)
        _make_response(
            db_session,
            assessment_id=a.id,
            question_id=q.id,
            score=5.0,
            evidence_status="pending_verification",  # uploaded but not yet verified
        )

        engine = ScoringEngineV2(db_session)
        subdomain_result = engine._score_subdomain(a.id, sd, a.assessment_mode)
        assert subdomain_result["evidence_blocked"] == 1
        # Score is capped at 3.0 even though the user claimed 5
        assert subdomain_result["final_score"] == 3.0

    def test_accepted_evidence_lifts_cap(self, db_session, make_user):
        from scoring_engine_v2 import ScoringEngineV2

        user, _ = make_user()
        a = _make_assessment(db_session, creator_id=user.id)
        _dom, sd, q = _make_domain_subdomain_question(db_session, evidence_required=True)
        _make_response(
            db_session,
            assessment_id=a.id,
            question_id=q.id,
            score=5.0,
            evidence_status="accepted",
        )

        engine = ScoringEngineV2(db_session)
        subdomain_result = engine._score_subdomain(a.id, sd, a.assessment_mode)
        assert subdomain_result["evidence_blocked"] == 0
        assert subdomain_result["final_score"] == 5.0

    def test_low_score_unaffected_by_evidence_policy(self, db_session, make_user):
        from scoring_engine_v2 import ScoringEngineV2

        user, _ = make_user()
        a = _make_assessment(db_session, creator_id=user.id)
        _dom, sd, q = _make_domain_subdomain_question(db_session, evidence_required=True)
        _make_response(
            db_session,
            assessment_id=a.id,
            question_id=q.id,
            score=2.0,
            evidence_status="pending_evidence",
        )
        engine = ScoringEngineV2(db_session)
        subdomain_result = engine._score_subdomain(a.id, sd, a.assessment_mode)
        assert subdomain_result["evidence_blocked"] == 0
        assert subdomain_result["final_score"] == 2.0

    def test_no_evidence_required_no_cap(self, db_session, make_user):
        from scoring_engine_v2 import ScoringEngineV2

        user, _ = make_user()
        a = _make_assessment(db_session, creator_id=user.id)
        _dom, sd, q = _make_domain_subdomain_question(db_session, evidence_required=False)
        _make_response(
            db_session,
            assessment_id=a.id,
            question_id=q.id,
            score=5.0,
            evidence_status="not_required",
        )
        engine = ScoringEngineV2(db_session)
        subdomain_result = engine._score_subdomain(a.id, sd, a.assessment_mode)
        assert subdomain_result["final_score"] == 5.0
