"""
Nexora AI - AI Video Generation Service
Implements asynchronous video jobs, progress tracking, and real MP4 generation
"""
import os
import uuid
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import cv2
import numpy as np
from PIL import Image
import imageio_ffmpeg

from backend.config import settings
from backend.database import SessionLocal
from backend.models import VideoJob, GeneratedMedia
from backend.services.image_gen_service import image_gen_service

class VideoGenService:
    @staticmethod
    async def create_video_job(
        prompt: str,
        style: str = "cinematic",
        aspect_ratio: str = "16:9",
        duration: int = 5,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates an async video generation job and initiates background synthesis"""
        settings.ensure_directories()
        job_id = str(uuid.uuid4())

        # Save initial job in database
        db = SessionLocal()
        try:
            job = VideoJob(
                id=job_id,
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio,
                duration=duration,
                status="pending",
                progress=5
            )
            db.add(job)
            db.commit()
            db.refresh(job)
        finally:
            db.close()

        # Fire and forget background worker
        asyncio.create_task(
            VideoGenService._process_video_job(job_id, prompt, style, aspect_ratio, duration, image_url)
        )

        return {
            "job_id": job_id,
            "status": "pending",
            "progress": 5,
            "prompt": prompt,
            "created_at": datetime.utcnow()
        }

    @staticmethod
    async def generate_video(
        prompt: str,
        style: str = "cinematic",
        aspect_ratio: str = "16:9",
        duration: int = 5,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronously generates a video and returns its completed metadata and accessible URL"""
        settings.ensure_directories()
        job_id = str(uuid.uuid4())

        db = SessionLocal()
        try:
            job = VideoJob(
                id=job_id,
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio,
                duration=duration,
                status="pending",
                progress=5
            )
            db.add(job)
            db.commit()
        finally:
            db.close()

        # Execute video synthesis directly
        await VideoGenService._process_video_job(job_id, prompt, style, aspect_ratio, duration, image_url)

        # Retrieve completed job
        db = SessionLocal()
        try:
            completed_job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
            return {
                "job_id": completed_job.id,
                "status": completed_job.status,
                "video_url": completed_job.video_url,
                "file_path": completed_job.file_path,
                "prompt": completed_job.prompt,
                "style": completed_job.style,
                "aspect_ratio": completed_job.aspect_ratio,
                "duration": completed_job.duration,
                "error_message": completed_job.error_message
            }
        finally:
            db.close()

    @staticmethod
    async def _process_video_job(
        job_id: str,
        prompt: str,
        style: str,
        aspect_ratio: str,
        duration: int,
        image_url: Optional[str] = None
    ):
        """Background worker that synthesizes an actual playable MP4 video"""
        db = SessionLocal()
        try:
            job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
            if not job:
                return

            job.status = "processing"
            job.progress = 20
            db.commit()

            # Resolution configuration
            if aspect_ratio == "16:9":
                width, height = 1280, 720
            elif aspect_ratio == "9:16":
                width, height = 720, 1280
            else:
                width, height = 720, 720

            # Step 1: Resolve or synthesize keyframe image (Supports Image-to-Video and Text-to-Video)
            job.progress = 35
            db.commit()

            keyframe_path = None
            if image_url:
                ref_filename = image_url.split("/")[-1].split("?")[0]
                for cand in [
                    settings.UPLOAD_DIR / ref_filename,
                    settings.GENERATED_IMAGE_DIR / ref_filename,
                    Path(image_url) if os.path.isabs(image_url) else None
                ]:
                    if cand and cand.exists() and cand.is_file():
                        keyframe_path = cand
                        break

            if not keyframe_path:
                keyframe_res = await image_gen_service.generate_image(
                    prompt=prompt,
                    style=style,
                    aspect_ratio=aspect_ratio
                )
                keyframe_path = keyframe_res["file_path"]

            job.progress = 60
            db.commit()

            # Step 2: Render universal H.264 MP4 and WebM sequences via FFmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            timestamp_int = int(datetime.utcnow().timestamp())
            output_mp4_name = f"nexora_vid_{job_id[:8]}_{timestamp_int}.mp4"
            output_webm_name = f"nexora_vid_{job_id[:8]}_{timestamp_int}.webm"
            output_mp4_path = settings.GENERATED_VIDEO_DIR / output_mp4_name
            output_webm_path = settings.GENERATED_VIDEO_DIR / output_webm_name

            fps = 24
            total_frames = max(24, int(fps * duration))
            job.progress = 75
            db.commit()

            # Render 1: Universal H.264 MP4 (yuv420p + faststart)
            cmd_mp4 = [
                ffmpeg_exe, "-y", "-loop", "1", "-i", str(keyframe_path),
                "-t", str(duration),
                "-vf", f"scale={width}:{height},zoompan=z='min(zoom+0.0015,1.2)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-preset", "veryfast",
                str(output_mp4_path)
            ]
            subprocess.run(cmd_mp4, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Render 2: Universal WebM VP8
            cmd_webm = [
                ffmpeg_exe, "-y", "-loop", "1", "-i", str(keyframe_path),
                "-t", str(duration),
                "-vf", f"scale={width}:{height},zoompan=z='min(zoom+0.0015,1.2)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}",
                "-c:v", "libvpx", "-pix_fmt", "yuv420p",
                str(output_webm_path)
            ]
            try:
                subprocess.run(cmd_webm, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

            # Step 3: Complete job
            video_url = f"/storage/generated_videos/{output_mp4_name}"
            job.status = "completed"
            job.progress = 100
            job.file_path = str(output_mp4_path)
            job.video_url = video_url
            db.commit()

            # Register in GeneratedMedia
            media = GeneratedMedia(
                id=str(uuid.uuid4()),
                media_type="video",
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio,
                file_path=str(output_mp4_path),
                filename=output_mp4_name,
                provider="nexora-motion-engine",
                job_id=job_id,
                status="completed"
            )
            db.add(media)
            db.commit()

        except Exception as e:
            if job:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()
        finally:
            db.close()

    @staticmethod
    def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
        """Returns current status and video URL for a given job"""
        db = SessionLocal()
        try:
            job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
            if not job:
                return None
            return {
                "job_id": job.id,
                "status": job.status,
                "progress": job.progress,
                "video_url": job.video_url,
                "prompt": job.prompt,
                "error_message": job.error_message,
                "created_at": job.created_at,
                "updated_at": job.updated_at
            }
        finally:
            db.close()

video_gen_service = VideoGenService()

