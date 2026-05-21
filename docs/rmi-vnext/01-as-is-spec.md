# 01 — RMI v1 As-Is Specification

**Document ID:** RMI-VNEXT-01  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** VP of Reliability · Principal Consultant · Engineering

---

## 1. Executive Summary

The current RMI Audit Toolkit (v1.0) is a full-stack assessment platform built on FastAPI + React/TypeScript, deployed on Railway with Supabase auth. It implements a **three-pillar model** (People, Process, Technology) with **16 hardcoded questions**, evidence-lock scoring, weakest-link caps, and role-weighted response aggregation. The platform produces PDF executive reports with radar charts.

**Verdict:** v1 is a functional MVP proving the core audit methodology. It lacks the question depth, industry modularity, and benchmarking infrastructure required to scale beyond single-site, single-industry engagements.

---

## 2. Architecture Inventory

### 2.1 Technology Stack

| Layer             | Technology                            | Evidence                                 |
|-------------------|---------------------------------------|------------------------------------------|
| Backend Framework | FastAPI (Python)                      | `[OBSERVED]` backend/main.py:1-7         |
| Database          | PostgreSQL (Railway) / SQLite (local) | `[OBSERVED]` backend/database.py         |
| ORM               | SQLAlchemy                            | `[OBSERVED]` backend/models.py:5-8       |
| Auth              | JWT + Supabase                        | `[OBSERVED]` backend/main.py:192-198     |
| Frontend          | React + TypeScript + Vite             | `[OBSERVED]` frontend/package.json       |
| State             | Zustand                               | `[OBSERVED]` frontend/src/api/store.ts:1 |
| Charts            | Recharts (via Victory/D3)             | `[OBSERVED]` frontend/package.json       |
| Reports           | ReportLab + Matplotlib                | `[OBSERVED]` backend/report_generator.py |
| AI Scoring        | OpenAI GPT-4o-mini                    | `[OBSERVED]` backend/ai_scoring.py       |
| Hosting           | Railway (both services)               | `[OBSERVED]` backend/railway.json        |

### 2.2 Database Schema — 12 Tables

`[OBSERVED]` backend/models.py

| Table                 | Purpose                | Key Fields                                                                                         |
|-----------------------|------------------------|----------------------------------------------------------------------------------------------------|
| `users`               | Auth & identity        | email, hashed_password, role (admin/auditor/client)                                                |
| `assessments`         | Audit engagements      | client_name, site_name, industry, asset_class, site_criticality, status                            |
| `assessment_auditors` | Team assignments (M:N) | role_in_audit (Lead/Technical/Observer)                                                            |
| `question_bank`       | Master question repo   | question_code, pillar, subcategory, target_role, question_type, weight, scoring_logic, is_critical |
| `question_responses`  | Answers + evidence     | response_value, numeric_score, is_draft, is_na, evidence_provided                                  |
| `observations`        | Field observations     | observation_type, pass_fail_result, severity, pillar, subcategory                                  |
| `data_analyses`       | CMMS metric results    | analysis_type, metrics (JSON), sample_size                                                         |
| `evidence`            | File attachments       | evidence_type, file_path (linked to responses/observations/analyses)                               |
| `scores`              | Calculated RMI scores  | pillar, raw_score, weighted_score, final_score, confidence_level                                   |
| `reports`             | Generated PDFs         | report_type, content (JSON), file_path                                                             |
| `iso14224_audits`     | ISO compliance checks  | check_item, check_category, passed, impact_on_score                                                |

---

## 3. RMI Framework — Current State

### 3.1 Pillar Structure

`[OBSERVED]` backend/models.py:18-22

```
PillarType (enum):
  PEOPLE
  PROCESS
  TECHNOLOGY
```

**Three pillars, equal weight.** No formal sub-pillar taxonomy beyond the `subcategory` free-text field on each question.

### 3.2 Question Bank

`[OBSERVED]` backend/question_bank.py:1-397

**Total Questions:** 16 (hardcoded in `seed_question_bank()`)

| Pillar     | Code Range     | Count | Subcategories                                                                                                              |
|------------|----------------|-------|----------------------------------------------------------------------------------------------------------------------------|
| People     | P-01 to P-05   | 5     | Competency, Reactive Reality, Empowerment, Knowledge Management, Investment in Competency                                  |
| Process    | PR-01 to PR-05 | 5     | Work Execution, SOP Usage, Safety Compliance, Planning Quality, PM Discipline                                              |
| Technology | T-01 to T-06   | 6     | Data Graveyard Detection, ISO 14224 Compliance, Reporting Capability, System Usability, Data Structure, Information Access |

### 3.3 Question Types

`[OBSERVED]` backend/models.py:25-31

| Type          | Enum              | Usage                    |
|---------------|-------------------|--------------------------|
| LIKERT        | 1-5 scale         | P-01, P-02, T-04, T-06   |
| BINARY        | Yes/No            | P-03, P-05, PR-03, T-02  |
| MULTI_SELECT  | Check options     | P-04                     |
| DATA_INPUT    | Numeric/%         | PR-04, PR-05, T-01, T-05 |
| OBSERVATIONAL | Field observation | PR-01, PR-02, T-03       |

### 3.4 Target Roles

`[OBSERVED]` backend/models.py:34-40

| Role       | Enum           | Weight |
|------------|----------------|--------|
| TECHNICIAN | Ground truth   | 60%    |
| SUPERVISOR | Middle layer   | 10%    |
| MANAGER    | Intent layer   | 20%    |
| PLANNER    | Planning layer | 10%    |
| AUDITOR    | Verification   | 20%    |

`[OBSERVED]` backend/scoring_engine.py:44-50 — Note: weights sum to **120%** (technician 60% + supervisor 10% + manager 20% + planner 10% + auditor 20%). This is because `combined_weight = role_weight * question_weight`, and the denominator normalizes.

### 3.5 Maturity Scale

`[OBSERVED]` backend/scoring_engine.py:400-410

| Level | Score Range | Label               |
|-------|-------------|---------------------|
| 1     | < 2.0       | Reactive            |
| 2     | 2.0–2.99    | Emerging Preventive |
| 3     | 3.0–3.99    | Preventive          |
| 4     | 4.0–4.49    | Predictive          |
| 5     | ≥ 4.5       | Prescriptive        |

---

## 4. Scoring Engine — Current Logic

`[OBSERVED]` backend/scoring_engine.py:1-800

### 4.1 Score Calculation Flow

```
Interview Score (80%)
  ├── For each response: numeric_score × role_weight × question_weight
  ├── Evidence Lock: scores ≥ 4 without evidence → capped at 3
  └── Divided by total weight (normalized)

Observation Score (20%)
  ├── Pass = 5 points, Fail = 1 point
  └── Average of all observations

CMMS Score (Technology pillar only, replaces part of weight)
  ├── Reactive Ratio → 1-5
  ├── PM Compliance → 1-5
  └── Data Quality → 1-5

Combined Score:
  ├── Standard: Interview(80%) + Observations(20%)
  ├── Technology w/ CMMS: Interview(60%) + Observations(20%) + CMMS(20%)
  └── Apply Weakest Link caps

Final Adjustments:
  ├── Critical failure (score ≤ 2) → cap pillar at 3.0
  ├── Safety observation failure → cap Process at 3.0
  └── CMMS quality < 2.0 → cap Technology at 3.5

Overall RMI = Average(People, Process, Technology)
```

### 4.2 Advanced Analytics (Strategic Evolution)

`[OBSERVED]` backend/scoring_engine.py:450-800

| Feature                 | Implementation                                                              | Status      |
|-------------------------|-----------------------------------------------------------------------------|-------------|
| Confidence Variance     | Std dev across roles per question; flags SD > 1.5 as "cultural disconnect"  | Implemented |
| Maturity Velocity       | Δ RMI / months since previous assessment; flags regression from high scores | Implemented |
| ISO 55001 Gap Analysis  | Maps questions to ISO clauses; scores ≤ 2 flagged as gaps                   | Implemented |
| Risk-Adjusted Weighting | site_criticality multiplier (1.0-2.0) for high-risk industries              | Implemented |

### 4.3 AI Scoring

`[OBSERVED]` backend/ai_scoring.py

- Uses OpenAI GPT-4o-mini for narrative text responses
- Returns 1-5 score + rationale + confidence
- Cost: ~$0.002 per evaluation
- Optional (requires `OPENAI_API_KEY`)

---

## 5. Frontend Architecture

### 5.1 Route Map

`[OBSERVED]` frontend/src/App.tsx

| Route                          | View                     | Purpose                                 |
|--------------------------------|--------------------------|-----------------------------------------|
| `/login`                       | Login.tsx                | JWT authentication                      |
| `/`                            | Dashboard.tsx            | Assessment list, create new             |
| `/assessment/:id`              | AssessmentDetail.tsx     | Pillar tabs, scoring, report generation |
| `/assessment/:id/interview`    | InterviewInterface.tsx   | Question-by-question flow               |
| `/assessment/:id/observations` | ObservationChecklist.tsx | Field observation entry                 |
| `/users`                       | UserManagement.tsx       | Admin user CRUD                         |

### 5.2 State Management

`[OBSERVED]` frontend/src/api/store.ts — Zustand store for auth state only. No global state for assessment data; fetched per-view via Axios.

### 5.3 Offline Capability

`[OBSERVED]` frontend/src/api/client.ts:17-65

- Offline queue for POST/PUT/PATCH requests (localStorage)
- Auto-sync when connection restored
- Network error detection (`ERR_NETWORK`)

---

## 6. API Surface

`[OBSERVED]` backend/main.py

### 6.1 Endpoints (26 routes)

| Group        | Endpoints                                                             | Auth        |
|--------------|-----------------------------------------------------------------------|-------------|
| Auth         | POST `/token`, POST `/users`, GET `/users/me`                         | Public/JWT  |
| Assessments  | CRUD `/assessments`, `/assessments/{id}`                              | JWT         |
| Questions    | GET `/questions`, GET `/assessments/{id}/questions`                   | JWT         |
| Responses    | GET/POST `/assessments/{id}/responses`                                | JWT         |
| Observations | GET/POST `/assessments/{id}/observations`, POST `/observations/batch` | JWT         |
| Scoring      | POST `/assessments/{id}/calculate-scores`                             | JWT         |
| Reports      | POST `/assessments/{id}/generate-report`, GET `/report/download`      | JWT         |
| CMMS         | POST `/assessments/{id}/upload-cmms`                                  | JWT         |
| ISO 14224    | POST `/assessments/{id}/validate-iso14224`                            | JWT         |
| Admin        | GET/DELETE `/users`, POST `/seed-questions`                           | JWT (admin) |

---

## 7. Report Generation

`[OBSERVED]` backend/report_generator.py (960 lines)

- ReportLab-based PDF generation
- Radar chart via Matplotlib (temp_radar.png)
- Sections: Cover, Executive Summary, Pillar Details, Recommendations, Roadmap
- Evidence appendix
- ISO 55001 gap analysis table

---

## 8. Data Flows

```
User Input → QuestionResponse → ScoringEngine → Score → ReportGenerator → PDF
                                      ↑
                 Observations ────────┘
                 CMMS Upload → DataAnalysis ──┘
                 ISO 14224 Validation ────────┘
```

---

## 9. Key Observations & Gaps

| #  | Observation                                                          | Severity | Evidence                                                         |
|----|----------------------------------------------------------------------|----------|------------------------------------------------------------------|
| 1  | Only 16 questions — insufficient depth for rigorous audit            | HIGH     | `[OBSERVED]` question_bank.py has exactly 16 question dicts      |
| 2  | No sub-pillar taxonomy — `subcategory` is free-text, not enforced    | MEDIUM   | `[OBSERVED]` models.py:146 — `subcategory = Column(String(100))` |
| 3  | Role weights sum to 120% — no obvious bug but normalization masks it | LOW      | `[OBSERVED]` scoring_engine.py:44-50                             |
| 4  | No industry modules — single framework for all verticals             | HIGH     | `[OBSERVED]` No industry-specific question routing exists        |
| 5  | No benchmarking — no peer comparison or percentile engine            | HIGH     | `[INFERRED]` No benchmark tables or comparison logic found       |
| 6  | No assessment modes — no QuickScan vs DeepDive routing               | HIGH     | `[OBSERVED]` All 16 questions always presented                   |
| 7  | Maturity level 4 band is only 0.5 wide (4.0-4.49) vs 1.0 for others  | MEDIUM   | `[OBSERVED]` scoring_engine.py:400-410                           |
| 8  | No practice library — no prescriptive "do this to level up" guidance | HIGH     | `[INFERRED]` No practice/recommendation catalog found            |
| 9  | No calibration protocol — no inter-rater reliability mechanism       | HIGH     | `[INFERRED]` No calibration logic found                          |
| 10 | Evidence lock only caps at 3, doesn't reject submission              | MEDIUM   | `[OBSERVED]` scoring_engine.py:193                               |

---

*End of As-Is Specification*
