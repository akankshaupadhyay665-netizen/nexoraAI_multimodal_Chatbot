"""
Nexora AI - Settings & Provider Credentials Router
"""
import os
from fastapi import APIRouter
from backend.config import settings, ENV_PATH
from backend.schemas import SettingsUpdateRequest, SettingsResponse
from backend.services.ai_service import ai_service

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("", response_model=SettingsResponse)
def get_settings():
    """Returns provider connectivity status and model catalog"""
    has_gemini = bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)
    has_hf = bool(settings.HUGGINGFACE_API_KEY and len(settings.HUGGINGFACE_API_KEY.strip()) > 5)
    
    return SettingsResponse(
        gemini_configured=has_gemini,
        huggingface_configured=has_hf,
        model_list=ai_service.get_available_models()
    )

@router.post("")
def update_settings(payload: SettingsUpdateRequest):
    """Updates API credentials dynamically in memory and persists to local .env"""
    updated = {}
    if payload.gemini_api_key is not None:
        key = payload.gemini_api_key.strip()
        settings.update_gemini_key(key)
        updated["gemini"] = True

    if payload.huggingface_api_key is not None:
        hf = payload.huggingface_api_key.strip()
        settings.update_hf_key(hf)
        updated["huggingface"] = True

    # Persist into .env if present
    try:
        if ENV_PATH.exists():
            lines = []
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            new_lines = []
            gemini_written = False
            hf_written = False

            for line in lines:
                if line.startswith("GEMINI_API_KEY="):
                    new_lines.append(f"GEMINI_API_KEY={settings.GEMINI_API_KEY}\n")
                    gemini_written = True
                elif line.startswith("HUGGINGFACE_API_KEY="):
                    new_lines.append(f"HUGGINGFACE_API_KEY={settings.HUGGINGFACE_API_KEY}\n")
                    hf_written = True
                else:
                    new_lines.append(line)

            if not gemini_written:
                new_lines.append(f"GEMINI_API_KEY={settings.GEMINI_API_KEY}\n")
            if not hf_written:
                new_lines.append(f"HUGGINGFACE_API_KEY={settings.HUGGINGFACE_API_KEY}\n")

            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
    except Exception:
        pass

    return {
        "status": "success",
        "updated": updated,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "huggingface_configured": bool(settings.HUGGINGFACE_API_KEY)
    }

@router.post("/test-connection")
async def test_connection():
    """Tests the configured Google Gemini API key by making a lightweight model ping"""
    if not settings.GEMINI_API_KEY or len(settings.GEMINI_API_KEY.strip()) < 5:
        return {"success": False, "message": "No Gemini API key configured. Enter your key and save first."}

    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Ping"
        )
        return {"success": True, "message": "Google Gemini 2.5 Flash connected & verified successfully!"}
    except Exception as e:
        return {"success": False, "message": f"Connection test failed: {str(e)}"}


