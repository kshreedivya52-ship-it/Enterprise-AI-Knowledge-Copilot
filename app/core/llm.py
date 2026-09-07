import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

# ---------------------------------------------------------------------------
# 1. Pydantic Schemas for Grounded Answers & Inline Citations
# ---------------------------------------------------------------------------
class CitationItem(BaseModel):
    source_id: int = Field(description="ID corresponding to [1], [2]")
    source_file: str
    chunk_index: Optional[int] = None
    quote: str = Field(description="Exact verbatim text snippet")

class RAGAnswer(BaseModel):
    answer: str
    citations: List[CitationItem] = []
    has_sufficient_context: bool = Field(description="False if context is insufficient")

# ---------------------------------------------------------------------------
# 2. Strict Grounding & Citation System Prompt
# ---------------------------------------------------------------------------
SYSTEM_CITATION_PROMPT = """You are an Enterprise AI Knowledge Copilot.
Your job is to answer the user's question with absolute factual accuracy based EXCLUSIVELY on the provided <context>.

STRICT RULES:
1. Grounding: Rely ONLY on facts stated directly in the <context>. Do NOT speculate, infer without evidence, or use outside knowledge.
2. Inline Citations: Every single claim, fact, or bullet point MUST have an inline bracketed citation referencing the source ID, e.g. [1], [2], or [1][2].
3. Exact Verbatim Quotes: In the citations list, extract the exact snippet from the source document that supports the claim.
4. Missing Information: If the provided <context> does not contain enough relevant information to fully answer the question, state:
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
# 3. Gemini 2.5 Flash Model Factory
# ---------------------------------------------------------------------------
def get_gemini_llm(model_name: Optional[str] = None):
    """
    Initializes Google Gemini via langchain-google-genai with structured Pydantic output.
    Reads GOOGLE_API_KEY or GEMINI_API_KEY from the environment.
    """
    return ChatGoogleGenerativeAI(
        model=model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        temperature=0.0,
        max_output_tokens=2048
    ).with_structured_output(RAGAnswer)


# ---------------------------------------------------------------------------
# 4. Main Traced Generation Function
# ---------------------------------------------------------------------------
@traceable(name="Gemini 2.5 Flash Citation Generation", run_type="chain")
async def generate_grounded_answer(
    query: str,
    documents: List[Dict[str, Any]],
    model_name: Optional[str] = None
) -> RAGAnswer:
    """
    Generates a citation-backed, grounded response using Google Gemini 2.5 Flash.
    
    Args:
        query: User search or question string.
        documents: List of reranked document chunks from stage 2.
        model_name: Optional model override (defaults to gemini-2.5-flash).
        
    Returns:
        RAGAnswer: Structured Pydantic object containing the answer, inline citations,
                   and exact source quotes.
    """
    # 1. Format reranked chunks into XML context
    context_str = format_context_for_llm(documents)
    
    # 2. Build structured chat prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_CITATION_PROMPT),
        ("human", "Here is the retrieved context:\n{context}\n\nUser Question: {question}\n\nProvide a grounded answer with inline citations:")
    ])
    
    # 3. Create chain with structured output
    chain = prompt_template | get_gemini_llm(model_name)
    
    # 4. Invoke LLM asynchronously
    result: RAGAnswer = await chain.ainvoke({
        "context": context_str,
        "question": query
    })
    
    return result
