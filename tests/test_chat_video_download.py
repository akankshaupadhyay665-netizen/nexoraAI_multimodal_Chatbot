import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from playwright.sync_api import sync_playwright

def test_chat_video_download():
    print("Testing Chat Studio Video Download in Chrome...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        page.goto("http://127.0.0.1:5500", wait_until="networkidle")
        time.sleep(1)
        
        # Send video generation prompt in chat
        chat_input = page.wait_for_selector("#chat-input")
        print("Sending prompt: 'generate video of cheetah sprinting'...")
        chat_input.fill("generate video of cheetah sprinting")
        page.click("#send-btn")
        
        # Wait for video generation response
        print("Waiting for video response in chat...")
        dl_btn = page.wait_for_selector("button:has-text('Download Video')", timeout=45000)
        assert dl_btn is not None, "Download Video button not found in Chat Studio"
        
        print("Clicking 'Download Video' button in Chat Studio...")
        with page.expect_download(timeout=15000) as download_info:
            dl_btn.click()
            
        download = download_info.value
        dl_path = download.path()
        size = os.path.getsize(dl_path) if dl_path and os.path.exists(dl_path) else 0
        print(f"[PASS] Chat Studio Video Downloaded: '{download.suggested_filename}', Size: {size} bytes")
        assert size > 0, "Video download is 0 bytes"
        
        page.screenshot(path="C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/chat_video_download_verified.png")
        browser.close()
        print("CHAT VIDEO DOWNLOAD VERIFICATION 100% PASSED!")

if __name__ == "__main__":
    test_chat_video_download()
