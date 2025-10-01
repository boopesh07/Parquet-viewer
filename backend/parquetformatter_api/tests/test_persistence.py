# backend/parquetformatter_api/tests/test_persistence.py
from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

from app.services import persistence, supabase_client

pytestmark = pytest.mark.asyncio


async def test_save_feedback_persists_to_supabase_and_log(monkeypatch, tmp_path):
    """Ensure feedback is pushed to Supabase and written to the local log."""

    captured: list[dict[str, object]] = []

    supabase_client.get_supabase_client.cache_clear()

    class DummyTable:
        def insert(self, record):  # type: ignore[override]
            captured.append(record)
            return self

        def execute(self):  # type: ignore[override]
            return None

    class DummyClient:
        def table(self, name):  # type: ignore[override]
            assert name == supabase_client.SUPABASE_FEEDBACK_TABLE
            return DummyTable()

    monkeypatch.setattr(supabase_client, "get_supabase_client", DummyClient)

    log_path = tmp_path / "feedback.log"
    monkeypatch.setattr("app.services.persistence.FEEDBACK_FILE_PATH", str(log_path))

    record = {"message": "Thanks", "client_host": "cli"}
    await persistence.save_feedback(record)

    assert captured and captured[0]["message"] == "Thanks"
    stored_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(stored_lines) == 1
    stored_record = json.loads(stored_lines[0])
    assert stored_record["message"] == "Thanks"


async def test_insert_feedback_raises_when_supabase_unconfigured(monkeypatch):
    """Misconfigured Supabase credentials should surface as HTTP errors."""

    def _raise_runtime_error():
        raise RuntimeError("Supabase credentials are not configured")

    supabase_client.get_supabase_client.cache_clear()
    monkeypatch.setattr(supabase_client, "get_supabase_client", _raise_runtime_error)

    with pytest.raises(HTTPException) as excinfo:
        await supabase_client.insert_feedback({"message": "Fail"})

    assert excinfo.value.status_code == 500
    assert excinfo.value.detail["code"] == "feedback_supabase_not_configured"


async def test_insert_session_metric_raises_when_supabase_unconfigured(monkeypatch):
    """Session metrics should also fail if Supabase is unavailable."""

    def _raise_runtime_error():
        raise RuntimeError("Supabase credentials are not configured")

    supabase_client.get_supabase_client.cache_clear()
    monkeypatch.setattr(supabase_client, "get_supabase_client", _raise_runtime_error)

    with pytest.raises(HTTPException) as excinfo:
        await supabase_client.insert_session_metric({"session_id": "abc", "event_name": "test"})

    assert excinfo.value.status_code == 500
    assert excinfo.value.detail["code"] == "metric_supabase_not_configured"
