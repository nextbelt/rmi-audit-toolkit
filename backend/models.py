"""
SQLAlchemy models for RMI Audit Software
Enterprise-grade database schema for audit-grade assessments
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Table
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


# ==================== ENUMS ====================

class PillarType(str, enum.Enum):
    """Three pillars of RMI assessment"""
    PEOPLE = "people"
    PROCESS = "process"
    TECHNOLOGY = "technology"


class QuestionType(str, enum.Enum):
    """Types of assessment questions"""
    LIKERT = "likert"  # 1-5 scale
    BINARY = "binary"  # Yes/No
    MULTI_SELECT = "multi_select"
    DATA_INPUT = "data_input"  # Numeric or percentage
    OBSERVATIONAL = "observational"  # Field observation


class TargetRole(str, enum.Enum):
    """Who the question is directed at"""
    TECHNICIAN = "technician"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    PLANNER = "planner"
    AUDITOR = "auditor"  # For observations/data analysis


class AssessmentStatus(str, enum.Enum):
    """Lifecycle status of an audit"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class EvidenceType(str, enum.Enum):
    """Types of evidence that can be attached"""
    PHOTO = "photo"
    DOCUMENT = "document"
    SCREENSHOT = "screenshot"
    CMMS_EXPORT = "cmms_export"
    NOTE = "note"
    VIDEO = "video"


# ==================== MODELS ====================

class User(Base):
    """System users (auditors, admins, clients)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, auditor, client
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assessments_created = relationship("Assessment", back_populates="creator")


class Assessment(Base):
    """
    Core assessment instance - represents a single RMI audit engagement
    This is the "audit project" that ties everything together
    """
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metadata
    client_name = Column(String(255), nullable=False, index=True)
    site_name = Column(String(255), nullable=False)
    asset_class = Column(String(100))  # e.g., "Pumps", "HVAC", "Processing"
    industry = Column(String(100))  # e.g., "Manufacturing", "Oil & Gas"
    
    # Assessment Details
    assessment_date = Column(DateTime, nullable=False)
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.DRAFT)
    framework_version = Column(String(20), default="1.0")  # Version control
    
    # Relationships
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", back_populates="assessments_created")
    
    # Audit team (many-to-many)
    auditors = relationship("AssessmentAuditor", back_populates="assessment")
    
    # Child records
    responses = relationship("QuestionResponse", back_populates="assessment")
    observations = relationship("Observation", back_populates="assessment")
    data_analyses = relationship("DataAnalysis", back_populates="assessment")
    scores = relationship("Score", back_populates="assessment")
    reports = relationship("Report", back_populates="assessment")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class AssessmentAuditor(Base):
    """Many-to-many relationship for audit teams"""
    __tablename__ = "assessment_auditors"
    
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    auditor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_in_audit = Column(String(50))  # "Lead", "Technical", "Observer"
    
    assessment = relationship("Assessment", back_populates="auditors")
    auditor = relationship("User")


class QuestionBank(Base):
    """
    Master question repository - the professional question bank
    This is version-controlled and reusable across assessments
    """
    __tablename__ = "question_bank"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Question Identity
    question_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "P-01", "PR-03"
    question_text = Column(Text, nullable=False)
    
    # Categorization
    pillar = Column(Enum(PillarType), nullable=False, index=True)
    subcategory = Column(String(100), nullable=False)  # e.g., "Competency", "Planning"
    target_role = Column(Enum(TargetRole), nullable=False)
    
    # Question Configuration
    question_type = Column(Enum(QuestionType), nullable=False)
    answer_options = Column(JSON, nullable=True)  # For multi-select, stores options
    
    # Scoring & Weighting
    weight = Column(Float, default=1.0)  # Impact on pillar score
    evidence_required = Column(Boolean, default=False)
    evidence_description = Column(Text, nullable=True)  # What evidence validates this
    
    # Scoring Logic
    scoring_logic = Column(JSON, nullable=True)  # Stores rules like "1: X, 5: Y"
    min_score = Column(Integer, default=1)
    max_score = Column(Integer, default=5)
    
    # Metadata
    is_critical = Column(Boolean, default=False)  # Critical questions affect pillar caps
    framework_version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    responses = relationship("QuestionResponse", back_populates="question")


class QuestionResponse(Base):
    """
    Individual answers to questions during an assessment
    Links assessment + question + response + evidence
    """
    __tablename__ = "question_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Links
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question_bank.id"), nullable=False)
    respondent_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who answered
    
    # Response Data
    response_value = Column(String(500), nullable=True)  # Actual answer
    numeric_score = Column(Float, nullable=True)  # Calculated score
    
    # Evidence Lock
    evidence_provided = Column(Boolean, default=False)
    evidence_notes = Column(Text, nullable=True)
    
    # Metadata
    answered_at = Column(DateTime, default=datetime.utcnow)
    answered_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Auditor who recorded
    
    # Relationships
    assessment = relationship("Assessment", back_populates="responses")
    question = relationship("QuestionBank", back_populates="responses")
    respondent = relationship("User", foreign_keys=[respondent_id])
    evidence_files = relationship("Evidence", back_populates="response")


class Observation(Base):
    """
    Field observations during shadowing/job execution
    Real-time evidence capture module
    """
    __tablename__ = "observations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Links
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    
    # Observation Details
    observation_title = Column(String(255), nullable=False)
    observation_type = Column(String(100))  # e.g., "Work Execution", "Safety"
    pillar = Column(Enum(PillarType), nullable=False)
    subcategory = Column(String(100))
    
    # Findings
    observation_notes = Column(Text, nullable=False)
    pass_fail_result = Column(Boolean, nullable=True)
    severity = Column(String(50), nullable=True)  # "Critical", "Major", "Minor"
    
    # Context
    observed_role = Column(String(100))  # Who was being observed
    location = Column(String(255))  # Where in facility
    observed_at = Column(DateTime, nullable=False)
    observer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="observations")
    observer = relationship("User")
    evidence_files = relationship("Evidence", back_populates="observation")


class DataAnalysis(Base):
    """
    CMMS data analysis results - the "Data Cruncher"
    Stores calculated metrics from uploaded CMMS exports
    """
    __tablename__ = "data_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Links
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    
    # Analysis Type
    analysis_type = Column(String(100), nullable=False)  # e.g., "Reactive Ratio", "PM Compliance"
    data_source = Column(String(255))  # File name or system
    
    # Calculated Metrics (stored as JSON for flexibility)
    metrics = Column(JSON, nullable=False)
    # Example: {"reactive_ratio": 0.67, "total_wos": 450, "emergency_wos": 302}
    
    # Sample Details
    sample_size = Column(Integer, nullable=True)
    sample_method = Column(String(100), nullable=True)  # "Random 50 WOs", "All 2024 Data"
    
    # Results
    pass_threshold = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    analyzed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="data_analyses")
    analyzer = relationship("User")
    evidence_files = relationship("Evidence", back_populates="data_analysis")


class Evidence(Base):
    """
    Evidence files and attachments
    Photos, documents, screenshots that validate scores
    """
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What is this evidence for?
    response_id = Column(Integer, ForeignKey("question_responses.id"), nullable=True)
    observation_id = Column(Integer, ForeignKey("observations.id"), nullable=True)
    data_analysis_id = Column(Integer, ForeignKey("data_analyses.id"), nullable=True)
    
    # Evidence Details
    evidence_type = Column(Enum(EvidenceType), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    response = relationship("QuestionResponse", back_populates="evidence_files")
    observation = relationship("Observation", back_populates="evidence_files")
    data_analysis = relationship("DataAnalysis", back_populates="evidence_files")
    uploader = relationship("User")


class Score(Base):
    """
    Calculated RMI scores - the output of the scoring engine
    Stores pillar scores, subcategory scores, and final RMI
    """
    __tablename__ = "scores"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Links
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    
    # Score Breakdown
    pillar = Column(Enum(PillarType), nullable=True)  # NULL for overall RMI
    subcategory = Column(String(100), nullable=True)
    
    # Score Values
    raw_score = Column(Float, nullable=False)  # Before weighting/caps
    weighted_score = Column(Float, nullable=False)  # After weighting
    final_score = Column(Float, nullable=False)  # After weakest-link caps
    
    # Scoring Details
    max_possible_score = Column(Float, default=5.0)
    confidence_level = Column(String(50))  # "High", "Medium", "Low" based on evidence
    
    # Calculation Metadata
    calculation_method = Column(Text, nullable=True)  # JSON of how it was calculated
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="scores")


class Report(Base):
    """
    Generated reports and exports
    Executive summaries, roadmaps, PDF exports
    """
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Links
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    
    # Report Details
    report_type = Column(String(100), nullable=False)  # "Executive Summary", "Technical Detail", "Roadmap"
    title = Column(String(255), nullable=False)
    
    # Content
    content = Column(JSON, nullable=True)  # Structured report data
    file_path = Column(String(500), nullable=True)  # Path to PDF/PPT
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="reports")
    generator = relationship("User")


class ISO14224Audit(Base):
    """
    ISO 14224 compliance checklist results
    Data integrity audit findings
    """
    __tablename__ = "iso14224_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Links
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    
    # Checklist Items
    check_item = Column(String(255), nullable=False)
    check_category = Column(String(100))  # "Hierarchy", "Failure Modes", "Taxonomy"
    
    # Results
    passed = Column(Boolean, nullable=False)
    evidence_notes = Column(Text)
    impact_on_score = Column(Float, default=0.0)
    
    # Metadata
    audited_at = Column(DateTime, default=datetime.utcnow)
    audited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    assessment = relationship("Assessment")
    auditor = relationship("User")
