# 11 — Calibration Protocol

**Document ID:** RMI-VNEXT-11  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** Auditor Training · Quality Assurance · Product

---

## 1. Purpose

Calibration ensures **inter-rater reliability (IRR)** — that two different auditors scoring the same site would produce the same result within acceptable variance. The target: **IRR ≥ 0.80 (Cohen's weighted kappa)**.

### 1.1 Why Calibration Matters

- v1 has no calibration protocol [INFERRED from absence in codebase]
- Without calibration, scoring is subjective — one auditor's "3" is another's "4"
- Clients who compare scores across auditors get inconsistent results
- Regulatory and ISO contexts require demonstrable scoring consistency

---

## 2. Calibration Framework

### 2.1 Calibration Levels

| Level                      | Who                      | When                    | Method                         |
|----------------------------|--------------------------|-------------------------|--------------------------------|
| **Initial Certification**  | New auditors             | Before first assessment | 3-day training + scored exam   |
| **Ongoing Calibration**    | All active auditors      | Quarterly               | Calibration exercise (2 hours) |
| **Re-Certification**       | Auditors with IRR < 0.75 | As needed               | 1-day refresher + re-exam      |
| **Annual Recertification** | All auditors             | Annually                | Full-day calibration workshop  |

### 2.2 Calibration Exercise Structure

Each calibration exercise uses **standardized case studies** with predetermined "gold standard" scores:

```
EXERCISE STRUCTURE:
1. Present case study (written scenario + evidence artifacts)
2. Auditor independently scores 10-15 questions
3. Compare auditor scores to gold standard
4. Calculate deviation and IRR
5. Facilitated discussion on divergent scores
6. Re-score any items with deviation > 1 point
7. Record final calibration score
```

### 2.3 Case Study Design

| Case Study Component  | Content                                |
|-----------------------|----------------------------------------|
| Site Description      | Industry, size, organizational context |
| Interview Transcripts | Simulated responses from each role     |
| Evidence Package      | Photos, CMMS screenshots, documents    |
| Observation Notes     | Structured field observation data      |
| CMMS Data Extract     | PM compliance, WO data, failure codes  |

Minimum **6 case studies** maintained in the calibration library, rotated annually.

---

## 3. Inter-Rater Reliability Measurement

### 3.1 Cohen's Weighted Kappa

```
FUNCTION calculate_irr(auditor_scores, gold_standard_scores):
    // Cohen's weighted kappa for ordinal data (1-5 scale)
    // Weights: linear (default) or quadratic
    
    observed_agreement = weighted_agreement(auditor_scores, gold_standard_scores)
    chance_agreement = weighted_chance_agreement(score_distribution)
    
    kappa = (observed_agreement - chance_agreement) / (1 - chance_agreement)
    
    RETURN kappa
```

### 3.2 IRR Interpretation

| Kappa     | Interpretation      | Action                                             |
|-----------|---------------------|----------------------------------------------------|
| < 0.40    | Poor agreement      | Fail — complete retraining required                |
| 0.40-0.59 | Moderate agreement  | Conditional pass — additional mentored assessments |
| 0.60-0.74 | Good agreement      | Pass — may audit with senior mentor                |
| 0.75-0.89 | Very good agreement | Pass — certified to audit independently            |
| ≥ 0.90    | Excellent agreement | Pass — eligible to become calibration trainer      |

**Minimum threshold for certification: κ ≥ 0.75**

### 3.3 Deviation Analysis

For each question, track:

```json
{
    "question_id": "WM.1-01",
    "gold_standard_score": 3,
    "auditor_score": 4,
    "deviation": 1,
    "direction": "over-scoring",
    "auditor_justification": "They have a scheduling meeting",
    "gold_standard_rationale": "Meeting exists but <50% attendance and no formal agenda — does not meet Level 4 criteria of data-driven scheduling"
}
```

### 3.4 Common Calibration Failures

| Failure Pattern      | Description                                                   | Correction                                           |
|----------------------|---------------------------------------------------------------|------------------------------------------------------|
| **Halo Effect**      | Rating everything high because overall impression is positive | Train on independent subdomain scoring               |
| **Central Tendency** | Avoiding extremes, clustering all scores at 3                 | Practice with Level 1 and Level 5 case studies       |
| **Leniency Bias**    | Consistently scoring 0.5-1.0 above gold standard              | Emphasize observable indicators, not aspirations     |
| **Severity Bias**    | Consistently scoring 0.5-1.0 below gold standard              | Review evidence acceptance criteria                  |
| **Recency Bias**     | Last interview dominates entire subdomain score               | Structured scoring after each interview, before next |
| **Affinity Bias**    | Higher scores for relatable/likeable respondents              | Blind scoring exercise (text only, no personal info) |

---

## 4. Auditor Certification Program

### 4.1 Certification Requirements

| Requirement             | Detail                                                                     |
|-------------------------|----------------------------------------------------------------------------|
| **Prerequisites**       | 5+ years maintenance/reliability experience OR relevant engineering degree |
| **Training**            | 3-day RMI vNext Auditor Training (classroom + virtual)                     |
| **Exam**                | Written exam (70% minimum) + practical scoring exercise (κ ≥ 0.75)         |
| **Mentored Assessment** | Complete 1 assessment with certified senior auditor                        |
| **Ongoing**             | Quarterly calibration exercises; annual recertification                    |

### 4.2 Certification Levels

| Level                 | Requirements                                     | Privileges                                  |
|-----------------------|--------------------------------------------------|---------------------------------------------|
| **Associate Auditor** | Training + exam passed                           | May audit with a Lead Auditor               |
| **Lead Auditor**      | 3+ completed assessments + κ ≥ 0.80              | May lead Standard assessments independently |
| **Senior Auditor**    | 10+ assessments + κ ≥ 0.85 + 2+ industries       | May lead DeepDive; may mentor Associates    |
| **Master Auditor**    | 25+ assessments + κ ≥ 0.90 + calibration trainer | Creates case studies; trains other auditors |

### 4.3 Certification Revocation

| Trigger                                                      | Action                              |
|--------------------------------------------------------------|-------------------------------------|
| IRR drops below 0.70 in two consecutive calibrations         | Suspended; retraining required      |
| Client complaint verified as scoring error                   | Investigation; potential retraining |
| Failure to complete quarterly calibration                    | Suspended until completed           |
| Ethical violation (fabricating evidence, score manipulation) | Permanent revocation                |

---

## 5. Calibration Exercise Database

### 5.1 Exercise Types

| Type                           | Duration | Questions                      | Use Case                      |
|--------------------------------|----------|--------------------------------|-------------------------------|
| **Quick Check**                | 30 min   | 5 questions from 1 subdomain   | Monthly self-check            |
| **Standard Exercise**          | 2 hours  | 15 questions across 3 domains  | Quarterly calibration         |
| **Full Assessment Simulation** | 4 hours  | 30+ questions all domains      | Annual recertification        |
| **Industry-Specific**          | 2 hours  | 15 questions + industry module | Industry certification add-on |

### 5.2 Exercise Content Rotation

```
Quarter 1: Case Study A (Manufacturing, Large, Level 2-3)
Quarter 2: Case Study B (Food & Beverage, Medium, Level 3-4)
Quarter 3: Case Study C (Oil & Gas, Large, Level 1-2)
Quarter 4: Case Study D (Pharmaceutical, Small, Level 4-5)

Annual Recertification: Case Study E or F (new, unseen)
```

### 5.3 Gold Standard Development

Gold standard scores are established by:

1. **3+ Master Auditors** independently score the case study
2. **Consensus meeting** resolves any deviations > 1 point
3. **Rationale documented** for every score
4. **External review** by Subject Matter Expert (industry-specific)
5. **Locked** as gold standard with version control

---

## 6. Technology Support

### 6.1 Calibration Module (Platform Feature)

```
Auditor Portal → Calibration Center

Features:
├── My Calibration Status
│   ├── Current IRR score
│   ├── Certification level & expiry
│   └── Next calibration due date
├── Take Exercise
│   ├── Quick Check (self-paced)
│   ├── Scheduled Calibration (timed, proctored)
│   └── Practice Mode (with instant feedback)
├── Results History
│   ├── Score trends over time
│   ├── Question-level deviation analysis
│   └── Bias pattern detection
└── Calibration Admin (Master Auditors only)
    ├── Create/edit case studies
    ├── Manage gold standards
    └── Review auditor performance
```

### 6.2 API Endpoints

```
POST /api/v2/calibration/exercises/{exercise_id}/submit
{
    "auditor_id": "uuid",
    "responses": [
        { "question_id": "WM.1-01", "score": 3, "justification": "..." },
        // ...
    ]
}

GET /api/v2/calibration/auditors/{auditor_id}/status
Response:
{
    "certification_level": "Lead Auditor",
    "current_irr": 0.82,
    "last_calibration": "2025-01-15",
    "next_calibration_due": "2025-04-15",
    "exercises_completed": 8,
    "bias_pattern": "slight_leniency",
    "recommendation": "Focus on evidence requirements for Level 4-5 scoring"
}
```

---

## 7. Continuous Improvement

### 7.1 Calibration Metrics Dashboard

| Metric                                   | Target            | Current (launch) |
|------------------------------------------|-------------------|------------------|
| Average auditor IRR                      | ≥ 0.80            | N/A (baseline)   |
| % auditors certified                     | 100% of active    | N/A              |
| Quarterly calibration completion rate    | >95%              | N/A              |
| Average question deviation               | < 0.5 points      | N/A              |
| Cross-auditor score variance (same site) | < 0.3 overall RMI | N/A              |

### 7.2 Question Difficulty Analysis

Track which questions have highest calibration variance:

```
High-Variance Questions (candidates for rubric improvement):
- WC.3-02 (knowledge transfer) — κ = 0.62 — RUBRIC NEEDS CLARIFICATION
- LC.1-03 (management commitment) — κ = 0.65 — ADD OBSERVABLE INDICATORS
- SG.3-01 (RCA process) — κ = 0.68 — CLARIFY LEVEL 3 vs LEVEL 4 BOUNDARY
```

Questions consistently causing calibration failures get rubric revisions.

---

*End of Calibration Protocol*
