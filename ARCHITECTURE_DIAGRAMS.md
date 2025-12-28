# RMI Audit Software - System Architecture Diagrams

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT INTERFACE                         │
│  (Web App / Mobile App / API Client - TO BE BUILT)          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       │ JWT Authentication
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI REST API                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth Routes  │  │Assessment API│  │ Scoring API  │      │
│  │ /register    │  │ /assessments │  │ /calculate   │      │
│  │ /token       │  │ /responses   │  │ /scores      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Observation   │  │ Data Analysis│  │ ISO 14224    │      │
│  │ API          │  │ API          │  │ API          │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │  ScoringEngine                                      │     │
│  │  • Role-weighted scoring (60/20/20)                │     │
│  │  • Evidence lock enforcement                       │     │
│  │  • Weakest link caps                               │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  CMMSDataAnalyzer                                   │     │
│  │  • Reactive ratio calculation                      │     │
│  │  • PM compliance analysis                          │     │
│  │  • Data graveyard detection                        │     │
│  │  • Bad actor identification                        │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  ISO14224Validator                                  │     │
│  │  • Hierarchy depth validation                      │     │
│  │  • Taxonomy alignment checks                       │     │
│  │  • Data completeness audits                        │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  ReportGenerator                                    │     │
│  │  • Executive summary PDF                           │     │
│  │  • Radar charts                                    │     │
│  │  • 30/60/90 roadmap                                │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQLAlchemy ORM
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ assessments  │  │question_bank │  │   scores     │      │
│  │              │  │              │  │              │      │
│  │ • client     │  │ • questions  │  │ • pillars    │      │
│  │ • site       │  │ • metadata   │  │ • RMI        │      │
│  │ • status     │  │ • weights    │  │ • confidence │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  responses   │  │ observations │  │  evidence    │      │
│  │              │  │              │  │              │      │
│  │ • answers    │  │ • field obs  │  │ • photos     │      │
│  │ • evidence   │  │ • checklists │  │ • docs       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │data_analyses │  │iso14224_audits│ │   reports    │      │
│  │              │  │              │  │              │      │
│  │ • metrics    │  │ • validation │  │ • PDFs       │      │
│  │ • CMMS data  │  │ • compliance │  │ • metadata   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  PostgreSQL / SQLite                                         │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Audit Workflow Diagram

```
START
  │
  ├─► 1. CREATE ASSESSMENT
  │   ├─ Client: ACME Manufacturing
  │   ├─ Site: Plant 4
  │   ├─ Industry: Food & Beverage
  │   └─ Date: 2025-12-27
  │
  ├─► 2. CONDUCT INTERVIEWS
  │   ├─ Interview Technicians (60% weight)
  │   │  └─ P-01: Training? → Score 4 + Evidence
  │   ├─ Interview Managers (20% weight)
  │   │  └─ P-05: Budget? → Score 2 + Evidence
  │   └─ Store in: question_responses table
  │
  ├─► 3. FIELD OBSERVATIONS
  │   ├─ Shadow technician on PM task
  │   │  └─ PR-01: Parts ready? → NO (Score 2)
  │   │  └─ PR-02: Used SOP? → NO (Score 1)
  │   │  └─ PR-03: LOTO applied? → YES (Score 5)
  │   ├─ Capture photos as evidence
  │   └─ Store in: observations + evidence tables
  │
  ├─► 4. ANALYZE CMMS DATA
  │   ├─ Upload work_orders.csv
  │   ├─ Calculate:
  │   │  ├─ Reactive Ratio: 67% → Score 1 (CRITICAL)
  │   │  ├─ PM Compliance: 58% → Score 2
  │   │  └─ Data Quality: 43% bad codes → Score 1
  │   └─ Store in: data_analyses table
  │
  ├─► 5. ISO 14224 VALIDATION
  │   ├─ Upload asset_hierarchy.xlsx
  │   ├─ Check:
  │   │  ├─ Hierarchy depth: 3 levels → FAIL
  │   │  └─ Taxonomy: No Component-Mode-Cause → FAIL
  │   └─ Store in: iso14224_audits table
  │
  ├─► 6. CALCULATE SCORES
  │   ├─ Run ScoringEngine.calculate_assessment_scores()
  │   ├─ Apply:
  │   │  ├─ Role weights (60/20/20)
  │   │  ├─ Evidence locks (cap high scores without proof)
  │   │  └─ Weakest link (critical failures cap pillars)
  │   ├─ Results:
  │   │  ├─ People: 2.8 / 5.0
  │   │  ├─ Process: 2.1 / 5.0 (capped by PR-03)
  │   │  ├─ Technology: 2.3 / 5.0 (capped by T-01)
  │   │  └─ Overall RMI: 2.4 → "Emerging Preventive"
  │   └─ Store in: scores table
  │
  ├─► 7. GENERATE REPORT
  │   ├─ ReportGenerator.generate_executive_report()
  │   ├─ Include:
  │   │  ├─ Executive summary
  │   │  ├─ Pillar scores table
  │   │  ├─ Radar chart
  │   │  ├─ Key findings
  │   │  └─ 30/60/90 roadmap
  │   ├─ Output: RMI_Audit_Report_ACME_Plant4_20251227.pdf
  │   └─ Store in: reports table
  │
  └─► 8. DELIVER TO CLIENT
      ├─ Present findings
      ├─ Review roadmap
      └─ Schedule follow-up audit
```

## 📊 Data Flow: Response to Score

```
USER SUBMITS ANSWER
       │
       ▼
┌─────────────────────────┐
│  POST /responses        │
│  {                      │
│    question_id: 1,      │  ◄── Question P-01: Training
│    response_value: "4", │
│    evidence_notes: "..." │
│  }                      │
└──────────┬──────────────┘
           │
           ▼
    ┌─────────────┐
    │  VALIDATION │
    │  • Question exists?     │
    │  • Evidence required?   │
    │  • Score in range?      │
    └─────────┬───────────────┘
              │
              ▼
       ┌────────────────┐
       │ EVIDENCE CHECK │
       │                │
       │ IF score ≥ 4   │
       │ AND evidence_required = True  │
       │ AND evidence_notes = NULL     │
       │ THEN score = min(score, 3)    │
       └────────┬───────────────────────┘
                │
                ▼
         ┌─────────────────┐
         │ SAVE TO DB      │
         │ question_responses table    │
         │ • response_value = "4"      │
         │ • numeric_score = 4.0       │
         │ • evidence_provided = True  │
         └─────────┬───────────────────┘
                   │
                   ▼
            [SCORING ENGINE TRIGGER]
                   │
                   ▼
         ┌──────────────────────┐
         │ CALCULATE PILLAR     │
         │                      │
         │ 1. Get all responses │
         │    for pillar        │
         │ 2. Apply role weights│
         │    (tech: 60%)       │
         │ 3. Apply question    │
         │    weights           │
         │ 4. Check critical    │
         │    failures          │
         │ 5. Apply caps        │
         └─────────┬────────────┘
                   │
                   ▼
            ┌─────────────┐
            │ FINAL SCORE │
            │             │
            │ People: 2.8 │
            │ Confidence: High    │
            │ Evidence: 85%       │
            └─────────────────────┘
```

## 🔐 Authentication Flow

```
CLIENT
  │
  ├─► 1. POST /register
  │   └─ Returns: {id: 1, email: "auditor@example.com"}
  │
  ├─► 2. POST /token (login)
  │   ├─ Send: {username: "auditor@example.com", password: "***"}
  │   └─ Returns: {access_token: "eyJ...", token_type: "bearer"}
  │
  ├─► 3. Store Token
  │   └─ Save JWT token in localStorage/sessionStorage
  │
  └─► 4. Use Token in Requests
      └─ Header: "Authorization: Bearer eyJ..."

SERVER
  │
  ├─► Verify JWT signature
  ├─► Extract user_id from token payload
  ├─► Load user from database
  └─► Allow/Deny request based on user.role
```

## 📦 Module Dependencies

```
main.py (FastAPI App)
   │
   ├─► config.py (Settings)
   ├─► database.py (DB Connection)
   ├─► models.py (SQLAlchemy Models)
   │
   ├─► question_bank.py
   │   └─► models.py
   │
   ├─► scoring_engine.py
   │   ├─► models.py
   │   └─► database.py
   │
   ├─► observation_module.py
   │   └─► models.py
   │
   ├─► data_analysis_module.py
   │   ├─► models.py
   │   ├─► scoring_engine.py
   │   └─► pandas
   │
   ├─► iso14224_module.py
   │   └─► models.py
   │
   └─► report_generator.py
       ├─► models.py
       ├─► scoring_engine.py
       ├─► reportlab
       └─► matplotlib
```

## 🗂️ Evidence Attachment Flow

```
AUDITOR UPLOADS PHOTO
        │
        ▼
┌──────────────────────┐
│ POST /observations   │
│ + File Upload        │
│                      │
│ File: LOTO_proof.jpg │
│ Type: photo          │
│ Linked to: obs_id=12 │
└──────────┬───────────┘
           │
           ▼
  ┌────────────────┐
  │ Save to Disk   │
  │ ./uploads/     │
  │ observation_12/│
  │ LOTO_proof.jpg │
  └────────┬───────┘
           │
           ▼
    ┌────────────────────┐
    │ Create DB Record   │
    │ evidence table     │
    │ • observation_id=12│
    │ • file_path=...    │
    │ • file_name=...    │
    │ • uploaded_by=1    │
    └────────┬───────────┘
             │
             ▼
      ┌─────────────────┐
      │ Link to Score   │
      │                 │
      │ PR-03 (LOTO)    │
      │ • evidence_provided = True   │
      │ • Can score 5   │
      └─────────────────┘
```

## 📈 Scoring Calculation Example

```
PEOPLE PILLAR SCORE CALCULATION

Responses:
┌──────────┬───────┬────────┬──────────┬──────────┬──────────┐
│ Question │ Role  │ Score  │ Q.Weight │ R.Weight │ Weighted │
├──────────┼───────┼────────┼──────────┼──────────┼──────────┤
│ P-01     │ Tech  │   4    │   1.5    │   0.60   │   3.60   │
│ P-02     │ Tech  │   2    │   1.2    │   0.60   │   1.44   │
│ P-03     │ Tech  │   5    │   1.0    │   0.60   │   3.00   │
│ P-04     │ Mgr   │   3    │   1.0    │   0.20   │   0.60   │
│ P-05     │ Mgr   │   1    │   0.8    │   0.20   │   0.16   │
└──────────┴───────┴────────┴──────────┴──────────┴──────────┘

Raw Score = Σ(Weighted) / Σ(Weights)
          = (3.60 + 1.44 + 3.00 + 0.60 + 0.16) / (1.5×0.6 + 1.2×0.6 + 1.0×0.6 + 1.0×0.2 + 0.8×0.2)
          = 8.80 / 2.78
          = 3.16

Check Evidence Lock:
  P-01: Score 4, Evidence Required? YES, Evidence Provided? YES → OK
  All checks pass.

Check Critical Failures:
  P-01: Critical? YES, Score 4 → OK (≥3)
  P-03: Critical? YES, Score 5 → OK

Weakest Link Applied? NO (no critical failures ≤2)

FINAL PEOPLE SCORE: 3.16 → Rounds to 3.2
CONFIDENCE: High (85% evidence coverage, 5 responses)
```

## 🎯 Quick Reference: When to Use What

| I Want To... | Use This Module | Key Function |
|--------------|-----------------|--------------|
| Add questions | `question_bank.py` | `seed_question_bank()` |
| Calculate scores | `scoring_engine.py` | `ScoringEngine.calculate_assessment_scores()` |
| Record field observations | `observation_module.py` | `ObservationManager.create_observation()` |
| Analyze CMMS data | `data_analysis_module.py` | `CMMSDataAnalyzer.analyze_work_orders()` |
| Validate data quality | `iso14224_module.py` | `ISO14224Validator.validate_*()` |
| Generate PDF report | `report_generator.py` | `ReportGenerator.generate_executive_report()` |
| Create API endpoint | `main.py` | Add FastAPI route |
| Initialize database | `init_db.py` | `python init_db.py` |

---

**This completes the visual architecture documentation!**
