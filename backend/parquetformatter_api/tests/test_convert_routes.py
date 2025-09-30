# backend/parquetformatter_api/tests/test_convert_routes.py
from __future__ import annotations

import json
from io import BytesIO, StringIO
from zipfile import ZipFile

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from httpx import AsyncClient
from pathlib import Path
import httpx
from urllib.parse import urlparse

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

    nested_ndjson_path = tmpdir.join("nested.ndjson")
    with open(nested_ndjson_path, "w") as f:
        f.write('{"meta": {"id": 1}, "values": [1, 2], "status": "ok"}\n')
        f.write('{"meta": {"id": 2}, "status": "pending"}\n')

    return {
        "csv": str(csv_path),
        "parquet": str(parquet_path),
        "ndjson": str(ndjson_path),
        "nested_ndjson": str(nested_ndjson_path),
    }


@pytest.fixture
def mock_remote_download(monkeypatch, sample_files):
    base_urls = {
        "parquet": "https://mock.local/sample.parquet",
        "csv": "https://mock.local/sample.csv",
        "ndjson": "https://mock.local/sample.ndjson",
    }

    file_map = {key: Path(path) for key, path in sample_files.items() if key in base_urls}
    url_to_path = {base_urls[key]: file_map[key] for key in file_map}

    class DummyStream:
        def __init__(self, url: str):
            self._content = url_to_path[url].read_bytes()
            filename = Path(urlparse(url).path).name or "download"
            self.headers = {"content-disposition": f'attachment; filename="{filename}"'}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        async def aiter_bytes(self, chunk_size: int):
            yield self._content

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def stream(self, method: str, url: str):
            if url not in url_to_path:
                raise httpx.RequestError(f"URL {url} not mocked", request=None)
            return DummyStream(url)

    monkeypatch.setattr('app.utils.uploads.httpx.AsyncClient', DummyClient)
    return base_urls


async def test_parquet_to_csv(client: AsyncClient, sample_files):
    with open(sample_files["parquet"], "rb") as f:
        files = [("files", ("sample.parquet", f, "application/octet-stream"))]
        response = await client.post("/v1/convert/parquet-to-csv", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "sample.csv" in response.headers["content-disposition"]

    parsed = pd.read_csv(StringIO(response.text))
    expected = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})
    pd.testing.assert_frame_equal(parsed, expected)


async def test_csv_to_parquet(client: AsyncClient, sample_files):
    with open(sample_files["csv"], "rb") as f:
        files = [("files", ("sample.csv", f, "text/csv"))]
        response = await client.post("/v1/convert/csv-to-parquet", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "sample.parquet" in response.headers["content-disposition"]

    table = pq.read_table(BytesIO(response.content))
    df = table.to_pandas()
    pd.testing.assert_frame_equal(df, pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]}))


async def test_ndjson_to_csv(client: AsyncClient, sample_files):
    with open(sample_files["ndjson"], "rb") as f:
        files = [("files", ("sample.ndjson", f, "application/x-ndjson"))]
        response = await client.post("/v1/convert/ndjson-to-csv", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "sample.csv" in response.headers["content-disposition"]

    parsed = pd.read_csv(StringIO(response.text))
    expected = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})
    pd.testing.assert_frame_equal(parsed, expected)


async def test_ndjson_to_csv_flattens_nested(client: AsyncClient, sample_files):
    with open(sample_files["nested_ndjson"], "rb") as f:
        files = [("files", ("nested.ndjson", f, "application/x-ndjson"))]
        response = await client.post("/v1/convert/ndjson-to-csv", files=files)

    assert response.status_code == 200
    df = pd.read_csv(StringIO(response.text))
    assert list(df.columns) == ["meta.id", "values", "status"]
    assert df.loc[0, "meta.id"] == 1
    assert df.loc[0, "values"] == "[1, 2]"
    assert pd.isna(df.loc[1, "values"]) or df.loc[1, "values"] == ""


async def test_csv_to_ndjson(client: AsyncClient, sample_files):
    with open(sample_files["csv"], "rb") as f:
        files = [("files", ("sample.csv", f, "text/csv"))]
        response = await client.post("/v1/convert/csv-to-ndjson", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-ndjson"
    assert "sample.ndjson" in response.headers["content-disposition"]

    lines = [json.loads(line) for line in response.text.strip().split("\n") if line]
    assert lines == [{"col1": 1, "col2": "A"}, {"col1": 2, "col2": "B"}]

async def test_multiple_csv_files_returns_zip(client: AsyncClient, sample_files):
    with open(sample_files["csv"], "rb") as f1, open(sample_files["csv"], "rb") as f2:
        response = await client.post(
            "/v1/convert/csv-to-ndjson",
            files=[
                ("files", ("alpha.csv", f1, "text/csv")),
                ("files", ("beta.csv", f2, "text/csv")),
            ],
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"].endswith('converted_files.zip"')

    with ZipFile(BytesIO(response.content)) as archive:
        assert sorted(archive.namelist()) == ["alpha.ndjson", "beta.ndjson"]
        lines = [line for line in archive.read("alpha.ndjson").decode().splitlines() if line]

    payload = [json.loads(line) for line in lines]
    assert payload == [{"col1": 1, "col2": "A"}, {"col1": 2, "col2": "B"}]


async def test_parquet_to_csv_via_url(client: AsyncClient, mock_remote_download):
    response = await client.post(
        "/v1/convert/parquet-to-csv",
        data={"urls": mock_remote_download["parquet"]},
    )

    assert response.status_code == 200
    parsed = pd.read_csv(StringIO(response.text))
    expected = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})
    pd.testing.assert_frame_equal(parsed, expected)
