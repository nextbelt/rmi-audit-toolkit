"""
RMI Scoring Engine - Enterprise-Grade Calculation Logic
Transparent, defensible, audit-grade scoring with evidence validation

Strategic Evolution Features:
- Confidence Variance (Cultural Blind Spot Detection)
- Maturity Velocity (Temporal Analysis)
- ISO 55001 Alignment Mapping
- Risk-Adjusted Weighting
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import (
    Assessment, QuestionResponse, Observation, DataAnalysis,
    Score, PillarType, QuestionBank, User
)
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from statistics import stdev, mean
from dateutil.relativedelta import relativedelta


class ScoringEngine:
    """
    Core scoring engine that calculates RMI scores
    Implements:
    - Weighted scoring by question importance
    - Evidence lock (no high scores without evidence)
    - Weakest link logic (critical failures cap pillar scores)
    - Role-based weighting (technician 60%, manager 20%, observations 20%)
    - Confidence Variance (Cultural Blind Spot Detection)
    - Maturity Velocity (Temporal Analysis)
    - Risk-Adjusted Weighting
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
    
    # Confidence Variance threshold for cultural disconnect
    CULTURAL_DISCONNECT_THRESHOLD = 1.5
    
    # ISO 55001 Clause Mappings
    ISO_55001_MAPPINGS = {
        "PEOPLE": "7.2",      # Competence
        "PROCESS": "8.1",     # Operational Planning and Control
        "TECHNOLOGY": "7.5"   # Information Requirements
    }
    
    # High-risk industries that get increased Process pillar weight
    HIGH_RISK_INDUSTRIES = ["oil & gas", "oil and gas", "chemical", "nuclear", "mining", "refinery"]
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_assessment_scores(self, assessment_id: int) -> Dict:
        """
        Calculate complete RMI scores for an assessment
        Returns: Dict with pillar scores, subcategory scores, final RMI,
                 confidence variance, maturity velocity, and ISO gap analysis
        """
        assessment = self.db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()
        
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        # Get site criticality multiplier for risk-adjusted weighting
        site_criticality = assessment.site_criticality or 1.0
        is_high_risk = (assessment.industry or "").lower() in self.HIGH_RISK_INDUSTRIES
        
        # Calculate scores for each pillar
        pillar_scores = {}
        confidence_variance = {}
        iso_gap_analysis = {}
        
        for pillar in PillarType:
            # Apply risk-adjusted weighting for Process pillar in high-risk industries
            risk_multiplier = site_criticality if (pillar == PillarType.PROCESS and is_high_risk) else 1.0
            
            pillar_score = self._calculate_pillar_score(assessment_id, pillar, risk_multiplier)
            pillar_scores[pillar.value] = pillar_score
            
            # Calculate confidence variance (Cultural Blind Spot Detection)
            variance_result = self._calculate_confidence_variance(assessment_id, pillar)
            confidence_variance[pillar.value] = variance_result
            
            # Map to ISO 55001
            iso_gap_analysis[pillar.value] = self._analyze_iso_55001_gaps(assessment_id, pillar)
        
        # Calculate overall RMI (average of three pillars)
        overall_rmi = sum(
            pillar_scores[p.value]['final_score'] 
            for p in PillarType
        ) / len(PillarType)
        
        # Calculate Maturity Velocity (compare to previous assessment)
        maturity_velocity = self._calculate_maturity_velocity(
            assessment.site_name, 
            assessment.assessment_date, 
            overall_rmi,
            assessment_id
        )
        
        # Save scores to database
        self._save_scores(assessment_id, pillar_scores, overall_rmi)
        
        return {
            "assessment_id": assessment_id,
            "pillar_scores": pillar_scores,
            "overall_rmi": round(overall_rmi, 2),
            "maturity_level": self._get_maturity_level(overall_rmi),
            "calculated_at": datetime.utcnow().isoformat(),
            
            # Strategic Evolution: New Analytics
            "confidence_variance": confidence_variance,
            "maturity_velocity": maturity_velocity,
            "iso_gap_analysis": iso_gap_analysis,
            "risk_adjusted": {
                "site_criticality": site_criticality,
                "is_high_risk_industry": is_high_risk,
                "industry": assessment.industry
            }
        }
    
    def _calculate_pillar_score(self, assessment_id: int, pillar: PillarType, risk_multiplier: float = 1.0) -> Dict:
        """Calculate score for a single pillar with observations (20% weight)
        
        Args:
            assessment_id: The assessment ID
            pillar: The pillar type (PEOPLE, PROCESS, TECHNOLOGY)
            risk_multiplier: Risk adjustment factor (1.0-2.0) for high-risk industries
        """
        
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
        
        # Get CMMS data analysis (Technology pillar only)
        data_analyses = []
        if pillar == PillarType.TECHNOLOGY:
            data_analyses = self.db.query(DataAnalysis).filter(
                DataAnalysis.assessment_id == assessment_id
            ).all()
        
        if not responses and not observations and not data_analyses:
            return {
                "raw_score": 0,
                "weighted_score": 0,
                "final_score": 0,
                "confidence": "No Data",
                "evidence_coverage": 0,
                "observation_count": 0,
                "interview_score": 0,
                "observation_score": 0,
                "cmms_score": 0,
                "cmms_analysis_count": 0
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

            # Risk-adjusted weighting: increase weight for PR-03 (LOTO) in high-risk sites
            if pillar == PillarType.PROCESS and question.question_code == "PR-03":
                question_weight *= risk_multiplier
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
                    if obs.observation_type and 'safety' in obs.observation_type.lower() and not obs.pass_fail_result:
                        observation_critical_failures.append({
                            "observation_title": obs.observation_title,
                            "type": obs.observation_type,
                            "severity": obs.severity,
                            "reason": "Safety observation failure"
                        })
            
            # Average observation score
            observation_score = sum(obs_scores) / len(obs_scores) if obs_scores else 0
        
        # ==========================================
        # PART 3: Calculate CMMS Data Score (Technology Pillar Only)
        # ==========================================
        cmms_score = 0
        cmms_impact = {}
        
        if pillar == PillarType.TECHNOLOGY and data_analyses:
            cmms_scores = []
            
            for analysis in data_analyses:
                metrics = analysis.metrics or {}
                
                # Reactive Ratio scoring (lower is better)
                if 'reactive_ratio' in metrics:
                    reactive_data = metrics['reactive_ratio']
                    if 'score' in reactive_data:
                        cmms_scores.append(reactive_data['score'])
                    elif 'reactive_ratio' in reactive_data:
                        # Convert ratio to score (0-5 scale)
                        ratio = reactive_data['reactive_ratio'] / 100  # Convert percentage
                        if ratio <= 0.15:
                            cmms_scores.append(5)  # Excellent
                        elif ratio <= 0.25:
                            cmms_scores.append(4)  # Good
                        elif ratio <= 0.40:
                            cmms_scores.append(3)  # Fair
                        elif ratio <= 0.60:
                            cmms_scores.append(2)  # Poor
                        else:
                            cmms_scores.append(1)  # Critical
                
                # PM Compliance scoring (higher is better)
                if 'pm_compliance_rate' in metrics:
                    compliance = metrics['pm_compliance_rate']
                    if compliance >= 95:
                        cmms_scores.append(5)
                    elif compliance >= 85:
                        cmms_scores.append(4)
                    elif compliance >= 75:
                        cmms_scores.append(3)
                    elif compliance >= 60:
                        cmms_scores.append(2)
                    else:
                        cmms_scores.append(1)
                
                # Data Quality scoring (higher is better)
                if 'data_quality' in metrics:
                    quality_data = metrics['data_quality']
                    if 'quality_score' in quality_data:
                        cmms_scores.append(quality_data['quality_score'])
                    elif 'closure_code_quality' in quality_data:
                        quality_pct = quality_data['closure_code_quality']
                        if quality_pct >= 90:
                            cmms_scores.append(5)
                        elif quality_pct >= 75:
                            cmms_scores.append(4)
                        elif quality_pct >= 60:
                            cmms_scores.append(3)
                        elif quality_pct >= 40:
                            cmms_scores.append(2)
                        else:
                            cmms_scores.append(1)
            
            # Average CMMS score
            cmms_score = sum(cmms_scores) / len(cmms_scores) if cmms_scores else 0
            cmms_impact = {
                "cmms_score": round(cmms_score, 2),
                "analysis_count": len(data_analyses),
                "metrics_evaluated": len(cmms_scores)
            }
        
        # ==========================================
        # PART 4: Combine Scores with Weights
        # ==========================================
        if pillar == PillarType.TECHNOLOGY and data_analyses and responses:
            # Technology with CMMS data: Interview 60%, Observations 20%, CMMS 20%
            combined_score = (interview_score * 0.60) + (observation_score * 0.20) + (cmms_score * 0.20)
        elif pillar == PillarType.TECHNOLOGY and data_analyses:
            # Only CMMS data for Technology
            combined_score = (cmms_score * 0.70) + (observation_score * 0.30)
        elif observations and responses:
            # Both interviews and observations: 80/20 split
            combined_score = (interview_score * 0.80) + (observation_score * 0.20)
        elif responses:
            # Only interviews: use interview score
            combined_score = interview_score
        else:
            # Only observations: use observation score
            combined_score = observation_score
        
        # ==========================================
        # PART 5: Apply Weakest Link Logic
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
        
        # CMMS data quality failures (cap Technology at 3.5 if data quality is poor)
        if pillar == PillarType.TECHNOLOGY and cmms_score > 0 and cmms_score < 2.0:
            final_score = min(final_score, 3.5)
        
        # Calculate confidence based on evidence coverage
        evidence_coverage = (evidence_count / evidence_required_count * 100) if evidence_required_count > 0 else 100
        confidence = self._calculate_confidence(evidence_coverage, len(responses))
        
        result = {
            "raw_score": round(combined_score, 2),
            "weighted_score": round(combined_score, 2),
            "final_score": round(final_score, 2),
            "confidence": confidence,
            "evidence_coverage": round(evidence_coverage, 1),
            "critical_failures": critical_failures + observation_critical_failures,
            "response_count": len(responses),
            "observation_count": len(observations),
            "interview_score": round(interview_score, 2),
            "observation_score": round(observation_score, 2),
            "cmms_score": round(cmms_score, 2) if pillar == PillarType.TECHNOLOGY else None,
            "cmms_analysis_count": len(data_analyses) if pillar == PillarType.TECHNOLOGY else 0
        }
        
        # Add CMMS impact details for Technology pillar
        if pillar == PillarType.TECHNOLOGY and cmms_impact:
            result["cmms_impact"] = cmms_impact
        
        return result
    
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
    
    # ============================================================
    # STRATEGIC EVOLUTION: ADVANCED ANALYTICS METHODS
    # ============================================================
    
    def _calculate_confidence_variance(self, assessment_id: int, pillar: PillarType) -> Dict:
        """
        Calculate confidence variance (Cultural Blind Spot Detection)
        
        Compares scores between different roles for the same questions.
        High variance (SD > 1.5) indicates cultural disconnect where
        different organizational levels have vastly different perceptions.
        
        Returns:
            Dict with variance metrics and cultural disconnect flags
        """
        from sqlalchemy import func
        
        # Get all responses grouped by question and role
        responses = self.db.query(
            QuestionBank.question_code,
            QuestionBank.question_text,
            QuestionBank.target_role,
            QuestionResponse.numeric_score,
            User.role
        ).join(
            QuestionResponse, QuestionBank.id == QuestionResponse.question_id
        ).outerjoin(
            User, User.id == QuestionResponse.respondent_id
        ).filter(
            QuestionResponse.assessment_id == assessment_id,
            QuestionBank.pillar == pillar,
            QuestionResponse.numeric_score.isnot(None),
            QuestionResponse.is_draft == False,
            QuestionResponse.is_na == False
        ).all()
        
        if not responses:
            return {
                "average_variance": 0,
                "cultural_disconnects": [],
                "questions_analyzed": 0,
                "variance_by_question": {}
            }
        
        # Group scores by question
        question_scores = {}
        for question_code, question_text, target_role, score, respondent_role in responses:
            if question_code not in question_scores:
                question_scores[question_code] = {
                    "text": question_text,
                    "scores": [],
                    "by_role": {}
                }
            question_scores[question_code]["scores"].append(score)
            role_key = respondent_role or (target_role.value if hasattr(target_role, 'value') else str(target_role))
            if role_key not in question_scores[question_code]["by_role"]:
                question_scores[question_code]["by_role"][role_key] = []
            question_scores[question_code]["by_role"][role_key].append(score)
        
        # Calculate variance for questions with multiple responses
        variance_by_question = {}
        cultural_disconnects = []
        total_variance = 0
        variance_count = 0
        
        for question_code, data in question_scores.items():
            if len(data["scores"]) >= 2:
                try:
                    question_stdev = stdev(data["scores"])
                    question_mean = mean(data["scores"])
                    
                    variance_by_question[question_code] = {
                        "standard_deviation": round(question_stdev, 2),
                        "mean": round(question_mean, 2),
                        "response_count": len(data["scores"]),
                        "scores_by_role": {
                            role: round(mean(scores), 2) if scores else None
                            for role, scores in data["by_role"].items()
                        }
                    }
                    
                    total_variance += question_stdev
                    variance_count += 1
                    
                    # Flag cultural disconnect if SD > threshold
                    if question_stdev > self.CULTURAL_DISCONNECT_THRESHOLD:
                        # Find the roles with highest disagreement
                        role_means = {
                            role: mean(scores) 
                            for role, scores in data["by_role"].items() 
                            if scores
                        }
                        if role_means:
                            max_role = max(role_means, key=role_means.get)
                            min_role = min(role_means, key=role_means.get)
                            
                            cultural_disconnects.append({
                                "question_code": question_code,
                                "question_text": data["text"][:100],
                                "standard_deviation": round(question_stdev, 2),
                                "highest_score_role": max_role,
                                "highest_score": round(role_means[max_role], 2),
                                "lowest_score_role": min_role,
                                "lowest_score": round(role_means[min_role], 2),
                                "gap": round(role_means[max_role] - role_means[min_role], 2),
                                "recommendation": f"Investigate perception gap between {max_role} and {min_role}"
                            })
                except Exception:
                    # Not enough data for stdev calculation
                    pass
        
        average_variance = (total_variance / variance_count) if variance_count > 0 else 0
        
        return {
            "average_variance": round(average_variance, 2),
            "cultural_disconnect_threshold": self.CULTURAL_DISCONNECT_THRESHOLD,
            "has_cultural_disconnect": len(cultural_disconnects) > 0,
            "cultural_disconnects": cultural_disconnects,
            "questions_analyzed": variance_count,
            "variance_by_question": variance_by_question
        }
    
    def _calculate_maturity_velocity(
        self, 
        site_name: str, 
        current_date: datetime, 
        current_rmi: float,
        current_assessment_id: int
    ) -> Dict:
        """
        Calculate Maturity Velocity (Temporal Analysis)
        
        Compares current RMI to the most recent previous assessment for the same site.
        Calculates the rate of change per month.
        
        Velocity = (Current_RMI - Previous_RMI) / Months_Between
        
        Flags sustainability_risk if:
        - Previous score was high (>=4.0) and current dropped
        - Velocity is negative after a recent improvement
        
        Returns:
            Dict with velocity metrics and sustainability analysis
        """
        # Find previous assessment for this site
        previous_assessment = self.db.query(Assessment, Score).join(
            Score, Assessment.id == Score.assessment_id
        ).filter(
            Assessment.site_name == site_name,
            Assessment.id != current_assessment_id,
            Score.pillar.is_(None)  # Overall score has NULL pillar
        ).order_by(
            Assessment.assessment_date.desc()
        ).first()
        
        if not previous_assessment:
            return {
                "velocity": None,
                "previous_rmi": None,
                "previous_date": None,
                "months_between": None,
                "trend": "No Previous Data",
                "sustainability_risk": False,
                "is_first_assessment": True
            }
        
        prev_assessment, prev_score = previous_assessment
        previous_rmi = prev_score.final_score
        previous_date = prev_assessment.assessment_date
        
        # Calculate months between assessments
        if current_date and previous_date:
            try:
                delta = relativedelta(current_date, previous_date)
                months_between = delta.years * 12 + delta.months + (delta.days / 30)
                months_between = max(months_between, 0.1)  # Avoid division by zero
            except Exception:
                months_between = 1  # Default to 1 month if calculation fails
        else:
            months_between = 1
        
        # Calculate velocity
        rmi_change = current_rmi - previous_rmi
        velocity = rmi_change / months_between
        
        # Determine trend
        if abs(velocity) < 0.1:
            trend = "Stable"
        elif velocity > 0.3:
            trend = "Rapid Improvement"
        elif velocity > 0:
            trend = "Improving"
        elif velocity > -0.3:
            trend = "Declining"
        else:
            trend = "Rapid Decline"
        
        # Check sustainability risk
        sustainability_risk = False
        risk_reasons = []
        
        # Risk 1: High score dropped significantly
        if previous_rmi >= 4.0 and current_rmi < previous_rmi - 0.5:
            sustainability_risk = True
            risk_reasons.append(
                f"High maturity regression: dropped from {previous_rmi:.1f} to {current_rmi:.1f}"
            )
        
        # Risk 2: Negative velocity after recent improvement
        # (Would need history of multiple assessments to fully implement)
        if velocity < -0.2 and previous_rmi > 3.0:
            sustainability_risk = True
            risk_reasons.append(
                f"Negative momentum: declining at {abs(velocity):.2f} points/month"
            )
        
        return {
            "velocity": round(velocity, 3),
            "velocity_per_year": round(velocity * 12, 2),
            "rmi_change": round(rmi_change, 2),
            "previous_rmi": round(previous_rmi, 2),
            "current_rmi": round(current_rmi, 2),
            "previous_date": previous_date.isoformat() if previous_date else None,
            "months_between": round(months_between, 1),
            "trend": trend,
            "sustainability_risk": sustainability_risk,
            "risk_reasons": risk_reasons,
            "is_first_assessment": False
        }
    
    def _analyze_iso_55001_gaps(self, assessment_id: int, pillar: PillarType) -> Dict:
        """
        Analyze ISO 55001 alignment gaps for a pillar
        
        Maps pillar questions to ISO 55001 clauses and identifies
        areas where scores indicate non-compliance or gaps.
        
        ISO 55001 Clause Mappings:
        - PEOPLE -> 7.2 (Competence)
        - PROCESS -> 8.1 (Operational Planning and Control)
        - TECHNOLOGY -> 7.5 (Information Requirements)
        
        Returns:
            Dict with ISO clause mapping, gap analysis, and recommendations
        """
        iso_clause = self.ISO_55001_MAPPINGS.get(pillar.value, "N/A")
        
        # Get responses with their ISO mappings
        responses = self.db.query(QuestionResponse, QuestionBank).join(
            QuestionBank
        ).filter(
            QuestionResponse.assessment_id == assessment_id,
            QuestionBank.pillar == pillar,
            QuestionResponse.numeric_score.isnot(None),
            QuestionResponse.is_draft == False
        ).all()
        
        if not responses:
            return {
                "iso_clause": iso_clause,
                "compliance_score": None,
                "gaps": [],
                "recommendations": []
            }
        
        # Analyze gaps (scores <= 2 indicate potential non-compliance)
        gaps = []
        scores = []
        
        for response, question in responses:
            scores.append(response.numeric_score)
            
            if response.numeric_score <= 2:
                gaps.append({
                    "question_code": question.question_code,
                    "question_text": question.question_text[:100],
                    "score": response.numeric_score,
                    "iso_clause": question.iso_55001_clause or iso_clause,
                    "severity": "Critical" if response.numeric_score == 1 else "Major",
                    "gap_description": self._get_iso_gap_description(
                        pillar, question.question_code, response.numeric_score
                    )
                })
        
        # Calculate compliance score (percentage of questions scoring >= 3)
        compliant_count = sum(1 for s in scores if s >= 3)
        compliance_score = (compliant_count / len(scores) * 100) if scores else 0
        
        # Generate recommendations based on gaps
        recommendations = self._generate_iso_recommendations(pillar, gaps, compliance_score)
        
        return {
            "iso_clause": iso_clause,
            "iso_clause_name": self._get_iso_clause_name(iso_clause),
            "compliance_score": round(compliance_score, 1),
            "total_questions": len(scores),
            "compliant_questions": compliant_count,
            "gap_count": len(gaps),
            "gaps": gaps,
            "recommendations": recommendations,
            "certification_readiness": "Ready" if compliance_score >= 80 else 
                                       "Needs Work" if compliance_score >= 60 else 
                                       "Not Ready"
        }
    
    def _get_iso_clause_name(self, clause: str) -> str:
        """Get the full name of an ISO 55001 clause"""
        clause_names = {
            "7.2": "Competence",
            "7.5": "Information Requirements",
            "8.1": "Operational Planning and Control",
            "4.1": "Understanding the Organization",
            "4.2": "Stakeholder Needs",
            "5.1": "Leadership",
            "6.1": "Risk and Opportunities",
            "6.2": "Asset Management Objectives",
            "9.1": "Monitoring and Measurement",
            "10.2": "Continual Improvement"
        }
        return clause_names.get(clause, "Unknown Clause")
    
    def _get_iso_gap_description(self, pillar: PillarType, question_code: str, score: int) -> str:
        """Generate a description of the ISO gap based on pillar and score"""
        base_descriptions = {
            PillarType.PEOPLE: "Competency gap identified. Personnel may lack required training, " +
                              "qualifications, or documented competence records.",
            PillarType.PROCESS: "Operational planning gap. Work procedures may be inadequate, " +
                               "missing, or not effectively implemented.",
            PillarType.TECHNOLOGY: "Information management gap. Asset data may be incomplete, " +
                                  "inaccessible, or not properly maintained."
        }
        
        severity = "Critical" if score == 1 else "Significant"
        return f"{severity} {base_descriptions.get(pillar, 'Gap identified in asset management system.')}"
    
    def _generate_iso_recommendations(
        self, 
        pillar: PillarType, 
        gaps: List[Dict], 
        compliance_score: float
    ) -> List[str]:
        """Generate ISO 55001 compliance recommendations based on gaps"""
        recommendations = []
        
        if compliance_score < 60:
            recommendations.append(
                f"PRIORITY: {pillar.value} pillar requires immediate attention. " +
                f"Consider engaging ISO 55001 consultants for gap remediation."
            )
        
        if pillar == PillarType.PEOPLE and gaps:
            recommendations.append(
                "Clause 7.2 Action: Develop competency framework with documented training records, " +
                "qualification matrices, and regular competency assessments."
            )
        
        if pillar == PillarType.PROCESS and gaps:
            recommendations.append(
                "Clause 8.1 Action: Review and update standard operating procedures (SOPs). " +
                "Ensure all maintenance activities have documented work instructions."
            )
        
        if pillar == PillarType.TECHNOLOGY and gaps:
            recommendations.append(
                "Clause 7.5 Action: Conduct CMMS data audit. Establish data governance " +
                "standards and implement data quality monitoring."
            )
        
        # Critical gaps get specific recommendations
        critical_gaps = [g for g in gaps if g.get('severity') == 'Critical']
        if critical_gaps:
            recommendations.append(
                f"CRITICAL: {len(critical_gaps)} question(s) scored 1/5. " +
                "These represent fundamental gaps that must be addressed before certification."
            )
        
        return recommendations
    
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
            if response.numeric_score is not None and question.evidence_required and response.numeric_score >= self.EVIDENCE_THRESHOLD:
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
    
    Now uses Semantic Quality Check (Actionability Index):
    - Scores higher if notes contain semantic entities:
      [Component] + [Failure Mode] + [Corrective Action]
    - Replaces simple 10-character length check with intelligent analysis
    """
    import pandas as pd
    import re
    
    if not isinstance(work_orders_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")
    
    # Assuming column: 'closure_notes' or 'resolution'
    if 'closure_notes' not in work_orders_df.columns:
        raise ValueError("Missing 'closure_notes' column")
    
    total_wos = len(work_orders_df)
    
    # Generic/useless codes
    generic_codes = ['done', 'fixed', 'complete', 'ok', 'n/a', 'closed', 'completed', '']
    
    # Semantic entity patterns for Actionability Index
    # These patterns detect meaningful maintenance information
    
    # Component patterns (what was worked on)
    component_patterns = [
        r'\b(pump|motor|valve|bearing|seal|belt|gear|shaft|coupling|fan|compressor|' +
        r'conveyor|sensor|actuator|plc|hmi|vfd|drive|filter|strainer|tank|pipe|' +
        r'electrical|mechanical|hydraulic|pneumatic|unit|machine|equipment)\b'
    ]
    
    # Failure mode patterns (what went wrong)
    failure_patterns = [
        r'\b(fail|broke|leak|worn|damaged|crack|vibrat|overheat|short|trip|' +
        r'stuck|seized|corrode|erode|misalign|loose|noise|cavitat|blocked|' +
        r'clogged|burnt|overload|undervolt|overvolt|ground fault|fault)\w*\b'
    ]
    
    # Corrective action patterns (what was done)
    action_patterns = [
        r'\b(replac|repair|adjust|tighten|clean|lubricat|align|calibrat|' +
        r'install|remov|rebuild|rewound|reseal|refurbish|inspect|test|' +
        r'reset|reprogram|recondition|overhaul)\w*\b'
    ]
    
    def calculate_actionability_score(notes: str) -> Dict:
        """
        Calculate actionability score for a single work order note
        Returns score 0-3 based on semantic entity detection
        """
        if pd.isna(notes) or not notes:
            return {"score": 0, "entities": {"component": False, "failure": False, "action": False}}
        
        notes_lower = notes.lower()
        
        # Check for generic codes first
        if notes_lower.strip() in generic_codes:
            return {"score": 0, "entities": {"component": False, "failure": False, "action": False}}
        
        # Detect semantic entities
        has_component = any(re.search(p, notes_lower) for p in component_patterns)
        has_failure = any(re.search(p, notes_lower) for p in failure_patterns)
        has_action = any(re.search(p, notes_lower) for p in action_patterns)
        
        entity_count = sum([has_component, has_failure, has_action])
        
        return {
            "score": entity_count,
            "entities": {
                "component": has_component,
                "failure": has_failure,
                "action": has_action
            }
        }
    
    # Analyze each work order
    actionability_results = work_orders_df['closure_notes'].apply(calculate_actionability_score)
    actionability_scores = [r['score'] for r in actionability_results]
    
    # Count quality levels
    high_quality = sum(1 for s in actionability_scores if s == 3)  # All 3 entities
    medium_quality = sum(1 for s in actionability_scores if s == 2)  # 2 entities
    low_quality = sum(1 for s in actionability_scores if s == 1)  # 1 entity
    poor_quality = sum(1 for s in actionability_scores if s == 0)  # No entities
    
    # Calculate weighted actionability index (0-100)
    weighted_score = (
        (high_quality * 100) + 
        (medium_quality * 66) + 
        (low_quality * 33) + 
        (poor_quality * 0)
    ) / total_wos if total_wos > 0 else 0
    
    graveyard_percentage = poor_quality / total_wos if total_wos > 0 else 0
    
    # Score based on actionability index
    if weighted_score >= 80:
        score = 5
        severity = "EXCELLENT - High actionability, rich semantic data"
    elif weighted_score >= 60:
        score = 4
        severity = "GOOD - Solid data quality with some gaps"
    elif weighted_score >= 40:
        score = 3
        severity = "ACCEPTABLE - Improvement needed"
    elif weighted_score >= 20:
        score = 2
        severity = "POOR - Significant data quality issues"
    else:
        score = 1
        severity = "SEVERE DATA GRAVEYARD - Cannot perform RCA"
    
    return {
        "metric": "Data Graveyard Index (Semantic)",
        "total_work_orders": total_wos,
        "poor_quality_closures": poor_quality,
        "graveyard_percentage": round(graveyard_percentage * 100, 1),
        "severity": severity,
        "score": score,
        
        # Actionability Index details
        "actionability_index": round(weighted_score, 1),
        "quality_breakdown": {
            "high_quality_3_entities": high_quality,
            "medium_quality_2_entities": medium_quality,
            "low_quality_1_entity": low_quality,
            "poor_quality_0_entities": poor_quality
        },
        "semantic_coverage": {
            "with_component": sum(1 for r in actionability_results if r['entities']['component']),
            "with_failure_mode": sum(1 for r in actionability_results if r['entities']['failure']),
            "with_corrective_action": sum(1 for r in actionability_results if r['entities']['action'])
        }
    }
