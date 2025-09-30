"""Supabase client helpers for persistence operations."""
from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any, Dict

from fastapi import HTTPException

from app.config import (
    SUPABASE_FEEDBACK_TABLE,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_SESSION_TABLE,
    SUPABASE_URL,
)

try:
    from supabase import Client, create_client  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled lazily
    Client = None  # type: ignore[assignment]
    create_client = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _ensure_credentials() -> tuple[str, str]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase credentials are not configured")
    return SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Initialise and cache the Supabase client."""
    if create_client is None:
        raise RuntimeError("supabase package is required. Install dependencies before running the API.")
    url, key = _ensure_credentials()
    logger.debug("Initialising Supabase client for %s", url)
    return create_client(url, key)


async def insert_feedback(record: Dict[str, Any]) -> None:
    """Insert a feedback record into Supabase."""
    client = get_supabase_client()

    def _execute() -> None:
        client.table(SUPABASE_FEEDBACK_TABLE).insert(record).execute()

    try:
        await asyncio.to_thread(_execute)
    except Exception as exc:  # pragma: no cover - network/client errors
        logger.exception("Failed to persist feedback to Supabase")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "feedback_persist_failed",
                "message": "Unable to persist feedback at this time.",
            },
        ) from exc


async def insert_session_metric(record: Dict[str, Any]) -> None:
    """Insert a session metric record into Supabase."""
    client = get_supabase_client()

    def _execute() -> None:
        client.table(SUPABASE_SESSION_TABLE).insert(record).execute()

    try:
        await asyncio.to_thread(_execute)
    except Exception as exc:  # pragma: no cover - network/client errors
        logger.exception("Failed to persist session metric to Supabase")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "metric_persist_failed",
                "message": "Unable to persist session metric at this time.",
            },
        ) from exc
