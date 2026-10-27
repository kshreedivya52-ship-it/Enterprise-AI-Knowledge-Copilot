from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.core.auth import require_role, CurrentUser
from app.core.parser import parse_document
from app.core.chunker import chunk_document
from app.core.vector_db import upsert_document_chunks
import tempfile
import shutil
import os

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    department: Optional[str] = Form(None),
    user: CurrentUser = Depends(require_role("editor")),  # ← RBAC gate
):
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
        
        # Determine document department: explicit param takes priority, else user.department
        doc_department = department.lower().strip() if department else user.department

        # Index in Qdrant vector database (Dense + Sparse)
        upsert_document_chunks(chunks, file.filename, department=doc_department)
        
        return {
            "message": "Document ingested and indexed successfully",
            "filename": file.filename,
            "uploaded_by": user.sub,
            "department": doc_department,
            "total_chunks": len(chunks),
            "chunks": chunks,
            # "markdown": markdown,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        shutil.rmtree(temp_dir, ignore_errors=True)

