"""
RMI vNext API v2 Router
All new endpoints under /api/v2/
v1 endpoints remain untouched at root.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import json

from database import get_db
from models import User
from auth import get_current_user
from models_v2 import (
    AssessmentV2, ResponseV2, QuestionV2, SubdomainScore,
    Domain, Subdomain, Practice, BenchmarkMetadata, CalibrationExercise,
    AssessmentMode, IndustryModule, EvidenceStatus, TargetRoleV2,
    DomainType, SubdomainType
)
from scoring_engine_v2 import ScoringEngineV2
from routing_engine import RoutingEngine
from benchmarking_engine import BenchmarkingEngine
from practice_engine import PracticeEngine
from rbac import filter_v2_visible, get_v2_assessment_or_403
import audit

router = APIRouter(prefix="/api/v2", tags=["vNext"])


# ═══════════════════════════════════════════
#  Pydantic Schemas
# ═══════════════════════════════════════════

class AssessmentCreate(BaseModel):
    organization_name: str
    site_name: str
    assessment_mode: str = "standard"
    assessment_date: Optional[str] = None
    industry_module: Optional[str] = None
    region: Optional[str] = None
    employee_count: Optional[int] = None
    lead_assessor: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: int
    organization_name: str
    site_name: str
    assessment_mode: str
    industry_module: Optional[str]
    overall_rmi: Optional[float]
    maturity_level: Optional[str]
    confidence_score: Optional[float]
    assessment_date: Optional[str]
    status: str

    class Config:
        from_attributes = True


class QuestionResponseCreate(BaseModel):
    question_id: int
    numeric_score: Optional[float] = None
    text_response: Optional[str] = None
    respondent_role: Optional[str] = None
    respondent_name: Optional[str] = None
    is_na: bool = False
    is_draft: bool = False
    evidence_status: str = "not_required"
    evidence_grade: Optional[str] = None
    notes: Optional[str] = None


class BulkResponseCreate(BaseModel):
    responses: List[QuestionResponseCreate]


class ModeUpgrade(BaseModel):
    new_mode: str


# ═══════════════════════════════════════════
#  Health
# ═══════════════════════════════════════════

@router.get("/health")
def health():
    return {"status": "ok", "version": "2.0", "framework": "RMI vNext"}


# ═══════════════════════════════════════════
#  Framework Structure
# ═══════════════════════════════════════════

@router.get("/framework")
def get_framework(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return the full domain/subdomain structure."""
    domains = db.query(Domain).order_by(Domain.display_order).all()
    result = []
    for dom in domains:
        subdomains = db.query(Subdomain).filter(
            Subdomain.domain_id == dom.id
        ).order_by(Subdomain.display_order).all()

        result.append({
            "code": dom.code,
            "name": dom.name,
            "description": dom.description,
            "subdomains": [
                {"code": sd.code, "name": sd.name}
                for sd in subdomains
            ],
        })
    return {"domains": result}


# ═══════════════════════════════════════════
#  Assessments
# ═══════════════════════════════════════════

@router.post("/assessments", response_model=AssessmentResponse)
def create_assessment(data: AssessmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new vNext assessment."""
    try:
        mode = AssessmentMode(data.assessment_mode)
    except ValueError:
        raise HTTPException(400, f"Invalid mode: {data.assessment_mode}. "
                                 f"Use: quickscan, standard, or deepdive")

    industry = None
    if data.industry_module:
        try:
            industry = IndustryModule(data.industry_module)
        except ValueError:
            raise HTTPException(400, f"Invalid industry: {data.industry_module}")

    assess_date = date.today()
    if data.assessment_date:
        try:
            assess_date = date.fromisoformat(data.assessment_date[:10])
        except (ValueError, TypeError):
            pass

    assessment = AssessmentV2(
        client_name=data.organization_name,
        site_name=data.site_name,
        assessment_mode=mode,
        industry_module=industry,
        assessment_date=assess_date,
        status="in_progress",
        creator_id=current_user.id,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return _format_assessment(assessment)


@router.get("/assessments")
def list_assessments(
    skip: int = 0, limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List vNext assessments visible to the current user (admin sees all)."""
    query = db.query(AssessmentV2).order_by(AssessmentV2.assessment_date.desc())
    query = filter_v2_visible(db, query, current_user)
    assessments = query.offset(skip).limit(limit).all()

    return [_format_assessment(a) for a in assessments]


@router.get("/assessments/{assessment_id}")
def get_assessment(assessment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a single assessment with subdomain scores."""
    assessment = get_v2_assessment_or_403(db, assessment_id, current_user)

    result = _format_assessment(assessment)

    # Include subdomain scores if scored
    if assessment.overall_rmi is not None:
        scores = (
            db.query(SubdomainScore, Subdomain)
            .join(Subdomain)
            .filter(SubdomainScore.assessment_id == assessment_id)
            .order_by(Subdomain.display_order)
            .all()
        )
        result["subdomain_scores"] = [
            {
                "subdomain_code": sd.code,
                "subdomain_name": sd.name,
                "raw_score": sc.raw_score,
                "final_score": sc.final_score,
                "cap_applied": sc.cap_applied,
                "cap_reason": sc.cap_reason,
            }
            for sc, sd in scores
        ]

    return result


# ═══════════════════════════════════════════
#  Questions / Routing
# ═══════════════════════════════════════════

@router.get("/assessments/{assessment_id}/questions")
def get_questions(
    assessment_id: int,
    respondent_role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get routed questions for an assessment based on its mode."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    engine = RoutingEngine(db)
    role_filter = None
    if respondent_role and respondent_role != 'ALL':
        try:
            role_filter = TargetRoleV2(respondent_role)
        except ValueError:
            pass
    try:
        questions = engine.get_questions(assessment_id, role_filter)
        # Always compute role counts from the full (unfiltered) question set
        all_questions = engine.get_questions(assessment_id, None)
        role_counts: dict = {}
        for q in all_questions:
            r = q.get("target_role") or "UNKNOWN"
            role_counts[r] = role_counts.get(r, 0) + 1
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {
        "questions": questions,
        "total": len(questions),
        "role_counts": role_counts,
    }


@router.get("/assessments/{assessment_id}/progress")
def get_progress(assessment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get completion progress for an assessment."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    engine = RoutingEngine(db)
    try:
        return engine.get_progress(assessment_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/assessments/{assessment_id}/upgrade-mode")
def upgrade_mode(
    assessment_id: int,
    data: ModeUpgrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upgrade assessment mode (QuickScan → Standard → DeepDive)."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    try:
        new_mode = AssessmentMode(data.new_mode)
    except ValueError:
        raise HTTPException(400, f"Invalid mode: {data.new_mode}")

    engine = RoutingEngine(db)
    try:
        return engine.upgrade_mode(assessment_id, new_mode)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════
#  Responses
# ═══════════════════════════════════════════

@router.get("/assessments/{assessment_id}/responses")
def get_responses(assessment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return all saved responses for an assessment."""
    get_v2_assessment_or_403(db, assessment_id, current_user)

    responses = db.query(ResponseV2).filter(
        ResponseV2.assessment_id == assessment_id
    ).all()

    return [
        {
            "id": r.id,
            "question_id": r.question_id,
            "numeric_score": r.numeric_score,
            "response_value": r.response_value,
            "respondent_role": r.respondent_role.value if r.respondent_role else None,
            "evidence_notes": r.evidence_notes,
            "evidence_status": r.evidence_status.value if r.evidence_status else None,
            "evidence_grade": r.evidence_grade,
            "is_na": r.is_na,
            "is_draft": r.is_draft,
        }
        for r in responses
    ]


@router.post("/assessments/{assessment_id}/responses")
def submit_response(
    assessment_id: int,
    data: QuestionResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a single question response."""
    assessment = get_v2_assessment_or_403(db, assessment_id, current_user)
    if getattr(assessment, "finalized_at", None) is not None:
        raise HTTPException(
            status_code=403,
            detail="Assessment is finalized; responses cannot be modified.",
        )

    question = db.query(QuestionV2).filter(
        QuestionV2.id == data.question_id
    ).first()
    if not question:
        raise HTTPException(404, "Question not found")

    # Upsert: check for existing response
    role_enum = None
    if data.respondent_role:
        try:
            role_enum = TargetRoleV2(data.respondent_role)
        except ValueError:
            pass

    evidence_enum = EvidenceStatus.NOT_REQUIRED
    try:
        evidence_enum = EvidenceStatus(data.evidence_status)
    except ValueError:
        pass

    existing = db.query(ResponseV2).filter(
        ResponseV2.assessment_id == assessment_id,
        ResponseV2.question_id == data.question_id,
        ResponseV2.respondent_role == role_enum,
    ).first()

    if existing:
        existing.numeric_score = data.numeric_score
        existing.response_value = data.text_response or (str(data.numeric_score) if data.numeric_score else None)
        existing.is_na = data.is_na
        existing.is_draft = data.is_draft
        existing.evidence_status = evidence_enum
        existing.evidence_grade = data.evidence_grade
        existing.evidence_notes = data.notes
        existing.answered_at = datetime.utcnow()
        response = existing
    else:
        response = ResponseV2(
            assessment_id=assessment_id,
            question_id=data.question_id,
            numeric_score=data.numeric_score,
            response_value=data.text_response or (str(data.numeric_score) if data.numeric_score else None),
            respondent_role=role_enum,
            is_na=data.is_na,
            is_draft=data.is_draft,
            evidence_status=evidence_enum,
            evidence_grade=data.evidence_grade,
            evidence_notes=data.notes,
        )
        db.add(response)

    db.commit()
    db.refresh(response)

    return {
        "id": response.id,
        "question_id": response.question_id,
        "numeric_score": response.numeric_score,
        "evidence_status": response.evidence_status.value if response.evidence_status else None,
        "is_draft": response.is_draft,
    }


@router.post("/assessments/{assessment_id}/responses/bulk")
def submit_responses_bulk(
    assessment_id: int,
    data: BulkResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit multiple responses at once."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    results = []
    for resp in data.responses:
        try:
            result = submit_response(assessment_id, resp, db, current_user)
            results.append({"question_id": resp.question_id, "status": "ok"})
        except HTTPException as e:
            results.append({"question_id": resp.question_id, "status": "error", "detail": e.detail})
    return {"submitted": len(results), "results": results}


# ═══════════════════════════════════════════
#  Scoring
# ═══════════════════════════════════════════

@router.post("/assessments/{assessment_id}/calculate-scores")
def calculate_scores(assessment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Run the full vNext scoring pipeline."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    engine = ScoringEngineV2(db)
    try:
        result = engine.calculate(assessment_id)
        audit.record(
            db,
            action="assessment.score",
            actor_id=int(current_user.id),  # type: ignore[arg-type]
            actor_email=str(current_user.email),  # type: ignore[arg-type]
            target_type="assessment_v2",
            target_id=assessment_id,
            details={"overall_rmi": result.get("overall_rmi")},
        )
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


# ═══════════════════════════════════════════
#  Benchmarking
# ═══════════════════════════════════════════

@router.get("/assessments/{assessment_id}/benchmark")
def benchmark_assessment(assessment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get percentile benchmarks for an assessment."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    engine = BenchmarkingEngine(db)
    try:
        return engine.benchmark_assessment(assessment_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/benchmarks/industry/{industry}")
def get_industry_stats(industry: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get aggregated industry benchmarks."""
    engine = BenchmarkingEngine(db)
    return engine.get_industry_stats(industry)


@router.post("/benchmarks/portfolio")
def portfolio_benchmark(
    site_names: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Multi-site portfolio benchmarking."""
    engine = BenchmarkingEngine(db)
    return engine.portfolio_benchmark(site_names)


# ═══════════════════════════════════════════
#  Practice Library
# ═══════════════════════════════════════════

@router.get("/assessments/{assessment_id}/recommendations")
def get_recommendations(
    assessment_id: int,
    top_n: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get prioritized improvement recommendations."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    engine = PracticeEngine(db)
    try:
        return engine.get_recommendations(assessment_id, top_n)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/practices/{practice_id}")
def get_practice(practice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get detailed practice information."""
    engine = PracticeEngine(db)
    result = engine.get_practice_detail(practice_id)
    if not result:
        raise HTTPException(404, "Practice not found")
    return result


@router.get("/practices/subdomain/{subdomain_code}")
def get_subdomain_practices(subdomain_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all practices for a subdomain."""
    engine = PracticeEngine(db)
    return engine.get_subdomain_practices(subdomain_code)


# ═══════════════════════════════════════════
#  Questions (direct access)
# ═══════════════════════════════════════════

@router.get("/questions")
def list_all_questions(
    subdomain: Optional[str] = None,
    mode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all questions, optionally filtered."""
    query = db.query(QuestionV2).filter(QuestionV2.is_active == True)

    if subdomain:
        sd = db.query(Subdomain).filter(Subdomain.code == subdomain).first()
        if sd:
            query = query.filter(QuestionV2.subdomain_id == sd.id)

    if mode:
        query = query.filter(QuestionV2.assessment_modes.contains(mode))

    questions = query.order_by(QuestionV2.question_code).all()

    sd_map = {sd.id: sd for sd in db.query(Subdomain).all()}
    return {
        "questions": [
            {
                "id": q.id,
                "code": q.question_code,
                "text": q.question_text,
                "type": q.question_type,
                "subdomain": sd_map[q.subdomain_id].code if q.subdomain_id in sd_map else None,
                "target_role": q.target_role.value if q.target_role else None,
                "weight": q.weight,
                "is_critical": q.is_critical,
                "evidence_required": q.evidence_required,
            }
            for q in questions
        ],
        "total": len(questions),
    }


# ═══════════════════════════════════════════
#  Calibration
# ═══════════════════════════════════════════

@router.get("/questions/{question_id}/calibration")
def get_calibration_anchor(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the calibration anchor for a question."""
    q = db.query(QuestionV2).filter(QuestionV2.id == question_id).first()
    if not q:
        raise HTTPException(404, "Question not found")

    rubric = q.scoring_rubric
    if isinstance(rubric, str):
        try:
            rubric = json.loads(rubric)
        except (json.JSONDecodeError, TypeError):
            rubric = {}

    return {
        "question_code": q.question_code,
        "calibration_anchor": q.calibration_anchor,
        "scoring_rubric": rubric,
        "iso_55001_clause": q.iso_55001_clause,
    }


# ═══════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════

def _format_assessment(a: AssessmentV2) -> dict:
    return {
        "id": a.id,
        "organization_name": a.client_name,
        "site_name": a.site_name,
        "assessment_mode": a.assessment_mode.value if a.assessment_mode else None,
        "industry_module": a.industry_module.value if a.industry_module else None,
        "overall_rmi": a.overall_rmi,
        "maturity_level": a.maturity_level,
        "confidence_score": a.confidence_score,
        "assessment_date": a.assessment_date.isoformat() if a.assessment_date else None,
        "status": a.status or "in_progress",
    }
