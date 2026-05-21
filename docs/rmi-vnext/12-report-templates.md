# 12 — Report Templates Specification

**Document ID:** RMI-VNEXT-12  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** Product · Engineering · Consulting

---

## 1. Report Types

| Report                   | Pages | Audience                       | Generation          | Frequency       |
|--------------------------|-------|--------------------------------|---------------------|-----------------|
| **Executive Summary**    | 2-3   | C-Suite, Plant Manager         | Auto                | Per assessment  |
| **Technical Detail**     | 30-50 | Reliability Manager, Engineers | Auto + AI narrative | Per assessment  |
| **QuickScan Report**     | 4-6   | Self-assessment user           | Auto                | Per QuickScan   |
| **Trend Report**         | 8-12  | Management                     | Auto                | Semi-annual     |
| **Portfolio Dashboard**  | 10-15 | VP Operations, Corporate       | Auto                | Quarterly       |
| **ISO 55001 Gap Report** | 15-20 | AM Team, Registrar prep        | Auto                | Per assessment  |
| **Calibration Report**   | 3-5   | QA, Auditor Training           | Auto                | Per calibration |

---

## 2. Executive Summary (2-3 Pages)

### 2.1 Layout

```
PAGE 1:
┌─────────────────────────────────────────────┐
│  [NextBelt Logo]    RMI Assessment Report    │
│                     Executive Summary         │
│                                               │
│  Site: [Name]       Date: [Date]              │
│  Industry: [Type]   Mode: [Standard/DeepDive] │
│  Auditor: [Name]    Confidence: [%]           │
├─────────────────────────────────────────────┤
│                                               │
│  ┌───────────────────┐                        │
│  │   OVERALL RMI     │                        │
│  │      3.42         │                        │
│  │   ────────────    │                        │
│  │   SYSTEMATIC      │                        │
│  │   (Level 3)       │                        │
│  │                   │                        │
│  │  Percentile: 67th │                        │
│  │  Peer Group: MFG  │                        │
│  │  Medium Sites     │                        │
│  └───────────────────┘                        │
│                                               │
│  DOMAIN SCORES                                │
│  ┌─────┬─────┬─────┬─────┬─────┐             │
│  │ WC  │ LC  │ WM  │ AI  │ SG  │             │
│  │ 3.1 │ 3.5 │ 3.6 │ 3.2 │ 3.7 │             │
│  │ L3  │ L3  │ L4  │ L3  │ L4  │             │
│  └─────┴─────┴─────┴─────┴─────┘             │
│                                               │
│  SPIDER CHART [15-axis radar chart]           │
│                                               │
├─────────────────────────────────────────────┤
PAGE 2:
│  TOP 5 STRENGTHS                              │
│  1. Work Management (WM) — Level 4 Proactive  │
│  2. Strategy & Governance (SG) — Level 4      │
│  3. ...                                       │
│                                               │
│  TOP 5 IMPROVEMENT PRIORITIES                 │
│  1. ⚠ LOTO Compliance (WM.3) — Domain cap     │
│  2. CMMS Data Quality (AI.2) — below peer avg │
│  3. ...                                       │
│                                               │
│  MATURITY VELOCITY                            │
│  Previous: 2.8 (Jan 2024)                     │
│  Current: 3.42 (Jan 2025)                     │
│  Velocity: +0.62 pts/year (Healthy)           │
│                                               │
│  RECOMMENDED NEXT STEPS                       │
│  • Address LOTO compliance (90-day priority)   │
│  • Implement failure code taxonomy (180 days)  │
│  • Schedule follow-up assessment (12 months)   │
└─────────────────────────────────────────────┘
```

### 2.2 Data Bindings

| Field          | Source                                           |
|----------------|--------------------------------------------------|
| Overall RMI    | `assessment.overall_rmi`                         |
| Maturity Level | `scoring_model.get_level(overall_rmi)`           |
| Percentile     | `benchmark_engine.get_percentile(assessment_id)` |
| Domain Scores  | `assessment.domains[*].score`                    |
| Spider Chart   | `assessment.subdomains[*].score` (15 axes)       |
| Strengths      | Top 5 subdomains by score                        |
| Priorities     | Top 5 by `practice_library.calculate_priority()` |
| Velocity       | `scoring_engine.maturity_velocity()`             |

---

## 3. Technical Detail Report (30-50 Pages)

### 3.1 Section Structure

```
1. Assessment Overview (2 pages)
   1.1 Site Information
   1.2 Assessment Scope & Methodology
   1.3 Auditor Team & Schedule
   1.4 Confidence Score & Limitations

2. Overall Results (3 pages)
   2.1 Overall RMI Score & Maturity Level
   2.2 Domain Score Summary
   2.3 Spider Chart & Heat Map
   2.4 Benchmark Comparison

3. Domain Detail — Workforce Capability (4-6 pages)
   3.1 Domain Score: X.X (Level N)
   3.2 Subdomain Scores
      3.2.1 WC.1 Technical Competency: X.X
      3.2.2 WC.2 Training & Development: X.X
      3.2.3 WC.3 Knowledge Management: X.X
   3.3 Key Findings
   3.4 Evidence Summary
   3.5 Cultural Blind Spots (if variance > 1.5)
   3.6 Recommendations

4. Domain Detail — Leadership & Culture (4-6 pages)
   [Same structure as §3]

5. Domain Detail — Work Management (4-6 pages)
   [Same structure as §3]

6. Domain Detail — Asset Information (4-6 pages)
   [Same structure as §3]

7. Domain Detail — Strategy & Governance (4-6 pages)
   [Same structure as §3]

8. Cross-Domain Analysis (3 pages)
   8.1 Domain Interaction Map
   8.2 Weakest-Link Caps Applied
   8.3 Critical Failure Items
   8.4 Systemic Themes

9. Improvement Roadmap (3-4 pages)
   9.1 Top 10 Improvement Actions (prioritized)
   9.2 Quick Wins (90-day)
   9.3 Medium-Term (6-12 months)
   9.4 Long-Term (12-24 months)
   9.5 Estimated Investment & ROI

10. Benchmarking Analysis (2-3 pages)
    10.1 Overall Percentile
    10.2 Domain Percentiles
    10.3 Peer Group Distribution
    10.4 Industry Trends

11. ISO 55001 Gap Summary (2 pages)
    11.1 Readiness Score
    11.2 Gap-to-Close by Clause

12. Appendices
    A. Question-Level Scores
    B. Evidence Inventory
    C. Interview Participant List (anonymized roles only)
    D. Observation Notes
    E. CMMS Data Summary
    F. Methodology & Scoring Model Reference
```

### 3.2 AI Narrative Generation

Each domain section includes an **AI-generated narrative** (GPT-4o / GPT-4o-mini):

```
PROMPT TEMPLATE:
"You are a senior reliability consultant. Based on the following subdomain 
scores and evidence, write a 200-word professional narrative summarizing 
the findings for {domain_name}. Use specific references to evidence. 
Tone: direct, constructive, no jargon. Write for a VP of Operations audience.

Subdomain Scores: {subdomain_scores}
Key Evidence: {evidence_summary}
Cultural Blind Spots: {blind_spots}
Weakest-Link Caps: {caps}
Industry Benchmark: {percentile}"
```

### 3.3 Chart Specifications

| Chart                   | Library                           | Placement          |
|-------------------------|-----------------------------------|--------------------|
| Spider Chart (15-axis)  | Matplotlib → PDF / Recharts → Web | §2.3, Exec Summary |
| Domain Bar Chart        | Matplotlib / Recharts             | §2.2               |
| Heat Map (5×3)          | Matplotlib / custom SVG           | §2.3               |
| Percentile Distribution | Matplotlib / Recharts             | §10.3              |
| Maturity Velocity Trend | Matplotlib / Recharts             | §2.4, Trend Report |
| ISO 55001 Gap Radar     | Matplotlib / Recharts             | §11                |

---

## 4. QuickScan Report (4-6 Pages)

### 4.1 Simplified Structure

```
1. Your RMI QuickScan Score: X.X (Level N)
   - Confidence note: "This is a self-assessment estimate"

2. Domain Overview (5 bars, one per domain)

3. Your Strengths (top 3 subdomains)

4. Your Opportunities (bottom 3 subdomains)

5. What Each Level Means (maturity scale reference)

6. Next Steps
   - "Your score suggests you're at Level N"
   - "Organizations at this level typically benefit from..."
   - CTA: "Get a Standard Assessment for validated results"
```

### 4.2 Design Intent

- **No evidence verification** → Report includes confidence caveat
- **No benchmarking** → Shows industry average as reference only
- **Lead generation** → Report designed to funnel toward Standard
- **Shareable** → PDF formatted for email sharing with executives

---

## 5. Trend Report (8-12 Pages)

### 5.1 Content

```
1. Assessment History Timeline
2. Overall RMI Trend (line chart with annotations)
3. Domain-Level Trends (5 small multiples)
4. Maturity Velocity Analysis
5. Improvement Action Tracking
   - Actions recommended vs. actions completed
   - Score impact of completed actions
6. Percentile Movement Over Time
7. Year-over-Year Comparison Table
8. Recommended Focus for Next Period
```

### 5.2 Trigger

Generated automatically when:
- 2+ assessments exist for the same site
- Time between assessments > 6 months
- Requested manually by client or auditor

---

## 6. Portfolio Dashboard (Enterprise)

### 6.1 Content

```
1. Portfolio Overview
   - Total sites assessed: N
   - Portfolio RMI: X.X
   - Portfolio percentile: Nth
   
2. Site Ranking Table
   - All sites ranked by RMI
   - Color-coded by maturity level
   - Velocity indicators (↑ ↓ →)
   
3. Domain Heat Map (sites × domains)
   - 5 columns (domains) × N rows (sites)
   - Color: green (≥4) / yellow (3-4) / red (<3)
   
4. Best Practice Transfer Opportunities
   - Highest-scoring site per domain
   - Recommended knowledge sharing pairs
   
5. Investment Prioritization
   - Sites with highest improvement potential
   - Estimated ROI for improvement programs
   
6. Industry Benchmarking
   - Portfolio vs. industry average per domain
```

---

## 7. Report Generation Architecture

### 7.1 v1 Architecture [OBSERVED: scoring_engine.py, models.py Report model]

- ReportLab for PDF generation
- Matplotlib for charts
- Stored as blob in Reports table
- Single report format

### 7.2 vNext Architecture

```
Report Generation Pipeline:

1. Score Calculation (scoring_engine)
        ↓
2. Benchmark Calculation (benchmark_engine)
        ↓
3. Practice Recommendations (practice_library)
        ↓
4. AI Narrative Generation (OpenAI API)
        ↓
5. Chart Generation (Matplotlib for PDF / Recharts data for web)
        ↓
6. Template Rendering
   ├── PDF: WeasyPrint (HTML → PDF) or ReportLab
   ├── Web: React components with Recharts
   └── PowerPoint: python-pptx (executive presentation)
        ↓
7. Storage (S3/Supabase Storage)
        ↓
8. Delivery (download link + email notification)
```

### 7.3 Template Engine

Migrate from pure-code report generation to **template-driven**:

```
templates/
├── executive-summary.html
├── technical-detail.html
├── quickscan-report.html
├── trend-report.html
├── portfolio-dashboard.html
├── iso-gap-report.html
└── components/
    ├── header.html
    ├── footer.html
    ├── spider-chart.html
    ├── domain-bar.html
    ├── heat-map.html
    └── recommendation-card.html
```

Benefits:
- Non-engineers can modify report layout
- White-label templates for consulting partners
- A/B testing of report formats
- Client-specific branding

---

## 8. White-Label Support

### 8.1 Customizable Elements

| Element             | Default                 | Customizable?                    |
|---------------------|-------------------------|----------------------------------|
| Logo                | NextBelt                | Yes — upload client/partner logo |
| Color scheme        | NextBelt brand          | Yes — primary, secondary, accent |
| Company name        | NextBelt LLC            | Yes — partner or client name     |
| Report title        | "RMI Assessment Report" | Yes — custom title               |
| Footer text         | "© NextBelt LLC"        | Yes — custom footer              |
| Cover page          | Standard                | Yes — custom cover template      |
| Methodology section | Standard                | No — ensures consistency         |
| Scoring model       | Standard                | No — ensures comparability       |

### 8.2 White-Label API

```
POST /api/v2/reports/{id}/generate
{
    "format": "pdf",
    "template": "executive-summary",
    "branding": {
        "logo_url": "https://...",
        "primary_color": "#1A365D",
        "company_name": "Reliability Partners Inc.",
        "custom_footer": "Powered by NextBelt RMI Platform"
    }
}
```

---

## 9. Report Delivery

### 9.1 Delivery Channels

| Channel            | Format               | Use Case                    |
|--------------------|----------------------|-----------------------------|
| In-app download    | PDF, PPTX            | Primary                     |
| Email              | PDF attachment       | Auto-delivery on completion |
| Shareable link     | Web view (read-only) | Executive sharing           |
| API                | JSON                 | System integration          |
| Scheduled delivery | PDF via email        | Portfolio quarterly reports |

### 9.2 Access Control

| Role             | Access                                     |
|------------------|--------------------------------------------|
| Site Admin       | All reports for their site                 |
| Auditor          | Reports they authored                      |
| Portfolio Admin  | All reports across their organization      |
| Client Executive | Executive summaries + portfolio dashboards |

---

*End of Report Templates Specification*
