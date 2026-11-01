"""
Nexora AI - Activity & Usage Reports Router
Provides real statistics, model breakdown, and CSV data export from SQLite
"""
import io
import csv
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import Conversation, Message, UploadedFile, GeneratedMedia, VideoJob

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("", response_model=Dict[str, Any])
def get_usage_reports(db: Session = Depends(get_db)):
    """Computes real live activity metrics and model distribution from the database"""
    # Conversations & Messages metrics
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    user_messages = db.query(Message).filter(Message.role == "user").count()
    assistant_messages = db.query(Message).filter(Message.role == "assistant").count()

    # Uploads & Media metrics
    total_uploads = db.query(UploadedFile).count()
    total_upload_bytes = db.query(func.sum(UploadedFile.file_size)).scalar() or 0
    upload_storage_mb = round(total_upload_bytes / (1024 * 1024), 2)

    total_images = db.query(GeneratedMedia).filter(GeneratedMedia.media_type == "image").count()
    total_videos = db.query(GeneratedMedia).filter(GeneratedMedia.media_type == "video").count()
    total_video_jobs = db.query(VideoJob).count()

    # Model usage distribution
    model_counts = db.query(
        Message.model_name, func.count(Message.id)
    ).filter(Message.role == "assistant", Message.model_name.isnot(None)).group_by(Message.model_name).all()

    models_breakdown = []
    for model_name, count in model_counts:
        pct = round((count / max(1, assistant_messages)) * 100, 1)
        models_breakdown.append({
            "model": model_name or "gemini-2.5-flash",
            "count": count,
            "percentage": pct
        })

    if not models_breakdown and assistant_messages > 0:
        models_breakdown.append({
            "model": "gemini-2.5-flash",
            "count": assistant_messages,
            "percentage": 100.0
        })

    # Recent activity timeline
    recent_activity = []
    
    # Recent messages
    recent_msgs = db.query(Message).order_by(Message.created_at.desc()).limit(6).all()
    for m in recent_msgs:
        recent_activity.append({
            "type": "chat_message",
            "event": f"Message ({m.role.capitalize()})",
            "details": (m.content[:60] + "...") if len(m.content) > 60 else m.content,
            "timestamp": m.created_at.isoformat() if m.created_at else datetime.utcnow().isoformat(),
            "model": m.model_name or "N/A"
        })

    # Recent uploads
    recent_files = db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).limit(4).all()
    for f in recent_files:
        recent_activity.append({
            "type": "file_upload",
            "event": f"Upload: {f.file_type.upper()}",
            "details": f"{f.original_name} ({round(f.file_size / 1024, 1)} KB)",
            "timestamp": f.created_at.isoformat() if f.created_at else datetime.utcnow().isoformat(),
            "model": "Multimodal Pipeline"
        })

    # Recent media
    recent_media = db.query(GeneratedMedia).order_by(GeneratedMedia.created_at.desc()).limit(4).all()
    for med in recent_media:
        recent_activity.append({
            "type": "media_generation",
            "event": f"Generated {med.media_type.capitalize()}",
            "details": (med.prompt[:60] + "...") if len(med.prompt) > 60 else med.prompt,
            "timestamp": med.created_at.isoformat() if med.created_at else datetime.utcnow().isoformat(),
            "model": med.provider
        })

    # Sort combined activity chronologically descending
    recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "metrics": {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "total_uploads": total_uploads,
            "upload_storage_mb": upload_storage_mb,
            "total_generated_images": total_images,
            "total_generated_videos": total_videos,
            "total_video_jobs": total_video_jobs
        },
        "models_breakdown": models_breakdown,
        "recent_activity": recent_activity[:15],
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/export-csv")
def export_reports_csv(db: Session = Depends(get_db)):
    """Exports activity data as a downloadable CSV report"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Timestamp", "Activity Category", "Description", "Model / Provider", "Details"])

    # Conversations & Messages
    msgs = db.query(Message).order_by(Message.created_at.desc()).limit(200).all()
    for m in msgs:
        writer.writerow([
            m.created_at.isoformat() if m.created_at else "",
            f"Chat ({m.role})",
            m.content.replace("\n", " ")[:120],
            m.model_name or "gemini-2.5-flash",
            f"Conversation ID: {m.conversation_id}"
        ])

    # Uploaded Files
    files = db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).limit(100).all()
    for f in files:
        writer.writerow([
            f.created_at.isoformat() if f.created_at else "",
            "File Upload",
            f.original_name,
            f.file_type,
            f"{round(f.file_size / 1024, 2)} KB"
        ])

    # Generated Media
    media = db.query(GeneratedMedia).order_by(GeneratedMedia.created_at.desc()).limit(100).all()
    for med in media:
        writer.writerow([
            med.created_at.isoformat() if med.created_at else "",
            f"Media ({med.media_type})",
            med.prompt.replace("\n", " ")[:120],
            med.provider,
            f"Style: {med.style}, Ratio: {med.aspect_ratio}"
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nexora_ai_activity_report.csv"}
    )

