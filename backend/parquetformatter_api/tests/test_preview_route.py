# backend/parquetformatter_api/tests/test_preview_route.py
import pytest
from httpx import AsyncClient
import httpx
from pathlib import Path
from urllib.parse import urlparse
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Fixture to create sample files for testing
@pytest.fixture(scope="module")
def sample_files(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("data")
    
    # Create CSV
    csv_path = tmpdir.join("sample.csv")
    with open(csv_path, "w") as f:
        f.write("a,b,c\\n1,2,3\\n4,5,6")

    # Create NDJSON
    ndjson_path = tmpdir.join("sample.ndjson")
    with open(ndjson_path, "w") as f:
        f.write('{"a": 1, "b": "foo"}\\n')
        f.write('{"a": 2, "b": "bar"}\\n')
        
    # Create Parquet
    parquet_path = tmpdir.join("sample.parquet")
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['A', 'B', 'C']})
    table = pa.Table.from_pandas(df)
    pq.write_table(table, parquet_path)

    # Create unsupported file
    unsupported_path = tmpdir.join("sample.txt")
    with open(unsupported_path, "w") as f:
        f.write("this is a text file")

    return {
        "csv": str(csv_path),
        "ndjson": str(ndjson_path),
        "parquet": str(parquet_path),
        "unsupported": str(unsupported_path),
    }

@pytest.fixture
def mock_remote_download(monkeypatch, sample_files):
    base_urls = {
        "parquet": "https://mock.local/sample.parquet",
        "ndjson": "https://mock.local/sample.ndjson",
    }

    url_to_path = {base_urls[key]: Path(sample_files[key]) for key in base_urls}

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

async def test_preview_parquet(client: AsyncClient, sample_files):
    with open(sample_files["parquet"], "rb") as f:
        files = {"file": ("sample.parquet", f, "application/octet-stream")}
        response = await client.post("/v1/preview", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "schema" in data
    assert "rows" in data
    assert len(data["rows"]) == 3
    assert data["schema"] == [
        {"name": "col1", "dtype": "BIGINT"},
        {"name": "col2", "dtype": "VARCHAR"},
    ]

async def test_preview_csv(client: AsyncClient, sample_files):
    with open(sample_files["csv"], "rb") as f:
        files = {"file": ("sample.csv", f, "text/csv")}
        response = await client.post("/v1/preview", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "schema" in data
    assert "rows" in data
    assert len(data["rows"]) == 2
    assert data["schema"] == [
        {"name": "a", "dtype": "BIGINT"},
        {"name": "b", "dtype": "BIGINT"},
        {"name": "c", "dtype": "BIGINT"},
    ]

async def test_preview_ndjson(client: AsyncClient, sample_files):
    with open(sample_files["ndjson"], "rb") as f:
        files = {"file": ("sample.ndjson", f, "application/x-ndjson")}
        response = await client.post("/v1/preview", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "schema" in data
    assert "rows" in data
    assert len(data["rows"]) == 2
    # Polars infers types
    assert data["schema"] == [
        {"name": "a", "dtype": "BIGINT"},
        {"name": "b", "dtype": "VARCHAR"},
    ]
    assert data["rows"][0] == {"a": 1, "b": "foo"}

async def test_preview_via_url(client: AsyncClient, mock_remote_download):
    response = await client.post(
        "/v1/preview",
        data={"url": mock_remote_download["parquet"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert any(column["name"] == "col1" for column in data["schema"])

async def test_preview_unsupported_file(client: AsyncClient, sample_files):
    with open(sample_files["unsupported"], "rb") as f:
        files = {"file": ("sample.txt", f, "text/plain")}
        response = await client.post("/v1/preview", files=files)
    
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "unsupported_preview"
    assert "Unsupported file type" in detail["message"]


async def test_preview_requires_input(client: AsyncClient):
    response = await client.post("/v1/preview")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "missing_file"
