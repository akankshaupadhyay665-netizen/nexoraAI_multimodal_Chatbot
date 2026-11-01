import urllib.request
import json
import os
import sys

def test_endpoints():
    print("Testing Nexora Backend Download Endpoints...")
    
    # 1. Fetch media items list
    req = urllib.request.Request("http://127.0.0.1:8000/api/media")
    with urllib.request.urlopen(req) as resp:
        media_items = json.loads(resp.read().decode())
    
    print(f"Found {len(media_items)} media items in database.")
    
    tested_image = False
    tested_video = False
    
    for item in media_items:
        m_id = item["id"]
        m_type = item["media_type"]
        filename = item["filename"]
        
        # Test download by ID
        url_id = f"http://127.0.0.1:8000/api/media/{m_id}/download"
        try:
            req_dl = urllib.request.Request(url_id)
            with urllib.request.urlopen(req_dl) as dl_resp:
                cd = dl_resp.headers.get("Content-Disposition")
                ct = dl_resp.headers.get("Content-Type")
                data = dl_resp.read()
                print(f"[PASS] /api/media/{m_id}/download ({m_type}) -> Status 200, Content-Type: {ct}, Content-Disposition: {cd}, Size: {len(data)} bytes")
                assert len(data) > 0, "Downloaded data is empty"
                assert "attachment" in (cd or ""), f"Missing attachment disposition in {cd}"
                if m_type == "image":
                    tested_image = True
                elif m_type == "video":
                    tested_video = True
        except Exception as e:
            print(f"[FAIL] /api/media/{m_id}/download: {e}")
            
        # Test download by filename
        url_fn = f"http://127.0.0.1:8000/api/media/download/file?filename={filename}"
        try:
            req_fn = urllib.request.Request(url_fn)
            with urllib.request.urlopen(req_fn) as fn_resp:
                cd = fn_resp.headers.get("Content-Disposition")
                ct = fn_resp.headers.get("Content-Type")
                data = fn_resp.read()
                print(f"[PASS] /api/media/download/file?filename={filename} -> Status 200, Content-Type: {ct}, Content-Disposition: {cd}, Size: {len(data)} bytes")
                assert len(data) > 0, "Downloaded data is empty"
                assert "attachment" in (cd or ""), f"Missing attachment disposition in {cd}"
        except Exception as e:
            print(f"[FAIL] /api/media/download/file?filename={filename}: {e}")
            
        if tested_image and tested_video:
            break

    print(f"\nSummary: Tested Image Download: {tested_image}, Tested Video Download: {tested_video}")
    if tested_image and tested_video:
        print("ALL BACKEND DOWNLOAD TESTS PASSED!")
    else:
        print("Warning: Missing either image or video to test.")

if __name__ == "__main__":
    test_endpoints()

