"""Application logging configuration."""
from __future__ import annotations

import logging

from app.config import ENABLE_GCP_LOGGING, GCP_LOG_NAME

_logger_configured = False


def setup_logging() -> None:
    """Configure logging for local or Google Cloud environments."""
    global _logger_configured
    if _logger_configured:
        return

    logging.basicConfig(level=logging.INFO)

    if ENABLE_GCP_LOGGING:
        try:
            import google.cloud.logging

            client = google.cloud.logging.Client()
            client.setup_logging(log_level=logging.INFO)
            logging.getLogger(__name__).info("Google Cloud logging enabled", extra={"logger": GCP_LOG_NAME})
        except Exception as exc:  # pragma: no cover - network/service unavailable
            logging.getLogger(__name__).warning("Failed to initialise Google Cloud logging: %s", exc)
    _logger_configured = True
