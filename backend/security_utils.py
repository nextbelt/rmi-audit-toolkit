"""
Cross-cutting security helpers: filename sanitization, upload validation
(now backend-agnostic via storage.py), rate limiting, and password-reset
tokens.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import tempfile
import time
import uuid
from collections import defaultdict, deque
from typing import Deque, Dict, Iterator, Optional, Tuple

from fastapi import HTTPException, Request, UploadFile, status

import storage
from config import settings
from storage import StoredObject

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Upload safety
# ---------------------------------------------------------------------------

_FILENAME_KEEP_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    """Return a filename safe to join with an upload directory.

    Strips directory components, replaces unsafe characters, and prefixes a
    short random hex so two clients cannot overwrite each other.
    """
    base = os.path.basename(name or "upload.bin")
    base = _FILENAME_KEEP_RE.sub("_", base).strip("._-") or "upload.bin"
    return f"{uuid.uuid4().hex[:12]}_{base}"


def assessment_upload_subdir(assessment_id: int, kind: str) -> str:
    safe_kind = re.sub(r"[^a-z_]+", "", kind.lower()) or "misc"
    return os.path.join("assessments", str(int(assessment_id)), safe_kind).replace("\\", "/")


async def save_upload(
    upload: UploadFile,
    *,
    subdir: str,
    max_bytes: Optional[int] = None,
) -> StoredObject:
    """Validate and persist an UploadFile.

    Raises 415 for bad ext/MIME, 413 for oversize. Returns a StoredObject that
    can be passed to storage.open_stream / get_signed_url / delete_object.
    """
    if max_bytes is None:
        max_bytes = settings.MAX_UPLOAD_SIZE

    original_name = upload.filename or ""
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_EXT:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Extension {ext or '(none)'} is not allowed",
        )
    if upload.content_type and upload.content_type not in settings.ALLOWED_UPLOAD_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"MIME {upload.content_type} is not allowed",
        )

    # Drain the upload into memory while enforcing the size cap. For our 50MB
    # cap this is acceptable; for larger limits switch to a streaming upload to
    # storage.put_object via a generator.
    chunks = bytearray()
    chunk_size = 1024 * 1024
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        chunks.extend(chunk)
        if len(chunks) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Upload exceeds {settings.MAX_UPLOAD_SIZE_MB} MB",
            )

    safe_name = sanitize_filename(original_name)
    return storage.put_object(
        subdir=subdir.replace("\\", "/"),
        filename=safe_name,
        data=bytes(chunks),
        mime=upload.content_type,
    )


def materialize_local(stored: StoredObject) -> Tuple[str, bool]:
    """Return a local file path for the stored object.

    For local backend: returns the existing path (no copy).
    For supabase backend: downloads to a temp file and returns that path; the
    second element of the tuple is True meaning "caller should remove this
    after use".
    """
    if stored.backend == "local":
        return stored.key, False

    ext = os.path.splitext(stored.key)[1] or ".bin"
    fd, tmp = tempfile.mkstemp(suffix=ext, prefix="rmi_dl_")
    with os.fdopen(fd, "wb") as out:
        for chunk in storage.open_stream(stored):
            out.write(chunk)
    return tmp, True


def resolve_local_path(stored_path: str) -> str:
    """Legacy helper: verify a local upload path is still inside UPLOAD_DIR."""
    upload_root = os.path.abspath(settings.UPLOAD_DIR)
    full = os.path.abspath(stored_path)
    if not (full == upload_root or full.startswith(upload_root + os.sep)):
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.isfile(full):
        raise HTTPException(status_code=404, detail="File not found")
    return full


# Back-compat alias for callers that imported the old name
resolve_upload_path = resolve_local_path


# ---------------------------------------------------------------------------
# Login rate limiting (in-process; sufficient for single-instance Railway)
# ---------------------------------------------------------------------------


class _SlidingWindowLimiter:
    """Tracks N attempts per key within a 60 second window."""

    def __init__(self, limit_per_min: int) -> None:
        self.limit = limit_per_min
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        window = self._hits[key]
        while window and now - window[0] > 60.0:
            window.popleft()
        if len(window) >= self.limit:
            retry = int(60.0 - (now - window[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many attempts. Try again in {retry}s.",
                headers={"Retry-After": str(retry)},
            )
        window.append(now)


login_limiter = _SlidingWindowLimiter(settings.LOGIN_RATE_LIMIT_PER_MIN)


def rate_limit_login(request: Request, username: str) -> None:
    """Apply the login rate limit using IP + username as the key."""
    ip = (request.client.host if request.client else "unknown") or "unknown"
    login_limiter.check(f"{ip}|{(username or '').lower()}")


# ---------------------------------------------------------------------------
# Password reset tokens (HMAC-signed, stateless)
# ---------------------------------------------------------------------------


def _reset_secret() -> bytes:
    return ("rmi-pw-reset::" + settings.SECRET_KEY).encode("utf-8")


def issue_password_reset_token(user_id: int) -> str:
    expiry = int(time.time()) + settings.PASSWORD_RESET_TOKEN_TTL_MINUTES * 60
    nonce = secrets.token_urlsafe(8)
    payload = f"{user_id}.{expiry}.{nonce}"
    sig = hmac.new(_reset_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_password_reset_token(token: str) -> int:
    """Return the user_id if valid; raise 400 otherwise."""
    try:
        user_id_s, expiry_s, nonce, sig = token.split(".", 3)
        payload = f"{user_id_s}.{expiry_s}.{nonce}"
        expected = hmac.new(_reset_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        if int(expiry_s) < int(time.time()):
            raise ValueError("expired")
        return int(user_id_s)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")


def hash_reset_token(token: str) -> str:
    """Stable hash of a reset token, for single-use replay tracking.

    Stored in password_reset_used so a leaked token cannot be replayed within
    its TTL. Uses the reset secret so the stored hash isn't a plain digest of
    the (otherwise signed) token.
    """
    return hmac.new(_reset_secret(), token.encode("utf-8"), hashlib.sha256).hexdigest()
