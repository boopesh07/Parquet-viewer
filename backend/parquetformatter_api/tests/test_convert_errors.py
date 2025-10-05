"""Tests covering conversion error handling for streaming responses."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import convert
from app.utils.uploads import StoredUpload


def test_parquet_conversion_error_surfaces_message(monkeypatch, tmp_path):
    """Streaming conversion failures should produce a 400 with the root cause."""

    stored_path = Path(tmp_path) / "input.parquet"
    stored_path.write_bytes(b"parquet-bytes")
    stored = StoredUpload(path=stored_path, filename="input.parquet", size=stored_path.stat().st_size)

    async def fake_persist_sources(files, urls):
        return [stored]

    def failing_stream(_):
        raise ValueError("duckdb: don't know what type: DECIMAL(42, 2)")

    monkeypatch.setattr(convert, "persist_sources", fake_persist_sources)
    monkeypatch.setattr(convert, "parquet_to_csv_stream", failing_stream)

    with TestClient(app) as client:
        response = client.post(
            "/v1/convert/parquet-to-csv",
            files={"files": ("dummy.parquet", b"contents", "application/octet-stream")},
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "conversion_failed"
    assert "duckdb: don't know what type" in detail["message"]
    assert "input.parquet" in detail["message"]
    assert not stored_path.exists(), "temporary upload should be cleaned up after failure"
