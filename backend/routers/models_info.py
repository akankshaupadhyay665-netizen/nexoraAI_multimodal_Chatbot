"""
Nexora AI - AI Models & Capabilities Router
"""
from typing import List, Dict, Any
from fastapi import APIRouter
from backend.services.ai_service import ai_service

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("", response_model=List[Dict[str, Any]])
def get_models():
    """Returns catalog of integrated AI models, provider information, and active capabilities"""
    return ai_service.get_available_models()

