import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from PIL import Image
from backend.services.image_gen_service import image_gen_service

async def main():
    print("Testing 16:9 cinematic lion generation...")
    res = await image_gen_service.generate_image(
        prompt="generate the image of lion",
        style="cinematic",
        aspect_ratio="16:9"
    )
    print("ID:", res["id"])
    print("Provider:", res["provider"])
    print("URL:", res["file_url"])
    im = Image.open(res["file_path"])
    print(f"Verified resolution: {im.size} (expected 1280x720)")
    assert im.size == (1280, 720), f"Expected (1280, 720) but got {im.size}"
    print("SUCCESS: 16:9 image generated and fitted perfectly!")

if __name__ == "__main__":
    asyncio.run(main())
