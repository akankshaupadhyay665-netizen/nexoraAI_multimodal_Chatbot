import cv2
import numpy as np

# Test different fourcc codecs
frame = np.zeros((480, 640, 3), dtype=np.uint8)

for tag in ['VP80', 'VP90', 'avc1', 'H264', 'X264', 'mp4v']:
    try:
        fourcc = cv2.VideoWriter_fourcc(*tag)
        ext = '.webm' if 'VP' in tag else '.mp4'
        writer = cv2.VideoWriter(f'tests/test_{tag}{ext}', fourcc, 24, (640, 480))
        for _ in range(10):
            writer.write(frame)
        writer.release()
        print(f"Tag {tag}: successfully written to tests/test_{tag}{ext}")
    except Exception as e:
        print(f"Tag {tag} failed: {e}")

