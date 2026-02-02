"""
Export/Render schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class ExportRequest(BaseModel):
    """Request to export/render final video"""
    project_id: str = Field(..., description="Project/Job ID")
    project_name: Optional[str] = Field(None, description="Project name for output filename")
    resolution: Literal["original", "1080p", "720p", "480p"] = Field("original", description="Output resolution")
    quality: Literal["high", "medium", "low"] = Field("high", description="Output quality (high=CRF18, medium=CRF23, low=CRF28)")
    burn_captions: bool = Field(True, description="Burn captions into video")
    format: Literal["mp4", "webm"] = Field("mp4", description="Output format")


class ExportResponse(BaseModel):
    """Response after triggering export"""
    project_id: str
    status: str  # "rendering"
    message: str


class ExportStatusResponse(BaseModel):
    """Response for export status check"""
    project_id: str
    status: str  # "rendering", "exported", "failed"
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    phase: Optional[str] = Field(None, description="Current phase: 'rendering', 'uploading', 'completed'")
    message: Optional[str] = None
    video_url: Optional[str] = Field(None, description="Final video URL (when exported)")
    error: Optional[str] = Field(None, description="Error message (when failed)")


class CancelExportRequest(BaseModel):
    """Request to cancel ongoing export"""
    project_id: str

