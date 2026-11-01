import subprocess
import imageio_ffmpeg
from pathlib import Path

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
img_path = Path("backend/storage/generated_images/nexora_gen_8ada7a43_1793444941.png")
out_path = Path("tests/test_fast_h264.mp4")

# FFmpeg zoompan directly from keyframe image
cmd = [
    ffmpeg_exe,
    "-y",
    "-loop", "1",
    "-i", str(img_path),
    "-t", "5",
    "-vf", "scale=1280:720,zoompan=z='min(zoom+0.0015,1.2)':d=120:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps=24",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    str(out_path)
]

print("Running fast FFmpeg command...")
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
if out_path.exists():
    print(f"Generated {out_path}: {out_path.stat().st_size} bytes!")
else:
    print("Stderr:", res.stderr)

