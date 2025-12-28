"""
FastAPI Application - REST API Layer
Enterprise-grade API with authentication and comprehensive endpoints
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os

from database import get_db, init_db
from models import (
    User, Assessment, QuestionBank, QuestionResponse,
    Observation, DataAnalysis, Score, Report,
    PillarType, QuestionType, TargetRole, AssessmentStatus
)
from scoring_engine import ScoringEngine
from observation_module import ObservationManager
from data_analysis_module import CMMSDataAnalyzer
from iso14224_module import ISO14224Validator
from config import settings

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Enterprise-grade Reliability Maturity Index (RMI) Audit Platform"
)

# CORS middleware for web frontend (supports local development on port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://rmi-audit-toolkit-frontend-production.up.railway.app",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for evidence uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ==================== PYDANTIC SCHEMAS ====================

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


class Token(BaseModel):
    access_token: str
    token_type: str


class AssessmentCreate(BaseModel):
    client_name: str
    site_name: str
    asset_class: Optional[str] = None
    industry: Optional[str] = None
    assessment_date: datetime


class AssessmentResponse(BaseModel):
    id: int
    client_name: str
    site_name: str
    status: AssessmentStatus
    assessment_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuestionResponseCreate(BaseModel):
    question_id: int
    response_value: str
    respondent_id: Optional[int] = None
    evidence_notes: Optional[str] = None


class ObservationCreate(BaseModel):
    title: str
    type: str
    pillar: str
    subcategory: Optional[str] = None
    notes: str
    pass_fail: Optional[bool] = None
    severity: Optional[str] = None
    observed_role: Optional[str] = None
    location: Optional[str] = None


class QuestionCreate(BaseModel):
    code: str
    pillar: PillarType
    question_type: QuestionType
    question_text: str
    target_role: TargetRole


# ==================== AUTHENTICATION ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


# ==================== API ENDPOINTS ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
async def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational"
    }


@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current logged-in user"""
    return current_user


# ==================== ASSESSMENT ENDPOINTS ====================

@app.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(
    assessment: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new RMI assessment"""
    db_assessment = Assessment(
        **assessment.dict(),
        creator_id=current_user.id,
        status=AssessmentStatus.DRAFT
    )
    
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    
    return db_assessment


@app.get("/assessments", response_model=List[AssessmentResponse])
async def list_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all assessments"""
    assessments = db.query(Assessment).all()
    return assessments


@app.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific assessment details"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    return assessment


@app.put("/assessments/{assessment_id}/status")
async def update_assessment_status(
    assessment_id: int,
    status: AssessmentStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update assessment status"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    assessment.status = status
    if status == AssessmentStatus.COMPLETED:
        assessment.completed_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Status updated", "new_status": status}


# ==================== QUESTION BANK ENDPOINTS ====================

@app.get("/questions")
async def list_questions(
    pillar: Optional[PillarType] = None,
    target_role: Optional[TargetRole] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List questions, optionally filtered by pillar or role"""
    query = db.query(QuestionBank).filter(QuestionBank.is_active == True)
    
    if pillar:
        query = query.filter(QuestionBank.pillar == pillar)
    if target_role:
        query = query.filter(QuestionBank.target_role == target_role)
    
    questions = query.all()
    return questions


@app.post("/questions")
async def create_question(
    question: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new question in the question bank"""
    db_question = QuestionBank(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@app.get("/questions/critical")
async def list_critical_questions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all critical questions"""
    questions = db.query(QuestionBank).filter(
        QuestionBank.is_critical == True,
        QuestionBank.is_active == True
    ).all()
    return questions


@app.post("/questions")
async def create_question(
    question: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new question (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_question = QuestionBank(
        code=question.code,
        pillar=question.pillar,
        question_type=question.question_type,
        question_text=question.question_text,
        target_role=question.target_role,
        is_active=True,
        is_critical=False
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


# ==================== QUESTION RESPONSE ENDPOINTS ====================

@app.post("/assessments/{assessment_id}/responses")
async def submit_response(
    assessment_id: int,
    response: QuestionResponseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a question response"""
    # Verify assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Get question to determine scoring
    question = db.query(QuestionBank).filter(QuestionBank.id == response.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Calculate numeric score based on response
    numeric_score = None
    if question.question_type == QuestionType.LIKERT:
        numeric_score = float(response.response_value)
    elif question.question_type == QuestionType.BINARY:
        numeric_score = 5.0 if response.response_value.lower() == 'yes' else 1.0
    
    # Create response
    db_response = QuestionResponse(
        assessment_id=assessment_id,
        question_id=response.question_id,
        respondent_id=response.respondent_id,
        response_value=response.response_value,
        numeric_score=numeric_score,
        evidence_provided=bool(response.evidence_notes),
        evidence_notes=response.evidence_notes,
        answered_by=current_user.id
    )
    
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    return db_response


@app.get("/assessments/{assessment_id}/responses")
async def list_responses(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all responses for an assessment"""
    responses = db.query(QuestionResponse).filter(
        QuestionResponse.assessment_id == assessment_id
    ).all()
    return responses


# ==================== OBSERVATION ENDPOINTS ====================

@app.post("/assessments/{assessment_id}/observations")
async def create_observation(
    assessment_id: int,
    observation: ObservationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a field observation"""
    obs_manager = ObservationManager(db)
    
    obs_data = observation.dict()
    obs_data['observed_at'] = datetime.utcnow()
    
    db_observation = obs_manager.create_observation(
        assessment_id=assessment_id,
        observer_id=current_user.id,
        observation_data=obs_data
    )
    
    return db_observation


@app.post("/assessments/{assessment_id}/observations/batch")
async def create_batch_observations(
    assessment_id: int,
    observations: List[ObservationCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple field observations at once (for checklists)"""
    obs_manager = ObservationManager(db)
    results = []
    
    for obs in observations:
        obs_data = obs.dict()
        obs_data['observed_at'] = datetime.utcnow()
        
        created = obs_manager.create_observation(
            assessment_id=assessment_id,
            observer_id=current_user.id,
            observation_data=obs_data
        )
        results.append(created)
    
    return {"created_count": len(results), "observations": results}
    
    db_observation = obs_manager.create_observation(
        assessment_id=assessment_id,
        observer_id=current_user.id,
        observation_data=obs_data
    )
    
    return db_observation


@app.get("/assessments/{assessment_id}/observations")
async def list_observations(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all observations for an assessment"""
    obs_manager = ObservationManager(db)
    observations = obs_manager.get_observations_by_assessment(assessment_id)
    return observations


# ==================== SCORING ENDPOINTS ====================

@app.post("/assessments/{assessment_id}/calculate-scores")
async def calculate_scores(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate RMI scores for an assessment"""
    scoring_engine = ScoringEngine(db)
    
    try:
        scores = scoring_engine.calculate_assessment_scores(assessment_id)
        return scores
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/assessments/{assessment_id}/scores")
async def get_scores(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get calculated scores for an assessment"""
    scores = db.query(Score).filter(Score.assessment_id == assessment_id).all()
    return scores


@app.get("/assessments/{assessment_id}/score-breakdown")
async def get_score_breakdown(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed score breakdown by pillar and subcategory"""
    scoring_engine = ScoringEngine(db)
    breakdown = scoring_engine.get_score_breakdown(assessment_id)
    return breakdown


# ==================== DATA ANALYSIS ENDPOINTS ====================

@app.post("/assessments/{assessment_id}/analyze-work-orders")
async def analyze_work_orders(
    assessment_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and analyze CMMS work order data"""
    # Save uploaded file
    file_path = f"./uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Analyze
    analyzer = CMMSDataAnalyzer(db)
    results = analyzer.analyze_work_orders(
        assessment_id=assessment_id,
        analyzer_id=current_user.id,
        file_path=file_path
    )
    
    return results


@app.post("/assessments/{assessment_id}/analyze-pm-compliance")
async def analyze_pm_compliance(
    assessment_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and analyze PM compliance data"""
    file_path = f"./uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    analyzer = CMMSDataAnalyzer(db)
    results = analyzer.analyze_pm_compliance(
        assessment_id=assessment_id,
        analyzer_id=current_user.id,
        file_path=file_path
    )
    
    return results


# ==================== ISO 14224 ENDPOINTS ====================

@app.post("/assessments/{assessment_id}/iso14224/validate-hierarchy")
async def validate_iso14224_hierarchy(
    assessment_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate asset hierarchy against ISO 14224"""
    import pandas as pd
    
    file_path = f"./uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Read hierarchy data
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    
    validator = ISO14224Validator(db)
    results = validator.validate_asset_hierarchy(
        assessment_id=assessment_id,
        auditor_id=current_user.id,
        hierarchy_data=df
    )
    
    return results


@app.get("/assessments/{assessment_id}/iso14224/summary")
async def get_iso14224_summary(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ISO 14224 audit summary"""
    validator = ISO14224Validator(db)
    summary = validator.get_audit_summary(assessment_id)
    return summary


# ==================== REPORT ENDPOINTS ====================

@app.post("/assessments/{assessment_id}/generate-report")
async def generate_report(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate executive PDF report"""
    from report_generator import ReportGenerator
    
    generator = ReportGenerator(db, output_dir=settings.REPORT_OUTPUT_DIR)
    
    try:
        pdf_path = generator.generate_executive_report(
            assessment_id=assessment_id,
            generated_by=current_user.id
        )
        
        return {
            "message": "Report generated successfully",
            "file_path": pdf_path,
            "download_url": f"/assessments/{assessment_id}/report/download"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/assessments/{assessment_id}/report/download")
async def download_report(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the latest generated report as PDF"""
    # Find the latest report for this assessment
    report = db.query(Report).filter(
        Report.assessment_id == assessment_id
    ).order_by(Report.generated_at.desc()).first()
    
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report not found. Generate a report first.")
    
    return FileResponse(
        path=report.file_path,
        filename=os.path.basename(report.file_path),
        media_type='application/pdf'
    )


# ==================== USER MANAGEMENT ENDPOINTS ====================

@app.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db.query(User).all()
    return users


@app.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    updates: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update allowed fields
    if "is_active" in updates:
        user.is_active = updates["is_active"]
    if "role" in updates:
        user.role = updates["role"]
    if "full_name" in updates:
        user.full_name = updates["full_name"]
    
    db.commit()
    db.refresh(user)
    
    return {"message": "User updated successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
