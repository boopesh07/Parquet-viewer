# backend/parquetformatter_api/tests/test_metrics_route.py
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def mock_save_session_metric(monkeypatch):
    stub = AsyncMock()
    monkeypatch.setattr("app.routes.metrics.save_session_metric", stub)
    return stub


async def test_post_session_metric_success(client: AsyncClient, mock_save_session_metric):
    payload = {
        "session_id": "sess-12345",
        "event_name": "conversion_complete",
        "page_path": "/parquet-to-csv",
        "attributes": {"files": 2},
    }
    response = await client.post("/v1/metrics/session", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_save_session_metric.assert_awaited()


async def test_post_session_metric_requires_session_id(client: AsyncClient):
    payload = {"event_name": "conversion_complete"}
    response = await client.post("/v1/metrics/session", json=payload)
    assert response.status_code == 422
