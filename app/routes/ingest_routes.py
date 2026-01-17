from fastapi import APIRouter
router = APIRouter()

@router.post("/transcript")
async def transcript_handler():
    return {"msg": "ingest endpoint placeholder"}
