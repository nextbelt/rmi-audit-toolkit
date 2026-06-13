"""
RMI vNext API v2 Router
All new endpoints under /api/v2/
v1 endpoints remain untouched at root.
"""
import logging
import os
import tempfile
from datetime import datetime, date
from typing import List, Optional
import json

from fastapi import (
    APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
)
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import audit
import storage
from auth import get_current_user
from database import get_db
from models import User
from models_v2 import (
    AssessmentV2, ResponseV2, QuestionV2, SubdomainScore,
    Domain, Subdomain, Practice, BenchmarkMetadata, CalibrationExercise,
    CMMSUploadV2,
    AssessmentMode, IndustryModule, EvidenceStatus, TargetRoleV2,
    DomainType, SubdomainType,
)
from rbac import filter_v2_visible, get_v2_assessment_or_403
from scoring_engine_v2 import ScoringEngineV2
from routing_engine import RoutingEngine
from benchmarking_engine import BenchmarkingEngine
from practice_engine import PracticeEngine
from security_utils import (
    save_upload,
    assessment_upload_subdir,
    materialize_local,
)
from storage import StoredObject

logger = logging.getLogger(__name__)

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
        region=(data.region or None),
        employee_count=data.employee_count,
        lead_assessor=(data.lead_assessor or None),
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
        # role_counts is always derived from the full (unfiltered) set. When no
        # role filter is requested (the common "ALL" path) we reuse that set and
        # skip a second routing pass. Role-specific routing is NOT a plain subset
        # of the full set (critical questions + min-fill), so it must go through
        # the engine when a role is requested.
        all_questions = engine.get_questions(assessment_id, None)
        questions = all_questions if role_filter is None else engine.get_questions(assessment_id, role_filter)
    except ValueError as e:
        raise HTTPException(404, str(e))

    role_counts: dict = {}
    for q in all_questions:
        r = q.get("target_role") or "UNKNOWN"
        role_counts[r] = role_counts.get(r, 0) + 1

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
            "evidence_file": {
                "filename": r.evidence_filename,
                "mime": r.evidence_mime,
                "size_bytes": r.evidence_size_bytes,
                "uploaded_at": r.evidence_uploaded_at.isoformat() if r.evidence_uploaded_at else None,
            } if r.evidence_file_path else None,
            "ai_analysis": {
                "suggested_score": r.ai_suggested_score,
                "observations": r.ai_observations,
                "confidence": r.ai_confidence,
                "analyzed_at": r.ai_analyzed_at.isoformat() if r.ai_analyzed_at else None,
            } if r.ai_analyzed_at else None,
            "is_na": r.is_na,
            "is_draft": r.is_draft,
        }
        for r in responses
    ]


def _upsert_response(db: Session, assessment_id: int, data: QuestionResponseCreate) -> ResponseV2:
    """Upsert a single response WITHOUT committing.

    Shared by the single and bulk endpoints so a batch is one transaction.
    Raises HTTPException(404) if the question is unknown.
    """
    question = db.query(QuestionV2).filter(QuestionV2.id == data.question_id).first()
    if not question:
        raise HTTPException(404, "Question not found")

    role_enum = None
    if data.respondent_role:
        try:
            role_enum = TargetRoleV2(data.respondent_role)
        except ValueError:
            pass

    explicit_status: Optional[EvidenceStatus] = None
    if data.evidence_status:
        try:
            explicit_status = EvidenceStatus(data.evidence_status)
        except ValueError:
            explicit_status = None

    existing = db.query(ResponseV2).filter(
        ResponseV2.assessment_id == assessment_id,
        ResponseV2.question_id == data.question_id,
        ResponseV2.respondent_role == role_enum,
    ).first()

    # Determine the right evidence_status for this response.
    #
    # The frontend ships "not_required" by default for every save, which is
    # only correct when the question doesn't require evidence. For questions
    # that DO require evidence we need to reflect reality:
    #   - file already on the row + previously ACCEPTED → keep ACCEPTED
    #   - file already on the row (PENDING_VERIFICATION) → keep that
    #   - no file → PENDING_EVIDENCE (so confidence is correctly docked)
    has_evidence_file = bool(existing and existing.evidence_file_path)
    prior_status = existing.evidence_status if existing else None

    if explicit_status is not None and explicit_status != EvidenceStatus.NOT_REQUIRED:
        evidence_enum = explicit_status
    elif not question.evidence_required:
        evidence_enum = EvidenceStatus.NOT_REQUIRED
    elif has_evidence_file:
        evidence_enum = (
            prior_status
            if prior_status in (EvidenceStatus.ACCEPTED, EvidenceStatus.PENDING_VERIFICATION)
            else EvidenceStatus.PENDING_VERIFICATION
        )
    else:
        evidence_enum = EvidenceStatus.PENDING_EVIDENCE

    if existing:
        existing.numeric_score = data.numeric_score
        existing.response_value = data.text_response or (str(data.numeric_score) if data.numeric_score else None)
        existing.is_na = data.is_na
        existing.is_draft = data.is_draft
        existing.evidence_status = evidence_enum
        existing.evidence_grade = data.evidence_grade
        existing.evidence_notes = data.notes
        existing.answered_at = datetime.utcnow()
        return existing

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
    return response


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

    response = _upsert_response(db, assessment_id, data)
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
    """Submit multiple responses at once — one transaction for the whole batch."""
    assessment = get_v2_assessment_or_403(db, assessment_id, current_user)
    if getattr(assessment, "finalized_at", None) is not None:
        raise HTTPException(403, "Assessment is finalized; responses cannot be modified.")

    results = []
    for resp in data.responses:
        try:
            _upsert_response(db, assessment_id, resp)
            results.append({"question_id": resp.question_id, "status": "ok"})
        except HTTPException as e:
            results.append({"question_id": resp.question_id, "status": "error", "detail": e.detail})

    db.commit()
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
#  ISO 55001 gap report
# ═══════════════════════════════════════════

@router.get("/assessments/{assessment_id}/iso-55001-gaps")
def iso_55001_gaps(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clause-by-clause ISO 55001 readiness report.

    For each ISO 55001 clause referenced by the question bank, returns the
    mean response score, gap from the readiness floor (3.0), and any
    low-scoring questions feeding that clause.
    """
    get_v2_assessment_or_403(db, assessment_id, current_user)
    from iso_55001 import build_gap_report
    return build_gap_report(db, assessment_id)


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
#  Evidence Upload & AI Analysis
# ═══════════════════════════════════════════

def _get_response_or_404(
    db: Session, assessment_id: int, question_id: int, current_user: User
) -> ResponseV2:
    """Resolve the response row for (assessment, question). 403/404 as needed."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    response = (
        db.query(ResponseV2)
        .filter(
            ResponseV2.assessment_id == assessment_id,
            ResponseV2.question_id == question_id,
        )
        .order_by(ResponseV2.id.desc())
        .first()
    )
    if not response:
        raise HTTPException(404, "Response not found — answer the question before uploading evidence.")
    return response


@router.post("/assessments/{assessment_id}/responses/{question_id}/evidence")
async def upload_evidence(
    assessment_id: int,
    question_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Attach an evidence file to a response."""
    assessment = get_v2_assessment_or_403(db, assessment_id, current_user)
    if getattr(assessment, "finalized_at", None) is not None:
        raise HTTPException(403, "Assessment is finalized; evidence cannot be modified.")

    response = _get_response_or_404(db, assessment_id, question_id, current_user)

    subdir = assessment_upload_subdir(assessment_id, "evidence")
    stored = await save_upload(file, subdir=subdir)

    # If there was a prior evidence file, drop the old object
    if response.evidence_file_path:
        try:
            storage.delete_object(StoredObject.parse(response.evidence_file_path))
        except Exception as exc:
            logger.warning("Failed to delete prior evidence: %s", exc)

    response.evidence_file_path = stored.serialize()
    response.evidence_filename = file.filename
    response.evidence_mime = stored.mime or file.content_type
    response.evidence_size_bytes = stored.bytes
    response.evidence_uploaded_at = datetime.utcnow()

    # Move evidence_status forward if it was waiting
    if response.evidence_status == EvidenceStatus.PENDING_EVIDENCE:
        response.evidence_status = EvidenceStatus.PENDING_VERIFICATION

    db.commit()
    db.refresh(response)

    audit.record(
        db,
        action="response.evidence.upload",
        actor_id=int(current_user.id),
        actor_email=str(current_user.email),
        target_type="response_v2",
        target_id=response.id,
        details={"question_id": question_id, "filename": file.filename, "bytes": stored.bytes},
    )

    return {
        "filename": response.evidence_filename,
        "mime": response.evidence_mime,
        "size_bytes": response.evidence_size_bytes,
        "uploaded_at": response.evidence_uploaded_at.isoformat(),
        "evidence_status": response.evidence_status.value if response.evidence_status else None,
    }


@router.get("/assessments/{assessment_id}/responses/{question_id}/evidence")
def download_evidence(
    assessment_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream the evidence file back to the caller. Supabase signed URLs are
    returned via 302 by the storage layer; local files stream directly."""
    response = _get_response_or_404(db, assessment_id, question_id, current_user)
    if not response.evidence_file_path:
        raise HTTPException(404, "No evidence uploaded for this response")

    stored = StoredObject.parse(response.evidence_file_path)

    signed = storage.get_signed_url(stored, ttl_seconds=300)
    if signed:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(signed, status_code=302)

    return StreamingResponse(
        storage.open_stream(stored),
        media_type=response.evidence_mime or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{response.evidence_filename or "evidence"}"',
        },
    )


@router.delete("/assessments/{assessment_id}/responses/{question_id}/evidence")
def delete_evidence(
    assessment_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detach (and delete) the evidence file from a response."""
    assessment = get_v2_assessment_or_403(db, assessment_id, current_user)
    if getattr(assessment, "finalized_at", None) is not None:
        raise HTTPException(403, "Assessment is finalized; evidence cannot be modified.")

    response = _get_response_or_404(db, assessment_id, question_id, current_user)
    if not response.evidence_file_path:
        return {"deleted": False}

    try:
        storage.delete_object(StoredObject.parse(response.evidence_file_path))
    except Exception as exc:
        logger.warning("Storage delete failed (continuing): %s", exc)

    response.evidence_file_path = None
    response.evidence_filename = None
    response.evidence_mime = None
    response.evidence_size_bytes = None
    response.evidence_uploaded_at = None
    response.ai_suggested_score = None
    response.ai_observations = None
    response.ai_confidence = None
    response.ai_analyzed_at = None

    # Drop evidence_status back to the right resting state for this question
    question = db.query(QuestionV2).filter(QuestionV2.id == question_id).first()
    if question and question.evidence_required:
        response.evidence_status = EvidenceStatus.PENDING_EVIDENCE
    else:
        response.evidence_status = EvidenceStatus.NOT_REQUIRED

    db.commit()

    return {"deleted": True}


@router.post("/assessments/{assessment_id}/responses/{question_id}/analyze-evidence")
def analyze_evidence(
    assessment_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the AI evidence analyzer against the uploaded file."""
    from config import settings

    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI analysis unavailable — OPENAI_API_KEY is not configured.")

    response = _get_response_or_404(db, assessment_id, question_id, current_user)
    if not response.evidence_file_path:
        raise HTTPException(400, "Upload evidence before running AI analysis.")

    question = db.query(QuestionV2).filter(QuestionV2.id == question_id).first()
    if not question:
        raise HTTPException(404, "Question not found")

    rubric = question.scoring_rubric
    if isinstance(rubric, str):
        try:
            rubric = json.loads(rubric)
        except (json.JSONDecodeError, TypeError):
            rubric = {}

    # Read the file bytes
    stored = StoredObject.parse(response.evidence_file_path)
    file_bytes = b"".join(storage.open_stream(stored))

    # Lazy import so the rest of the API still works without OpenAI configured
    from ai_scoring import AIScoringEngine

    engine = AIScoringEngine()
    result = engine.analyze_evidence(
        question_text=question.question_text,
        question_code=question.question_code,
        scoring_rubric=rubric if isinstance(rubric, dict) else None,
        file_bytes=file_bytes,
        mime_type=response.evidence_mime,
        filename=response.evidence_filename,
        existing_notes=response.evidence_notes,
    )

    response.ai_suggested_score = result.get("numeric_score")
    response.ai_observations = result.get("observations")
    response.ai_confidence = result.get("confidence")
    response.ai_analyzed_at = datetime.utcnow()
    db.commit()

    audit.record(
        db,
        action="response.evidence.analyze",
        actor_id=int(current_user.id),
        actor_email=str(current_user.email),
        target_type="response_v2",
        target_id=response.id,
        details={
            "question_id": question_id,
            "suggested_score": result.get("numeric_score"),
            "confidence": result.get("confidence"),
        },
    )

    return {
        "suggested_score": result.get("numeric_score"),
        "observations": result.get("observations"),
        "confidence": result.get("confidence"),
        "key_findings": result.get("key_findings", []),
        "analyzed_kind": result.get("analyzed_kind"),
        "analyzed_at": response.ai_analyzed_at.isoformat(),
    }


# ═══════════════════════════════════════════
#  CMMS Snapshot Upload
# ═══════════════════════════════════════════

def _analyze_cmms_file(kind: str, local_path: str) -> dict:
    """CPU-bound CMMS parse + metrics. Runs in a threadpool (no DB access)."""
    from data_analysis_module import CMMSDataAnalyzer

    analyzer = CMMSDataAnalyzer(db=None)  # the methods used here don't touch the DB
    if kind == "work_orders":
        df = analyzer.import_work_orders(local_path)
        metrics = analyzer.analyze_work_orders(0, 0, local_path)
        try:
            ba = analyzer.detect_bad_actors(df, top_n=10).to_dict()
            bad_actors = list(ba.get("failure_count", {}).items()) if isinstance(ba, dict) else []
        except Exception:
            bad_actors = []  # bad-actor detection needs an asset column; optional
        return {"metrics": metrics, "bad_actors": bad_actors, "record_count": int(len(df))}

    df = analyzer.import_pm_data(local_path)
    metrics = analyzer.analyze_pm_compliance(0, 0, local_path)
    return {"metrics": metrics, "bad_actors": None, "record_count": int(len(df))}


@router.post("/assessments/{assessment_id}/cmms-uploads")
async def upload_cmms_snapshot(
    assessment_id: int,
    file: UploadFile = File(...),
    kind: str = Form("work_orders"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a CMMS data snapshot (CSV or Excel) and run analysis.

    `kind` is "work_orders" (default) or "pm".
    """
    assessment = get_v2_assessment_or_403(db, assessment_id, current_user)
    if getattr(assessment, "finalized_at", None) is not None:
        raise HTTPException(403, "Assessment is finalized; uploads disabled.")

    kind = kind.lower().strip()
    if kind not in {"work_orders", "pm"}:
        raise HTTPException(400, "kind must be 'work_orders' or 'pm'")

    subdir = assessment_upload_subdir(assessment_id, "cmms")
    stored = await save_upload(file, subdir=subdir)

    upload = CMMSUploadV2(
        assessment_id=assessment_id,
        kind=kind,
        file_path=stored.serialize(),
        original_filename=file.filename,
        file_size_bytes=stored.bytes,
        uploaded_by=current_user.id,
        status="processing",
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    # Materialize the file to a local path for pandas, then run the CPU-bound
    # parse/metrics in a threadpool so the async event loop isn't blocked.
    local_path, is_temp = materialize_local(stored)
    try:
        analysis = await run_in_threadpool(_analyze_cmms_file, kind, local_path)
        upload.metrics = analysis["metrics"]
        if analysis["bad_actors"] is not None:
            upload.bad_actors = analysis["bad_actors"]
        upload.record_count = analysis["record_count"]
        upload.status = "processed"
    except Exception as exc:
        logger.exception("CMMS analysis failed")
        upload.status = "error"
        upload.error_message = str(exc)[:500]
    finally:
        if is_temp:
            try:
                os.remove(local_path)
            except Exception:
                pass

    db.commit()
    db.refresh(upload)

    audit.record(
        db,
        action="assessment.cmms.upload",
        actor_id=int(current_user.id),
        actor_email=str(current_user.email),
        target_type="assessment_v2",
        target_id=assessment_id,
        details={"upload_id": upload.id, "kind": kind, "status": upload.status},
    )

    return _format_cmms_upload(upload)


@router.get("/assessments/{assessment_id}/cmms-uploads")
def list_cmms_uploads(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List CMMS uploads attached to an assessment."""
    get_v2_assessment_or_403(db, assessment_id, current_user)
    rows = (
        db.query(CMMSUploadV2)
        .filter(CMMSUploadV2.assessment_id == assessment_id)
        .order_by(CMMSUploadV2.uploaded_at.desc())
        .all()
    )
    return [_format_cmms_upload(r) for r in rows]


@router.delete("/assessments/{assessment_id}/cmms-uploads/{upload_id}")
def delete_cmms_upload(
    assessment_id: int,
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a CMMS upload (file + metrics)."""
    assessment = get_v2_assessment_or_403(db, assessment_id, current_user)
    if getattr(assessment, "finalized_at", None) is not None:
        raise HTTPException(403, "Assessment is finalized; uploads cannot be modified.")

    row = (
        db.query(CMMSUploadV2)
        .filter(CMMSUploadV2.id == upload_id, CMMSUploadV2.assessment_id == assessment_id)
        .first()
    )
    if not row:
        raise HTTPException(404, "CMMS upload not found")

    try:
        storage.delete_object(StoredObject.parse(row.file_path))
    except Exception as exc:
        logger.warning("Failed to delete CMMS file from storage: %s", exc)

    db.delete(row)
    db.commit()
    return {"deleted": True}


def _format_cmms_upload(u: CMMSUploadV2) -> dict:
    return {
        "id": u.id,
        "assessment_id": u.assessment_id,
        "kind": u.kind,
        "original_filename": u.original_filename,
        "file_size_bytes": u.file_size_bytes,
        "status": u.status,
        "error_message": u.error_message,
        "metrics": u.metrics,
        "bad_actors": u.bad_actors,
        "record_count": u.record_count,
        "uploaded_at": u.uploaded_at.isoformat() if u.uploaded_at else None,
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
        "region": a.region,
        "employee_count": a.employee_count,
        "lead_assessor": a.lead_assessor,
    }
