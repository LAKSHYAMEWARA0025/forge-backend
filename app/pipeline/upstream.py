from app.db.supabase import get_supabase
from app.services.assembly_service import AssemblyService
from app.services.gemini_service import GeminiService
from app.services.schema_service import SchemaService


def pipeline_transcription_to_gemini(project_id: str, video_url: str):
    supabase = get_supabase()

    # fetch base schema
    proj = supabase.table("project").select("*").eq("project_id", project_id).single().execute()
    if not proj.data:
        return

    base_schema = proj.data["schema_json"]

    # --- step 1: transcription ---
    parsed = AssemblyService.transcribe_and_parse(video_url)

    # --- step 2: call gemini ---
    gem_out = GeminiService.generate_script(parsed)   # teammate function

    # --- step 3: merge ---
    merged = SchemaService.merge_gemini_into_schema(
        base_schema,
        gem_out,
        first_run=True
    )

    # --- step 4: update DB ---
    supabase.table("project").update({
        "schema_json": merged,
        "status": "ready"
    }).eq("project_id", project_id).execute()

    return True
