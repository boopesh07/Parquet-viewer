# backend/parquetformatter_api/app/config.py

"""
Application wide configuration settings.
"""

MAX_FILES_PER_REQUEST: int = 5
MAX_FILE_SIZE_MB: int = 500
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
STREAM_CHUNK_SIZE: int = 65536
FEEDBACK_FILE_PATH: str = "feedback.log"
