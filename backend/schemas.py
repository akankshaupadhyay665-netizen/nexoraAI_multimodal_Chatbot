"""
Nexora AI - Pydantic Request & Response Schemas
"""
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

# Conversations
class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    model_used: Optional[str] = "gemini-flash-lite-latest"

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None

class MessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime
    model_name: Optional[str] = None
    status: Optional[str] = "completed"
    attachments: Optional[str] = None

class ConversationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    model_used: str
    is_pinned: bool
    messages: List[MessageSchema] = []

# Chat Request
class ChatMessageAttachment(BaseModel):
    id: Optional[str] = None
    name: str
    type: str  # 'image', 'document', 'audio', 'video'
    url: str
    extracted_text: Optional[str] = None

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    model: Optional[str] = "gemini-flash-lite-latest"
    attachments: Optional[List[ChatMessageAttachment]] = []
    stream: Optional[bool] = False
    system_instruction: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    user_message: MessageSchema
    assistant_message: MessageSchema
    model_used: str

# Image Studio
class ImageGenerateRequest(BaseModel):
    prompt: str
    style: Optional[str] = "photorealistic"
    aspect_ratio: Optional[str] = "1:1"  # '1:1', '16:9', '9:16', '4:3'
    quantity: Optional[int] = 1 # 1 to 4 images
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    model: Optional[str] = "flux"

class ImageEditRequest(BaseModel):
    prompt: str
    image_url: str
    instruction: Optional[str] = None
    style: Optional[str] = "photorealistic"

class ImageGenerateResponse(BaseModel):
    id: str
    image_url: str
    prompt: str
    style: str
    aspect_ratio: str
    provider: str
    created_at: datetime

# Video Studio
class VideoGenerateRequest(BaseModel):
    prompt: str
    style: Optional[str] = "cinematic"
    aspect_ratio: Optional[str] = "16:9"
    duration: Optional[int] = 5
    image_url: Optional[str] = None

class VideoJobResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    video_url: Optional[str] = None
    prompt: str
    error_message: Optional[str] = None
    created_at: datetime

# Files
class FileUploadResponse(BaseModel):
    id: str
    original_name: str
    file_type: str
    mime_type: str
    file_size: int
    file_url: str
    extracted_text: Optional[str] = None

# Settings
class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None

class SettingsResponse(BaseModel):
    gemini_configured: bool
    huggingface_configured: bool
    model_list: List[Dict[str, Any]]

# Web & URL Media Schemas
class UrlInfoRequest(BaseModel):
    url: str

class UrlInfoResponse(BaseModel):
    success: bool
    type: str  # 'youtube', 'direct_video', 'vimeo', 'image', 'webpage'
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    embed_url: Optional[str] = None
    image: Optional[str] = None
    has_transcript: Optional[bool] = False
    transcript_text: Optional[str] = None
    transcript_segments: Optional[List[Dict[str, Any]]] = None
    is_hls: Optional[bool] = False
    error: Optional[str] = None

