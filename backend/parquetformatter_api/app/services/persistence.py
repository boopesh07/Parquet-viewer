"""Persistence helpers for feedback and session metrics."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException

from app.config import FEEDBACK_FILE_PATH
from app.services.supabase_client import insert_feedback, insert_session_metric

logger = logging.getLogger(__name__)


async def save_feedback(record: Dict[str, Any]) -> None:
    """Persist feedback to Supabase and append to the feedback log."""
    await insert_feedback(record)

    try:
        with open(FEEDBACK_FILE_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
    except Exception as exc:  # pragma: no cover - filesystem issues
        logger.exception("Failed to append feedback to local log")
        raise HTTPException(
            status_code=500,
            detail={"code": "feedback_log_failed", "message": "Could not log feedback."},
        ) from exc


async def save_session_metric(record: Dict[str, Any]) -> None:
    """Persist a session metric to Supabase."""
    payload = {**record}
    if "occurred_at" not in payload:
        payload["occurred_at"] = datetime.utcnow().isoformat()
    await insert_session_metric(payload)
