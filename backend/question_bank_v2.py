"""
RMI vNext Question Bank Seeder
Reads the 150-question JSON spec and populates the database.
"""
import json
import os
from pathlib import Path
from sqlalchemy.orm import Session

from models_v2 import (
    Domain, Subdomain, QuestionV2, DomainType, SubdomainType, TargetRoleV2
)

# ── Map string codes to enums ──
DOMAIN_ENUM_MAP = {
    "WC": DomainType.WC,
    "LC": DomainType.LC,
    "WM": DomainType.WM,
    "AI": DomainType.AI,
    "SG": DomainType.SG,
}

SUBDOMAIN_ENUM_MAP = {
    "WC.1": SubdomainType.WC_1, "WC.2": SubdomainType.WC_2, "WC.3": SubdomainType.WC_3,
    "LC.1": SubdomainType.LC_1, "LC.2": SubdomainType.LC_2, "LC.3": SubdomainType.LC_3,
    "WM.1": SubdomainType.WM_1, "WM.2": SubdomainType.WM_2, "WM.3": SubdomainType.WM_3,
    "AI.1": SubdomainType.AI_1, "AI.2": SubdomainType.AI_2, "AI.3": SubdomainType.AI_3,
    "SG.1": SubdomainType.SG_1, "SG.2": SubdomainType.SG_2, "SG.3": SubdomainType.SG_3,
}

ROLE_MAP = {
    "SUPERVISOR": TargetRoleV2.SUPERVISOR,
    "MANAGER": TargetRoleV2.MANAGER,
    "TECHNICIAN": TargetRoleV2.TECHNICIAN,
    "PLANNER": TargetRoleV2.PLANNER,
    "AUDITOR": TargetRoleV2.RELIABILITY_ENGINEER,  # vNext renamed AUDITOR → RE
    "RELIABILITY_ENGINEER": TargetRoleV2.RELIABILITY_ENGINEER,
}

DOMAIN_DESCRIPTIONS = {
    "WC": "Technical competency, training & development, and knowledge management across the maintenance workforce.",
    "LC": "Management commitment, safety & reliability culture, and organizational structure for maintenance excellence.",
    "WM": "Planning & scheduling, preventive/predictive maintenance, and work execution quality.",
    "AI": "CMMS/EAM effectiveness, data quality & integrity, and analytics & decision support.",
    "SG": "Asset management policy, performance measurement, and continuous improvement governance.",
}


def _locate_json() -> Path:
    """Find the question bank JSON relative to this file."""
    candidates = [
        Path(__file__).resolve().parent.parent / "docs" / "rmi-vnext" / "04-question-bank.json",
        Path(__file__).resolve().parent / "04-question-bank.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Could not find 04-question-bank.json. "
        "Place it in docs/rmi-vnext/ or in the backend/ directory."
    )


def seed_domains_and_subdomains(db: Session) -> dict:
    """Create the 5 domains and 15 subdomains. Returns {code: id} maps."""
    domain_map: dict[str, int] = {}
    subdomain_map: dict[str, int] = {}

    json_path = _locate_json()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for d_order, domain_data in enumerate(data["domains"], start=1):
        code = domain_data["domain_code"]
        existing = db.query(Domain).filter(Domain.code == code).first()
        if existing:
            domain_map[code] = existing.id
        else:
            dom = Domain(
                code=code,
                name=domain_data["domain_name"],
                description=DOMAIN_DESCRIPTIONS.get(code, ""),
                display_order=d_order,
            )
            db.add(dom)
            db.flush()
            domain_map[code] = dom.id

        for sd_order, sub_data in enumerate(domain_data["subdomains"], start=1):
            sd_code = sub_data["subdomain_code"]
            existing_sd = db.query(Subdomain).filter(Subdomain.code == sd_code).first()
            if existing_sd:
                subdomain_map[sd_code] = existing_sd.id
            else:
                sd = Subdomain(
                    code=sd_code,
                    name=sub_data["subdomain_name"],
                    domain_id=domain_map[code],
                    display_order=d_order * 10 + sd_order,
                )
                db.add(sd)
                db.flush()
                subdomain_map[sd_code] = sd.id

    db.commit()
    return {"domains": domain_map, "subdomains": subdomain_map}


def seed_question_bank_v2(db: Session) -> int:
    """
    Seed all 150 questions from the JSON spec.
    Returns the count of questions inserted (skips existing by question_code).
    """
    maps = seed_domains_and_subdomains(db)
    subdomain_map = maps["subdomains"]

    json_path = _locate_json()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    inserted = 0
    for domain_data in data["domains"]:
        for sub_data in domain_data["subdomains"]:
            sd_code = sub_data["subdomain_code"]
            sd_id = subdomain_map[sd_code]

            for q_order, q in enumerate(sub_data["questions"], start=1):
                # Skip if already seeded
                exists = db.query(QuestionV2).filter(
                    QuestionV2.question_code == q["question_code"]
                ).first()
                if exists:
                    continue

                # Determine the domain code from the subdomain code (e.g. "WC.1" → "WC")
                domain_code = sd_code.split(".")[0]
                question = QuestionV2(
                    question_code=q["question_code"],
                    question_text=q["question_text"],
                    question_type=q["question_type"],
                    domain=DOMAIN_ENUM_MAP[domain_code],
                    subdomain_id=sd_id,
                    target_role=ROLE_MAP.get(q.get("target_role"), TargetRoleV2.TECHNICIAN),
                    # Store a real JSON array (the column is JSON). An older
                    # revision json.dumps'd this into a string, which made the
                    # SQL `contains` filter fail on Postgres; routing now parses
                    # modes in Python so both encodings work, but new rows should
                    # be clean arrays.
                    assessment_modes=q.get("assessment_mode", ["standard", "deepdive"]),
                    weight=q.get("weight", 1.0),
                    is_critical=q.get("is_critical", False),
                    evidence_required=q.get("evidence_required", False),
                    evidence_guidance=q.get("evidence_guidance"),
                    scoring_rubric=json.dumps(q.get("scoring_rubric", {})),
                    iso_55001_clause=q.get("iso_55001_clause"),
                    calibration_anchor=q.get("calibration_anchor"),
                    practice_link=q.get("practice_link"),
                    is_active=True,
                )
                db.add(question)
                inserted += 1

    db.commit()
    print(f"[seed] Inserted {inserted} vNext questions.")
    return inserted
