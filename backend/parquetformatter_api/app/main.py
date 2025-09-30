# backend/parquetformatter_api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import convert, feedback, metrics, preview
from app.services.logging_config import setup_logging

app = FastAPI(
    title="Parquet Formatter API",
    description="API for converting between Parquet, CSV, and NDJSON formats.",
    version="1.0.0",
)

setup_logging()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(convert.router, prefix="/v1", tags=["convert"])
app.include_router(preview.router, prefix="/v1", tags=["preview"])
app.include_router(feedback.router, prefix="/v1", tags=["feedback"])
app.include_router(metrics.router, prefix="/v1", tags=["metrics"])

@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
