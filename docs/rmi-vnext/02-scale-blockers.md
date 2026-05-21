# 02 — Scale Blockers Analysis

**Document ID:** RMI-VNEXT-02  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** VP of Reliability · Principal Consultant

---

## 1. Purpose

This document identifies every structural limitation in RMI v1 that prevents the framework from scaling to multi-site, multi-industry, multi-tier commercial use. Each blocker is categorized by severity and mapped to the vNext deliverable that resolves it.

---

## 2. Blocker Inventory

### BLOCKER-01: Shallow Question Bank (16 Questions)

- **Severity:** CRITICAL
- **Evidence:** `[OBSERVED]` backend/question_bank.py — exactly 16 question dicts in `seed_question_bank()`
- **Impact:** A 16-question audit cannot differentiate maturity levels within a pillar. ISO/IEC 17021-style audits require 50–100+ evidence points per domain. Current depth is appropriate for a 30-minute QuickScan, not a 3-day deep audit.
- **Resolution:** → 03-vnext-framework.md, 04-question-bank.json (150+ questions)
- **Risk if unresolved:** Clients dismiss RMI as "just a survey." Consulting competitors (Deloitte, Accenture, SMRP) have deeper instruments.

---

### BLOCKER-02: No Sub-Pillar Taxonomy

- **Severity:** HIGH
- **Evidence:** `[OBSERVED]` backend/models.py:146 — `subcategory = Column(String(100))` is a free-text field
- **Impact:** Subcategories are inconsistently named across questions (e.g., "Competency" vs "Investment in Competency"). No enforced hierarchy means: (a) no sub-pillar scoring, (b) no heatmap drill-down, (c) no targeted improvement recommendations.
- **Resolution:** → 03-vnext-framework.md defines formal 5-domain × 3-subdomain hierarchy
- **Risk if unresolved:** Cannot produce gap-level recommendations. Reports stay at pillar level only.

---

### BLOCKER-03: No Industry Modules

- **Severity:** CRITICAL
- **Evidence:** `[OBSERVED]` No industry-specific question routing anywhere in codebase
- **Impact:** A food plant and a refinery get the same 16 questions. No regulatory compliance layer (FDA, OSHA PSM, API, NFPA). Cannot sell "RMI for Food" or "RMI for Oil & Gas" as differentiated products.
- **Resolution:** → 03-vnext-framework.md (Universal Core + Industry Modules architecture)
- **Risk if unresolved:** Cannot compete in regulated industries. Each new client requires manual question customization.

---

### BLOCKER-04: No Assessment Modes (QuickScan / Standard / DeepDive)

- **Severity:** HIGH
- **Evidence:** `[OBSERVED]` frontend/src/views/InterviewInterface.tsx — all questions rendered in sequence, no mode selection
- **Impact:** Cannot offer tiered pricing (Tier 1 audit @ $5K vs Tier 3 @ $50K). A QuickScan (15 min, 15 questions) and a DeepDive (3 days, 150+ questions) must use the same interface. No routing logic to select question subsets.
- **Resolution:** → 06-routing-rules.md
- **Risk if unresolved:** Sales friction — clients can't "try before they buy." Consultants can't scope engagements properly.

---

### BLOCKER-05: No Benchmarking Engine

- **Severity:** HIGH
- **Evidence:** `[INFERRED]` No benchmark tables, percentile calculations, or peer comparison logic found
- **Impact:** Scores are absolute (1-5) with no context. A score of 3.2 means nothing without "…which is 72nd percentile among food manufacturers." Cannot provide competitive intelligence or industry positioning.
- **Resolution:** → 08-benchmarking-spec.md
- **Risk if unresolved:** Reports lack the "so what?" factor. Executive sponsors can't justify investment without peer context.

---

### BLOCKER-06: No Practice Library

- **Severity:** HIGH  
- **Evidence:** `[INFERRED]` No practice catalog, recommendation engine, or prescriptive guidance system found
- **Impact:** The RMI tells you *where you are* but not *what to do next*. Consultants must manually write recommendations for every engagement. No reusable library of "to move from Level 2 to Level 3 in PM Compliance, implement X."
- **Resolution:** → 09-practice-library.md
- **Risk if unresolved:** Every report requires 20+ hours of manual recommendation writing. Cannot scale consulting delivery.

---

### BLOCKER-07: No Calibration Protocol

- **Severity:** HIGH
- **Evidence:** `[INFERRED]` No inter-rater reliability mechanism, no calibration exercises, no scoring rubric beyond `scoring_logic` JSON
- **Impact:** Two auditors scoring the same facility will produce different results. No mechanism to detect or correct drift. Audit-grade defensibility requires IRR ≥ 0.80.
- **Resolution:** → 11-calibration-protocol.md
- **Risk if unresolved:** Scores are not reproducible. Cannot withstand scrutiny from client legal/compliance teams.

---

### BLOCKER-08: Maturity Level Band Asymmetry

- **Severity:** MEDIUM
- **Evidence:** `[OBSERVED]` backend/scoring_engine.py:400-410
- **Impact:** Level 4 (Predictive) spans only 0.5 points (4.0–4.49) while all other levels span 1.0 points. This makes it statistically harder to "earn" Level 4 and easier to skip directly to Level 5. The boundary at 4.5 is arbitrary.
- **Resolution:** → 07-scoring-model.md (rebalanced scale)
- **Risk if unresolved:** Clients perceive Level 4 as meaningless. Level 5 becomes too easy to claim.

---

### BLOCKER-09: Evidence Lock Is Too Soft

- **Severity:** MEDIUM
- **Evidence:** `[OBSERVED]` backend/scoring_engine.py:193 — `response.numeric_score = min(response.numeric_score, 3)`
- **Impact:** The evidence lock silently caps high scores at 3 rather than rejecting the submission or flagging it for review. The auditor may not realize their score was modified. Frontend validation exists at submission time `[OBSERVED]` but backend fallback is passive.
- **Resolution:** → 07-scoring-model.md (hard reject + audit trail)
- **Risk if unresolved:** Score integrity is compromised. Auditors may unknowingly submit capped scores.

---

### BLOCKER-10: No Multi-Site Aggregation

- **Severity:** HIGH
- **Evidence:** `[INFERRED]` No site-grouping, portfolio-level scoring, or cross-site comparison logic
- **Impact:** Enterprise clients with 20+ sites need a portfolio dashboard showing site rankings, trend lines, and investment priority. Current system treats each assessment as isolated.
- **Resolution:** → 08-benchmarking-spec.md, 12-report-templates.md
- **Risk if unresolved:** Cannot sell enterprise contracts. Each site is a standalone engagement.

---

### BLOCKER-11: No Temporal Trend Views

- **Severity:** MEDIUM
- **Evidence:** `[OBSERVED]` backend/scoring_engine.py:600-660 — `_calculate_maturity_velocity()` exists but only compares to the single most recent prior assessment
- **Impact:** No multi-assessment trend line. No "you've improved 0.8 points over 18 months across 4 assessments." The velocity calculation is pairwise only.
- **Resolution:** → 12-report-templates.md (trend report spec)
- **Risk if unresolved:** Cannot demonstrate ROI of ongoing consulting engagements.

---

### BLOCKER-12: Hardcoded Questions (Not Data-Driven)

- **Severity:** MEDIUM
- **Evidence:** `[OBSERVED]` backend/question_bank.py — questions are Python dicts in a seed function, not loaded from a config file or admin UI
- **Impact:** Adding/modifying questions requires code deployment. No admin UI for question management. Cannot support customer-specific question sets without forking the codebase.
- **Resolution:** → 04-question-bank.json (JSON-driven catalog), admin UI
- **Risk if unresolved:** Every new client customization requires developer involvement.

---

### BLOCKER-13: No Freemium / Self-Service Path

- **Severity:** MEDIUM
- **Evidence:** `[INFERRED]` No public self-assessment, no registration flow, no pricing tiers
- **Impact:** No lead generation mechanism. Potential clients can't discover their maturity level without engaging a consultant. Competitors (Fiix, Limble, UpKeep) offer free maturity assessments as marketing tools.
- **Resolution:** → 06-routing-rules.md (QuickScan mode), 03-vnext-framework.md (freemium model)
- **Risk if unresolved:** Pipeline depends 100% on outbound sales.

---

### BLOCKER-14: Report Generator Is Monolithic

- **Severity:** LOW
- **Evidence:** `[OBSERVED]` backend/report_generator.py — 960 lines, single class, single output format (PDF)
- **Impact:** Cannot produce different report types (executive summary vs technical detail vs trend report) without major refactoring. No PowerPoint or interactive HTML export.
- **Resolution:** → 12-report-templates.md
- **Risk if unresolved:** Reports don't match audience needs. Board members need 2-page summaries; maintenance managers need 40-page details.

---

## 3. Severity Summary

| Severity | Count | Blockers                                                   |
|----------|-------|------------------------------------------------------------|
| CRITICAL | 2     | BLOCKER-01 (Question depth), BLOCKER-03 (Industry modules) |
| HIGH     | 7     | BLOCKER-02, 04, 05, 06, 07, 10, 11                         |
| MEDIUM   | 5     | BLOCKER-08, 09, 12, 13, 14                                 |
| LOW      | 0     | —                                                          |

---

## 4. Resolution Dependency Chain

```
BLOCKER-01 (Questions) ──→ 04-question-bank.json ──→ 06-routing-rules.md
                                                         ↓
BLOCKER-03 (Industries) ──→ 03-vnext-framework.md ──→ 04-question-bank.json
                                                         ↓
BLOCKER-04 (Modes) ──────→ 06-routing-rules.md ──→ 07-scoring-model.md
                                                         ↓
BLOCKER-05 (Benchmarks) ──→ 08-benchmarking-spec.md
                                  ↓
BLOCKER-06 (Practices) ───→ 09-practice-library.md ──→ 10-maturity-pathways.md
                                                         ↓
BLOCKER-07 (Calibration) ──→ 11-calibration-protocol.md
                                                         ↓
BLOCKER-10 (Multi-site) ──→ 08-benchmarking-spec.md + 12-report-templates.md
```

**Critical path:** Framework → Questions → Routing → Scoring → Benchmarking → Practices

---

*End of Scale Blockers Analysis*
