"""
Migrates existing mp4 video files to webm format for 100% HTML5 browser playback
"""
import sqlite3
import cv2
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
VIDEO_DIR = BASE_DIR / "backend" / "storage" / "generated_videos"
DB_PATH = BASE_DIR / "nexora.db"

def migrate():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Convert existing mp4 video files
    for mp4_file in VIDEO_DIR.glob("*.mp4"):
        webm_path = mp4_file.with_suffix(".webm")
        if not webm_path.exists():
            print(f"Converting {mp4_file.name} to {webm_path.name}...")
            cap = cv2.VideoCapture(str(mp4_file))
            fps = cap.get(cv2.CAP_PROP_FPS) or 24
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            out = cv2.VideoWriter(str(webm_path), cv2.VideoWriter_fourcc(*'VP80'), fps, (w, h))
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            cap.release()
            out.release()
            print(f"Successfully created: {webm_path.name}")

    # Update video_jobs
    c.execute("SELECT id, video_url FROM video_jobs;")
    jobs = c.fetchall()
    for j_id, v_url in jobs:
        if v_url and v_url.endswith(".mp4"):
            new_url = v_url.replace(".mp4", ".webm")
            new_fn = Path(new_url).name
            new_path = str(VIDEO_DIR / new_fn)
            c.execute("UPDATE video_jobs SET file_path = ?, video_url = ? WHERE id = ?;", (new_path, new_url, j_id))
            print(f"Updated video_job {j_id} -> {new_url}")

    # Update generated_media
    c.execute("SELECT id, filename FROM generated_media WHERE media_type = 'video';")
    media_rows = c.fetchall()
    for m_id, m_fn in media_rows:
        if m_fn and m_fn.endswith(".mp4"):
            new_fn = m_fn.replace(".mp4", ".webm")
            new_path = str(VIDEO_DIR / new_fn)
            c.execute("UPDATE generated_media SET filename = ?, file_path = ? WHERE id = ?;", (new_fn, new_path, m_id))
            print(f"Updated generated_media {m_id} -> {new_fn}")

    conn.commit()
    conn.close()
    print("Video migration completed successfully!")

if __name__ == "__main__":
    migrate()

