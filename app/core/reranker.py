from typing import List, Dict, Any
from fastembed.rerank.cross_encoder import TextCrossEncoder
from langsmith import traceable

# Global variable to cache the loaded model in memory
_reranker_model = None


def get_reranker() -> TextCrossEncoder:
    """
    Singleton pattern: Loads the BGE Reranker model into memory once.
    Subsequent calls reuse the cached model instance.
    """
    global _reranker_model
    if _reranker_model is None:
        # Default model is 'BAAI/bge-reranker-base' (lightweight, highly accurate ONNX model)
        _reranker_model = TextCrossEncoder(model_name="BAAI/bge-reranker-base")
    return _reranker_model


@traceable(name="bge rerank", run_type="tool")
def rerank_documents(
    query: str, 
    documents: List[Dict[str, Any]], 
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Takes candidate documents retrieved from Qdrant and re-scores them 
    against the query using BGE Cross-Encoder.
    
    Args:
        query: The user search query string.
        documents: List of retrieved chunks from Stage 1 (Qdrant).
                   Each item has 'text', 'id', 'score', and 'metadata'.
        top_n: The maximum number of high-precision chunks to return.
        
    Returns:
        List of reranked and sorted documents with their new 'rerank_score'.
    """
    if not documents:
        return []

    reranker = get_reranker()
    
    # 1. Extract raw text strings to pass to the reranker
    doc_texts = [doc["text"] for doc in documents]
    
    # 2. Compute cross-attention scores for (query, doc_text) pairs
    # FastEmbed rerank() yields a float score for each document in order
    scores = list(reranker.rerank(query=query, documents=doc_texts))
    
    # 3. Match the scores back to original documents to preserve all metadata
    reranked_docs = []
    for doc, score in zip(documents, scores):
        reranked_docs.append({
            "id": doc.get("id"),
            "text": doc.get("text"),
            "metadata": doc.get("metadata", {}),
            "first_stage_score": doc.get("score"),
            "rerank_score": float(score)
        })
        
    # 4. Sort documents descending by rerank_score and slice top_n
    reranked_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked_docs[:top_n]
