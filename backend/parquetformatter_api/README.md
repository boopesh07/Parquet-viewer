# Parquet Formatter API

FastAPI service for ParquetFormatter.com. It converts between Parquet, CSV, and NDJSON formats, streams large files, and exposes a preview/feedback API.

## Requirements
- Python 3.11
- curl/Postman (optional, for manual testing)

## Local Setup
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install \
  fastapi==0.111.1 \
  "uvicorn[standard]"==0.29.0 \
  duckdb==1.4.0 \
  polars==0.20.31 \
  pyarrow==16.1.0 \
  python-multipart==0.0.9 \
  zipstream-ng==1.9.0 \
  pytest==8.3.3 \
  pytest-asyncio==0.24.0 \
  httpx==0.28.1 \
  pandas==2.2.3
```

## Run the Server
From `backend/parquetformatter_api` with the venv active:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```
API root: `http://localhost:8080`

## Run Tests
```bash
cd backend/parquetformatter_api
source ../.venv/bin/activate
pytest tests
```

## Endpoints
| Method | Path | Description |
| ------ | ---- | ----------- |
| GET    | `/healthz` | Liveness probe, returns `{ "ok": true }`. |
| POST   | `/v1/convert/parquet-to-csv` | Upload up to 5 Parquet files (`files[]`) and stream CSV (multi-file → ZIP). |
| POST   | `/v1/convert/csv-to-parquet` | Upload CSV, stream Parquet (multi-file → ZIP). |
| POST   | `/v1/convert/ndjson-to-csv` | Upload NDJSON/JSONL, stream CSV (multi-file → ZIP). |
| POST   | `/v1/convert/csv-to-ndjson` | Upload CSV, stream NDJSON (multi-file → ZIP). |
| POST   | `/v1/preview` | Upload a single Parquet/CSV/NDJSON file, returns schema and first 50 rows. |
| POST   | `/v1/feedback` | Accepts JSON feedback `{ message, email?, page_path? }`. |

### curl Examples
Replace paths as needed; responses are streamed back to the `--output` path.

```bash
# Parquet → CSV
curl --location 'http://localhost:8080/v1/convert/parquet-to-csv' \
  --form 'files=@"/path/to/sample.parquet";type=application/octet-stream' \
  --output sample.csv

# CSV → Parquet
curl --location 'http://localhost:8080/v1/convert/csv-to-parquet' \
  --form 'files=@"/path/to/sample.csv";type=text/csv' \
  --output sample.parquet

# CSV → NDJSON
curl --location 'http://localhost:8080/v1/convert/csv-to-ndjson' \
  --form 'files=@"/path/to/sample.csv";type=text/csv' \
  --output sample.ndjson

# NDJSON → CSV
curl --location 'http://localhost:8080/v1/convert/ndjson-to-csv' \
  --form 'files=@"/path/to/sample.ndjson";type=application/x-ndjson' \
  --output sample_from_ndjson.csv

# Preview (single file only)
curl --location 'http://localhost:8080/v1/preview' \
  --form 'file=@"/path/to/sample.parquet"' | jq

# Feedback
curl --location 'http://localhost:8080/v1/feedback' \
  --header 'Content-Type: application/json' \
  --data '{"message": "Preview looks great!", "email": "user@example.com"}'
```

### Notes
- Field name must be `files` for the conversion endpoints and `file` for preview.
- Up to 5 files per request, max 500 MB each.
- The service writes temporary files during conversions but deletes them before responding.
