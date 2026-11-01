"""
Nexora AI - Media Gallery Router
"""
import re
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import GeneratedMedia

router = APIRouter(prefix="/api/media", tags=["media-gallery"])

@router.get("")
def list_media(
    media_type: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(60, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists generated images and videos for the Media Gallery"""
    target_type = media_type or type
    query = db.query(GeneratedMedia)
    if target_type:
        query = query.filter(GeneratedMedia.media_type == target_type)
    
    items = query.order_by(GeneratedMedia.created_at.desc()).limit(limit).all()
    results = []
    for item in items:
        folder = "generated_images" if item.media_type == "image" else "generated_videos"
        results.append({
            "id": item.id,
            "media_type": item.media_type,
            "prompt": item.prompt,
            "style": item.style,
            "aspect_ratio": item.aspect_ratio,
            "filename": item.filename,
            "file_url": f"/storage/{folder}/{item.filename}",
            "provider": item.provider,
            "status": item.status,
            "created_at": item.created_at
        })
    return results

@router.get("/download/file")
def download_media_by_filename(filename: str = Query(...), db: Session = Depends(get_db)):
    """
    Downloads media file by filename from generated_images, generated_videos, or uploads.
    Forces browser download via Content-Disposition: attachment header.
    """
    safe_filename = Path(filename).name
    possible_paths = [
        settings.GENERATED_IMAGE_DIR / safe_filename,
        settings.GENERATED_VIDEO_DIR / safe_filename,
        settings.UPLOAD_DIR / safe_filename
    ]
    for p in possible_paths:
        if p.exists() and p.is_file():
            ext = p.suffix.lower()
            m_type = "image/png" if ext == ".png" else ("image/jpeg" if ext in [".jpg", ".jpeg"] else ("video/mp4" if ext == ".mp4" else ("video/webm" if ext == ".webm" else "application/octet-stream")))
            return FileResponse(
                path=str(p),
                media_type=m_type,
                filename=safe_filename,
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_filename}"',
                    "Access-Control-Expose-Headers": "Content-Disposition"
                }
            )

    raise HTTPException(status_code=404, detail=f"File {safe_filename} not found on disk")

@router.get("/{media_id}/download")
def download_media_by_id(media_id: str, db: Session = Depends(get_db)):
    """
    Downloads media file by database ID, job ID, or exact filename.
    Returns FileResponse with Content-Disposition: attachment for real browser download.
    """
    item = db.query(GeneratedMedia).filter(GeneratedMedia.id == media_id).first()
    if not item:
        item = db.query(GeneratedMedia).filter(
            (GeneratedMedia.job_id == media_id) |
            (GeneratedMedia.filename == media_id)
        ).first()

    if not item:
        # Check if media_id is an actual filename directly in generated_images or generated_videos
        possible_paths = [
            settings.GENERATED_IMAGE_DIR / media_id,
            settings.GENERATED_VIDEO_DIR / media_id,
            settings.UPLOAD_DIR / media_id
        ]
        for p in possible_paths:
            if p.exists() and p.is_file():
                ext = p.suffix.lower()
                m_type = "image/png" if ext == ".png" else ("video/mp4" if ext == ".mp4" else ("video/webm" if ext == ".webm" else "application/octet-stream"))
                return FileResponse(
                    path=str(p),
                    media_type=m_type,
                    filename=p.name,
                    headers={
                        "Content-Disposition": f'attachment; filename="{p.name}"',
                        "Access-Control-Expose-Headers": "Content-Disposition"
                    }
                )
        raise HTTPException(status_code=404, detail="Media record not found")

    file_path = Path(item.file_path)
    if not file_path.is_absolute():
        file_path = settings.BASE_DIR / file_path

    if not file_path.exists() or not file_path.is_file():
        # Check by filename inside storage directory
        alt_dir = settings.GENERATED_IMAGE_DIR if item.media_type == "image" else settings.GENERATED_VIDEO_DIR
        alt_path = alt_dir / item.filename
        if alt_path.exists():
            file_path = alt_path
        else:
            raise HTTPException(status_code=404, detail=f"File {item.filename} not found on disk")

    ext = file_path.suffix.lower()
    content_type = "image/png" if ext == ".png" else ("image/jpeg" if ext in [".jpg", ".jpeg"] else ("video/mp4" if ext == ".mp4" else ("video/webm" if ext == ".webm" else "application/octet-stream")))

    safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', (item.prompt or "nexora_media")[:32]).strip('_') or "nexora_media"
    download_filename = f"{safe_title}{ext}"

    return FileResponse(
        path=str(file_path),
        media_type=content_type,
        filename=download_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.delete("/{media_id}")
def delete_media(media_id: str, db: Session = Depends(get_db)):
    """Deletes media item and frees local storage"""
    item = db.query(GeneratedMedia).filter(GeneratedMedia.id == media_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Media item not found")

    p = Path(item.file_path)
    if p.exists():
        try:
            p.unlink()
        except Exception:
            pass

    db.delete(item)
    db.commit()
    return {"status": "deleted", "media_id": media_id}
