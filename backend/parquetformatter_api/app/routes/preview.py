"""Data preview endpoint implementations."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.converters.duck import get_csv_schema_and_preview, get_parquet_schema_and_preview
from app.converters.polars_ndjson import get_ndjson_schema_and_preview
from app.utils.uploads import persist_upload

router = APIRouter()


@router.post("/preview")
async def get_preview(file: UploadFile = File(...)):
    stored = await persist_upload(file)
    suffix = Path(stored.filename).suffix.lower()

    try:
        if suffix == ".parquet":
            return get_parquet_schema_and_preview(stored.path)
        if suffix == ".csv":
            return get_csv_schema_and_preview(stored.path)
        if suffix in {".ndjson", ".jsonl"}:
            return get_ndjson_schema_and_preview(stored.path)
        raise HTTPException(
            status_code=400,
            detail={"code": "unsupported_preview", "message": "Unsupported file type for preview."},
        )
    except HTTPException:
        raise
    except Exception as exc:  # DuckDB/Polars parsing errors
        raise HTTPException(
            status_code=400,
            detail={"code": "preview_failed", "message": f"Failed to preview file: {exc}"},
        ) from exc
    finally:
        stored.cleanup()
