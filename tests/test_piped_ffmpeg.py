import subprocess
import imageio_ffmpeg
import numpy as np
import cv2
from pathlib import Path

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
width, height = 1280, 720
fps = 24
duration = 5
total_frames = fps * duration

cmd = [
    ffmpeg_exe,
    "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{width}x{height}",
    "-pix_fmt", "bgr24",
    "-r", str(fps),
    "-i", "-",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    "-crf", "22",
    "-preset", "veryfast",
    "tests/test_piped_h264.mp4"
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Feed 120 frames
canvas = np.zeros((height, width, 3), dtype=np.uint8)
for i in range(total_frames):
    canvas[:, :, 0] = int(i * 2) % 255
    canvas[:, :, 1] = int(i * 3) % 255
    canvas[:, :, 2] = 200
    cv2.putText(canvas, f"Frame {i}/{total_frames}", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    proc.stdin.write(canvas.tobytes())

proc.stdin.close()
proc.wait()

p = Path("tests/test_piped_h264.mp4")
print(f"Generated test_piped_h264.mp4: exists={p.exists()}, size={p.stat().st_size if p.exists() else 0} bytes")

