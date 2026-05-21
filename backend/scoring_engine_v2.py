"""
RMI vNext Scoring Engine — v2
Rebalanced maturity scale, evidence hard-reject, subdomain-level scoring,
weakest-link rules, confidence bands, maturity velocity, and ISO 55001 gap analysis.
"""
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from statistics import stdev, mean
import json

from models_v2 import (
    AssessmentV2, ResponseV2, QuestionV2, SubdomainScore,
    Subdomain, Domain, DomainType, SubdomainType,
    AssessmentMode, EvidenceStatus, TargetRoleV2
)


class ScoringEngineV2:
    """
    vNext scoring engine.

    Score hierarchy:
      Question → Subdomain → Domain → Overall RMI
    """

    # ── Role weights (sum = 1.00) ──
    ROLE_WEIGHTS: Dict[str, float] = {
        "TECHNICIAN":          0.35,
        "SUPERVISOR":          0.20,
        "MANAGER":             0.15,
        "PLANNER":             0.15,
        "RELIABILITY_ENGINEER": 0.15,
    }

    # ── Maturity level boundaries (equal-width top bands) ──
    MATURITY_LEVELS = [
        (1.00, 1.99, 1, "Reactive"),
        (2.00, 2.99, 2, "Emerging"),
        (3.00, 3.59, 3, "Systematic"),
        (3.60, 4.29, 4, "Proactive"),
        (4.30, 5.00, 5, "Prescriptive"),
    ]

    # ── Default domain weights (equal) ──
    DEFAULT_DOMAIN_WEIGHTS: Dict[str, float] = {
        "WC": 0.20, "LC": 0.20, "WM": 0.20, "AI": 0.20, "SG": 0.20,
    }

    # ── Industry module weight overrides ──
    INDUSTRY_WEIGHTS: Dict[str, Dict[str, float]] = {
        "MFG": {"WC": 0.20, "LC": 0.15, "WM": 0.25, "AI": 0.20, "SG": 0.20},
        "FNB": {"WC": 0.15, "LC": 0.20, "WM": 0.25, "AI": 0.15, "SG": 0.25},
        "ONG": {"WC": 0.20, "LC": 0.25, "WM": 0.20, "AI": 0.15, "SG": 0.20},
        "MNM": {"WC": 0.20, "LC": 0.20, "WM": 0.25, "AI": 0.15, "SG": 0.20},
        "UTL": {"WC": 0.15, "LC": 0.15, "WM": 0.20, "AI": 0.30, "SG": 0.20},
        "PHA": {"WC": 0.15, "LC": 0.15, "WM": 0.20, "AI": 0.20, "SG": 0.30},
    }

    # ── Critical failure items → domain cap ──
    CRITICAL_CAPS = {
        "LC.2-01": {"domain": "LC", "cap": 2.0, "label": "Stop-work authority absent"},
        "WM.3-03": {"domain": "WM", "cap": 3.0, "label": "LOTO compliance failure"},
        "AI.1-01": {"domain": "AI", "cap": 1.5, "label": "No CMMS"},
        "SG.1-01": {"domain": "SG", "cap": 2.0, "label": "No written AM policy"},
        "WC.1-01": {"domain": "WC", "cap": 2.5, "label": "No equipment training"},
    }

    # ── Cross-domain caps ──
    CROSS_DOMAIN_CAPS = [
        {"if_domain": "AI", "below": 2.0, "cap_domains": ["WC", "LC", "WM", "SG"], "cap": 4.0,
         "label": "AI < 2.0 — cannot verify maturity without data systems"},
        {"if_domain": "LC", "below": 2.0, "cap_domains": ["WM", "WC"], "cap": 3.5,
         "label": "LC < 2.0 — poor leadership undermines work management & training"},
        {"if_domain": "SG", "below": 2.0, "cap_domains": ["__overall__"], "cap": 3.5,
         "label": "SG < 2.0 — no strategy means no sustained improvement"},
    ]

    CULTURAL_DISCONNECT_THRESHOLD = 1.5
    CRITICAL_DISCONNECT_THRESHOLD = 2.0

    # Evidence policy — see SCORING_POLICY.md
    EVIDENCE_REQUIRED_FOR_SCORE_AT_OR_ABOVE = 4
    EVIDENCE_CAP_WITHOUT_ACCEPTED = 3.0

    def __init__(self, db: Session):
        self.db = db

    # ═══════════════════════════════════════════
    #  PUBLIC API
    # ═══════════════════════════════════════════

    def calculate(self, assessment_id: int) -> Dict:
        """Full scoring pipeline for a vNext assessment."""
        assessment = self.db.query(AssessmentV2).filter(
            AssessmentV2.id == assessment_id
        ).first()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Determine domain weights
        industry = assessment.industry_module.value if assessment.industry_module else None
        domain_weights = self.INDUSTRY_WEIGHTS.get(industry, self.DEFAULT_DOMAIN_WEIGHTS)

        # ── Step 1: Score each subdomain ──
        subdomains = self.db.query(Subdomain).order_by(Subdomain.display_order).all()
        subdomain_results: Dict[str, Dict] = {}
        caps_applied: List[Dict] = []
        blind_spots: List[Dict] = []

        for sd in subdomains:
            result = self._score_subdomain(assessment_id, sd, assessment.assessment_mode)
            subdomain_results[sd.code] = result

            # Detect cultural blind spots
            bs = self._detect_blind_spot(assessment_id, sd)
            if bs:
                blind_spots.append(bs)

        # ── Step 2: Apply critical-failure caps (question-level) ──
        caps_applied += self._apply_critical_caps(assessment_id, subdomain_results)

        # ── Step 3: Aggregate to domain scores ──
        domain_results: Dict[str, Dict] = {}
        domains = self.db.query(Domain).order_by(Domain.display_order).all()
        for dom in domains:
            sd_codes = [sd.code for sd in dom.subdomains]
            sd_scores = [subdomain_results[c]["final_score"] for c in sd_codes
                         if subdomain_results[c]["final_score"] is not None]
            domain_score = mean(sd_scores) if sd_scores else None
            domain_results[dom.code] = {
                "score": round(domain_score, 2) if domain_score else None,
                "subdomains": {c: subdomain_results[c] for c in sd_codes},
            }

        # ── Step 4: Apply cross-domain caps ──
        caps_applied += self._apply_cross_domain_caps(domain_results)

        # ── Step 5: Overall RMI ──
        weighted_scores = []
        for code, data in domain_results.items():
            if data["score"] is not None:
                w = domain_weights.get(code, 0.20)
                weighted_scores.append(data["score"] * w)

        overall_rmi = sum(weighted_scores) / sum(
            domain_weights[c] for c in domain_results if domain_results[c]["score"] is not None
        ) if weighted_scores else None

        # Apply overall cap from cross-domain rules
        overall_cap = None
        for cap in caps_applied:
            if cap.get("target") == "__overall__":
                overall_cap = cap["cap"]
        if overall_cap and overall_rmi and overall_rmi > overall_cap:
            overall_rmi = overall_cap

        overall_rmi = round(overall_rmi, 2) if overall_rmi else None

        # ── Step 6: Confidence ──
        confidence = self._calculate_confidence(assessment_id, assessment.assessment_mode, blind_spots)

        # ── Step 7: Maturity level ──
        maturity = self._get_maturity_level(overall_rmi) if overall_rmi else None

        # ── Step 8: Velocity ──
        velocity = self._calculate_velocity(assessment)

        # ── Step 9: ISO 55001 readiness ──
        iso_readiness = self._iso_readiness(subdomain_results)

        # ── Step 10: Persist ──
        self._persist_scores(assessment, subdomain_results, domain_results,
                             overall_rmi, confidence, maturity)

        return {
            "assessment_id": assessment_id,
            "overall_rmi": overall_rmi,
            "maturity_level": maturity,
            "confidence": round(confidence, 2) if confidence else None,
            "confidence_band": [
                round(overall_rmi - (1 - confidence) * 1.0, 2) if overall_rmi and confidence else None,
                round(overall_rmi + (1 - confidence) * 1.0, 2) if overall_rmi and confidence else None,
            ],
            "domains": domain_results,
            "caps_applied": caps_applied,
            "blind_spots": blind_spots,
            "velocity": velocity,
            "iso_55001_readiness": round(iso_readiness, 2) if iso_readiness is not None else None,
            "domain_weights": domain_weights,
            "calculated_at": datetime.utcnow().isoformat(),
        }

    # ═══════════════════════════════════════════
    #  SUBDOMAIN SCORING
    # ═══════════════════════════════════════════

    def _score_subdomain(self, assessment_id: int, sd: Subdomain,
                         mode: AssessmentMode) -> Dict:
        """Calculate weighted score for a single subdomain."""
        responses = (
            self.db.query(ResponseV2, QuestionV2)
            .join(QuestionV2)
            .filter(
                ResponseV2.assessment_id == assessment_id,
                QuestionV2.subdomain_id == sd.id,
                ResponseV2.is_draft == False,
                ResponseV2.is_na == False,
            )
            .all()
        )

        if not responses:
            return {"raw_score": None, "final_score": None, "response_count": 0,
                    "evidence_blocked": 0, "cap_applied": False, "cap_reason": None}

        total_weighted = 0.0
        total_weight = 0.0
        evidence_blocked = 0

        for resp, question in responses:
            if resp.numeric_score is None:
                continue

            # ── Evidence policy ──
            # If the question requires evidence and the response is at or above
            # the evidence threshold, the score is soft-capped unless the
            # evidence status is ACCEPTED. PENDING_VERIFICATION (uploaded but
            # not yet verified) and REJECTED both fall back to the cap so
            # claims do not lift maturity without a verified audit trail.
            effective_score = float(resp.numeric_score)
            if (
                question.evidence_required
                and effective_score >= self.EVIDENCE_REQUIRED_FOR_SCORE_AT_OR_ABOVE
                and resp.evidence_status != EvidenceStatus.ACCEPTED
            ):
                evidence_blocked += 1
                effective_score = min(effective_score, self.EVIDENCE_CAP_WITHOUT_ACCEPTED)

            role_w = self.ROLE_WEIGHTS.get(
                resp.respondent_role.value if resp.respondent_role else "TECHNICIAN", 0.20
            )
            q_w = question.weight or 1.0
            combined = role_w * q_w

            # Evidence grade multiplier
            grade_mult = {"A": 1.0, "B": 0.95, "C": 0.85, "D": 0.75}.get(
                resp.evidence_grade, 1.0
            )

            total_weighted += effective_score * combined * grade_mult
            total_weight += combined

        raw = total_weighted / total_weight if total_weight > 0 else None

        return {
            "raw_score": round(raw, 2) if raw else None,
            "final_score": round(raw, 2) if raw else None,  # caps applied later
            "response_count": len(responses),
            "evidence_blocked": evidence_blocked,
            "cap_applied": False,
            "cap_reason": None,
        }

    # ═══════════════════════════════════════════
    #  CAPS
    # ═══════════════════════════════════════════

    def _apply_critical_caps(self, assessment_id: int,
                             sd_results: Dict[str, Dict]) -> List[Dict]:
        """Apply weakest-link caps from critical failure items."""
        caps = []
        for q_code, rule in self.CRITICAL_CAPS.items():
            question = self.db.query(QuestionV2).filter(
                QuestionV2.question_code == q_code,
                QuestionV2.is_active == True,
            ).first()
            if not question:
                continue

            resp = self.db.query(ResponseV2).filter(
                ResponseV2.assessment_id == assessment_id,
                ResponseV2.question_id == question.id,
                ResponseV2.is_na == False,
            ).first()
            if not resp or resp.numeric_score is None:
                continue

            trigger = False
            if q_code in ("LC.2-01", "AI.1-01", "SG.1-01", "WC.1-01"):
                trigger = resp.numeric_score == 1
            elif q_code == "WM.3-03":
                trigger = resp.numeric_score <= 2

            if trigger:
                # Cap all subdomains in that domain
                domain_code = rule["domain"]
                for sd_code, sd_data in sd_results.items():
                    if sd_code.startswith(domain_code + ".") and sd_data["final_score"] is not None:
                        if sd_data["final_score"] > rule["cap"]:
                            sd_data["final_score"] = rule["cap"]
                            sd_data["cap_applied"] = True
                            sd_data["cap_reason"] = rule["label"]
                caps.append({
                    "question": q_code,
                    "domain": rule["domain"],
                    "cap": rule["cap"],
                    "label": rule["label"],
                    "trigger_score": resp.numeric_score,
                })
        return caps

    def _apply_cross_domain_caps(self, domain_results: Dict[str, Dict]) -> List[Dict]:
        """Apply cross-domain cap rules."""
        caps = []
        for rule in self.CROSS_DOMAIN_CAPS:
            src = domain_results.get(rule["if_domain"])
            if not src or src["score"] is None:
                continue
            if src["score"] < rule["below"]:
                for target in rule["cap_domains"]:
                    if target == "__overall__":
                        caps.append({"target": "__overall__", "cap": rule["cap"],
                                     "label": rule["label"]})
                    else:
                        tgt = domain_results.get(target)
                        if tgt and tgt["score"] is not None and tgt["score"] > rule["cap"]:
                            tgt["score"] = rule["cap"]
                            caps.append({"target": target, "cap": rule["cap"],
                                         "label": rule["label"]})
        return caps

    # ═══════════════════════════════════════════
    #  CULTURAL BLIND SPOT DETECTION
    # ═══════════════════════════════════════════

    def _detect_blind_spot(self, assessment_id: int, sd: Subdomain) -> Optional[Dict]:
        """Detect variance between roles for a subdomain."""
        responses = (
            self.db.query(ResponseV2)
            .join(QuestionV2)
            .filter(
                ResponseV2.assessment_id == assessment_id,
                QuestionV2.subdomain_id == sd.id,
                ResponseV2.numeric_score.isnot(None),
                ResponseV2.is_draft == False,
                ResponseV2.is_na == False,
            )
            .all()
        )

        role_scores: Dict[str, List[float]] = {}
        for r in responses:
            role = r.respondent_role.value if r.respondent_role else "UNKNOWN"
            role_scores.setdefault(role, []).append(r.numeric_score)

        if len(role_scores) < 2:
            return None

        role_avgs = {r: mean(scores) for r, scores in role_scores.items()}
        variance = max(role_avgs.values()) - min(role_avgs.values())

        if variance >= self.CULTURAL_DISCONNECT_THRESHOLD:
            severity = "critical" if variance >= self.CRITICAL_DISCONNECT_THRESHOLD else "warning"
            return {
                "subdomain": sd.code,
                "variance": round(variance, 2),
                "role_averages": {k: round(v, 2) for k, v in role_avgs.items()},
                "severity": severity,
            }
        return None

    # ═══════════════════════════════════════════
    #  CONFIDENCE
    # ═══════════════════════════════════════════

    def _calculate_confidence(self, assessment_id: int,
                              mode: AssessmentMode,
                              blind_spots: List[Dict]) -> float:
        """Calculate overall confidence score (0.0 – 1.0)."""
        confidence = 1.0

        # Mode penalty
        if mode == AssessmentMode.QUICKSCAN:
            confidence -= 0.25

        # Evidence gaps
        total_responses = self.db.query(ResponseV2).filter(
            ResponseV2.assessment_id == assessment_id,
            ResponseV2.is_na == False,
        ).count()
        evidence_blocked = self.db.query(ResponseV2).filter(
            ResponseV2.assessment_id == assessment_id,
            ResponseV2.evidence_status == EvidenceStatus.PENDING_EVIDENCE,
        ).count()
        if total_responses > 0:
            confidence -= (evidence_blocked / total_responses) * 0.30

        # Blind spots
        for bs in blind_spots:
            if bs["severity"] == "critical":
                confidence -= 0.30
            else:
                confidence -= 0.15

        return max(confidence, 0.30)

    # ═══════════════════════════════════════════
    #  MATURITY LEVEL
    # ═══════════════════════════════════════════

    def _get_maturity_level(self, score: float) -> str:
        for low, high, level_num, name in self.MATURITY_LEVELS:
            if low <= score <= high:
                return f"Level {level_num} - {name}"
        return "Level 1 - Reactive"

    # ═══════════════════════════════════════════
    #  VELOCITY
    # ═══════════════════════════════════════════

    def _calculate_velocity(self, assessment: AssessmentV2) -> Dict:
        """Compare to most recent previous assessment for the same site."""
        previous = (
            self.db.query(AssessmentV2)
            .filter(
                AssessmentV2.site_name == assessment.site_name,
                AssessmentV2.id != assessment.id,
                AssessmentV2.overall_rmi.isnot(None),
                AssessmentV2.assessment_date < assessment.assessment_date,
            )
            .order_by(AssessmentV2.assessment_date.desc())
            .first()
        )
        if not previous or not previous.overall_rmi or not assessment.overall_rmi:
            return {"status": "baseline", "message": "No previous assessment for velocity"}

        months = max(
            (assessment.assessment_date - previous.assessment_date).days / 30.44, 1
        )
        delta = assessment.overall_rmi - previous.overall_rmi
        velocity = delta / (months / 12)

        if velocity > 1.0:
            interpretation = "Suspicious — verify evidence"
        elif velocity > 0.7:
            interpretation = "Rapid improvement"
        elif velocity > 0.3:
            interpretation = "Healthy improvement"
        elif velocity > 0:
            interpretation = "Slow improvement"
        elif velocity > -0.5:
            interpretation = "Stagnation"
        else:
            interpretation = "Regression"

        return {
            "status": "calculated",
            "previous_rmi": previous.overall_rmi,
            "current_rmi": assessment.overall_rmi,
            "delta": round(delta, 2),
            "velocity_per_year": round(velocity, 2),
            "months_between": round(months, 1),
            "interpretation": interpretation,
        }

    # ═══════════════════════════════════════════
    #  ISO 55001 READINESS
    # ═══════════════════════════════════════════

    def _iso_readiness(self, sd_results: Dict[str, Dict]) -> Optional[float]:
        """% of subdomains scoring ≥ 3.0 (Systematic)."""
        scores = [v["final_score"] for v in sd_results.values() if v["final_score"] is not None]
        if not scores:
            return None
        return sum(1 for s in scores if s >= 3.0) / len(scores)

    # ═══════════════════════════════════════════
    #  PERSISTENCE
    # ═══════════════════════════════════════════

    def _persist_scores(self, assessment: AssessmentV2,
                        sd_results: Dict, domain_results: Dict,
                        overall_rmi: Optional[float], confidence: float,
                        maturity: Optional[str]):
        """Save subdomain scores and update assessment summary."""
        # Delete old subdomain scores
        self.db.query(SubdomainScore).filter(
            SubdomainScore.assessment_id == assessment.id
        ).delete()

        # Insert new
        subdomains = self.db.query(Subdomain).all()
        sd_map = {sd.code: sd.id for sd in subdomains}

        for code, data in sd_results.items():
            if code in sd_map:
                self.db.add(SubdomainScore(
                    assessment_id=assessment.id,
                    subdomain_id=sd_map[code],
                    raw_score=data.get("raw_score"),
                    final_score=data.get("final_score"),
                    cap_applied=data.get("cap_applied", False),
                    cap_reason=data.get("cap_reason"),
                    confidence=confidence,
                ))

        # Update assessment record
        assessment.overall_rmi = overall_rmi
        assessment.confidence_score = confidence
        assessment.maturity_level = maturity

        self.db.commit()
