"""
RMI Scoring Engine - Enterprise-Grade Calculation Logic
Transparent, defensible, audit-grade scoring with evidence validation
"""
from sqlalchemy.orm import Session
from models import (
    Assessment, QuestionResponse, Observation, DataAnalysis,
    Score, PillarType, QuestionBank
)
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime


class ScoringEngine:
    """
    Core scoring engine that calculates RMI scores
    Implements:
    - Weighted scoring by question importance
    - Evidence lock (no high scores without evidence)
    - Weakest link logic (critical failures cap pillar scores)
    - Role-based weighting (technician 60%, manager 20%, observations 20%)
    """
    
    # Role weights for calculating pillar scores
    ROLE_WEIGHTS = {
        "technician": 0.60,  # Ground truth - what's really happening
        "supervisor": 0.10,
        "manager": 0.20,     # Intent - what they think is happening
        "planner": 0.10,
        "auditor": 0.20      # Verification - observations & data
    }
    
    # Evidence requirements for scores
    EVIDENCE_THRESHOLD = 3  # Scores >= 4 require evidence
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_assessment_scores(self, assessment_id: int) -> Dict:
        """
        Calculate complete RMI scores for an assessment
        Returns: Dict with pillar scores, subcategory scores, and final RMI
        """
        assessment = self.db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        # Calculate scores for each pillar
        pillar_scores = {}
        for pillar in PillarType:
            pillar_score = self._calculate_pillar_score(assessment_id, pillar)
            pillar_scores[pillar.value] = pillar_score
        
        # Calculate overall RMI (average of three pillars)
        overall_rmi = sum(
            pillar_scores[p.value]['final_score'] 
            for p in PillarType
        ) / len(PillarType)
        
        # Save scores to database
        self._save_scores(assessment_id, pillar_scores, overall_rmi)
        
        return {
            "assessment_id": assessment_id,
            "pillar_scores": pillar_scores,
            "overall_rmi": round(overall_rmi, 2),
            "maturity_level": self._get_maturity_level(overall_rmi),
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_pillar_score(self, assessment_id: int, pillar: PillarType) -> Dict:
        """Calculate score for a single pillar with observations (20% weight)"""
        
        # Get all responses for this pillar (exclude drafts and N/A responses)
        responses = self.db.query(QuestionResponse, QuestionBank).join(
            QuestionBank
        ).filter(
            QuestionResponse.assessment_id == assessment_id,
            QuestionBank.pillar == pillar,
            QuestionResponse.is_draft == False,  # Exclude draft responses
            QuestionResponse.is_na == False      # Exclude N/A responses
        ).all()
        
        # Get all observations for this pillar
        observations = self.db.query(Observation).filter(
            Observation.assessment_id == assessment_id,
            Observation.pillar == pillar
        ).all()
        
        if not responses and not observations:
            return {
                "raw_score": 0,
                "weighted_score": 0,
                "final_score": 0,
                "confidence": "No Data",
                "evidence_coverage": 0,
                "observation_count": 0,
                "interview_score": 0,
                "observation_score": 0
            }
        
        # ==========================================
        # PART 1: Calculate Interview Score (80%)
        # ==========================================
        interview_score = 0
        total_weighted_score = 0
        total_weight = 0
        evidence_count = 0
        evidence_required_count = 0
        critical_failures = []
        
        for response, question in responses:
            if response.numeric_score is None:
                continue
            
            # Check evidence lock
            if question.evidence_required and response.numeric_score >= self.EVIDENCE_THRESHOLD:
                if not response.evidence_provided:
                    # Cannot score high without evidence - cap at 3
                    response.numeric_score = min(response.numeric_score, 3)
            
            # Track evidence coverage
            if question.evidence_required:
                evidence_required_count += 1
                if response.evidence_provided:
                    evidence_count += 1
            
            # Apply role weight and question weight
            role_weight = self.ROLE_WEIGHTS.get(question.target_role.value, 1.0)
            question_weight = question.weight or 1.0
            combined_weight = role_weight * question_weight
            
            total_weighted_score += response.numeric_score * combined_weight
            total_weight += combined_weight
            
            # Check for critical failures
            if question.is_critical and response.numeric_score <= 2:
                critical_failures.append({
                    "question_code": question.question_code,
                    "score": response.numeric_score,
                    "question": question.question_text
                })
        
        # Calculate interview score (80% weight)
        interview_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # ==========================================
        # PART 2: Calculate Observation Score (20%)
        # ==========================================
        observation_score = 0
        observation_critical_failures = []
        
        if observations:
            # Convert pass/fail to numeric scores
            obs_scores = []
            for obs in observations:
                if obs.pass_fail_result is not None:
                    # Pass = 5 points, Fail = 1 point
                    obs_numeric = 5 if obs.pass_fail_result else 1
                    obs_scores.append(obs_numeric)
                    
                    # Check for critical observation failures
                    if obs.type and 'safety' in obs.type.lower() and not obs.pass_fail_result:
                        observation_critical_failures.append({
                            "observation_title": obs.title,
                            "type": obs.type,
                            "severity": obs.severity,
                            "reason": "Safety observation failure"
                        })
            
            # Average observation score
            observation_score = sum(obs_scores) / len(obs_scores) if obs_scores else 0
        
        # ==========================================
        # PART 3: Combine Scores with Weights
        # ==========================================
        if observations and responses:
            # Both interviews and observations: 80/20 split
            combined_score = (interview_score * 0.80) + (observation_score * 0.20)
        elif responses:
            # Only interviews: use interview score
            combined_score = interview_score
        else:
            # Only observations: use observation score
            combined_score = observation_score
        
        # ==========================================
        # PART 4: Apply Weakest Link Logic
        # ==========================================
        final_score = combined_score
        
        # Interview critical failures
        if critical_failures:
            worst_critical = min(cf['score'] for cf in critical_failures)
            if worst_critical <= 2:
                final_score = min(final_score, 3.0)
        
        # Observation critical failures (Safety violations cap Process at 3.0)
        if observation_critical_failures and pillar == PillarType.PROCESS:
            final_score = min(final_score, 3.0)
        
        # Calculate confidence based on evidence coverage
        evidence_coverage = (evidence_count / evidence_required_count * 100) if evidence_required_count > 0 else 100
        confidence = self._calculate_confidence(evidence_coverage, len(responses))
        
        return {
            "raw_score": round(combined_score, 2),
            "weighted_score": round(combined_score, 2),
            "final_score": round(final_score, 2),
            "confidence": confidence,
            "evidence_coverage": round(evidence_coverage, 1),
            "critical_failures": critical_failures + observation_critical_failures,
            "response_count": len(responses),
            "observation_count": len(observations),
            "interview_score": round(interview_score, 2),
            "observation_score": round(observation_score, 2)
        }
    
    def _calculate_confidence(self, evidence_coverage: float, response_count: int) -> str:
        """Determine confidence level of the score"""
        if response_count < 3:
            return "Low - Insufficient Data"
        elif evidence_coverage < 50:
            return "Medium - Limited Evidence"
        elif evidence_coverage >= 80 and response_count >= 5:
            return "High - Well Evidenced"
        else:
            return "Medium - Adequate"
    
    def _get_maturity_level(self, rmi_score: float) -> str:
        """Convert numeric RMI to maturity description"""
        if rmi_score < 2.0:
            return "Level 1 - Reactive"
        elif rmi_score < 3.0:
            return "Level 2 - Emerging Preventive"
        elif rmi_score < 4.0:
            return "Level 3 - Preventive"
        elif rmi_score < 4.5:
            return "Level 4 - Predictive"
        else:
            return "Level 5 - Prescriptive"
    
    def _save_scores(self, assessment_id: int, pillar_scores: Dict, overall_rmi: float):
        """Save calculated scores to database"""
        
        # Delete existing scores for this assessment
        self.db.query(Score).filter(Score.assessment_id == assessment_id).delete()
        
        # Save pillar scores
        for pillar_name, pillar_data in pillar_scores.items():
            pillar_score = Score(
                assessment_id=assessment_id,
                pillar=PillarType(pillar_name),
                raw_score=pillar_data['raw_score'],
                weighted_score=pillar_data['weighted_score'],
                final_score=pillar_data['final_score'],
                confidence_level=pillar_data['confidence'],
                calculation_method=json.dumps({
                    "evidence_coverage": pillar_data['evidence_coverage'],
                    "critical_failures": pillar_data.get('critical_failures', [])
                })
            )
            self.db.add(pillar_score)
        
        # Save overall RMI score
        overall_score = Score(
            assessment_id=assessment_id,
            pillar=None,  # NULL indicates overall score
            raw_score=overall_rmi,
            weighted_score=overall_rmi,
            final_score=overall_rmi,
            confidence_level=self._get_overall_confidence(pillar_scores),
            calculation_method=json.dumps({
                "method": "Average of three pillar scores",
                "pillar_breakdown": {
                    pillar: data['final_score'] 
                    for pillar, data in pillar_scores.items()
                }
            })
        )
        self.db.add(overall_score)
        
        self.db.commit()
    
    def _get_overall_confidence(self, pillar_scores: Dict) -> str:
        """Calculate overall confidence from pillar confidences"""
        confidences = [data['confidence'] for data in pillar_scores.values()]
        if all('High' in c for c in confidences):
            return "High"
        elif any('Low' in c for c in confidences):
            return "Low"
        else:
            return "Medium"
    
    def validate_evidence_requirements(self, assessment_id: int) -> List[Dict]:
        """
        Check which high scores are missing required evidence
        Returns list of violations that need attention
        """
        violations = []
        
        responses = self.db.query(QuestionResponse, QuestionBank).join(
            QuestionBank
        ).filter(
            QuestionResponse.assessment_id == assessment_id
        ).all()
        
        for response, question in responses:
            if question.evidence_required and response.numeric_score >= self.EVIDENCE_THRESHOLD:
                if not response.evidence_provided:
                    violations.append({
                        "question_code": question.question_code,
                        "question_text": question.question_text,
                        "score": response.numeric_score,
                        "evidence_description": question.evidence_description,
                        "severity": "HIGH - Score will be capped at 3"
                    })
        
        return violations
    
    def get_score_breakdown(self, assessment_id: int) -> Dict:
        """
        Get detailed breakdown of scores by pillar and subcategory
        Useful for generating reports and identifying gaps
        """
        breakdown = {}
        
        for pillar in PillarType:
            responses = self.db.query(QuestionResponse, QuestionBank).join(
                QuestionBank
            ).filter(
                QuestionResponse.assessment_id == assessment_id,
                QuestionBank.pillar == pillar
            ).all()
            
            # Group by subcategory
            subcategories = {}
            for response, question in responses:
                subcat = question.subcategory
                if subcat not in subcategories:
                    subcategories[subcat] = {
                        "scores": [],
                        "questions": []
                    }
                
                subcategories[subcat]["scores"].append(response.numeric_score or 0)
                subcategories[subcat]["questions"].append({
                    "code": question.question_code,
                    "text": question.question_text,
                    "score": response.numeric_score,
                    "is_critical": question.is_critical
                })
            
            # Calculate subcategory averages
            breakdown[pillar.value] = {
                subcat: {
                    "average_score": round(sum(data["scores"]) / len(data["scores"]), 2) if data["scores"] else 0,
                    "question_count": len(data["questions"]),
                    "questions": data["questions"]
                }
                for subcat, data in subcategories.items()
            }
        
        return breakdown


def calculate_reactive_ratio(work_orders_df) -> Dict:
    """
    Calculate reactive vs preventive ratio from CMMS data
    Input: DataFrame with work order data
    Returns: Dict with metrics
    """
    import pandas as pd
    
    if not isinstance(work_orders_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    
    # Classify work orders
    # Assuming columns: 'work_order_type' or 'priority'
    total_wos = len(work_orders_df)
    
    # Common classifications (adjust based on actual CMMS)
    reactive_types = ['emergency', 'corrective', 'breakdown', 'urgent']
    
    if 'work_order_type' in work_orders_df.columns:
        reactive_count = work_orders_df[
            work_orders_df['work_order_type'].str.lower().isin(reactive_types)
        ].shape[0]
    elif 'priority' in work_orders_df.columns:
        # High priority assumed reactive
        reactive_count = work_orders_df[
            work_orders_df['priority'].isin(['1', 'Emergency', 'Urgent'])
        ].shape[0]
    else:
        raise ValueError("Cannot determine work order type - missing 'work_order_type' or 'priority' column")
    
    reactive_ratio = reactive_count / total_wos if total_wos > 0 else 0
    
    # Determine severity
    if reactive_ratio > 0.6:
        severity = "CRITICAL - REACTIVE SPIRAL"
        score = 1
    elif reactive_ratio > 0.4:
        severity = "HIGH - Reactive Dominant"
        score = 2
    elif reactive_ratio > 0.25:
        severity = "MEDIUM - Balanced but Reactive-Heavy"
        score = 3
    elif reactive_ratio > 0.15:
        severity = "GOOD - Preventive Focus"
        score = 4
    else:
        severity = "EXCELLENT - Proactive Maintenance"
        score = 5
    
    return {
        "metric": "Reactive Ratio",
        "total_work_orders": total_wos,
        "reactive_work_orders": reactive_count,
        "preventive_work_orders": total_wos - reactive_count,
        "reactive_ratio": round(reactive_ratio * 100, 1),
        "severity": severity,
        "score": score,
        "threshold_50_percent": reactive_ratio > 0.5
    }


def calculate_pm_compliance(pm_data_df) -> Dict:
    """
    Calculate PM compliance (on-time completion rate)
    Input: DataFrame with PM completion data
    """
    import pandas as pd
    
    if not isinstance(pm_data_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    
    # Assuming columns: 'due_date', 'completed_date'
    if 'due_date' not in pm_data_df.columns or 'completed_date' not in pm_data_df.columns:
        raise ValueError("Missing required columns: 'due_date' and 'completed_date'")
    
    # Convert to datetime
    pm_data_df['due_date'] = pd.to_datetime(pm_data_df['due_date'])
    pm_data_df['completed_date'] = pd.to_datetime(pm_data_df['completed_date'])
    
    # Calculate days late (allowing 7-day grace period)
    pm_data_df['days_late'] = (pm_data_df['completed_date'] - pm_data_df['due_date']).dt.days
    
    total_pms = len(pm_data_df)
    on_time_pms = len(pm_data_df[pm_data_df['days_late'] <= 7])
    late_pms = total_pms - on_time_pms
    
    compliance_rate = on_time_pms / total_pms if total_pms > 0 else 0
    
    # Score based on compliance
    if compliance_rate >= 0.95:
        score = 5
        severity = "EXCELLENT"
    elif compliance_rate >= 0.85:
        score = 4
        severity = "GOOD"
    elif compliance_rate >= 0.70:
        score = 3
        severity = "ACCEPTABLE"
    elif compliance_rate >= 0.50:
        score = 2
        severity = "POOR"
    else:
        score = 1
        severity = "CRITICAL - PM Program Breaking Down"
    
    return {
        "metric": "PM Compliance",
        "total_pms": total_pms,
        "on_time_pms": on_time_pms,
        "late_pms": late_pms,
        "compliance_rate": round(compliance_rate * 100, 1),
        "average_days_late": round(pm_data_df[pm_data_df['days_late'] > 0]['days_late'].mean(), 1),
        "severity": severity,
        "score": score
    }


def calculate_data_graveyard_index(work_orders_df) -> Dict:
    """
    Calculate data quality score (Data Graveyard Index)
    Measures how many WOs have meaningful closure data
    """
    import pandas as pd
    
    if not isinstance(work_orders_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    
    # Assuming column: 'closure_notes' or 'resolution'
    if 'closure_notes' not in work_orders_df.columns:
        raise ValueError("Missing 'closure_notes' column")
    
    total_wos = len(work_orders_df)
    
    # Generic/useless codes
    generic_codes = ['done', 'fixed', 'complete', 'ok', 'n/a', 'closed', '']
    
    # Count WOs with generic codes or very short notes
    poor_quality = work_orders_df[
        (work_orders_df['closure_notes'].str.lower().isin(generic_codes)) |
        (work_orders_df['closure_notes'].str.len() < 10)
    ].shape[0]
    
    graveyard_percentage = poor_quality / total_wos if total_wos > 0 else 0
    
    # Score
    if graveyard_percentage > 0.40:
        score = 1
        severity = "SEVERE DATA GRAVEYARD - Cannot perform RCA"
    elif graveyard_percentage > 0.20:
        score = 2
        severity = "POOR - Significant data quality issues"
    elif graveyard_percentage > 0.10:
        score = 3
        severity = "ACCEPTABLE - Some improvement needed"
    elif graveyard_percentage > 0.04:
        score = 4
        severity = "GOOD - Minor gaps"
    else:
        score = 5
        severity = "EXCELLENT - High data quality"
    
    return {
        "metric": "Data Graveyard Index",
        "total_work_orders": total_wos,
        "poor_quality_closures": poor_quality,
        "graveyard_percentage": round(graveyard_percentage * 100, 1),
        "severity": severity,
        "score": score
    }
