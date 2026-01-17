from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.db.supabase import get_supabase
import subprocess
import cloudinary.uploader

router = APIRouter()

# Placeholder function X
def function_x(project_id: str, schema: dict, video_url: str) -> dict:
    """
    Returns data for ffmpeg consumption.
    Real implementation will transform schema -> timeline/captions/overlays
    """
    # teammate will implement
    return {
        "ffmpeg_input": {
            "timeline": schema.get("timeline"),
            "tracks": schema.get("tracks")
        },
        "video_url": video_url
    }


def run_ffmpeg_and_upload(project_id: str, ffmpeg_payload: dict):
    video_url = ffmpeg_payload["video_url"]
    timeline = ffmpeg_payload["ffmpeg_input"]["timeline"]
    tracks = ffmpeg_payload["ffmpeg_input"]["tracks"]

    # (Placeholder for real ffmpeg command)
    # Example ffmpeg command using input URL:
    cmd = [
        "ffmpeg",
        "-i", video_url,
        "-y",
        "output.mp4"
    ]

    # Run ffmpeg (blocking for now)
    subprocess.run(cmd, check=True)

    # Upload to Cloudinary stream
    upload_resp = cloudinary.uploader.upload("output.mp4", resource_type="video")

    edited_video_url = upload_resp["secure_url"]

    # Return — we will update DB in the next step
    return edited_video_url


@router.post("/start")
def start_export(req: dict, background_tasks: BackgroundTasks):
    if "project_id" not in req:
        raise HTTPException(status_code=400, detail="project_id required")

    project_id = req["project_id"]
    supabase = get_supabase()

    # Fetch project
    proj_resp = supabase.table("project").select("*").eq("project_id", project_id).single().execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="project not found")

    project = proj_resp.data
    if project["status"] != "ready":
        raise HTTPException(status_code=400, detail=f"cannot export in state {project['status']}")

    # Fetch video
    vid_resp = supabase.table("video").select("*").eq("vid_id", project["vid_id"]).single().execute()
    if not vid_resp.data:
        raise HTTPException(status_code=404, detail="video not found")

    video = vid_resp.data
    schema = project["schema_json"]
    video_url = video["vid_url"]

    # Status: ready → rendering
    supabase.table("project").update({
        "status": "rendering"
    }).eq("project_id", project_id).execute()

    def pipeline():
        ffmpeg_payload = function_x(project_id, schema, video_url)
        edited_url = run_ffmpeg_and_upload(project_id, ffmpeg_payload)

    # ---- FINAL STEP ----
        supabase = get_supabase()

        # fetch schema again in case frontend modified
        proj_resp = supabase.table("project").select("*").eq("project_id", project_id).single().execute()
        if not proj_resp.data:
            print("Project disappeared", project_id)
            return

        project = proj_resp.data
        updated_schema = project["schema_json"]

        # mutate export block
        if "export" not in updated_schema:
            updated_schema["export"] = {}

        updated_schema["export"]["videoUrl"] = edited_url

        # status: rendering → exported
        supabase.table("project").update({
            "schema_json": updated_schema,
            "status": "exported"
        }).eq("project_id", project_id).execute()

        print("FULL EXPORT COMPLETE:", edited_url)


    background_tasks.add_task(pipeline)

    return {"status": "rendering_started", "project_id": project_id}
