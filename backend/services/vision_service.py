"""
Nexora AI - Vision & Multimodal Image Analysis Service
"""
import base64
from pathlib import Path
from typing import Dict, Any
from PIL import Image

class VisionService:
    @staticmethod
    def inspect_image(image_path: str) -> Dict[str, Any]:
        """Analyzes image dimensions, format, color mode and metadata"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with Image.open(path) as img:
            width, height = img.size
            format_name = img.format or path.suffix.replace(".", "").upper()
            mode = img.mode

        return {
            "filename": path.name,
            "width": width,
            "height": height,
            "aspect_ratio": f"{width}:{height}",
            "format": format_name,
            "mode": mode,
            "size_kb": round(path.stat().st_size / 1024, 2)
        }

    @staticmethod
    def get_base64_encoded(image_path: str) -> str:
        """Returns base64 encoded string of image for API payload"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

vision_service = VisionService()

