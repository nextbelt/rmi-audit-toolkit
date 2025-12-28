"""
Configuration management for RMI Audit Software
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./rmi_audit.db"
    
    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    APP_NAME: str = "RMI Audit Software"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_UPLOAD_SIZE: int = 52428800  # bytes
    UPLOAD_DIR: str = "./uploads"
    
    # Reporting
    REPORT_OUTPUT_DIR: str = "./reports"
    LOGO_PATH: Optional[str] = None
    
    # Supabase (optional - for enhanced auth)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
