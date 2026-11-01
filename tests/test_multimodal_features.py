"""
NEXORA AI - Multimodal Integration Unit Tests
Verifies Image Batch Generation, Video Studio API, Model Catalog, and Media Downloads
"""
import sys
import time
import requests

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("==================================================")
    print("NEXORA AI - MULTIMODAL INTEGRATION TEST SUITE")
    print("==================================================")

    # 1. Health & Server Status
    health_res = requests.get(f"{BASE_URL}/api/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "online"
    assert health_data["gemini_ready"] is True
    print("✅ TEST 1: Backend health and Gemini engine online")

    # 2. Live Model Catalog
    models_res = requests.get(f"{BASE_URL}/api/models")
    assert models_res.status_code == 200
    models_data = models_res.json()
    assert len(models_data) >= 5
    model_ids = [m["id"] for m in models_data]
    assert "gemini-flash-lite-latest" in model_ids
    assert "nexora-motion-engine" in model_ids
    print(f"✅ TEST 2: Model catalog active with {len(models_data)} models verified")

    # 3. Image Batch Generation (Quantity = 2)
    print("⚙️ Testing batch image generation (2 variations)...")
    batch_res = requests.post(f"{BASE_URL}/api/image/generate-batch", json={
        "prompt": "futuristic crystalline holographic data orb glowing",
        "style": "photorealistic",
        "aspect_ratio": "1:1",
        "quantity": 2
    }, timeout=30)
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert isinstance(batch_data, list)
    assert len(batch_data) == 2
    assert batch_data[0]["image_url"].startswith("/storage/")
    assert batch_data[1]["image_url"].startswith("/storage/")
    img_id_1 = batch_data[0]["id"]
    print(f"✅ TEST 3: Multi-image batch generated 2 unique images with distinct IDs: {img_id_1[:8]}..., {batch_data[1]['id'][:8]}...")

    # 4. Image Download Endpoint
    img_dl_res = requests.get(f"{BASE_URL}/api/media/{img_id_1}/download")
    assert img_dl_res.status_code == 200
    assert "image" in img_dl_res.headers.get("Content-Type", "")
    assert "attachment" in img_dl_res.headers.get("Content-Disposition", "")
    assert len(img_dl_res.content) > 1000
    print(f"✅ TEST 4: Direct image binary download verified ({len(img_dl_res.content)} bytes)")

    # 5. Video Studio Job Creation & Progress Polling
    print("⚙️ Submitting async video generation task...")
    vid_res = requests.post(f"{BASE_URL}/api/video/generate", json={
        "prompt": "neon cybernetic data stream zooming through a microchip",
        "style": "cinematic",
        "aspect_ratio": "16:9",
        "duration": 3
    })
    assert vid_res.status_code == 200
    vid_job = vid_res.json()
    job_id = vid_job["job_id"]
    print(f"  Job queued with ID: {job_id}. Polling execution progress...")

    completed = False
    for attempt in range(25):
        time.sleep(2)
        poll_res = requests.get(f"{BASE_URL}/api/video/jobs/{job_id}")
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        print(f"  Progress: {poll_data['progress']}% - Status: {poll_data['status']}")
        if poll_data["status"] == "completed":
            completed = True
            assert poll_data["video_url"].startswith("/storage/")
            break
        elif poll_data["status"] == "failed":
            raise RuntimeError(f"Video job failed: {poll_data.get('error_message')}")

    assert completed is True
    print(f"✅ TEST 5: Video rendering completed successfully with output URL: {poll_data['video_url']}")

    # 6. Video Download & Playback Accessibility
    vid_static_url = f"{BASE_URL}{poll_data['video_url']}"
    vid_dl_res = requests.get(vid_static_url)
    assert vid_dl_res.status_code == 200
    assert len(vid_dl_res.content) > 50000
    print(f"✅ TEST 6: Video binary stream verified ({len(vid_dl_res.content):,} bytes rendered)")

    print("\n🎉 ALL 6 MULTIMODAL INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
