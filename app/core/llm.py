import os
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

# ---------------------------------------------------------------------------
# 1. Pydantic Schemas for Grounded Answers & Inline Citations
# ---------------------------------------------------------------------------
class CitationItem(BaseModel):
    source_id: int = Field(description="ID corresponding to [1], [2]")
    source_file: str
    chunk_index: Optional[Union[int, str]] = None
    quote: str = Field(description="Exact verbatim text snippet")

class RAGAnswer(BaseModel):
    answer: str
    citations: List[CitationItem] = Field(default_factory=list, description="List of citation items matching inline brackets")
    has_sufficient_context: bool = Field(default=True, description="True if context is sufficient, False if context is insufficient")

# ---------------------------------------------------------------------------
# 2. Strict Grounding & Citation System Prompt
# ---------------------------------------------------------------------------
SYSTEM_CITATION_PROMPT = """You are an Enterprise AI Knowledge Copilot.
Your job is to answer the user's question with absolute factual accuracy based EXCLUSIVELY on the provided <context>.

STRICT RULES:
1. Grounding: Rely ONLY on facts stated directly in the <context>. Do NOT speculate, infer without evidence, or use outside knowledge.
2. Inline Citations: Every single claim, fact, or bullet point MUST have an inline bracketed citation referencing the source ID, e.g. [1], [2], or [1][2].
3. Exact Verbatim Quotes: In the citations list, extract the exact snippet from the source document that supports the claim.
4. Output Schema Fields: You MUST ALWAYS include and populate all JSON output fields (`answer`, `citations`, `has_sufficient_context`). Set `has_sufficient_context` to true when the context is sufficient, or false when context is insufficient.
5. Missing Information: If the provided <context> does not contain enough relevant information to fully answer the question, state:
   "The provided enterprise documents do not contain sufficient information to answer this question."
   and set `has_sufficient_context` to false.
"""


def format_context_for_llm(documents: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved and reranked chunks into clean, structured XML source blocks.
    """
    if not documents:
        return "<context>\nNo relevant documents retrieved from the knowledge base.\n</context>"
    
    formatted_sources = []
    for i, doc in enumerate(documents, start=1):
        metadata = doc.get("metadata", {})
        source_file = metadata.get("source_file", "Unknown Document")
        chunk_idx = metadata.get("chunk_index", "N/A")
        text = doc.get("text", "").strip()
        
        source_block = (
            f'<source id="{i}" file="{source_file}" chunk="{chunk_idx}">\n'
            f'{text}\n'
            f'</source>'
        )
        formatted_sources.append(source_block)
        
    return "<context>\n" + "\n\n".join(formatted_sources) + "\n</context>"


# ---------------------------------------------------------------------------
# 3. OpenAI GPT-4o Model Factory
# ---------------------------------------------------------------------------
def get_openai_llm(model_name: Optional[str] = None):
    """
    Initializes OpenAI GPT-4o via langchain-openai with structured Pydantic output.
    Reads OPENAI_API_KEY and OPENAI_MODEL from the environment.
    """
    raw_key = os.getenv("OPENAI_API_KEY", "")
    api_key = raw_key.strip("'\"") if raw_key else None
    return ChatOpenAI(
        model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.0,
        max_tokens=4096,
        api_key=api_key,
    ).with_structured_output(RAGAnswer)


# Backward compatibility aliases
get_llm = get_openai_llm
get_gemini_llm = get_openai_llm


# ---------------------------------------------------------------------------
# 4. Main Traced Generation Function
# ---------------------------------------------------------------------------
@traceable(name="gpt-4o Citation Generation", run_type="chain")
async def generate_grounded_answer(
    query: str,
    documents: List[Dict[str, Any]],
    chat_history: Optional[str] = None,
    model_name: Optional[str] = None
) -> RAGAnswer:
    """
    Generates a citation-backed, grounded response using OpenAI GPT-4o.
    
    Args:
        query: User search or question string.
        documents: List of reranked document chunks from stage 2.
        chat_history: Formatted string of past conversation messages.
        model_name: Optional model override (defaults to gpt-4o).
        
    Returns:
        RAGAnswer: Structured Pydantic object containing the answer, inline citations,
                   and exact source quotes.
    """
    # 1. Early guard: If no documents found in knowledge base, return immediately without wasting LLM quota
    if not documents:
        return RAGAnswer(
            answer="No relevant documents were found in the knowledge base to answer this question. Please make sure your file is uploaded and indexed by clicking the **'Index document'** button in the sidebar.",
            citations=[],
            has_sufficient_context=False
        )

    # 2. Format reranked chunks into XML context
    context_str = format_context_for_llm(documents)
    history_str = chat_history or "No prior conversation history."
    
    # 3. Build structured chat prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_CITATION_PROMPT + "\n\n<conversation_history>\n{chat_history}\n</conversation_history>"),
        ("human", "Here is the retrieved context:\n{context}\n\nUser Question: {question}\n\nProvide a grounded answer with inline citations:")
    ])
    
    # 4. Invoke LLM with error handling for quota/rate limits and server spikes
    try:
        chain = prompt_template | get_openai_llm(model_name)
        result: RAGAnswer = await chain.ainvoke({
            "context": context_str,
            "chat_history": history_str,
            "question": query
        })
        return result
    except Exception as e:
        err_str = str(e)
        if "insufficient_quota" in err_str or "rate_limit_exceeded" in err_str or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            answer_text = (
                "⚠️ **OpenAI Quota Limit Reached (429 Rate Limit / Insufficient Quota)**: "
                "The OpenAI API quota or rate limit for GPT-4o has been exceeded. "
                "Please verify your `OPENAI_API_KEY` and account balance in `.env` or OpenAI dashboard."
            )
        elif "503" in err_str or "UNAVAILABLE" in err_str or "service_unavailable" in err_str:
            answer_text = (
                "⚠️ **OpenAI Service Temporarily Busy (503 Service Unavailable)**: "
                "OpenAI servers are currently experiencing high traffic. Please try your question again in a moment."
            )
        else:
            answer_text = f"⚠️ Could not generate grounded answer from AI model: {err_str}"

        # If we have retrieved document chunks, include a snippet so the user gets value
        citations = []
        for i, doc in enumerate(documents[:3], 1):
            meta = doc.get("metadata", {})
            citations.append(CitationItem(
                source_id=i,
                source_file=meta.get("source_file", "Uploaded Document"),
                chunk_index=meta.get("chunk_index"),
                quote=doc.get("text", "")[:180] + "..."
            ))

        return RAGAnswer(
            answer=answer_text,
            citations=citations,
            has_sufficient_context=False
        )
