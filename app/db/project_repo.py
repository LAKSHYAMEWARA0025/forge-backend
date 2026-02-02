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
    
    @staticmethod
    def update_status(project_id: str, status: str):
        """Update project status"""
        supabase = get_supabase()
        
        resp = supabase.table("project").update({
            "status": status
        }).eq("project_id", project_id).execute()
        
        return resp
    
    @staticmethod
    def update_export_url(project_id: str, export_url: str):
        """Update project with exported video URL"""
        supabase = get_supabase()
        
        resp = supabase.table("project").update({
            "export_url": export_url
        }).eq("project_id", project_id).execute()
        
        return resp
    
    @staticmethod
    def update_error(project_id: str, error_message: str):
        """Update project with error message"""
        supabase = get_supabase()
        
        resp = supabase.table("project").update({
            "error": error_message
        }).eq("project_id", project_id).execute()
        
        return resp
    
    @staticmethod
    def get_project(project_id: str):
        """Get project by ID"""
        supabase = get_supabase()
        
        resp = supabase.table("project").select("*").eq(
            "project_id", project_id
        ).single().execute()
        
        return resp.data if resp.data else None

