"""
Nexora AI - AI Service Routing & Multimodal Mock Tests
"""
import asyncio
from backend.services.ai_service import ai_service

def test_ai_service_models_list():
    """Verify AI model catalog schema and defaults"""
    models = ai_service.get_available_models()
    assert len(models) >= 4
    default_model = next((m for m in models if m.get("is_default")), None)
    assert default_model is not None
    assert default_model["id"] == "gemini-flash-lite-latest"

def test_ai_fallback_code_response():
    """Verify intelligent fallback for code questions"""
    res = asyncio.run(ai_service.generate_response(
        prompt="Write a python function to compute fibonacci sequence",
        model_name="gemini-flash-lite-latest"
    ))
    assert "```python" in res
    assert "def " in res or "asyncio" in res or "fibonacci" in res

def test_ai_fallback_document_response():
    """Verify intelligent fallback when document attachment is provided"""
    attachments = [{
        "name": "research_paper.pdf",
        "type": "document",
        "url": "/storage/uploads/paper.pdf",
        "extracted_text": "Executive Summary: The neural network achieved 98.4% accuracy across benchmarks."
    }]
    res = asyncio.run(ai_service.generate_response(
        prompt="Summarize the attached research paper",
        attachments=attachments,
        model_name="gemini-flash-lite-latest"
    ))
    assert "Document Analysis" in res or "research_paper" in res or "98.4%" in res
