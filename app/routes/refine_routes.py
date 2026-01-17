from fastapi import APIRouter
from pydantic import BaseModel
from app.db.supabase import get_supabase
from app.db.project_repo import ProjectRepo
from app.services.schema_service import SchemaService
# from app.services.gemini_service import GeminiService   # future

router = APIRouter()

class RefineRequest(BaseModel):
    project_id: str
    gemini_json: dict   # temporary since teammate gives gemini output


@router.post("/apply")
def apply_refinement(req: RefineRequest):
    supabase = get_supabase()

    # fetch old schema
    old = supabase.table("project").select("schema_json, status").eq(
        "project_id", req.project_id
    ).single().execute()

    old_schema = old.data.get("schema_json")

    # merge new
    merged = SchemaService.merge_gemini_into_schema(
        base_schema=old_schema,
        gemini_json=req.gemini_json
    )

    # update db
    ProjectRepo.update_schema(
        project_id=req.project_id,
        new_schema=merged,
        status="ready"
    )

    return {
        "project_id": req.project_id,
        "status": "ready",
        "schema": merged
    }
