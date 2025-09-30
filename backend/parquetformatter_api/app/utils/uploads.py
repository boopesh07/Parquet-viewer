"""Helpers for persisting incoming uploads to temporary files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence
import tempfile

from urllib.parse import unquote, urlparse

from fastapi import HTTPException, UploadFile

import httpx

from app.config import (
    ALLOWED_REMOTE_SCHEMES,
    DOWNLOAD_TIMEOUT_SECONDS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_PER_REQUEST,
    STREAM_CHUNK_SIZE,
)


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


def _filename_from_url(url: str, content_disposition: str | None) -> str:
    if content_disposition:
        parts = [fragment.strip() for fragment in content_disposition.split(";")]
        for fragment in parts:
            if fragment.lower().startswith("filename="):
                filename = fragment.split("=", 1)[1].strip('"')
                if filename:
                    return filename
    parsed = urlparse(url)
    candidate = Path(unquote(parsed.path or ""))
    if candidate.name:
        return candidate.name
    return "download"


async def persist_url(
    url: str,
    *,
    max_bytes: int = MAX_FILE_SIZE_BYTES,
    chunk_size: int = STREAM_CHUNK_SIZE,
) -> StoredUpload:
    """Download a remote resource to a temporary file enforcing size limits."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_REMOTE_SCHEMES:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_url_scheme", "message": "Only HTTP(S) URLs are allowed."},
        )

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=DOWNLOAD_TIMEOUT_SECONDS) as client:
            async with client.stream("GET", url) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:  # pragma: no cover - handled below
                    raise HTTPException(
                        status_code=exc.response.status_code,
                        detail={
                            "code": "download_failed",
                            "message": f"Failed to download URL {url}: {exc.response.reason_phrase}",
                        },
                    ) from exc

                filename = _filename_from_url(url, response.headers.get("content-disposition"))
                suffix = Path(filename).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    temp_path = Path(tmp.name)
                    total_bytes = 0
                    try:
                        async for chunk in response.aiter_bytes(chunk_size):
                            total_bytes += len(chunk)
                            if total_bytes > max_bytes:
                                raise HTTPException(
                                    status_code=413,
                                    detail={
                                        "code": "file_too_large",
                                        "message": f"Remote file exceeds the {max_bytes // (1024 * 1024)} MB limit.",
                                    },
                                )
                            tmp.write(chunk)
                    except Exception:
                        tmp.close()
                        _delete_path(temp_path)
                        raise
        return StoredUpload(path=temp_path, filename=filename, size=total_bytes)
    except HTTPException:
        raise
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "download_error", "message": f"Could not fetch URL {url}: {exc}"},
        ) from exc


async def persist_urls(urls: Sequence[str]) -> List[StoredUpload]:
    """Persist a sequence of remote URLs to temporary files."""
    stored: List[StoredUpload] = []
    try:
        for url in urls:
            stored.append(await persist_url(url))
    except Exception:
        cleanup_uploads(stored)
        raise
    return stored


async def persist_sources(
    files: Sequence[UploadFile],
    urls: Sequence[str],
) -> List[StoredUpload]:
    """Persist a mix of uploads and remote URLs, enforcing combined limits."""
    total_count = len(files) + len(urls)
    if total_count == 0:
        raise HTTPException(
            status_code=400,
            detail={"code": "missing_files", "message": "At least one file or URL must be provided."},
        )
    if total_count > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "too_many_files",
                "message": f"A maximum of {MAX_FILES_PER_REQUEST} items are allowed per request.",
            },
        )

    stored: List[StoredUpload] = []
    try:
        if files:
            stored.extend(await persist_uploads(files))
        if urls:
            stored.extend(await persist_urls(urls))
    except Exception:
        cleanup_uploads(stored)
        raise
    return stored
