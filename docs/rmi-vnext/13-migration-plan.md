# 13 — Migration Plan: v1 → vNext

**Document ID:** RMI-VNEXT-13  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** Engineering · Product · Operations

---

## 1. Migration Scope

### 1.1 What Changes

| Component | v1 | vNext | Migration Effort |
|-----------|-----|------|-----------------|
| **Pillars → Domains** | 3 (People, Process, Technology) | 5 (WC, LC, WM, AI, SG) | Schema change + data mapping |
| **Questions** | 16 hardcoded | 150+ database-driven | Question bank redesign |
| **Scoring Scale** | Unequal bands (L4=0.50 width) | Equal-width bands (L4=0.70) | Scoring engine rewrite |
| **Evidence** | Silent cap | Hard reject | UX + API change |
| **Roles** | 5 (AUDITOR included) | 5 (RE replaces AUDITOR) | Role mapping |
| **Assessment Modes** | Single mode | QuickScan/Standard/DeepDive | New routing engine |
| **Industry Modules** | None | 6 modules | New feature |
| **Benchmarking** | None | Percentile engine | New feature |
| **Practice Library** | None | 75 entries | New feature |
| **Calibration** | None | IRR protocol | New feature |
| **Reports** | Single PDF | 7 report types | Report engine rewrite |

### 1.2 What Stays

| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI backend | Retained | Extended, not replaced |
| React + TypeScript frontend | Retained | Extended with new views |
| SQLAlchemy ORM | Retained | New models added |
| PostgreSQL (Railway) | Retained | Schema migration |
| JWT + Supabase auth | Retained | Role model extended |
| Axios client | Retained | New endpoints added |
| Zustand store | Retained | Expanded beyond auth-only |

---

## 2. Data Migration

### 2.1 Pillar → Domain Mapping

| v1 Pillar | vNext Domain(s) | Mapping Logic |
|-----------|----------------|---------------|
| People | WC (Workforce Capability) + LC (Leadership & Culture) | Split: P-01,P-02,P-04,P-05 → WC; P-03 → LC |
| Process | WM (Work Management) | Direct: PR-01..PR-05 → WM subdomains |
| Technology | AI (Asset Information) | Direct: T-01..T-06 → AI subdomains |
| (none) | SG (Strategy & Governance) | NEW — no v1 data to migrate |

### 2.2 Question Mapping

| v1 Code | v1 Pillar | vNext Code | vNext Domain | vNext Subdomain |
|---------|----------|-----------|-------------|----------------|
| P-01 | People | WC.1-01 | WC | Technical Competency |
| P-02 | People | WM.1-02 | WM | Planning & Scheduling |
| P-03 | People | LC.2-01 | LC | Safety & Reliability Culture |
| P-04 | People | WC.3-01 | WC | Knowledge Management |
| P-05 | People | WC.2-03 | WC | Training & Development |
| PR-01 | Process | WM.3-02 | WM | Work Execution & Quality |
| PR-02 | Process | WM.3-01 | WM | Work Execution & Quality |
| PR-03 | Process | WM.3-03 | WM | Work Execution & Quality |
| PR-04 | Process | WM.1-01 | WM | Planning & Scheduling |
| PR-05 | Process | WM.2-01 | WM | PM/PdM |
| T-01 | Technology | AI.2-01 | AI | Data Quality & Integrity |
| T-02 | Technology | AI.2-03 | AI | Data Quality & Integrity |
| T-03 | Technology | AI.3-01 | AI | Analytics & Decision Support |
| T-04 | Technology | AI.1-01 | AI | CMMS/EAM Effectiveness |
| T-05 | Technology | AI.2-02 | AI | Data Quality & Integrity |
| T-06 | Technology | AI.1-04 | AI | CMMS/EAM Effectiveness |

**Note:** P-02 (emergency interruptions) crosses from People → WM. This is intentional — emergency interruptions are a work management metric, not a workforce capability metric.

### 2.3 Score Recalculation

Historical v1 scores **cannot** be directly compared to vNext scores because:
1. Different scale boundaries (v1: L4 at 4.0; vNext: L4 at 3.6)
2. Different domain structure (3 → 5 domains)
3. Different role weights
4. Only 16/150 questions have data

**Strategy:** 
- Store v1 scores as `legacy_score` in assessment record
- Display v1 scores with "v1 methodology" qualifier
- Do NOT attempt to recalculate v1 assessments on vNext scale
- Trend reports spanning v1→vNext show a methodology break marker

### 2.4 Role Migration

| v1 Role | v1 Weight | vNext Role | vNext Weight | Notes |
|---------|----------|-----------|-------------|-------|
| TECHNICIAN | 0.60 | TECHNICIAN | 0.35 | Weight reduced |
| SUPERVISOR | 0.10 | SUPERVISOR | 0.20 | Weight increased |
| MANAGER | 0.20 | MANAGER | 0.15 | Weight reduced |
| PLANNER | 0.10 | PLANNER | 0.15 | Weight increased |
| AUDITOR | 0.20 | (removed) | — | Auditor is not a respondent role |
| (none) | — | RELIABILITY_ENGINEER | 0.15 | New role |

---

## 3. Database Schema Migration

### 3.1 New Tables

```sql
-- Domain/Subdomain taxonomy (replaces hardcoded PillarType enum)
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(2) NOT NULL UNIQUE,        -- WC, LC, WM, AI, SG
    name VARCHAR(50) NOT NULL,
    description TEXT,
    default_weight DECIMAL(3,2) DEFAULT 0.20,
    display_order INTEGER NOT NULL
);

CREATE TABLE subdomains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES domains(id),
    code VARCHAR(4) NOT NULL UNIQUE,        -- WC.1, WC.2, WC.3, etc.
    name VARCHAR(50) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL
);

-- Assessment mode and industry module
ALTER TABLE assessments ADD COLUMN assessment_mode VARCHAR(10) DEFAULT 'standard';
ALTER TABLE assessments ADD COLUMN industry_module VARCHAR(3);
ALTER TABLE assessments ADD COLUMN legacy_score JSONB;  -- preserved v1 scores
ALTER TABLE assessments ADD COLUMN confidence_score DECIMAL(3,2);

-- Benchmark metadata
CREATE TABLE benchmark_metadata (
    assessment_id UUID PRIMARY KEY REFERENCES assessments(id),
    industry_code VARCHAR(3),
    site_size_category VARCHAR(10),
    region VARCHAR(30),
    asset_intensity VARCHAR(10),
    maintenance_fte INTEGER,
    is_benchmark_eligible BOOLEAN DEFAULT TRUE
);

-- Practice library
CREATE TABLE practices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id VARCHAR(20) NOT NULL UNIQUE,  -- WM.1-01-P
    subdomain_id UUID REFERENCES subdomains(id),
    title VARCHAR(200) NOT NULL,
    pathways JSONB NOT NULL,  -- maturity pathway content
    references JSONB,
    industry_variations JSONB,
    tools JSONB,  -- linked tool files
    version VARCHAR(10) DEFAULT '2.0',
    is_active BOOLEAN DEFAULT TRUE
);

-- Calibration
CREATE TABLE calibration_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auditor_id UUID REFERENCES users(id),
    exercise_type VARCHAR(20),
    case_study_id VARCHAR(20),
    irr_score DECIMAL(3,2),
    deviation_details JSONB,
    completed_at TIMESTAMP
);

-- Subdomain-level scores (finer granularity than pillar-level)
CREATE TABLE subdomain_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id),
    subdomain_id UUID REFERENCES subdomains(id),
    raw_score DECIMAL(3,2),
    weighted_score DECIMAL(3,2),
    evidence_adjusted_score DECIMAL(3,2),
    cap_applied BOOLEAN DEFAULT FALSE,
    cap_reason TEXT,
    confidence DECIMAL(3,2),
    percentile INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Modified Tables

```sql
-- question_bank: Add subdomain reference and assessment mode tags
ALTER TABLE question_bank ADD COLUMN subdomain_id UUID REFERENCES subdomains(id);
ALTER TABLE question_bank ADD COLUMN assessment_modes JSONB DEFAULT '["standard","deepdive"]';
ALTER TABLE question_bank ADD COLUMN calibration_anchor TEXT;
ALTER TABLE question_bank ADD COLUMN practice_link VARCHAR(20);
ALTER TABLE question_bank ADD COLUMN iso_55001_clause VARCHAR(20);
ALTER TABLE question_bank ADD COLUMN version VARCHAR(10) DEFAULT '2.0';
ALTER TABLE question_bank ADD COLUMN is_active BOOLEAN DEFAULT TRUE;

-- question_responses: Add evidence status
ALTER TABLE question_responses ADD COLUMN evidence_status VARCHAR(20) DEFAULT 'not_required';
  -- Values: not_required, pending_evidence, pending_verification, accepted, rejected

-- scores: Add subdomain-level detail
ALTER TABLE scores ADD COLUMN domain_scores JSONB;
ALTER TABLE scores ADD COLUMN subdomain_scores JSONB;
ALTER TABLE scores ADD COLUMN confidence_band JSONB;
ALTER TABLE scores ADD COLUMN caps_applied JSONB;
ALTER TABLE scores ADD COLUMN blind_spots JSONB;

-- users: Add auditor certification level
ALTER TABLE users ADD COLUMN certification_level VARCHAR(20);
ALTER TABLE users ADD COLUMN certification_expiry DATE;
ALTER TABLE users ADD COLUMN current_irr DECIMAL(3,2);
```

### 3.3 Migration Script Execution Order

```
1. Create new tables (domains, subdomains, practices, etc.)
2. Seed domain and subdomain data
3. Seed vNext question bank (150 questions)
4. ALTER existing tables (add new columns)
5. Migrate question_bank records: map pillar → subdomain
6. Migrate assessment records: add legacy_score, set mode='standard'
7. Migrate score records: add domain_scores JSONB
8. Mark v1 questions as version='1.0', is_active=false
9. Run validation queries
10. Create new indexes
```

---

## 4. API Migration

### 4.1 Versioned Endpoints

| Strategy | Detail |
|----------|--------|
| **URL versioning** | `/api/v1/...` (existing) + `/api/v2/...` (vNext) |
| **Parallel operation** | v1 and v2 run simultaneously during transition |
| **Deprecation** | v1 deprecated 6 months after v2 launch |
| **Sunset** | v1 removed 12 months after v2 launch |

### 4.2 New v2 Endpoints

```
Assessment Management:
  POST   /api/v2/assessments                    (with mode + industry)
  GET    /api/v2/assessments/{id}               (includes subdomain scores)
  POST   /api/v2/assessments/{id}/calculate     (vNext scoring engine)
  GET    /api/v2/assessments/{id}/benchmark     (new)
  GET    /api/v2/assessments/{id}/recommendations (new)
  POST   /api/v2/assessments/{id}/reroute       (adaptive routing, future)

Question Bank:
  GET    /api/v2/questions                      (with mode/subdomain filters)
  GET    /api/v2/questions/{id}                 (includes rubric + anchor)

Practice Library:
  GET    /api/v2/practices                      (new)
  GET    /api/v2/practices/{id}                 (new)
  GET    /api/v2/practices/{id}/tools/{filename} (new)

Benchmarking:
  GET    /api/v2/benchmarks/industry/{code}     (new)
  GET    /api/v2/portfolios/{org_id}/benchmark  (new, enterprise)

Reports:
  POST   /api/v2/reports/{id}/generate          (multi-format)
  GET    /api/v2/reports/{id}/download           (PDF/PPTX)

Calibration:
  POST   /api/v2/calibration/exercises/{id}/submit (new)
  GET    /api/v2/calibration/auditors/{id}/status  (new)
```

---

## 5. Frontend Migration

### 5.1 New Views/Components

| View | Purpose | Priority |
|------|---------|----------|
| Assessment Mode Selector | QuickScan/Standard/DeepDive + industry | P0 |
| Subdomain Score Display | 5×3 heat map + spider chart | P0 |
| Evidence Upload with Status | Hard reject UX + status indicators | P0 |
| Practice Library Browser | Browse/search practices | P1 |
| Benchmark Comparison | Percentile charts | P1 |
| Portfolio Dashboard | Multi-site enterprise view | P2 |
| Calibration Center | Auditor calibration exercises | P2 |
| QuickScan Public Flow | Unauthenticated QuickScan | P1 |

### 5.2 Zustand Store Expansion

v1 store is auth-only [OBSERVED: store.ts]. vNext needs:

```typescript
// Expand from auth-only to full state management
interface RMIStore {
    // Auth (existing)
    user: User | null;
    token: string | null;
    
    // Assessment (new)
    currentAssessment: Assessment | null;
    assessmentMode: 'quickscan' | 'standard' | 'deepdive';
    industryModule: string | null;
    routedQuestions: Question[];
    responses: Map<string, Response>;
    
    // Scoring (new)
    scores: {
        overall: number;
        domains: Record<string, DomainScore>;
        subdomains: Record<string, number>;
        confidence: number;
        caps: Cap[];
        blindSpots: BlindSpot[];
    } | null;
    
    // Benchmark (new)
    benchmark: {
        percentile: number;
        peerCount: number;
        domainPercentiles: Record<string, number>;
    } | null;
    
    // Offline (new)
    offlineQueue: QueuedRequest[];
    isOnline: boolean;
}
```

---

## 6. Migration Timeline

### 6.1 Phase Plan

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| **Phase 1: Foundation** | 4 weeks | DB schema migration, domain/subdomain models, v2 question bank seeded |
| **Phase 2: Scoring Engine** | 3 weeks | vNext scoring engine, evidence hard-reject, new maturity scale |
| **Phase 3: Assessment Routing** | 2 weeks | QuickScan/Standard/DeepDive routing, industry modules |
| **Phase 4: Frontend Core** | 4 weeks | New assessment flow, subdomain UI, evidence UX |
| **Phase 5: Benchmarking** | 2 weeks | Percentile engine, peer groups, benchmark API |
| **Phase 6: Practice Library** | 2 weeks | Content CMS, recommendation engine, tool downloads |
| **Phase 7: Reports** | 3 weeks | 7 report types, template engine, AI narratives |
| **Phase 8: Calibration** | 2 weeks | Calibration module, IRR tracking, exercise platform |
| **Phase 9: Portfolio** | 2 weeks | Enterprise multi-site, portfolio dashboard |
| **Phase 10: Testing & Launch** | 3 weeks | Integration testing, UAT, v1 deprecation plan |

**Total: ~27 weeks (6-7 months)**

### 6.2 Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Data loss during migration | Run v1 and v2 in parallel; don't delete v1 data |
| Scoring inconsistency | Store v1 scores as legacy; clear methodology break marker |
| Benchmark cold start | Synthetic benchmarks from industry data until N ≥ 50 |
| Auditor retraining | Phase calibration launch after 2+ assessments complete |
| Client confusion | Clear communication: "Your v1 score and v2 score use different scales" |

---

## 7. Backward Compatibility

### 7.1 v1 Assessment Access

- All v1 assessments remain accessible at `/api/v1/assessments/{id}`
- v1 reports remain downloadable
- v1 scores displayed with "Legacy (v1)" badge
- No v1 features are removed until v2 has full feature parity

### 7.2 Data Continuity

```
Assessment Timeline View:

  v1 Assessment 1    v1 Assessment 2    v2 Assessment 1
  Jan 2024           Jul 2024           Jan 2025
  RMI: 2.8 (v1)     RMI: 3.1 (v1)     RMI: 3.42 (v2)
  ─────────────────────┬─────────────────────────────
                       │
                 Methodology Break
                 (v1 → v2 transition)
```

---

*End of Migration Plan*
