"""DuckDB-powered conversions and previews for Parquet/CSV data."""
from __future__ import annotations

from pathlib import Path
from typing import Generator
import tempfile

import duckdb
import pyarrow as pa
import pyarrow.csv as pacsv

from app.utils.streams import make_iterator_from_tempfile


def _connect(*, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Create a new DuckDB in-memory connection.

    DuckDB does not support read-only in-memory databases, so the flag is
    accepted for API symmetry but ignored.
    """
    return duckdb.connect(database=":memory:")


def _escape(path: Path | str) -> str:
    return str(path).replace("'", "''")


def parquet_to_csv_stream(input_path: str | Path) -> Generator[bytes, None, None]:
    """Stream CSV bytes produced from a Parquet file."""
    path = Path(input_path)
    conn = _connect()
    try:
        reader = conn.execute("SELECT * FROM read_parquet(?)", [str(path)]).fetch_record_batch()
        if reader is None:
            return
        header_written = False
        try:
            while True:
                batch = reader.read_next_batch()
                if batch is None or batch.num_rows == 0:
                    break
                table = pa.Table.from_batches([batch])
                sink = pa.BufferOutputStream()
                options = pacsv.WriteOptions(include_header=not header_written)
                pacsv.write_csv(table, sink, options)
                payload = sink.getvalue().to_pybytes()
                if payload:
                    yield payload
                    header_written = True
        except StopIteration:
            pass
        finally:
            reader.close()
    finally:
        conn.close()


def csv_to_parquet_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    compression: str = "snappy",
) -> None:
    """Convert CSV at ``input_path`` to Parquet ``output_path`` using DuckDB."""
    src = Path(input_path)
    dest = Path(output_path)
    conn = _connect()
    try:
        query = (
            "COPY (SELECT * FROM read_csv_auto('{src}')) "
            "TO '{dest}' (FORMAT 'parquet', COMPRESSION '{compression}')"
        ).format(src=_escape(src), dest=_escape(dest), compression=compression)
        conn.execute(query)
    finally:
        conn.close()


def csv_to_parquet_stream(
    input_path: str | Path,
    *,
    compression: str = "snappy",
) -> Generator[bytes, None, None]:
    """Stream Parquet bytes produced from a CSV source."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
        temp_path = Path(tmp.name)
    try:
        csv_to_parquet_file(input_path, temp_path, compression=compression)
        yield from make_iterator_from_tempfile(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def get_parquet_schema_and_preview(path: str | Path) -> dict:
    """Return schema metadata and the first 50 rows from a Parquet file."""
    src = Path(path)
    conn = _connect(read_only=True)
    try:
        schema_rows = conn.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(src)]).fetchall()
        preview_arrow = conn.execute(
            "SELECT * FROM read_parquet(?) LIMIT 50", [str(src)]
        ).fetch_arrow_table()
    finally:
        conn.close()

    schema = [{"name": name, "dtype": str(dtype)} for name, dtype, *_ in schema_rows]
    rows = preview_arrow.to_pylist()
    return {"schema": schema, "rows": rows}


def get_csv_schema_and_preview(path: str | Path) -> dict:
    """Return schema metadata and the first 50 rows from a CSV file."""
    src = Path(path)
    text = src.read_text(encoding="utf-8")
    normalized = text.replace("\\r\\n", "\n").replace("\\n", "\n")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(normalized.encode("utf-8"))
        normalized_path = Path(tmp.name)

    conn = _connect(read_only=True)
    try:
        schema_rows = conn.execute(
            "DESCRIBE SELECT * FROM read_csv(?, HEADER=TRUE)", [str(normalized_path)]
        ).fetchall()
        preview_arrow = conn.execute(
            "SELECT * FROM read_csv(?, HEADER=TRUE) LIMIT 50", [str(normalized_path)]
        ).fetch_arrow_table()
    finally:
        conn.close()
        normalized_path.unlink(missing_ok=True)

    schema = [{"name": name, "dtype": str(dtype)} for name, dtype, *_ in schema_rows]
    rows = preview_arrow.to_pylist()
    return {"schema": schema, "rows": rows}

