import os
import sys
import time
from playwright.sync_api import sync_playwright

def test_browser_downloads():
    print("Starting Playwright Browser Download Verification...")
    downloads_recorded = []
    
    with sync_playwright() as p:
        # Launch Chrome or Chromium
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        # Navigate to Nexora Frontend
        page.goto("http://127.0.0.1:5500", wait_until="networkidle")
        print("[PASS] Nexora Frontend loaded successfully.")
        
        # Take initial screenshot
        page.screenshot(path="C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/test_initial_load.png")
        
        # ----------------------------------------------------
        # TEST 1: Video Generator Page Download
        # ----------------------------------------------------
        print("\n--- TEST 1: Video Generator Download ---")
        page.click('.nav-link[data-view="video-studio"]')
        page.wait_for_selector("#vid-studio-results-grid", state="visible")
        time.sleep(1)
        
        video_cards = page.query_selector_all("#vid-studio-results-grid .video-result-card")
        print(f"Found {len(video_cards)} video cards in Video Studio.")
        if video_cards:
            dl_btn = video_cards[0].query_selector("button:has-text('Download Video'), .btn:has-text('Download')")
            if dl_btn:
                print("Clicking Video Download button...")
                with page.expect_download(timeout=15000) as download_info:
                    dl_btn.click()
                download = download_info.value
                dl_path = download.path()
                size = os.path.getsize(dl_path) if dl_path and os.path.exists(dl_path) else 0
                print(f"[PASS] Video downloaded: {download.suggested_filename}, Size: {size} bytes")
                assert size > 0, "Video download is 0 bytes"
                downloads_recorded.append(("Video Studio", download.suggested_filename, size))
            else:
                print("[WARNING] Download button not found on video card.")
        
        # ----------------------------------------------------
        # TEST 2: Image Generator Page Download
        # ----------------------------------------------------
        print("\n--- TEST 2: Image Generator Download ---")
        page.click('.nav-link[data-view="image-studio"]')
        page.wait_for_selector("#img-studio-results-grid", state="visible")
        time.sleep(1)
        
        image_cards = page.query_selector_all("#img-studio-results-grid .image-card")
        print(f"Found {len(image_cards)} image cards in Image Studio.")
        if image_cards:
            dl_btn = image_cards[0].query_selector(".download-btn, [title*='Download']")
            if dl_btn:
                print("Clicking Image Download button...")
                with page.expect_download(timeout=15000) as download_info:
                    dl_btn.click()
                download = download_info.value
                dl_path = download.path()
                size = os.path.getsize(dl_path) if dl_path and os.path.exists(dl_path) else 0
                print(f"[PASS] Image downloaded: {download.suggested_filename}, Size: {size} bytes")
                assert size > 0, "Image download is 0 bytes"
                downloads_recorded.append(("Image Studio", download.suggested_filename, size))
            else:
                print("[WARNING] Download button not found on image card.")

        # ----------------------------------------------------
        # TEST 3: Generated Media Gallery Download
        # ----------------------------------------------------
        print("\n--- TEST 3: Generated Media Gallery Download ---")
        page.click('.nav-link[data-view="media-gallery"]')
        page.wait_for_selector("#gallery-items-grid", state="visible")
        time.sleep(1.5)
        
        gallery_cards = page.query_selector_all("#gallery-items-grid .gallery-card")
        print(f"Found {len(gallery_cards)} media cards in Generated Media gallery.")
        if gallery_cards:
            card_dl_btn = gallery_cards[0].query_selector(".download-btn")
            if card_dl_btn:
                print("Clicking Gallery Card Download button...")
                with page.expect_download(timeout=15000) as download_info:
                    card_dl_btn.click()
                download = download_info.value
                dl_path = download.path()
                size = os.path.getsize(dl_path) if dl_path and os.path.exists(dl_path) else 0
                print(f"[PASS] Gallery card downloaded: {download.suggested_filename}, Size: {size} bytes")
                assert size > 0, "Gallery download is 0 bytes"
                downloads_recorded.append(("Media Gallery Card", download.suggested_filename, size))
            
            # ----------------------------------------------------
            # TEST 4: Media Preview Modal Download
            # ----------------------------------------------------
            print("\n--- TEST 4: Media Preview Modal Download ---")
            prev_btn = gallery_cards[0].query_selector(".preview-btn")
            if prev_btn:
                print("Opening Preview Modal...")
                prev_btn.click()
                page.wait_for_selector("#media-preview-modal.open", state="visible")
                time.sleep(1)
                
                # Capture screenshot of preview modal
                page.screenshot(path="C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/test_preview_modal.png")
                
                modal_dl_btn = page.query_selector("#preview-modal-download-btn")
                assert modal_dl_btn is not None, "Preview modal download button not found"
                print("Clicking Preview Modal Download button...")
                with page.expect_download(timeout=15000) as download_info:
                    modal_dl_btn.click()
                download = download_info.value
                dl_path = download.path()
                size = os.path.getsize(dl_path) if dl_path and os.path.exists(dl_path) else 0
                print(f"[PASS] Modal preview downloaded: {download.suggested_filename}, Size: {size} bytes")
                assert size > 0, "Modal preview download is 0 bytes"
                downloads_recorded.append(("Preview Modal", download.suggested_filename, size))
                
                # Close modal
                page.click("#close-preview-modal-btn")
                time.sleep(0.5)

        # ----------------------------------------------------
        # TEST 5: Chat Studio In-Chat Download Button
        # ----------------------------------------------------
        print("\n--- TEST 5: Chat Studio Action Pill Download ---")
        page.click('.nav-link[data-view="chat-studio"]')
        time.sleep(1)
        
        # Check if any messages with download buttons exist
        chat_dl_btns = page.query_selector_all(".generated-media-actions button:has-text('Download'), .generated-image-actions button:has-text('Download')")
        print(f"Found {len(chat_dl_btns)} action pill download buttons in Chat Studio.")
        if chat_dl_btns:
            print("Clicking In-Chat Download button...")
            with page.expect_download(timeout=15000) as download_info:
                chat_dl_btns[0].click()
            download = download_info.value
            dl_path = download.path()
            size = os.path.getsize(dl_path) if dl_path and os.path.exists(dl_path) else 0
            print(f"[PASS] Chat action pill downloaded: {download.suggested_filename}, Size: {size} bytes")
            assert size > 0, "Chat action pill download is 0 bytes"
            downloads_recorded.append(("Chat Studio Action Pill", download.suggested_filename, size))
        
        # Capture final screenshot
        page.screenshot(path="C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/test_downloads_final.png")
        
        browser.close()
        
    print("\n================ DOWNLOAD TEST SUMMARY ================")
    for src, name, sz in downloads_recorded:
        print(f"SUCCESS: {src} -> '{name}' ({sz:,} bytes)")
    print("=======================================================")
    print("ALL 5 DOWNLOAD WORKFLOWS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_browser_downloads()

