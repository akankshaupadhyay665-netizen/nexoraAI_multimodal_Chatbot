import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from playwright.sync_api import sync_playwright

def test_chat_studio_download():
    print("Testing Chat Studio Download Button in Chrome...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        page.goto("http://127.0.0.1:5500", wait_until="networkidle")
        time.sleep(1)
        
        # Check conversations in sidebar
        conv_items = page.query_selector_all("#chat-history-list .history-item")
        print(f"Found {len(conv_items)} conversations in sidebar.")
        
        found_media_chat = False
        for c in conv_items[:5]:
            title = c.inner_text()
            if any(k in title.lower() for k in ["generate", "image", "video", "rose", "lion"]):
                print(f"Loading conversation: '{title.strip()}'")
                c.click()
                time.sleep(2)
                found_media_chat = True
                break
                
        # If no conversation with media found, send a prompt to generate an image
        if not found_media_chat:
            print("Generating an image in chat to test download button...")
            chat_input = page.wait_for_selector("#chat-input")
            chat_input.fill("generate image of a neon cyber butterfly")
            page.click("#send-btn")
            # Wait for generation to complete
            page.wait_for_selector(".generated-media-actions, .generated-image-actions", timeout=30000)
            time.sleep(2)
            
        # Find download button in chat
        dl_btn = page.wait_for_selector("button:has-text('Download Image'), button:has-text('Download Video'), a:has-text('Download Image'), a:has-text('Download Video')", timeout=15000)
        assert dl_btn is not None, "Download button not found in Chat Studio"
        
        btn_text = dl_btn.inner_text()
        print(f"Clicking Chat Action Pill: '{btn_text}'...")
        
        with page.expect_download(timeout=20000) as download_info:
            dl_btn.click()
            
        download = download_info.value
        dl_path = download.path()
        size = os.path.getsize(dl_path) if dl_path and os.path.exists(dl_path) else 0
        print(f"[PASS] Chat Studio Downloaded: '{download.suggested_filename}', Size: {size} bytes")
        assert size > 0, "Chat download is 0 bytes"
        
        # Take screenshot of chat download success
        page.screenshot(path="C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/chat_download_verified.png")
        
        browser.close()
        print("CHAT STUDIO DOWNLOAD VERIFICATION PASSED!")

if __name__ == "__main__":
    test_chat_studio_download()
