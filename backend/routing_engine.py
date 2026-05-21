"""
RMI vNext Routing Engine
Selects questions based on assessment mode (QuickScan / Standard / DeepDive),
respondent role, and optional industry module.
"""
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from models_v2 import (
    QuestionV2, Subdomain, Domain, AssessmentV2,
    AssessmentMode, TargetRoleV2, IndustryModule
)


class RoutingEngine:
    """
    Determines which questions to present for a given assessment
    based on mode, respondent role, and industry module.
    """

    # ── QuickScan: 1 question per subdomain (15 total) ──
    QUICKSCAN_PER_SUBDOMAIN = 1

    # ── Standard: 4-5 questions per subdomain (60-75 total) ──
    STANDARD_MIN_PER_SUBDOMAIN = 4
    STANDARD_MAX_PER_SUBDOMAIN = 5

    # ── DeepDive: all questions (150+) ──

    # ── Role weights for Standard mode routing ──
    ROLE_PRIORITY = [
        TargetRoleV2.TECHNICIAN,
        TargetRoleV2.SUPERVISOR,
        TargetRoleV2.MANAGER,
        TargetRoleV2.PLANNER,
        TargetRoleV2.RELIABILITY_ENGINEER,
    ]

    def __init__(self, db: Session):
        self.db = db

    def get_questions(
        self,
        assessment_id: int,
        respondent_role: Optional[TargetRoleV2] = None,
    ) -> List[Dict]:
        """
        Return the ordered list of questions for this assessment.

        Returns list of dicts with question metadata.
        """
        assessment = self.db.query(AssessmentV2).filter(
            AssessmentV2.id == assessment_id
        ).first()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        mode = assessment.assessment_mode

        if mode == AssessmentMode.QUICKSCAN:
            return self._route_quickscan()
        elif mode == AssessmentMode.STANDARD:
            return self._route_standard(respondent_role)
        elif mode == AssessmentMode.DEEPDIVE:
            return self._route_deepdive(respondent_role)
        else:
            raise ValueError(f"Unknown assessment mode: {mode}")

    # ─────────────────────────────────────────
    #  QuickScan (15 questions)
    # ─────────────────────────────────────────

    def _route_quickscan(self) -> List[Dict]:
        """
        Select 1 question per subdomain — the one tagged with quickscan mode,
        highest weight, and is_critical=True preference.
        """
        subdomains = self.db.query(Subdomain).order_by(Subdomain.display_order).all()
        questions = []

        for sd in subdomains:
            # Get all quickscan-eligible questions for this subdomain
            candidates = (
                self.db.query(QuestionV2)
                .filter(
                    QuestionV2.subdomain_id == sd.id,
                    QuestionV2.is_active == True,
                    QuestionV2.assessment_modes.contains("quickscan"),
                )
                .order_by(
                    QuestionV2.is_critical.desc(),
                    QuestionV2.weight.desc(),
                    QuestionV2.question_code,
                )
                .limit(self.QUICKSCAN_PER_SUBDOMAIN)
                .all()
            )

            for q in candidates:
                questions.append(self._format_question(q, sd))

        return questions

    # ─────────────────────────────────────────
    #  Standard (60-75 questions)
    # ─────────────────────────────────────────

    def _route_standard(self, respondent_role: Optional[TargetRoleV2] = None) -> List[Dict]:
        """
        Select 4-5 questions per subdomain, preferring:
        1. Critical questions always included
        2. Questions matching respondent role
        3. Questions tagged for 'standard' mode
        4. Highest weight first
        """
        subdomains = self.db.query(Subdomain).order_by(Subdomain.display_order).all()
        questions = []

        for sd in subdomains:
            base_query = (
                self.db.query(QuestionV2)
                .filter(
                    QuestionV2.subdomain_id == sd.id,
                    QuestionV2.is_active == True,
                    QuestionV2.assessment_modes.contains("standard"),
                )
            )

            # Critical questions are always included
            critical = base_query.filter(QuestionV2.is_critical == True).all()

            # Non-critical, filtered by role if specified, sorted by weight
            nc_query = base_query.filter(QuestionV2.is_critical == False)
            if respondent_role:
                nc_query = nc_query.filter(QuestionV2.target_role == respondent_role)
            non_critical = (
                nc_query
                .order_by(QuestionV2.weight.desc(), QuestionV2.question_code)
                .all()
            )

            # Combine: all critical + fill to max
            selected = list(critical)
            remaining_slots = self.STANDARD_MAX_PER_SUBDOMAIN - len(selected)
            selected.extend(non_critical[:max(remaining_slots, 0)])

            # Ensure minimum
            if len(selected) < self.STANDARD_MIN_PER_SUBDOMAIN:
                # Add more from deepdive-only pool
                deepdive_extras = (
                    self.db.query(QuestionV2)
                    .filter(
                        QuestionV2.subdomain_id == sd.id,
                        QuestionV2.is_active == True,
                        ~QuestionV2.id.in_([q.id for q in selected]),
                    )
                    .order_by(QuestionV2.weight.desc())
                    .limit(self.STANDARD_MIN_PER_SUBDOMAIN - len(selected))
                    .all()
                )
                selected.extend(deepdive_extras)

            for q in selected:
                questions.append(self._format_question(q, sd))

        return questions

    # ─────────────────────────────────────────
    #  DeepDive (150+ questions)
    # ─────────────────────────────────────────

    def _route_deepdive(self, respondent_role: Optional[TargetRoleV2] = None) -> List[Dict]:
        """Active questions filtered by role, ordered by subdomain then question_code."""
        query = (
            self.db.query(QuestionV2)
            .join(Subdomain)
            .filter(QuestionV2.is_active == True)
            .order_by(Subdomain.display_order, QuestionV2.question_code)
        )

        if respondent_role:
            # Filter to only questions targeting this role
            query = query.filter(QuestionV2.target_role == respondent_role)

        ordered = query.all()

        # Need subdomain info
        sd_map = {sd.id: sd for sd in self.db.query(Subdomain).all()}

        return [self._format_question(q, sd_map.get(q.subdomain_id)) for q in ordered]

    # ─────────────────────────────────────────
    #  Mode Transition
    # ─────────────────────────────────────────

    def upgrade_mode(self, assessment_id: int, new_mode: AssessmentMode) -> Dict:
        """
        Upgrade assessment mode (QuickScan → Standard → DeepDive).
        Existing responses are preserved; new questions are added.
        """
        assessment = self.db.query(AssessmentV2).filter(
            AssessmentV2.id == assessment_id
        ).first()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        mode_order = [AssessmentMode.QUICKSCAN, AssessmentMode.STANDARD, AssessmentMode.DEEPDIVE]
        current_idx = mode_order.index(assessment.assessment_mode)
        new_idx = mode_order.index(new_mode)

        if new_idx <= current_idx:
            raise ValueError(
                f"Cannot downgrade from {assessment.assessment_mode.value} to {new_mode.value}. "
                "Mode transitions are one-way: QuickScan → Standard → DeepDive."
            )

        old_mode = assessment.assessment_mode
        assessment.assessment_mode = new_mode
        self.db.commit()

        # Calculate new questions
        new_questions = self.get_questions(assessment_id)

        return {
            "assessment_id": assessment_id,
            "previous_mode": old_mode.value,
            "new_mode": new_mode.value,
            "total_questions": len(new_questions),
            "message": f"Upgraded from {old_mode.value} to {new_mode.value}. "
                       f"Existing responses preserved. {len(new_questions)} questions now available.",
        }

    # ─────────────────────────────────────────
    #  Helpers
    # ─────────────────────────────────────────

    def _format_question(self, q: QuestionV2, sd: Optional[Subdomain]) -> Dict:
        """Format a question for API response."""
        rubric = q.scoring_rubric
        if isinstance(rubric, str):
            try:
                rubric = json.loads(rubric)
            except (json.JSONDecodeError, TypeError):
                rubric = {}

        modes = q.assessment_modes
        if isinstance(modes, str):
            try:
                modes = json.loads(modes)
            except (json.JSONDecodeError, TypeError):
                modes = []

        # Derive domain info from subdomain relationship
        domain = sd.domain if sd and hasattr(sd, 'domain') and sd.domain else None
        domain_code = domain.code if domain else (sd.code.split('.')[0] if sd and sd.code else None)
        domain_name = domain.name if domain else None

        return {
            "id": q.id,
            "question_code": q.question_code,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "domain_code": domain_code,
            "domain_name": domain_name,
            "subdomain_code": sd.code if sd else None,
            "subdomain_name": sd.name if sd else None,
            "target_role": q.target_role.value if q.target_role else None,
            "weight": q.weight,
            "is_critical": q.is_critical,
            "evidence_required": q.evidence_required,
            "evidence_guidance": q.evidence_guidance,
            "scoring_rubric": rubric,
            "calibration_anchor": q.calibration_anchor,
            "assessment_modes": modes,
            "iso_55001_clause": q.iso_55001_clause,
        }

    def get_progress(self, assessment_id: int) -> Dict:
        """Calculate assessment completion progress."""
        from models_v2 import ResponseV2

        assessment = self.db.query(AssessmentV2).filter(
            AssessmentV2.id == assessment_id
        ).first()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        total_questions = len(self.get_questions(assessment_id))
        answered = self.db.query(ResponseV2).filter(
            ResponseV2.assessment_id == assessment_id,
            ResponseV2.is_draft == False,
        ).count()

        return {
            "assessment_id": assessment_id,
            "mode": assessment.assessment_mode.value,
            "total_questions": total_questions,
            "answered": answered,
            "remaining": max(total_questions - answered, 0),
            "completion_pct": round(answered / total_questions * 100, 1) if total_questions > 0 else 0,
        }
