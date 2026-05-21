"""Upload path safety: extension allowlist, size enforcement, sanitization."""
from io import BytesIO

import pytest


class FakeUpload:
    def __init__(self, *, filename, content, content_type=None):
        self.filename = filename
        self._buf = BytesIO(content if isinstance(content, bytes) else content.encode())
        self.content_type = content_type

    async def read(self, n: int = -1) -> bytes:
        return self._buf.read(n) if n != -1 else self._buf.read()


@pytest.mark.asyncio
async def test_save_upload_rejects_bad_extension(tmp_upload_dir):
    from fastapi import HTTPException

    from security_utils import save_upload

    upload = FakeUpload(filename="evil.sh", content=b"#!/bin/sh\necho pwn")
    with pytest.raises(HTTPException) as exc:
        await save_upload(upload, subdir="cmms")
    assert exc.value.status_code == 415


@pytest.mark.asyncio
async def test_save_upload_strips_traversal_in_name(tmp_upload_dir, monkeypatch):
    # Force the storage abstraction to use the local backend
    monkeypatch.setattr("storage.STORAGE_BACKEND", "local")
    from security_utils import save_upload

    upload = FakeUpload(filename="../../etc/passwd.csv", content=b"col1,col2\n1,2\n")
    stored = await save_upload(upload, subdir="cmms")
    assert stored.backend == "local"
    assert "../" not in stored.key
    assert "..\\" not in stored.key
    assert stored.bytes > 0
    # The on-disk basename must end with .csv and not contain traversal
    import os as _os
    name = _os.path.basename(stored.key)
    assert name.endswith(".csv")
    assert ".." not in name


@pytest.mark.asyncio
async def test_save_upload_enforces_size_limit(tmp_upload_dir, monkeypatch):
    from fastapi import HTTPException

    from security_utils import save_upload

    # Tiny limit
    monkeypatch.setattr("config.settings.MAX_UPLOAD_SIZE", 16)
    monkeypatch.setattr("config.settings.MAX_UPLOAD_SIZE_MB", 0)
    upload = FakeUpload(filename="big.csv", content=b"a" * 2048)
    with pytest.raises(HTTPException) as exc:
        await save_upload(upload, subdir="cmms", max_bytes=16)
    assert exc.value.status_code == 413
