"""
Background task for video rendering
"""
import os
import tempfile
from app.services.ffmpeg_service import FFmpegService
from app.services.cloudinary_service import CloudinaryService
from app.db.project_repo import ProjectRepo


# Global dict to track render progress and cancellation
render_progress = {}
render_processes = {}


def update_render_progress(project_id: str, progress: float, phase: str = "rendering"):
    """Update render progress in memory"""
    render_progress[project_id] = {
        "progress": progress,
        "phase": phase
    }
    print(f"[Render {project_id}] {phase.capitalize()}: {progress:.1f}%")


def cancel_render(project_id: str):
    """Cancel ongoing render"""
    if project_id in render_processes:
        process = render_processes[project_id]
        if process and process.poll() is None:  # Process is still running
            process.terminate()
            process.wait()
            print(f"[Render {project_id}] Cancelled")
        del render_processes[project_id]
    
    if project_id in render_progress:
        del render_progress[project_id]


def get_render_progress(project_id: str) -> float:
    """Get current render progress"""
    progress_data = render_progress.get(project_id, {"progress": 0, "phase": "rendering"})
    return progress_data["progress"]


def get_render_status(project_id: str) -> dict:
    """Get current render status with phase information"""
    return render_progress.get(project_id, {"progress": 0, "phase": "rendering"})


async def render_video_task(
    project_id: str,
    video_url: str,
    config: dict,
    filename: str,
    resolution: str = "original",
    quality: str = "high"
):
    """
    Background task to render video using direct pipe to Cloudinary
    
    Args:
        project_id: Project/Job ID
        video_url: Source video URL
        config: Edit configuration
        filename: Output filename
        resolution: Output resolution
        quality: Output quality
    """
    filter_file = None
    process = None
    temp_path = None
    
    try:
        print(f"[Render {project_id}] Starting render...")
        
        # Initialize progress
        update_render_progress(project_id, 0, "rendering")
        
        # Update status to rendering
        ProjectRepo.update_status(project_id, "rendering")
        
        # Create temporary file for output
        # Use mkstemp for better Windows compatibility
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)  # Close file descriptor immediately so FFmpeg can write
        
        # Render progress callback (0-80% of total progress)
        def render_progress_callback(progress: float):
            # Rendering takes 80% of total progress
            total_progress = progress * 0.8
            update_render_progress(project_id, total_progress, "rendering")
        
        # Render video to temp file
        success = FFmpegService.render_video(
            input_url=video_url,
            output_path=temp_path,
            config=config,
            resolution=resolution,
            quality=quality,
            progress_callback=render_progress_callback
        )
        
        if not success:
            raise Exception("FFmpeg rendering failed")
        
        print(f"[Render {project_id}] Rendering complete, uploading to Cloudinary...")
        
        # Upload progress callback (80-100% of total progress)
        def upload_progress_callback(progress: float):
            # Upload takes 20% of total progress (80-100%)
            total_progress = 80 + (progress * 0.2)
            update_render_progress(project_id, total_progress, "uploading")
        
        # Get file size for progress tracking
        file_size = os.path.getsize(temp_path)
        
        # Upload to Cloudinary with progress tracking
        with open(temp_path, 'rb') as video_file:
            video_url_result = CloudinaryService.upload_video_stream(
                video_stream=video_file,
                filename=filename,
                folder="rendered_videos",
                progress_callback=upload_progress_callback,
                estimated_size=file_size
            )
        
        print(f"[Render {project_id}] Upload complete: {video_url_result}")
        
        # Update database with final video URL
        ProjectRepo.update_export_url(project_id, video_url_result)
        ProjectRepo.update_status(project_id, "exported")
        
        update_render_progress(project_id, 100, "completed")
        
        print(f"[Render {project_id}] Export complete!")
        
    except Exception as e:
        print(f"[Render {project_id}] Failed: {str(e)}")
        
        # Clean up process if still running
        if process and process.poll() is None:
            process.terminate()
            process.wait()
        
        # Update status to failed
        ProjectRepo.update_status(project_id, "failed")
        ProjectRepo.update_error(project_id, str(e))
        
        raise
        
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        # Clean up filter file
        if filter_file and os.path.exists(filter_file):
            try:
                os.remove(filter_file)
            except:
                pass
        
        # Clean up progress tracking
        if project_id in render_progress:
            del render_progress[project_id]
        if project_id in render_processes:
            del render_processes[project_id]
