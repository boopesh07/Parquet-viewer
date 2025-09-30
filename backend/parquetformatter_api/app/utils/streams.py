"""Utilities for building streaming responses."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from app.config import STREAM_CHUNK_SIZE


def iterate_file_in_chunks(
    path: str | Path,
    *,
    chunk_size: int = STREAM_CHUNK_SIZE,
) -> Iterator[bytes]:
    """Yield ``chunk_size`` byte segments from ``path`` until EOF."""
    file_path = Path(path)
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    with file_path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            yield chunk


def make_iterator_from_tempfile(
    path: str | Path,
    *,
    chunk_size: int = STREAM_CHUNK_SIZE,
) -> Iterator[bytes]:
    """Proxy to :func:`iterate_file_in_chunks` for backwards compatibility."""
    yield from iterate_file_in_chunks(path, chunk_size=chunk_size)
