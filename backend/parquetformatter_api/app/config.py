# backend/parquetformatter_api/app/config.py

"""Application wide configuration settings."""

import os

MAX_FILES_PER_REQUEST: int = 5
MAX_FILE_SIZE_MB: int = 500
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
STREAM_CHUNK_SIZE: int = 65536
FEEDBACK_FILE_PATH: str = "feedback.log"

# Remote ingestion settings
ALLOWED_REMOTE_SCHEMES: set[str] = {"http", "https"}
DOWNLOAD_TIMEOUT_SECONDS: float = 30.0

# Supabase persistence settings (expected to be provided via environment)

SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_FEEDBACK_TABLE: str = os.getenv("SUPABASE_FEEDBACK_TABLE", "feedback")
SUPABASE_SESSION_TABLE: str = os.getenv("SUPABASE_SESSION_TABLE", "session_metrics")

# Observability
ENABLE_GCP_LOGGING: bool = os.getenv("ENABLE_GCP_LOGGING", "false").lower() in {"1", "true", "yes"}
GCP_LOG_NAME: str = os.getenv("GCP_LOG_NAME", "parquetformatter-backend")
