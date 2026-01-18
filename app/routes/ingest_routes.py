from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Dict, Any

from app.db.supabase import get_supabase
# from app.services.assembly_service import start_transcription  # TODO: Implement in Flow 1

router = APIRouter()

class IngestRequest(BaseModel):
    video_url: str
    metadata: Dict[str, Any]

@router.post("/start")
def start_ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    supabase = get_supabase()

    vid_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())

    # 1. video insert
    supabase.table("video").insert({
        "vid_id": vid_id,
        "vid_url": req.video_url,
        "metadata": req.metadata
    }).execute()

    # 2. create initial schema
    now = datetime.utcnow().isoformat() + "Z"
    duration = req.metadata.get("duration", 0)

    schema_v0 = {
        "id": project_id,
        "meta": {
            "schemaVersion": "1.0",
            "projectId": project_id,
            "createdAt": now,
            "duration": duration,
            "timeUnit": "seconds"
        },
        "source": {
            "video": {
                "id": vid_id,
                "url": req.video_url,
                "width": req.metadata.get("width"),
                "height": req.metadata.get("height"),
                "aspectRatio": req.metadata.get("aspectRatio"),
                "duration": duration
            }
        },
        "timeline": {"start": 0, "end": duration},
        "tracks": {
            "video": {},
            "text": {"captions": [], "title": None},
            "audio": []
        },
        "effects": {},
        "transcript": {"words": []},
        "settings": {
            "autoCaptions": True,
            "dynamicAnimations": True,
            "highlightKeywords": True,
            "introFadeIn": True,
            "outroFadeOut": True
        },
        "export": {
            "resolution": {"width": 1080, "height": 1920},
            "format": "mp4",
            "burnCaptions": True
        }
    }

    # 3. create project row
    supabase.table("project").insert({
        "project_id": project_id,
        "vid_id": vid_id,
        "schema_json": schema_v0,
        "status": "pending"
    }).execute()

    # 4. Start transcription async (TODO: Implement in Flow 1)
    # background_tasks.add_task(start_transcription, project_id, req.video_url)

    return {"project_id": project_id, "status": "pending"}
