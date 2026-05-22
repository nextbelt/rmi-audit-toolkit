"""
ISO 55001:2014 clause taxonomy + gap-report engine.

Question rows are tagged with their ISO 55001 clause (QuestionV2.iso_55001_clause).
This module:
  - Maps each clause code → its canonical name + parent section
  - Aggregates response scores per clause to produce a certification-readiness
    gap report
"""
from __future__ import annotations

from statistics import mean
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models_v2 import QuestionV2, ResponseV2


# ── ISO 55001:2014 Clause Definitions ─────────────────────────────────────
# Per the published standard. Sections 4-10 are the auditable requirements.
ISO_55001_SECTIONS: List[Dict] = [
    {
        "section": "4",
        "title": "Context of the organization",
        "clauses": [
            ("4.1", "Understanding the organization and its context"),
            ("4.2", "Understanding the needs and expectations of stakeholders"),
            ("4.3", "Determining the scope of the asset management system"),
            ("4.4", "Asset management system"),
        ],
    },
    {
        "section": "5",
        "title": "Leadership",
        "clauses": [
            ("5.1", "Leadership and commitment"),
            ("5.2", "Policy"),
            ("5.3", "Organizational roles, responsibilities and authorities"),
        ],
    },
    {
        "section": "6",
        "title": "Planning",
        "clauses": [
            ("6.1", "Actions to address risks and opportunities"),
            ("6.2", "Asset management objectives and planning"),
            ("6.2.1", "Asset management objectives"),
            ("6.2.2", "Planning to achieve asset management objectives"),
        ],
    },
    {
        "section": "7",
        "title": "Support",
        "clauses": [
            ("7.1", "Resources"),
            ("7.2", "Competence"),
            ("7.3", "Awareness"),
            ("7.4", "Communication"),
            ("7.5", "Documented information"),
            ("7.6", "Information requirements"),
        ],
    },
    {
        "section": "8",
        "title": "Operation",
        "clauses": [
            ("8.1", "Operational planning and control"),
            ("8.2", "Management of change"),
            ("8.3", "Outsourcing"),
        ],
    },
    {
        "section": "9",
        "title": "Performance evaluation",
        "clauses": [
            ("9.1", "Monitoring, measurement, analysis and evaluation"),
            ("9.2", "Internal audit"),
            ("9.3", "Management review"),
        ],
    },
    {
        "section": "10",
        "title": "Improvement",
        "clauses": [
            ("10.1", "Nonconformity and corrective action"),
            ("10.2", "Preventive action"),
            ("10.3", "Continual improvement"),
        ],
    },
]

# Flat clause -> name lookup
ISO_CLAUSE_NAMES: Dict[str, str] = {
    clause: name
    for section in ISO_55001_SECTIONS
    for clause, name in section["clauses"]
}

# Clause -> section number lookup
ISO_CLAUSE_SECTION: Dict[str, str] = {
    clause: section["section"]
    for section in ISO_55001_SECTIONS
    for clause, _ in section["clauses"]
}

# Readiness floor: a clause is "ready" when its mean question score >= this.
# Mirrors the v2 scoring engine's "Systematic" maturity floor.
READINESS_FLOOR = 3.0


def _status_for(score: Optional[float], answered: int, total: int) -> str:
    """Translate a clause score into a status the UI can color-code."""
    if total == 0:
        return "unmapped"
    if answered == 0:
        return "unanswered"
    if score is None:
        return "unanswered"
    if score >= READINESS_FLOOR + 1.0:
        return "exceeds"
    if score >= READINESS_FLOOR:
        return "ready"
    if score >= READINESS_FLOOR - 1.0:
        return "gap"
    return "major_gap"


def build_gap_report(db: Session, assessment_id: int) -> Dict:
    """
    Build a clause-by-clause readiness report for an assessment.

    Returns:
        {
            "assessment_id": int,
            "floor": 3.0,
            "summary": {
                "total_clauses_mapped": int,
                "clauses_ready": int,
                "clauses_with_gap": int,
                "clauses_major_gap": int,
                "overall_readiness_pct": float,    # share of clauses ready+
            },
            "sections": [
                {
                  "section": "4",
                  "title": "Context of the organization",
                  "ready": int, "total": int,
                  "clauses": [
                      {
                          "clause": "4.1",
                          "name": "...",
                          "score": 3.4 | null,
                          "gap": 0.0,                 # max(floor - score, 0)
                          "status": "ready" | "gap" | "major_gap" | "unanswered" | "unmapped" | "exceeds",
                          "questions_total": int,
                          "questions_answered": int,
                          "low_questions": [
                              {"id": 12, "code": "WM.1-03", "text": "...", "score": 2.0},
                              ...
                          ],
                      },
                      ...
                  ],
                },
                ...
            ],
        }
    """
    rows = (
        db.query(QuestionV2, ResponseV2)
        .outerjoin(
            ResponseV2,
            (ResponseV2.question_id == QuestionV2.id)
            & (ResponseV2.assessment_id == assessment_id)
            & (ResponseV2.is_draft == False)  # noqa: E712
            & (ResponseV2.is_na == False),  # noqa: E712
        )
        .filter(QuestionV2.is_active == True, QuestionV2.iso_55001_clause.isnot(None))  # noqa: E712
        .all()
    )

    # Bucket by clause code
    by_clause: Dict[str, Dict] = {}
    for q, r in rows:
        c = q.iso_55001_clause
        if not c:
            continue
        bucket = by_clause.setdefault(
            c, {"questions": [], "scores": [], "responses": []}
        )
        bucket["questions"].append(q)
        if r is not None and r.numeric_score is not None:
            bucket["scores"].append(float(r.numeric_score))
            bucket["responses"].append((q, float(r.numeric_score)))

    # Build per-clause result
    clause_results: Dict[str, Dict] = {}
    for clause_code, bucket in by_clause.items():
        questions = bucket["questions"]
        scores = bucket["scores"]
        score = round(mean(scores), 2) if scores else None
        gap = round(max(READINESS_FLOOR - score, 0.0), 2) if score is not None else None

        # Pick out low-scoring questions (below the floor) to surface as
        # actionable "fix these" items.
        low = sorted(
            [
                {
                    "id": q.id,
                    "code": q.question_code,
                    "text": q.question_text[:160],
                    "score": round(s, 1),
                }
                for q, s in bucket["responses"]
                if s < READINESS_FLOOR
            ],
            key=lambda x: x["score"],
        )

        clause_results[clause_code] = {
            "clause": clause_code,
            "name": ISO_CLAUSE_NAMES.get(clause_code, clause_code),
            "score": score,
            "gap": gap,
            "status": _status_for(score, len(scores), len(questions)),
            "questions_total": len(questions),
            "questions_answered": len(scores),
            "low_questions": low[:5],  # cap so the payload stays small
        }

    # Group clauses under their parent section in canonical order
    sections_out: List[Dict] = []
    summary_ready = 0
    summary_gap = 0
    summary_major = 0
    summary_total_mapped = 0

    for section in ISO_55001_SECTIONS:
        clauses_out = []
        section_ready = 0
        for clause_code, clause_name in section["clauses"]:
            result = clause_results.get(clause_code)
            if not result:
                # No questions tagged at this clause; mark unmapped so the UI
                # can still render the row.
                result = {
                    "clause": clause_code,
                    "name": clause_name,
                    "score": None,
                    "gap": None,
                    "status": "unmapped",
                    "questions_total": 0,
                    "questions_answered": 0,
                    "low_questions": [],
                }
            else:
                summary_total_mapped += 1
                if result["status"] in ("ready", "exceeds"):
                    summary_ready += 1
                    section_ready += 1
                elif result["status"] == "gap":
                    summary_gap += 1
                elif result["status"] == "major_gap":
                    summary_major += 1
            clauses_out.append(result)
        sections_out.append({
            "section": section["section"],
            "title": section["title"],
            "ready": section_ready,
            "total": sum(
                1
                for c in section["clauses"]
                if c[0] in clause_results
                and clause_results[c[0]]["status"] != "unmapped"
            ),
            "clauses": clauses_out,
        })

    overall_pct = (
        round(summary_ready / summary_total_mapped * 100, 1)
        if summary_total_mapped > 0
        else 0.0
    )

    return {
        "assessment_id": assessment_id,
        "floor": READINESS_FLOOR,
        "summary": {
            "total_clauses_mapped": summary_total_mapped,
            "clauses_ready": summary_ready,
            "clauses_with_gap": summary_gap,
            "clauses_major_gap": summary_major,
            "overall_readiness_pct": overall_pct,
        },
        "sections": sections_out,
    }
