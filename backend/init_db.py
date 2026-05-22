"""
Database initialization.

Creates tables, registers v1 + v2 metadata, seeds the question bank, practices,
and benchmark peer data. Will only create a default admin user when both
INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD environment variables are set.

Usage:
    INITIAL_ADMIN_EMAIL=you@example.com \\
    INITIAL_ADMIN_PASSWORD='a-long-strong-password' \\
    python init_db.py
"""
from __future__ import annotations

import logging
import sys

import bcrypt

import models_extra  # noqa: F401 -- registers audit_log + assessment_members
import models_v2  # noqa: F401 -- registers v2 tables
from config import settings
from database import SessionLocal, init_db
from models import QuestionBank, User
from question_bank import seed_question_bank
from question_bank_v2 import seed_domains_and_subdomains, seed_question_bank_v2

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("init_db")


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def initialize_database() -> None:
    log.info("Creating tables…")
    init_db()

    db = SessionLocal()
    try:
        if db.query(QuestionBank).count() > 0:
            log.info("v1 question bank already seeded; skipping.")
        else:
            log.info("Seeding v1 question bank…")
            seed_question_bank(db)
        log.info("Seeding v2 domains + subdomains…")
        seed_domains_and_subdomains(db)
        log.info("Seeding v2 question bank…")
        seed_question_bank_v2(db)

        if settings.INITIAL_ADMIN_EMAIL and settings.INITIAL_ADMIN_PASSWORD:
            if len(settings.INITIAL_ADMIN_PASSWORD) < 12:
                if settings.ENVIRONMENT.lower() == "production":
                    log.error("INITIAL_ADMIN_PASSWORD must be at least 12 characters.")
                    sys.exit(2)
                log.warning(
                    "INITIAL_ADMIN_PASSWORD is shorter than 12 characters; "
                    "allowing it only because ENVIRONMENT=%s.",
                    settings.ENVIRONMENT,
                )
            existing = db.query(User).filter(User.email == settings.INITIAL_ADMIN_EMAIL).first()
            if existing:
                log.info("Admin user already exists; skipping.")
            else:
                admin = User(
                    email=settings.INITIAL_ADMIN_EMAIL,
                    hashed_password=_hash(settings.INITIAL_ADMIN_PASSWORD),
                    full_name="System Administrator",
                    role="admin",
                    is_active=True,
                )
                db.add(admin)
                db.commit()
                log.info("Created admin %s", settings.INITIAL_ADMIN_EMAIL)
        else:
            log.warning(
                "INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD not set — skipping admin seed. "
                "Set them in the environment to create the first admin user."
            )
    finally:
        db.close()

    try:
        from seed_practices import seed_practices

        db2 = SessionLocal()
        try:
            log.info("Seeding practice library…")
            seed_practices(db2)
        finally:
            db2.close()
    except Exception as exc:
        log.warning("Practice seeding skipped: %s", exc)

    try:
        from seed_benchmark import seed_benchmark_peers

        db3 = SessionLocal()
        try:
            log.info("Seeding benchmark peer data…")
            seed_benchmark_peers(db3)
        finally:
            db3.close()
    except Exception as exc:
        log.warning("Benchmark seeding skipped: %s", exc)

    log.info("Database initialization complete.")


if __name__ == "__main__":
    initialize_database()
