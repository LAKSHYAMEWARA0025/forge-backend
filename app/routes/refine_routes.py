from fastapi import APIRouter
router = APIRouter()

@router.post("/refine")
async def refine_handler():
    return {"msg": "refine endpoint placeholder"}
