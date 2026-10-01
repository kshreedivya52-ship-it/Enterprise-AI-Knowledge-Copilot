from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import Conversation, ChatMessage


async def get_or_create_conversation(
    db: AsyncSession,
    user_id: str,
    conversation_id: Optional[str] = None,
    title: Optional[str] = None
) -> Conversation:
    """
    Retrieves an existing conversation thread by ID and User ID.
    If no ID is provided or conversation does not exist, creates a new one.
    """
    if conversation_id:
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        result = await db.execute(stmt)
        conversation = result.scalars().first()
        if conversation:
            return conversation

    # Create new conversation if not found or no ID passed
    new_conversation = Conversation(
        user_id=user_id,
        title=title or "New Conversation"
    )
    db.add(new_conversation)
    await db.commit()
    await db.refresh(new_conversation)
    return new_conversation

# 2. Append a user query or assistant answer (with citations) to PostgreSQL
async def add_chat_message(
    db: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    citations: Optional[List[Dict[str, Any]]] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> ChatMessage:
    """
    Appends a user prompt or assistant answer (with citations) to a conversation.
    """
    message = ChatMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        citations=citations,
        extra_metadata=extra_metadata
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

# 3. Retrieve recent message history in chronological order
async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: str,
    limit: int = 20
) -> List[ChatMessage]:
    """
    Retrieves recent chat history for a conversation thread in chronological order.
    """
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

# 4. List all chat threads belonging to a user
async def list_user_conversations(
    db: AsyncSession,
    user_id: str,
    limit: int = 50
) -> List[Conversation]:
    """
    Lists all chat sessions owned by a specific user, sorted by most recently updated.
    """
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

# 5. Delete a conversation thread and its messages
async def delete_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: str
) -> bool:
    """
    Deletes a conversation thread and all its messages for a given user.
    """
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    )
    result = await db.execute(stmt)
    conversation = result.scalars().first()
    
    if not conversation:
        return False
        
    await db.delete(conversation)
    await db.commit()
    return True
