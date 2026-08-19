# app/routes/search.py
from fastapi import APIRouter
from app.core.vector_db import query_hybrid_search  # <-- Import the helper function!

router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
async def search_endpoint(q: str):
    """
    Exposes search to the web.
    E.g. GET http://localhost:8000/search?q=API timeout
    """
    results = query_hybrid_search(query_text=q)
    return {"results": results}
