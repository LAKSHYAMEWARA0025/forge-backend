# app/pipeline/export.py

from app.db.supabase import get_supabase
from app.services.export_formatter import format_for_ffmpeg  # teammate fn
from app.services.render_service import RenderService
from app.services.cloud_service import CloudService  # imaginary cloudinary
from app.services.ffmpeg_service import FFmpegService  # imaginary ffmpeg


def pipeline_export(project_id: str):
    supabase = get_supabase()

    # fetch project
    proj = supabase.table("project").select("*").eq("project_id", project_id).single().execute()
    if not proj.data:
        return False

    schema = proj.data["schema_json"]
    vid_id = proj.data["vid_id"]

    # fetch video
    vid = supabase.table("video").select("*").eq("vid_id", vid_id).single().execute()
    if not vid.data:
        return False

    video_url = vid.data["vid_url"]

    # step 1 — format for ffmpeg (function X)
    ffmpeg_config = format_for_ffmpeg(schema, video_url)

    # step 2 — generate render assets (ass subtitles)
    render_assets = RenderService.prepare_ffmpeg_config(schema)

    # step 3 — run ffmpeg streaming to cloudinary
    edited_video_url = FFmpegService.render_and_upload(
        video_url,
        ffmpeg_config,
        render_assets
    )

    # step 4 — update schema & status
    schema["export"]["videoUrl"] = edited_video_url

    supabase.table("project").update({
        "schema_json": schema,
        "status": "exported"
    }).eq("project_id", project_id).execute()

    return True
