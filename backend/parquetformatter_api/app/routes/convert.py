"""Conversion endpoints implementing streaming responses."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable, List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
import zipstream

from app.config import MAX_FILES_PER_REQUEST
from app.converters.duck import csv_to_parquet_stream, parquet_to_csv_stream
from app.converters.polars_ndjson import csv_to_ndjson_stream, ndjson_to_csv_stream
from app.utils.streams import iterator_with_cleanup
from app.utils.uploads import StoredUpload, cleanup_uploads, persist_uploads

router = APIRouter()


def _validate_file_count(files: List[UploadFile]) -> None:
    if not files:
        raise HTTPException(
            status_code=400,
            detail={"code": "no_files", "message": "At least one file must be provided."},
        )
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "too_many_files",
                "message": f"Up to {MAX_FILES_PER_REQUEST} files can be processed per request.",
            },
        )


def _derive_output_name(original: str, extension: str) -> str:
    stem = Path(original).stem or "converted"
    return f"{stem}{extension}"


def _single_file_response(
    stored: StoredUpload,
    *,
    generator_factory: Callable[[StoredUpload], Iterable[bytes]],
    extension: str,
    media_type: str,
) -> StreamingResponse:
    output_name = _derive_output_name(stored.filename, extension)
    iterator = iterator_with_cleanup(generator_factory(stored), stored.cleanup)
    headers = {"Content-Disposition": f'attachment; filename="{output_name}"'}
    background = BackgroundTask(stored.cleanup)
    return StreamingResponse(iterator, media_type=media_type, headers=headers, background=background)


def _zip_response(
    stored_files: List[StoredUpload],
    *,
    generator_factory: Callable[[StoredUpload], Iterable[bytes]],
    extension: str,
) -> StreamingResponse:
    zip_stream = zipstream.ZipStream(compress_type=zipstream.ZIP_DEFLATED)
    for stored in stored_files:
        arcname = _derive_output_name(stored.filename, extension)
        iterator = iterator_with_cleanup(generator_factory(stored), stored.cleanup)
        zip_stream.add(iterator, arcname)

    headers = {"Content-Disposition": 'attachment; filename="converted_files.zip"'}
    background = BackgroundTask(lambda: cleanup_uploads(stored_files))
    return StreamingResponse(zip_stream, media_type="application/zip", headers=headers, background=background)


async def _prepare_uploads(files: List[UploadFile]) -> List[StoredUpload]:
    _validate_file_count(files)
    return await persist_uploads(files)


@router.post("/convert/parquet-to-csv")
async def parquet_to_csv_route(files: List[UploadFile] = File(...)):
    stored_files = await _prepare_uploads(files)

    def generator(stored: StoredUpload):
        return parquet_to_csv_stream(stored.path)

    if len(stored_files) == 1:
        return _single_file_response(
            stored_files[0],
            generator_factory=generator,
            extension=".csv",
            media_type="text/csv",
        )
    return _zip_response(stored_files, generator_factory=generator, extension=".csv")


@router.post("/convert/csv-to-parquet")
async def csv_to_parquet_route(files: List[UploadFile] = File(...)):
    stored_files = await _prepare_uploads(files)

    def generator(stored: StoredUpload):
        return csv_to_parquet_stream(stored.path)

    if len(stored_files) == 1:
        return _single_file_response(
            stored_files[0],
            generator_factory=generator,
            extension=".parquet",
            media_type="application/octet-stream",
        )
    return _zip_response(stored_files, generator_factory=generator, extension=".parquet")


@router.post("/convert/ndjson-to-csv")
async def ndjson_to_csv_route(files: List[UploadFile] = File(...)):
    stored_files = await _prepare_uploads(files)

    def generator(stored: StoredUpload):
        return ndjson_to_csv_stream(stored.path)

    if len(stored_files) == 1:
        return _single_file_response(
            stored_files[0],
            generator_factory=generator,
            extension=".csv",
            media_type="text/csv",
        )
    return _zip_response(stored_files, generator_factory=generator, extension=".csv")


@router.post("/convert/csv-to-ndjson")
async def csv_to_ndjson_route(files: List[UploadFile] = File(...)):
    stored_files = await _prepare_uploads(files)

    def generator(stored: StoredUpload):
        return csv_to_ndjson_stream(stored.path)

    if len(stored_files) == 1:
        return _single_file_response(
            stored_files[0],
            generator_factory=generator,
            extension=".ndjson",
            media_type="application/x-ndjson",
        )
    return _zip_response(stored_files, generator_factory=generator, extension=".ndjson")
