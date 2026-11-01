import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import imageio_ffmpeg
import subprocess
from backend.services.image_gen_service import image_gen_service
import asyncio

async def heal_missing_videos():
    vid_dir = BASE_DIR / "backend" / "storage" / "generated_videos"
    img_dir = BASE_DIR / "backend" / "storage" / "generated_images"
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    target_webm = vid_dir / "nexora_vid_44a29910_1793445890.webm"
    target_mp4 = vid_dir / "nexora_vid_44a29910_1793445890.mp4"
    
    # 1. Generate keyframe for "a small girl in a sunny garden"
    print("Generating keyframe for small girl...")
    img_res = await image_gen_service.generate_image(
        prompt="a cute small girl in a sunny garden, photorealistic, smiling, cinematic lighting",
        style="photorealistic",
        aspect_ratio="16:9"
    )
    keyframe = img_res["file_path"]
    print("Keyframe generated:", keyframe)

    # 2. Render MP4 (H.264 yuv420p +faststart)
    cmd_mp4 = [
        ffmpeg_exe, "-y", "-loop", "1", "-i", str(keyframe),
        "-t", "5",
        "-vf", "scale=1280:720,zoompan=z='min(zoom+0.0015,1.2)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(target_mp4)
    ]
    subprocess.run(cmd_mp4, check=True)
    print("Rendered MP4:", target_mp4.stat().st_size, "bytes")

    # 3. Render WebM (VP8)
    cmd_webm = [
        ffmpeg_exe, "-y", "-loop", "1", "-i", str(keyframe),
        "-t", "5",
        "-vf", "scale=1280:720,zoompan=z='min(zoom+0.0015,1.2)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=24",
        "-c:v", "libvpx", "-pix_fmt", "yuv420p",
        str(target_webm)
    ]
    subprocess.run(cmd_webm, check=True)
    print("Rendered WebM:", target_webm.stat().st_size, "bytes")

if __name__ == "__main__":
    asyncio.run(heal_missing_videos())
