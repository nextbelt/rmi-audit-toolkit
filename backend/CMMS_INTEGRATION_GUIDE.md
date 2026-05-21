"""
Comprehensive guide to CMMS Data Integration in RMI Audit Toolkit
"""

# ============================================================
# HOW CMMS DATA INTEGRATES INTO RMI SCORES
# ============================================================

"""
CMMS (Computerized Maintenance Management System) data uploads provide OBJECTIVE,
data-driven evidence for the TECHNOLOGY pillar scoring.

INTEGRATION FLOW:
1. Upload CSV/Excel file with work order data
2. System analyzes data and calculates metrics
3. Metrics are converted to 1-5 scores
4. Scores are integrated into Technology pillar calculation

WEIGHT IN SCORING:
- Technology Pillar (with CMMS data) = 60% Interviews + 20% Observations + 20% CMMS
- Technology Pillar (without CMMS data) = 80% Interviews + 20% Observations
- People Pillar = 80% Interviews + 20% Observations (no CMMS data)
- Process Pillar = 80% Interviews + 20% Observations (no CMMS data)

CMMS ONLY AFFECTS TECHNOLOGY PILLAR!
"""

# ============================================================
# DATA POINTS EXTRACTED FROM CMMS UPLOAD
# ============================================================

"""
1. REACTIVE RATIO (% of unplanned work vs total work)
   - Formula: (Reactive WOs / Total WOs) * 100
   - Scoring:
     * ≤15% → Score 5 (Excellent - proactive maintenance culture)
     * 15-25% → Score 4 (Good - balanced approach)
     * 25-40% → Score 3 (Fair - somewhat reactive)
     * 40-60% → Score 2 (Poor - mostly reactive)
     * >60% → Score 1 (Critical - fire-fighting mode)

2. PM COMPLIANCE (% of PMs completed on time)
   - Formula: (On-Time PMs / Total PMs) * 100
   - Scoring:
     * ≥95% → Score 5 (Excellent)
     * 85-95% → Score 4 (Good)
     * 75-85% → Score 3 (Fair)
     * 60-75% → Score 2 (Poor)
     * <60% → Score 1 (Critical)

3. DATA QUALITY (% of work orders with meaningful closure codes)
   - Formula: (Detailed WOs / Total WOs) * 100
   - Generic codes: "DONE", "FIXED", "COMPLETE" (don't count)
   - Detailed codes: "Replaced bearing", "Calibrated sensor" (count)
   - Scoring:
     * ≥90% → Score 5 (Excellent data for analytics)
     * 75-90% → Score 4 (Good data quality)
     * 60-75% → Score 3 (Fair - some detail lacking)
     * 40-60% → Score 2 (Poor - mostly generic)
     * <40% → Score 1 (Critical - data graveyard)

4. WORK TYPE DISTRIBUTION
   - Breakdown: Preventive, Corrective, Predictive, Emergency
   - Used for insights in report but not directly scored

5. TOTAL RECORDS ANALYZED
   - Number of work orders reviewed
   - Shown in UI for transparency
"""

# ============================================================
# REQUIRED CSV/EXCEL COLUMNS
# ============================================================

"""
MINIMUM REQUIRED COLUMNS (flexible names supported):

For Work Order Analysis:
- "WO Number" or "Work Order ID" or "WO#"
- "Type" or "WO Type" or "Work Type" (PM, CM, Emergency, etc.)
- "Status" or "WO Status" (Completed, Closed, etc.)
- "Created" or "Date Created" or "Entry Date"
- "Completed" or "Date Completed" or "Finish Date"
- "Notes" or "Resolution" or "Closure Notes" (for data quality analysis)

For PM Compliance Analysis:
- "PM Number" or "PM ID"
- "Due Date" or "Scheduled Date"
- "Completed Date" or "Actual Date"
- "Status"

EXAMPLE CSV FORMAT:
```csv
WO Number,Type,Status,Created,Completed,Notes
WO-12345,PM,Completed,2024-01-01,2024-01-02,Replaced bearing on pump P-101
WO-12346,CM,Completed,2024-01-03,2024-01-03,Fixed
WO-12347,Emergency,Completed,2024-01-05,2024-01-05,Motor failure - replaced motor
```
"""

# ============================================================
# HOW IT APPEARS IN THE REPORT
# ============================================================

"""
1. CMMS METRICS CARD (Frontend UI)
   Location: Assessment Detail page, below pillar scores
   Display:
   - Green success card with "CMMS Analysis Results"
   - Reactive Ratio: XX% (with ⚠️ warning if >40%)
   - PM Compliance: XX% (with ⚠️ warning if <75%)
   - Data Quality: XX%
   - Total Records: XX work orders analyzed
   - Info box: "Technology Pillar Score Impact: CMMS contributes 20%"

2. TECHNOLOGY PILLAR SCORE BREAKDOWN (Frontend UI)
   Location: Pillar score card
   Display:
   - Main score: X.X / 5.0
   - Component breakdown:
     * Interviews: X.X (60% weight)
     * Observations: X.X (20% weight)
     * CMMS Data: X.X (20% weight) ← Shows when CMMS data uploaded

3. PDF REPORT SECTIONS
   Location: Multiple sections throughout report
   
   a) Executive Summary:
      - Technology score includes CMMS impact
      - If CMMS shows poor data quality, flagged as key finding
   
   b) Key Findings (if CMMS data is poor):
      - "Data quality in CMMS limits analytics capability"
      - "High reactive ratio indicates fire-fighting mode"
      - "PM compliance below industry standards"
   
   c) Technology Pillar Section:
      - CMMS metrics table:
        | Metric              | Value  | Target | Status |
        |---------------------|--------|--------|--------|
        | Reactive Ratio      | XX%    | <25%   | ⚠️     |
        | PM Compliance       | XX%    | >90%   | ✓/⚠️   |
        | Data Quality        | XX%    | >80%   | ✓/⚠️   |
   
   d) Strategic Roadmap:
      - If CMMS data quality is poor: Recommends "Standardize CMMS closure codes"
      - If reactive ratio is high: Recommends "Reduce reactive maintenance"
      - If PM compliance is low: Recommends "Improve PM scheduling adherence"
"""

# ============================================================
# WEAKEST LINK LOGIC (CMMS Impact)
# ============================================================

"""
If CMMS Score < 2.0 → Technology pillar capped at 3.5 max

This prevents gaming the system:
- Even if interviews are good (4.0) and observations are good (4.0)
- If CMMS data shows terrible data quality (1.5)
- Technology pillar cannot exceed 3.5
- Rationale: Can't claim good technology practices with poor CMMS data

Example:
- Interview Score: 4.0
- Observation Score: 4.0
- CMMS Score: 1.5 (poor data quality)
- Without weakest link: (4.0 * 0.6) + (4.0 * 0.2) + (1.5 * 0.2) = 3.5
- With weakest link: min(3.5, 3.5) = 3.5 (cap triggered!)

If CMMS was 1.8:
- Calculated: (4.0 * 0.6) + (4.0 * 0.2) + (1.8 * 0.2) = 3.56
- Capped at: 3.5 (because CMMS < 2.0)
"""

# ============================================================
# TROUBLESHOOTING CMMS UPLOAD
# ============================================================

"""
Common Issues:

1. "File upload fails"
   - Check file format: Must be CSV or Excel (.xlsx)
   - Check column names: Must match expected patterns (see above)
   - Check file size: Should be under 10MB
   - Check backend logs: Look for "analyze-work-orders" endpoint errors

2. "Data uploaded but no CMMS score shown"
   - Click "Calculate Scores" button after upload
   - Check that assessment is not finalized (locked)
   - Verify Technology pillar calculation includes CMMS

3. "CMMS score seems wrong"
   - Check reactive ratio calculation: Are work types correctly classified?
   - Check data quality: Are closure notes too generic?
   - Review metrics in database: DataAnalysis table

4. "Frontend shows 'Cannot upload data to finalized assessment'"
   - Assessment is locked - cannot modify
   - Need to create new assessment or unlock (admin only)
"""

# ============================================================
# DATABASE STORAGE
# ============================================================

"""
Table: data_analyses

Columns:
- id (primary key)
- assessment_id (foreign key to assessments)
- analyzer_id (user who uploaded)
- analysis_type (e.g., "Work Order Analysis")
- metrics (JSON blob with all calculated metrics)
- data_source (filename of uploaded file)
- analyzed_at (timestamp)

Example metrics JSON:
{
  "reactive_ratio": {
    "reactive_ratio": 45.5,
    "reactive_count": 455,
    "total_count": 1000
  },
  "data_quality": {
    "closure_code_quality": 62.3,
    "detailed_count": 623,
    "generic_count": 377
  },
  "work_type_distribution": {
    "PM": 30,
    "CM": 50,
    "Emergency": 20
  },
  "total_records_analyzed": 1000,
  "analysis_date": "2025-01-15T10:30:00"
}
"""

print("=" * 80)
print("CMMS DATA INTEGRATION GUIDE LOADED")
print("=" * 80)
print("\nKey Points:")
print("✓ CMMS data ONLY affects Technology pillar (20% weight)")
print("✓ Analyzes: Reactive Ratio, PM Compliance, Data Quality")
print("✓ Poor CMMS data (<2.0) caps Technology at 3.5 max")
print("✓ Appears in: Frontend metrics card, pillar breakdown, PDF report")
print("✓ Upload via: Assessment Detail page → CMMS Upload button")
print("\nUpload CSV/Excel with columns: WO Number, Type, Status, Created, Completed, Notes")
