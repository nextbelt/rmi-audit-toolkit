"""
Shared pytest fixtures: in-memory SQLite, FastAPI TestClient, and a logged-in
user/admin pair for RBAC tests.
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

# Make backend/ the import root no matter where pytest is invoked from.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Configure env BEFORE importing app modules
os.environ.setdefault("SECRET_KEY", "test-only-key-with-sufficient-length-for-checks-0123456789")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
# Test fixtures create @example.com users; allow that domain in tests.
os.environ.setdefault("ALLOWED_EMAIL_DOMAIN", "example.com")


from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database  # noqa: E402  -- must come after env setup
from database import Base, get_db  # noqa: E402


@pytest.fixture(scope="function")
def tmp_upload_dir(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    monkeypatch.setattr("config.settings.UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr("config.settings.REPORT_OUTPUT_DIR", str(report_dir))
    yield {"upload": str(upload_dir), "report": str(report_dir)}


@pytest.fixture(scope="function")
def db_session(tmp_path, monkeypatch):
    """A fresh in-process SQLite database for each test."""
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    test_engine = create_engine(url, connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", TestingSession)

    # Import all model modules so their tables are registered on Base.metadata
    import models  # noqa: F401
    import models_v2  # noqa: F401
    import models_extra  # noqa: F401

    Base.metadata.create_all(bind=test_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session, tmp_upload_dir, monkeypatch):
    """FastAPI TestClient with the test DB wired in."""
    from main import app

    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    """Factory that creates a user and returns (user, plaintext_password)."""
    import bcrypt
    from models import User

    counter = {"n": 0}

    def _make(*, email=None, role="auditor", password="ALongTestPassword123!", active=True):
        counter["n"] += 1
        em = email or f"user{counter['n']}@example.com"
        u = User(
            email=em,
            full_name=f"User {counter['n']}",
            role=role,
            is_active=active,
            hashed_password=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        return u, password

    return _make


@pytest.fixture
def auth_headers(client, make_user):
    """Return a function that gives `Authorization: Bearer ...` headers."""
    def _headers(user_password_pair):
        user, password = user_password_pair
        r = client.post(
            "/token",
            data={"username": user.email, "password": password},
        )
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _headers
