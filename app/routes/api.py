from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/api", tags=["items"])

@router.get("/home")
async def read_items():

    return {"message": "hello world"}
