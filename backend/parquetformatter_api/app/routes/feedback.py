# backend/parquetformatter_api/app/routes/feedback.py
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.persistence import save_feedback

router = APIRouter()

class FeedbackPayload(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    email: str | None = None
    page_path: str | None = None

@router.post("/feedback")
async def post_feedback(payload: FeedbackPayload, request: Request) -> dict[str, Any]:
    """Accept user feedback and persist it via Supabase."""
    feedback_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": payload.message,
        "email": payload.email,
        "page_path": payload.page_path,
        "user_agent": request.headers.get("user-agent"),
        "client_host": request.client.host if request.client else "unknown",
    }

    await save_feedback(feedback_data)
    return {"status": "ok", "message": "Feedback received"}
