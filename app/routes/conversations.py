from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, CurrentUser
from app.core.database import get_db
from app.models.chat import Conversation
from app.crud.chat import (
    list_user_conversations,
    get_conversation_messages,
    delete_conversation,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=List[dict])
async def list_conversations_endpoint(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all active chat conversation threads for the authenticated user,
    sorted by most recently updated.
    """
    conversations = await list_user_conversations(db=db, user_id=user.sub)
    return [
        {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
        }
        for conv in conversations
    ]


@router.get("/{session_id}/messages")
async def get_conversation_messages_endpoint(
    session_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches the full transcript of messages for a specific conversation session.
    """
    # 1. Verify that the conversation thread exists and belongs to the user
    stmt = select(Conversation).where(
        Conversation.id == session_id,
        Conversation.user_id == user.sub
    )
    result = await db.execute(stmt)
    conversation = result.scalars().first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation session '{session_id}' not found for this user."
        )

    # 2. Fetch all messages in the conversation thread
    messages = await get_conversation_messages(db=db, conversation_id=session_id, limit=100)

    return {
        "session_id": session_id,
        "title": conversation.title,
        "total_messages": len(messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "citations": msg.citations,
                "created_at": msg.created_at
            }
            for msg in messages
        ]
    }


@router.delete("/{session_id}")
async def delete_conversation_endpoint(
    session_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a conversation session and all its associated messages from PostgreSQL.
    """
    deleted = await delete_conversation(db=db, conversation_id=session_id, user_id=user.sub)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation thread not found or access denied."
        )
    return {"message": f"Conversation session '{session_id}' deleted successfully."}
