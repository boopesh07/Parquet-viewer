"""Polars-backed conversions for NDJSON data."""
from __future__ import annotations

from pathlib import Path
from typing import Generator, List
import tempfile

import json
import polars as pl

from app.utils.streams import make_iterator_from_tempfile
from app.converters.duck import _connect


def ndjson_to_csv_stream(input_path: str | Path) -> Generator[bytes, None, None]:
    """Stream CSV bytes derived from an NDJSON source using Polars."""
    src = Path(input_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        temp_path = Path(tmp.name)
    try:
        rows = _load_ndjson_rows(src)
        frame = pl.from_dicts(rows) if rows else pl.DataFrame()
        frame.write_csv(str(temp_path))
        yield from make_iterator_from_tempfile(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


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
    normalized = text.replace("\\r\\n", "\n").replace("\\n", "\n")

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


def _load_ndjson_rows(path: Path) -> List[dict]:
    """Load all NDJSON rows into Python dictionaries."""
    rows: List[dict] = []
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\\r\\n", "\n").replace("\\n", "\n")
    for line in normalized.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows
