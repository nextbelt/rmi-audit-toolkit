"""
Storage abstraction.

Two backends:
- ``local``     — write to ``settings.UPLOAD_DIR``. Default.
- ``supabase``  — write to a Supabase Storage bucket via the REST API.

Configured via ``STORAGE_BACKEND`` (``local`` | ``supabase``). When
``supabase`` is selected, ``SUPABASE_URL`` and ``SUPABASE_SERVICE_KEY`` must
also be set, and a bucket name is read from ``SUPABASE_BUCKET`` (default
``evidence``). The bucket is expected to be PRIVATE; downloads go through
short-lived signed URLs.

The adapter intentionally has a tiny surface so it is easy to swap to R2 / S3
later: ``put_object(key, data, mime)``, ``get_signed_url(key, ttl)``,
``open_stream(key)``, ``delete(key)``.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterator, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "evidence")
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local").lower()


@dataclass
class StoredObject:
    """A pointer to a stored object. Persisted as the file_path column."""

    backend: str  # "local" | "supabase"
    key: str  # for local: absolute path; for supabase: bucket-relative key
    bytes: int
    mime: Optional[str] = None

    def serialize(self) -> str:
        # Keep backwards-compatible: a plain absolute path means local backend.
        # Otherwise prefix with the backend name.
        if self.backend == "local":
            return self.key
        return f"{self.backend}://{self.key}"

    @classmethod
    def parse(cls, raw: str) -> "StoredObject":
        if raw.startswith("supabase://"):
            return cls(backend="supabase", key=raw[len("supabase://"):], bytes=0)
        return cls(backend="local", key=raw, bytes=0)


# ---------------------------------------------------------------------------
# Local backend
# ---------------------------------------------------------------------------


def _local_put(subdir: str, filename: str, data: bytes, mime: Optional[str]) -> StoredObject:
    target_dir = os.path.join(os.path.abspath(settings.UPLOAD_DIR), subdir)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, filename)
    with open(path, "wb") as out:
        out.write(data)
    return StoredObject(backend="local", key=path, bytes=len(data), mime=mime)


def _local_stream(key: str) -> Iterator[bytes]:
    with open(key, "rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            yield chunk


def _local_delete(key: str) -> None:
    try:
        os.remove(key)
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Supabase Storage backend
# ---------------------------------------------------------------------------


def _supa_client() -> tuple[str, dict[str, str]]:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "STORAGE_BACKEND=supabase requires SUPABASE_URL and SUPABASE_SERVICE_KEY"
        )
    base = settings.SUPABASE_URL.rstrip("/")
    headers = {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
    }
    return base, headers


def _supa_put(subdir: str, filename: str, data: bytes, mime: Optional[str]) -> StoredObject:
    base, headers = _supa_client()
    key = f"{subdir.strip('/')}/{filename}"
    url = f"{base}/storage/v1/object/{SUPABASE_BUCKET}/{key}"
    h = {**headers, "x-upsert": "true"}
    if mime:
        h["Content-Type"] = mime
    r = httpx.post(url, content=data, headers=h, timeout=60.0)
    r.raise_for_status()
    return StoredObject(backend="supabase", key=key, bytes=len(data), mime=mime)


def _supa_signed_url(key: str, ttl_seconds: int) -> str:
    base, headers = _supa_client()
    url = f"{base}/storage/v1/object/sign/{SUPABASE_BUCKET}/{key}"
    r = httpx.post(url, json={"expiresIn": ttl_seconds}, headers=headers, timeout=15.0)
    r.raise_for_status()
    signed = r.json().get("signedURL") or r.json().get("signedUrl") or ""
    # Supabase returns a relative URL; resolve against base
    if signed.startswith("/"):
        signed = base + signed
    return signed


def _supa_stream(key: str) -> Iterator[bytes]:
    base, headers = _supa_client()
    url = f"{base}/storage/v1/object/{SUPABASE_BUCKET}/{key}"
    with httpx.stream("GET", url, headers=headers, timeout=60.0) as r:
        r.raise_for_status()
        for chunk in r.iter_bytes(chunk_size=1024 * 1024):
            yield chunk


def _supa_delete(key: str) -> None:
    base, headers = _supa_client()
    url = f"{base}/storage/v1/object/{SUPABASE_BUCKET}/{key}"
    httpx.delete(url, headers=headers, timeout=15.0).raise_for_status()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def put_object(*, subdir: str, filename: str, data: bytes, mime: Optional[str] = None) -> StoredObject:
    if STORAGE_BACKEND == "supabase":
        return _supa_put(subdir, filename, data, mime)
    return _local_put(subdir, filename, data, mime)


def open_stream(stored: StoredObject) -> Iterator[bytes]:
    if stored.backend == "supabase":
        yield from _supa_stream(stored.key)
    else:
        yield from _local_stream(stored.key)


def get_signed_url(stored: StoredObject, ttl_seconds: int = 300) -> Optional[str]:
    """Return a time-limited URL the browser can hit directly.

    Local backend has no signed-URL concept — return None so callers fall back
    to streaming through the authenticated route.
    """
    if stored.backend == "supabase":
        return _supa_signed_url(stored.key, ttl_seconds)
    return None


def delete_object(stored: StoredObject) -> None:
    if stored.backend == "supabase":
        _supa_delete(stored.key)
    else:
        _local_delete(stored.key)


def backend_name() -> str:
    return STORAGE_BACKEND
