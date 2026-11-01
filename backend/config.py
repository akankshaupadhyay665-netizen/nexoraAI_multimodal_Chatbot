"""
Nexora AI - Configuration Manager
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    PROJECT_NAME: str = "NEXORA AI"
    TAGLINE: str = "One Intelligence. Infinite Possibilities."
    VERSION: str = "1.0.0"
    
    # Server configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "5500"))
    FRONTEND_URL: str = f"http://127.0.0.1:{FRONTEND_PORT}"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'nexora.db'}")
    
    # Storage Paths
    UPLOAD_DIR: Path = BASE_DIR / "backend" / "storage" / "uploads"
    GENERATED_IMAGE_DIR: Path = BASE_DIR / "backend" / "storage" / "generated_images"
    GENERATED_VIDEO_DIR: Path = BASE_DIR / "backend" / "storage" / "generated_videos"
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    
    # Limits
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    ALLOWED_DOC_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/csv",
        "application/msword"
    }
    ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/mp4", "audio/x-m4a", "audio/webm", "audio/ogg"}
    ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}

    @classmethod
    def ensure_directories(cls):
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.GENERATED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        cls.GENERATED_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def update_gemini_key(cls, key: str):
        cls.GEMINI_API_KEY = key
        os.environ["GEMINI_API_KEY"] = key

    @classmethod
    def update_hf_key(cls, key: str):
        cls.HUGGINGFACE_API_KEY = key
        os.environ["HUGGINGFACE_API_KEY"] = key

settings = Settings()
settings.ensure_directories()

