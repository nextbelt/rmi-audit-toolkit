# 🚨 SECURITY ALERT & IMPLEMENTATION ROADMAP

## CRITICAL: Immediate Action Required

### 1. **ROTATE ALL PRODUCTION CREDENTIALS IMMEDIATELY**

Your production credentials were found hardcoded in version control:
- Email: `nextbelt@next-belt.com`  
- Password: `C/aljan2026*`
- Production URL: `rmi-audit-toolkit-backend-production.up.railway.app`

**ACTION REQUIRED NOW:**
1. Log into Railway → Change admin password immediately
2. Create new admin account with secure credentials
3. Delete or disable the compromised `nextbelt@next-belt.com` account
4. Review Railway access logs for unauthorized access

### 2. **Fixed Files** ✅
- `seed_questions.py` - Now uses environment variables
- `test_response.py` - Now uses environment variables

### 3. **Remaining Security Improvements Needed**

#### A. Admin Initialization Security
**File**: `init_db.py`
**Issue**: Creates admin with hardcoded "admin123" password
**Fix**: 
```python
ADMIN_PASSWORD = os.getenv("ADMIN_INIT_PASSWORD")
if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = input("Set admin password: ")
    confirm = input("Confirm password: ")
    if ADMIN_PASSWORD != confirm:
        raise ValueError("Passwords don't match")
```

#### B. Remove Development Test Files from Production
**Files to exclude from deployment**:
- `create_local_user.py`
- `test_local.py`
- `init_local_db.py`
- All `test_*.py` files

**Update `.gitignore`**:
```
# Local development only - never deploy
create_local_user.py
test_local.py
init_local_db.py
test_*.py
```

---

## METHODOLOGY IMPROVEMENTS (High Priority)

### 1. Evidence Lock Enhancement

**File**: `scoring_engine.py` (Line ~100-115)

**Current Code**:
```python
if question.evidence_required and response.numeric_score >= self.EVIDENCE_THRESHOLD:
    if not response.evidence_provided:
        response.numeric_score = min(response.numeric_score, 3)
```

**ISSUE**: This caps the score but doesn't enforce it in final calculations.

**IMPROVED IMPLEMENTATION**:
```python
# In _calculate_pillar_score method
for response, question in responses:
    if response.numeric_score is None:
        continue
    
    # STRICT EVIDENCE LOCK - Cap at 3.0 if high score without evidence
    if question.evidence_required and response.numeric_score >= 4.0:
        if not response.evidence_provided:
            response.numeric_score = 3.0  # Hard cap, no exceptions
            # Log this for audit trail
            print(f"⚠️  Evidence lock applied to Q{question.question_code}: Score capped at 3.0 (no evidence)")
```

**Rationale**: Removes auditor subjectivity. A score of 5 ("World Class") MUST have photo/document evidence. Without it, maximum defensible score is 3 ("Managed but not optimized").

---

### 2. Dynamic Role Weighting

**File**: `scoring_engine.py` (Line ~125-140)

**Current Issue**: If no Technicians respond, their 60% weight is lost, deflating the score.

**IMPROVED IMPLEMENTATION**:
```python
def _calculate_pillar_score(self, assessment_id: int, pillar: PillarType) -> Dict:
    # Get all responses for this pillar
    responses = self.db.query(QuestionResponse, QuestionBank).join(
        QuestionBank
    ).filter(
        QuestionResponse.assessment_id == assessment_id,
        QuestionBank.pillar == pillar
    ).all()
    
    # Calculate ACTUAL role weights based on who responded
    role_counts = {}
    for response, question in responses:
        role = question.target_role.value
        role_counts[role] = role_counts.get(role, 0) + 1
    
    # Dynamically normalize weights
    actual_weights = {}
    total_base_weight = sum(
        self.ROLE_WEIGHTS.get(role, 1.0) * count 
        for role, count in role_counts.items()
    )
    
    for role, count in role_counts.items():
        base_weight = self.ROLE_WEIGHTS.get(role, 1.0)
        actual_weights[role] = (base_weight * count) / total_base_weight
    
    # Now apply actual_weights instead of hardcoded weights
    for response, question in responses:
        role_weight = actual_weights.get(question.target_role.value, 0.5)
        # ... rest of calculation
```

**Rationale**: If you only interview Managers and Auditors (no Technicians), their weights should sum to 100%, not leave a 60% gap.

---

### 3. Critical Question Pillar Cap

**File**: `scoring_engine.py` (Line ~150-170)

**Current Implementation**: Checks for critical failures but caps at 3.0.

**ENHANCED LOGIC**:
```python
# Apply CRITICAL FAILURE logic - severe cap
if critical_failures:
    worst_critical = min(cf['score'] for cf in critical_failures)
    
    if worst_critical == 1:  # Complete failure on critical item
        final_score = min(final_score, 2.0)  # Entire pillar capped at "Reactive"
        print(f"⚠️  CRITICAL FAILURE in {pillar.value}: Score capped at 2.0")
        print(f"   Failed question: {critical_failures[0]['question_code']}")
    elif worst_critical == 2:  # Major gap on critical item
        final_score = min(final_score, 3.0)  # Capped at "Managed"
        print(f"⚠️  Critical Gap in {pillar.value}: Score capped at 3.0")
```

**Example**: If LOTO (Lockout/Tagout) compliance scores a 1, the PROCESS pillar cannot exceed 2.0, even if planning/scheduling is perfect.

---

## QUESTION BANK ENHANCEMENTS (Medium Priority)

### 1. Expand Technology Pillar

**File**: `question_bank.py`

**Add these questions**:
```python
{
    "question_code": "T-07",
    "pillar": "TECHNOLOGY",
    "question_type": "LIKERT",
    "question_text": "Is operational data (SCADA/Historian) integrated with CMMS for automated work order triggering?",
    "target_role": "TECHNICIAN",
    "subcategory": "OT/IT Integration",
    "weight": 1.2,
    "evidence_required": True,
    "evidence_description": "Screenshot of integration, API documentation, or workflow diagram",
    "is_critical": False,
    "min_score": 0,
    "max_score": 5
},
{
    "question_code": "T-08",
    "pillar": "TECHNOLOGY",
    "question_type": "LIKERT",
    "question_text": "What is the cybersecurity posture for connected industrial assets (patch management, network segmentation)?",
    "target_role": "MANAGER",
    "subcategory": "Cyber-Physical Security",
    "weight": 1.5,
    "evidence_required": True,
    "evidence_description": "Network diagram, vulnerability scan report, or security policy documentation",
    "is_critical": True,  # Critical for modern plants
    "min_score": 0,
    "max_score": 5
},
{
    "question_code": "T-09",
    "pillar": "TECHNOLOGY",
    "question_type": "DATA_INPUT",
    "question_text": "What percentage of work orders are created from automated triggers (condition-based, time-based, or sensor-based)?",
    "target_role": "PLANNER",
    "subcategory": "Automation Maturity",
    "weight": 1.0,
    "evidence_required": True,
    "evidence_description": "CMMS report showing WO creation sources",
    "is_critical": False,
    "min_score": 0,
    "max_score": 5
}
```

---

### 2. Standardized Likert Scale Definitions

**File**: Create `maturity_framework.py`

```python
"""
Standard Maturity Definitions for All Questions
Use this matrix to ensure consistent scoring across auditors
"""

MATURITY_SCALE = {
    1: {
        "label": "Reactive / Ad Hoc",
        "description": "No formal process. Firefighting mode. Undocumented.",
        "indicators": [
            "No documentation exists",
            "Purely reactive maintenance",
            "Tribal knowledge only",
            "No metrics tracked"
        ]
    },
    2: {
        "label": "Initial / Controlled",
        "description": "Process exists but depends on individuals. Inconsistent application.",
        "indicators": [
            "Informal procedures exist",
            "Some documentation but not followed consistently",
            "Success depends on specific people",
            "Basic metrics tracked sporadically"
        ]
    },
    3: {
        "label": "Defined / Managed",
        "description": "Documented process. Standardized across teams. Moderately consistent.",
        "indicators": [
            "Formal documented procedures",
            "Training programs established",
            "Metrics tracked and reviewed monthly",
            "Some continuous improvement"
        ]
    },
    4: {
        "label": "Optimized / Proactive",
        "description": "Data-driven. Continuous improvement culture. Predictive capabilities.",
        "indicators": [
            "Data drives decision-making",
            "Predictive analytics in use",
            "Continuous improvement culture",
            "Benchmarking against industry standards"
        ]
    },
    5: {
        "label": "World Class / Excellence",
        "description": "Best-in-class. Fully integrated. Predictive and prescriptive.",
        "indicators": [
            "Industry-leading performance",
            "Automated predictive maintenance",
            "Full digital twin integration",
            "Regularly benchmarked as top quartile"
        ]
    }
}
```

**Usage in Frontend**: Display this matrix in the `InterviewInterface.tsx` to guide auditors during scoring.

---

## DATA ANALYSIS ENHANCEMENTS (Medium Priority)

### 1. Fuzzy Column Matching

**File**: `data_analysis_module.py`

**Add dependency**: `pip install thefuzz[speedup]`

```python
from thefuzz import process, fuzz

class CMMSDataAnalyzer:
    
    # Common aliases for WO fields
    COLUMN_ALIASES = {
        "work_order_number": ["WO #", "OrderID", "Work Order", "WO Number", "Reference", "WO"],
        "equipment_id": ["Asset", "Equipment", "Tag", "Asset ID", "Equipment Tag", "Unit"],
        "description": ["Notes", "Work Description", "Comments", "Details", "Problem"],
        "start_date": ["Created", "Open Date", "Start", "Opened", "Issue Date"],
        "completion_date": ["Closed", "Complete", "Finished", "Resolved", "Closed Date"],
        "work_type": ["Type", "Category", "Work Category", "PM Type", "Order Type"],
        "labor_hours": ["Hours", "Labor", "Manhours", "Time", "Duration"]
    }
    
    def _smart_map_columns(self, df_columns: list, required_field: str) -> str:
        """
        Use fuzzy matching to automatically map CSV columns to required fields
        
        Args:
            df_columns: List of actual column names from uploaded CSV
            required_field: The field we need (e.g., "work_order_number")
        
        Returns:
            Best matching column name, or None if no good match found
        """
        possible_names = self.COLUMN_ALIASES.get(required_field, [required_field])
        
        # Fuzzy match against all possible names
        best_match = None
        best_score = 0
        
        for col in df_columns:
            for possible in possible_names:
                score = fuzz.ratio(col.lower(), possible.lower())
                if score > best_score:
                    best_score = score
                    best_match = col
        
        # Require at least 70% match confidence
        if best_score >= 70:
            print(f"✅ Auto-mapped '{required_field}' → '{best_match}' (confidence: {best_score}%)")
            return best_match
        
        return None
    
    def import_work_orders(self, file_path: str, column_mapping: dict = None):
        """Enhanced with auto-mapping"""
        df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
        
        # If no manual mapping provided, try auto-mapping
        if not column_mapping:
            column_mapping = {}
            for required_field in ["work_order_number", "equipment_id", "description", ...]:
                auto_mapped = self._smart_map_columns(df.columns.tolist(), required_field)
                if auto_mapped:
                    column_mapping[required_field] = auto_mapped
                else:
                    print(f"⚠️  Could not auto-map '{required_field}' - manual mapping required")
        
        # ... rest of import logic
```

---

### 2. Enhanced Data Graveyard Detection

**File**: `data_analysis_module.py` (Line ~250-280)

**Current Code**:
```python
GENERIC_WORDS = ["done", "fixed", "ok", "complete"]
```

**ENHANCED VERSION**:
```python
DATA_GRAVEYARD_INDICATORS = {
    # Vague closures with no detail
    "generic_closure": [
        "done", "fixed", "ok", "complete", "finished", "resolved",
        "checked", "inspected", "repaired", "changed part"
    ],
    
    # Copy-paste descriptions
    "lazy_descriptions": [
        "see above", "as per", "same as before", "ditto",
        "n/a", "na", "none", "\\-", "\\."  # Just dashes or periods
    ],
    
    # Zero-effort closes
    "zero_hour_work": [
        # Detected by checking labor_hours == 0 AND status == "Complete"
    ],
    
    # PM compliance red flags
    "pm_gaming": [
        "skipped", "not required", "deferred", "weather",
        "parts on order", "will do next time"
    ]
}

def calculate_data_graveyard_index(self, assessment_id: int) -> dict:
    """Enhanced DGI calculation"""
    # ... existing logic ...
    
    # NEW: Check for zero-hour completions
    zero_hour_wos = wo_df[
        (wo_df['labor_hours'] == 0) & 
        (wo_df['status'].str.lower() == 'complete')
    ]
    zero_hour_pct = (len(zero_hour_wos) / total_wos) * 100
    
    # Flag PM gaming behaviors
    pm_gaming_count = 0
    for desc in wo_df['description'].str.lower():
        if any(word in desc for word in DATA_GRAVEYARD_INDICATORS['pm_gaming']):
            pm_gaming_count += 1
    
    # Calculate composite DGI
    dgi_score = (
        (generic_pct * 0.4) +  # Generic closures
        (zero_hour_pct * 0.3) +  # Zero-hour work
        (pm_gaming_count / total_wos * 100 * 0.3)  # PM gaming
    )
    
    return {
        "data_graveyard_index": round(dgi_score, 1),
        "generic_closure_pct": round(generic_pct, 1),
        "zero_hour_completion_pct": round(zero_hour_pct, 1),
        "pm_gaming_flags": pm_gaming_count,
        "recommendation": self._get_dgi_recommendation(dgi_score)
    }
```

---

## IMPLEMENTATION PRIORITY ROADMAP

### 🔴 **Phase 1: CRITICAL (Do Immediately)**
1. ✅ Remove hardcoded production credentials
2. ✅ Add environment variable checks to all scripts
3. 🔲 Rotate production passwords on Railway
4. 🔲 Review Railway logs for unauthorized access
5. 🔲 Update `.gitignore` to exclude test scripts

### 🟠 **Phase 2: HIGH PRIORITY (This Week)**
1. 🔲 Implement strict Evidence Lock (scoring_engine.py)
2. 🔲 Add dynamic role weighting
3. 🔲 Enforce critical question pillar cap
4. 🔲 Create maturity_framework.py for consistent scoring

### 🟡 **Phase 3: MEDIUM PRIORITY (Next 2 Weeks)**
1. 🔲 Expand Technology pillar questions (T-07, T-08, T-09)
2. 🔲 Implement fuzzy column matching in data analyzer
3. 🔲 Enhance Data Graveyard Index calculation
4. 🔲 Add maturity scale definitions to frontend

### 🟢 **Phase 4: ENHANCEMENT (Next Month)**
1. 🔲 Implement PWA for offline capability
2. 🔲 Add service worker for data sync
3. 🔲 Create admin dashboard for AI score review
4. 🔲 Add inconsistency detection (cross-role score variance)

---

## TESTING CHECKLIST

Before deploying any changes:
- [ ] All environment variables documented in `.env.example`
- [ ] No hardcoded credentials remain in codebase
- [ ] Scoring engine tests pass with new logic
- [ ] AI scoring works with enhanced methodology
- [ ] Data Graveyard Index calculation verified with sample data
- [ ] Frontend displays maturity definitions correctly

---

## ESTIMATED EFFORT

- **Phase 1 (Critical Security)**: 2-4 hours
- **Phase 2 (Scoring Improvements)**: 8-12 hours
- **Phase 3 (Feature Enhancements)**: 16-24 hours
- **Phase 4 (Advanced Features)**: 40-60 hours

**Total**: 66-100 hours of development work

---

## QUESTIONS FOR STAKEHOLDERS

1. **Security**: Have you verified there's been no unauthorized access to production?
2. **Methodology**: Do you want to pilot the stricter evidence lock on one assessment first?
3. **Question Bank**: Which additional Technology questions are highest priority?
4. **Data Analysis**: Do you have sample CMMS exports we can use to test fuzzy matching?
5. **Timeline**: What's the target date for Phase 2 completion?

---

**Next Steps**: 
1. Review this roadmap
2. Prioritize which improvements to implement first
3. Set up a staging environment to test changes before production deployment
