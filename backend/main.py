"""
FastAPI application entry point.

Layered:
    /                     -- health + root
    /token                -- OAuth2 password login (rate-limited)
    /users                -- admin user management
    /assessments/*        -- v1 routes still consumed by the UI (finalize,
                             generate-report, report download, CMMS analyze)
    /api/v2/*             -- v2 router (current product)
    /password-reset/*     -- token-based password reset flow
    /uploads/{path}       -- authenticated download of stored evidence
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

import audit
import models_v2  # noqa: F401  -- register v2 tables with Base.metadata
import models_extra  # noqa: F401 -- register audit_log + assessment_members + reset-token usage
from api_v2 import router as v2_router
from auth import get_current_user, oauth2_scheme  # noqa: F401 (oauth2_scheme reused indirectly)
from config import assert_production_secrets, settings
from database import engine, get_db, init_db
from models import Report, User
from models_extra import PasswordResetTokenUsage
from rbac import get_v2_assessment_or_403
import storage
from security_utils import (
    hash_reset_token,
    issue_password_reset_token,
    rate_limit_login,
    resolve_local_path,
    verify_password_reset_token,
)
from storage import StoredObject

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app & middleware
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Reliability Maturity Index (RMI) Audit Platform — NextBelt LLC",
)


_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:4000",
    "https://rmi-audit-toolkit-frontend-production.up.railway.app",
]
_origins = list(_DEFAULT_ORIGINS)
if settings.FRONTEND_URL and settings.FRONTEND_URL not in _origins:
    _origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Disposition"],
    max_age=3600,
)


# The /uploads directory exists on disk but is NOT mounted as public static.
# Use the authenticated `GET /uploads/{path:path}` route below.
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app.include_router(v2_router)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    full_name: Optional[str] = None


_ALLOWED_ROLES = {"admin", "auditor", "client"}


class Token(BaseModel):
    access_token: str
    token_type: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class AssessmentSummary(BaseModel):
    assessment_id: int
    pillar_scores: Dict[str, Any]
    overall_rmi: float
    maturity_level: str
    calculated_at: str
    confidence_variance: Dict[str, Any]
    maturity_velocity: Dict[str, Any]
    iso_gap_analysis: Dict[str, Any]
    risk_adjusted: Dict[str, Any]


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), (hashed_password or "").encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _validate_password_strength(password: str) -> None:
    if not password or len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters.")
    if password.lower() in {"admin123", "password", "password123", "letmein"}:
        raise HTTPException(status_code=400, detail="Password is too common.")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
#
# Migrations are owned by Alembic now. Run them at deploy time before the
# uvicorn process starts (see backend/railway.json and DEPLOYMENT.md):
#
#     alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
#
# init_db() remains as a fallback for first-time local SQLite use: if no
# tables exist at startup, create them all from Base.metadata so a developer
# running `python -m uvicorn main:app` against a fresh sqlite file does not
# get a stack trace before they've run Alembic.


def _maybe_bootstrap_tables() -> None:
    """Create tables only if the DB has none — first-run local DX only.

    In any real deploy, `alembic upgrade head` has already run.
    """
    from sqlalchemy import inspect as sa_inspect

    inspector = sa_inspect(engine)
    if not inspector.get_table_names():
        logger.warning(
            "Database has no tables. Bootstrapping from Base.metadata for local dev. "
            "Run `alembic upgrade head` instead in any real deploy."
        )
        init_db()


@app.on_event("startup")
async def _on_startup() -> None:
    assert_production_secrets()
    _maybe_bootstrap_tables()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/")
async def root() -> dict:
    return {
        "application": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
    }


@app.get("/healthz")
async def healthz() -> dict:
    """Lightweight health probe for the load balancer."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@app.post("/register", response_model=UserResponse)
async def register_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    _validate_password_strength(payload.password)

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit.record(
        db,
        action="user.create",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_type="user",
        target_id=user.id,
        ip_address=(request.client.host if request.client else None),
        details={"email": user.email, "role": user.role},
    )
    return user


@app.post("/token", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    rate_limit_login(request, form_data.username)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        # Generic message; do not leak account existence
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token({"sub": user.email})
    audit.record(
        db,
        action="user.login",
        actor_id=user.id,
        actor_email=user.email,
        target_type="user",
        target_id=user.id,
        ip_address=(request.client.host if request.client else None),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


@app.post("/password-reset/request")
async def password_reset_request(
    payload: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Issue a reset token. Always returns 200 to avoid account enumeration.

    The token is returned in the response body in non-production so an admin
    can hand it to the user out-of-band. In production it is logged at INFO
    level so it ends up in Railway logs only. Plugging in an email provider
    is a one-line change here.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    response: Dict[str, Any] = {"ok": True}
    if user and user.is_active:
        token = issue_password_reset_token(user.id)
        if settings.ENVIRONMENT.lower() == "production":
            logger.info("password_reset_token_issued user=%s", user.email)
        else:
            response["debug_token"] = token
        audit.record(
            db,
            action="user.password_reset_requested",
            actor_id=user.id,
            actor_email=user.email,
            target_type="user",
            target_id=user.id,
            ip_address=(request.client.host if request.client else None),
        )
    return response


@app.post("/password-reset/confirm")
async def password_reset_confirm(
    payload: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = verify_password_reset_token(payload.token)

    # Single-use enforcement: a leaked/intercepted token must not be replayable
    # within its TTL. The token hash is recorded on first successful use.
    token_hash = hash_reset_token(payload.token)
    if db.query(PasswordResetTokenUsage).filter(
        PasswordResetTokenUsage.token_hash == token_hash
    ).first():
        raise HTTPException(status_code=400, detail="This reset link has already been used.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    _validate_password_strength(payload.new_password)
    user.hashed_password = get_password_hash(payload.new_password)
    db.add(PasswordResetTokenUsage(token_hash=token_hash))
    db.commit()
    audit.record(
        db,
        action="user.password_reset_confirmed",
        actor_id=user.id,
        actor_email=user.email,
        target_type="user",
        target_id=user.id,
        ip_address=(request.client.host if request.client else None),
    )
    return {"ok": True}


# ---------------------------------------------------------------------------
# Authenticated upload download
# ---------------------------------------------------------------------------


@app.get("/uploads/{path:path}")
async def serve_upload(
    path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Authenticated download for stored evidence.

    Works with either storage backend:
    - local: streams the file from UPLOAD_DIR after a path-traversal check.
    - supabase: streams from Supabase Storage via the service-role API.

    Per-assessment access is enforced when the path begins with
    ``assessments/<id>/``.
    """
    # Enforce per-assessment membership if applicable.
    parts = path.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "assessments":
        try:
            assessment_id = int(parts[1])
        except ValueError:
            assessment_id = None
        if assessment_id is not None:
            get_v2_assessment_or_403(db, assessment_id, current_user)

    if storage.backend_name() == "supabase":
        stored = StoredObject(backend="supabase", key=path, bytes=0)
        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            storage.open_stream(stored),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{os.path.basename(path)}"'},
        )

    # Local backend
    full = resolve_local_path(os.path.join(settings.UPLOAD_DIR, path))
    return FileResponse(full, filename=os.path.basename(full))


# ---------------------------------------------------------------------------
# Assessment lifecycle endpoints (v2-only).
#   POST /assessments/{id}/finalize
#   POST /assessments/{id}/generate-report
#   GET  /assessments/{id}/report/download
#
# CMMS upload lives under /api/v2/assessments/{id}/cmms-uploads. The legacy v1
# routes and pillar engine have been removed — the product is v2 only.
# ---------------------------------------------------------------------------


@app.post("/assessments/{assessment_id}/finalize")
async def finalize_assessment(
    assessment_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = get_v2_assessment_or_403(db, assessment_id, current_user)
    if getattr(assessment, "finalized_at", None):
        return {"message": "Assessment already finalized", "finalized_at": assessment.finalized_at}

    assessment.finalized_at = datetime.utcnow()
    assessment.status = "completed"
    assessment.completed_at = datetime.utcnow()
    db.commit()

    audit.record(
        db,
        action="assessment.finalize",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_type="assessment_v2",
        target_id=assessment_id,
        ip_address=(request.client.host if request.client else None),
    )
    return {"message": "Assessment finalized", "finalized_at": assessment.finalized_at}


@app.post("/assessments/{assessment_id}/generate-report")
async def generate_report(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate the branded executive PDF report for a v2 assessment.

    PDF rendering (matplotlib + reportlab) is CPU-bound, so it runs in a
    threadpool to avoid blocking the async event loop.
    """
    get_v2_assessment_or_403(db, assessment_id, current_user)
    from report_generator_v2 import ReportGeneratorV2

    generator = ReportGeneratorV2(db, output_dir=settings.REPORT_OUTPUT_DIR)
    try:
        pdf_path = await run_in_threadpool(
            generator.generate, assessment_id=assessment_id, generated_by=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    audit.record(
        db,
        action="assessment.report.generate",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_type="assessment_v2",
        target_id=assessment_id,
    )
    return {
        "message": "Report generated successfully",
        "file_path": pdf_path,
        "download_url": f"/assessments/{assessment_id}/report/download",
    }


@app.get("/assessments/{assessment_id}/report/download")
async def download_report(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_v2_assessment_or_403(db, assessment_id, current_user)

    report = (
        db.query(Report)
        .filter(Report.assessment_id == assessment_id)
        .order_by(Report.generated_at.desc())
        .first()
    )
    if not report or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not found. Generate a report first.")

    full = str(report.file_path)
    if not os.path.isfile(full):
        raise HTTPException(status_code=404, detail="Report file missing")
    return FileResponse(path=full, filename=os.path.basename(full), media_type="application/pdf")


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------


@app.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(User).all()


@app.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    updates: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if updates.role is not None and updates.role not in _ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{updates.role}'. Allowed: {sorted(_ALLOWED_ROLES)}",
        )

    changed: Dict[str, Any] = {}
    for field in ("is_active", "role", "full_name"):
        value = getattr(updates, field)
        if value is not None:
            setattr(user, field, value)
            changed[field] = value

    db.commit()
    db.refresh(user)
    audit.record(
        db,
        action="user.update",
        actor_id=current_user.id,
        actor_email=current_user.email,
        target_type="user",
        target_id=user_id,
        ip_address=(request.client.host if request.client else None),
        details=changed,
    )
    return {"message": "User updated", "changes": changed}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["./"], log_level="info")
