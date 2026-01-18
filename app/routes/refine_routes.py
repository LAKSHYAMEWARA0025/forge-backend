from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import copy

from app.db.supabase import get_supabase
from app.db.project_repo import ProjectRepo
from app.services.gemini_service import GeminiService
from app.services.validation_service import ValidationService
from app.services.config_update_service import ConfigUpdateService

router = APIRouter()


class ChatEditRequest(BaseModel):
    project_id: str
    message: str


class ChatEditResponse(BaseModel):
    project_id: str
    status: str  # "success", "partial_success", "rejected"
    message: str
    applied_edits: Optional[List[str]] = None
    rejected_edits: Optional[List[str]] = None
    updated_config: Optional[dict] = None


@router.post("/chat", response_model=ChatEditResponse)
def chat_edit(req: ChatEditRequest):
    """
    AI Chat Edit - Process natural language edit requests
    
    Flow:
    1. Fetch current config from DB
    2. Call Gemini LLM to analyze request
    3. Validate each edit instruction
    4. Apply valid edits to config
    5. Update DB with new config
    6. Return response with updated config
    """
    
    try:
        supabase = get_supabase()
        
        # Fetch current config
        result = supabase.table("project").select("schema, status").eq(
            "project_id", req.project_id
        ).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        current_config = result.data.get("schema")
        
        if not current_config:
            raise HTTPException(status_code=400, detail="Project has no configuration")
        
        # Call Gemini LLM
        try:
            llm_response = GeminiService.apply_chat_edit(req.message, current_config)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")
        
        # Log LLM response for debugging
        print(f"LLM Response: {llm_response}")
        
        # Check if LLM rejected the request
        if not llm_response.get("is_allowed", False):
            return ChatEditResponse(
                project_id=req.project_id,
                status="rejected",
                message=llm_response.get("rejection_reason", "Edit request not allowed"),
                updated_config=None
            )
        
        # Process edits
        edits = llm_response.get("edits", [])
        
        if not edits:
            # Return more helpful message
            return ChatEditResponse(
                project_id=req.project_id,
                status="rejected",
                message=f"Could not understand the edit request. LLM response: {llm_response.get('message', 'No edits generated')}",
                updated_config=None
            )
        
        # Validate and apply edits
        updated_config = copy.deepcopy(current_config)
        applied_edits = []
        rejected_edits = []
        
        for edit in edits:
            # Validate edit
            is_valid, error_message = ValidationService.validate_single_edit(edit)
            
            if is_valid:
                # Apply edit
                try:
                    updated_config = ConfigUpdateService.apply_edit(updated_config, edit)
                    
                    # Track applied edit
                    edit_description = _get_edit_description(edit)
                    applied_edits.append(edit_description)
                    
                except Exception as e:
                    # Track rejected edit
                    edit_description = _get_edit_description(edit)
                    rejected_edits.append(f"{edit_description}: {str(e)}")
            else:
                # Track rejected edit
                edit_description = _get_edit_description(edit)
                rejected_edits.append(f"{edit_description}: {error_message}")
        
        # Determine status
        if not applied_edits:
            # All edits rejected
            return ChatEditResponse(
                project_id=req.project_id,
                status="rejected",
                message=f"All edits rejected. {'; '.join(rejected_edits)}",
                rejected_edits=rejected_edits,
                updated_config=None
            )
        
        # Update database
        ProjectRepo.update_schema(
            project_id=req.project_id,
            new_schema=updated_config,
            status="ready"
        )
        
        # Build response message
        if rejected_edits:
            status = "partial_success"
            message = f"{llm_response.get('message', 'Edits applied')}. However, some edits were rejected: {'; '.join(rejected_edits)}"
        else:
            status = "success"
            message = llm_response.get('message', 'All edits applied successfully')
        
        return ChatEditResponse(
            project_id=req.project_id,
            status=status,
            message=message,
            applied_edits=applied_edits,
            rejected_edits=rejected_edits if rejected_edits else None,
            updated_config=updated_config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{project_id}/config")
def get_config(project_id: str):
    """
    Get edit configuration for a project
    """
    try:
        supabase = get_supabase()
        
        result = supabase.table("project").select("schema, status").eq(
            "project_id", project_id
        ).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        config = result.data.get("schema")
        
        if not config:
            raise HTTPException(status_code=404, detail="Project has no configuration")
        
        return {
            "project_id": project_id,
            "status": result.data.get("status"),
            "config": config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


class UpdateVideoRequest(BaseModel):
    video_url: str


@router.post("/update-video")
def update_video_hack(req: UpdateVideoRequest):
    """
    HACK: Update video URL in existing project config
    This simulates the initial processing without creating a new job
    Always uses project_id: 7e0d0aa6-17b6-44cd-baef-889e52bd1088
    """
    
    # Hardcoded project ID for demo
    project_id = "7e0d0aa6-17b6-44cd-baef-889e52bd1088"
    
    try:
        supabase = get_supabase()
        
        # Fetch current config (using 'schema' column, not 'schema_json')
        result = supabase.table("project").select("schema, vid_id").eq(
            "project_id", project_id
        ).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        config = result.data.get("schema")
        vid_id = result.data.get("vid_id")
        
        if not config:
            raise HTTPException(status_code=404, detail="Project has no configuration")
        
        # Update video URL in config
        config["source"]["video"]["url"] = req.video_url
        
        # Update video table
        if vid_id:
            supabase.table("video").update({
                "vid_url": req.video_url
            }).eq("vid_id", vid_id).execute()
        
        # Update project config (using 'schema' column)
        ProjectRepo.update_schema(
            project_id=project_id,
            new_schema=config,
            status="ready"
        )
        
        return {
            "project_id": project_id,
            "status": "success",
            "message": "Video URL updated successfully",
            "video_url": req.video_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{project_id}/status")
def get_status(project_id: str):
    """
    Get project status for polling
    """
    
    # Check for invalid project_id
    if not project_id or project_id == "undefined" or project_id == "null":
        raise HTTPException(
            status_code=400, 
            detail="Invalid project_id. Please provide a valid project ID."
        )
    
    try:
        supabase = get_supabase()
        
        result = supabase.table("project").select("status, project_id").eq(
            "project_id", project_id
        ).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "project_id": project_id,
            "status": result.data.get("status", "unknown")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


def _get_edit_description(edit: dict) -> str:
    """Get human-readable description of an edit"""
    action = edit.get("action", "unknown")
    
    if action == "update_text_animation":
        target = edit.get("target", "")
        preset = edit.get("preset_id", "")
        return f"{target} animation to {preset}"
    
    elif action == "update_video_animation":
        preset = edit.get("preset_id", "")
        return f"video animation to {preset}"
    
    elif action == "update_text_style":
        target = edit.get("target", "")
        props = edit.get("properties", {})
        return f"{target} ({', '.join(props.keys())})"
    
    elif action == "update_video_fade":
        fade_type = edit.get("fade_type", "")
        return f"{fade_type} settings"
    
    elif action == "update_highlights":
        operation = edit.get("operation", "")
        return f"{operation} highlights"
    
    else:
        return action
