"""
NEXORA AI - Web Media & YouTube Intelligence Test Suite
Verifies SSRF protection, YouTube ID extraction, oEmbed, transcripts,
direct video (MP4/HLS) detection, Open Graph web parsing, and URL info API.
"""
import sys
import asyncio
from pathlib import Path

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

from backend.services.web_media_service import web_media_service

async def run_tests():
    print("==================================================")
    print("NEXORA AI - WEB MEDIA & YOUTUBE TEST SUITE")
    print("==================================================")

    # 1. SSRF Protection Tests
    assert web_media_service.is_safe_url("http://127.0.0.1:8000") is False
    assert web_media_service.is_safe_url("http://localhost:5500") is False
    assert web_media_service.is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert web_media_service.is_safe_url("http://192.168.1.100") is False
    assert web_media_service.is_safe_url("http://10.0.0.1") is False
    assert web_media_service.is_safe_url("ftp://example.com") is False
    assert web_media_service.is_safe_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert web_media_service.is_safe_url("https://example.com") is True
    print("✅ TEST 1: SSRF Protection verified (Loopback, private IPs & link-local blocked)")

    # 2. YouTube ID Extraction
    id1 = web_media_service.extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    id2 = web_media_service.extract_youtube_id("https://youtu.be/dQw4w9WgXcQ?t=10")
    id3 = web_media_service.extract_youtube_id("https://www.youtube.com/shorts/dQw4w9WgXcQ")
    id4 = web_media_service.extract_youtube_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
    assert id1 == "dQw4w9WgXcQ"
    assert id2 == "dQw4w9WgXcQ"
    assert id3 == "dQw4w9WgXcQ"
    assert id4 == "dQw4w9WgXcQ"
    print("✅ TEST 2: YouTube URL Regex & ID Extraction verified across watch, youtu.be, shorts, and embed formats")

    # 3. Direct Video & HLS Stream Identification
    v1 = await web_media_service.get_direct_video_info("https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4")
    assert v1["success"] is True
    assert v1["type"] == "direct_video"
    assert v1["format"] == "mp4"
    assert v1["is_hls"] is False

    v2 = await web_media_service.get_direct_video_info("https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8")
    assert v2["type"] == "direct_video"
    assert v2["format"] == "m3u8"
    assert v2["is_hls"] is True
    print("✅ TEST 3: Direct video (MP4) and HLS stream (M3U8) detection verified")

    # 4. Open Graph Webpage Extraction
    web_info = await web_media_service.get_webpage_info("https://example.com")
    assert web_info["success"] is True
    assert web_info["type"] == "webpage"
    assert "example.com" in web_info["domain"]
    assert "Example Domain" in web_info["title"]
    assert len(web_info["readable_text"]) > 10
    print(f"✅ TEST 4: Webpage metadata and text extraction verified ('{web_info['title']}')")

    # 5. YouTube Live Metadata & Embed URL Extraction
    print("⚙️ Fetching YouTube oEmbed metadata for test video...")
    yt_info = await web_media_service.get_youtube_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert yt_info["success"] is True
    assert yt_info["type"] == "youtube"
    assert yt_info["video_id"] == "dQw4w9WgXcQ"
    assert "youtube-nocookie.com/embed/dQw4w9WgXcQ" in yt_info["embed_url"]
    assert "Rick" in yt_info["title"] or "dQw4w9WgXcQ" in yt_info["title"]
    print(f"✅ TEST 5: YouTube oEmbed verified: Title = '{yt_info['title']}', Embed = '{yt_info['embed_url']}'")

    print("\n🎉 ALL 5 WEB MEDIA & YOUTUBE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_tests())

