# backend/parquetformatter_api/tests/test_feedback_route.py
import pytest
from httpx import AsyncClient

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

async def test_post_feedback_success(client: AsyncClient):
    """
    Test that valid feedback is successfully submitted.
    """
    payload = {"message": "This is a test feedback message."}
    response = await client.post("/v1/feedback", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Feedback received"}

async def test_post_feedback_missing_message(client: AsyncClient):
    """
    Test that a request with a missing message field is rejected.
    """
    payload = {"email": "test@example.com"}
    response = await client.post("/v1/feedback", json=payload)
    assert response.status_code == 422  # Unprocessable Entity

async def test_post_feedback_empty_message(client: AsyncClient):
    """
    Test that a request with an empty message is rejected.
    """
    payload = {"message": ""}
    response = await client.post("/v1/feedback", json=payload)
    assert response.status_code == 422 # Validation error from Pydantic model

async def test_post_feedback_with_all_fields(client: AsyncClient):
    """
    Test that a request with all fields is processed correctly.
    """
    payload = {
        "message": "This is a test with all fields.",
        "email": "user@example.com",
        "page_path": "/parquet-to-csv"
    }
    response = await client.post("/v1/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Feedback received"
