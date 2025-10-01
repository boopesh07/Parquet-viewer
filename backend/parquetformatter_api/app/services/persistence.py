"""Persistence helpers for feedback and session metrics."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException

from app.services.supabase_client import insert_feedback, insert_session_metric

logger = logging.getLogger(__name__)


async def save_feedback(record: Dict[str, Any]) -> None:
    """Persist feedback to Supabase and append to the feedback log."""
    await insert_feedback(record)

    logger.debug("Feedback saved to Supabase: %s", json.dumps(record, default=str))


async def save_session_metric(record: Dict[str, Any]) -> None:
    """Persist a session metric to Supabase."""
    payload = {**record}
    if "occurred_at" not in payload:
        payload["occurred_at"] = datetime.utcnow().isoformat()
    await insert_session_metric(payload)
