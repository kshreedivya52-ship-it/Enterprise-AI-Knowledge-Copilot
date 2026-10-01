from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from langsmith import traceable

from app.core.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.core.vector_db import query_hybrid_search
from app.core.reranker import rerank_documents
from app.core.llm import generate_grounded_answer
from app.crud.chat import (
    get_or_create_conversation,
    add_chat_message,
    get_conversation_messages,
)

router = APIRouter(prefix="/search", tags=["search"])


def format_history_for_prompt(messages) -> str:
    """Formats raw database chat messages into a clean readable transcript for Gemini."""
    if not messages:
        return "No prior conversation history."
    formatted = []
    for msg in messages:
        role_label = "User" if msg.role == "user" else "Assistant"
        formatted.append(f"{role_label}: {msg.content}")
    return "\n".join(formatted)


@router.get("")
@traceable(name="hybrid search endpoint with conversation history", run_type="chain")
async def search_endpoint(
    q: str = Query(..., min_length=1, description="Search query string"),
    session_id: Optional[str] = Query(None, description="Optional conversation session UUID"),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stateful RAG endpoint:
    1. Loads or creates a conversation session in PostgreSQL for the user.
    2. Fetches past messages to inject context window into Gemini.
    3. Performs hybrid retrieval + reranking.
    4. Generates grounded answer with citations.
    5. Saves user question & assistant response + citations to PostgreSQL.
    """
    try:
        dept_filter = None if user.role == "admin" else user.department

        # 1. Fetch or create conversation thread in PostgreSQL
        conversation = await get_or_create_conversation(
            db=db,
            user_id=user.sub,
            conversation_id=session_id,
            title=q[:50]  # Auto-title using first prompt snippet
        )

        # 2. Retrieve recent message history (sliding window of last 10 messages)
        past_messages = await get_conversation_messages(
            db=db,
            conversation_id=conversation.id,
            limit=10
        )
        formatted_history = format_history_for_prompt(past_messages)

        # 3. Hybrid retrieval (Dense + Sparse)
        results = query_hybrid_search(query_text=q, department=dept_filter)

        # 4. Rerank candidates to top 5 precision chunks
        final_results = rerank_documents(query=q, documents=results, top_n=5)

        # 5. Grounded generation with citation verification + past history context
        rag_response = await generate_grounded_answer(
            query=q,
            documents=final_results,
            chat_history=formatted_history
        )

        # 6. Save user message to PostgreSQL
        await add_chat_message(
            db=db,
            conversation_id=conversation.id,
            role="user",
            content=q
        )

        # 7. Save assistant answer & citations to PostgreSQL
        citations_json = [c.model_dump() for c in rag_response.citations]
        await add_chat_message(
            db=db,
            conversation_id=conversation.id,
            role="assistant",
            content=rag_response.answer,
            citations=citations_json,
            extra_metadata={
                "has_sufficient_context": rag_response.has_sufficient_context,
                "total_sources_cited": len(rag_response.citations)
            }
        )

        return {
            "session_id": conversation.id,
            "query": q,
            "user": user.sub,
            "department_filter": dept_filter or "all (admin)",
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
