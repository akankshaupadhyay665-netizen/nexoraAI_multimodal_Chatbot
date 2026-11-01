"""
NEXORA AI - Web Media & URL Intelligence Router
Provides endpoints to inspect URLs (YouTube, Direct Video, Open Graph, Webpages)
and stream safe media previews.
"""
from fastapi import APIRouter, HTTPException, Query, Response
import httpx

from backend.schemas import UrlInfoRequest
from backend.services.web_media_service import web_media_service

router = APIRouter(prefix="/api/media", tags=["web-media"])

@router.post("/url-info")
async def inspect_url(req: UrlInfoRequest):
    """
    Inspects any URL to extract metadata, YouTube transcripts,
    direct video stream formats, or Open Graph web previews.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    if not web_media_service.is_safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid or restricted URL (Private IP addresses blocked)")

    info = await web_media_service.inspect_url(url)
    return info

@router.get("/proxy-image")
async def proxy_image(url: str = Query(..., description="Target image URL to proxy safely")):
    """
    Proxies remote image bytes safely to avoid CORS issues and SSRF exploits.
    """
    if not web_media_service.is_safe_url(url):
        raise HTTPException(status_code=400, detail="Restricted URL")

    image_bytes = await web_media_service.fetch_image_bytes(url)
    if not image_bytes:
        raise HTTPException(status_code=404, detail="Image could not be retrieved")

    # Determine basic mime type
    lower = url.lower()
    media_type = "image/jpeg"
    if lower.endswith(".png"):
        media_type = "image/png"
    elif lower.endswith(".webp"):
        media_type = "image/webp"
    elif lower.endswith(".gif"):
        media_type = "image/gif"
    elif lower.endswith(".svg"):
        media_type = "image/svg+xml"

    return Response(content=image_bytes, media_type=media_type)

