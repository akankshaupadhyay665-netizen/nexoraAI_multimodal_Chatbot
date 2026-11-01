import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
db_path = BASE_DIR / "nexora.db"
con = sqlite3.connect(str(db_path))
cur = con.cursor()

new_content = """### 🎬 Video Regenerated in Universal MP4 Format

I have re-rendered the video for **"a small girl"** using our **Universal H.264 MP4 Engine**. It is now ready for playback directly in your browser:

<video src="/storage/generated_videos/nexora_vid_44a29910_1793445890.mp4" controls autoplay loop muted playsinline style="width: 100%; max-width: 680px; border-radius: 12px; margin: 12px 0; background: #000;"></video>

*(Download using the button below or view in the Video Generator studio).*"""

new_att = json.dumps([{
    "id": "44a29910",
    "name": "Generated_a_small_girl.mp4",
    "type": "video",
    "url": "/storage/generated_videos/nexora_vid_44a29910_1793445890.mp4"
}])

cur.execute("""
    UPDATE messages 
    SET content = ?, attachments = ? 
    WHERE id = '4301a297-6513-4b14-9986-b26b440cfb9d'
""", (new_content, new_att))
con.commit()
print("Updated message 4301a297 successfully with working MP4 video player!")
con.close()

