"""
Configuration management for RMI Audit Software.
"""
import os
import sys
from typing import List, Optional
from pydantic_settings import BaseSettings


# Substrings that mark a key as obviously placeholder. Be conservative — a
# valid randomly-generated key must not contain any of these.
_INSECURE_SECRET_PATTERNS = (
    "development",
    "change-in-production",
    "change-this",
    "change-me",
    "your-super-secret",
    "your-secret",
    "your-jwt",
    "example.com",
    "replace-with",
    "placeholder",
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "sqlite:///./rmi_audit.db"

    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application
    APP_NAME: str = "RMI Audit Software"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # "development" | "production"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_UPLOAD_SIZE: int = 52428800
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_UPLOAD_MIME: List[str] = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/pdf",
        "image/png",
        "image/jpeg",
    ]
    ALLOWED_UPLOAD_EXT: List[str] = [".csv", ".xls", ".xlsx", ".pdf", ".png", ".jpg", ".jpeg"]

    # Reporting
    REPORT_OUTPUT_DIR: str = "./reports"
    LOGO_PATH: Optional[str] = None

    # Supabase (kept for forward compatibility; backend does not currently use)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Admin seed (init_db.py will refuse to create a default admin unless these are set)
    INITIAL_ADMIN_EMAIL: Optional[str] = None
    INITIAL_ADMIN_PASSWORD: Optional[str] = None

    # Rate limiting
    LOGIN_RATE_LIMIT_PER_MIN: int = 10

    # Password reset
    PASSWORD_RESET_TOKEN_TTL_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def _is_insecure_secret(key: str) -> bool:
    if not key or len(key) < 32:
        return True
    lowered = key.lower()
    return any(p in lowered for p in _INSECURE_SECRET_PATTERNS)


def assert_production_secrets() -> None:
    """Refuse to boot in production with an obviously weak SECRET_KEY.

    Called by main.py at startup. In ENVIRONMENT=development we only warn so
    local dev doesn't require a 32+ char key.
    """
    is_prod = settings.ENVIRONMENT.lower() == "production"
    if _is_insecure_secret(settings.SECRET_KEY):
        if is_prod:
            sys.stderr.write(
                "FATAL: SECRET_KEY is missing or insecure. "
                "Generate one with `python -c \"import secrets; print(secrets.token_urlsafe(48))\"` "
                "and set SECRET_KEY in the environment before booting.\n"
            )
            sys.exit(1)
        else:
            # Non-fatal in dev, but loud
            sys.stderr.write(
                "WARNING: SECRET_KEY is insecure (default or <32 chars). "
                "Set SECRET_KEY before running in production.\n"
            )
