"""
Supabase Authentication Integration
Replaces JWT auth with Supabase Auth for production deployment
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os
from typing import Optional

# Supabase client setup
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

security = HTTPBearer()


async def get_current_user_supabase(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verify Supabase JWT token and return user data
    Use this instead of get_current_user when Supabase auth is enabled
    """
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase not configured"
        )
    
    token = credentials.credentials
    
    try:
        # Verify the JWT token with Supabase
        user = supabase.auth.get_user(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_supabase_user(email: str, password: str, metadata: dict = None):
    """
    Create a new user in Supabase Auth
    Called when registering new auditors/clients
    """
    if not supabase:
        raise Exception("Supabase not configured")
    
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": metadata or {}
            }
        })
        return response
    except Exception as e:
        raise Exception(f"Failed to create user: {str(e)}")


def verify_supabase_token(token: str):
    """
    Verify a Supabase JWT token
    Returns user data if valid, None if invalid
    """
    if not supabase:
        return None
    
    try:
        user = supabase.auth.get_user(token)
        return user
    except:
        return None
