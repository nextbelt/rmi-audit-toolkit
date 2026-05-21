# 06 — Assessment Routing Rules

**Document ID:** RMI-VNEXT-06  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** Product · Engineering · Auditor Training

---

## 1. Assessment Mode Definitions

| Mode          | Questions        | Duration  | Evidence    | Price Point          | Use Case                                  |
|---------------|------------------|-----------|-------------|----------------------|-------------------------------------------|
| **QuickScan** | 15 (1/subdomain) | 30-45 min | Optional    | Free / Freemium      | Lead gen, self-assessment, health check   |
| **Standard**  | 60-75            | 2-3 days  | Required ≥4 | Paid License         | Annual audit, compliance check            |
| **DeepDive**  | 150+             | 5-10 days | Required ≥3 | Premium / Consulting | Transformation program, M&A due diligence |

---

## 2. QuickScan Routing Logic

### 2.1 Question Selection

QuickScan selects exactly **1 question per subdomain** (15 total). The selected question is tagged `"assessment_modes": ["quickscan", "standard", "deepdive"]` in the question bank — meaning it appears in ALL modes.

**Selection Criteria for QuickScan Questions:**
1. Must be LIKERT type (1-5 scale) for consistent scoring
2. Must have highest predictive correlation with subdomain score
3. Must be answerable without CMMS access or field observation
4. Must be understandable by a Maintenance Manager role

### 2.2 QuickScan Scoring

```
QuickScan Score = Average of 15 subdomain proxy scores
Domain Score = Average of 3 subdomain proxies within domain
Overall RMI = Weighted average of 5 domain scores
```

**Limitations:**
- No evidence verification → scores above 3.5 carry a "confidence warning"
- No weakest-link enforcement → identified but not enforced
- No benchmarking → percentile ranks shown as "estimated range"

### 2.3 QuickScan → Standard Trigger

The QuickScan report includes a "Recommended Next Step" section:

| QuickScan Result | Recommendation                                                                                                                                                |
|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| RMI < 2.0        | "Your organization is in reactive mode. A Standard assessment will identify the 3-5 highest-impact improvements."                                             |
| RMI 2.0-3.0      | "You've built some foundation. A Standard assessment will reveal hidden blockers preventing the leap to proactive maintenance."                               |
| RMI 3.0-4.0      | "Strong fundamentals detected. A Standard assessment with evidence validation will confirm your actual maturity and identify optimization targets."           |
| RMI > 4.0        | "Your self-assessment scores are high. A Standard assessment with evidence verification will validate these claims and benchmark you against industry peers." |

---

## 3. Standard Assessment Routing Logic

### 3.1 Question Selection

Standard mode selects **60-75 questions** using this algorithm:

```
FOR each subdomain (15 total):
    SELECT all questions tagged "standard" (typically 6-7 per subdomain)
    
    IF industry_module is set:
        ADD industry-specific standard questions (1-2 per subdomain)
    
    IF previous_assessment exists:
        BOOST questions where previous score < 3.0 (add 1-2 deepdive questions)
        SKIP questions where previous score = 5.0 AND evidence_verified = true
    
    ENFORCE minimum 4 questions per subdomain
    ENFORCE maximum 8 questions per subdomain (before industry add-ons)
```

### 3.2 Role-Based Routing

Different questions route to different interview targets:

| Target Role          | v1 Weight [OBSERVED: scoring_engine.py:18-24] | vNext Weight | Rationale                                                 |
|----------------------|-----------------------------------------------|--------------|-----------------------------------------------------------|
| TECHNICIAN           | 0.60                                          | 0.35         | Reduced — was over-indexed on single perspective          |
| SUPERVISOR           | 0.10                                          | 0.20         | Increased — critical link between shop floor and planning |
| MANAGER              | 0.20                                          | 0.15         | Slightly reduced — answers tend to be aspirational        |
| PLANNER              | 0.10                                          | 0.15         | Increased — planning is a core competency differentiator  |
| RELIABILITY_ENGINEER | N/A                                           | 0.15         | NEW — dedicated reliability function indicator            |

### 3.3 Standard Scoring

```
Subdomain Score = Weighted_Average(question_scores, role_weights)
    THEN apply evidence_check()
    THEN apply weakest_link()

Domain Score = Average(subdomain_1, subdomain_2, subdomain_3)
    THEN apply domain_weakest_link()

Overall RMI = Weighted_Average(domain_scores, domain_weights)
```

---

## 4. DeepDive Assessment Routing Logic

### 4.1 Question Selection

DeepDive mode includes **ALL 150+ questions** plus:

```
FOR each subdomain:
    SELECT all questions (all modes)
    ADD industry-specific questions (ALL tagged for this industry)
    ADD regulatory compliance questions (if applicable)
    
    IF site has multiple units/lines:
        ENABLE per-unit observation questions
        MULTIPLY observational questions × number of sampled units
    
    TOTAL typically 150-200+ questions depending on industry and site size
```

### 4.2 DeepDive-Specific Features

| Feature                   | Description                                                                                                               |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------|
| **Multi-Unit Sampling**   | Observational questions administered across 3+ production units                                                           |
| **Cross-Role Validation** | Same question asked to different roles; variance > 1.5 = cultural blind spot [INFERRED from v1 confidence_variance logic] |
| **Evidence Deep Review**  | Evidence required for scores ≥ 3 (stricter than Standard)                                                                 |
| **CMMS Data Pull**        | Automated extraction of KPIs (PM compliance, backlog age, MTBF/MTTR)                                                      |
| **Observation Walks**     | Structured gemba walks with standardized checklists                                                                       |
| **Workshop Sessions**     | Facilitated group sessions for Process and Culture subdomains                                                             |

### 4.3 DeepDive Duration Planning

| Site Size              | Expected Duration | Auditor-Days |
|------------------------|-------------------|--------------|
| < 50 maintenance FTE   | 3-5 days          | 6-10         |
| 50-200 maintenance FTE | 5-7 days          | 12-18        |
| 200+ maintenance FTE   | 7-10 days         | 20-30        |

---

## 5. Industry Module Routing

### 5.1 Module Selection

Industry module is selected at assessment creation time:

| Code | Industry                | Additional Questions | Regulatory Focus          |
|------|-------------------------|----------------------|---------------------------|
| MFG  | Manufacturing (General) | +10-15               | ISO 55001, TPM            |
| FNB  | Food & Beverage         | +15-20               | FSMA, GMP, HACCP          |
| ONG  | Oil & Gas               | +15-20               | API, PSM, OSHA 1910.119   |
| MNM  | Mining & Minerals       | +10-15               | MSHA, ISO 17359           |
| UTL  | Utilities               | +10-15               | NERC CIP, FERC            |
| PHA  | Pharmaceuticals         | +15-20               | FDA 21 CFR Part 211, cGMP |

### 5.2 Module Weight Overrides

Industry modules can override default domain weights:

```json
{
  "MFG": { "WC": 0.20, "LC": 0.15, "WM": 0.25, "AI": 0.20, "SG": 0.20 },
  "FNB": { "WC": 0.15, "LC": 0.20, "WM": 0.25, "AI": 0.15, "SG": 0.25 },
  "ONG": { "WC": 0.20, "LC": 0.25, "WM": 0.20, "AI": 0.15, "SG": 0.20 },
  "MNM": { "WC": 0.20, "LC": 0.20, "WM": 0.25, "AI": 0.15, "SG": 0.20 },
  "UTL": { "WC": 0.15, "LC": 0.15, "WM": 0.20, "AI": 0.30, "SG": 0.20 },
  "PHA": { "WC": 0.15, "LC": 0.15, "WM": 0.20, "AI": 0.20, "SG": 0.30 }
}
```

**Rationale:**
- FNB/PHA elevate SG due to regulatory documentation requirements
- ONG elevates LC due to safety culture criticality
- UTL elevates AI due to SCADA/control system data dependency
- MNM elevates WM due to equipment criticality in harsh environments

---

## 6. Adaptive Routing (Future Enhancement)

### 6.1 Real-Time Question Adaptation

In future versions, the routing engine will dynamically adjust:

```
IF subdomain_score_so_far < 2.0 AFTER 3 questions:
    SKIP remaining Level 4-5 diagnostic questions
    ADD Level 1-2 root cause questions
    FLAG subdomain for management interview escalation

IF subdomain_score_so_far > 4.0 AFTER 3 questions:
    SKIP remaining Level 1-2 diagnostic questions
    ADD Level 4-5 differentiation questions
    REQUIRE evidence for current answers before proceeding
```

### 6.2 Skip Logic

```
IF WC.1-01 (trained on equipment) = 1 (No training):
    SKIP WC.1-05 (certification tracking system)
    SKIP WC.1-07 (competency assessment frequency)
    ADD WC.1-08 (barriers to training)

IF AI.1-01 (CMMS adoption) = 1 (No CMMS):
    SKIP ALL AI.1 questions except AI.1-01 and AI.1-02
    SKIP ALL AI.2 data quality questions
    SET AI domain score cap = 1.5
    FLAG: "No CMMS detected — critical blocker for reliability maturity"
```

---

## 7. Mode Transition Rules

### 7.1 Upgrade Path

| From      | To       | Requirements                                                            |
|-----------|----------|-------------------------------------------------------------------------|
| QuickScan | Standard | Purchase Standard license + schedule auditor                            |
| Standard  | DeepDive | Purchase DeepDive license + assign lead auditor + site access agreement |
| QuickScan | DeepDive | Not permitted — must complete Standard first                            |

### 7.2 Data Preservation

When upgrading assessment mode:
- QuickScan answers are **pre-populated** into Standard
- Standard answers are **pre-populated** into DeepDive
- Evidence uploaded in previous modes is **preserved and linked**
- Scores are **recalculated** with the new mode's full question set
- Previous mode report is **archived** (not overwritten)

---

## 8. API Integration Points

### 8.1 Assessment Creation

```
POST /api/v2/assessments
{
    "site_name": "Plant Alpha",
    "industry_module": "MFG",
    "assessment_mode": "standard",
    "target_roles": ["TECHNICIAN", "SUPERVISOR", "MANAGER", "PLANNER", "RELIABILITY_ENGINEER"],
    "previous_assessment_id": null  // or UUID for follow-up
}
```

**Response includes:** Routed question set with ordering, role assignments, and evidence requirements.

### 8.2 Dynamic Re-Routing (Future)

```
POST /api/v2/assessments/{id}/reroute
{
    "completed_responses": [...],
    "trigger": "adaptive"
}
```

**Response:** Updated remaining question set based on scores so far.

---

*End of Assessment Routing Rules*
