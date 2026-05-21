# 09 — Practice Library Specification

**Document ID:** RMI-VNEXT-09  
**Status:** FINAL  
**Author:** NextBelt AI Engineering  
**Date:** 2025-01-19  
**Audience:** Consulting · Product · Engineering

---

## 1. Purpose

The Practice Library is the **prescriptive backbone** of the RMI vNext platform. It answers the question every client asks after seeing their score: **"What do I do now?"**

Every question in the question bank links to a Practice Library entry via `practice_link`. The library provides:
- Concrete, actionable guidance to move from current maturity level to the next
- Implementation playbooks with timelines and resource estimates
- Tool templates, checklists, and reference artifacts
- Success metrics to validate improvement

---

## 2. Practice Library Structure

### 2.1 Entry Schema

```json
{
    "practice_id": "WM.1-01-P",
    "title": "Implementing a Work Planning Process",
    "subdomain": "WM.1",
    "linked_questions": ["WM.1-01", "WM.1-02", "WM.1-03"],
    "maturity_pathways": {
        "1_to_2": {
            "title": "From Reactive to Emerging",
            "description": "Establish a basic planning function",
            "actions": [
                "Assign a dedicated Planner role (even part-time)",
                "Create a standard job plan template (5-field minimum)",
                "Begin writing job plans for the top 20 PM tasks by frequency",
                "Establish a weekly scheduling meeting with Operations"
            ],
            "timeline": "60-90 days",
            "resources": "0.5 FTE Planner + Supervisor buy-in",
            "success_metrics": [
                "Job plans exist for top 20 PM tasks",
                "Weekly scheduling meeting occurring consistently",
                "Planned work > 30% of total WOs"
            ],
            "tools": ["job-plan-template-basic.xlsx", "weekly-scheduling-meeting-agenda.docx"]
        },
        "2_to_3": {
            "title": "From Emerging to Systematic",
            "description": "Standardize and expand planning coverage",
            "actions": [
                "Expand job plans to cover all PM and top 50 CM tasks",
                "Implement a formal backlog management process",
                "Define schedule compliance KPI (target: >80%)",
                "Train all Planners on estimating labor, parts, and duration",
                "Implement a kitting process for planned jobs"
            ],
            "timeline": "90-180 days",
            "resources": "1 FTE Planner per 20 technicians",
            "success_metrics": [
                "Schedule compliance >80%",
                "Planned work >60% of total WOs",
                "Backlog aging report reviewed weekly",
                "Kitting in place for >50% of planned jobs"
            ],
            "tools": ["backlog-management-guide.pdf", "schedule-compliance-tracker.xlsx"]
        },
        "3_to_4": {
            "title": "From Systematic to Proactive",
            "description": "Data-driven planning optimization",
            "actions": [
                "Implement job plan feedback loop (post-job reviews)",
                "Use historical data to optimize labor/duration estimates",
                "Establish priority system based on criticality and risk",
                "Integrate CMMS with procurement for auto-kitting",
                "Implement multi-week scheduling (3-4 week horizon)"
            ],
            "timeline": "6-12 months",
            "resources": "Dedicated Planning & Scheduling team",
            "success_metrics": [
                "Schedule compliance >90%",
                "Planned work >80% of total WOs",
                "Job plan accuracy within ±20% of estimates",
                "Zero unplanned stockouts on planned jobs"
            ],
            "tools": ["job-plan-feedback-form.pdf", "criticality-assessment-matrix.xlsx"]
        },
        "4_to_5": {
            "title": "From Proactive to Prescriptive",
            "description": "World-class planning and scheduling",
            "actions": [
                "AI-assisted job plan generation from CMMS history",
                "Predictive scheduling based on condition monitoring triggers",
                "Automated resource optimization across multiple units",
                "Integration with production planning (S&OP alignment)",
                "Continuous improvement of planning KPIs with statistical control"
            ],
            "timeline": "12-18 months",
            "resources": "Advanced analytics + dedicated Reliability Engineering",
            "success_metrics": [
                "Schedule compliance >95%",
                "Planned work >90% of total WOs",
                "Schedule breaks due to emergencies <5%",
                "Planning accuracy within ±10%"
            ],
            "tools": ["spc-kpi-tracking-template.xlsx"]
        }
    },
    "references": [
        { "type": "standard", "title": "SMRP Best Practice 5.4 — Planning & Scheduling" },
        { "type": "book", "title": "Maintenance Planning & Scheduling Handbook, Richard Palmer, 4th Ed." },
        { "type": "iso", "title": "ISO 55001:2014 §6.2 — Asset Management Objectives" }
    ],
    "industry_variations": {
        "ONG": "Add turnaround planning integration; align with RAGAGEP requirements",
        "FNB": "Include sanitation schedule integration; align with Master Sanitation Schedule",
        "PHA": "Add change control (MOC) integration for planned modifications"
    }
}
```

### 2.2 Practice Catalog Summary

| Domain | Subdomain                         | Practice Entries | Key Practices                                                      |
|--------|-----------------------------------|------------------|--------------------------------------------------------------------|
| WC     | WC.1 Technical Competency         | 5                | Skills matrix, certification program, OJT structure                |
| WC     | WC.2 Training & Development       | 5                | Training needs analysis, budget justification, e-learning          |
| WC     | WC.3 Knowledge Management         | 5                | Mentoring program, knowledge base, tribal knowledge capture        |
| LC     | LC.1 Management Commitment        | 5                | Reliability business case, maintenance budget model, staffing plan |
| LC     | LC.2 Safety & Reliability Culture | 5                | Stop-work authority program, near-miss reporting, just culture     |
| LC     | LC.3 Organizational Structure     | 5                | Planner/scheduler org design, RE role definition, RACI matrix      |
| WM     | WM.1 Planning & Scheduling        | 5                | Job planning process, backlog management, scheduling protocol      |
| WM     | WM.2 PM/PdM                       | 5                | PM optimization, PdM technology roadmap, RCM implementation        |
| WM     | WM.3 Work Execution & Quality     | 5                | SOP program, LOTO compliance, first-time fix improvement           |
| AI     | AI.1 CMMS/EAM Effectiveness       | 5                | CMMS selection guide, mobile deployment, workflow design           |
| AI     | AI.2 Data Quality & Integrity     | 5                | Failure code taxonomy, WO closure standards, asset hierarchy       |
| AI     | AI.3 Analytics & Decision Support | 5                | Bad actor analysis, dashboard design, predictive model pilot       |
| SG     | SG.1 Asset Management Policy      | 5                | AM policy template, risk register, ISO 55001 roadmap               |
| SG     | SG.2 Performance Measurement      | 5                | KPI framework, OEE implementation, maintenance cost model          |
| SG     | SG.3 Continuous Improvement       | 5                | RCA process, improvement tracking, management review protocol      |

**Total: 75 practice entries** covering all 15 subdomains × 5 key practices each.

---

## 3. Practice-Score Linkage

### 3.1 Automatic Recommendation Engine

After scoring, the platform automatically generates practice recommendations:

```
FUNCTION generate_recommendations(assessment):
    recommendations = []
    
    FOR each subdomain in assessment.subdomains:
        current_level = get_maturity_level(subdomain.score)
        next_level = current_level + 1
        
        IF next_level > 5:
            CONTINUE  // already at max
        
        pathway_key = f"{current_level}_to_{next_level}"
        
        FOR each linked_practice in subdomain.practice_links:
            practice = get_practice(linked_practice)
            recommendation = {
                "subdomain": subdomain.code,
                "current_level": current_level,
                "target_level": next_level,
                "practice": practice.title,
                "actions": practice.maturity_pathways[pathway_key].actions,
                "timeline": practice.maturity_pathways[pathway_key].timeline,
                "priority": calculate_priority(subdomain)
            }
            recommendations.append(recommendation)
    
    SORT recommendations BY priority DESC
    RETURN TOP 10 recommendations  // focus on highest-impact
```

### 3.2 Priority Calculation

```
Priority = (impact_score × feasibility_score × urgency_score)

WHERE:
    impact_score = domain_weight × question_weight × gap_to_next_level
    feasibility_score = 1.0 / timeline_months  // faster = higher priority
    urgency_score = 2.0 IF weakest_link_cap_active ELSE 1.0
```

### 3.3 Report Integration

The assessment report includes a **"Top 10 Improvement Actions"** section:

```markdown
## Your Top 10 Improvement Actions

1. **[CRITICAL] Implement LOTO Compliance Program** (WM.3)
   Current: Level 2 → Target: Level 3
   Timeline: 60-90 days | Impact: Removes domain cap at 3.0
   
2. **Establish Work Planning Function** (WM.1)
   Current: Level 1 → Target: Level 2
   Timeline: 60-90 days | Impact: +0.8 points on WM domain
   
3. **Deploy Failure Code Taxonomy** (AI.2)
   Current: Level 2 → Target: Level 3
   Timeline: 90-180 days | Impact: +0.5 points on AI domain
   
...
```

---

## 4. Tool Library

### 4.1 Downloadable Templates

Each practice entry links to downloadable tools:

| Tool Type              | Count | Examples                                                     |
|------------------------|-------|--------------------------------------------------------------|
| Excel Templates        | ~25   | Skills matrix, PM schedule, criticality matrix, KPI tracker  |
| Word Templates         | ~15   | AM policy, SOP template, RCA report, training plan           |
| PDF Guides             | ~20   | Implementation playbooks, best practice summaries            |
| Checklist Templates    | ~10   | Audit checklists, LOTO verification, PM task lists           |
| Presentation Templates | ~5    | Executive briefing, reliability business case, training deck |

### 4.2 Tool Naming Convention

```
{subdomain_code}-{practice_number}-{tool_type}-{description}.{ext}

Example: WM.1-01-T-job-plan-template.xlsx
         WM.1-01-G-planning-implementation-guide.pdf
         LC.2-02-C-near-miss-reporting-checklist.docx
```

### 4.3 Tool Versioning

- Tools are versioned with semantic versioning (v1.0, v1.1, v2.0)
- Industry-variant tools are suffixed: `WM.1-01-T-job-plan-template-FNB.xlsx`
- Deprecated tools are archived, not deleted

---

## 5. Commercial Model Integration

### 5.1 Access Tiers

| Tier                 | Practice Access                             | Tool Access                        |
|----------------------|---------------------------------------------|------------------------------------|
| **Free (QuickScan)** | Summary recommendations (titles only)       | None                               |
| **Standard**         | Full practice entries for scored subdomains | Basic templates (5 per assessment) |
| **DeepDive**         | Full practice library access                | All templates + industry variants  |
| **Enterprise**       | Full library + custom practices             | All + custom tool development      |
| **Consultant**       | Full library + white-label                  | All + editable source files        |

### 5.2 Consulting Revenue Integration

The Practice Library serves as the **consulting engagement funnel**:

```
QuickScan (Free)
    → "You scored Level 2 in WM.1. Here's what Level 3 looks like."
    → CTA: "Get a Standard Assessment to identify specific gaps"

Standard Assessment (Paid)
    → "Here are your top 10 actions with implementation guides."
    → CTA: "Need help implementing? Schedule a consulting engagement."

DeepDive Assessment (Premium)
    → Full practice library + custom implementation roadmap
    → CTA: "Our consultants can lead your transformation program."

Consulting Engagement (High-Value)
    → Consultants use Practice Library as structured delivery framework
    → Progress tracked via follow-up assessments
    → Revenue: Assessment license + consulting days + annual reassessment
```

---

## 6. Content Maintenance

### 6.1 Review Cycle

| Content Type           | Review Frequency           | Reviewer                        |
|------------------------|----------------------------|---------------------------------|
| Practice entries       | Annually                   | Subject Matter Expert + Product |
| Tool templates         | Semi-annually              | Consulting team                 |
| Industry variations    | Annually                   | Industry SME                    |
| References & standards | When standards are updated | Standards liaison               |

### 6.2 Content Contribution Model

1. **Internal** — NextBelt consulting team creates and maintains core content
2. **Client-Contributed** — Anonymized best practices from DeepDive engagements (with consent)
3. **Partner-Contributed** — CMMS vendors, training providers contribute domain-specific content
4. **Community** — Future: user-contributed tips and case studies (moderated)

---

## 7. API Endpoints

### 7.1 Get Recommendations for Assessment

```
GET /api/v2/assessments/{id}/recommendations
Query params:
    ?limit=10
    &sort_by=priority
    &include_tools=true
```

### 7.2 Get Practice Entry

```
GET /api/v2/practices/{practice_id}
Query params:
    ?industry_module=FNB
    &current_level=2
    &target_level=3
```

### 7.3 List Practices by Subdomain

```
GET /api/v2/practices?subdomain=WM.1
```

### 7.4 Download Tool

```
GET /api/v2/practices/{practice_id}/tools/{tool_filename}
```

---

*End of Practice Library Specification*
