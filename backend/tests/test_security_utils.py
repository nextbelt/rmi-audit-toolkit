"""Filename sanitization, upload validation, password reset tokens."""
from __future__ import annotations

import os
import time

import pytest

from security_utils import (
    issue_password_reset_token,
    sanitize_filename,
    verify_password_reset_token,
)


class TestSanitizeFilename:
    def test_strips_directory_components(self):
        out = sanitize_filename("../../etc/passwd")
        assert ".." not in out
        assert "/" not in out
        assert "\\" not in out

    def test_replaces_special_chars(self):
        out = sanitize_filename("evil$file;name?.csv")
        # Special chars collapsed to underscores
        assert "$" not in out
        assert ";" not in out
        assert "?" not in out
        assert out.endswith(".csv")

    def test_prepends_uuid_prefix(self):
        out = sanitize_filename("report.pdf")
        assert "_report.pdf" in out
        # 12-char hex prefix
        prefix = out.split("_", 1)[0]
        assert len(prefix) == 12
        int(prefix, 16)  # hex parseable

    def test_handles_empty_input(self):
        out = sanitize_filename("")
        assert out.endswith("upload.bin")

    def test_two_calls_produce_different_names(self):
        a = sanitize_filename("x.pdf")
        b = sanitize_filename("x.pdf")
        assert a != b


class TestPasswordResetTokens:
    def test_round_trip(self):
        token = issue_password_reset_token(42)
        assert verify_password_reset_token(token) == 42

    def test_tampered_signature_rejected(self):
        from fastapi import HTTPException

        token = issue_password_reset_token(42)
        bad = token[:-1] + ("0" if token[-1] != "0" else "1")
        with pytest.raises(HTTPException) as exc:
            verify_password_reset_token(bad)
        assert exc.value.status_code == 400

    def test_expired_token_rejected(self, monkeypatch):
        from fastapi import HTTPException

        token = issue_password_reset_token(42)
        # Move time forward 100 minutes — beyond the default 30m TTL
        future = time.time() + 100 * 60
        monkeypatch.setattr("security_utils.time.time", lambda: future)
        with pytest.raises(HTTPException) as exc:
            verify_password_reset_token(token)
        assert exc.value.status_code == 400

    def test_garbage_token_rejected(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            verify_password_reset_token("not-a-token")
        with pytest.raises(HTTPException):
            verify_password_reset_token("a.b.c.d")
