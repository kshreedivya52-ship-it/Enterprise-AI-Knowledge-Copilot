from typing import List, Dict, Any
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable

# Initialize splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""]
)

@traceable(name="Chunker", run_type="tool")
def chunk_document(
    text: str,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Splits a document text into recursive chunks and extracts metadata for each chunk.
    """
    chunks = splitter.split_text(text)
    
    structured_chunks = []
    for index, chunk in enumerate(chunks):
        structured_chunks.append({
            "chunk_index": index,
            "text": chunk,
            "metadata": {
                "source_file": os.path.basename(filename),
                "char_count": len(chunk),
                "word_count": len(chunk.split()),
                "snippet": chunk[:60] + "..." if len(chunk) > 60 else chunk
            }
        })
    return structured_chunks
