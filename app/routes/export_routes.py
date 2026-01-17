from fastapi import APIRouter
router = APIRouter()

@router.post("/final")
async def export_handler():
    return {"msg": "export endpoint placeholder"}
