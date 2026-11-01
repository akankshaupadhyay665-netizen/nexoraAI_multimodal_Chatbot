"""
NEXORA AI - Image Generation & Unique DB ID Verification Suite
Verifies:
1. POST /api/image/generate with prompt 'rose ultra' (resolves sqlite3.IntegrityError)
2. POST /api/image/generate with prompt 'A beautiful pink rose in a cinematic garden.'
3. Unique UUID validation across sequential requests (0 duplicate key collisions)
4. Database persistence in SQLite (generated_media table)
5. GET /api/media returns saved records with metadata and download URLs
6. File integrity and valid image header validation
"""
import sys
import os
import json
import sqlite3
import urllib.request
from pathlib import Path
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = Path(__file__).resolve().parent.parent / "nexora.db"

def run_tests():
    print("==================================================")
    print("NEXORA AI - IMAGE GENERATION DB REPAIR VERIFICATION")
    print("==================================================")

    # 1. Inspect Initial DB count
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM generated_media;")
    initial_count = c.fetchone()[0]
    print(f"[Initial Check] Existing records in generated_media: {initial_count}")
    conn.close()

    # ==================================================
    # TEST 1: 'rose ultra' Generation
    # ==================================================
    print("\n--- TEST 1: Generating image with prompt 'rose ultra' ---")
    payload1 = {
        "prompt": "rose ultra",
        "style": "photorealistic",
        "aspect_ratio": "1:1"
    }
    req1 = urllib.request.Request(
        f"{BASE_URL}/api/image/generate",
        data=json.dumps(payload1).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res1 = urllib.request.urlopen(req1, timeout=30)
    assert res1.status == 200, f"Expected 200 OK, got {res1.status}"
    data1 = json.loads(res1.read().decode("utf-8"))
    
    media_id_1 = data1["id"]
    image_url_1 = data1["image_url"]
    provider_1 = data1["provider"]
    print(f"  [SUCCESS] ID: {media_id_1}")
    print(f"  [SUCCESS] Image URL: {image_url_1}")
    print(f"  [SUCCESS] Provider: {provider_1}")
    assert media_id_1, "Missing ID in response!"
    assert image_url_1.startswith("/storage/generated_images/"), f"Unexpected URL format: {image_url_1}"

    # Verify record in SQLite
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, prompt, provider, file_path, status FROM generated_media WHERE id = ?;", (media_id_1,))
    row1 = c.fetchone()
    assert row1 is not None, f"Record with ID {media_id_1} not found in database!"
    assert row1[1] == "rose ultra"
    assert row1[4] == "completed"
    print(f"  [DB Verified] Found SQLite record for '{row1[1]}' with provider '{row1[2]}'")
    conn.close()

    # ==================================================
    # TEST 2: 'A beautiful pink rose in a cinematic garden.'
    # ==================================================
    print("\n--- TEST 2: Generating image with prompt 'A beautiful pink rose in a cinematic garden.' ---")
    payload2 = {
        "prompt": "A beautiful pink rose in a cinematic garden.",
        "style": "cinematic",
        "aspect_ratio": "1:1"
    }
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/image/generate",
        data=json.dumps(payload2).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res2 = urllib.request.urlopen(req2, timeout=30)
    assert res2.status == 200, f"Expected 200 OK, got {res2.status}"
    data2 = json.loads(res2.read().decode("utf-8"))
    
    media_id_2 = data2["id"]
    image_url_2 = data2["image_url"]
    provider_2 = data2["provider"]
    print(f"  [SUCCESS] ID: {media_id_2}")
    print(f"  [SUCCESS] Image URL: {image_url_2}")
    print(f"  [SUCCESS] Provider: {provider_2}")

    # Verify ID is genuinely unique
    assert media_id_1 != media_id_2, f"DUPLICATE ID DETECTED! Both images have id: {media_id_1}"
    print(f"  [Unique Check Passed] ID1 != ID2 ({media_id_1} vs {media_id_2})")

    # ==================================================
    # TEST 3: Sequential Multiple Generations (Zero Duplicate IDs)
    # ==================================================
    print("\n--- TEST 3: Sequential Multiple Image Generations ---")
    prompts = [
        "Cyberpunk neon metropolis with flying cars",
        "Futuristic AI quantum core crystal glowing blue",
        "Golden retriever puppy playing in autumn park"
    ]
    generated_ids = [media_id_1, media_id_2]
    for p in prompts:
        req = urllib.request.Request(
            f"{BASE_URL}/api/image/generate",
            data=json.dumps({"prompt": p, "style": "photorealistic", "aspect_ratio": "1:1"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=30)
        assert res.status == 200
        d = json.loads(res.read().decode("utf-8"))
        gid = d["id"]
        assert gid not in generated_ids, f"DUPLICATE ID FOUND: {gid}"
        generated_ids.append(gid)
        print(f"  [Generated] '{p[:30]}...' -> ID: {gid}")

    print(f"  Total generated in this run: {len(generated_ids)} (All unique: {len(generated_ids) == len(set(generated_ids))})")

    # ==================================================
    # TEST 4: Media Gallery API Persistence Check
    # ==================================================
    print("\n--- TEST 4: Media Gallery API Verification ---")
    req_gal = urllib.request.Request(f"{BASE_URL}/api/media?media_type=image")
    res_gal = urllib.request.urlopen(req_gal, timeout=10)
    assert res_gal.status == 200
    gallery_items = json.loads(res_gal.read().decode("utf-8"))
    gal_ids = [item["id"] for item in gallery_items]
    
    for gid in generated_ids:
        assert gid in gal_ids, f"Generated ID {gid} missing from /api/media gallery!"
    print(f"  [Verified] All {len(generated_ids)} generated media records are present in /api/media gallery response.")

    # ==================================================
    # TEST 5: Image File Download & Integrity Verification
    # ==================================================
    print("\n--- TEST 5: Image File Download & Format Verification ---")
    download_url = f"{BASE_URL}{image_url_1}"
    dl_req = urllib.request.Request(download_url)
    dl_res = urllib.request.urlopen(dl_req, timeout=10)
    assert dl_res.status == 200, f"Failed to download image from {download_url}"
    img_bytes = dl_res.read()
    assert len(img_bytes) > 2000, f"Downloaded image bytes too small: {len(img_bytes)}"

    # Validate image header with PIL
    import io
    pil_img = Image.open(io.BytesIO(img_bytes))
    print(f"  [Image Valid] Format: {pil_img.format}, Size: {pil_img.size}, Mode: {pil_img.mode}")
    assert pil_img.size[0] >= 512 and pil_img.size[1] >= 512, f"Image dimensions too small: {pil_img.size}"

    # Verify SQLite final count
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM generated_media;")
    final_count = c.fetchone()[0]
    conn.close()
    print(f"\n[Final DB Check] Total records in generated_media: {final_count} (Increased by {final_count - initial_count})")
    assert final_count >= initial_count + len(generated_ids), "Final record count does not match generated items!"

    print("\n==================================================")
    print("ALL 5 BACKEND & DATABASE TESTS PASSED 100%!")
    print("Zero unique constraint errors. All UUIDs unique and persisted.")
    print("==================================================")

if __name__ == "__main__":
    run_tests()

