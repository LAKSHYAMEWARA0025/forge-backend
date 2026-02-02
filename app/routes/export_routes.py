"""
Export/Render routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.export_schema import (
    ExportRequest,
    ExportResponse,
    ExportStatusResponse,
    CancelExportRequest
)
from app.db.project_repo import ProjectRepo
from app.tasks.render_task import render_video_task, get_render_progress, get_render_status, cancel_render
import uuid

router = APIRouter()


@router.post("/render", response_model=ExportResponse)
async def start_render(req: ExportRequest, background_tasks: BackgroundTasks):
    """
    Start video rendering process
    
    Export Options:
    - project_name: Name for output file
    - resolution: original, 1080p, 720p, 480p
    - quality: high (CRF 18), medium (CRF 23), low (CRF 28)
    - burn_captions: Whether to burn captions into video
    
    Flow:
    1. Fetch project and edit config from DB
    2. Validate config exists
    3. Update status to "rendering"
    4. Trigger background render task
    5. Return immediate response (client polls /status endpoint)
    """
    try:
        # Fetch project
        project = ProjectRepo.get_project(req.project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if config exists
        config = project.get("schema")
        if not config:
            raise HTTPException(status_code=400, detail="Project has no edit configuration")
        
        # Check current status
        current_status = project.get("status")
        if current_status == "rendering":
            raise HTTPException(status_code=400, detail="Project is already being rendered")
        
        # Get video URL from config
        video_url = config.get("source", {}).get("video", {}).get("url")
        if not video_url:
            raise HTTPException(status_code=400, detail="No video source found in configuration")
        
        # Generate filename from project_name or use project_id
        if req.project_name:
            # Sanitize project name for filename
            safe_name = "".join(c for c in req.project_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            filename = f"{safe_name}_{uuid.uuid4().hex[:6]}"
        else:
            filename = f"video_{req.project_id}_{uuid.uuid4().hex[:8]}"
        
        # If burn_captions is False, remove captions from config
        render_config = config.copy()
        if not req.burn_captions:
            if "tracks" in render_config and "text" in render_config["tracks"]:
                render_config["tracks"]["text"]["captions"] = []
                render_config["tracks"]["text"]["highlights"] = []
        
        # Trigger background render task
        background_tasks.add_task(
            render_video_task,
            project_id=req.project_id,
            video_url=video_url,
            config=render_config,
            filename=filename,
            resolution=req.resolution,
            quality=req.quality
        )
        
        return ExportResponse(
            project_id=req.project_id,
            status="rendering",
            message=f"Video rendering started. Poll /export/status/{req.project_id} for progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start render: {str(e)}")


@router.get("/status/{project_id}", response_model=ExportStatusResponse)
async def get_render_status_endpoint(project_id: str):
    """
    Get render status and progress with phase information
    
    Returns:
    - status: "rendering", "exported", "failed"
    - progress: 0-100 (only when rendering)
    - phase: "rendering", "uploading", "completed" (only when rendering)
    - video_url: Final video URL (only when exported)
    - error: Error message (only when failed)
    """
    try:
        # Fetch project
        project = ProjectRepo.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        status = project.get("status")
        
        # If rendering, get progress and phase
        if status == "rendering":
            status_data = get_render_status(project_id)
            progress = status_data.get("progress", 0)
            phase = status_data.get("phase", "rendering")
            
            phase_messages = {
                "rendering": f"Rendering video: {progress:.1f}%",
                "uploading": f"Uploading to cloud: {progress:.1f}%",
                "completed": "Finalizing..."
            }
            
            return ExportStatusResponse(
                project_id=project_id,
                status="rendering",
                progress=progress,
                phase=phase,
                message=phase_messages.get(phase, f"Processing: {progress:.1f}%")
            )
        
        # If exported, return video URL
        elif status == "exported":
            video_url = project.get("export_url")
            return ExportStatusResponse(
                project_id=project_id,
                status="exported",
                progress=100,
                phase="completed",
                message="Video exported successfully",
                video_url=video_url
            )
        
        # If failed, return error
        elif status == "failed":
            error = project.get("error", "Unknown error")
            return ExportStatusResponse(
                project_id=project_id,
                status="failed",
                message="Rendering failed",
                error=error
            )
        
        # Other statuses
        else:
            return ExportStatusResponse(
                project_id=project_id,
                status=status,
                message=f"Project status: {status}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/cancel")
async def cancel_render_endpoint(req: CancelExportRequest):
    """
    Cancel ongoing render process
    """
    try:
        # Check if project exists
        project = ProjectRepo.get_project(req.project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if rendering
        if project.get("status") != "rendering":
            raise HTTPException(status_code=400, detail="Project is not being rendered")
        
        # Cancel render
        cancel_render(req.project_id)
        
        # Update status
        ProjectRepo.update_status(req.project_id, "ready")
        
        return {
            "project_id": req.project_id,
            "status": "cancelled",
            "message": "Render cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel render: {str(e)}")


# Legacy endpoint (keep for backward compatibility)
@router.post("/final")
async def export_handler():
    return {"msg": "Use /export/render endpoint instead"}

