"""Maintenance–Operations perception gap (OPERATIONS role)."""
from datetime import date


def test_ops_alignment_gap(db_session, make_user):
    from models_v2 import (
        AssessmentMode, AssessmentV2, Domain, DomainType, QuestionV2, Subdomain,
        TargetRoleV2, ResponseV2,
    )
    from report_renderer import HTMLReportRenderer

    user, _ = make_user()
    a = AssessmentV2(client_name="X", site_name="Y", assessment_mode=AssessmentMode.DEEPDIVE,
                     assessment_date=date.today(), status="in_progress", creator_id=user.id)
    db_session.add(a); db_session.flush()
    dom = Domain(code="LC", name="Leadership & Culture", description="", display_order=1)
    db_session.add(dom); db_session.flush()
    sd = Subdomain(domain_id=dom.id, code="LC.1", name="Mgmt", display_order=1)
    db_session.add(sd); db_session.flush()

    def q(code, role):
        x = QuestionV2(subdomain_id=sd.id, question_code=code, question_text="?",
                       question_type="likert", domain=DomainType.LC, target_role=role,
                       weight=1.0, scoring_rubric={"1": "a", "5": "b"}, is_critical=False,
                       evidence_required=False, is_active=True)
        db_session.add(x); db_session.flush(); return x

    qm = q("LC.1-01", TargetRoleV2.MANAGER)
    qo = q("LC.1-OP1", TargetRoleV2.OPERATIONS)
    db_session.add(ResponseV2(assessment_id=a.id, question_id=qm.id, numeric_score=4.0,
                              respondent_role=TargetRoleV2.MANAGER, is_draft=False, is_na=False))
    db_session.add(ResponseV2(assessment_id=a.id, question_id=qo.id, numeric_score=2.0,
                              respondent_role=TargetRoleV2.OPERATIONS, is_draft=False, is_na=False))
    db_session.commit()

    al = HTMLReportRenderer(db_session)._ops_alignment(a.id)
    assert al is not None
    assert al["ops_avg"] == 2.0          # operations rates the partnership low
    assert al["maint_avg"] == 4.0        # maintenance rates its L&C high
    assert al["gap"] == 2.0              # maintenance sees it 2 pts higher -> disconnect
    assert al["lowest"][0]["code"] == "LC.1-OP1"


def test_ops_alignment_none_without_operations(db_session, make_user):
    """No operations respondent -> no alignment section (graceful)."""
    from models_v2 import (
        AssessmentMode, AssessmentV2, Domain, DomainType, QuestionV2, Subdomain,
        TargetRoleV2, ResponseV2,
    )
    from report_renderer import HTMLReportRenderer

    user, _ = make_user()
    a = AssessmentV2(client_name="X", site_name="Y", assessment_mode=AssessmentMode.DEEPDIVE,
                     assessment_date=date.today(), status="in_progress", creator_id=user.id)
    db_session.add(a); db_session.flush()
    dom = Domain(code="LC", name="L&C", description="", display_order=1)
    db_session.add(dom); db_session.flush()
    sd = Subdomain(domain_id=dom.id, code="LC.1", name="Mgmt", display_order=1)
    db_session.add(sd); db_session.flush()
    qm = QuestionV2(subdomain_id=sd.id, question_code="LC.1-01", question_text="?",
                    question_type="likert", domain=DomainType.LC, target_role=TargetRoleV2.MANAGER,
                    weight=1.0, scoring_rubric={"1": "a"}, is_critical=False,
                    evidence_required=False, is_active=True)
    db_session.add(qm); db_session.flush()
    db_session.add(ResponseV2(assessment_id=a.id, question_id=qm.id, numeric_score=3.0,
                              respondent_role=TargetRoleV2.MANAGER, is_draft=False, is_na=False))
    db_session.commit()

    assert HTMLReportRenderer(db_session)._ops_alignment(a.id) is None
