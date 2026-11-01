"""
Nexora AI - AI Image Studio Router
"""
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import GeneratedMedia
from backend.schemas import ImageGenerateRequest, ImageEditRequest, ImageGenerateResponse
from backend.services.image_gen_service import image_gen_service, STYLE_PROMPTS

router = APIRouter(prefix="/api/image", tags=["image-studio"])

@router.get("/styles")
def get_available_styles() -> Dict[str, str]:
    """Returns available artistic rendering styles and prompt enhancers"""
    return STYLE_PROMPTS

@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(
    req: ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generates a real AI image via Pollinations Flux generative model"""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        result = await image_gen_service.generate_image(
            prompt=req.prompt,
            style=req.style or "photorealistic",
            aspect_ratio=req.aspect_ratio or "1:1",
            negative_prompt=req.negative_prompt,
            seed=req.seed,
            model=req.model or "flux",
            db=db
        )

        return ImageGenerateResponse(
            id=result["id"],
            image_url=result["image_url"],
            prompt=result["prompt"],
            style=result["style"],
            aspect_ratio=result["aspect_ratio"],
            provider=result["provider"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@router.post("/generate-batch", response_model=List[ImageGenerateResponse])
async def generate_image_batch(
    req: ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generates multiple unique image variations (1 to 4 images) in one batch request"""
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    count = max(1, min(4, req.quantity or 1))
    results = []

    for i in range(count):
        sub_seed = (req.seed or 1000) + (i * 1337)
        try:
            res = await image_gen_service.generate_image(
                prompt=req.prompt,
                style=req.style or "photorealistic",
                aspect_ratio=req.aspect_ratio or "1:1",
                negative_prompt=req.negative_prompt,
                seed=sub_seed,
                model=req.model or "flux",
                db=db
            )
            results.append(ImageGenerateResponse(
                id=res["id"],
                image_url=res["image_url"],
                prompt=res["prompt"],
                style=res["style"],
                aspect_ratio=res["aspect_ratio"],
                provider=res["provider"],
                created_at=res["created_at"]
            ))
        except Exception as err:
            if not results:
                raise HTTPException(status_code=500, detail=f"Batch generation failed on item {i+1}: {str(err)}")
            break

    return results

@router.post("/edit", response_model=ImageGenerateResponse)
async def edit_image(
    req: ImageEditRequest,
    db: Session = Depends(get_db)
):
    """Creates an AI-guided variation or modification of a reference image"""
    try:
        result = await image_gen_service.edit_image(
            prompt=req.prompt,
            image_url=req.image_url,
            instruction=req.instruction,
            style=req.style or "photorealistic",
            db=db
        )

        return ImageGenerateResponse(
            id=result["id"],
            image_url=result["image_url"],
            prompt=result["prompt"],
            style=result["style"],
            aspect_ratio=result["aspect_ratio"],
            provider=result["provider"],
            created_at=result["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image edit failed: {str(e)}")

