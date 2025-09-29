"""Helpers for persisting incoming uploads to temporary files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import tempfile

from fastapi import HTTPException, UploadFile

from app.config import MAX_FILE_SIZE_BYTES, STREAM_CHUNK_SIZE


@dataclass
class StoredUpload:
    """Representation of an uploaded file persisted to disk."""

    path: Path
    filename: str
    size: int

    def cleanup(self) -> None:
        """Remove the persisted file if it still exists."""
        try:
            self.path.unlink(missing_ok=True)
        except TypeError:
            # Python <3.8 compatibility: fallback to manual check
            if self.path.exists():
                self.path.unlink()


def _delete_path(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except TypeError:
        if path.exists():
            path.unlink()


def cleanup_uploads(uploads: Iterable[StoredUpload]) -> None:
    """Remove any temporary files associated with stored uploads."""
    for stored in uploads:
        stored.cleanup()


async def persist_upload(
    upload: UploadFile,
    *,
    max_bytes: int = MAX_FILE_SIZE_BYTES,
    chunk_size: int = STREAM_CHUNK_SIZE,
) -> StoredUpload:
    """Stream an UploadFile to a NamedTemporaryFile while enforcing size limits."""
    original_name = upload.filename or "upload"
    suffix = Path(original_name).suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        temp_path = Path(tmp.name)
        total_bytes = 0
        try:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail={
                            "code": "file_too_large",
                            "message": f"File '{original_name}' exceeds the {max_bytes // (1024 * 1024)} MB limit.",
                        },
                    )
                tmp.write(chunk)
        except Exception:
            tmp.close()
            _delete_path(temp_path)
            raise

    await upload.close()
    return StoredUpload(path=temp_path, filename=original_name, size=total_bytes)


async def persist_uploads(files: Iterable[UploadFile]) -> List[StoredUpload]:
    """Persist multiple uploads, cleaning up all if any single save fails."""
    stored: List[StoredUpload] = []
    try:
        for upload in files:
            stored.append(await persist_upload(upload))
    except Exception:
        cleanup_uploads(stored)
        raise
    return stored
