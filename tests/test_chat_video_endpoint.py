import httpx
import json
import time

def test_chat_video():
    url = "http://127.0.0.1:8000/api/chat"
    payload = {
        "message": "generate the video of lions in a jungle",
        "model": "gemini-flash-lite-latest"
    }
    print(f"Sending prompt: {payload['message']} to {url}...")
    t0 = time.time()
    resp = httpx.post(url, json=payload, timeout=60.0)
    elapsed = time.time() - t0
    print(f"Response status: {resp.status_code} in {elapsed:.1f}s")
    assert resp.status_code == 200, f"Error: {resp.text}"
    
    data = resp.json()
    asst_msg = data["assistant_message"]
    print("Content preview (safe):")
    print(asst_msg["content"][:300].encode('ascii', 'replace').decode('ascii'))
    print("Attachments:", asst_msg["attachments"])
    
    assert "<video" in asst_msg["content"], "Video tag missing from assistant content!"
    assert ".webm" in asst_msg["content"], "WebM video file missing from assistant content!"
    print("\nSUCCESS: Chat Studio video generation returned actual playable WebM video!")

if __name__ == "__main__":
    test_chat_video()
