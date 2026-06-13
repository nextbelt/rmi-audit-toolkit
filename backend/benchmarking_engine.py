"""
RMI vNext Benchmarking Engine
Percentile ranking, peer-group segmentation, and portfolio benchmarking.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from models import User  # noqa: F401 – must be imported before models_v2 (SQLAlchemy relationship)
from models_v2 import (
    AssessmentV2, SubdomainScore, BenchmarkMetadata,
    AssessmentMode, IndustryModule, Domain, Subdomain
)


class BenchmarkingEngine:
    """
    Provides percentile rankings against anonymized peer groups.
    """

    # Minimum assessments in a peer group to show benchmarks
    MIN_ANONYMITY_THRESHOLD = 5
    # Full percentile resolution requires 30+ assessments
    FULL_BENCHMARK_THRESHOLD = 30
    # Rolling window (years) for peer data
    ROLLING_WINDOW_YEARS = 3

    # ── Peer group segmentation dimensions ──
    VALID_INDUSTRIES = [m.value for m in IndustryModule]
    SIZE_BUCKETS = ["small", "medium", "large", "enterprise"]
    SIZE_THRESHOLDS = {
        "small": (0, 100),
        "medium": (101, 500),
        "large": (501, 2000),
        "enterprise": (2001, float("inf")),
    }

    def __init__(self, db: Session):
        self.db = db

    # ═══════════════════════════════════════════
    #  PUBLIC API
    # ═══════════════════════════════════════════

    def benchmark_assessment(self, assessment_id: int) -> Dict:
        """
        Calculate percentile rankings for an assessment against its peer group.
        """
        assessment = self.db.query(AssessmentV2).filter(
            AssessmentV2.id == assessment_id
        ).first()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        if assessment.overall_rmi is None:
            raise ValueError("Assessment has not been scored yet")

        # Determine peer group
        peer_group = self._build_peer_group(assessment)
        peer_scores = self._get_peer_scores(peer_group, exclude_id=assessment_id)

        if len(peer_scores) < self.MIN_ANONYMITY_THRESHOLD:
            return {
                "assessment_id": assessment_id,
                "status": "insufficient_peers",
                "peer_count": len(peer_scores),
                "min_required": self.MIN_ANONYMITY_THRESHOLD,
                "message": f"Only {len(peer_scores)} peers found; need {self.MIN_ANONYMITY_THRESHOLD} for benchmarking.",
            }

        # Overall percentile
        overall_pct = self._percentile(assessment.overall_rmi, [s["overall_rmi"] for s in peer_scores])

        # Domain percentiles
        domain_benchmarks = self._domain_benchmarks(assessment_id, peer_scores)

        # Quartile
        quartile = self._quartile(overall_pct)

        # Peer group stats
        overall_scores = [s["overall_rmi"] for s in peer_scores if s["overall_rmi"] is not None]
        peer_stats = {
            "count": len(peer_scores),
            "mean": round(mean(overall_scores), 2) if overall_scores else None,
            "std_dev": round(stdev(overall_scores), 2) if len(overall_scores) > 1 else None,
            "min": round(min(overall_scores), 2) if overall_scores else None,
            "max": round(max(overall_scores), 2) if overall_scores else None,
        }

        result = {
            "assessment_id": assessment_id,
            "status": "benchmarked",
            "overall_rmi": assessment.overall_rmi,
            "percentile": overall_pct,
            "quartile": quartile,
            "quartile_label": self._quartile_label(quartile),
            "peer_group": peer_group,
            "peer_stats": peer_stats,
            "domain_benchmarks": domain_benchmarks,
            "calculated_at": datetime.utcnow().isoformat(),
        }

        # Persist benchmark metadata
        self._persist_benchmark(assessment, result)

        return result

    def get_industry_stats(self, industry: str) -> Dict:
        """Get aggregated statistics for an industry."""
        cutoff = datetime.utcnow() - timedelta(days=self.ROLLING_WINDOW_YEARS * 365)

        assessments = (
            self.db.query(AssessmentV2)
            .filter(
                AssessmentV2.industry_module == industry,
                AssessmentV2.overall_rmi.isnot(None),
                AssessmentV2.assessment_date >= cutoff,
            )
            .all()
        )

        if len(assessments) < self.MIN_ANONYMITY_THRESHOLD:
            return {"industry": industry, "status": "insufficient_data",
                    "count": len(assessments)}

        scores = [a.overall_rmi for a in assessments]
        return {
            "industry": industry,
            "status": "available",
            "count": len(assessments),
            "mean": round(mean(scores), 2),
            "median": round(sorted(scores)[len(scores) // 2], 2),
            "std_dev": round(stdev(scores), 2) if len(scores) > 1 else 0,
            "p25": round(self._percentile_value(scores, 25), 2),
            "p50": round(self._percentile_value(scores, 50), 2),
            "p75": round(self._percentile_value(scores, 75), 2),
            "p90": round(self._percentile_value(scores, 90), 2),
        }

    def portfolio_benchmark(self, site_names: List[str]) -> Dict:
        """
        Multi-site portfolio benchmarking for enterprise customers.
        """
        assessments = (
            self.db.query(AssessmentV2)
            .filter(
                AssessmentV2.site_name.in_(site_names),
                AssessmentV2.overall_rmi.isnot(None),
            )
            .order_by(AssessmentV2.assessment_date.desc())
            .all()
        )

        # Get latest per site
        latest_by_site: Dict[str, AssessmentV2] = {}
        for a in assessments:
            if a.site_name not in latest_by_site:
                latest_by_site[a.site_name] = a

        if len(latest_by_site) < 2:
            return {"status": "insufficient_sites", "count": len(latest_by_site)}

        sites = []
        for name, a in sorted(latest_by_site.items(), key=lambda x: x[1].overall_rmi or 0, reverse=True):
            sites.append({
                "site_name": name,
                "overall_rmi": a.overall_rmi,
                "maturity_level": a.maturity_level,
                "assessment_date": a.assessment_date.isoformat() if a.assessment_date else None,
                "mode": a.assessment_mode.value if a.assessment_mode else None,
            })

        scores = [s["overall_rmi"] for s in sites if s["overall_rmi"] is not None]
        return {
            "status": "available",
            "site_count": len(sites),
            "sites": sites,
            "portfolio_mean": round(mean(scores), 2) if scores else None,
            "portfolio_spread": round(max(scores) - min(scores), 2) if len(scores) > 1 else 0,
            "best_practice_site": sites[0]["site_name"] if sites else None,
        }

    # ═══════════════════════════════════════════
    #  PEER GROUP
    # ═══════════════════════════════════════════

    def _build_peer_group(self, assessment: AssessmentV2) -> Dict:
        """Determine the peer group for an assessment."""
        industry = assessment.industry_module.value if assessment.industry_module else None
        employee_count = getattr(assessment, 'employee_count', None) or 0
        size = "medium"
        for bucket, (lo, hi) in self.SIZE_THRESHOLDS.items():
            if lo <= employee_count <= hi:
                size = bucket
                break

        return {
            "industry": industry,
            "size": size,
            "mode": assessment.assessment_mode.value if assessment.assessment_mode else None,
            "region": getattr(assessment, 'region', None),
        }

    def _get_peer_scores(self, peer_group: Dict, exclude_id: int = 0) -> List[Dict]:
        """Fetch scored assessments matching the peer group."""
        cutoff = datetime.utcnow() - timedelta(days=self.ROLLING_WINDOW_YEARS * 365)

        query = self.db.query(AssessmentV2).filter(
            AssessmentV2.overall_rmi.isnot(None),
            AssessmentV2.assessment_date >= cutoff,
            AssessmentV2.id != exclude_id,
        )

        # Filter by industry (primary segmentation)
        if peer_group.get("industry"):
            query = query.filter(AssessmentV2.industry_module == peer_group["industry"])

        # Filter by size bucket (only if the column exists on the model)
        if peer_group.get("size") and hasattr(AssessmentV2, 'employee_count'):
            lo, hi = self.SIZE_THRESHOLDS.get(peer_group["size"], (0, float("inf")))
            if hi != float("inf"):
                query = query.filter(
                    AssessmentV2.employee_count >= lo,
                    AssessmentV2.employee_count <= hi,
                )
            else:
                query = query.filter(AssessmentV2.employee_count >= lo)

        return [
            {"id": a.id, "overall_rmi": a.overall_rmi, "site_name": a.site_name}
            for a in query.all()
        ]

    # ═══════════════════════════════════════════
    #  DOMAIN BENCHMARKS
    # ═══════════════════════════════════════════

    def _domain_benchmarks(self, assessment_id: int, peer_scores: List[Dict]) -> Dict:
        """Calculate per-domain percentiles.

        Batched: 2 queries total (ours + all peers) instead of 5 x (1 + N peers).
        """
        domains = self.db.query(Domain).order_by(Domain.display_order).all()
        domain_by_id = {d.id: d.code for d in domains}
        peer_ids = [p["id"] for p in peer_scores]

        # ── One query: our subdomain scores keyed by domain ──
        our_by_domain: Dict[str, List[float]] = {}
        our_rows = (
            self.db.query(SubdomainScore.final_score, Subdomain.domain_id)
            .join(Subdomain, SubdomainScore.subdomain_id == Subdomain.id)
            .filter(SubdomainScore.assessment_id == assessment_id)
            .all()
        )
        for final_score, domain_id in our_rows:
            if final_score is not None:
                our_by_domain.setdefault(domain_by_id.get(domain_id, ""), []).append(final_score)

        # ── One query: ALL peer subdomain scores, grouped (assessment, domain) ──
        peer_by_assessment_domain: Dict[tuple, List[float]] = {}
        if peer_ids:
            peer_rows = (
                self.db.query(
                    SubdomainScore.assessment_id, SubdomainScore.final_score, Subdomain.domain_id
                )
                .join(Subdomain, SubdomainScore.subdomain_id == Subdomain.id)
                .filter(SubdomainScore.assessment_id.in_(peer_ids))
                .all()
            )
            for a_id, final_score, domain_id in peer_rows:
                if final_score is not None:
                    code = domain_by_id.get(domain_id, "")
                    peer_by_assessment_domain.setdefault((a_id, code), []).append(final_score)

        result = {}
        for dom in domains:
            our_list = our_by_domain.get(dom.code, [])
            our_domain_avg = mean(our_list) if our_list else None

            peer_domain_avgs = [
                mean(scores)
                for (a_id, code), scores in peer_by_assessment_domain.items()
                if code == dom.code and scores
            ]

            pct = (
                self._percentile(our_domain_avg, peer_domain_avgs)
                if peer_domain_avgs and our_domain_avg is not None else None
            )
            result[dom.code] = {
                "score": round(our_domain_avg, 2) if our_domain_avg is not None else None,
                "percentile": pct,
                "quartile": self._quartile(pct) if pct is not None else None,
            }

        return result

    # ═══════════════════════════════════════════
    #  STATISTICS HELPERS
    # ═══════════════════════════════════════════

    @staticmethod
    def _percentile(value: float, population: List[float]) -> int:
        """Calculate the percentile rank of value within population."""
        if not population:
            return 50
        below = sum(1 for v in population if v < value)
        equal = sum(1 for v in population if v == value)
        return round((below + 0.5 * equal) / len(population) * 100)

    @staticmethod
    def _percentile_value(data: List[float], pct: int) -> float:
        """Get the value at a given percentile from sorted data."""
        s = sorted(data)
        idx = (pct / 100) * (len(s) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(s) - 1)
        frac = idx - lo
        return s[lo] + frac * (s[hi] - s[lo])

    @staticmethod
    def _quartile(percentile: int) -> int:
        if percentile >= 75:
            return 1  # Top quartile
        elif percentile >= 50:
            return 2
        elif percentile >= 25:
            return 3
        else:
            return 4  # Bottom quartile

    @staticmethod
    def _quartile_label(q: int) -> str:
        return {1: "Top Quartile", 2: "Second Quartile",
                3: "Third Quartile", 4: "Bottom Quartile"}.get(q, "Unknown")

    # ═══════════════════════════════════════════
    #  PERSISTENCE
    # ═══════════════════════════════════════════

    def _persist_benchmark(self, assessment: AssessmentV2, result: Dict):
        """Save benchmark metadata.

        Columns are JSON-typed, so dicts are stored directly (no json.dumps).
        Field names must match the BenchmarkMetadata model exactly.
        """
        existing = self.db.query(BenchmarkMetadata).filter(
            BenchmarkMetadata.assessment_id == assessment.id
        ).first()

        peer_group = result.get("peer_group", {})
        peer_count = result["peer_stats"]["count"]
        overall_percentile = result["percentile"]
        domain_percentiles = result.get("domain_benchmarks", {})

        if existing:
            existing.peer_group_criteria = peer_group
            existing.peer_count = peer_count
            existing.overall_percentile = overall_percentile
            existing.domain_percentiles = domain_percentiles
            existing.industry_code = peer_group.get("industry")
            existing.site_size_category = (peer_group.get("size") or "").upper() or None
            existing.region = peer_group.get("region")
            existing.calculated_at = datetime.utcnow()
        else:
            self.db.add(BenchmarkMetadata(
                assessment_id=assessment.id,
                peer_group_criteria=peer_group,
                peer_count=peer_count,
                overall_percentile=overall_percentile,
                domain_percentiles=domain_percentiles,
                industry_code=peer_group.get("industry"),
                site_size_category=(peer_group.get("size") or "").upper() or None,
                region=peer_group.get("region"),
                calculated_at=datetime.utcnow(),
            ))

        self.db.commit()
