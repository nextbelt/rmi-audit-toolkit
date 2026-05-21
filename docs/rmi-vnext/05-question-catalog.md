# 05 — Question Catalog Documentation

**Document ID:** RMI-VNEXT-05  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** VP of Reliability · Auditor Training · Product

---

## 1. Catalog Overview

The RMI vNext Question Bank (04-question-bank.json) contains **150 questions** organized into 5 domains × 3 subdomains. This document explains the design rationale, usage patterns, and maintenance procedures.

---

## 2. Domain & Subdomain Summary

### 2.1 Workforce Capability (WC) — 30 Questions

| Subdomain              | Code | Focus                                               | QuickScan | Standard | DeepDive |
|------------------------|------|-----------------------------------------------------|-----------|----------|----------|
| Technical Competency   | WC.1 | Skills, certifications, equipment-specific training | 1         | 7        | 10       |
| Training & Development | WC.2 | Training programs, budgets, progression paths       | 1         | 7        | 10       |
| Knowledge Management   | WC.3 | Knowledge transfer, documentation, mentoring        | 1         | 7        | 10       |

**Key Signals:** This domain reveals whether the maintenance workforce has the skills and knowledge to execute reliably. QuickScan question WC.1-01 asks technicians directly if they feel trained on their assigned equipment — this single question predicts overall workforce maturity with ~0.7 correlation.

### 2.2 Leadership & Culture (LC) — 30 Questions

| Subdomain                    | Code | Focus                                                    | QuickScan | Standard | DeepDive |
|------------------------------|------|----------------------------------------------------------|-----------|----------|----------|
| Management Commitment        | LC.1 | Budget, staffing, executive sponsorship                  | 1         | 7        | 10       |
| Safety & Reliability Culture | LC.2 | Stop-work authority, near-miss reporting, blame culture  | 1         | 7        | 10       |
| Organizational Structure     | LC.3 | Planner ratios, reporting lines, reliability engineering | 1         | 7        | 10       |

**Key Signals:** LC.2-01 (stop-work authority) is a critical binary question. A "No" answer triggers a weakest-link cap on the entire domain — you cannot claim mature reliability culture if technicians can't stop unsafe work.

### 2.3 Work Management (WM) — 30 Questions

| Subdomain                         | Code | Focus                                              | QuickScan | Standard | DeepDive |
|-----------------------------------|------|----------------------------------------------------|-----------|----------|----------|
| Planning & Scheduling             | WM.1 | Job plans, schedule compliance, backlog management | 1         | 7        | 10       |
| Preventive/Predictive Maintenance | WM.2 | PM optimization, PdM adoption, RCM analysis        | 1         | 7        | 10       |
| Work Execution & Quality          | WM.3 | SOP usage, LOTO compliance, first-time fix rate    | 1         | 7        | 10       |

**Key Signals:** WM.3-03 (LOTO compliance) is a CRITICAL safety item with weight 2.0. Failure automatically caps the Work Management domain at 3.0. This is non-negotiable.

### 2.4 Asset Information (AI) — 30 Questions

| Subdomain                    | Code | Focus                                                 | QuickScan | Standard | DeepDive |
|------------------------------|------|-------------------------------------------------------|-----------|----------|----------|
| CMMS/EAM Effectiveness       | AI.1 | System adoption, mobile access, workflow coverage     | 1         | 7        | 10       |
| Data Quality & Integrity     | AI.2 | Failure codes, closure quality, asset hierarchy depth | 1         | 7        | 10       |
| Analytics & Decision Support | AI.3 | Bad actor reports, dashboards, predictive models      | 1         | 7        | 10       |

**Key Signals:** AI.2 is where the "data graveyard" detection happens. T-01 from v1 (random WO sampling for generic closure codes) maps to AI.2-01 in vNext.

### 2.5 Strategy & Governance (SG) — 30 Questions

| Subdomain               | Code | Focus                                                   | QuickScan | Standard | DeepDive |
|-------------------------|------|---------------------------------------------------------|-----------|----------|----------|
| Asset Management Policy | SG.1 | Written AM policy, ISO 55001 alignment, risk register   | 1         | 7        | 10       |
| Performance Measurement | SG.2 | KPI definitions, OEE tracking, maintenance cost metrics | 1         | 7        | 10       |
| Continuous Improvement  | SG.3 | RCA process, improvement tracking, management review    | 1         | 7        | 10       |

**Key Signals:** SG is entirely NEW in vNext. This domain ensures organizations have the strategic foundation that makes tactical improvements stick. Without SG, sites improve temporarily then regress.

---

## 3. Question Type Distribution

| Type                 | Count | Usage                                |
|----------------------|-------|--------------------------------------|
| LIKERT (1-5)         | ~60   | Self-assessment perception questions |
| BINARY (Yes/No)      | ~25   | Critical compliance checks           |
| DATA_INPUT (numeric) | ~25   | CMMS metrics, percentages            |
| OBSERVATIONAL        | ~20   | Field observation items              |
| MULTI_SELECT         | ~10   | Process maturity indicators          |
| NARRATIVE            | ~10   | Open-ended for AI scoring            |

---

## 4. Scoring Rubric Design Principles

### 4.1 Rubric Construction Rules

Every scoring rubric follows these rules:

1. **Level 1** describes absence or chaos (no process, no documentation, firefighting)
2. **Level 2** describes ad-hoc or inconsistent practice (some effort, no standardization)
3. **Level 3** describes standardized but basic practice (documented, consistent, but not optimized)
4. **Level 4** describes data-driven and measured practice (metrics tracked, decisions evidence-based)
5. **Level 5** describes world-class / prescriptive practice (continuous improvement, benchmarked, industry-leading)

### 4.2 Anchor Examples

Each rubric level uses **observable, concrete indicators** — never vague terms like "good" or "adequate."

❌ Bad: "Level 3: Adequate training program"  
✅ Good: "Level 3: Documented training program with skills matrix covering >70% of critical equipment. Records maintained but no formal competency assessment."

### 4.3 Calibration Anchors

Every question includes a `calibration_anchor` — a brief scenario that trained auditors use to align their scoring. Example:

> "A technician who has 5+ years of experience, no formal certification, but can troubleshoot most issues on their assigned line through tribal knowledge. Score = 2 (experienced but undocumented competence)."

---

## 5. Evidence Guidance

### 5.1 Evidence Requirements by Level

| Score | Evidence Required?          | Guidance                                    |
|-------|-----------------------------|---------------------------------------------|
| 1-3   | Optional but recommended    | Notes, observations, verbal confirmation    |
| 4     | **Required**                | Document, screenshot, photo, or CMMS export |
| 5     | **Required + Verification** | Independent artifact + auditor verification |

### 5.2 Evidence Categories

| Category     | Examples                                                  |
|--------------|-----------------------------------------------------------|
| Documents    | SOPs, training records, competency matrices, AM policies  |
| CMMS Exports | WO reports, PM compliance reports, failure code analyses  |
| Photos       | LOTO application, kitting setup, visual management boards |
| Screenshots  | Dashboard views, report outputs, system configurations    |
| Interviews   | Recorded statements (with consent), meeting minutes       |

---

## 6. Question Lifecycle Management

### 6.1 Version Control

- Questions are versioned with the framework version (e.g., "2.0")
- Retired questions are soft-deleted (`is_active = false`), never hard-deleted
- Question text changes require a new question code (for audit trail)
- Scoring rubric adjustments within a version are tracked with changelog

### 6.2 Adding New Questions

1. Assign question to domain + subdomain
2. Write scoring rubric (5 levels, observable indicators)
3. Define evidence requirements
4. Create calibration anchor
5. Link to Practice Library entry
6. Tag assessment modes
7. Run through calibration exercise with 3+ auditors
8. Achieve IRR ≥ 0.80 before production deployment

### 6.3 Industry Module Questions

Industry-specific questions follow the same lifecycle but are:
- Prefixed with the module code (e.g., `WM.2-07-FNB`)
- Tagged with `industry_modules: ["FNB"]`
- Subject to industry SME review
- Validated against regulatory requirements

---

## 7. Mapping to v1 Questions

| v1 Code | v1 Question                           | vNext Code | vNext Subdomain              |
|---------|---------------------------------------|------------|------------------------------|
| P-01    | Trained on assigned equipment?        | WC.1-01    | Technical Competency         |
| P-02    | Emergency interruptions per week?     | WM.1-02    | Planning & Scheduling        |
| P-03    | Authorized to stop production?        | LC.2-01    | Safety & Reliability Culture |
| P-04    | Knowledge transfer mechanism?         | WC.3-01    | Knowledge Management         |
| P-05    | Training budget line item?            | WC.2-03    | Training & Development       |
| PR-01   | Spare part available immediately?     | WM.3-02    | Work Execution & Quality     |
| PR-02   | SOP referenced during repair?         | WM.3-01    | Work Execution & Quality     |
| PR-03   | LOTO correctly applied?               | WM.3-03    | Work Execution & Quality     |
| PR-04   | % WOs with job plans?                 | WM.1-01    | Planning & Scheduling        |
| PR-05   | PM tasks completed on time?           | WM.2-01    | PM/PdM                       |
| T-01    | Generic closure codes (50 WO sample)? | AI.2-01    | Data Quality & Integrity     |
| T-02    | Failure codes align with ISO 14224?   | AI.2-03    | Data Quality & Integrity     |
| T-03    | Bad Actor report in < 5 min?          | AI.3-01    | Analytics & Decision Support |
| T-04    | CMMS data entry difficulty?           | AI.1-01    | CMMS/EAM Effectiveness       |
| T-05    | Asset hierarchy depth?                | AI.2-02    | Data Quality & Integrity     |
| T-06    | WO attachments accessible?            | AI.1-04    | CMMS/EAM Effectiveness       |

All 16 v1 questions are preserved in vNext with enhanced scoring rubrics and calibration anchors.

---

*End of Question Catalog Documentation*
