from app.db.supabase import get_supabase

class ProjectRepo:

    @staticmethod
    def update_schema(project_id: str, new_schema: dict, status: str = "ready"):
        supabase = get_supabase()

        resp = supabase.table("project").update({
            "schema": new_schema,
            "status": status
        }).eq("project_id", project_id).execute()

        return resp
