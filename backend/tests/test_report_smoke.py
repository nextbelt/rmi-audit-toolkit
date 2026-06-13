"""Smoke test: the v2 report generator produces a real, non-empty PDF and does
not mutate the assessment's persisted scores (generation is read-only).
"""
import os
from datetime import date


def test_report_generates_nondestructive_pdf(db_session, make_user, tmp_upload_dir):
    from models_v2 import (
        AssessmentMode,
        AssessmentV2,
        Domain,
        Subdomain,
        SubdomainScore,
    )
    from report_generator_v2 import ReportGeneratorV2

    user, _ = make_user(role="admin")

    dom = Domain(code="WC", name="Workforce Capability", display_order=1)
    db_session.add(dom)
    db_session.commit()
    db_session.refresh(dom)

    sd = Subdomain(domain_id=dom.id, code="WC.1", name="Technical Competency", display_order=1)
    db_session.add(sd)
    db_session.commit()
    db_session.refresh(sd)

    a = AssessmentV2(
        client_name="ACME Industrial",
        site_name="Plant A",
        assessment_mode=AssessmentMode.STANDARD,
        assessment_date=date.today(),
        status="completed",
        creator_id=user.id,
        overall_rmi=3.20,
        maturity_level="Level 3 - Systematic",
    )
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)

    db_session.add(
        SubdomainScore(assessment_id=a.id, subdomain_id=sd.id, raw_score=3.2, final_score=3.2)
    )
    db_session.commit()

    gen = ReportGeneratorV2(db_session, output_dir=tmp_upload_dir["report"])
    path = gen.generate(assessment_id=a.id, generated_by=user.id)

    assert os.path.isfile(path)
    assert os.path.getsize(path) > 5000  # a real multi-section PDF, not a stub

    # Read-only: the official score must be untouched after generating a report.
    db_session.refresh(a)
    assert a.overall_rmi == 3.20

    # A registry row was written for the download endpoint.
    from models import Report

    assert db_session.query(Report).filter(Report.assessment_id == a.id).count() == 1
