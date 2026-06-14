"""Regression tests for mode-based question routing (RoutingEngine).

Locks in the fix for the bug where ``assessment_modes`` was stored double-encoded
(``json.dumps`` into a JSON column) and the SQL ``.contains()`` filter raised on
Postgres ("operator does not exist: json ~~ text") — so QuickScan/Standard
returned nothing while DeepDive returned all 150. Routing now parses modes in
Python, so both a real JSON array and a double-encoded string work, and every
mode yields its expected per-subdomain count.
"""
import json

import pytest

from models_v2 import Domain, Subdomain, QuestionV2, DomainType, TargetRoleV2
from routing_engine import RoutingEngine

N_SUBDOMAINS = 3
QS_PER_SUBDOMAIN = 6


def _seed(db, *, modes_as_string):
    dom = Domain(code="WC", name="Workforce", display_order=1)
    db.add(dom)
    db.flush()
    for s in range(1, N_SUBDOMAINS + 1):
        sd = Subdomain(domain_id=dom.id, code=f"WC.{s}", name=f"Sub {s}", display_order=s)
        db.add(sd)
        db.flush()
        for q in range(1, QS_PER_SUBDOMAIN + 1):
            if q == 1:                       # the quickscan-tagged, critical one
                modes, critical = ["quickscan", "standard", "deepdive"], True
            elif q <= 4:                     # standard + deepdive
                modes, critical = ["standard", "deepdive"], False
            else:                            # deepdive-only
                modes, critical = ["deepdive"], False
            db.add(QuestionV2(
                question_code=f"WC.{s}-{q:02d}",
                question_text=f"Q{q}",
                domain=DomainType.WC,
                subdomain_id=sd.id,
                target_role=TargetRoleV2.TECHNICIAN,
                question_type="LIKERT",
                scoring_rubric={"1": "a", "5": "b"},
                # The prod bug stored this as json.dumps(...) (a string) in a JSON
                # column; exercise both shapes.
                assessment_modes=json.dumps(modes) if modes_as_string else modes,
                weight=float(QS_PER_SUBDOMAIN - q + 1),
                is_critical=critical,
                is_active=True,
            ))
    db.commit()


@pytest.mark.parametrize(
    "modes_as_string", [False, True], ids=["json-array", "double-encoded-string"]
)
def test_routing_counts_per_mode(db_session, modes_as_string):
    _seed(db_session, modes_as_string=modes_as_string)
    eng = RoutingEngine(db_session)

    # QuickScan: exactly one question per subdomain.
    assert len(eng._route_quickscan()) == N_SUBDOMAINS

    # Standard: 4-5 per subdomain (not everything, not nothing).
    std = eng._route_standard()
    assert N_SUBDOMAINS * 4 <= len(std) <= N_SUBDOMAINS * 5

    # DeepDive: every active question.
    assert len(eng._route_deepdive()) == N_SUBDOMAINS * QS_PER_SUBDOMAIN


def test_quickscan_only_picks_tagged_questions(db_session):
    _seed(db_session, modes_as_string=True)
    for q in RoutingEngine(db_session)._route_quickscan():
        assert "quickscan" in [m.lower() for m in q["assessment_modes"]]
