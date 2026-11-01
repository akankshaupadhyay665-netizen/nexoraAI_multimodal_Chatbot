"""
Nexora AI - AI Video Studio Router
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import VideoJob
from backend.schemas import VideoGenerateRequest, VideoJobResponse
from backend.services.video_gen_service import video_gen_service

router = APIRouter(prefix="/api/video", tags=["video-studio"])

@router.post("/generate", response_model=VideoJobResponse)
async def generate_video(
    req: VideoGenerateRequest,
    db: Session = Depends(get_db)
):
    """Submits an asynchronous video generation task"""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    job_data = await video_gen_service.create_video_job(
        prompt=req.prompt,
        style=req.style or "cinematic",
        aspect_ratio=req.aspect_ratio or "16:9",
        duration=req.duration or 5,
        image_url=req.image_url
    )

    return VideoJobResponse(
        job_id=job_data["job_id"],
        status=job_data["status"],
        progress=job_data["progress"],
        prompt=job_data["prompt"],
        created_at=job_data["created_at"]
    )

@router.get("/jobs/{job_id}", response_model=VideoJobResponse)
def get_job_status(job_id: str):
    """Polls the execution status and progress of an asynchronous video job"""
    status = video_gen_service.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Video job not found")

    return VideoJobResponse(
        job_id=status["job_id"],
        status=status["status"],
        progress=status["progress"],
        video_url=status.get("video_url"),
        prompt=status["prompt"],
        error_message=status.get("error_message"),
        created_at=status["created_at"]
    )

@router.get("/jobs", response_model=List[VideoJobResponse])
def list_video_jobs(db: Session = Depends(get_db)):
    """Lists recent video generation jobs"""
    jobs = db.query(VideoJob).order_by(VideoJob.created_at.desc()).limit(20).all()
    res = []
    for j in jobs:
        res.append(VideoJobResponse(
            job_id=j.id,
            status=j.status,
            progress=j.progress,
            video_url=j.video_url,
            prompt=j.prompt,
            error_message=j.error_message,
            created_at=j.created_at
        ))
    return res

