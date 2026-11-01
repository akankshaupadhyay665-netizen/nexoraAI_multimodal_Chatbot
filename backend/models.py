"""
Nexora AI - SQLAlchemy Database Models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship

from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    model_used = Column(String(100), default="gemini-2.5-flash")
    is_pinned = Column(Boolean, default=False)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    files = relationship("UploadedFile", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    model_name = Column(String(100), nullable=True)
    status = Column(String(20), default="completed")
    attachments = Column(Text, nullable=True)  # JSON-encoded metadata of attached files

    conversation = relationship("Conversation", back_populates="messages")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    original_name = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'image', 'document', 'audio', 'video'
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="files")

class GeneratedMedia(Base):
    __tablename__ = "generated_media"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    media_type = Column(String(20), nullable=False)  # 'image', 'video'
    prompt = Column(Text, nullable=False)
    style = Column(String(50), nullable=True)
    aspect_ratio = Column(String(20), nullable=True)
    file_path = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    provider = Column(String(50), default="pollinations-flux")
    job_id = Column(String(100), nullable=True)
    status = Column(String(20), default="completed")
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prompt = Column(Text, nullable=False)
    style = Column(String(50), nullable=True, default="cinematic")
    aspect_ratio = Column(String(20), nullable=True, default="16:9")
    duration = Column(Integer, default=5)
    status = Column(String(20), default="pending")  # 'pending', 'processing', 'completed', 'failed'
    progress = Column(Integer, default=0)
    file_path = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

