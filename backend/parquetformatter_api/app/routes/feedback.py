# backend/parquetformatter_api/app/routes/feedback.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import json
from datetime import datetime

from app.config import FEEDBACK_FILE_PATH

router = APIRouter()

class FeedbackPayload(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    email: str | None = None
    page_path: str | None = None

@router.post("/feedback")
async def post_feedback(payload: FeedbackPayload, request: Request):
    """
    Accepts feedback from users and logs it to a file.
    """
    try:
        feedback_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": payload.message,
            "email": payload.email,
            "page_path": payload.page_path,
            "user_agent": request.headers.get("user-agent"),
            "client_host": request.client.host if request.client else "unknown",
        }

        with open(FEEDBACK_FILE_PATH, "a") as f:
            f.write(json.dumps(feedback_data) + "\\n")

        return {"status": "ok", "message": "Feedback received"}
    except Exception as e:
        # In a real app, you'd have more sophisticated logging
        print(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail="Could not save feedback.")
