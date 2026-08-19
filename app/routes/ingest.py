from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.parser import parse_document
from app.core.chunker import chunk_document
from app.core.vector_db import upsert_document_chunks
import tempfile
import shutil
import os

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document, parse it, chunk it recursively, and index it into Qdrant.
    """
    # Save to temp file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse!
        markdown = await parse_document(temp_path)
        
        # Split recursively!
        chunks = chunk_document(markdown, file.filename)
        
        # Index in Qdrant vector database (Dense + Sparse)
        upsert_document_chunks(chunks, file.filename)
        
        return {
            "message": "Document ingested and indexed successfully",
            "filename": file.filename,
            "total_chunks": len(chunks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        shutil.rmtree(temp_dir, ignore_errors=True)

