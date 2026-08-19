from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["items"])

@router.get("/home")
async def read_items():
    return {"message": "hello world"}


