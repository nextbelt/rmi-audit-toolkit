"""AI evidence relevance gate: verdict parsing + confidence impact of rejection.

Locks in the guardrail that stops an unrelated file (e.g. a selfie) from being
passed off as evidence to remove the confidence penalty.
"""
from datetime import date


def test_normalize_payload_verdict():
    from ai_scoring import AIScoringEngine
    norm = AIScoringEngine._normalize_payload  # staticmethod; no API key needed

    assert norm({"verdict": "irrelevant"}, "image")["is_evidence"] is False
    assert norm({"verdict": "relevant"}, "image")["is_evidence"] is True
    # Derive verdict from is_evidence when the model omits the string.
    assert norm({"is_evidence": False}, "image")["verdict"] == "irrelevant"
    assert norm({"is_evidence": True}, "image")["verdict"] == "relevant"
    # Genuinely unknown → unclear (fail-open at the call site).
    assert norm({}, "image")["verdict"] == "unclear"
    # reason falls back to observations.
    assert norm({"verdict": "irrelevant", "observations": "a selfie"}, "image")["reason"] == "a selfie"


def _setup(db_session, creator_id, evidence_status):
    from models_v2 import (
        AssessmentMode, AssessmentV2, Domain, DomainType, QuestionV2, Subdomain,
        TargetRoleV2, ResponseV2, EvidenceStatus,
    )
    a = AssessmentV2(client_name="ACME", site_name="Plant A",
                     assessment_mode=AssessmentMode.STANDARD, assessment_date=date.today(),
                     status="in_progress", creator_id=creator_id)
    db_session.add(a); db_session.flush()
    dom = Domain(code="WC", name="Workforce", description="", display_order=1)
    db_session.add(dom); db_session.flush()
    sd = Subdomain(domain_id=dom.id, code="WC.1", name="Tech", display_order=1)
    db_session.add(sd); db_session.flush()
    q = QuestionV2(subdomain_id=sd.id, question_code="WC.1-01", question_text="?",
                   question_type="likert", domain=DomainType.WC, target_role=TargetRoleV2.TECHNICIAN,
                   weight=1.0, scoring_rubric={"1": "no", "5": "yes"}, is_critical=False,
                   evidence_required=True, is_active=True)
    db_session.add(q); db_session.flush()
    r = ResponseV2(assessment_id=a.id, question_id=q.id, numeric_score=4.0,
                   respondent_role=TargetRoleV2.TECHNICIAN, is_draft=False, is_na=False,
                   evidence_status=EvidenceStatus(evidence_status))
    db_session.add(r); db_session.commit()
    return a


def test_rejected_evidence_docks_confidence(db_session, make_user):
    from scoring_engine_v2 import ScoringEngineV2
    from models_v2 import AssessmentMode
    user, _ = make_user()
    a = _setup(db_session, user.id, "rejected")  # irrelevant file, gate rejected it
    conf = ScoringEngineV2(db_session)._calculate_confidence(a.id, AssessmentMode.STANDARD, [])
    assert conf < 1.0  # the rejected (irrelevant) evidence leaves the claim unsupported


def test_status_for_verdict_fail_closed():
    from api_v2 import _status_for_verdict
    from models_v2 import EvidenceStatus
    # Only confidently-relevant evidence is credited.
    assert _status_for_verdict("relevant", True) == EvidenceStatus.PENDING_VERIFICATION
    assert _status_for_verdict("irrelevant", True) == EvidenceStatus.REJECTED
    # 'unclear' / AI outage is NOT credited — stays a confidence drag.
    assert _status_for_verdict("unclear", True) == EvidenceStatus.PENDING_EVIDENCE
    # Questions that don't require evidence are never gated.
    assert _status_for_verdict("relevant", False) == EvidenceStatus.NOT_REQUIRED


def test_valid_evidence_keeps_confidence(db_session, make_user):
    from scoring_engine_v2 import ScoringEngineV2
    from models_v2 import AssessmentMode
    user, _ = make_user()
    a = _setup(db_session, user.id, "pending_verification")  # uploaded + relevant
    conf = ScoringEngineV2(db_session)._calculate_confidence(a.id, AssessmentMode.STANDARD, [])
    assert conf == 1.0  # relevant evidence does not dock confidence
