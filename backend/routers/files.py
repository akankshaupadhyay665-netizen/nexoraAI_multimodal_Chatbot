"""
Nexora AI - Multimodal File Upload & Analysis Router
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import UploadedFile
from backend.schemas import FileUploadResponse
from backend.services.document_service import document_service
from backend.services.vision_service import vision_service
from backend.services.audio_service import audio_service
from backend.services.video_service import video_service
from backend.services.rag_service import rag_service

router = APIRouter(prefix="/api/files", tags=["files"])

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Secure multimodal file upload and intelligent feature extraction"""
    settings.ensure_directories()

    # Determine general file category
    mime_type = file.content_type or "application/octet-stream"
    original_name = file.filename or "uploaded_file"
    ext = Path(original_name).suffix.lower()

    if mime_type in settings.ALLOWED_IMAGE_TYPES or ext in [".jpg", ".jpeg", ".png", ".webp"]:
        file_type = "image"
    elif mime_type in settings.ALLOWED_DOC_TYPES or ext in [".pdf", ".docx", ".doc", ".txt", ".csv", ".md"]:
        file_type = "document"
    elif mime_type in settings.ALLOWED_AUDIO_TYPES or ext in [".mp3", ".wav", ".m4a", ".ogg", ".webm"]:
        file_type = "audio"
    elif mime_type in settings.ALLOWED_VIDEO_TYPES or ext in [".mp4", ".mov", ".webm", ".avi"]:
        file_type = "video"
    else:
        file_type = "document"  # Default generic text/document

    # Secure unique filename
    file_id = str(uuid.uuid4())
    stored_filename = f"{file_id[:8]}_{original_name.replace(' ', '_')}"
    destination = settings.UPLOAD_DIR / stored_filename

    # Read and validate size
    contents = await file.read()
    file_size = len(contents)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Save to disk
    with open(destination, "wb") as f:
        f.write(contents)

    # Extract text or metadata depending on category
    extracted_text = None
    try:
        if file_type == "document":
            extraction = document_service.extract_text_from_file(str(destination), mime_type)
            extracted_text = extraction.get("text", "")
            # Auto-index into RAG Vector Knowledge Base
            chunks = document_service.chunk_document_for_rag(extraction)
            rag_service.index_document(doc_id=file_id, filename=original_name, chunks_data=chunks)

        elif file_type == "image":
            img_info = vision_service.inspect_image(str(destination))
            extracted_text = (
                f"Image Details: {img_info.get('format')} image, "
                f"Resolution {img_info.get('width')}x{img_info.get('height')}, "
                f"Size {img_info.get('size_kb')} KB."
            )

        elif file_type == "audio":
            aud_info = audio_service.inspect_audio(str(destination))
            dur = f", Duration: {aud_info.get('duration_seconds')}s" if aud_info.get("duration_seconds") else ""
            extracted_text = f"Audio Track: {aud_info.get('format')}{dur}, Size {aud_info.get('size_kb')} KB."

        elif file_type == "video":
            # Extract sampled frames for preview
            sampled_dir = settings.UPLOAD_DIR / f"{file_id[:8]}_frames"
            vid_info = video_service.inspect_and_sample_frames(str(destination), max_frames=3, output_dir=str(sampled_dir))
            extracted_text = (
                f"Video Stream: {vid_info.get('width')}x{vid_info.get('height')} @ {vid_info.get('fps')} fps, "
                f"Duration {vid_info.get('duration_seconds')} seconds."
            )
    except Exception as e:
        extracted_text = f"[Analysis Notice: {str(e)}]"

    # Persist in DB
    record = UploadedFile(
        id=file_id,
        conversation_id=conversation_id,
        original_name=original_name,
        stored_filename=stored_filename,
        file_type=file_type,
        mime_type=mime_type,
        file_size=file_size,
        file_path=str(destination),
        extracted_text=extracted_text
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    file_url = f"/storage/uploads/{stored_filename}"

    return FileUploadResponse(
        id=record.id,
        original_name=record.original_name,
        file_type=record.file_type,
        mime_type=record.mime_type,
        file_size=record.file_size,
        file_url=file_url,
        extracted_text=record.extracted_text
    )

@router.get("", response_model=List[FileUploadResponse])
def list_uploaded_files(db: Session = Depends(get_db)):
    """Lists all uploaded user files with URLs and metadata"""
    files = db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).limit(100).all()
    res = []
    for f in files:
        res.append(FileUploadResponse(
            id=f.id,
            original_name=f.original_name,
            file_type=f.file_type,
            mime_type=f.mime_type,
            file_size=f.file_size,
            file_url=f"/storage/uploads/{f.stored_filename}",
            extracted_text=f.extracted_text
        ))
    return res

@router.get("/{file_id}/download")
def download_file(file_id: str, db: Session = Depends(get_db)):
    """Downloads uploaded file with Content-Disposition: attachment"""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        file_record = db.query(UploadedFile).filter(UploadedFile.stored_filename == file_id).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File record not found")

    p = Path(file_record.file_path)
    if not p.is_absolute():
        p = settings.BASE_DIR / p

    if not p.exists() or not p.is_file():
        p = settings.UPLOAD_DIR / file_record.stored_filename
        if not p.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

    download_name = file_record.original_name or p.name
    return FileResponse(
        path=str(p),
        media_type=file_record.mime_type or "application/octet-stream",
        filename=download_name,
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.delete("/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Deletes uploaded file and removes it from disk"""
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove from disk
    p = Path(file_record.file_path)
    if p.exists():
        try:
            p.unlink()
        except Exception:
            pass

    # Remove from RAG index
    rag_service.remove_document(file_id)

    db.delete(file_record)
    db.commit()
    return {"status": "deleted", "file_id": file_id}

@router.post("/rag/search")
def search_knowledge_base(
    query: str = Form(...),
    top_k: int = Form(4),
    file_id: Optional[str] = Form(None)
):
    """Semantic vector search across indexed documents in RAG knowledge base"""
    results = rag_service.search(query=query, top_k=top_k, doc_id_filter=file_id)
    return {
        "query": query,
        "results_count": len(results),
        "matches": results
    }

@router.post("/compare")
def compare_uploaded_documents(
    file_id_1: str = Form(...),
    file_id_2: str = Form(...),
    db: Session = Depends(get_db)
):
    """Compares two uploaded documents and returns structural and thematic comparison"""
    f1 = db.query(UploadedFile).filter(UploadedFile.id == file_id_1).first()
    f2 = db.query(UploadedFile).filter(UploadedFile.id == file_id_2).first()

    if not f1 or not f2:
        raise HTTPException(status_code=404, detail="One or both document files not found")

    ext1 = document_service.extract_text_from_file(f1.file_path, f1.mime_type)
    ext2 = document_service.extract_text_from_file(f2.file_path, f2.mime_type)

    comparison_report = document_service.compare_documents(ext1, ext2)
    return {
        "doc1": f1.original_name,
        "doc2": f2.original_name,
        "comparison": comparison_report
    }

