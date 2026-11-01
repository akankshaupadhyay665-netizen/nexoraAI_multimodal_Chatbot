"""
NEXORA AI - Main FastAPI Application
Tagline: "One Intelligence. Infinite Possibilities."
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import engine, Base
from backend.routers import chat, files, image_studio, video_studio, media, models_info, reports, settings as settings_router, web_media

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=f"{settings.TAGLINE} - Multimodal Multi-Model Generative AI Platform",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration for local cross-origin development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Ensure storage directories exist
settings.ensure_directories()

# Mount Static Directories for file downloads & media preview
storage_base = Path(settings.UPLOAD_DIR).parent
app.mount("/storage", StaticFiles(directory=str(storage_base)), name="storage")

# Include Routers
app.include_router(chat.router)
app.include_router(files.router)
app.include_router(image_studio.router)
app.include_router(video_studio.router)
app.include_router(media.router)
app.include_router(web_media.router)
app.include_router(models_info.router)
app.include_router(reports.router)
app.include_router(settings_router.router)

@app.get("/api/health")
def health_check():
    """Health check endpoint to verify backend status"""
    return {
        "status": "online",
        "platform": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "database": "sqlite_connected",
        "gemini_ready": bool(settings.GEMINI_API_KEY)
    }

@app.get("/")
def root():
    return {
        "platform": "NEXORA AI",
        "tagline": "One Intelligence. Infinite Possibilities.",
        "documentation": "/docs",
        "health": "/api/health",
        "api_endpoints": {
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "conversations": "/api/conversations",
            "files": "/api/files/upload",
            "image_generate": "/api/image/generate",
            "video_generate": "/api/video/generate",
            "media_gallery": "/api/media",
            "models": "/api/models",
            "settings": "/api/settings"
        }
    }

