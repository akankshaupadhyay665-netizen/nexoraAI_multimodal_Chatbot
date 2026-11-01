"""
Nexora AI - Chat & Conversation Router
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import re
from backend.config import settings
from backend.database import get_db
from backend.models import Conversation, Message
from backend.schemas import (
    ChatRequest, ChatResponse, ConversationSchema, 
    ConversationCreate, ConversationUpdate, MessageSchema
)
from backend.services.ai_service import ai_service
from backend.services.image_gen_service import image_gen_service
from backend.services.video_gen_service import video_gen_service
from backend.services.web_media_service import web_media_service

router = APIRouter(prefix="/api", tags=["chat"])

def detect_video_generation_intent(prompt: str, model_name: Optional[str] = None) -> Optional[dict]:
    """
    Detects whether user prompt explicitly requests generative video synthesis.
    Returns parsed intent dictionary or None for standard conversational queries.
    """
    clean = prompt.strip()
    lower = clean.lower()

    if model_name == "nexora-motion-engine":
        return {"prompt": clean, "style": "cinematic", "aspect_ratio": "16:9", "duration": 5}

    if lower.startswith("explain") or lower.startswith("why ") or lower.startswith("what is") or lower.startswith("how "):
        return None

    video_triggers = [
        "generate the video of", "generate the video", "generate a video of", "generate a video",
        "generate video of", "generate video", "create the video of", "create a video of",
        "create a video", "create video of", "create video", "make a video of", "make a video",
        "make video of", "make video", "render a video of", "render a video", "render video",
        "synthesize a video", "synthesize video", "video of", "/video"
    ]

    is_video = any(t in lower for t in video_triggers)
    if not is_video:
        return None

    # Extract clean subject
    subject = clean
    for t in [
        "generate the video of", "generate a video of", "generate video of",
        "create the video of", "create a video of", "create video of",
        "make the video of", "make a video of", "make video of",
        "render a video of", "render video of", "synthesize a video of",
        "generate the video", "generate a video", "generate video",
        "create a video", "create video", "make a video", "make video",
        "/video"
    ]:
        if t in lower:
            idx = lower.find(t) + len(t)
            extracted = clean[idx:].strip()
            if extracted:
                subject = extracted
            break

    # Determine motion style
    style = "cinematic"
    if "realistic" in lower or "natural" in lower:
        style = "realistic"
    elif "animated" in lower or "cartoon" in lower or "anime" in lower or "sci-fi" in lower:
        style = "animated"

    # Determine aspect ratio
    aspect_ratio = "16:9"
    if "9:16" in lower or "vertical" in lower or "reel" in lower or "tiktok" in lower or "shorts" in lower:
        aspect_ratio = "9:16"
    elif "1:1" in lower or "square" in lower:
        aspect_ratio = "1:1"

    # Determine duration
    duration = 5
    if "10" in lower or "ten" in lower:
        duration = 10
    elif "3" in lower or "three" in lower:
        duration = 3

    return {"prompt": subject, "style": style, "aspect_ratio": aspect_ratio, "duration": duration}

def detect_image_generation_intent(prompt: str, model_name: Optional[str] = None) -> Optional[dict]:
    """
    Detects whether user prompt explicitly requests generative image synthesis.
    Returns parsed intent dictionary or None for standard conversational queries.
    """
    clean = prompt.strip()
    lower = clean.lower()

    if model_name == "pollinations-flux":
        return {"prompt": clean, "style": "photorealistic", "aspect_ratio": "1:1"}

    # Exclude explanations or standard queries
    if lower.startswith("explain") or lower.startswith("why ") or lower.startswith("what is") or lower.startswith("how "):
        return None

    # Check for direct image triggers
    triggers = [
        "generate an image", "generate image", "create an image", "create image",
        "make an image", "draw an image", "draw a picture", "paint an image",
        "generate a photo", "generate a photorealistic image", "generate photo",
        "create a photo", "create a picture", "generate a picture",
        "render an image", "image of", "photo of", "picture of",
        "/image", "/imagine"
    ]

    is_image = any(t in lower for t in triggers)
    if not is_image:
        return None

    # Extract subject
    subject = clean
    for t in ["generate a photorealistic image of", "generate an image of", "generate image of", 
              "create an image of", "create a photo of", "generate a photo of", "generate a picture of",
              "create a picture of", "draw an image of", "paint an image of", "render an image of",
              "/image", "/imagine"]:
        if t in lower:
            idx = lower.find(t) + len(t)
            extracted = clean[idx:].strip()
            if extracted:
                subject = extracted
            break

    # Determine style
    style = "photorealistic"
    for st in ["cinematic", "anime", "cartoon", "3d", "digital art", "watercolor", "fantasy", "minimalist"]:
        if st in lower:
            style = st
            break

    # Determine aspect ratio
    aspect_ratio = "1:1"
    if "16:9" in lower or "widescreen" in lower or "landscape" in lower:
        aspect_ratio = "16:9"
    elif "9:16" in lower or "vertical" in lower or "portrait" in lower:
        aspect_ratio = "9:16"
    elif "4:3" in lower:
        aspect_ratio = "4:3"

    return {"prompt": subject, "style": style, "aspect_ratio": aspect_ratio}

@router.get("/conversations", response_model=List[ConversationSchema])
def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists conversations sorted by updated_at descending"""
    convs = db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(limit).all()
    return convs

@router.post("/conversations", response_model=ConversationSchema)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db)
):
    """Creates a new conversation thread"""
    conv = Conversation(
        id=str(uuid.uuid4()),
        title=payload.title or "New Conversation",
        model_used=payload.model_used or "gemini-flash-lite-latest"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves a single conversation by ID with all messages"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.put("/conversations/{conversation_id}", response_model=ConversationSchema)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """Updates title or pinned status of a conversation"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if payload.title is not None:
        conv.title = payload.title
    if payload.is_pinned is not None:
        conv.is_pinned = payload.is_pinned
    
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conv)
    return conv

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Deletes a conversation and its messages"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"status": "deleted", "conversation_id": conversation_id}

@router.delete("/conversations")
def clear_all_conversations(db: Session = Depends(get_db)):
    """Clears all conversation history"""
    db.query(Message).delete()
    db.query(Conversation).delete()
    db.commit()
    return {"status": "all_cleared"}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db)
):
    """Synchronous chat endpoint with conversation memory and multimodal support"""
    # 1. Resolve or create conversation
    conv_id = req.conversation_id
    conv = None
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    
    if not conv:
        # Generate initial title from first 30 chars of message
        title_summary = req.message.strip()[:35] or "New Conversation"
        conv = Conversation(
            id=str(uuid.uuid4()),
            title=title_summary,
            model_used=req.model or "gemini-flash-lite-latest"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id

    # 2. Save user message
    attachments_json = json.dumps([a.dict() for a in req.attachments]) if req.attachments else None
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=req.message,
        model_name=req.model,
        attachments=attachments_json,
        status="completed"
    )
    db.add(user_msg)
    db.commit()

    # 3. Fetch recent history
    recent_msgs = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at.desc()).limit(8).all()
    recent_msgs.reverse()

    history = [{"role": m.role, "content": m.content} for m in recent_msgs if m.id != user_msg.id]

    clean_lower = req.message.strip().lower()

    # Special handling for "video is not working" / "video not playing"
    if any(k in clean_lower for k in ["video is not working", "video not working", "video not playing", "video isn't playing", "video is not opening", "video not opening", "video not generating"]):
        # Find last subject from conversation history
        last_subject = "cinematic scene"
        for m in reversed(history):
            if m["role"] == "user" and not any(k in m["content"].lower() for k in ["working", "not playing", "help"]):
                last_subject = m["content"].strip()
                break
        
        # Strip generation commands from subject
        for prefix in ["generate video of", "generate the video of", "generate a video of", "create video of", "make video of"]:
            if last_subject.lower().startswith(prefix):
                last_subject = last_subject[len(prefix):].strip()
                break

        vid_result = await video_gen_service.generate_video(prompt=last_subject)
        video_url = vid_result["video_url"]
        webm_url = video_url.replace(".mp4", ".webm")
        ai_content = (
            f"### 🎬 Video Regenerated in Universal MP4 Format\n\n"
            f"I have re-rendered the video for **\"{last_subject}\"** using our **Universal H.264 MP4 Engine**.\n\n"
            f"- **Format**: `H.264 MP4 (Web Compatible)`\n"
            f"- **Resolution**: `1280x720 HD`\n"
            f"- **Duration**: `5 seconds`\n"
            f"- **Engine**: `Nexora Motion Studio (FFmpeg AVC)`\n\n"
            f"<video controls autoplay loop muted playsinline style=\"width: 100%; max-width: 680px; border-radius: 12px; margin: 12px 0; background: #000;\"><source src=\"{video_url}\" type=\"video/mp4\"><source src=\"{webm_url}\" type=\"video/webm\">Your browser does not support HTML5 video.</video>\n\n"
            f"*(You can play it directly above or download it with the button below).*"
        )
        asst_attachments = [{
            "id": vid_result["job_id"],
            "name": f"Generated_{last_subject[:24].replace(' ', '_')}.mp4",
            "type": "video",
            "url": video_url
        }]
        assistant_attachments_json = json.dumps(asst_attachments)
        video_intent = None
        image_intent = None
    else:
        # 4. Check for Video or Image Generation Intent
        found_urls = web_media_service.extract_urls(req.message)
        video_intent = detect_video_generation_intent(req.message, req.model)

        # Contextual check: Only for actual prompt subjects in a video thread if no URLs and not a conversational command
        if not video_intent and not found_urls and any("video" in m.get("content", "").lower() for m in history[-2:]):
            conversational_starters = ("what", "who", "where", "how", "why", "can", "is", "tell", "show", "read", "summarize", "check", "open", "please", "help")
            if len(clean_lower.split()) <= 6 and not clean_lower.startswith(conversational_starters):
                video_intent = {"prompt": req.message.strip(), "style": "cinematic", "aspect_ratio": "16:9", "duration": 5}

        image_intent = None if (video_intent or found_urls) else detect_image_generation_intent(req.message, req.model)
        assistant_attachments_json = None

    if video_intent:
        # Route directly to dedicated Video Generation Pipeline
        vid_result = await video_gen_service.generate_video(
            prompt=video_intent["prompt"],
            style=video_intent["style"],
            aspect_ratio=video_intent["aspect_ratio"],
            duration=video_intent["duration"]
        )
        video_url = vid_result["video_url"]
        webm_url = video_url.replace(".mp4", ".webm")
        ai_content = (
            f"### 🎬 Generated Video\n\n"
            f"Here is the generated cinematic video for your prompt: **\"{video_intent['prompt']}\"**\n\n"
            f"- **Style**: `{vid_result['style'].capitalize()}`\n"
            f"- **Duration**: `{vid_result['duration']} seconds`\n"
            f"- **Aspect Ratio**: `{vid_result['aspect_ratio']}`\n"
            f"- **Engine**: `Nexora Motion Engine (Universal H.264 MP4)`\n\n"
            f"<video controls autoplay loop muted playsinline style=\"width: 100%; max-width: 680px; border-radius: 12px; margin: 12px 0; background: #000;\"><source src=\"{video_url}\" type=\"video/mp4\"><source src=\"{webm_url}\" type=\"video/webm\">Your browser does not support HTML5 video.</video>\n\n"
            f"*(Download using the controls below, or access anytime in the **Video Generator** studio).*"
        )
        asst_attachments = [{
            "id": vid_result["job_id"],
            "name": f"Generated_{video_intent['prompt'][:24].replace(' ', '_')}.mp4",
            "type": "video",
            "url": video_url
        }]
        assistant_attachments_json = json.dumps(asst_attachments)
    elif image_intent:
        # Route directly to dedicated Image Generation Pipeline
        img_result = await image_gen_service.generate_image(
            prompt=image_intent["prompt"],
            style=image_intent["style"],
            aspect_ratio=image_intent["aspect_ratio"]
        )
        ai_content = (
            f"### 🎨 Generated Artwork\n\n"
            f"Here is the generated image for your prompt: **\"{image_intent['prompt']}\"**\n\n"
            f"- **Style**: `{img_result['style'].capitalize()}`\n"
            f"- **Aspect Ratio**: `{img_result['aspect_ratio']}`\n"
            f"- **Engine**: `{img_result['provider']}`\n\n"
            f"![{image_intent['prompt']}]({img_result['image_url']})\n\n"
            f"*(Download or regenerate using the controls below, or access anytime in the **Generated Media** gallery).*"
        )
        asst_attachments = [{
            "id": img_result["id"],
            "name": f"Generated_{image_intent['prompt'][:24]}.png",
            "type": "image",
            "url": img_result["image_url"]
        }]
        assistant_attachments_json = json.dumps(asst_attachments)
    elif assistant_attachments_json is None:
        # Route to Text Multimodal Conversational Engine
        attachments_list = [a.dict() for a in req.attachments] if req.attachments else []

        # Automatic Web, YouTube, Direct Video & Image URL Inspection
        found_urls = web_media_service.extract_urls(req.message)
        extracted_media_attachments = []
        for u in found_urls[:4]:  # limit to 4 URLs per message
            try:
                media_info = await web_media_service.inspect_url(u)
                if media_info.get("success"):
                    m_type = media_info.get("type")
                    if m_type == "youtube":
                        att_dict = {
                            "id": f"yt_{media_info['video_id']}",
                            "name": media_info.get("title", "YouTube Video"),
                            "type": "youtube",
                            "url": u,
                            "video_id": media_info["video_id"],
                            "embed_url": media_info["embed_url"],
                            "thumbnail": media_info.get("thumbnail_url"),
                            "author": media_info.get("author"),
                            "has_transcript": media_info.get("has_transcript", False),
                            "transcript_text": media_info.get("transcript_text", ""),
                            "transcript_segments": media_info.get("transcript_segments", [])
                        }
                        attachments_list.append(att_dict)
                        extracted_media_attachments.append(att_dict)
                    elif m_type == "direct_video":
                        att_dict = {
                            "id": f"vid_{uuid.uuid4().hex[:8]}",
                            "name": media_info.get("title", "Direct Video Stream"),
                            "type": "direct_video",
                            "url": u,
                            "format": media_info.get("format", "mp4"),
                            "is_hls": media_info.get("is_hls", False)
                        }
                        attachments_list.append(att_dict)
                        extracted_media_attachments.append(att_dict)
                    elif m_type == "vimeo":
                        att_dict = {
                            "id": f"vimeo_{uuid.uuid4().hex[:8]}",
                            "name": media_info.get("title", "Vimeo Video"),
                            "type": "vimeo",
                            "url": u,
                            "embed_url": media_info.get("embed_url"),
                            "thumbnail": media_info.get("thumbnail_url"),
                            "author": media_info.get("author")
                        }
                        attachments_list.append(att_dict)
                        extracted_media_attachments.append(att_dict)
                    elif m_type == "image":
                        att_dict = {
                            "id": f"img_{uuid.uuid4().hex[:8]}",
                            "name": media_info.get("title", "Web Image"),
                            "type": "image",
                            "url": u
                        }
                        attachments_list.append(att_dict)
                        extracted_media_attachments.append(att_dict)
                    elif m_type == "webpage":
                        att_dict = {
                            "id": f"web_{uuid.uuid4().hex[:8]}",
                            "name": media_info.get("title", "Web Page"),
                            "type": "webpage",
                            "url": u,
                            "description": media_info.get("description", ""),
                            "image": media_info.get("image", ""),
                            "favicon": media_info.get("favicon", ""),
                            "readable_text": media_info.get("readable_text", "")
                        }
                        attachments_list.append(att_dict)
                        extracted_media_attachments.append(att_dict)
            except Exception:
                pass

        ai_content = await ai_service.generate_response(
            prompt=req.message,
            conversation_history=history,
            attachments=attachments_list,
            model_name=req.model or "gemini-flash-lite-latest",
            system_instruction=req.system_instruction
        )

        if extracted_media_attachments:
            assistant_attachments_json = json.dumps(extracted_media_attachments)

        # Defensive Media Healer: Ensure any /storage/ video URL hallucinated by LLM is synthesized!
        vid_matches = re.findall(r'/storage/generated_videos/([a-zA-Z0-9_\-\.]+)', ai_content)
        for filename in vid_matches:
            disk_path = settings.GENERATED_VIDEO_DIR / filename
            if not disk_path.exists():
                heal_res = await video_gen_service.generate_video(prompt=req.message)
                real_url = heal_res["video_url"]
                ai_content = ai_content.replace(f"/storage/generated_videos/{filename}", real_url)
                asst_attachments = [{
                    "id": heal_res["job_id"],
                    "name": f"Generated_{req.message[:24].replace(' ', '_')}.mp4",
                    "type": "video",
                    "url": real_url
                }]
                assistant_attachments_json = json.dumps(asst_attachments)

        # Convert any markdown image syntax pointing to a video into an HTML5 <video> tag
        ai_content = re.sub(
            r'!\[(.*?)\]\((.*?/storage/generated_videos/[^\s\)]+)\)',
            r'<video controls autoplay loop muted playsinline style="width: 100%; max-width: 680px; border-radius: 12px; margin: 12px 0; background: #000;"><source src="\2" type="video/mp4"></video>',
            ai_content
        )
        ai_content = re.sub(
            r'!\[(.*?)\]\(((?:http://127\.0\.0\.1:8000)?/storage/[^\s\)]+\.(?:mp4|webm))\)',
            r'<video controls autoplay loop muted playsinline style="width: 100%; max-width: 680px; border-radius: 12px; margin: 12px 0; background: #000;"><source src="\2" type="video/mp4"></video>',
            ai_content
        )

    # 5. Save assistant message
    asst_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content=ai_content,
        model_name=req.model or "gemini-flash-lite-latest",
        attachments=assistant_attachments_json,
        status="completed"
    )
    db.add(asst_msg)
    
    # Update conversation timestamp & model
    conv.updated_at = datetime.utcnow()
    conv.model_used = req.model or conv.model_used
    db.commit()
    db.refresh(user_msg)
    db.refresh(asst_msg)

    return ChatResponse(
        conversation_id=conv_id,
        user_message=MessageSchema.model_validate(user_msg),
        assistant_message=MessageSchema.model_validate(asst_msg),
        model_used=req.model or "gemini-flash-lite-latest"
    )

@router.post("/chat/stream")
async def chat_stream_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db)
):
    """Server-Sent Events (SSE) streaming chat endpoint"""
    conv_id = req.conversation_id
    conv = None
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    
    if not conv:
        conv = Conversation(
            id=str(uuid.uuid4()),
            title=req.message.strip()[:35] or "New Conversation",
            model_used=req.model or "gemini-2.5-flash"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id

    # Save user message
    attachments_json = json.dumps([a.dict() for a in req.attachments]) if req.attachments else None
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=req.message,
        model_name=req.model,
        attachments=attachments_json
    )
    db.add(user_msg)
    db.commit()

    # Pre-create assistant message placeholder
    asst_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content="",
        model_name=req.model,
        status="generating"
    )
    db.add(asst_msg)
    db.commit()

    async def sse_event_generator():
        accumulated_chunks = []
        try:
            attachments_list = [a.dict() for a in req.attachments] if req.attachments else []
            
            # Send initial event with conversation and message IDs
            yield f"data: {json.dumps({'event': 'start', 'conversation_id': conv_id, 'message_id': asst_msg.id})}\n\n"

            async for chunk in ai_service.generate_streaming_response(
                prompt=req.message,
                attachments=attachments_list,
                model_name=req.model or "gemini-flash-lite-latest"
            ):
                accumulated_chunks.append(chunk)
                payload = json.dumps({"event": "chunk", "content": chunk})
                yield f"data: {payload}\n\n"

            # Finalize message in DB
            final_content = "".join(accumulated_chunks)
            sub_db = next(get_db())
            msg_to_update = sub_db.query(Message).filter(Message.id == asst_msg.id).first()
            if msg_to_update:
                msg_to_update.content = final_content
                msg_to_update.status = "completed"
                sub_db.commit()

            yield f"data: {json.dumps({'event': 'done', 'final_content': final_content})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")

@router.post("/messages/{message_id}/regenerate", response_model=ChatResponse)
async def regenerate_message(
    message_id: str,
    db: Session = Depends(get_db)
):
    """Regenerates response for the last user prompt in conversation"""
    target_msg = db.query(Message).filter(Message.id == message_id).first()
    if not target_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    conv_id = target_msg.conversation_id
    # Find the preceding user message
    user_msg = db.query(Message).filter(
        Message.conversation_id == conv_id,
        Message.role == "user",
        Message.created_at <= target_msg.created_at
    ).order_by(Message.created_at.desc()).first()

    if not user_msg:
        raise HTTPException(status_code=400, detail="No preceding user message to regenerate from")

    new_content = await ai_service.generate_response(
        prompt=user_msg.content,
        model_name=target_msg.model_name or "gemini-flash-lite-latest"
    )

    target_msg.content = new_content
    target_msg.created_at = datetime.utcnow()
    db.commit()
    db.refresh(target_msg)

    return ChatResponse(
        conversation_id=conv_id,
        user_message=MessageSchema.model_validate(user_msg),
        assistant_message=MessageSchema.model_validate(target_msg),
        model_used=target_msg.model_name or "gemini-flash-lite-latest"
    )

