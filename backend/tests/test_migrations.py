"""
Migration Forward + Rollback Tests — verifies that all SQLAlchemy models can
create their tables from scratch and that drop-and-recreate is idempotent.

Run with:
    pytest tests/test_migrations.py -v
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker


def _all_expected_tables() -> frozenset[str]:
    """Return the complete set of table names that should exist after create_all."""
    import models  # noqa: F401  -- registers v1 tables on Base.metadata
    import models_extra  # noqa: F401  -- registers audit_log, assessment_members, etc.
    import models_v2  # noqa: F401  -- registers v2 tables on Base.metadata

    import database

    return frozenset(database.Base.metadata.tables.keys())


def test_forward_migration_creates_all_tables(tmp_path):
    """Base.metadata.create_all() should produce every table we expect."""
    from database import Base

    db_file = tmp_path / "fwd.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )

    expected = _all_expected_tables()
    Base.metadata.create_all(bind=engine)

    actual = set(inspect(engine).get_table_names())
    missing = expected - actual

    assert not missing, f"Tables missing after create_all: {sorted(missing)}"
    assert len(actual) >= 14, f"Expected >= 14 tables, found only {len(actual)}: {sorted(actual)}"


def test_rollback_and_recreate_is_idempotent(tmp_path):
    """drop_all followed by create_all must produce the same schema."""
    from database import Base

    db_file = tmp_path / "rollback.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )

    expected = _all_expected_tables()
    Base.metadata.create_all(bind=engine)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    actual = set(inspect(engine).get_table_names())
    missing = expected - actual

    assert not missing, f"Tables missing after drop/recreate: {sorted(missing)}"
    assert len(actual) >= 14, (
        f"Drop + recreate produced only {len(actual)} tables: {sorted(actual)}"
    )
