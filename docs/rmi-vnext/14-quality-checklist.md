# 14 — Quality Checklist

**Document ID:** RMI-VNEXT-14  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** Project Lead · QA · Engineering

---

## 1. Purpose

This checklist validates that all RMI vNext deliverables meet the quality standards defined in the AI Master Prompt. Every item must be verified before declaring the design phase complete.

---

## 2. Deliverable Completeness

| # | Deliverable | File | Created | Reviewed | Notes |
|---|------------|------|---------|----------|-------|
| 01 | As-Is Specification | 01-as-is-spec.md | ✅ | ☐ | All [OBSERVED] claims have path:line refs |
| 02 | Scale Blockers | 02-scale-blockers.md | ✅ | ☐ | 14 blockers: 2 CRITICAL, 7 HIGH, 5 MEDIUM |
| 03 | vNext Framework Architecture | 03-vnext-framework.md | ✅ | ☐ | 5 domains × 3 subdomains |
| 04 | Question Bank JSON | 04-question-bank.json | ✅ | ☐ | 150 questions across 15 subdomains |
| 05 | Question Catalog Documentation | 05-question-catalog.md | ✅ | ☐ | v1→vNext question mapping included |
| 06 | Assessment Routing Rules | 06-routing-rules.md | ✅ | ☐ | QuickScan/Standard/DeepDive logic |
| 07 | Scoring Model Specification | 07-scoring-model.md | ✅ | ☐ | Rebalanced scale, evidence hard-reject |
| 08 | Benchmarking Specification | 08-benchmarking-spec.md | ✅ | ☐ | Percentile engine, peer groups |
| 09 | Practice Library | 09-practice-library.md | ✅ | ☐ | 75 practice entries, commercial model |
| 10 | Maturity Pathways | 10-maturity-pathways.md | ✅ | ☐ | Level-by-level progression, all 15 subdomains |
| 11 | Calibration Protocol | 11-calibration-protocol.md | ✅ | ☐ | IRR ≥ 0.80 target, certification program |
| 12 | Report Templates | 12-report-templates.md | ✅ | ☐ | 7 report types, white-label support |
| 13 | Migration Plan | 13-migration-plan.md | ✅ | ☐ | v1→vNext data mapping, 27-week timeline |
| 14 | Quality Checklist | 14-quality-checklist.md | ✅ | ☐ | This document |
| 00 | Master README | 00-README.md | ✅ | ☐ | Index linking all deliverables |

---

## 3. Framework Integrity Checks

### 3.1 Domain/Subdomain Consistency

| Check | Pass | Notes |
|-------|------|-------|
| 5 domains defined consistently across all documents | ☐ | WC, LC, WM, AI, SG |
| 3 subdomains per domain (15 total) across all documents | ☐ | |
| Domain codes match between framework, question bank, scoring model, and migration plan | ☐ | |
| Subdomain codes match between framework, question bank, and practice library | ☐ | |
| No orphan subdomains (referenced but undefined) | ☐ | |
| No orphan questions (not assigned to a subdomain) | ☐ | |

### 3.2 Question Bank Integrity

| Check | Pass | Notes |
|-------|------|-------|
| 150 questions total in JSON | ☐ | 10 per subdomain × 15 subdomains |
| Every question has a unique code | ☐ | Format: XX.N-NN |
| Every question has a scoring rubric (levels 1-5) | ☐ | |
| Every question has assessment_modes array | ☐ | |
| At least 1 question per subdomain tagged "quickscan" | ☐ | 15 total |
| QuickScan questions are all LIKERT type | ☐ | |
| Every question has iso_55001_clause | ☐ | |
| Every question has calibration_anchor | ☐ | |
| Every question has practice_link | ☐ | |
| Every question has evidence_guidance | ☐ | |
| All 16 v1 questions mapped to vNext equivalents | ☐ | Per catalog §7 |

### 3.3 Scoring Model Consistency

| Check | Pass | Notes |
|-------|------|-------|
| Maturity scale boundaries match across all documents | ☐ | L1: 1.0-1.99, L2: 2.0-2.99, L3: 3.0-3.59, L4: 3.6-4.29, L5: 4.3-5.0 |
| Role weights sum to 1.00 | ☐ | 0.35+0.20+0.15+0.15+0.15 = 1.00 |
| Default domain weights sum to 1.00 | ☐ | 5 × 0.20 = 1.00 |
| All industry module weight overrides sum to 1.00 | ☐ | 6 industry modules |
| Evidence hard-reject documented consistently | ☐ | ≥4 without evidence = BLOCKED |
| Weakest-link rules consistent between scoring model and question catalog | ☐ | |
| Confidence calculation documented with all deduction factors | ☐ | |

### 3.4 Routing Logic Consistency

| Check | Pass | Notes |
|-------|------|-------|
| QuickScan = 15 questions (1/subdomain) | ☐ | |
| Standard = 60-75 questions | ☐ | |
| DeepDive = 150+ questions | ☐ | |
| Mode transition rules documented | ☐ | QS→Std→DD (no QS→DD) |
| Data preservation on mode upgrade documented | ☐ | |
| Industry module weight overrides documented for all 6 modules | ☐ | |

---

## 4. Evidence & Traceability Checks

### 4.1 [OBSERVED] Claims

| Check | Pass | Notes |
|-------|------|-------|
| All [OBSERVED] tags include path:line reference | ☐ | |
| Referenced files exist in repository | ☐ | |
| Referenced line numbers are accurate (±5 lines) | ☐ | |
| No [OBSERVED] claims that should be [INFERRED] | ☐ | |

### 4.2 [INFERRED] Claims

| Check | Pass | Notes |
|-------|------|-------|
| All inferences are clearly marked [INFERRED] | ☐ | |
| Inferences are reasonable given available evidence | ☐ | |
| No critical design decisions based solely on inference | ☐ | |

---

## 5. Cross-Reference Checks

### 5.1 Document Links

| From | References | To | Valid |
|------|-----------|-----|-------|
| 05-question-catalog | v1 question mapping | 04-question-bank.json | ☐ |
| 06-routing-rules | Industry weight overrides | 07-scoring-model | ☐ |
| 07-scoring-model | Practice Library recommendation | 09-practice-library | ☐ |
| 09-practice-library | Maturity level descriptions | 10-maturity-pathways | ☐ |
| 10-maturity-pathways | Score interpretation | 07-scoring-model | ☐ |
| 11-calibration-protocol | Question rubrics | 04-question-bank.json | ☐ |
| 12-report-templates | Scoring data bindings | 07-scoring-model | ☐ |
| 12-report-templates | Benchmark data | 08-benchmarking-spec | ☐ |
| 12-report-templates | Recommendations | 09-practice-library | ☐ |
| 13-migration-plan | Question mapping | 05-question-catalog | ☐ |
| 13-migration-plan | Schema changes | 07-scoring-model | ☐ |

---

## 6. Voice & Tone Checks

| Check | Pass | Notes |
|-------|------|-------|
| VP of Reliability + Principal Consultant voice maintained | ☐ | |
| Concise, decisive, prescriptive — no hedge words | ☐ | |
| No "consider," "perhaps," "might" in recommendations | ☐ | |
| Technical accuracy verified for maintenance/reliability domain | ☐ | |
| ISO references are correct standard numbers | ☐ | |
| Industry terminology used correctly | ☐ | |

---

## 7. Technical Accuracy Checks

| Check | Pass | Notes |
|-------|------|-------|
| ISO 55001:2014 clause numbers are valid | ☐ | |
| ISO 14224 references are appropriate for failure coding | ☐ | |
| SMRP Best Practice references are valid | ☐ | |
| Cohen's weighted kappa formula description is correct | ☐ | |
| Planner-to-technician ratios are industry-standard (1:15-20) | ☐ | |
| PM compliance targets are realistic (80-95% range) | ☐ | |
| Training hours benchmarks are industry-appropriate | ☐ | |
| OEE calculation framework is correct | ☐ | |

---

## 8. Implementation Readiness Checks

| Check | Pass | Notes |
|-------|------|-------|
| All API endpoints defined with request/response schemas | ☐ | |
| Database migration scripts defined in execution order | ☐ | |
| Frontend component inventory complete | ☐ | |
| Zustand store schema defined | ☐ | |
| Report template rendering pipeline defined | ☐ | |
| Benchmark cold-start strategy defined | ☐ | |
| Migration timeline with phases and durations | ☐ | |
| Risk mitigations identified for each phase | ☐ | |

---

## 9. Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Lead | | | |
| Technical Lead | | | |
| Domain Expert (Reliability) | | | |
| Product Owner | | | |

---

*End of Quality Checklist*
