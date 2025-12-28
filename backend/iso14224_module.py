"""
ISO 14224 Data Integrity Audit Module
Validates CMMS data structure against ISO 14224 standards
"""
from sqlalchemy.orm import Session
from models import ISO14224Audit
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime


class ISO14224Validator:
    """
    Validates CMMS data structure and taxonomy against ISO 14224
    ISO 14224: Petroleum and natural gas industries — Collection and exchange of reliability and maintenance data for equipment
    
    Key validation areas:
    - Asset hierarchy structure
    - Failure mode classification
    - Event taxonomy
    - Maintenance taxonomy
    - Data completeness
    """
    
    # Required hierarchy levels per ISO 14224
    REQUIRED_HIERARCHY_LEVELS = [
        "Site/Facility",
        "Area/Unit",
        "System",
        "Equipment",
        "Component"
    ]
    
    # Standard failure mode categories per ISO 14224
    FAILURE_MODE_CATEGORIES = [
        "Breakdown",
        "Degraded",
        "External leakage",
        "Internal leakage",
        "Erratic output",
        "Fail to start",
        "Fail to stop",
        "Spurious operation",
        "Structural deficiency",
        "Parameter deviation"
    ]
    
    # Failure cause categories
    FAILURE_CAUSE_CATEGORIES = [
        "Design fault",
        "Installation fault",
        "Manufacturing fault",
        "Material fault",
        "Assembly fault",
        "Operational fault",
        "Maintenance fault",
        "External influence",
        "Wear out",
        "Miscellaneous"
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_asset_hierarchy(
        self,
        assessment_id: int,
        auditor_id: int,
        hierarchy_data: pd.DataFrame
    ) -> Dict:
        """
        Validate asset hierarchy depth and structure
        
        Args:
            hierarchy_data: DataFrame with asset hierarchy (columns representing levels)
        
        Returns:
            Validation results with pass/fail for each check
        """
        results = []
        
        # Check 1: Hierarchy depth
        hierarchy_depth = len([col for col in hierarchy_data.columns if 'level' in col.lower() or 'hierarchy' in col.lower()])
        
        depth_passed = hierarchy_depth >= 4
        results.append({
            "check_item": "Asset Hierarchy Depth",
            "check_category": "Hierarchy",
            "passed": depth_passed,
            "evidence_notes": f"Found {hierarchy_depth} levels. ISO 14224 recommends minimum 4 levels.",
            "impact_on_score": 1.0 if depth_passed else -1.0
        })
        
        # Check 2: Functional location structure
        # Look for consistent naming convention
        if 'functional_location' in hierarchy_data.columns:
            sample_locs = hierarchy_data['functional_location'].head(20)
            consistent_structure = self._check_naming_consistency(sample_locs)
            
            results.append({
                "check_item": "Functional Location Naming Consistency",
                "check_category": "Hierarchy",
                "passed": consistent_structure,
                "evidence_notes": "Checked 20 sample functional locations for consistent delimiter and structure",
                "impact_on_score": 0.5 if consistent_structure else -0.5
            })
        
        # Check 3: Component-level tracking
        component_level_exists = any('component' in col.lower() for col in hierarchy_data.columns)
        
        results.append({
            "check_item": "Component-Level Tracking",
            "check_category": "Hierarchy",
            "passed": component_level_exists,
            "evidence_notes": "Component level required for detailed RCA",
            "impact_on_score": 1.0 if component_level_exists else -1.0
        })
        
        # Save to database
        for result in results:
            self._save_audit_result(assessment_id, auditor_id, result)
        
        return {
            "total_checks": len(results),
            "passed_checks": sum(1 for r in results if r['passed']),
            "failed_checks": sum(1 for r in results if not r['passed']),
            "results": results
        }
    
    def validate_failure_taxonomy(
        self,
        assessment_id: int,
        auditor_id: int,
        failure_data: pd.DataFrame
    ) -> Dict:
        """
        Validate failure mode and cause classification against ISO 14224
        
        Args:
            failure_data: DataFrame with failure records (must have failure_mode, failure_cause columns)
        """
        results = []
        
        # Check 1: Failure mode field exists
        has_failure_mode = 'failure_mode' in failure_data.columns
        
        results.append({
            "check_item": "Failure Mode Field Exists",
            "check_category": "Failure Modes",
            "passed": has_failure_mode,
            "evidence_notes": "Failure mode classification is mandatory per ISO 14224",
            "impact_on_score": 2.0 if has_failure_mode else -2.0
        })
        
        if has_failure_mode:
            # Check 2: Failure modes align with standard categories
            unique_modes = failure_data['failure_mode'].dropna().unique()
            aligned_modes = [m for m in unique_modes if any(std in str(m).lower() for std in [fm.lower() for fm in self.FAILURE_MODE_CATEGORIES])]
            
            alignment_percentage = len(aligned_modes) / len(unique_modes) * 100 if len(unique_modes) > 0 else 0
            taxonomy_passed = alignment_percentage >= 70
            
            results.append({
                "check_item": "Failure Mode Taxonomy Alignment",
                "check_category": "Failure Modes",
                "passed": taxonomy_passed,
                "evidence_notes": f"{alignment_percentage:.1f}% of failure modes align with ISO 14224 standard categories",
                "impact_on_score": 1.5 if taxonomy_passed else -1.0
            })
        
        # Check 3: Failure cause tracking
        has_failure_cause = 'failure_cause' in failure_data.columns
        
        results.append({
            "check_item": "Failure Cause Field Exists",
            "check_category": "Failure Causes",
            "passed": has_failure_cause,
            "evidence_notes": "Root cause tracking enables reliability improvement",
            "impact_on_score": 1.0 if has_failure_cause else -1.0
        })
        
        # Check 4: Component-Failure Mode-Cause hierarchy
        required_fields = ['component', 'failure_mode', 'failure_cause']
        has_full_taxonomy = all(field in failure_data.columns for field in required_fields)
        
        results.append({
            "check_item": "Complete Failure Taxonomy (Component-Mode-Cause)",
            "check_category": "Taxonomy",
            "passed": has_full_taxonomy,
            "evidence_notes": "ISO 14224 requires three-level failure classification",
            "impact_on_score": 2.0 if has_full_taxonomy else -2.0
        })
        
        # Save to database
        for result in results:
            self._save_audit_result(assessment_id, auditor_id, result)
        
        return {
            "total_checks": len(results),
            "passed_checks": sum(1 for r in results if r['passed']),
            "failed_checks": sum(1 for r in results if not r['passed']),
            "results": results
        }
    
    def validate_data_completeness(
        self,
        assessment_id: int,
        auditor_id: int,
        data: pd.DataFrame,
        critical_fields: List[str]
    ) -> Dict:
        """
        Validate data completeness for critical fields
        
        Args:
            data: DataFrame to validate
            critical_fields: List of field names that must be populated
        """
        results = []
        
        for field in critical_fields:
            if field not in data.columns:
                results.append({
                    "check_item": f"Critical Field: {field}",
                    "check_category": "Data Completeness",
                    "passed": False,
                    "evidence_notes": f"Field '{field}' not found in data",
                    "impact_on_score": -1.0
                })
                continue
            
            # Calculate completeness
            total_records = len(data)
            populated_records = data[field].notna().sum()
            completeness = populated_records / total_records * 100 if total_records > 0 else 0
            
            passed = completeness >= 90  # 90% threshold
            
            results.append({
                "check_item": f"Critical Field: {field}",
                "check_category": "Data Completeness",
                "passed": passed,
                "evidence_notes": f"{completeness:.1f}% populated ({populated_records}/{total_records} records)",
                "impact_on_score": 0.5 if passed else -0.5
            })
        
        # Save to database
        for result in results:
            self._save_audit_result(assessment_id, auditor_id, result)
        
        return {
            "total_checks": len(results),
            "passed_checks": sum(1 for r in results if r['passed']),
            "failed_checks": sum(1 for r in results if not r['passed']),
            "results": results
        }
    
    def validate_closure_quality(
        self,
        assessment_id: int,
        auditor_id: int,
        work_orders: pd.DataFrame
    ) -> Dict:
        """
        Validate work order closure data quality
        Checks for meaningful closure codes and notes
        """
        results = []
        
        # Generic/useless closure codes
        generic_codes = ['done', 'fixed', 'complete', 'ok', 'closed', 'n/a', '']
        
        if 'closure_code' in work_orders.columns:
            total_wos = len(work_orders)
            generic_closures = work_orders[
                work_orders['closure_code'].str.lower().isin(generic_codes)
            ].shape[0]
            
            quality_percentage = (total_wos - generic_closures) / total_wos * 100 if total_wos > 0 else 0
            passed = quality_percentage >= 80
            
            results.append({
                "check_item": "Closure Code Quality",
                "check_category": "Data Quality",
                "passed": passed,
                "evidence_notes": f"{quality_percentage:.1f}% have meaningful closure codes (sample of {total_wos} WOs)",
                "impact_on_score": 1.5 if passed else -1.5
            })
        
        # Check closure notes length
        if 'closure_notes' in work_orders.columns:
            avg_note_length = work_orders['closure_notes'].str.len().mean()
            sufficient_detail = avg_note_length >= 20  # At least 20 characters on average
            
            results.append({
                "check_item": "Closure Notes Detail",
                "check_category": "Data Quality",
                "passed": sufficient_detail,
                "evidence_notes": f"Average closure note length: {avg_note_length:.0f} characters",
                "impact_on_score": 1.0 if sufficient_detail else -1.0
            })
        
        # Save to database
        for result in results:
            self._save_audit_result(assessment_id, auditor_id, result)
        
        return {
            "total_checks": len(results),
            "passed_checks": sum(1 for r in results if r['passed']),
            "failed_checks": sum(1 for r in results if not r['passed']),
            "results": results
        }
    
    def _check_naming_consistency(self, location_series: pd.Series) -> bool:
        """Check if functional locations follow consistent naming pattern"""
        # Look for consistent delimiter usage
        delimiters = ['-', '_', '.', '/']
        
        delimiter_counts = {d: 0 for d in delimiters}
        for loc in location_series:
            for delimiter in delimiters:
                if delimiter in str(loc):
                    delimiter_counts[delimiter] += 1
        
        # If one delimiter is used in >80% of locations, consider it consistent
        max_delimiter_usage = max(delimiter_counts.values()) if delimiter_counts else 0
        consistency = max_delimiter_usage / len(location_series) >= 0.8
        
        return consistency
    
    def _save_audit_result(
        self,
        assessment_id: int,
        auditor_id: int,
        result: Dict
    ):
        """Save individual audit check result to database"""
        audit_record = ISO14224Audit(
            assessment_id=assessment_id,
            audited_by=auditor_id,
            check_item=result['check_item'],
            check_category=result['check_category'],
            passed=result['passed'],
            evidence_notes=result['evidence_notes'],
            impact_on_score=result['impact_on_score']
        )
        
        self.db.add(audit_record)
        self.db.commit()
    
    def get_audit_summary(self, assessment_id: int) -> Dict:
        """Get summary of all ISO 14224 audit results for an assessment"""
        audits = self.db.query(ISO14224Audit).filter(
            ISO14224Audit.assessment_id == assessment_id
        ).all()
        
        total_checks = len(audits)
        passed_checks = sum(1 for a in audits if a.passed)
        failed_checks = total_checks - passed_checks
        
        total_impact = sum(a.impact_on_score for a in audits)
        
        # Calculate compliance score (1-5 scale)
        if total_checks == 0:
            compliance_score = 0
        else:
            pass_rate = passed_checks / total_checks
            # Convert to 1-5 scale
            if pass_rate >= 0.90:
                compliance_score = 5
            elif pass_rate >= 0.75:
                compliance_score = 4
            elif pass_rate >= 0.60:
                compliance_score = 3
            elif pass_rate >= 0.40:
                compliance_score = 2
            else:
                compliance_score = 1
        
        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "pass_rate": round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0,
            "compliance_score": compliance_score,
            "total_impact_on_score": total_impact,
            "by_category": self._group_by_category(audits)
        }
    
    def _group_by_category(self, audits: List[ISO14224Audit]) -> Dict:
        """Group audit results by category"""
        categories = {}
        
        for audit in audits:
            cat = audit.check_category
            if cat not in categories:
                categories[cat] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }
            
            categories[cat]["total"] += 1
            if audit.passed:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
        
        return categories
