# 07 — Scoring Model Specification

**Document ID:** RMI-VNEXT-07  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** Engineering · Data Science · Product

---

## 1. v1 Scoring Architecture (Baseline)

### 1.1 Current Implementation [OBSERVED: scoring_engine.py:1-800]

**Score Aggregation:**
- Interview Score: 80% weight [OBSERVED: scoring_engine.py:~180]
- Observation Score: 20% weight
- Technology Pillar exception: Interview(60%) + Observations(20%) + CMMS(20%)

**Role Weights** [OBSERVED: scoring_engine.py:18-24]:
```python
ROLE_WEIGHTS = {
    'TECHNICIAN': 0.60,
    'SUPERVISOR': 0.10,
    'MANAGER': 0.20,
    'PLANNER': 0.10,
    'AUDITOR': 0.20
}
```

**Maturity Level Boundaries** [OBSERVED: scoring_engine.py:~30-40]:
| Level | Name                | Range      |
|-------|---------------------|------------|
| 1     | Reactive            | < 2.0      |
| 2     | Emerging Preventive | 2.0 – 2.99 |
| 3     | Preventive          | 3.0 – 3.99 |
| 4     | Predictive          | 4.0 – 4.49 |
| 5     | Prescriptive        | ≥ 4.50     |

**Problem:** Levels 4 and 5 share only 1.0 points of range while Level 2 spans 1.0 and Level 3 spans 1.0. Getting from 4.0 to 4.5 (Predictive → Prescriptive) is harder than 2.0 to 3.0 (Emerging → Preventive). The scale is **compressed at the top**.

### 1.2 Evidence Lock [OBSERVED: scoring_engine.py:~200-220]
- Score ≥ 4 without evidence → silently capped at 3
- **Problem:** Silent capping confuses auditors; they enter 5 but see 3 in the report

### 1.3 Weakest-Link Rules [OBSERVED: scoring_engine.py:~250-280]
- Safety observation failure (P-03) → cap Process pillar at 3.0
- CMMS data quality < 2.0 → cap Technology pillar at 3.5
- Critical question failure → cap pillar at 3.0

---

## 2. vNext Scoring Architecture

### 2.1 Rebalanced Maturity Scale

| Level | Name         | Range       | Width | Design Rationale           |
|-------|--------------|-------------|-------|----------------------------|
| 1     | Reactive     | 1.00 – 1.99 | 1.00  | Firefighting, no process   |
| 2     | Emerging     | 2.00 – 2.99 | 1.00  | Some process, inconsistent |
| 3     | Systematic   | 3.00 – 3.59 | 0.60  | Standardized, documented   |
| 4     | Proactive    | 3.60 – 4.29 | 0.70  | Data-driven, measured      |
| 5     | Prescriptive | 4.30 – 5.00 | 0.70  | World-class, optimized     |

**Changes from v1:**
- Level 3 renamed "Preventive" → "Systematic" (reflects process maturity, not just PM type)
- Level 4 renamed "Predictive" → "Proactive" (predictive maintenance is a technique, not a maturity level)
- Top levels rebalanced: L3=0.60, L4=0.70, L5=0.70 (vs v1's L3=1.0, L4=0.50, L5=0.50)
- Mid-range discrimination improved — most organizations cluster in 2.5-3.5 range

### 2.2 Score Hierarchy

```
Question Score (1-5)
    ↓ role_weight × question_weight
Subdomain Score (weighted average of questions in subdomain)
    ↓ evidence_check() → hard reject if score ≥4 without evidence
    ↓ weakest_link() → critical failure caps
Domain Score (average of 3 subdomain scores)
    ↓ domain_weight (default equal or industry-overridden)
Overall RMI (weighted average of 5 domain scores)
    ↓ confidence_interval()
Final RMI ± Confidence Band
```

### 2.3 Role Weights (vNext)

| Role                 | Weight | Change from v1 | Rationale                                                |
|----------------------|--------|----------------|----------------------------------------------------------|
| TECHNICIAN           | 0.35   | ↓ from 0.60    | Still most important, but over-indexing created bias     |
| SUPERVISOR           | 0.20   | ↑ from 0.10    | Bridge role — knows both floor reality and planning gaps |
| MANAGER              | 0.15   | ↓ from 0.20    | Manager responses tend toward aspirational bias          |
| PLANNER              | 0.15   | ↑ from 0.10    | Planning effectiveness is a key maturity differentiator  |
| RELIABILITY_ENGINEER | 0.15   | NEW            | Dedicated RE function indicates organizational maturity  |

**Role absence handling:** If RELIABILITY_ENGINEER role is not present at site, redistribute weight proportionally to PLANNER (0.225) and SUPERVISOR (0.275).

### 2.4 Question Weights

| Weight | Meaning                      | Typical Count |
|--------|------------------------------|---------------|
| 1.0    | Standard question            | ~100          |
| 1.5    | Important differentiator     | ~30           |
| 2.0    | Critical / safety-related    | ~15           |
| 0.5    | Supplementary / nice-to-have | ~5            |

---

## 3. Evidence Enforcement

### 3.1 Hard Reject (Replaces Silent Cap)

**v1 behavior** [OBSERVED: scoring_engine.py:~200-220]: Score ≥ 4 without evidence → silently reduced to 3.  
**vNext behavior:** Score ≥ 4 without evidence → **REJECTED with explicit notification**.

```
FUNCTION evidence_check(response):
    IF response.score >= 4 AND response.evidence IS EMPTY:
        response.status = "PENDING_EVIDENCE"
        response.effective_score = NULL  // Not 3, not anything — unscored
        NOTIFY auditor: "Score of {score} requires evidence. Upload supporting artifact to proceed."
        RETURN BLOCKED
    
    IF response.score == 5 AND response.evidence_verified == FALSE:
        response.status = "PENDING_VERIFICATION"
        response.effective_score = NULL
        NOTIFY auditor: "Score of 5 requires independent verification."
        RETURN BLOCKED
    
    RETURN ACCEPTED
```

### 3.2 Evidence Quality Scoring

| Evidence Grade | Criteria                                                | Score Multiplier |
|----------------|---------------------------------------------------------|------------------|
| A              | Primary artifact (photo, CMMS export, signed document)  | 1.00             |
| B              | Secondary artifact (screenshot, meeting minutes, email) | 0.95             |
| C              | Verbal confirmation only (recorded interview)           | 0.85             |
| D              | Self-reported with no artifact                          | 0.75             |

---

## 4. Weakest-Link Rules (vNext)

### 4.1 Critical Failure Items

| Question                      | Trigger             | Cap Effect           |
|-------------------------------|---------------------|----------------------|
| LC.2-01 (Stop-work authority) | Score = 1 (No)      | Cap LC domain at 2.0 |
| WM.3-03 (LOTO compliance)     | Score ≤ 2           | Cap WM domain at 3.0 |
| AI.1-01 (CMMS adoption)       | Score = 1 (No CMMS) | Cap AI domain at 1.5 |
| SG.1-01 (Written AM policy)   | Score = 1           | Cap SG domain at 2.0 |
| WC.1-01 (Equipment training)  | Score = 1           | Cap WC domain at 2.5 |

### 4.2 Cross-Domain Caps

| Condition       | Cap Effect                   | Rationale                                               |
|-----------------|------------------------------|---------------------------------------------------------|
| AI domain < 2.0 | Cap all other domains at 4.0 | Can't verify maturity claims without data systems       |
| LC domain < 2.0 | Cap WM and WC domains at 3.5 | Poor leadership undermines work management and training |
| SG domain < 2.0 | Cap overall RMI at 3.5       | No strategy = no sustained improvement                  |

### 4.3 Cap Notification

Unlike v1's silent capping, vNext **explicitly notifies** in the report:

```
⚠ DOMAIN CAP APPLIED
Your Work Management domain score of 4.2 has been capped at 3.0 due to 
LOTO compliance (WM.3-03) scoring ≤ 2. Address this critical safety item 
before your next assessment to unlock higher maturity recognition.

RECOMMENDED ACTION: See Practice Library entry WM.3-03-P for LOTO 
program implementation guide.
```

---

## 5. Confidence & Variance Analysis

### 5.1 Cultural Blind Spot Detection [INFERRED from v1 confidence_variance]

When the same question is asked to multiple roles, score variance indicates potential blind spots:

```
FUNCTION cultural_blind_spot(subdomain_responses):
    role_scores = GROUP responses BY role
    variance = STDEV(role_averages)
    
    IF variance > 1.5:
        FLAG "Cultural Blind Spot" on subdomain
        // Manager says 4, Technician says 2 → disconnect
        REDUCE subdomain confidence by 15%
    
    IF variance > 2.0:
        FLAG "Critical Disconnect" on subdomain
        REDUCE subdomain confidence by 30%
        ADD to executive summary as action item
```

### 5.2 Confidence Score Calculation

```
Base Confidence = 100%

DEDUCTIONS:
    - Missing evidence for scored questions: -5% per question
    - Single respondent per role: -10% per role
    - Cultural blind spot (variance > 1.5): -15% per subdomain
    - Critical disconnect (variance > 2.0): -30% per subdomain
    - QuickScan mode (no evidence): -25% base
    - No field observations: -20% base
    - No CMMS data integration: -15% base

Minimum confidence = 30%
```

### 5.3 Confidence Display

```
Your RMI Score: 3.42 ± 0.35 (Confidence: 72%)
Maturity Level: Systematic (Level 3)

Interpretation: Your actual maturity likely falls between 3.07 and 3.77, 
which spans the upper Emerging to lower Proactive range.
```

---

## 6. Domain Weighting

### 6.1 Default Weights (Universal Core)

| Domain | Default Weight | Rationale                            |
|--------|----------------|--------------------------------------|
| WC     | 0.20           | People capability — foundational     |
| LC     | 0.20           | Leadership & culture — enabler       |
| WM     | 0.20           | Work execution — core operations     |
| AI     | 0.20           | Data & systems — enabling technology |
| SG     | 0.20           | Strategy — sustainability            |

Default = equal weighting. No domain is more important than another at the universal level.

### 6.2 Industry Overrides

See [06-routing-rules.md](06-routing-rules.md) §5.2 for industry-specific weight tables.

### 6.3 Custom Weighting (DeepDive Only)

In DeepDive mode, the client organization can request custom domain weights based on strategic priorities:

```
POST /api/v2/assessments/{id}/weights
{
    "custom_weights": {
        "WC": 0.15,
        "LC": 0.25,
        "WM": 0.30,
        "AI": 0.15,
        "SG": 0.15
    },
    "justification": "Safety-critical environment prioritizing culture and work execution"
}
```

**Constraints:**
- All weights must sum to 1.00
- No weight < 0.10 (every domain matters)
- No weight > 0.35 (no single-domain dominance)
- Custom weights require auditor approval
- Report shows BOTH default-weighted and custom-weighted scores

---

## 7. Maturity Velocity

### 7.1 Velocity Calculation [INFERRED from v1 maturity_velocity]

```
FUNCTION maturity_velocity(current_assessment, previous_assessment):
    IF previous_assessment IS NULL:
        RETURN "Baseline — no velocity data"
    
    time_delta = current.date - previous.date  // in months
    score_delta = current.overall_rmi - previous.overall_rmi
    
    velocity = score_delta / (time_delta / 12)  // points per year
    
    RETURN {
        "velocity": velocity,
        "interpretation": interpret_velocity(velocity),
        "by_domain": calculate_domain_velocities()
    }
```

### 7.2 Velocity Interpretation

| Velocity   | Interpretation      | Typical Cause                                  |
|------------|---------------------|------------------------------------------------|
| < -0.5     | Regression          | Staff turnover, budget cuts, leadership change |
| -0.5 to 0  | Stagnation          | No active improvement program                  |
| 0 to 0.3   | Slow improvement    | Incremental changes, organic growth            |
| 0.3 to 0.7 | Healthy improvement | Active reliability program                     |
| 0.7 to 1.0 | Rapid improvement   | Transformation program underway                |
| > 1.0      | Suspicious          | Verify evidence — may indicate gaming          |

---

## 8. ISO 55001 Gap Analysis

### 8.1 Clause Mapping

Every question in the bank maps to one or more ISO 55001 clauses via the `iso_55001_clause` field. The gap analysis report shows:

```
ISO 55001 Clause 6.2.1 (Asset Management Objectives)
    Linked Questions: SG.1-02, SG.2-01, SG.2-03
    Average Score: 2.8
    Gap to Level 3 (Systematic): +0.2 points
    Gap to Level 4 (Proactive): +0.8 points
    
    Recommended Practice: SG.1-02-P (Developing AM Objectives)
```

### 8.2 Certification Readiness Score

```
ISO 55001 Readiness = Percentage of linked questions scoring ≥ 3.0

    < 40%: Not ready — significant foundational gaps
    40-60%: Early stage — address "must-have" clauses first
    60-80%: Getting close — focus on evidence documentation
    > 80%: Certification-ready — engage registrar
```

---

## 9. Scoring Engine API

### 9.1 Calculate Assessment Score

```
POST /api/v2/assessments/{id}/calculate
{
    "include_confidence": true,
    "include_velocity": true,
    "include_iso_gaps": true,
    "custom_weights": null  // or override object
}
```

**Response:**
```json
{
    "overall_rmi": 3.42,
    "confidence": 0.72,
    "confidence_band": [3.07, 3.77],
    "maturity_level": "Systematic",
    "maturity_level_number": 3,
    "domains": {
        "WC": { "score": 3.1, "subdomains": { "WC.1": 2.8, "WC.2": 3.2, "WC.3": 3.3 } },
        "LC": { "score": 3.5, "subdomains": { "LC.1": 3.4, "LC.2": 3.8, "LC.3": 3.3 } },
        "WM": { "score": 3.6, "subdomains": { "WM.1": 3.5, "WM.2": 3.8, "WM.3": 3.5 } },
        "AI": { "score": 3.2, "subdomains": { "AI.1": 3.0, "AI.2": 3.4, "AI.3": 3.2 } },
        "SG": { "score": 3.7, "subdomains": { "SG.1": 3.5, "SG.2": 3.9, "SG.3": 3.7 } }
    },
    "caps_applied": [
        { "type": "weakest_link", "domain": "WM", "question": "WM.3-03", "original": 4.2, "capped": 3.0 }
    ],
    "blind_spots": [
        { "subdomain": "WC.1", "variance": 1.8, "manager_avg": 4.0, "technician_avg": 2.2 }
    ],
    "velocity": { "overall": 0.45, "interpretation": "Healthy improvement" },
    "iso_55001_readiness": 0.62
}
```

---

*End of Scoring Model Specification*
