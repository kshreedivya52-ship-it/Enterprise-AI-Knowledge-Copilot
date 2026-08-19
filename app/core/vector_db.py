import os
import hashlib
from typing import List, Dict, Any
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding, SparseTextEmbedding
from langsmith import traceable

# Initialize Client
client = QdrantClient("http://localhost:6333")
COLLECTION_NAME = "hybrid_knowledge_base"

# Load BGE for semantic search (384 dimensions)
dense_model = TextEmbedding("BAAI/bge-small-en-v1.5")

# Load SPLADE for keyword search
sparse_model = SparseTextEmbedding("prithivida/Splade_PP_en_v1")


def init_qdrant():
    """
    Safely initialize Qdrant collection with both Dense and Sparse configurations
    if it does not already exist.
    """
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(
                    size=384, 
                    distance=models.Distance.COSINE
                ),
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(),
            }
        )


def _get_stable_id(text: str) -> int:
    """Helper to generate a stable positive 32-bit integer ID from text."""
    # Using hashlib MD5 to guarantee stability across environments (standard Python hash() is randomized per process)
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)

@traceable(name="save to qdrant", run_type="tool")
def upsert_document_chunks(chunks: List[Dict[str, Any]], filename: str):
    """
    Generate dense and sparse embeddings for a list of document chunks
    and upsert them with payload metadata into Qdrant.
    """
    init_qdrant()
    
    # Extract raw text from chunks
    texts = [chunk["text"] for chunk in chunks]
    if not texts:
        return
        
    # Batch embed texts
    dense_embeddings = list(dense_model.embed(texts))
    sparse_embeddings = list(sparse_model.embed(texts))
    
    points = []
    for i, chunk in enumerate(chunks):
        dense_vec = dense_embeddings[i].tolist()
        sparse_vec = sparse_embeddings[i]
        
        # Prepare Qdrant point structure
        point_id = _get_stable_id(chunk["text"])
        
        # Combine text and chunk metadata into the payload
        payload = {
            "text": chunk["text"],
            "source_file": filename,
            **chunk["metadata"]
        }
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector={
                    "dense": dense_vec,
                    "sparse": models.SparseVector(
                        indices=sparse_vec.indices.tolist(),
                        values=sparse_vec.values.tolist()
                    )
                },
                payload=payload
            )
        )
        
    client.upsert(
        collection_name=COLLECTION_NAME,
        wait=True,
        points=points
    )

@traceable(name="query hybrid search", run_type="tool")
def query_hybrid_search(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Perform hybrid search (Dense Vector + SPLADE Sparse Vector) in Qdrant
    and merge the rankings using Reciprocal Rank Fusion (RRF).
    """
    init_qdrant()
    
    # Generate embeddings for the search query
    query_dense = list(dense_model.embed([query_text]))[0].tolist()
    query_sparse = list(sparse_model.embed([query_text]))[0]
    
    # Execute fused search
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=query_dense,
                using="dense",
                limit=20
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=query_sparse.indices.tolist(),
                    values=query_sparse.values.tolist()
                ),
                using="sparse",
                limit=20
            )
        ],
        query=models.FusionQuery(
            fusion=models.Fusion.RRF
        ),
        limit=limit
    )
    
    # Format and return matched items
    return [
        {
            "score": hit.score,
            "id": hit.id,
            "text": hit.payload.get("text"),
            "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
        }
        for hit in results.points
    ]
