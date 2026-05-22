"""
RMI vNext Models — v2 Database Schema
Extends v1 models with 5-domain taxonomy, subdomain scoring,
assessment modes, industry modules, practice library, benchmarking,
and auditor calibration.

All v1 models remain untouched in models.py for backward compatibility.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


# ===================== vNext ENUMS =====================

class DomainType(str, enum.Enum):
    """Five domains of RMI vNext assessment"""
    WC = "WC"   # Workforce Capability
    LC = "LC"   # Leadership & Culture
    WM = "WM"   # Work Management
    AI = "AI"   # Asset Information
    SG = "SG"   # Strategy & Governance


class SubdomainType(str, enum.Enum):
    """15 subdomains (3 per domain)"""
    # Workforce Capability
    WC_1 = "WC.1"  # Technical Competency
    WC_2 = "WC.2"  # Training & Development
    WC_3 = "WC.3"  # Knowledge Management
    # Leadership & Culture
    LC_1 = "LC.1"  # Management Commitment
    LC_2 = "LC.2"  # Safety & Reliability Culture
    LC_3 = "LC.3"  # Organizational Structure
    # Work Management
    WM_1 = "WM.1"  # Planning & Scheduling
    WM_2 = "WM.2"  # Preventive/Predictive Maintenance
    WM_3 = "WM.3"  # Work Execution & Quality
    # Asset Information
    AI_1 = "AI.1"  # CMMS/EAM Effectiveness
    AI_2 = "AI.2"  # Data Quality & Integrity
    AI_3 = "AI.3"  # Analytics & Decision Support
    # Strategy & Governance
    SG_1 = "SG.1"  # Asset Management Policy
    SG_2 = "SG.2"  # Performance Measurement
    SG_3 = "SG.3"  # Continuous Improvement


class AssessmentMode(str, enum.Enum):
    """Three assessment tiers"""
    QUICKSCAN = "quickscan"   # 15 questions, free
    STANDARD = "standard"     # 60-75 questions, paid
    DEEPDIVE = "deepdive"     # 150+ questions, premium


class IndustryModule(str, enum.Enum):
    """Industry vertical modules"""
    MFG = "MFG"  # Manufacturing (General)
    FNB = "FNB"  # Food & Beverage
    ONG = "ONG"  # Oil & Gas
    MNM = "MNM"  # Mining & Minerals
    UTL = "UTL"  # Utilities
    PHA = "PHA"  # Pharmaceuticals


class EvidenceStatus(str, enum.Enum):
    """Evidence verification lifecycle"""
    NOT_REQUIRED = "not_required"
    PENDING_EVIDENCE = "pending_evidence"
    PENDING_VERIFICATION = "pending_verification"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TargetRoleV2(str, enum.Enum):
    """vNext respondent roles (AUDITOR replaced by RELIABILITY_ENGINEER)"""
    TECHNICIAN = "TECHNICIAN"
    SUPERVISOR = "SUPERVISOR"
    MANAGER = "MANAGER"
    PLANNER = "PLANNER"
    RELIABILITY_ENGINEER = "RELIABILITY_ENGINEER"


class CertificationLevel(str, enum.Enum):
    """Auditor certification tiers"""
    ASSOCIATE = "ASSOCIATE"
    LEAD = "LEAD"
    SENIOR = "SENIOR"
    MASTER = "MASTER"


# ===================== vNext MODELS =====================

class Domain(Base):
    """RMI vNext domain definitions"""
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(2), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    default_weight = Column(Float, default=0.20)
    display_order = Column(Integer, nullable=False)

    subdomains = relationship("Subdomain", back_populates="domain", order_by="Subdomain.display_order")


class Subdomain(Base):
    """RMI vNext subdomain definitions (3 per domain)"""
    __tablename__ = "subdomains"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    code = Column(String(4), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    display_order = Column(Integer, nullable=False)

    domain = relationship("Domain", back_populates="subdomains")
    questions = relationship("QuestionV2", back_populates="subdomain")
    scores = relationship("SubdomainScore", back_populates="subdomain")


class QuestionV2(Base):
    """
    vNext question bank — 150+ database-driven questions.
    Separate table from v1 QuestionBank to avoid migration conflicts.
    """
    __tablename__ = "question_bank_v2"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    question_code = Column(String(20), unique=True, nullable=False, index=True)
    question_text = Column(Text, nullable=False)

    # Taxonomy
    domain = Column(Enum(DomainType), nullable=False, index=True)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"), nullable=False)
    target_role = Column(Enum(TargetRoleV2), nullable=False)

    # Question type & options
    question_type = Column(String(20), nullable=False)  # LIKERT, BINARY, DATA_INPUT, etc.
    answer_options = Column(JSON, nullable=True)

    # Scoring
    weight = Column(Float, default=1.0)
    scoring_rubric = Column(JSON, nullable=False)  # {1: "...", 2: "...", ...5: "..."}
    min_score = Column(Integer, default=1)
    max_score = Column(Integer, default=5)

    # Assessment mode tags
    assessment_modes = Column(JSON, default=["standard", "deepdive"])
    # e.g. ["quickscan","standard","deepdive"]

    # Evidence
    evidence_required = Column(Boolean, default=False)
    evidence_guidance = Column(Text, nullable=True)

    # Calibration & Practice
    calibration_anchor = Column(Text, nullable=True)
    practice_link = Column(String(20), nullable=True)  # e.g. "WM.1-01-P"

    # ISO alignment
    iso_55001_clause = Column(String(20), nullable=True)

    # Critical / weakest-link
    is_critical = Column(Boolean, default=False)

    # Industry module specificity (NULL = universal core)
    industry_module = Column(Enum(IndustryModule), nullable=True)

    # Lifecycle
    version = Column(String(10), default="2.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subdomain = relationship("Subdomain", back_populates="questions")
    responses = relationship("ResponseV2", back_populates="question")


class AssessmentV2(Base):
    """
    vNext assessment — extends v1 with mode, industry module, and
    subdomain-level scoring. Separate table so v1 assessments are untouched.
    """
    __tablename__ = "assessments_v2"

    id = Column(Integer, primary_key=True, index=True)

    # Site metadata
    client_name = Column(String(255), nullable=False, index=True)
    site_name = Column(String(255), nullable=False)
    industry = Column(String(100))
    site_criticality = Column(Float, default=1.0)

    # vNext fields
    assessment_mode = Column(Enum(AssessmentMode), nullable=False, default=AssessmentMode.STANDARD)
    industry_module = Column(Enum(IndustryModule), nullable=True)
    framework_version = Column(String(20), default="2.0")

    # Lifecycle
    status = Column(String(20), default="DRAFT")
    assessment_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    finalized_at = Column(DateTime, nullable=True)

    # Scoring results (denormalized for fast reads)
    overall_rmi = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    maturity_level = Column(String(50), nullable=True)

    # Legacy link (if this is a re-assessment of a v1 site)
    legacy_assessment_id = Column(Integer, nullable=True)
    legacy_score = Column(JSON, nullable=True)  # Preserved v1 pillar scores

    # Relationships
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User")
    responses = relationship("ResponseV2", back_populates="assessment", cascade="all, delete-orphan")
    subdomain_scores = relationship("SubdomainScore", back_populates="assessment", cascade="all, delete-orphan")
    benchmark = relationship("BenchmarkMetadata", back_populates="assessment", uselist=False, cascade="all, delete-orphan")


class ResponseV2(Base):
    """vNext question responses with evidence status tracking"""
    __tablename__ = "responses_v2"

    id = Column(Integer, primary_key=True, index=True)

    assessment_id = Column(Integer, ForeignKey("assessments_v2.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question_bank_v2.id"), nullable=False)
    respondent_role = Column(Enum(TargetRoleV2), nullable=True)

    # Response data
    response_value = Column(String(500), nullable=True)
    numeric_score = Column(Float, nullable=True)

    # Evidence tracking (hard-reject, not silent cap)
    evidence_status = Column(
        Enum(EvidenceStatus),
        default=EvidenceStatus.NOT_REQUIRED
    )
    evidence_notes = Column(Text, nullable=True)
    evidence_grade = Column(String(1), nullable=True)  # A, B, C, D

    # Evidence file (uploaded by user; serialized StoredObject path)
    evidence_file_path = Column(String(500), nullable=True)
    evidence_filename = Column(String(255), nullable=True)
    evidence_mime = Column(String(120), nullable=True)
    evidence_size_bytes = Column(Integer, nullable=True)
    evidence_uploaded_at = Column(DateTime, nullable=True)

    # AI analysis of the uploaded evidence
    ai_suggested_score = Column(Float, nullable=True)
    ai_observations = Column(Text, nullable=True)
    ai_confidence = Column(String(10), nullable=True)  # HIGH / MEDIUM / LOW
    ai_analyzed_at = Column(DateTime, nullable=True)

    # Flags
    is_draft = Column(Boolean, default=False)
    is_na = Column(Boolean, default=False)

    # Metadata
    answered_at = Column(DateTime, default=datetime.utcnow)
    answered_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    assessment = relationship("AssessmentV2", back_populates="responses")
    question = relationship("QuestionV2", back_populates="responses")

    __table_args__ = (
        UniqueConstraint("assessment_id", "question_id", "respondent_role",
                         name="uq_response_v2"),
    )


class SubdomainScore(Base):
    """Subdomain-level scores (15 per assessment)"""
    __tablename__ = "subdomain_scores"

    id = Column(Integer, primary_key=True, index=True)

    assessment_id = Column(Integer, ForeignKey("assessments_v2.id"), nullable=False)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"), nullable=False)

    raw_score = Column(Float, nullable=True)
    weighted_score = Column(Float, nullable=True)
    evidence_adjusted_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)

    cap_applied = Column(Boolean, default=False)
    cap_reason = Column(Text, nullable=True)

    confidence = Column(Float, nullable=True)  # 0.0 - 1.0
    percentile = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assessment = relationship("AssessmentV2", back_populates="subdomain_scores")
    subdomain = relationship("Subdomain", back_populates="scores")

    __table_args__ = (
        UniqueConstraint("assessment_id", "subdomain_id",
                         name="uq_subdomain_score"),
    )


class BenchmarkMetadata(Base):
    """Peer-group metadata for benchmarking"""
    __tablename__ = "benchmark_metadata"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments_v2.id"), unique=True, nullable=False)

    industry_code = Column(String(3), nullable=True)
    site_size_category = Column(String(10), nullable=True)   # SMALL, MEDIUM, LARGE
    region = Column(String(30), nullable=True)
    asset_intensity = Column(String(10), nullable=True)      # LIGHT, MEDIUM, HEAVY
    maintenance_fte = Column(Integer, nullable=True)
    is_benchmark_eligible = Column(Boolean, default=True)

    # Cached results
    overall_percentile = Column(Integer, nullable=True)
    peer_count = Column(Integer, nullable=True)
    domain_percentiles = Column(JSON, nullable=True)
    calculated_at = Column(DateTime, nullable=True)

    assessment = relationship("AssessmentV2", back_populates="benchmark")


class Practice(Base):
    """Prescriptive practice library entries"""
    __tablename__ = "practices"

    id = Column(Integer, primary_key=True, index=True)
    practice_id = Column(String(20), unique=True, nullable=False, index=True)
    practice_code = Column(String(20), nullable=True, index=True)

    subdomain_id = Column(Integer, ForeignKey("subdomains.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    pathways = Column(JSON, nullable=True)          # {1_to_2: {...}, 2_to_3: {...}, ...}
    references = Column(JSON, nullable=True)
    industry_variations = Column(JSON, nullable=True)
    tools = Column(JSON, nullable=True)             # linked downloadable files

    # Maturity transition
    from_level = Column(Integer, nullable=True)     # Current maturity level
    to_level = Column(Integer, nullable=True)       # Target maturity level
    priority_rank = Column(Integer, default=1)

    # Effort / Impact
    impact_rating = Column(String(10), default="medium")   # low, medium, high
    effort_rating = Column(String(10), default="medium")
    timeline = Column(String(30), nullable=True)           # e.g. "3-6 months"

    # Additional metadata
    success_metrics = Column(JSON, nullable=True)
    resources = Column(JSON, nullable=True)
    iso_55001_clause = Column(String(20), nullable=True)
    is_critical_path = Column(Boolean, default=False)

    version = Column(String(10), default="2.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    subdomain = relationship("Subdomain")


class CalibrationExercise(Base):
    """Auditor calibration exercise results"""
    __tablename__ = "calibration_exercises"

    id = Column(Integer, primary_key=True, index=True)

    auditor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_type = Column(String(20), nullable=False)      # QUICK_CHECK, STANDARD, FULL, INDUSTRY
    case_study_id = Column(String(20), nullable=True)

    irr_score = Column(Float, nullable=True)                # Cohen's weighted kappa
    deviation_details = Column(JSON, nullable=True)
    bias_pattern = Column(String(50), nullable=True)        # leniency, severity, halo, etc.

    passed = Column(Boolean, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)

    auditor = relationship("User")


class CMSSUploadKind(str, enum.Enum):
    """CMMS snapshot kinds the analyzer understands."""
    WORK_ORDERS = "work_orders"
    PM = "pm"


class CMMSUploadV2(Base):
    """
    A CMMS data snapshot attached to a vNext assessment.

    The analyzer in data_analysis_module.py parses the file, computes reactive
    ratio / PM compliance / data-graveyard metrics, and stores them in
    `metrics` JSON. Scoring engine reads these to boost or cap relevant
    subdomains (AI.1, WM.2).
    """
    __tablename__ = "cmms_uploads_v2"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments_v2.id", ondelete="CASCADE"), nullable=False, index=True)

    kind = Column(String(20), nullable=False)  # work_orders | pm
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    status = Column(String(20), nullable=False, default="processed")  # processed | error
    error_message = Column(Text, nullable=True)

    metrics = Column(JSON, nullable=True)
    bad_actors = Column(JSON, nullable=True)
    record_count = Column(Integer, nullable=True)

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
