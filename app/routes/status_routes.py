from fastapi import APIRouter
from app.db.supabase import get_supabase

router = APIRouter()

@router.get("/db-test")
def db_test():
    supabase = get_supabase()
    result = supabase.table("video").insert({
        "vid_url": "https://dummy.test",
        "metadata": {"test": True}
    }).execute()
    return {"data": result.data}
