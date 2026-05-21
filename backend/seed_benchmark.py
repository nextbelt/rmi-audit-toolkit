"""
Seed synthetic peer assessment data for benchmarking demonstrations.
Creates 8 anonymized peer assessments with realistic score distributions
so the benchmarking engine can produce percentile rankings.
"""
import os, sys, random, json
from datetime import datetime, timedelta

os.environ.setdefault("LOCAL_DEV_MODE", "true")
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import User
from models_v2 import (
    AssessmentV2, AssessmentMode, IndustryModule,
    SubdomainScore, Subdomain, Domain,
)


# Synthetic peer profiles — anonymized site names with realistic score bands
PEER_PROFILES = [
    {"site": "Peer Site Alpha",   "org": "Anon Corp A", "mode": "standard", "industry": "MFG", "band": (2.0, 2.8)},
    {"site": "Peer Site Beta",    "org": "Anon Corp B", "mode": "standard", "industry": "MFG", "band": (2.5, 3.3)},
    {"site": "Peer Site Gamma",   "org": "Anon Corp C", "mode": "standard", "industry": "MFG", "band": (2.8, 3.5)},
    {"site": "Peer Site Delta",   "org": "Anon Corp D", "mode": "standard", "industry": "MFG", "band": (3.0, 3.8)},
    {"site": "Peer Site Epsilon", "org": "Anon Corp E", "mode": "standard", "industry": "MFG", "band": (3.2, 4.0)},
    {"site": "Peer Site Zeta",    "org": "Anon Corp F", "mode": "deepdive", "industry": "MFG", "band": (3.5, 4.2)},
    {"site": "Peer Site Eta",     "org": "Anon Corp G", "mode": "standard", "industry": "FNB", "band": (1.8, 2.5)},
    {"site": "Peer Site Theta",   "org": "Anon Corp H", "mode": "standard", "industry": "ONG", "band": (3.8, 4.5)},
]


def seed_benchmark_peers(db):
    """Create synthetic peer assessments with subdomain scores."""
    # Find or create a system user for synthetic data
    system_user = db.query(User).filter(User.email == "admin@nextbelt.com").first()
    if not system_user:
        print("  ⚠️  No admin user found. Run init_db.py first.")
        return 0

    subdomains = db.query(Subdomain).order_by(Subdomain.display_order).all()
    if not subdomains:
        print("  ⚠️  No subdomains found. Run init_db.py first.")
        return 0

    created = 0
    random.seed(42)  # Reproducible results

    for profile in PEER_PROFILES:
        # Check if already seeded
        existing = db.query(AssessmentV2).filter(
            AssessmentV2.site_name == profile["site"]
        ).first()

        lo, hi = profile["band"]

        # Generate subdomain scores within the band
        sd_scores_vals = {}
        for sd in subdomains:
            base = random.uniform(lo, hi)
            noise = random.gauss(0, 0.3)
            score = max(1.0, min(5.0, round(base + noise, 2)))
            sd_scores_vals[sd.id] = score

        overall = round(sum(sd_scores_vals.values()) / len(sd_scores_vals), 2)

        if overall >= 4.5:
            mat_level = "World-Class"
        elif overall >= 3.5:
            mat_level = "Proactive"
        elif overall >= 2.5:
            mat_level = "Systematic"
        elif overall >= 1.5:
            mat_level = "Emerging"
        else:
            mat_level = "Reactive"

        days_ago = random.randint(30, 700)
        assess_date = datetime.utcnow() - timedelta(days=days_ago)

        industry_enum = IndustryModule(profile["industry"]) if profile["industry"] in [e.value for e in IndustryModule] else None
        mode_enum = AssessmentMode(profile["mode"])

        if existing:
            # Update existing assessment if it has null scores
            if existing.overall_rmi is None:
                existing.overall_rmi = overall
                existing.maturity_level = mat_level
                existing.confidence_score = round(random.uniform(0.7, 0.95), 2)
                # Update subdomain scores
                for sd in subdomains:
                    score_val = sd_scores_vals[sd.id]
                    sd_score = db.query(SubdomainScore).filter(
                        SubdomainScore.assessment_id == existing.id,
                        SubdomainScore.subdomain_id == sd.id,
                    ).first()
                    if sd_score:
                        sd_score.raw_score = score_val
                        sd_score.weighted_score = score_val
                        sd_score.final_score = score_val
                        sd_score.confidence = round(random.uniform(0.65, 0.95), 2)
                    else:
                        db.add(SubdomainScore(
                            assessment_id=existing.id,
                            subdomain_id=sd.id,
                            raw_score=score_val,
                            weighted_score=score_val,
                            final_score=score_val,
                            confidence=round(random.uniform(0.65, 0.95), 2),
                        ))
                created += 1
            continue

        assessment = AssessmentV2(
            client_name=profile["org"],
            site_name=profile["site"],
            industry=profile["industry"],
            assessment_mode=mode_enum,
            industry_module=industry_enum,
            status="FINALIZED",
            assessment_date=assess_date,
            overall_rmi=overall,
            confidence_score=round(random.uniform(0.7, 0.95), 2),
            maturity_level=mat_level,
            creator_id=system_user.id,
        )
        db.add(assessment)
        db.flush()  # Get the ID

        # Create subdomain scores
        for sd in subdomains:
            score_val = sd_scores_vals[sd.id]
            sd_score = SubdomainScore(
                assessment_id=assessment.id,
                subdomain_id=sd.id,
                raw_score=score_val,
                weighted_score=score_val,
                final_score=score_val,
                confidence=round(random.uniform(0.65, 0.95), 2),
            )
            db.add(sd_score)

        created += 1

    db.commit()
    return created


if __name__ == "__main__":
    db = SessionLocal()
    try:
        n = seed_benchmark_peers(db)
        print(f"✅ Seeded {n} peer assessments for benchmarking")
    finally:
        db.close()
