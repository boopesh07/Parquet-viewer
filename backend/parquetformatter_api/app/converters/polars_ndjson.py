"""Conversions for NDJSON data backed by streaming helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Generator, Iterable, List
import tempfile
import json
import csv

import polars as pl

from app.utils.streams import make_iterator_from_tempfile
from app.converters.duck import _connect

from fastapi import HTTPException


def _flatten_record(data: dict, *, parent_key: str = "", sep: str = ".") -> Dict[str, object]:
    """Flatten nested dictionaries, serialising lists to JSON."""
    items: Dict[str, object] = {}
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(_flatten_record(value, parent_key=new_key, sep=sep))
        elif isinstance(value, list):
            items[new_key] = json.dumps(value, ensure_ascii=False)
        else:
            items[new_key] = value
    return items


def _iter_ndjson_lines(path: Path) -> Iterable[str]:
    """Yield NDJSON lines, expanding literal escape sequences when present."""
    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            if not raw_line:
                continue
            # Remove actual newline characters first.
            trimmed = raw_line.strip("\n")
            if not trimmed:
                continue

            if "\\n" in trimmed or "\\r\\n" in trimmed:
                normalized = trimmed.replace("\\r\\n", "\n").replace("\\n", "\n")
                for fragment in normalized.splitlines():
                    candidate = fragment.strip()
                    if candidate:
                        yield candidate
            else:
                candidate = trimmed.strip()
                if candidate:
                    yield candidate


def _collect_ndjson_rows(path: Path) -> tuple[List[str], Path]:
    """Flatten NDJSON rows and persist them to a temporary buffer."""
    headers: List[str] = []
    seen: set[str] = set()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson", mode="w", encoding="utf-8") as buffer:
        buffer_path = Path(buffer.name)
        for idx, stripped in enumerate(_iter_ndjson_lines(path)):
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise HTTPException(
                    status_code=400,
                    detail={"code": "invalid_ndjson", "message": f"Line {idx + 1} is not valid JSON: {exc}"},
                ) from exc
            if not isinstance(record, dict):
                raise HTTPException(
                    status_code=400,
                    detail={"code": "invalid_ndjson", "message": "Each NDJSON entry must be a JSON object."},
                )
            flattened = _flatten_record(record)
            for key in flattened:
                if key not in seen:
                    headers.append(key)
                    seen.add(key)
            buffer.write(json.dumps(flattened, ensure_ascii=False))
            buffer.write("\n")
    return headers, buffer_path


def ndjson_to_csv_stream(input_path: str | Path) -> Generator[bytes, None, None]:
    """Stream CSV bytes derived from an NDJSON source with flattening."""
    src = Path(input_path)
    headers, buffer_path = _collect_ndjson_rows(src)
    fieldnames = headers or []
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline="", encoding="utf-8") as tmp:
        writer = csv.DictWriter(tmp, fieldnames=fieldnames, extrasaction="ignore")
        if fieldnames:
            writer.writeheader()
        with buffer_path.open("r", encoding="utf-8") as buffered_rows:
            for line in buffered_rows:
                if not line.strip():
                    continue
                flattened = json.loads(line)
                if fieldnames:
                    writer.writerow({key: flattened.get(key, "") for key in fieldnames})
                else:
                    writer.writerow({})
        temp_path = Path(tmp.name)
    try:
        yield from make_iterator_from_tempfile(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)
        buffer_path.unlink(missing_ok=True)


def csv_to_ndjson_stream(input_path: str | Path) -> Generator[bytes, None, None]:
    """Stream NDJSON bytes derived from a CSV source."""
    src = Path(input_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson") as tmp:
        temp_path = Path(tmp.name)
    try:
        df = pl.read_csv(str(src))
        df.write_ndjson(str(temp_path))
        yield from make_iterator_from_tempfile(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def get_ndjson_schema_and_preview(path: str | Path) -> dict:
    """Return schema metadata and a 50-row preview from an NDJSON file."""
    src = Path(path)
    text = src.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\\r\\n", "\n").replace("\\n", "\n")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson") as tmp:
        tmp.write(normalized.encode("utf-8"))
        normalized_path = Path(tmp.name)

    conn = _connect()
    try:
        schema_rows = conn.execute(
            "DESCRIBE SELECT * FROM read_json_auto(?, format='newline_delimited')",
            [str(normalized_path)],
        ).fetchall()
        preview_arrow = conn.execute(
            "SELECT * FROM read_json_auto(?, format='newline_delimited') LIMIT 50",
            [str(normalized_path)],
        ).fetch_arrow_table()
    finally:
        conn.close()
        normalized_path.unlink(missing_ok=True)

    schema = [{"name": name, "dtype": str(dtype)} for name, dtype, *_ in schema_rows]
    rows = preview_arrow.to_pylist()
    return {"schema": schema, "rows": rows}
