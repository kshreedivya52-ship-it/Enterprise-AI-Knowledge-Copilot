# app/routes/search.py
from fastapi import APIRouter, Query
from langsmith import traceable
from app.core.vector_db import query_hybrid_search
from app.core.reranker import rerank_documents

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
@traceable(name="hybrid search endpoint", run_type="chain")
async def search_endpoint(q: str):
    """
    Exposes search to the web.
    E.g. GET http://localhost:8000/search?q=API timeout
    """
    results = query_hybrid_search(query_text=q)
    final_results = rerank_documents(query=q, documents=results, top_n=5)

    # response = llm.invoke(f"""Here are the search results {final_results} and the
    # user question is {q}\n answer the user question based on the search results""")
    
    return {
        "query": q,
        "candidates_before_rerank": len(results),
        "results_after_rerank": len(final_results),
        "before_rerank": results[:10],
        "after_rerank": final_results
    }


# # 2-stage hybrid search endpoint with reranking
# @router.get("/rerank")
# @traceable(name="2-stage search with reranking", run_type="chain")
# async def search(
#     query: str = Query(..., min_length=1, description="Search query cannot be empty"),
#     top_k: int = Query(5, ge=1, le=50, description="Number of results between 1 and 50")
# ):
    
#     # 1. Retrieve MORE candidates than we need (let reranker filter)
#     candidates = query_hybrid_search(query_text=query, limit=20)
    
#     # 2. RERANK (metadata preserved automatically!)
    
#     return {
#         "query": query,
#         "candidates_before_rerank": len(candidates),
#         "results_after_rerank": len(final_results),
#         "results": final_results
#     }
