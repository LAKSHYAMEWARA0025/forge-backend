# ingest_routes.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime
from app.db.supabase import get_supabase
from app.pipeline.upstream import pipeline_transcription_to_gemini

router = APIRouter()

class IngestRequest(BaseModel):
    video_url: str
    metadata: dict

@router.post("/start")
def start_ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    supabase = get_supabase()

    vid_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())

    # insert video
    supabase.table("video").insert({
        "vid_id": vid_id,
        "vid_url": req.video_url,
        "metadata": req.metadata
    }).execute()

    # build initial schema_v0
    now = datetime.utcnow().isoformat() + "Z"
    dur = req.metadata.get("duration", 0)

    schema_v0 = {
        "id": project_id,
        "meta": {
            "schemaVersion": "1.0",
            "projectId": project_id,
            "createdAt": now,
            "duration": dur,
            "timeUnit": "seconds"
        },
        "source": {
            "video": {
                "id": vid_id,
                "url": req.video_url,
                "width": req.metadata.get("width"),
                "height": req.metadata.get("height"),
                "aspectRatio": req.metadata.get("aspectRatio"),
                "duration": dur
            }
        },
        "timeline": {"start": 0, "end": dur},
        "tracks": {"text": {"captions": [], "title": None}},
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

    # insert project
    supabase.table("project").insert({
        "project_id": project_id,
        "vid_id": vid_id,
        "schema": schema_v0,
        "status": "pending"
    }).execute()

    # async pipeline call
    background_tasks.add_task(
        pipeline_transcription_to_gemini,
        project_id,
        req.video_url
    )

    return {"project_id": project_id, "status": "pending"}
