"""
Authentication.

Primary: Supabase Auth. The frontend signs users in via Supabase and sends the
Supabase access token (ES256, signed by the project's current JWT key). We verify
it against the project's public JWKS — no shared secret needed.

Transitional fallback: the legacy HS256 token issued by our own /token endpoint
is still accepted so nothing breaks during the cutover. Remove once the frontend
is fully on Supabase.

Authorization model: the Supabase user's email is the link to our `User` table,
which holds the app role (admin/auditor/...) for RBAC. A first-time Supabase user
is auto-provisioned a profile (role=auditor). Access is restricted to the
@next-belt.com domain (defense-in-depth alongside the Supabase signup trigger).
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt  # PyJWT

from database import get_db
from models import User
from config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=True)

# Lazy JWKS client (cached) for verifying Supabase ES256 tokens.
_jwk_client: Optional["jwt.PyJWKClient"] = None


def _jwks() -> Optional["jwt.PyJWKClient"]:
    global _jwk_client
    if _jwk_client is None and settings.SUPABASE_URL:
        url = settings.SUPABASE_URL.rstrip("/") + "/auth/v1/.well-known/jwks.json"
        _jwk_client = jwt.PyJWKClient(url)
    return _jwk_client


def _email_from_supabase_token(token: str) -> Optional[str]:
    client = _jwks()
    if not client:
        return None
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=settings.SUPABASE_URL.rstrip("/") + "/auth/v1",
            options={"require": ["exp", "sub"]},
        )
        return payload.get("email")
    except Exception:
        return None


def _email_from_legacy_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = _email_from_supabase_token(token) or _email_from_legacy_token(token)
    if not email:
        raise credentials_exception
    email = email.strip().lower()

    domain = settings.ALLOWED_EMAIL_DOMAIN.lower()
    if not email.endswith("@" + domain):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access is restricted to @{domain} accounts.",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        # First login of a valid @next-belt.com Supabase user → provision a profile.
        user = User(
            email=email,
            full_name=email.split("@")[0].replace(".", " ").title(),
            role="auditor",
            is_active=True,
            hashed_password="supabase",  # passwords are managed by Supabase now
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise credentials_exception

    return user
