"""
RMI vNext Practice Library Engine
Recommendation engine that generates prioritized improvement actions
based on assessment scores, maturity pathways, and practice entries.
"""
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from models_v2 import (
    Practice, SubdomainScore, Subdomain, Domain,
    AssessmentV2, QuestionV2
)


class PracticeEngine:
    """
    Generates improvement recommendations from the practice library
    based on assessment scores and maturity pathways.
    """

    # ── Priority calculation weights ──
    IMPACT_WEIGHT = 0.40
    FEASIBILITY_WEIGHT = 0.30
    URGENCY_WEIGHT = 0.30

    # ── Max recommendations per request ──
    DEFAULT_TOP_N = 10

    # ── Maturity pathway definitions ──
    MATURITY_PATHWAYS = {
        "1_to_2": {
            "from_level": 1, "to_level": 2,
            "focus": "Establish basics",
            "typical_timeline": "6-12 months",
            "key_themes": [
                "Document existing processes",
                "Establish CMMS foundations",
                "Basic PM program",
                "Safety culture fundamentals",
                "Define roles and responsibilities",
            ],
        },
        "2_to_3": {
            "from_level": 2, "to_level": 3,
            "focus": "Systematic processes",
            "typical_timeline": "12-18 months",
            "key_themes": [
                "Formalize planning & scheduling",
                "Implement PM optimization",
                "Deploy PdM technologies",
                "Data quality improvement",
                "Training curriculum development",
            ],
        },
        "3_to_4": {
            "from_level": 3, "to_level": 4,
            "focus": "Proactive optimization",
            "typical_timeline": "18-24 months",
            "key_themes": [
                "RCM/FMEA-based strategies",
                "Advanced analytics",
                "Reliability engineering function",
                "Cross-functional integration",
                "Benchmark-driven targets",
            ],
        },
        "4_to_5": {
            "from_level": 4, "to_level": 5,
            "focus": "World-class excellence",
            "typical_timeline": "24-36 months",
            "key_themes": [
                "Predictive/prescriptive analytics",
                "ISO 55001 alignment",
                "Digital transformation",
                "Knowledge management systems",
                "Industry leadership",
            ],
        },
    }

    def __init__(self, db: Session):
        self.db = db

    # ═══════════════════════════════════════════
    #  PUBLIC API
    # ═══════════════════════════════════════════

    def get_recommendations(
        self,
        assessment_id: int,
        top_n: int = DEFAULT_TOP_N,
    ) -> Dict:
        """
        Generate prioritized recommendations based on assessment scores.
        """
        assessment = self.db.query(AssessmentV2).filter(
            AssessmentV2.id == assessment_id
        ).first()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        if assessment.overall_rmi is None:
            raise ValueError("Assessment has not been scored yet")

        # Get all subdomain scores
        sd_scores = (
            self.db.query(SubdomainScore, Subdomain)
            .join(Subdomain)
            .filter(SubdomainScore.assessment_id == assessment_id)
            .all()
        )

        recommendations = []
        for sd_score, subdomain in sd_scores:
            if sd_score.final_score is None:
                continue

            current_level = int(sd_score.final_score)
            target_level = min(current_level + 1, 5)

            # Get practices for this subdomain and maturity transition
            practices = (
                self.db.query(Practice)
                .filter(
                    Practice.subdomain_id == subdomain.id,
                    Practice.is_active == True,
                )
                .order_by(Practice.priority_rank)
                .all()
            )

            for practice in practices:
                # Filter by maturity relevance
                if practice.from_level and practice.from_level != current_level:
                    continue
                if practice.to_level and practice.to_level != target_level:
                    continue

                priority = self._calculate_priority(
                    sd_score.final_score, practice, assessment.overall_rmi
                )

                recommendations.append({
                    "practice_id": practice.id,
                    "subdomain_code": subdomain.code,
                    "subdomain_name": subdomain.name,
                    "title": practice.title,
                    "description": practice.description,
                    "current_score": round(sd_score.final_score, 2),
                    "target_level": target_level,
                    "priority_score": round(priority, 3),
                    "impact": practice.impact_rating or "medium",
                    "effort": practice.effort_rating or "medium",
                    "timeline": practice.timeline or "3-6 months",
                    "practice_link": practice.practice_code,
                    "tools": self._parse_json_field(practice.tools),
                    "success_metrics": self._parse_json_field(practice.success_metrics),
                    "resources": self._parse_json_field(practice.resources),
                })

        # Sort by priority (highest first) and take top N
        recommendations.sort(key=lambda r: r["priority_score"], reverse=True)
        top_recs = recommendations[:top_n]

        # Maturity pathway
        overall_level = int(assessment.overall_rmi) if assessment.overall_rmi else 1
        pathway_key = f"{overall_level}_to_{min(overall_level + 1, 5)}"
        pathway = self.MATURITY_PATHWAYS.get(pathway_key, self.MATURITY_PATHWAYS["1_to_2"])

        return {
            "assessment_id": assessment_id,
            "overall_rmi": assessment.overall_rmi,
            "current_maturity": overall_level,
            "target_maturity": min(overall_level + 1, 5),
            "pathway": pathway,
            "total_recommendations": len(recommendations),
            "top_recommendations": top_recs,
            "by_domain": self._group_by_domain(recommendations),
        }

    def get_practice_detail(self, practice_id: int) -> Optional[Dict]:
        """Get full details of a single practice entry."""
        practice = self.db.query(Practice).filter(Practice.id == practice_id).first()
        if not practice:
            return None

        subdomain = self.db.query(Subdomain).filter(
            Subdomain.id == practice.subdomain_id
        ).first()

        return {
            "id": practice.id,
            "practice_code": practice.practice_code,
            "title": practice.title,
            "description": practice.description,
            "subdomain_code": subdomain.code if subdomain else None,
            "subdomain_name": subdomain.name if subdomain else None,
            "from_level": practice.from_level,
            "to_level": practice.to_level,
            "impact_rating": practice.impact_rating,
            "effort_rating": practice.effort_rating,
            "timeline": practice.timeline,
            "tools": self._parse_json_field(practice.tools),
            "success_metrics": self._parse_json_field(practice.success_metrics),
            "resources": self._parse_json_field(practice.resources),
            "iso_55001_clause": practice.iso_55001_clause,
            "is_active": practice.is_active,
        }

    def get_subdomain_practices(self, subdomain_code: str) -> List[Dict]:
        """Get all practices for a subdomain."""
        subdomain = self.db.query(Subdomain).filter(
            Subdomain.code == subdomain_code
        ).first()
        if not subdomain:
            return []

        practices = (
            self.db.query(Practice)
            .filter(
                Practice.subdomain_id == subdomain.id,
                Practice.is_active == True,
            )
            .order_by(Practice.from_level, Practice.priority_rank)
            .all()
        )

        return [
            {
                "id": p.id,
                "practice_code": p.practice_code,
                "title": p.title,
                "from_level": p.from_level,
                "to_level": p.to_level,
                "impact_rating": p.impact_rating,
                "effort_rating": p.effort_rating,
                "timeline": p.timeline,
            }
            for p in practices
        ]

    # ═══════════════════════════════════════════
    #  PRIORITY CALCULATION
    # ═══════════════════════════════════════════

    def _calculate_priority(self, score: float, practice: Practice,
                            overall_rmi: float) -> float:
        """
        Priority = impact × feasibility × urgency.
        Higher score = higher priority.
        """
        # Impact: how much improvement is possible
        gap = 5.0 - score
        impact = min(gap / 4.0, 1.0)  # Normalize to 0-1

        # Feasibility: inverse of effort
        effort_map = {"low": 0.9, "medium": 0.6, "high": 0.3}
        feasibility = effort_map.get(practice.effort_rating or "medium", 0.6)

        # Urgency: lower scores are more urgent
        urgency = max(1.0 - (score / 5.0), 0.1)

        # Bonus for critical subdomain caps
        cap_bonus = 0.2 if practice.is_critical_path else 0.0

        priority = (
            impact * self.IMPACT_WEIGHT +
            feasibility * self.FEASIBILITY_WEIGHT +
            urgency * self.URGENCY_WEIGHT +
            cap_bonus
        )

        return priority

    # ═══════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════

    def _group_by_domain(self, recommendations: List[Dict]) -> Dict:
        """Group recommendations by domain."""
        grouped: Dict[str, List] = {}
        for rec in recommendations:
            # Extract domain from subdomain code (e.g., "WC.1" → "WC")
            domain_code = rec["subdomain_code"].split(".")[0] if rec.get("subdomain_code") else "UNK"
            grouped.setdefault(domain_code, []).append(rec)
        return grouped

    @staticmethod
    def _parse_json_field(value) -> list:
        """Safely parse a JSON field."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return [value]
        return []
