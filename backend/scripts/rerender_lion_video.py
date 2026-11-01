import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import cv2
import numpy as np

def render_webm(keyframe_path, output_path, width=1280, height=720, duration=5, fps=24):
    base_img = cv2.imread(str(keyframe_path))
    if base_img is None:
        raise ValueError(f"Could not load {keyframe_path}")
    base_img = cv2.resize(base_img, (width, height))
    
    fourcc = cv2.VideoWriter_fourcc(*'VP80')
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    total_frames = int(fps * duration)
    for frame_idx in range(total_frames):
        t = frame_idx / float(total_frames)
        scale = 1.0 + 0.12 * np.sin(t * np.pi)
        h_c, w_c = int(height / scale), int(width / scale)
        top = (height - h_c) // 2
        left = (width - w_c) // 2
        cropped = base_img[top:top+h_c, left:left+w_c]
        frame = cv2.resize(cropped, (width, height))
        writer.write(frame)
    writer.release()
    print(f"Rendered {output_path.name}: {output_path.stat().st_size} bytes")

def main():
    img_dir = BASE_DIR / "backend" / "storage" / "generated_images"
    vid_dir = BASE_DIR / "backend" / "storage" / "generated_videos"
    
    # Use real lion image
    lion_img = img_dir / "nexora_gen_663589cb_1793440635.png"
    if not lion_img.exists():
        lion_img = list(img_dir.glob("*lion*"))[0]
        
    for vid_name in ["nexora_vid_cae6cfac_1793440677.webm", "nexora_vid_5d7c01d1_1793438120.webm"]:
        target = vid_dir / vid_name
        render_webm(lion_img, target)
        print(f"Updated {vid_name} with real lion animation!")

if __name__ == "__main__":
    main()

