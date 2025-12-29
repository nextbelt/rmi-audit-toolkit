# RMI Audit Software - Complete System Documentation

**NextBelt LLC - Enterprise Reliability Maturity Index Assessment Platform**

**Version:** 1.0.0  
**Date:** December 27, 2025  
**Architecture:** Full-stack enterprise backend with REST API

---

## 🎯 Executive Overview

This is a **professional, audit-grade software platform** for conducting Reliability Maturity Index (RMI) assessments at asset-intensive facilities. This is NOT a survey tool - it's an ISO/SOC-style audit platform that produces defensible, evidence-based maturity scores.

### Key Differentiators

- **Evidence-Based Scoring**: High scores (4-5) are locked until evidence is provided
- **Weakest Link Logic**: Critical failures automatically cap pillar scores
- **Role-Weighted Responses**: Technicians 60%, Managers 20%, Observations 20%
- **ISO 14224 Compliance**: Validates CMMS data against international standards
- **Automated CMMS Analysis**: Calculates reactive ratio, PM compliance, data quality
- **Executive-Grade Reports**: Board-ready PDFs with charts and roadmaps

---

## 📁 System Architecture

### Technology Stack

```
Backend Framework:  FastAPI (Python 3.9+)
Database:          PostgreSQL / SQLite
ORM:               SQLAlchemy
Authentication:    JWT (OAuth2)
Data Analysis:     Pandas, NumPy
Reporting:         ReportLab, Matplotlib
File Processing:   Excel/CSV import (openpyxl, xlrd)
API Documentation: OpenAPI/Swagger (auto-generated)
```

### Project Structure

```
RMI Audit Toolkit/
│
├── config.py                   # Application configuration
├── database.py                 # Database connection & session management
├── models.py                   # SQLAlchemy data models (12 tables)
├── main.py                     # FastAPI application & REST endpoints
│
├── question_bank.py            # Professional question repository
├── scoring_engine.py           # RMI calculation logic with evidence validation
├── observation_module.py       # Field observation capture
├── data_analysis_module.py     # CMMS data analysis & metrics
├── iso14224_module.py          # ISO 14224 validation engine
├── report_generator.py         # Executive report generation (PDF)
│
├── init_db.py                  # Database initialization script
├── requirements.txt            # Python dependencies
└── .env.example                # Environment configuration template
```

---

## 🗄️ Database Schema

### Core Entities (12 Tables)

1. **users** - System users (auditors, admins, clients)
2. **assessments** - RMI audit engagements (the "project")
3. **assessment_auditors** - Audit team assignments (many-to-many)
4. **question_bank** - Master question repository (reusable, versioned)
5. **question_responses** - Individual answers with evidence
6. **observations** - Field observations during shadowing
7. **data_analyses** - CMMS data analysis results
8. **evidence** - Files (photos, docs, CMMS exports)
9. **scores** - Calculated RMI scores (pillar + overall)
10. **reports** - Generated reports (PDFs, metadata)
11. **iso14224_audits** - ISO 14224 compliance checks
12. **users** - Authentication & authorization

### Entity Relationships

```
Assessment (1) ──→ (N) QuestionResponses
Assessment (1) ──→ (N) Observations
Assessment (1) ──→ (N) DataAnalyses
Assessment (1) ──→ (N) Scores
Assessment (1) ──→ (N) Reports
Assessment (1) ──→ (N) ISO14224Audits

QuestionResponse (1) ──→ (N) Evidence
Observation (1) ──→ (N) Evidence
DataAnalysis (1) ──→ (N) Evidence

QuestionBank (1) ──→ (N) QuestionResponses
```

---

## 📊 The Professional Question Bank

### Question Metadata (What Makes It Audit-Grade)

Each question includes:

| Field | Purpose |
|-------|---------|
| **question_code** | Unique ID (e.g., "P-01", "T-03") |
| **pillar** | People / Process / Technology |
| **subcategory** | Fine-grained classification (e.g., "Competency", "Data Integrity") |
| **target_role** | Technician / Manager / Planner / Auditor |
| **question_type** | Likert / Binary / Multi-Select / Data Input / Observational |
| **weight** | Scoring importance (0.8 - 2.0) |
| **evidence_required** | Boolean - locks scores ≥4 until evidence provided |
| **evidence_description** | What validates this answer |
| **scoring_logic** | JSON rules: `{"1": "Description", "5": "Description"}` |
| **is_critical** | Critical failures cap pillar scores |

### Complete Question Bank (16 Pre-Loaded Questions)

---

## 👥 PEOPLE PILLAR (5 Questions)

Focuses on workforce competency, empowerment, and organizational culture.

---

### P-01: Equipment-Specific Training (CRITICAL)

**Question**: "Do you feel trained on the specific equipment you are assigned to maintain today?"

**Target Role**: Technician  
**Question Type**: Likert Scale (1-5)  
**Weight**: 1.5 (High importance)  
**Evidence Required**: Yes (if score ≥4)  
**Critical Question**: Yes (failure caps People pillar at 3.0)

**Scoring Rubric**:

| Score | Description | Meaning |
|-------|-------------|----------|
| **1** | I learn by guessing / No formal training | Reactive, unsafe |
| **2** | Some on-the-job training but inconsistent | Ad-hoc learning |
| **3** | Basic training provided | Minimum competency |
| **4** | Comprehensive training with documentation | Structured program |
| **5** | Formal certification program with ongoing skill validation | World-class |

**Evidence Required for Score ≥4**:  
Training certificate, competency matrix, or formal documentation

**Why It's Critical**:  
Untrained technicians cannot perform preventive work effectively, leading to reactive maintenance spiral.

---

### P-02: Emergency Interruptions

**Question**: "In a typical week, how many times is your scheduled work interrupted by an emergency?"

**Target Role**: Technician  
**Question Type**: Likert Scale (1-5)  
**Weight**: 1.2  
**Evidence Required**: No  
**Critical Question**: No

**Scoring Rubric**:

| Score | Description | Reactive Reality |
|-------|-------------|------------------|
| **1** | Daily / Constant interruptions (5+ per week) | Reactive spiral |
| **2** | Frequent interruptions (3-4 per week) | High reactive load |
| **3** | Occasional interruptions (1-2 per week) | Emerging preventive |
| **4** | Rare interruptions (1-2 per month) | Preventive discipline |
| **5** | Almost never / Scheduled work is protected | Predictive maturity |

**What This Measures**:  
The reality gap between planned vs. reactive work. High interruptions indicate poor equipment reliability.

---

### P-03: Stop Work Authority (CRITICAL)

**Question**: "If you see a safety or reliability risk, do you feel authorized to stop production?"

**Target Role**: Technician  
**Question Type**: Binary (Yes/No)  
**Weight**: 1.0  
**Evidence Required**: No  
**Critical Question**: Yes

**Scoring Rubric**:

| Answer | Score | Meaning |
|--------|-------|----------|
| **Yes** | 5 points | Empowered workforce / Strong safety culture |
| **No** | 1 point | Authority gap / Cultural issue / Safety risk |

**Why It's Critical**:  
Lack of stop work authority indicates cultural problems that undermine all reliability efforts.

---

### P-04: Knowledge Transfer Mechanisms

**Question**: "How is knowledge transferred from senior technicians to new hires?"

**Target Role**: Manager  
**Question Type**: Multi-Select  
**Weight**: 1.0  
**Evidence Required**: Yes (if score ≥4)  
**Critical Question**: No

**Answer Options**:
- Ad-hoc shadowing only
- Informal mentorship
- Documented training program
- Knowledge base / Wiki
- Formal certification path
- Cross-training rotations

**Scoring Rubric**:

| Score | Description |
|-------|-------------|
| **1** | Only ad-hoc shadowing (tribal knowledge) |
| **3** | Informal mentorship + some documentation |
| **5** | Formal program + knowledge base + certification |

**Evidence Required for Score ≥4**:  
Documentation of mentorship program, knowledge base screenshots, or training records

**What This Measures**:  
Protection against knowledge loss when experienced workers retire.

---

### P-05: Training Budget Allocation

**Question**: "Does the maintenance budget include a dedicated line item for technician training?"

**Target Role**: Manager  
**Question Type**: Binary (Yes/No)  
**Weight**: 0.8  
**Evidence Required**: Yes  
**Critical Question**: No

**Scoring Rubric**:

| Answer | Score | Meaning |
|--------|-------|----------|
| **Yes** | 5 points | Training is a funded priority |
| **No** | 1 point | Training not formalized in budget |

**Evidence Required**:  
Budget spreadsheet showing training allocation

**What This Measures**:  
Organizational commitment to workforce development. No budget = no training.

---

## ⚙️ PROCESS PILLAR (5 Questions)

Focuses on work execution, planning discipline, and procedural adherence.

---

### PR-01: Spare Parts Availability

**Question**: "Did the technician have the correct spare part available immediately?"

**Target Role**: Auditor (Observation)  
**Question Type**: Observational  
**Weight**: 1.3  
**Evidence Required**: Yes  
**Critical Question**: No

**Scoring Rubric**:

| Score | Description | Impact |
|-------|-------------|--------|
| **1** | Technician had to leave area to find/order part (delay >30 min) | Work stoppage |
| **2** | Part available in storeroom but not kitted | Inefficiency |
| **3** | Part kitted but not at job site | Some planning |
| **4** | Part at job site but some confusion | Good planning |
| **5** | Kitting process had exact part ready at job site | Excellent planning |

**Evidence Required**:  
Photo of part available at job site OR note documenting delay/search time

**What This Measures**:  
Planning effectiveness. Parts kitting is a leading indicator of work order planning quality.

---

### PR-02: SOP Usage During Work

**Question**: "Did the technician reference a Standard Operating Procedure (SOP) during the repair?"

**Target Role**: Auditor (Observation)  
**Question Type**: Observational  
**Weight**: 1.2  
**Evidence Required**: Yes  
**Critical Question**: No

**Scoring Rubric**:

| Score | Description | Risk Level |
|-------|-------------|------------|
| **1** | No SOP visible / Technician unaware of SOP | High risk of error |
| **2** | SOP exists but not accessible at job site | Procedures ignored |
| **3** | SOP referenced briefly | Minimal compliance |
| **4** | SOP used for most steps | Strong adherence |
| **5** | SOP followed step-by-step with sign-off | Excellent discipline |

**Evidence Required**:  
Photo of SOP in use OR note explaining why SOP was not referenced

**What This Measures**:  
Process discipline. Work quality suffers without procedure adherence.

---

### PR-03: LOTO Procedure Compliance (CRITICAL)

**Question**: "Was the Lock-Out/Tag-Out (LOTO) procedure correctly applied before work started?"

**Target Role**: Auditor (Observation)  
**Question Type**: Binary (Pass/Fail)  
**Weight**: 2.0 (Highest weight - safety critical)  
**Evidence Required**: Yes  
**Critical Question**: Yes (CRITICAL FAIL)

**Scoring Rubric**:

| Answer | Score | Consequence |
|--------|-------|-------------|
| **Pass** | 5 points | Safety protocol followed |
| **Fail** | 1 point | **CRITICAL FAIL - Automatic Process pillar cap at 3.0** |

**Evidence Required**:  
Photo of LOTO application or safety permit

**Why It's Critical**:  
LOTO violations are life-threatening. A single failure invalidates all other process scores.

---

### PR-04: Job Plan Quality (CRITICAL)

**Question**: "What percentage of Work Orders have a detailed Job Plan attached?"

**Target Role**: Planner  
**Question Type**: Data Input (%)  
**Weight**: 1.4  
**Evidence Required**: Yes  
**Critical Question**: Yes

**Scoring Rubric**:

| Score | % WOs with Job Plans | Maturity Level |
|-------|---------------------|----------------|
| **1** | <10% (just headers) | No planning discipline |
| **2** | 10-30% (basic plans) | Emerging planning |
| **3** | 30-60% | Inconsistent planning |
| **4** | 60-90% (detailed plans) | Strong planning |
| **5** | >90% (comprehensive plans with steps/parts/safety) | World-class planning |

**Evidence Required**:  
CMMS report showing % of WOs with job plans, or sample of 20 WOs

**Why It's Critical**:  
Job plans are the foundation of planned maintenance. <30% caps Process pillar at 3.0.

---

### PR-05: PM Compliance Rate (CRITICAL)

**Question**: "Are Preventive Maintenance (PM) tasks completed within their scheduled window?"

**Target Role**: Planner  
**Question Type**: Data Input (%)  
**Weight**: 1.3  
**Evidence Required**: Yes  
**Critical Question**: Yes

**Scoring Rubric**:

| Score | On-Time PM % | Discipline Level |
|-------|--------------|------------------|
| **1** | <50% | No PM discipline (reactive spiral) |
| **2** | 50-70% | Struggling to keep up |
| **3** | 70-85% | Acceptable compliance |
| **4** | 85-95% | Strong discipline |
| **5** | >95% (with documented exceptions) | Exceptional discipline |

**Evidence Required**:  
CMMS PM compliance report showing on-time completion %

**Why It's Critical**:  
PM compliance is the heartbeat of reliability. Low compliance = equipment degradation.

---

## 💻 TECHNOLOGY PILLAR (6 Questions)

Focuses on CMMS data quality, system usability, and technology enablement.

---

### T-01: Data Graveyard Detection (CRITICAL)

**Question**: "Random Sampling: Pull 50 closed work orders. How many have generic closure codes like 'DONE' or 'FIXED'?"

**Target Role**: Auditor  
**Question Type**: Data Input (count)  
**Weight**: 1.5  
**Evidence Required**: Yes  
**Critical Question**: Yes

**Scoring Rubric**:

| Score | # WOs with Generic Codes | Data Quality |
|-------|-------------------------|---------------|
| **1** | >20 WOs (>40%) | **SEVERE DATA GRAVEYARD** - Cannot perform RCA |
| **2** | 10-20 WOs (20-40%) | Poor data quality |
| **3** | 5-10 WOs (10-20%) | Acceptable data quality |
| **4** | 2-5 WOs (4-10%) | Good data quality |
| **5** | <2 WOs (<4%) | High data quality |

**Evidence Required**:  
Screenshot of CMMS export showing closure codes or Excel analysis

**Why It's Critical**:  
>40% generic codes means you cannot identify failure patterns. Caps Technology pillar at 2.0.

**What to Look For**:
- "DONE"
- "FIXED"
- "OK"
- "COMPLETE"
- "REPLACED PART"
- Notes <10 characters

---

### T-02: ISO 14224 Taxonomy Alignment (CRITICAL)

**Question**: "Do failure codes align with ISO 14224 taxonomy (Component - Failure Mode - Cause)?"

**Target Role**: Auditor  
**Question Type**: Binary (Yes/No)  
**Weight**: 1.2  
**Evidence Required**: Yes  
**Critical Question**: Yes

**Scoring Rubric**:

| Answer | Score | Data Structure |
|--------|-------|----------------|
| **Yes** | 5 points | Structured, analyzable data (can perform RCA) |
| **No** | 1 point | Unstructured data / Cannot perform Root Cause Analysis |

**Evidence Required**:  
Screenshot of failure code structure in CMMS or data export

**ISO 14224 Taxonomy Structure**:
```
Component (What failed)
  └─ Failure Mode (How it failed)
      └─ Failure Cause (Why it failed)

Example:
  Pump Seal ← Component
    └─ External Leakage ← Failure Mode
        └─ Wear Out ← Failure Cause
```

**Why It's Critical**:  
Without structured failure taxonomy, you cannot identify root causes or prevent recurrence.

---

### T-03: Bad Actor Reporting Capability

**Question**: "Can you generate a 'Bad Actor' report (Top 10 failing assets) in under 5 minutes?"

**Target Role**: Manager  
**Question Type**: Observational  
**Weight**: 1.0  
**Evidence Required**: Yes  
**Critical Question**: No

**Scoring Rubric**:

| Score | Description | System Capability |
|-------|-------------|-------------------|
| **1** | No - Must export to Excel and manually analyze | No reporting capability |
| **2** | Requires custom SQL or IT support | IT-dependent |
| **3** | Possible but requires 15-30 minutes | Cumbersome |
| **4** | Can generate in 5-10 minutes | Good capability |
| **5** | Yes - One-click dashboard available | Excellent capability |

**Evidence Required**:  
Screenshot of report OR timer evidence showing time to generate

**What This Measures**:  
CMMS reporting maturity. Can managers get actionable data quickly?

---

### T-04: CMMS Usability

**Question**: "Rate the difficulty of entering data into the current CMMS."

**Target Role**: Technician  
**Question Type**: Likert Scale (1-5)  
**Weight**: 0.8  
**Evidence Required**: No  
**Critical Question**: No

**Scoring Rubric**:

| Score | Description | User Experience |
|-------|-------------|------------------|
| **1** | Extremely frustrating / I avoid it when possible | System rejection |
| **2** | Difficult - Too many fields/steps | High friction |
| **3** | Acceptable - Some friction | Tolerable |
| **4** | Easy - Straightforward process | Good UX |
| **5** | Seamless - Mobile-friendly, intuitive | Excellent UX |

**What This Measures**:  
User adoption. Difficult systems = poor data quality (garbage in, garbage out).

---

### T-05: Asset Hierarchy Depth

**Question**: "What is the asset hierarchy depth in the CMMS?"

**Target Role**: Auditor  
**Question Type**: Data Input (levels)  
**Weight**: 1.0  
**Evidence Required**: Yes  
**Critical Question**: No

**Scoring Rubric**:

| Score | Hierarchy Depth | Structure Quality |
|-------|----------------|-------------------|
| **1** | Flat (1-2 levels) | No functional hierarchy |
| **2** | Basic (3 levels) | Site > Area > Equipment |
| **3** | Good (4 levels) | Site > Area > System > Equipment |
| **4** | Comprehensive (5 levels) | Includes components |
| **5** | ISO 14224 compliant (5+ levels) | Down to failure mode level |

**Evidence Required**:  
Screenshot of asset hierarchy or CMMS structure export

**Ideal Structure**:
```
Site (Plant 1)
  └─ Area (Finishing Department)
      └─ System (Conveyor Line A)
          └─ Equipment (Motor 304A)
              └─ Component (Bearing)
```

---

### T-06: Work Order Attachments Accessibility

**Question**: "Are work order attachments (photos, manuals) easily accessible from the CMMS?"

**Target Role**: Technician  
**Question Type**: Likert Scale (1-5)  
**Weight**: 0.9  
**Evidence Required**: No  
**Critical Question**: No

**Scoring Rubric**:

| Score | Description | Information Access |
|-------|-------------|--------------------|
| **1** | No attachment capability or never used | No knowledge capture |
| **2** | Possible but cumbersome | Rarely used |
| **3** | Available but not consistently used | Inconsistent adoption |
| **4** | Easy to access, commonly used | Good adoption |
| **5** | Integrated with mobile access, widely adopted | Excellent adoption |

**What This Measures**:  
Knowledge retention. Photos and manuals at point-of-work improve quality and speed.

---

## 🧮 RMI Scoring Engine

### The Scoring Algorithm

```python
# 1. Role-Weighted Scoring
ROLE_WEIGHTS = {
    "technician": 0.60,  # Ground truth
    "manager": 0.20,     # Intent
    "auditor": 0.20      # Verification (observations + data)
}

# 2. Question Weighting
weighted_score = Σ(response_score × role_weight × question_weight) / Σ(weights)

# 3. Filter Draft and N/A Responses
responses = responses.filter(
    QuestionResponse.is_draft == False,
    QuestionResponse.is_na == False
)

# 4. Evidence Lock
if question.evidence_required and score >= 4:
    if not evidence_provided:
        score = min(score, 3)  # Cap at 3

# 5. Weakest Link Logic
if any critical_question.score <= 2:
    pillar_score = min(pillar_score, 3.0)

# 6. Overall RMI
RMI = (People_Score + Process_Score + Technology_Score) / 3
```

### Maturity Levels

| RMI Score | Maturity Level |
|-----------|----------------|
| < 2.0 | **Reactive** - Fire-fighting mode |
| 2.0 - 2.9 | **Emerging Preventive** - Building discipline |
| 3.0 - 3.9 | **Preventive** - Planned maintenance dominant |
| 4.0 - 4.4 | **Predictive** - Condition-based strategies |
| 4.5 - 5.0 | **Prescriptive** - World-class, AI-enabled |

### Confidence Levels

- **High**: ≥80% evidence coverage + ≥5 responses
- **Medium**: 50-79% evidence or 3-4 responses
- **Low**: <50% evidence or <3 responses

---

## 🔬 Data Analysis Module (The "Data Cruncher")

### Automated CMMS Metrics

#### 1. Reactive Ratio
```python
reactive_ratio = (emergency_WOs + corrective_WOs) / total_WOs

Score mapping:
1: >60% reactive (REACTIVE SPIRAL)
2: 40-60% reactive
3: 25-40% reactive
4: 15-25% reactive
5: <15% reactive
```

#### 2. PM Compliance
```python
pm_compliance = on_time_PMs / total_PMs
# (7-day grace period allowed)

Score mapping:
1: <50% on-time
3: 70-85% on-time
5: >95% on-time
```

#### 3. Data Graveyard Index
```python
graveyard_% = (generic_closure_codes + notes<10_chars) / total_WOs

Score mapping:
1: >40% poor quality (CANNOT PERFORM RCA)
3: 10-20% poor quality
5: <4% poor quality
```

#### 4. Bad Actor Detection
```python
# Top 10 failing assets by corrective/emergency WO count
# Requires: asset_id or equipment column
```

### Supported File Formats

- CSV (comma-separated)
- Excel (.xlsx, .xls)
- Custom column mapping configurable per CMMS system

---

## 🏗️ ISO 14224 Validation Module

### What is ISO 14224?

International standard for reliability and maintenance data collection in petroleum/process industries.

### Validation Checks

#### 1. Asset Hierarchy Depth
- Required: Minimum 4 levels
- Optimal: 5+ levels (Site → Area → System → Equipment → Component)
- Scoring impact: ±1.0 to ±2.0 points

#### 2. Failure Taxonomy Structure
- Component → Failure Mode → Failure Cause
- Standard failure modes: Breakdown, Leakage, Erratic output, etc.
- Alignment threshold: ≥70% for passing score

#### 3. Data Completeness
- Critical fields: ≥90% populated
- Examples: Equipment ID, Failure Mode, Work Description

#### 4. Closure Code Quality
- Generic codes flagged: "DONE", "FIXED", "OK"
- Requires meaningful closure descriptions

### Impact on Technology Score

ISO 14224 compliance directly affects the **Technology pillar** score:
- Full compliance: +2.0 points
- Partial compliance: +0.5 to +1.0 points
- Non-compliance: -2.0 points (caps Technology score at 3.0)

---

## 🎭 Observation & Shadowing Module

### Use Cases

1. **Job Shadowing**: Follow technician during PM/repair
2. **Safety Compliance**: LOTO, PPE, permits
3. **Process Adherence**: SOP usage, parts kitting, tool readiness
4. **CMMS Usage**: Real-time data entry, mobile access

### Pre-Built Checklists

#### Work Execution Checklist
- Spare parts availability
- SOP reference & usage
- Tools & equipment readiness

#### Safety Checklist (Critical)
- LOTO procedure applied
- PPE compliance
- Permit-to-work obtained

#### CMMS Usage Checklist
- Mobile device access
- Real-time work order updates
- Photo attachment capability

### Evidence Capture

- **Photos**: JPEG/PNG uploads
- **Notes**: Markdown-formatted observations
- **Pass/Fail**: Binary compliance checks
- **Severity**: Critical / Major / Minor

All evidence auto-linked to:
- Specific questions (if applicable)
- Observations
- Final scores

---

## 📈 Executive Report Generator

### Report Types

#### 1. Executive Summary (PDF)
- Cover page with client branding
- Overall RMI score (1-5)
- Pillar breakdown table
- Radar chart visualization
- Key findings by pillar
- 30/60/90-day roadmap
- Technology gap analysis

#### 2. Technical Detail Report
- All questions with responses
- Evidence attachments index
- Observation log
- CMMS data analysis details
- ISO 14224 compliance checklist

#### 3. PowerPoint Export (Future)
- Key slides for board presentation
- Visual dashboards
- Roadmap timeline

### Charts & Visualizations

1. **Radar Chart**: 3-pillar maturity profile
2. **Bar Chart**: Subcategory scores
3. **Timeline**: Roadmap phases
4. **Data Quality Heatmap**: ISO 14224 compliance

### Report Branding

- Configurable NextBelt logo
- Client-specific cover page
- Professional color scheme (blues, grays)
- Board-ready formatting

---

## 🆕 Data Saving & UX Improvements (Dec 2024)

### Draft Response System

All question responses now support **draft mode**:

```python
class QuestionResponse:
    is_draft = Column(Boolean, default=False)  # Autosaved drafts
    is_na = Column(Boolean, default=False)     # Not Applicable
```

**Autosave Logic:**
- Drafts save automatically 1 second after typing stops
- Only final responses (is_draft=False) count toward RMI score
- Scoring engine filters: `WHERE is_draft = False AND is_na = False`

### N/A (Not Applicable) Handling

Questions can be marked as "Not Applicable":
- Checkbox disables answer fields and score buttons
- Excluded from scoring calculations entirely
- Useful for questions irrelevant to specific facilities
- Example: Predictive maintenance questions for small sites without PdM

### Evidence Validation Enforcement

**Before submission**, the UI now blocks high scores without evidence:

```typescript
if (score >= 4 && evidence_required && !has_evidence && !is_na) {
  setValidationError('⚠️ Evidence is required for scores ≥4');
  return; // Block submission
}
```

This prevents the need for post-audit score downgrades.

### Offline Queue Management

For field work in basements or remote sites:
- Network errors automatically queue requests to localStorage
- Auto-sync when connection restored
- Shows pending queue count in dashboard
- Manual retry button for failed requests

### Safari Compatibility

Full support for macOS/iOS Safari:
- `withCredentials: true` for cross-origin requests
- CORS headers: `expose_headers=["*"]`, `max_age=3600`
- Tested on Safari 17+ and iOS Safari

---

## 🔐 Security & Authentication

### JWT-Based Auth

```python
# User registration
POST /register
{
  "email": "auditor@nextbelt.com",
  "password": "secure_password",
  "full_name": "Jane Auditor",
  "role": "auditor"
}

# Login
POST /token
{
  "username": "auditor@nextbelt.com",
  "password": "secure_password"
}
# Returns: {"access_token": "eyJ...", "token_type": "bearer"}

# Use token in header
Authorization: Bearer eyJ...
```

### User Roles

- **Admin**: Full system access, user management
- **Auditor**: Create assessments, conduct audits, generate reports
- **Client**: View-only access to their assessments

### Default Credentials

```
Email: admin@nextbelt.com
Password: admin123
⚠️ CHANGE IMMEDIATELY IN PRODUCTION
```

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
# Navigate to project directory
cd "c:\Users\cncha\OneDrive\Desktop\RMI Audit Toolkit"

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env

# Edit .env and configure database URL
```

### 2. Database Setup

```bash
# Initialize database and seed question bank
python init_db.py
```

Output:
```
✅ Database tables created
✅ Seeded 16 questions
✅ Admin user created
```

### 3. Start API Server

```bash
# Development mode
python main.py

# Production mode with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Access API Documentation

Open browser: `http://localhost:8000/docs`

This opens **Swagger UI** with interactive API testing.

---

## 📡 REST API Endpoints (Key Routes)

### Authentication
```
POST   /register              # Create new user
POST   /token                 # Login and get JWT token
```

### Assessments
```
POST   /assessments                           # Create new audit
GET    /assessments                           # List all audits
GET    /assessments/{id}                      # Get specific audit
PUT    /assessments/{id}/status               # Update status
```

### Question Bank
```
GET    /questions                             # List all questions
GET    /questions?pillar=people               # Filter by pillar
GET    /questions?target_role=technician      # Filter by role
GET    /questions/critical                    # List critical questions
```

### Responses
```
POST   /assessments/{id}/responses            # Submit answer
GET    /assessments/{id}/responses            # List all answers
```

### Observations
```
POST   /assessments/{id}/observations         # Record observation
GET    /assessments/{id}/observations         # List observations
```

### Scoring
```
POST   /assessments/{id}/calculate-scores     # Run scoring engine
GET    /assessments/{id}/scores               # Get scores
GET    /assessments/{id}/score-breakdown      # Detailed breakdown
```

### Data Analysis
```
POST   /assessments/{id}/analyze-work-orders      # Upload CMMS WO data
POST   /assessments/{id}/analyze-pm-compliance    # Upload PM data
```

### ISO 14224
```
POST   /assessments/{id}/iso14224/validate-hierarchy    # Validate hierarchy
POST   /assessments/{id}/iso14224/validate-taxonomy     # Validate failure codes
GET    /assessments/{id}/iso14224/summary               # Get compliance summary
```

---

## 🔄 Typical Audit Workflow

### Phase 1: Setup (Day 1)
1. **Create Assessment**
   ```
   POST /assessments
   {
     "client_name": "ACME Manufacturing",
     "site_name": "Plant 4",
     "industry": "Food & Beverage",
     "assessment_date": "2025-12-27"
   }
   ```

2. **Assign Audit Team**
   - Lead auditor
   - Technical specialist
   - Data analyst

### Phase 2: Data Collection (Days 2-4)

#### Interview Technicians
```
POST /assessments/1/responses
{
  "question_id": 1,  # P-01: Training
  "response_value": "4",
  "evidence_notes": "Completed Level 2 Pump Certification on 2025-10-15"
}
```

#### Conduct Field Observations
```
POST /assessments/1/observations
{
  "title": "PM Task Observation - Pump 304A",
  "type": "Work Execution",
  "pillar": "process",
  "notes": "Technician did not reference SOP. Part not kitted.",
  "pass_fail": false,
  "severity": "Major"
}
```

#### Upload CMMS Data
```
POST /assessments/1/analyze-work-orders
[Upload CSV file with work orders]

Response:
{
  "reactive_ratio": {
    "reactive_ratio": 67.3,
    "severity": "CRITICAL - REACTIVE SPIRAL",
    "score": 1
  }
}
```

### Phase 3: Analysis (Day 5)

#### Run Scoring Engine
```
POST /assessments/1/calculate-scores

Response:
{
  "overall_rmi": 2.4,
  "maturity_level": "Emerging Preventive",
  "pillar_scores": {
    "people": {"final_score": 2.8, "confidence": "High"},
    "process": {"final_score": 2.1, "confidence": "Medium"},
    "technology": {"final_score": 2.3, "confidence": "High"}
  }
}
```

#### Validate ISO 14224 Compliance
```
POST /assessments/1/iso14224/validate-hierarchy
[Upload asset hierarchy export]

POST /assessments/1/iso14224/validate-taxonomy
[Upload failure codes]
```

### Phase 4: Reporting (Day 6)

#### Generate Executive Report
```python
from report_generator import ReportGenerator
generator = ReportGenerator(db)
pdf_path = generator.generate_executive_report(
    assessment_id=1,
    generated_by=current_user.id
)
# Returns: "./reports/RMI_Audit_Report_ACME_Plant4_20251227.pdf"
```

### Phase 5: Delivery (Day 7)
- Present findings to client leadership
- Review roadmap priorities
- Schedule 90-day follow-up

---

## 🧪 Evidence Requirements (The "Lock")

### Evidence Lock Logic

```python
# High scores require proof
if question.evidence_required and response.score >= 4:
    if not evidence.provided:
        response.score = min(response.score, 3)
        alert = "Score capped at 3 - Evidence required for scores ≥4"
```

### Evidence Types

1. **Photos** (.jpg, .png)
   - LOTO application
   - Work execution
   - Asset condition
   - Safety compliance

2. **Documents** (.pdf, .docx)
   - Training certificates
   - SOPs
   - Competency matrices
   - Budget spreadsheets

3. **Screenshots** (.png)
   - CMMS dashboards
   - Bad actor reports
   - PM compliance charts

4. **CMMS Exports** (.csv, .xlsx)
   - Work order history
   - PM schedule
   - Asset hierarchy
   - Failure codes

5. **Notes** (text)
   - Interview summaries
   - Observation details
   - Auditor commentary

---

## 🎯 Scoring Validation Rules

### Critical Failure Rules

| Question Code | Failure Condition | Impact |
|---------------|-------------------|--------|
| P-01 | Training score ≤ 2 | People pillar capped at 3.0 |
| P-03 | No stop work authority | People pillar capped at 3.0 |
| PR-03 | LOTO not applied | Process pillar = CRITICAL FAIL |
| PR-04 | <30% job plans | Process pillar capped at 3.0 |
| T-01 | >40% generic codes | Technology pillar capped at 2.0 |
| T-02 | No ISO 14224 alignment | Technology pillar capped at 3.0 |

### Score Normalization

```python
# Raw score (before caps)
raw_score = weighted_average(all_responses)

# Apply evidence caps
for response in responses:
    if evidence_required and score >= 4 and not evidence_provided:
        response.score = 3

# Recalculate weighted score
weighted_score = recalculate_with_caps()

# Apply weakest link
if critical_failures_exist:
    final_score = min(weighted_score, 3.0)
else:
    final_score = weighted_score
```

---

## 📊 Sample Output: Assessment Summary

```json
{
  "assessment_id": 1,
  "client_name": "ACME Manufacturing",
  "site_name": "Plant 4",
  "overall_rmi": 2.4,
  "maturity_level": "Emerging Preventive",
  
  "pillar_scores": {
    "people": {
      "raw_score": 3.1,
      "final_score": 2.8,
      "confidence": "High",
      "evidence_coverage": 85.0,
      "critical_failures": [
        {
          "question_code": "P-01",
          "score": 2,
          "question": "Do you feel trained on the specific equipment you are assigned to maintain today?"
        }
      ]
    },
    "process": {
      "raw_score": 2.1,
      "final_score": 2.1,
      "confidence": "Medium",
      "evidence_coverage": 60.0,
      "critical_failures": []
    },
    "technology": {
      "raw_score": 2.9,
      "final_score": 2.3,
      "confidence": "High",
      "evidence_coverage": 90.0,
      "critical_failures": [
        {
          "question_code": "T-01",
          "score": 1,
          "question": "Random Sampling: Pull 50 closed work orders. How many have generic closure codes like 'DONE' or 'FIXED'?"
        }
      ]
    }
  },
  
  "cmms_analysis": {
    "reactive_ratio": 67.3,
    "pm_compliance": 58.2,
    "data_graveyard_index": 43.5,
    "bad_actors": ["Pump-304A", "Compressor-12", "Motor-45B"]
  },
  
  "iso14224_compliance": {
    "hierarchy_depth": "FAIL - Only 3 levels",
    "taxonomy_alignment": "FAIL - No Component-Mode-Cause structure",
    "compliance_score": 1
  },
  
  "roadmap_priorities": [
    "30-Day: Audit 100 recent WOs for data quality",
    "60-Day: Redesign failure code structure per ISO 14224",
    "90-Day: Implement Reliability Center of Excellence"
  ]
}
```

---

## 🔧 Customization & Extension

### Adding New Questions

```python
# In question_bank.py
new_question = {
    "question_code": "P-06",
    "question_text": "Your custom question here",
    "pillar": PillarType.PEOPLE,
    "subcategory": "New Category",
    "target_role": TargetRole.TECHNICIAN,
    "question_type": QuestionType.LIKERT,
    "weight": 1.0,
    "evidence_required": False,
    "scoring_logic": {"1": "Bad", "5": "Excellent"},
    "is_critical": False
}

db.add(QuestionBank(**new_question))
db.commit()
```

### Custom CMMS Column Mapping

```python
# In data_analysis_module.py
custom_mapping = {
    "work_order_number": ["WO_NUM", "Order_ID"],
    "work_order_type": ["TYPE", "Category"],
    "priority": ["PRIORITY_CODE"],
    # ... add your CMMS columns
}

analyzer.import_work_orders(file_path, column_mapping=custom_mapping)
```

### Adding Custom Observations

```python
custom_checklist = [
    {
        "title": "Custom Check",
        "type": "Custom Type",
        "pillar": "process",
        "subcategory": "My Category",
        "notes": "Observation template"
    }
]

obs_manager.create_checklist_observation(
    assessment_id=1,
    observer_id=user_id,
    checklist_items=custom_checklist
)
```

---

## 🐛 Troubleshooting

### Database Connection Issues

**Problem**: `OperationalError: no such table`

**Solution**:
```bash
python init_db.py  # Re-initialize database
```

### Evidence Lock Not Working

**Problem**: User can submit score of 5 without evidence

**Check**:
```python
question = db.query(QuestionBank).filter_by(question_code="P-01").first()
print(question.evidence_required)  # Should be True
```

### Scoring Engine Returns 0

**Problem**: `overall_rmi: 0`

**Likely Cause**: No responses submitted yet

**Solution**:
```python
responses = db.query(QuestionResponse).filter_by(assessment_id=1).all()
print(f"Found {len(responses)} responses")
```

### CMMS Import Fails

**Problem**: `ValueError: work_order_type column not found`

**Solution**: Provide custom column mapping or check CSV headers

```python
import pandas as pd
df = pd.read_csv("your_file.csv")
print(df.columns)  # Verify column names
```

---

## 📚 API Testing Examples (Using curl)

### Create Assessment
```bash
curl -X POST http://localhost:8000/assessments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "site_name": "Test Site",
    "assessment_date": "2025-12-27T00:00:00"
  }'
```

### Submit Response
```bash
curl -X POST http://localhost:8000/assessments/1/responses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": 1,
    "response_value": "4",
    "evidence_notes": "Training cert attached"
  }'
```

### Calculate Scores
```bash
curl -X POST http://localhost:8000/assessments/1/calculate-scores \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Upload CMMS Data
```bash
curl -X POST http://localhost:8000/assessments/1/analyze-work-orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@work_orders.csv"
```

---

## 🎓 Appendix: Key Concepts

### What is RMI?

**Reliability Maturity Index (RMI)** is a quantitative measure (1-5 scale) of an organization's maintenance and reliability capabilities across People, Process, and Technology.

### The Reactive Spiral

A vicious cycle where:
1. Poor maintenance leads to more breakdowns
2. Breakdowns consume all resources
3. No time for preventive work
4. More breakdowns occur
5. **Result**: 60%+ reactive work = SPIRAL

### Evidence-Based Auditing

Unlike surveys, this platform requires **tangible proof**:
- "We have training" → Show me the training matrix
- "Our CMMS has failure codes" → Show me 50 sample work orders
- "Technicians use SOPs" → Let me observe a job

### ISO 14224 Taxonomy

```
Component (What failed)
  └─ Failure Mode (How it failed)
      └─ Failure Cause (Why it failed)

Example:
  Pump Seal (Component)
    └─ External Leakage (Mode)
        └─ Wear Out (Cause)
```

---

## 📞 Support & Contact

**Developed for:** NextBelt LLC  
**Platform Version:** 1.0.0  
**Last Updated:** December 27, 2025

### For Technical Support

- Check [API Documentation](http://localhost:8000/docs)
- Review this guide's Troubleshooting section
- Verify database initialization: `python init_db.py`

### For Feature Requests

This platform is designed to evolve. Future enhancements may include:
- Mobile app for field data collection
- Real-time dashboards for ongoing audits
- Integration with major CMMS systems (SAP, Maximo, Fiix)
- Machine learning for predictive scoring
- Multi-site benchmarking

---

## ✅ Pre-Flight Checklist (Before First Audit)

- [ ] Database initialized (`python init_db.py`)
- [ ] API server running (`python main.py`)
- [ ] Admin user created and tested
- [ ] Question bank seeded (16 questions)
- [ ] Upload directories created (`./uploads`, `./reports`)
- [ ] `.env` file configured with production settings
- [ ] Test assessment created
- [ ] Sample CMMS data uploaded and analyzed
- [ ] PDF report generated successfully
- [ ] Evidence upload tested

---

## 🏆 System Highlights

### What Makes This Enterprise-Grade?

1. **Audit Trail**: Every response, observation, and score change is logged
2. **Version Control**: Question bank is versioned (framework_version)
3. **Multi-Tenancy Ready**: Assessments isolated by client
4. **Role-Based Access**: Admin / Auditor / Client roles
5. **Scalable Architecture**: FastAPI async-ready for high concurrency
6. **Data Integrity**: Foreign key constraints, cascading deletes
7. **Professional Output**: Board-ready reports, not spreadsheets

### Performance at Scale

- **Small Audit**: 50 questions, 10 observations → <5 minutes to score
- **Medium Audit**: 100 questions, 30 observations, 1000 WOs → <15 minutes
- **Large Audit**: 200 questions, 50 observations, 10,000 WOs → <30 minutes

### Compliance & Standards

- ✅ ISO 14224 validation built-in
- ✅ Evidence requirements enforced
- ✅ Audit trail for regulatory review
- ✅ Defensible methodology (role-weighted, evidence-based)

---

## 🚀 You're Ready to Conduct World-Class Reliability Audits

This system transforms reliability assessments from subjective surveys into **defensible, evidence-based audits** that drive real operational improvement.

Every score is traceable. Every high score is proven. Every report is board-ready.

**Welcome to enterprise reliability auditing.**

---

**END OF DOCUMENTATION**
