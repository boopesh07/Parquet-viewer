# backend/parquetformatter_api/tests/test_convert_routes.py
from __future__ import annotations

import json
from io import BytesIO, StringIO

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def sample_files(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("data_convert")

    csv_path = tmpdir.join("sample.csv")
    with open(csv_path, "w") as f:
        f.write("col1,col2\n1,A\n2,B")

    parquet_path = tmpdir.join("sample.parquet")
    df = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, parquet_path)

    ndjson_path = tmpdir.join("sample.ndjson")
    with open(ndjson_path, "w") as f:
        f.write('{"col1": 1, "col2": "A"}\n')
        f.write('{"col1": 2, "col2": "B"}\n')

    return {
        "csv": str(csv_path),
        "parquet": str(parquet_path),
        "ndjson": str(ndjson_path),
    }


async def test_parquet_to_csv(client: AsyncClient, sample_files):
    with open(sample_files["parquet"], "rb") as f:
        files = {"files": ("sample.parquet", f)}
        response = await client.post("/v1/convert/parquet-to-csv", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "sample.csv" in response.headers["content-disposition"]

    parsed = pd.read_csv(StringIO(response.text))
    expected = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})
    pd.testing.assert_frame_equal(parsed, expected)


async def test_csv_to_parquet(client: AsyncClient, sample_files):
    with open(sample_files["csv"], "rb") as f:
        files = {"files": ("sample.csv", f)}
        response = await client.post("/v1/convert/csv-to-parquet", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "sample.parquet" in response.headers["content-disposition"]

    table = pq.read_table(BytesIO(response.content))
    df = table.to_pandas()
    pd.testing.assert_frame_equal(df, pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]}))


async def test_ndjson_to_csv(client: AsyncClient, sample_files):
    with open(sample_files["ndjson"], "rb") as f:
        files = {"files": ("sample.ndjson", f)}
        response = await client.post("/v1/convert/ndjson-to-csv", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "sample.csv" in response.headers["content-disposition"]

    parsed = pd.read_csv(StringIO(response.text))
    expected = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})
    pd.testing.assert_frame_equal(parsed, expected)


async def test_csv_to_ndjson(client: AsyncClient, sample_files):
    with open(sample_files["csv"], "rb") as f:
        files = {"files": ("sample.csv", f)}
        response = await client.post("/v1/convert/csv-to-ndjson", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-ndjson"
    assert "sample.ndjson" in response.headers["content-disposition"]

    lines = [json.loads(line) for line in response.text.strip().split("\n") if line]
    assert lines == [{"col1": 1, "col2": "A"}, {"col1": 2, "col2": "B"}]
