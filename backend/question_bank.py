"""
Professional Question Bank - Pre-loaded Questions
Enterprise-grade RMI assessment questions with full metadata
"""
from models import QuestionBank, PillarType, QuestionType, TargetRole
from sqlalchemy.orm import Session


def seed_question_bank(db: Session):
    """
    Load the professional question bank into the database
    This is the core content that makes the audit defensible
    """
    
    questions = [
        # ==================== PEOPLE PILLAR ====================
        {
            "question_code": "P-01",
            "question_text": "Do you feel trained on the specific equipment you are assigned to maintain today?",
            "pillar": PillarType.PEOPLE,
            "subcategory": "Competency",
            "target_role": TargetRole.TECHNICIAN,
            "question_type": QuestionType.LIKERT,
            "weight": 1.5,  # High weight - critical question
            "evidence_required": True,
            "evidence_description": "If score >3: Training certificate, competency matrix, or formal documentation",
            "scoring_logic": {
                "1": "I learn by guessing / No formal training",
                "2": "Some on-the-job training but inconsistent",
                "3": "Basic training provided",
                "4": "Comprehensive training with documentation",
                "5": "Formal certification program with ongoing skill validation"
            },
            "is_critical": True,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "P-02",
            "question_text": "In a typical week, how many times is your scheduled work interrupted by an emergency?",
            "pillar": PillarType.PEOPLE,
            "subcategory": "Reactive Reality",
            "target_role": TargetRole.TECHNICIAN,
            "question_type": QuestionType.LIKERT,
            "weight": 1.2,
            "evidence_required": False,
            "evidence_description": None,
            "scoring_logic": {
                "1": "Daily / Constant interruptions (5+ per week)",
                "2": "Frequent interruptions (3-4 per week)",
                "3": "Occasional interruptions (1-2 per week)",
                "4": "Rare interruptions (1-2 per month)",
                "5": "Almost never / Scheduled work is protected"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "P-03",
            "question_text": "If you see a safety or reliability risk, do you feel authorized to stop production?",
            "pillar": PillarType.PEOPLE,
            "subcategory": "Empowerment",
            "target_role": TargetRole.TECHNICIAN,
            "question_type": QuestionType.BINARY,
            "weight": 1.0,
            "evidence_required": False,
            "evidence_description": None,
            "scoring_logic": {
                "Yes": "5 points - Empowered workforce",
                "No": "1 point - Authority gap / Cultural issue"
            },
            "is_critical": True,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "P-04",
            "question_text": "How is knowledge transferred from senior technicians to new hires?",
            "pillar": PillarType.PEOPLE,
            "subcategory": "Knowledge Management",
            "target_role": TargetRole.MANAGER,
            "question_type": QuestionType.MULTI_SELECT,
            "weight": 1.0,
            "evidence_required": True,
            "evidence_description": "Documentation of mentorship program, knowledge base screenshots, or training records",
            "answer_options": [
                "Ad-hoc shadowing only",
                "Informal mentorship",
                "Documented training program",
                "Knowledge base / Wiki",
                "Formal certification path",
                "Cross-training rotations"
            ],
            "scoring_logic": {
                "1": "Only ad-hoc shadowing",
                "3": "Informal mentorship + some documentation",
                "5": "Formal program + knowledge base + certification"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "P-05",
            "question_text": "Does the maintenance budget include a dedicated line item for technician training?",
            "pillar": PillarType.PEOPLE,
            "subcategory": "Investment in Competency",
            "target_role": TargetRole.MANAGER,
            "question_type": QuestionType.BINARY,
            "weight": 0.8,
            "evidence_required": True,
            "evidence_description": "Budget spreadsheet showing training allocation",
            "scoring_logic": {
                "Yes": "5 points - Training is funded priority",
                "No": "1 point - Training not formalized in budget"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        },
        
        # ==================== PROCESS PILLAR ====================
        {
            "question_code": "PR-01",
            "question_text": "Did the technician have the correct spare part available immediately?",
            "pillar": PillarType.PROCESS,
            "subcategory": "Work Execution",
            "target_role": TargetRole.AUDITOR,
            "question_type": QuestionType.OBSERVATIONAL,
            "weight": 1.3,
            "evidence_required": True,
            "evidence_description": "Photo of part available at job site OR note documenting delay/search time",
            "scoring_logic": {
                "1": "Technician had to leave area to find/order part (delay >30 min)",
                "2": "Part available in storeroom but not kitted",
                "3": "Part kitted but not at job site",
                "4": "Part at job site but some confusion",
                "5": "Kitting process had exact part ready at job site"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "PR-02",
            "question_text": "Did the technician reference a Standard Operating Procedure (SOP) during the repair?",
            "pillar": PillarType.PROCESS,
            "subcategory": "SOP Usage",
            "target_role": TargetRole.AUDITOR,
            "question_type": QuestionType.OBSERVATIONAL,
            "weight": 1.2,
            "evidence_required": True,
            "evidence_description": "Photo of SOP in use OR note explaining why SOP was not referenced",
            "scoring_logic": {
                "1": "No SOP visible / Technician unaware of SOP",
                "2": "SOP exists but not accessible at job site",
                "3": "SOP referenced briefly",
                "4": "SOP used for most steps",
                "5": "SOP followed step-by-step with sign-off"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "PR-03",
            "question_text": "Was the Lock-Out/Tag-Out (LOTO) procedure correctly applied before work started?",
            "pillar": PillarType.PROCESS,
            "subcategory": "Safety Compliance",
            "target_role": TargetRole.AUDITOR,
            "question_type": QuestionType.BINARY,
            "weight": 2.0,  # Critical safety item
            "evidence_required": True,
            "evidence_description": "Photo of LOTO application or safety permit",
            "scoring_logic": {
                "Pass": "5 points - Safety protocol followed",
                "Fail": "CRITICAL FAIL - Automatic pillar cap at 3.0"
            },
            "is_critical": True,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "PR-04",
            "question_text": "What percentage of Work Orders have a detailed Job Plan attached?",
            "pillar": PillarType.PROCESS,
            "subcategory": "Planning Quality",
            "target_role": TargetRole.PLANNER,
            "question_type": QuestionType.DATA_INPUT,
            "weight": 1.4,
            "evidence_required": True,
            "evidence_description": "CMMS report showing % of WOs with job plans, or sample of 20 WOs",
            "scoring_logic": {
                "1": "<10% of WOs have plans (just headers)",
                "2": "10-30% have basic plans",
                "3": "30-60% have plans",
                "4": "60-90% have detailed plans",
                "5": ">90% have comprehensive job plans with steps/parts/safety"
            },
            "is_critical": True,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "PR-05",
            "question_text": "Are Preventive Maintenance (PM) tasks completed within their scheduled window?",
            "pillar": PillarType.PROCESS,
            "subcategory": "PM Discipline",
            "target_role": TargetRole.PLANNER,
            "question_type": QuestionType.DATA_INPUT,
            "weight": 1.3,
            "evidence_required": True,
            "evidence_description": "CMMS PM compliance report showing on-time completion %",
            "scoring_logic": {
                "1": "<50% PMs completed on time",
                "2": "50-70% on time",
                "3": "70-85% on time",
                "4": "85-95% on time",
                "5": ">95% on time with documented reasons for exceptions"
            },
            "is_critical": True,
            "min_score": 1,
            "max_score": 5
        },
        
        # ==================== TECHNOLOGY PILLAR ====================
        {
            "question_code": "T-01",
            "question_text": "Random Sampling: Pull 50 closed work orders. How many have generic closure codes like 'DONE' or 'FIXED'?",
            "pillar": PillarType.TECHNOLOGY,
            "subcategory": "Data Graveyard Detection",
            "target_role": TargetRole.AUDITOR,
            "question_type": QuestionType.DATA_INPUT,
            "weight": 1.5,
            "evidence_required": True,
            "evidence_description": "Screenshot of CMMS export showing closure codes or Excel analysis",
            "scoring_logic": {
                "1": ">20 WOs (>40%) have generic codes - SEVERE DATA GRAVEYARD",
                "2": "10-20 WOs (20-40%) generic codes",
                "3": "5-10 WOs (10-20%) generic codes",
                "4": "2-5 WOs (4-10%) generic codes",
                "5": "<2 WOs (<4%) generic codes - High data quality"
            },
            "is_critical": True,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "T-02",
            "question_text": "Do failure codes align with ISO 14224 taxonomy (Component - Failure Mode - Cause)?",
            "pillar": PillarType.TECHNOLOGY,
            "subcategory": "ISO 14224 Compliance",
            "target_role": TargetRole.AUDITOR,
            "question_type": QuestionType.BINARY,
            "weight": 1.2,
            "evidence_required": True,
            "evidence_description": "Screenshot of failure code structure in CMMS or data export",
            "scoring_logic": {
                "Yes": "5 points - Structured, analyzable data",
                "No": "1 point - Unstructured data / Cannot perform RCA"
            },
            "is_critical": True,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "T-03",
            "question_text": "Can you generate a 'Bad Actor' report (Top 10 failing assets) in under 5 minutes?",
            "pillar": PillarType.TECHNOLOGY,
            "subcategory": "Reporting Capability",
            "target_role": TargetRole.MANAGER,
            "question_type": QuestionType.OBSERVATIONAL,
            "weight": 1.0,
            "evidence_required": True,
            "evidence_description": "Screenshot of report OR timer evidence showing time to generate",
            "scoring_logic": {
                "1": "No - Must export to Excel and manually analyze",
                "2": "Requires custom SQL or IT support",
                "3": "Possible but requires 15-30 minutes",
                "4": "Can generate in 5-10 minutes",
                "5": "Yes - One-click dashboard available"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "T-04",
            "question_text": "Rate the difficulty of entering data into the current CMMS.",
            "pillar": PillarType.TECHNOLOGY,
            "subcategory": "System Usability",
            "target_role": TargetRole.TECHNICIAN,
            "question_type": QuestionType.LIKERT,
            "weight": 0.8,
            "evidence_required": False,
            "evidence_description": None,
            "scoring_logic": {
                "1": "Extremely frustrating / I avoid it when possible",
                "2": "Difficult - Too many fields/steps",
                "3": "Acceptable - Some friction",
                "4": "Easy - Straightforward process",
                "5": "Seamless - Mobile-friendly, intuitive"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "T-05",
            "question_text": "What is the asset hierarchy depth in the CMMS?",
            "pillar": PillarType.TECHNOLOGY,
            "subcategory": "Data Structure",
            "target_role": TargetRole.AUDITOR,
            "question_type": QuestionType.DATA_INPUT,
            "weight": 1.0,
            "evidence_required": True,
            "evidence_description": "Screenshot of asset hierarchy or CMMS structure export",
            "scoring_logic": {
                "1": "Flat structure (1-2 levels) - No functional hierarchy",
                "2": "Basic structure (3 levels) - Site > Area > Equipment",
                "3": "Good structure (4 levels) - Site > Area > System > Equipment",
                "4": "Comprehensive (5 levels) - Includes components",
                "5": "ISO 14224 compliant (5+ levels) - Down to failure mode level"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        },
        {
            "question_code": "T-06",
            "question_text": "Are work order attachments (photos, manuals) easily accessible from the CMMS?",
            "pillar": PillarType.TECHNOLOGY,
            "subcategory": "Information Access",
            "target_role": TargetRole.TECHNICIAN,
            "question_type": QuestionType.LIKERT,
            "weight": 0.9,
            "evidence_required": False,
            "evidence_description": None,
            "scoring_logic": {
                "1": "No attachment capability or never used",
                "2": "Possible but cumbersome",
                "3": "Available but not consistently used",
                "4": "Easy to access, commonly used",
                "5": "Integrated with mobile access, widely adopted"
            },
            "is_critical": False,
            "min_score": 1,
            "max_score": 5
        }
    ]
    
    # Add questions to database
    for q_data in questions:
        question = QuestionBank(**q_data)
        db.add(question)
    
    db.commit()
    print(f"✅ Seeded {len(questions)} professional questions into the database")
    return len(questions)


def get_questions_by_pillar(db: Session, pillar: PillarType):
    """Retrieve all questions for a specific pillar"""
    return db.query(QuestionBank).filter(
        QuestionBank.pillar == pillar,
        QuestionBank.is_active == True
    ).all()


def get_questions_by_role(db: Session, role: TargetRole):
    """Retrieve all questions for a specific role"""
    return db.query(QuestionBank).filter(
        QuestionBank.target_role == role,
        QuestionBank.is_active == True
    ).all()


def get_critical_questions(db: Session):
    """Retrieve all critical questions that affect pillar caps"""
    return db.query(QuestionBank).filter(
        QuestionBank.is_critical == True,
        QuestionBank.is_active == True
    ).all()
