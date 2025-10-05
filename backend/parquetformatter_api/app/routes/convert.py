"""Conversion endpoints for ParquetFormatter API."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, List, Sequence

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import zipstream

from app.converters.duck import csv_to_parquet_stream, parquet_to_csv_stream
from app.converters.polars_ndjson import csv_to_ndjson_stream, ndjson_to_csv_stream
from app.utils.uploads import StoredUpload, cleanup_uploads, persist_sources

router = APIRouter()

StreamFunc = Callable[[str | Path], Iterable[bytes]]


@dataclass(slots=True)
class ConversionSpec:
    """Description of a conversion pipeline."""

    stream_fn: StreamFunc
    media_type: str
    output_suffix: str


def _conversion_error(filename: str, exc: Exception) -> HTTPException:
    """Wrap low-level conversion failures with a client-facing HTTP error."""
    message = f"Failed to convert {filename}: {exc}"
    return HTTPException(status_code=400, detail={"code": "conversion_failed", "message": message})


def _prefetch_stream(stored: StoredUpload, spec: ConversionSpec) -> Iterator[bytes]:
    """Prime a stream so conversion errors surface before streaming begins."""
    try:
        raw_iterable = spec.stream_fn(stored.path)
    except HTTPException:
        raise
    except Exception as exc:
        raise _conversion_error(stored.filename, exc) from exc
    iterator = iter(raw_iterable)

    try:
        first_chunk = next(iterator)
    except StopIteration:
        return iter(())
    except HTTPException:
        raise
    except Exception as exc:
        raise _conversion_error(stored.filename, exc) from exc

    def generator() -> Iterator[bytes]:
        try:
            yield first_chunk
            yield from iterator
        except HTTPException:
            raise
        except Exception as exc:
            raise _conversion_error(stored.filename, exc) from exc

    return generator()


def _build_single_file_response(stored: StoredUpload, spec: ConversionSpec) -> StreamingResponse:
    """Stream a converted payload for a single upload."""
    filename = Path(stored.filename).with_suffix(spec.output_suffix).name

    try:
        stream = _prefetch_stream(stored, spec)
    except Exception:
        cleanup_uploads([stored])
        raise

    def iterator() -> Iterator[bytes]:
        try:
            yield from stream
        finally:
            cleanup_uploads([stored])

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(iterator(), media_type=spec.media_type, headers=headers)


def _build_zip_response(stored_uploads: List[StoredUpload], spec: ConversionSpec) -> StreamingResponse:
    """Bundle multiple converted results into a streaming ZIP archive."""
    archive = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)

    prepared_streams: List[tuple[StoredUpload, Iterator[bytes]]] = []
    try:
        for stored in stored_uploads:
            prepared_streams.append((stored, _prefetch_stream(stored, spec)))
    except Exception:
        cleanup_uploads(stored_uploads)
        raise

    for stored, stream in prepared_streams:
        member_name = Path(stored.filename).with_suffix(spec.output_suffix).name
        archive.add(stream, member_name)

    def iterator() -> Iterator[bytes]:
        try:
            yield from archive
        finally:
            cleanup_uploads(stored_uploads)

    headers = {"Content-Disposition": 'attachment; filename="converted_files.zip"'}
    return StreamingResponse(iterator(), media_type="application/zip", headers=headers)


async def _convert_payload(
    files: Sequence[UploadFile],
    urls: Sequence[str],
    spec: ConversionSpec,
) -> StreamingResponse:
    stored_uploads = await persist_sources(list(files), list(urls))
    if len(stored_uploads) == 1:
        return _build_single_file_response(stored_uploads[0], spec)
    return _build_zip_response(stored_uploads, spec)


def _normalize_urls(urls: List[str] | str) -> List[str]:
    if not urls:
        return []
    candidates = [urls] if isinstance(urls, str) else urls
    normalized = [candidate.strip() for candidate in candidates if candidate and candidate.strip()]
    if not normalized:
        return []
    return normalized


@router.post("/convert/parquet-to-csv")
async def parquet_to_csv(
    files: List[UploadFile] = File([]),
    urls: List[str] = Form([]),
):
    """Convert uploaded Parquet files to CSV."""
    spec = ConversionSpec(stream_fn=parquet_to_csv_stream, media_type="text/csv", output_suffix=".csv")
    return await _convert_payload(files, _normalize_urls(urls), spec)


@router.post("/convert/csv-to-parquet")
async def csv_to_parquet(
    files: List[UploadFile] = File([]),
    urls: List[str] = Form([]),
):
    """Convert uploaded CSV files to Parquet."""
    spec = ConversionSpec(
        stream_fn=csv_to_parquet_stream,
        media_type="application/octet-stream",
        output_suffix=".parquet",
    )
    return await _convert_payload(files, _normalize_urls(urls), spec)


@router.post("/convert/ndjson-to-csv")
async def ndjson_to_csv(
    files: List[UploadFile] = File([]),
    urls: List[str] = Form([]),
):
    """Convert uploaded NDJSON files to CSV."""
    spec = ConversionSpec(stream_fn=ndjson_to_csv_stream, media_type="text/csv", output_suffix=".csv")
    return await _convert_payload(files, _normalize_urls(urls), spec)


@router.post("/convert/csv-to-ndjson")
async def csv_to_ndjson(
    files: List[UploadFile] = File([]),
    urls: List[str] = Form([]),
):
    """Convert uploaded CSV files to NDJSON."""
    spec = ConversionSpec(
        stream_fn=csv_to_ndjson_stream,
        media_type="application/x-ndjson",
        output_suffix=".ndjson",
    )
    return await _convert_payload(files, _normalize_urls(urls), spec)
