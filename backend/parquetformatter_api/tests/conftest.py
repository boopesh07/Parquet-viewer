# backend/parquetformatter_api/tests/conftest.py
from __future__ import annotations

import os
import sys

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """HTTPX client bound to the FastAPI application for integration tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
