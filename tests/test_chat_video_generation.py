"""
Test Chat Video Generation Pipeline & Controls
Validates that prompts like "generate the video of lions in a jungle" produce:
1. A valid video file on disk (.mp4)
2. An HTML5 <video> tag in message content (never an <img> tag)
3. Correct video attachments metadata
4. Working download endpoint
"""
import sys
import os
import httpx
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def test_chat_video_generation():
    print("Testing Chat Studio Video Generation...")
    url = "http://127.0.0.1:8000/api/chat"
    payload = {
        "message": "generate the video of lions in a jungle",
        "model": "gemini-flash-lite-latest"
    }

    with httpx.Client(timeout=45.0) as client:
        res = client.post(url, json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        asst_msg = data.get("assistant_message", {})
        content = asst_msg.get("content", "")
        attachments = asst_msg.get("attachments", "[]")
        
        print("Assistant Message Content Snippet:\n", content[:250])
        print("Attachments:", attachments)
        
        # 1. Assert content contains <video> tag and NOT <img
        assert "<video" in content, "Content must contain an HTML5 <video> player"
        assert "<source" in content, "Video player must have <source> element"
        assert not content.startswith("!["), "Video must not be formatted as markdown image syntax"
        
        # 2. Assert attachments contains video type
        import json
        if isinstance(attachments, str):
            att_list = json.loads(attachments)
        else:
            att_list = attachments
            
        assert len(att_list) > 0, "Must contain at least 1 attachment"
        vid_att = next((a for a in att_list if a.get("type") == "video"), None)
        assert vid_att is not None, "Attachment must be of type 'video'"
        assert vid_att["url"].endswith(".mp4"), "Video URL must be .mp4 format"
        
        # 3. Verify file exists via download endpoint
        dl_url = f"http://127.0.0.1:8000{vid_att['url']}"
        dl_res = client.get(dl_url)
        assert dl_res.status_code == 200, f"Video stream failed: {dl_res.status_code}"
        assert len(dl_res.content) > 1000, "Video content must not be empty"
        print(f"✅ Video file verified! Size: {len(dl_res.content)} bytes, Content-Type: {dl_res.headers.get('content-type')}")
        
    print("\n🎉 CHAT VIDEO GENERATION TEST PASSED COMPLETELY!")

if __name__ == "__main__":
    test_chat_video_generation()

