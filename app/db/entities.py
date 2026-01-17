from pydantic import BaseModel
from typing import Any, Dict
from datetime import datetime

class TranscriptEntity(BaseModel):
    id: str
    video_url: str
    raw_transcript: Dict[str, Any]
    refined_transcript: Dict[str, Any] | None = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    version: int = 1
