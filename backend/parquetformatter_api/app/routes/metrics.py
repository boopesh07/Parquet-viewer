"""Metrics collection endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.persistence import save_session_metric

router = APIRouter()


class SessionMetricPayload(BaseModel):
    session_id: str = Field(..., min_length=5, max_length=128)
    event_name: str = Field(..., min_length=1, max_length=128)
    page_path: str | None = None
    user_agent: str | None = None
    attributes: Dict[str, Any] | None = None
    occurred_at: datetime | None = None


@router.post("/metrics/session")
async def post_session_metric(payload: SessionMetricPayload, request: Request) -> dict[str, str]:
    """Persist session-level analytics events for deeper analysis."""
    metric = {
        "session_id": payload.session_id,
        "event_name": payload.event_name,
        "page_path": payload.page_path,
        "user_agent": payload.user_agent or request.headers.get("user-agent"),
        "attributes": payload.attributes or {},
        "occurred_at": (payload.occurred_at or datetime.utcnow()).isoformat(),
        "client_host": request.client.host if request.client else "unknown",
    }

    await save_session_metric(metric)
    return {"status": "ok"}
