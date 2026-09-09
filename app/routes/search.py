from fastapi import APIRouter, HTTPException
from langsmith import traceable
from app.core.vector_db import query_hybrid_search
from app.core.reranker import rerank_documents
from app.core.llm import generate_grounded_answer

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
@traceable(name="hybrid search endpoint", run_type="chain")
async def search_endpoint(q: str):
    """
    Exposes search to the web.
    E.g. GET http://localhost:8000/search?q=API timeout
    """
    try:
        # 1. Hybrid retrieval(Dense + Sparse)
        results = query_hybrid_search(query_text=q)
        
        # 2. Rerank to top 5 precision chunks
        final_results = rerank_documents(query=q, documents=results, top_n=5)

        # 3. Grounded generation with citation verification
        rag_response = await generate_grounded_answer(query=q, documents=final_results)
        
        return {
            "query": q,
            "answer": rag_response.answer,
            "has_sufficient_context": rag_response.has_sufficient_context,
            "citations": rag_response.citations,
            "total_sources_cited": len(rag_response.citations),
            "reranked_chunks": final_results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search pipeline error: {str(e)}"
        )


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
