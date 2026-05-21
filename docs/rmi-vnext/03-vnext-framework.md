# 03 — RMI vNext Framework Architecture

**Document ID:** RMI-VNEXT-03  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** VP of Reliability · Principal Consultant · Product

---

## 1. Design Philosophy

> "Measure what matters. Prescribe what works. Prove it with evidence."

RMI vNext replaces the flat 3-pillar / 16-question model with a **two-layer architecture**: a Universal Core that works across all industries, plus pluggable Industry Modules that add regulatory and vertical-specific depth.

**Design Principles:**
1. **Evidence over opinion** — every score must trace to an artifact
2. **Prescriptive, not descriptive** — every gap maps to a concrete practice
3. **Scalable by design** — QuickScan (15 min) to DeepDive (3 days) from the same question bank
4. **Commercially tiered** — freemium QuickScan → paid Standard → premium DeepDive

---

## 2. Framework Hierarchy

### 2.1 Two-Layer Model

```
┌─────────────────────────────────────────────────────┐
│                  UNIVERSAL CORE                      │
│  5 Domains × 3 Subdomains = 15 Assessment Areas     │
│  ~150 Questions (all industries)                     │
├─────────────────────────────────────────────────────┤
│              INDUSTRY MODULES (Plug-in)              │
│  +20-40 questions per vertical                       │
│  Regulatory compliance overlays                      │
│  Industry-specific benchmarks                        │
└─────────────────────────────────────────────────────┘
```

### 2.2 Universal Core — 5 Domains

The three v1 pillars expand to **five domains** — splitting "People" into Workforce and Leadership, and adding a Strategy & Governance domain.

| # | Domain                    | Code | v1 Mapping       | Rationale                                             |
|---|---------------------------|------|------------------|-------------------------------------------------------|
| 1 | **Workforce Capability**  | WC   | People (partial) | Technician skills, training, knowledge transfer       |
| 2 | **Leadership & Culture**  | LC   | People (partial) | Management commitment, safety culture, empowerment    |
| 3 | **Work Management**       | WM   | Process          | Planning, scheduling, execution, PM discipline        |
| 4 | **Asset Information**     | AI   | Technology       | CMMS quality, data integrity, analytics capability    |
| 5 | **Strategy & Governance** | SG   | (NEW)            | Asset management policy, KPIs, continuous improvement |

### 2.3 Subdomain Structure (3 per Domain)

| Domain                       | Subdomain 1                  | Subdomain 2                            | Subdomain 3                       |
|------------------------------|------------------------------|----------------------------------------|-----------------------------------|
| **WC** Workforce Capability  | WC.1 Technical Competency    | WC.2 Training & Development            | WC.3 Knowledge Management         |
| **LC** Leadership & Culture  | LC.1 Management Commitment   | LC.2 Safety & Reliability Culture      | LC.3 Organizational Structure     |
| **WM** Work Management       | WM.1 Planning & Scheduling   | WM.2 Preventive/Predictive Maintenance | WM.3 Work Execution & Quality     |
| **AI** Asset Information     | AI.1 CMMS/EAM Effectiveness  | AI.2 Data Quality & Integrity          | AI.3 Analytics & Decision Support |
| **SG** Strategy & Governance | SG.1 Asset Management Policy | SG.2 Performance Measurement           | SG.3 Continuous Improvement       |

### 2.4 Question Distribution Target

| Tier      | Mode           | Duration  | Questions                   | Coverage                |
|-----------|----------------|-----------|-----------------------------|-------------------------|
| QuickScan | Self-service   | 15-30 min | 15 (1 per subdomain)        | Pulse check             |
| Standard  | Consultant-led | 1-2 days  | 60-75                       | Full subdomain coverage |
| DeepDive  | Audit team     | 3-5 days  | 150+ core + industry module | Full evidence audit     |

---

## 3. Industry Modules

### 3.1 Module Architecture

Each Industry Module is a JSON overlay that:
- Adds 20-40 industry-specific questions mapped to subdomains
- Overrides scoring weights for industry-relevant subdomains
- Adds regulatory compliance checks
- Provides industry-specific benchmark data
- Includes vertical-specific practice library entries

### 3.2 Initial Module Roadmap

| Priority | Module                  | Code | Regulatory Overlay         | Target Market                |
|----------|-------------------------|------|----------------------------|------------------------------|
| P0       | Manufacturing (General) | MFG  | OSHA, ISO 55001            | Default / widest market      |
| P1       | Food & Beverage         | FNB  | FDA 21 CFR, FSMA, SQF, BRC | Rise Baking, current clients |
| P2       | Oil & Gas               | ONG  | API 580/581, OSHA PSM      | High-value engagements       |
| P3       | Mining & Metals         | MNM  | MSHA, ISO 17359            | Heavy industry               |
| P4       | Utilities / Power       | UTL  | NERC CIP, IEEE             | Regulated infrastructure     |
| P5       | Pharmaceutical          | PHA  | FDA cGMP, 21 CFR Part 211  | High-compliance vertical     |

### 3.3 Module Data Structure

```json
{
  "module_id": "FNB",
  "module_name": "Food & Beverage",
  "version": "1.0",
  "regulatory_frameworks": ["FDA 21 CFR", "FSMA", "SQF", "BRC"],
  "weight_overrides": {
    "WM.2": 1.3,
    "LC.2": 1.5
  },
  "questions": [
    {
      "question_code": "FNB-01",
      "subdomain": "WM.2",
      "question_text": "Are PM tasks on food-contact surfaces documented with sanitation sign-off?",
      "regulatory_reference": "21 CFR 117.35",
      "question_type": "BINARY",
      "weight": 1.5,
      "is_critical": true
    }
  ],
  "benchmarks": {
    "p25": 2.1,
    "p50": 2.8,
    "p75": 3.4,
    "p90": 4.1
  }
}
```

---

## 4. Maturity Scale — Rebalanced

### 4.1 Five-Level Model (Equal Bands)

| Level | Score Range | Label           | Defining Characteristic                                |
|-------|-------------|-----------------|--------------------------------------------------------|
| 1     | 1.00 – 1.99 | **Reactive**    | Firefighting. No formal maintenance strategy.          |
| 2     | 2.00 – 2.99 | **Planned**     | Basic PM exists but inconsistent execution.            |
| 3     | 3.00 – 3.59 | **Proactive**   | Systematic PM/PdM with evidence-based decisions.       |
| 4     | 3.60 – 4.29 | **Optimized**   | Data-driven decisions. Continuous improvement culture. |
| 5     | 4.30 – 5.00 | **World-Class** | Prescriptive. Industry benchmark. ISO 55001 aligned.   |

**Change from v1:** Level 4 band expanded from 0.5 to 0.7 points. Level 5 threshold raised from 4.5 to 4.3 (broader but still elite). Level 3 label changed from "Preventive" to "Proactive" to encompass PdM adoption.

### 4.2 Maturity Descriptors Per Domain

Each domain gets a **maturity descriptor matrix** — a 5×5 grid showing what each level looks like in each subdomain. This is the backbone of the Practice Library (doc 09).

---

## 5. Question Taxonomy

### 5.1 Question Schema (vNext)

Every question in the bank carries these metadata fields:

| Field                | Type    | Purpose                                                                 |
|----------------------|---------|-------------------------------------------------------------------------|
| `question_id`        | UUID    | Globally unique identifier                                              |
| `question_code`      | String  | Human-readable code (e.g., WC.1-03)                                     |
| `domain`             | Enum    | One of 5 domains                                                        |
| `subdomain`          | String  | e.g., "WC.1"                                                            |
| `question_text`      | String  | The actual question                                                     |
| `question_type`      | Enum    | LIKERT / BINARY / MULTI_SELECT / DATA_INPUT / OBSERVATIONAL / NARRATIVE |
| `target_role`        | Enum    | TECHNICIAN / SUPERVISOR / MANAGER / PLANNER / AUDITOR                   |
| `assessment_mode`    | Array   | ["quickscan", "standard", "deepdive"]                                   |
| `weight`             | Float   | Scoring weight within subdomain                                         |
| `is_critical`        | Boolean | Triggers weakest-link cap                                               |
| `evidence_required`  | Boolean | Must provide artifact for scores ≥ 4                                    |
| `evidence_guidance`  | String  | What constitutes acceptable evidence                                    |
| `scoring_rubric`     | Object  | Level 1-5 descriptors                                                   |
| `iso_55001_clause`   | String  | ISO 55001:2024 clause reference                                         |
| `industry_modules`   | Array   | Which modules include this question                                     |
| `calibration_anchor` | String  | Reference scenario for calibration exercises                            |
| `practice_link`      | String  | ID of linked practice in Practice Library                               |
| `data_source`        | String  | Where to find the answer (CMMS, interview, observation)                 |
| `benchmark_category` | String  | Category for benchmark comparison                                       |

### 5.2 Question Naming Convention

```
{Domain}.{Subdomain#}-{Sequential##}[-{IndustryModule}]

Examples:
  WC.1-01       → Workforce Capability, Technical Competency, Question 1 (Core)
  WM.2-07       → Work Management, PM/PdM, Question 7 (Core)
  WM.2-07-FNB   → Same question with Food & Beverage overlay
  AI.2-03       → Asset Information, Data Quality, Question 3 (Core)
```

---

## 6. Assessment Modes

### 6.1 Mode Definitions

| Mode          | Trigger                | Duration  | Assessor                          | Output                                   |
|---------------|------------------------|-----------|-----------------------------------|------------------------------------------|
| **QuickScan** | Self-service or Tier 1 | 15-30 min | Client (unattended) or consultant | Pulse Score + Domain Radar               |
| **Standard**  | Tier 2 engagement      | 1-2 days  | 1-2 consultants                   | Full Report + Roadmap                    |
| **DeepDive**  | Tier 3 / ISO alignment | 3-5 days  | Audit team (2-4)                  | Audit Report + Practice Plan + Benchmark |

### 6.2 Mode → Question Routing

See 06-routing-rules.md for complete routing logic.

---

## 7. Commercial Model

### 7.1 Tiered Pricing Architecture

| Tier       | Product            | RMI Mode                  | Price Point         | Delivery                       |
|------------|--------------------|---------------------------|---------------------|--------------------------------|
| Free       | QuickScan          | QuickScan                 | $0                  | Self-service web app           |
| Tier 1     | The Audit          | Standard                  | $5,000–$15,000      | Consultant-led, 1-2 days       |
| Tier 2     | The Transformation | DeepDive + Roadmap        | $25,000–$75,000     | Audit team, 3-5 days + roadmap |
| Tier 3     | The Pilot          | DeepDive + Implementation | $75,000–$250,000    | Multi-month engagement         |
| Enterprise | Portfolio License  | All modes, multi-site     | Annual subscription | Dedicated platform instance    |

### 7.2 Freemium Funnel

```
QuickScan (Free) → "Your RMI is 2.4 — here's what Level 3 looks like"
    ↓
Standard Audit (Tier 1) → "Deep assessment reveals these 12 gaps"
    ↓
Transformation (Tier 2) → "Here's the 18-month roadmap"
    ↓
Pilot (Tier 3) → "We'll implement the first 3 practices with you"
    ↓
Enterprise License → "Your 20 sites managed in one dashboard"
```

---

## 8. Data Architecture (vNext)

### 8.1 New Entities

| Entity             | Purpose                            | Relationship                  |
|--------------------|------------------------------------|-------------------------------|
| `domains`          | Enforced 5-domain taxonomy         | Parent of subdomains          |
| `subdomains`       | 15 formal subdomains               | Parent of questions           |
| `industry_modules` | Module definitions                 | Links to questions            |
| `module_questions` | Module-specific question overrides | M:N with question_bank        |
| `practices`        | Practice Library entries           | Linked to subdomain + level   |
| `benchmarks`       | Industry benchmark data            | Keyed by industry + subdomain |
| `calibration_sets` | Calibration exercise scenarios     | Linked to questions           |
| `site_groups`      | Multi-site portfolios              | Parent of assessments         |
| `assessment_modes` | Mode configuration                 | Linked to assessments         |

### 8.2 Migration Path

See 13-migration-plan.md for v1 → vNext data migration strategy.

---

## 9. Key Design Decisions

| # | Decision                                | Rationale                                                                                                           |
|---|-----------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| 1 | 5 domains instead of 3 pillars          | People split into Workforce + Leadership enables targeted improvement. Strategy domain ensures ISO 55001 alignment. |
| 2 | 3 subdomains per domain (not 5)         | 15 total subdomains is tractable for scoring. 25 would create analysis paralysis.                                   |
| 3 | Industry Modules as overlays, not forks | Single codebase. Modules add questions and adjust weights, never remove core questions.                             |
| 4 | QuickScan is 1 question per subdomain   | 15 questions = 15-minute self-service. Minimum viable signal per subdomain.                                         |
| 5 | Equal-width maturity bands (mostly)     | Removes v1's compressed Level 4 band. Makes progression feel achievable.                                            |
| 6 | Practice Library as backbone            | Every gap maps to a practice. This is the consulting IP that differentiates NextBelt.                               |
| 7 | Evidence required at ≥ 4 (hard reject)  | vNext upgrades from "silent cap at 3" to "submission blocked without evidence."                                     |
| 8 | Calibration built into framework        | Every question gets a calibration anchor — a reference scenario for inter-rater training.                           |

---

*End of vNext Framework Architecture*
