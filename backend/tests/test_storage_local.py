"""Local-backend smoke tests for the storage abstraction."""
from __future__ import annotations


def test_put_and_stream_local(tmp_upload_dir, monkeypatch):
    monkeypatch.setattr("storage.STORAGE_BACKEND", "local")
    import storage

    stored = storage.put_object(subdir="t", filename="abc.csv", data=b"hello,world\n", mime="text/csv")
    assert stored.backend == "local"
    chunks = b"".join(storage.open_stream(stored))
    assert chunks == b"hello,world\n"

    # Serialize / parse round-trip
    raw = stored.serialize()
    parsed = storage.StoredObject.parse(raw)
    assert parsed.backend == "local"
    assert parsed.key == stored.key


def test_put_and_parse_supabase_uri(tmp_upload_dir, monkeypatch):
    import storage

    raw = "supabase://assessments/12/cmms/abc.csv"
    parsed = storage.StoredObject.parse(raw)
    assert parsed.backend == "supabase"
    assert parsed.key == "assessments/12/cmms/abc.csv"
    assert parsed.serialize() == raw


def test_signed_url_local_returns_none(tmp_upload_dir, monkeypatch):
    monkeypatch.setattr("storage.STORAGE_BACKEND", "local")
    import storage

    stored = storage.put_object(subdir="t", filename="abc.csv", data=b"x", mime="text/csv")
    # Local backend has no signed-URL concept; callers must stream through the
    # authenticated endpoint instead.
    assert storage.get_signed_url(stored) is None
