"""Streaming helpers for conversion responses."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Callable, Generator, Iterable, Iterator, Optional

from app.config import STREAM_CHUNK_SIZE


def read_from_binaryio(
    handle, *, chunk_size: int = STREAM_CHUNK_SIZE
) -> Iterator[bytes]:
    """Yield chunks from a binary file-like object until exhausted."""
    while True:
        chunk = handle.read(chunk_size)
        if not chunk:
            break
        yield chunk


def make_iterator_from_tempfile(
    file_path: str | Path,
    *,
    chunk_size: int = STREAM_CHUNK_SIZE,
) -> Iterator[bytes]:
    """Yield bytes from a temporary file path in chunks."""
    path = Path(file_path)
    with path.open("rb") as handle:
        yield from read_from_binaryio(handle, chunk_size=chunk_size)


def make_iterator_from_bytesio(
    buffer: BytesIO,
    *,
    chunk_size: int = STREAM_CHUNK_SIZE,
) -> Iterator[bytes]:
    """Yield bytes from an in-memory BytesIO buffer in chunks."""
    buffer.seek(0)
    yield from read_from_binaryio(buffer, chunk_size=chunk_size)


def iterator_with_cleanup(
    iterator: Iterable[bytes],
    cleanup: Callable[[], None],
) -> Iterator[bytes]:
    """Wrap an iterator to guarantee cleanup once iteration completes."""
    try:
        for chunk in iterator:
            yield chunk
    finally:
        cleanup()
