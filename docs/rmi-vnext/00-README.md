# RMI vNext — Design Documentation

**Reliability Maturity Index — Next Generation Framework**  
**NextBelt LLC · January 2025**

---

## Overview

This directory contains the complete design specification for the RMI vNext framework — a ground-up redesign of the Reliability Maturity Index assessment platform. The redesign expands the framework from 3 pillars / 16 questions to 5 domains / 150+ questions, introduces three assessment modes, industry modules, a prescriptive practice library, and a benchmarking engine.

---

## Document Index

| #                                | Document                           | Description                                                                                                                                          |
|----------------------------------|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| [01](01-as-is-spec.md)           | **As-Is Specification**            | Complete forensic analysis of the current v1 codebase with [OBSERVED] path:line references                                                           |
| [02](02-scale-blockers.md)       | **Scale Blockers**                 | 14 identified blockers preventing v1 from scaling (2 CRITICAL, 7 HIGH, 5 MEDIUM)                                                                     |
| [03](03-vnext-framework.md)      | **vNext Framework Architecture**   | The 5-domain × 3-subdomain design, industry modules, assessment modes, and commercial model                                                          |
| [04](04-question-bank.json)      | **Question Bank (JSON)**           | 150 machine-readable questions with scoring rubrics, ISO 55001 mappings, calibration anchors, and practice links                                     |
| [05](05-question-catalog.md)     | **Question Catalog Documentation** | Human-readable catalog explaining question design rationale, type distribution, evidence requirements, and v1→vNext mapping                          |
| [06](06-routing-rules.md)        | **Assessment Routing Rules**       | QuickScan (15q) / Standard (60-75q) / DeepDive (150+q) routing logic, role-based targeting, industry module routing, and adaptive routing            |
| [07](07-scoring-model.md)        | **Scoring Model Specification**    | Rebalanced maturity scale, role weights, evidence hard-reject, weakest-link rules, confidence calculation, and velocity tracking                     |
| [08](08-benchmarking-spec.md)    | **Benchmarking Specification**     | Percentile engine, peer group segmentation, privacy controls, portfolio benchmarking, cold-start strategy                                            |
| [09](09-practice-library.md)     | **Practice Library**               | 75 prescriptive practice entries (5 per subdomain) with maturity pathways, implementation playbooks, and consulting funnel integration               |
| [10](10-maturity-pathways.md)    | **Maturity Pathways**              | Level-by-level progression descriptions for all 15 subdomains with observable indicators and typical maturity profiles                               |
| [11](11-calibration-protocol.md) | **Calibration Protocol**           | Inter-rater reliability (IRR ≥ 0.80) protocol, auditor certification program, case study exercises, bias correction                                  |
| [12](12-report-templates.md)     | **Report Templates**               | 7 report types (Executive Summary, Technical Detail, QuickScan, Trend, Portfolio, ISO Gap, Calibration) with template engine and white-label support |
| [13](13-migration-plan.md)       | **Migration Plan**                 | v1 → vNext data mapping, schema migration scripts, API versioning strategy, 27-week implementation timeline                                          |
| [14](14-quality-checklist.md)    | **Quality Checklist**              | Final quality gate with completeness, consistency, cross-reference, and sign-off checks                                                              |

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    RMI vNext Framework                        │
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│    WC    │    LC    │    WM    │    AI    │       SG         │
│ Workforce│Leadership│   Work   │  Asset   │   Strategy &     │
│Capability│ & Culture│Management│  Info    │  Governance      │
├──────────┼──────────┼──────────┼──────────┼──────────────────┤
│ WC.1     │ LC.1     │ WM.1     │ AI.1     │ SG.1             │
│ WC.2     │ LC.2     │ WM.2     │ AI.2     │ SG.2             │
│ WC.3     │ LC.3     │ WM.3     │ AI.3     │ SG.3             │
├──────────┴──────────┴──────────┴──────────┴──────────────────┤
│              Universal Core (150 questions)                   │
├──────────────────────────────────────────────────────────────┤
│  Industry Modules: MFG | FNB | ONG | MNM | UTL | PHA        │
├──────────────────────────────────────────────────────────────┤
│  Assessment Modes: QuickScan(15q) | Standard(60-75q) |       │
│                    DeepDive(150+q)                            │
├──────────────────────────────────────────────────────────────┤
│  Maturity Scale: L1 Reactive | L2 Emerging | L3 Systematic | │
│                  L4 Proactive | L5 Prescriptive              │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

1. **5 Domains (not 3 pillars)** — Adding Leadership & Culture and Strategy & Governance addresses the two biggest blind spots in v1
2. **Equal-width maturity bands** — L3=0.60, L4=0.70, L5=0.70 replaces v1's compressed top (L4=0.50, L5=0.50)
3. **Evidence hard-reject (not silent cap)** — Scores ≥4 without evidence are BLOCKED, not silently reduced
4. **Practice Library backbone** — Every question links to prescriptive guidance; the library IS the consulting IP
5. **Three assessment modes** — QuickScan (free lead-gen) → Standard (paid) → DeepDive (premium consulting)
6. **Industry modules** — Weight overrides and supplementary questions per industry vertical
7. **Calibration protocol** — IRR ≥ 0.80 ensures scoring consistency across auditors
8. **Benchmarking engine** — Percentile-based peer comparison with privacy controls

---

## Repository Context

- **Source Repository:** `C:\Users\cncha\OneDrive\Desktop\RMI Audit Toolkit`
- **Tech Stack:** FastAPI (Python) + React/TypeScript/Vite + PostgreSQL + Supabase + Railway
- **All [OBSERVED] references** point to files in the source repository with path:line notation
- **All [INFERRED] claims** are explicitly marked as inferences

---

## Getting Started

1. Read [01-as-is-spec.md](01-as-is-spec.md) to understand the current v1 state
2. Read [02-scale-blockers.md](02-scale-blockers.md) to understand why vNext is needed
3. Read [03-vnext-framework.md](03-vnext-framework.md) for the vNext architecture
4. Review [13-migration-plan.md](13-migration-plan.md) for implementation roadmap
5. Use [14-quality-checklist.md](14-quality-checklist.md) to validate before implementation

---

*© 2025 NextBelt LLC. All rights reserved.*
