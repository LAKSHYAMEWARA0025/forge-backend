# routes/export_routes.py

from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.db.supabase import get_supabase
from app.pipeline.export import pipeline_export

router = APIRouter()

@router.post("/start")
def start_export(req: dict, background_tasks: BackgroundTasks):
    if "project_id" not in req:
        raise HTTPException(status_code=400, detail="project_id required")

    project_id = req["project_id"]

    supabase = get_supabase()

    proj = supabase.table("project").select("*").eq("project_id", project_id).single().execute()
    if not proj.data:
        raise HTTPException(status_code=404, detail="project not found")

    if proj.data["status"] != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"cannot export in state {proj.data['status']}"
        )

    # mark rendering
    supabase.table("project").update({"status": "rendering"}).eq("project_id", project_id).execute()

    background_tasks.add_task(pipeline_export, project_id)

    return {
        "project_id": project_id,
        "status": "rendering"
    }
