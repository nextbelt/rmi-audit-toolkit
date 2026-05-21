# 08 — Benchmarking Specification

**Document ID:** RMI-VNEXT-08  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** Product · Data Science · Sales

---

## 1. Benchmarking Overview

The RMI vNext benchmarking engine provides **percentile-based peer comparison** so organizations can answer: "Where do we stand relative to similar facilities?"

### 1.1 Why Benchmarking Matters

A raw RMI score of 3.2 means nothing without context:
- 3.2 in Oil & Gas might be top quartile (heavily regulated, most sites are reactive)
- 3.2 in Automotive Manufacturing might be bottom quartile (industry standard is higher)
- 3.2 for a 500-person plant is different from 3.2 for a 20-person shop

---

## 2. Peer Group Segmentation

### 2.1 Segmentation Dimensions

| Dimension           | Categories                                                                  | Source              |
|---------------------|-----------------------------------------------------------------------------|---------------------|
| **Industry**        | MFG, FNB, ONG, MNM, UTL, PHA, OTHER                                         | Assessment creation |
| **Site Size**       | Small (<50 maint FTE), Medium (50-200), Large (200+)                        | Assessment metadata |
| **Region**          | North America, Europe, Asia-Pacific, Latin America, Middle East/Africa      | Site address        |
| **Assessment Mode** | QuickScan, Standard, DeepDive                                               | Assessment type     |
| **Asset Intensity** | Light (office/warehouse), Medium (discrete mfg), Heavy (process/continuous) | Assessment metadata |

### 2.2 Peer Group Formation Rules

```
PRIMARY peer group = Industry + Size
    Minimum sample: 30 assessments
    
IF PRIMARY < 30:
    EXPAND to Industry (all sizes)
    
IF still < 30:
    EXPAND to Size (all industries)
    
IF still < 30:
    USE global pool
    FLAG "Limited peer data — percentile is approximate"
```

### 2.3 Data Isolation

- QuickScan assessments are benchmarked only against other QuickScans
- Standard and DeepDive assessments are benchmarked together (deeper always valid)
- Never mix QuickScan with Standard/DeepDive in the same peer group

---

## 3. Percentile Engine

### 3.1 Calculation Method

```
FUNCTION calculate_percentile(score, peer_group):
    peer_scores = GET all overall_rmi FROM assessments 
                  WHERE peer_group matches
                  AND assessment_date > (NOW - 3 years)  // rolling window
                  AND status = "COMPLETED"
    
    percentile = (COUNT(peer_scores < score) / COUNT(peer_scores)) × 100
    
    RETURN {
        "percentile": ROUND(percentile, 0),
        "peer_count": COUNT(peer_scores),
        "peer_median": MEDIAN(peer_scores),
        "peer_mean": MEAN(peer_scores),
        "peer_stdev": STDEV(peer_scores),
        "quartile": FLOOR(percentile / 25) + 1,
        "peer_group_label": format_peer_group_label()
    }
```

### 3.2 Percentile Interpretation

| Percentile | Quartile | Label           | Guidance                                                       |
|------------|----------|-----------------|----------------------------------------------------------------|
| 0-25       | Q1       | Below Average   | Significant gaps vs. peers; focus on foundational improvements |
| 26-50      | Q2       | Average         | Tracking with peers; targeted improvements will differentiate  |
| 51-75      | Q3       | Above Average   | Outperforming most peers; refine advanced practices            |
| 76-100     | Q4       | Industry Leader | Top quartile; maintain edge and share best practices           |

### 3.3 Domain-Level Percentiles

Percentiles are calculated at **overall, domain, and subdomain** levels:

```json
{
    "overall": { "score": 3.42, "percentile": 67, "quartile": "Q3" },
    "domains": {
        "WC": { "score": 3.1, "percentile": 52, "quartile": "Q3" },
        "LC": { "score": 3.5, "percentile": 71, "quartile": "Q3" },
        "WM": { "score": 3.6, "percentile": 78, "quartile": "Q4" },
        "AI": { "score": 3.2, "percentile": 45, "quartile": "Q2" },
        "SG": { "score": 3.7, "percentile": 82, "quartile": "Q4" }
    }
}
```

This allows organizations to see: "We're top quartile in Work Management but below average in Asset Information."

---

## 4. Benchmark Data Model

### 4.1 Assessment Metadata Schema

```sql
CREATE TABLE benchmark_metadata (
    assessment_id UUID PRIMARY KEY REFERENCES assessments(id),
    industry_code VARCHAR(3) NOT NULL,        -- MFG, FNB, ONG, etc.
    site_size_category VARCHAR(10) NOT NULL,   -- SMALL, MEDIUM, LARGE
    region VARCHAR(30) NOT NULL,               -- NORTH_AMERICA, etc.
    asset_intensity VARCHAR(10) NOT NULL,      -- LIGHT, MEDIUM, HEAVY
    assessment_mode VARCHAR(10) NOT NULL,      -- QUICKSCAN, STANDARD, DEEPDIVE
    maintenance_fte INTEGER,                   -- actual headcount
    annual_maintenance_budget DECIMAL(12,2),   -- USD, optional
    total_asset_replacement_value DECIMAL(15,2), -- USD, optional
    is_benchmark_eligible BOOLEAN DEFAULT TRUE,
    anonymized_site_id VARCHAR(20),            -- for privacy
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_benchmark_peer ON benchmark_metadata (
    industry_code, site_size_category, assessment_mode
);
```

### 4.2 Benchmark Score Cache

```sql
CREATE TABLE benchmark_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id),
    score_type VARCHAR(10) NOT NULL,   -- OVERALL, DOMAIN, SUBDOMAIN
    score_key VARCHAR(10) NOT NULL,    -- 'overall', 'WC', 'WC.1', etc.
    score DECIMAL(3,2) NOT NULL,
    percentile INTEGER,
    peer_group_hash VARCHAR(64),       -- hash of peer group criteria
    peer_count INTEGER,
    calculated_at TIMESTAMP DEFAULT NOW()
);
```

### 4.3 Peer Group Stats Cache

```sql
CREATE TABLE peer_group_stats (
    peer_group_hash VARCHAR(64) PRIMARY KEY,
    industry_code VARCHAR(3),
    site_size_category VARCHAR(10),
    assessment_mode VARCHAR(10),
    score_key VARCHAR(10) NOT NULL,
    sample_count INTEGER NOT NULL,
    mean_score DECIMAL(3,2),
    median_score DECIMAL(3,2),
    stdev_score DECIMAL(3,2),
    p25_score DECIMAL(3,2),
    p75_score DECIMAL(3,2),
    min_score DECIMAL(3,2),
    max_score DECIMAL(3,2),
    calculated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours')
);
```

---

## 5. Privacy & Anonymization

### 5.1 Data Handling Rules

| Data Element         | Treatment                                    |
|----------------------|----------------------------------------------|
| Organization name    | **Never** included in benchmark datasets     |
| Site name            | **Never** included in benchmark datasets     |
| Individual scores    | **Never** exposed to other organizations     |
| Aggregate statistics | Shared only when peer group ≥ 30 assessments |
| Industry averages    | Published in annual reports (aggregated)     |
| Respondent names     | **Never** included in any benchmark data     |

### 5.2 Minimum Anonymity Threshold

```
IF peer_group_count < 5:
    DO NOT show any benchmark data
    DISPLAY "Insufficient peer data for benchmarking"

IF peer_group_count >= 5 AND < 30:
    SHOW percentile with "approximate" qualifier
    DO NOT show distribution charts
    
IF peer_group_count >= 30:
    SHOW full benchmarking with distribution charts
```

---

## 6. Portfolio Benchmarking (Enterprise Feature)

### 6.1 Multi-Site Dashboard

For enterprise clients with multiple sites:

```
GET /api/v2/portfolios/{org_id}/benchmark

Response:
{
    "organization": "Acme Corp",
    "total_sites": 12,
    "assessed_sites": 8,
    "portfolio_rmi": 3.28,
    "portfolio_percentile": 61,
    "sites": [
        {
            "anonymized_id": "SITE-A",
            "rmi": 3.8,
            "percentile": 82,
            "best_domain": "WM",
            "worst_domain": "AI",
            "velocity": 0.4
        },
        // ...
    ],
    "internal_ranking": [
        { "rank": 1, "site": "SITE-C", "rmi": 4.1 },
        { "rank": 2, "site": "SITE-A", "rmi": 3.8 },
        // ...
    ],
    "best_practice_transfer": [
        {
            "from": "SITE-C",
            "to": ["SITE-D", "SITE-E"],
            "domain": "WM",
            "score_gap": 1.2,
            "recommendation": "Transfer SITE-C's planning & scheduling practices to SITE-D and SITE-E"
        }
    ]
}
```

### 6.2 Internal vs. External Benchmarking

| View         | Description                             | Value                                         |
|--------------|-----------------------------------------|-----------------------------------------------|
| **Internal** | Compare your sites against each other   | Identify best practice transfer opportunities |
| **External** | Compare your portfolio against industry | Understand competitive position               |
| **Combined** | Internal ranking + external percentiles | Full picture for capital allocation           |

---

## 7. Trend Analysis

### 7.1 Time-Series Benchmarking

Track percentile movement over time:

```json
{
    "site": "SITE-A",
    "trend": [
        { "date": "2024-01", "rmi": 2.8, "percentile": 35 },
        { "date": "2024-07", "rmi": 3.2, "percentile": 52 },
        { "date": "2025-01", "rmi": 3.6, "percentile": 68 }
    ],
    "velocity": 0.8,
    "percentile_velocity": 33,  // moved 33 percentile points in 12 months
    "interpretation": "Rapid improvement — outpacing peer group growth rate"
}
```

### 7.2 Industry Trend Data

Aggregate industry trends published quarterly:

```json
{
    "industry": "MFG",
    "period": "2025-Q1",
    "global_mean_rmi": 2.95,
    "global_median_rmi": 2.80,
    "yoy_change": 0.12,
    "top_improving_domain": "AI",
    "lowest_scoring_domain": "SG",
    "trend": "Gradual improvement driven by CMMS modernization"
}
```

---

## 8. Benchmark Data Collection

### 8.1 Opt-In Model

- All assessments are eligible for benchmarking by default
- Organizations can opt out at assessment creation
- Opted-out assessments still receive percentiles (they consume benchmarks but don't contribute)
- Premium/enterprise clients can opt out of contribution while retaining access

### 8.2 Data Quality Gates

Assessments are excluded from benchmark pools if:

| Exclusion Criteria                                  | Rationale                          |
|-----------------------------------------------------|------------------------------------|
| Assessment incomplete (< 80% questions answered)    | Partial data skews pool            |
| Assessment abandoned (no completion within 90 days) | Stale data                         |
| Confidence score < 40%                              | Too uncertain to benchmark against |
| Known test/demo assessment                          | Pollutes pool                      |
| Single-respondent assessment in Standard/DeepDive   | Insufficient perspective diversity |

---

## 9. API Endpoints

### 9.1 Get Assessment Benchmark

```
GET /api/v2/assessments/{id}/benchmark
Query params:
    ?level=overall|domain|subdomain
    &peer_group=default|custom
    &custom_industry=MFG
    &custom_size=MEDIUM
```

### 9.2 Get Industry Statistics

```
GET /api/v2/benchmarks/industry/{industry_code}
Query params:
    ?period=2025-Q1
    &size_filter=MEDIUM
    &region_filter=NORTH_AMERICA
```

### 9.3 Get Portfolio Benchmark (Enterprise)

```
GET /api/v2/portfolios/{org_id}/benchmark
Query params:
    ?include_internal=true
    &include_external=true
    &include_trends=true
```

---

## 10. Cold-Start Strategy

### 10.1 The Bootstrap Problem

At launch, the benchmark pool is empty. Strategy:

1. **Phase 1 (0-50 assessments):** No benchmarking. Display "Benchmarking data will be available once sufficient assessments are completed."
2. **Phase 2 (50-200 assessments):** Global-only benchmarking. All assessments in one pool regardless of industry/size.
3. **Phase 3 (200-500 assessments):** Industry-level benchmarking enabled. Size segmentation still global.
4. **Phase 4 (500+ assessments):** Full segmented benchmarking.

### 10.2 Synthetic Benchmarks (Optional)

During Phase 1-2, offer "reference benchmarks" based on published industry data:
- SMRP Best Practices metrics
- EFNMS maintenance maturity studies
- ISO 55001 certification body statistics

These are labeled "Reference Benchmark (not peer-derived)" and retired once real data is sufficient.

---

*End of Benchmarking Specification*
