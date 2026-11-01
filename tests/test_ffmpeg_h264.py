import subprocess
import imageio_ffmpeg
from pathlib import Path

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
print("Using FFmpeg:", ffmpeg_exe)

# Create a test 5s mp4 with h264 yuv420p from color pattern
cmd = [
    ffmpeg_exe,
    "-y",
    "-f", "lavfi",
    "-i", "testsrc=size=1280x720:rate=24",
    "-t", "5",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    "tests/test_h264_perfect.mp4"
]

res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
p = Path("tests/test_h264_perfect.mp4")
print(f"Generated test_h264_perfect.mp4: exists={p.exists()}, size={p.stat().st_size if p.exists() else 0}")

