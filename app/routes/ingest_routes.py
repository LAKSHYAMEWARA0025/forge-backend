from fastapi import APIRouter
from pydantic import BaseModel
from app.services.assembly_service import AssemblyService
from app.services.schema_service import SchemaService

router = APIRouter()

class VideoInput(BaseModel):
    video_url: str

@router.post("/transcript")
async def transcript_handler(payload: VideoInput):
    raw_data = AssemblyService.fetch_transcript(payload.video_url)
    formatted = SchemaService.to_internal_schema(raw_data)
    return formatted
