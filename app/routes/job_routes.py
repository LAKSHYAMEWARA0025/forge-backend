"""
Job management routes - Flow 1 (Initial Processing)
Complete implementation with background tasks
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from app.db.supabase import get_supabase
from app.db.project_repo import ProjectRepo

router = APIRouter()


class VideoMetadata(BaseModel):
    width: int
    height: int
    duration: float
    aspect_ratio: Optional[str] = "16:9"
    fps: Optional[int] = 30


class JobCreateRequest(BaseModel):
    video_url: str
    metadata: VideoMetadata


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    video_url: Optional[str] = None
    edit_config: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@router.post("/create")
async def create_job(request: JobCreateRequest, background_tasks: BackgroundTasks):
    """
    Create a new video processing job
    
    Flow:
    1. Create video record in DB
    2. Create project with initial config
    3. Trigger background task for processing
    4. Return job_id immediately
    """
    
    try:
        supabase = get_supabase()
        
        # Generate IDs
        job_id = str(uuid.uuid4())
        video_id = str(uuid.uuid4())
        
        # Insert video
        supabase.table("video").insert({
            "vid_id": video_id,
            "vid_url": request.video_url,
            "metadata": request.metadata.model_dump()
        }).execute()
        
        # Create initial config
        now = datetime.utcnow().isoformat() + "Z"
        duration = request.metadata.duration
        
        initial_config = {
            "id": job_id,
            "meta": {
                "schemaVersion": "1.1",
                "createdAt": now,
                "duration": duration,
                "timeUnit": "seconds"
            },
            "source": {
                "video": {
                    "id": video_id,
                    "url": request.video_url,
                    "width": request.metadata.width,
                    "height": request.metadata.height,
                    "aspectRatio": request.metadata.aspect_ratio,
                    "duration": duration
                }
            },
            "timeline": {
                "start": 0,
                "end": duration
            },
            "tracks": {
                "video": {
                    "animation": {
                        "presetId": "fade_in_out",
                        "fadeIn": {
                            "start": 0.0,
                            "duration": 0.8
                        },
                        "fadeOut": {
                            "start": max(0, duration - 2.0),
                            "duration": 2.0
                        }
                    }
                },
                "text": {
                    "globalStyle": {
                        "fontFamily": "Inter",
                        "fontSize": 14,
                        "fontWeight": 700,
                        "color": "#ffffff",
                        "background": "rgba(0,0,0,0.45)",
                        "padding": [12, 16],
                        "borderRadius": 12,
                        "position": {
                            "anchor": "bottom_center",
                            "offsetY": -50
                        }
                    },
                    "highlightStyle": {
                        "color": "#ffd166",
                        "scale": 1.03,
                        "fontWeight": 800
                    },
                    "animation": {
                        "entry": {
                            "presetId": "slide_up_fade",
                            "duration": 0.2
                        },
                        "exit": {
                            "presetId": "fade_out",
                            "duration": 0.2
                        },
                        "highlight": {
                            "presetId": "none",
                            "duration": 0.4
                        }
                    },
                    "captions": [],
                    "highlights": []
                },
                "audio": []
            },
            "settings": {
                "autoCaptions": True,
                "dynamicAnimations": True,
                "highlightKeywords": True,
                "introFadeIn": True,
                "outroFadeOut": True
            },
            "export": {
                "resolution": {
                    "width": request.metadata.width,
                    "height": request.metadata.height
                },
                "format": "mp4",
                "burnCaptions": True
            }
        }
        
        # Insert project
        supabase.table("project").insert({
            "project_id": job_id,
            "vid_id": video_id,
            "schema": initial_config,
            "status": "pending"
        }).execute()
        
        # Trigger background processing
        background_tasks.add_task(
            process_video_background,
            job_id=job_id,
            video_url=request.video_url,
            video_metadata=request.metadata.model_dump()
        )
        
        return {
            "job_id": job_id,
            "status": "pending"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Get job status for polling
    """
    
    if not job_id or job_id == "undefined" or job_id == "null":
        raise HTTPException(status_code=400, detail="Invalid job_id")
    
    try:
        supabase = get_supabase()
        
        result = supabase.table("project").select("status, project_id, schema").eq(
            "project_id", job_id
        ).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job_id,
            "status": result.data.get("status", "unknown"),
            "edit_config": result.data.get("schema") if result.data.get("status") == "ready" else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{job_id}/config")
async def get_job_config(job_id: str):
    """
    Get edit configuration for a job
    """
    
    try:
        supabase = get_supabase()
        
        result = supabase.table("project").select("schema, status").eq(
            "project_id", job_id
        ).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        config = result.data.get("schema")
        
        if not config:
            raise HTTPException(status_code=404, detail="Job has no configuration")
        
        return {
            "job_id": job_id,
            "status": result.data.get("status"),
            "config": config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


async def process_video_background(job_id: str, video_url: str, video_metadata: Dict[str, Any]):
    """
    Background task to process video
    
    Steps:
    1. Transcribe audio using AssemblyAI
    2. Process transcription with Gemini LLM
    3. Generate edit configuration
    4. Update job status to READY
    """
    
    try:
        print(f"[Job {job_id}] Starting video processing...")
        
        # Import services here to avoid circular imports
        from app.services.assembly_service import AssemblyService
        from app.services.gemini_service import GeminiService
        from app.services.config_service import ConfigService
        
        # Step 1: Transcribe audio
        print(f"[Job {job_id}] Starting transcription...")
        transcription_data = await AssemblyService.transcribe_video(video_url)
        print(f"[Job {job_id}] Transcription completed")
        
        # Step 2: Process with LLM
        print(f"[Job {job_id}] Processing with LLM...")
        llm_response = await GeminiService.process_transcription(
            transcription_data,
            video_metadata.get("duration", 0)
        )
        print(f"[Job {job_id}] LLM processing completed")
        
        # Step 3: Generate edit configuration
        print(f"[Job {job_id}] Generating edit configuration...")
        edit_config = ConfigService.generate_edit_config(
            job_id=job_id,
            video_url=video_url,
            video_metadata=video_metadata,
            llm_response=llm_response
        )
        
        # Step 4: Update job with config and mark as READY
        ProjectRepo.update_schema(
            project_id=job_id,
            new_schema=edit_config,
            status="ready"
        )
        
        print(f"[Job {job_id}] Processing completed successfully")
        
    except Exception as e:
        print(f"[Job {job_id}] Processing failed: {str(e)}")
        
        # Update job status to FAILED
        try:
            supabase = get_supabase()
            supabase.table("project").update({
                "status": "failed"
            }).eq("project_id", job_id).execute()
        except:
            pass
