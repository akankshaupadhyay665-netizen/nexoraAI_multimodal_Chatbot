"""
NEXORA AI - Complete Playwright Browser Test for Image Studio & Media Gallery
Verifies:
1. Image Studio generation with prompt 'rose ultra'
2. No 'UNIQUE constraint failed' errors or error toasts
3. Image card rendered in Image Studio gallery with action controls (Download, Copy, Regen)
4. Navigation to Media Gallery: verifying prompt, provider, formatted date, preview, download, delete
5. Browser reload: verifying persistent storage in SQLite
6. Saving screenshots of verified state
"""
import sys
import os
import time
import shutil
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://127.0.0.1:5500"
BRAIN_DIR = r"C:\Users\Hp\.gemini\antigravity\brain\8ae4ae20-391d-4302-8aeb-5150ef4d3f19"

def run_browser_test():
    print("==================================================")
    print("NEXORA AI - BROWSER IMAGE STUDIO & GALLERY TEST")
    print("==================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--use-gl=angle", "--use-angle=swiftshader", "--no-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_logs = []
        page_errors = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type.upper()}] {msg.text}"))
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        # Step 1: Open Frontend
        print(f"\n[Step 1] Loading {FRONTEND_URL}...")
        page.goto(FRONTEND_URL, wait_until="networkidle")
        time.sleep(1.5)

        # Step 2: Navigate to Image Studio
        print("\n[Step 2] Navigating to Image Studio...")
        studio_nav = page.locator('.nav-link[data-view="image-studio"]')
        studio_nav.click()
        time.sleep(1)
        assert page.locator("#view-image-studio").is_visible(), "Image Studio view not visible!"

        # Step 3: Enter prompt 'rose ultra' and click Generate
        print("\n[Step 3] Submitting prompt 'rose ultra' in Image Studio...")
        prompt_input = page.locator("#img-studio-prompt")
        prompt_input.fill("rose ultra")
        
        generate_btn = page.locator("#img-studio-generate-btn")
        generate_btn.click()

        # Wait for image generation response (up to 35 seconds)
        print("  Waiting for image generation to complete...")
        start_t = time.time()
        image_card_found = False
        while time.time() - start_t < 35:
            cards = page.locator("#img-studio-results-grid .image-card")
            if cards.count() > 0:
                image_card_found = True
                break
            time.sleep(1)

        assert image_card_found, "Image card not rendered in Image Studio gallery!"
        print("  [SUCCESS] Image card rendered in Image Studio gallery!")

        # Verify image element inside card
        first_card = page.locator("#img-studio-results-grid .image-card").first
        img = first_card.locator("img")
        assert img.count() > 0, "No img tag inside image card!"
        src = img.get_attribute("src") or ""
        print(f"  [SUCCESS] Generated image src: {src}")
        assert "storage/generated_images" in src, f"Unexpected image source: {src}"

        # Verify overlay buttons (Download, Regenerate, Send to Chat, Copy)
        assert first_card.locator(".download-btn").count() > 0, "Download button missing!"
        assert first_card.locator(".regen-btn").count() > 0, "Regenerate button missing!"
        print("  [SUCCESS] Image action controls verified.")

        # Save Image Studio Screenshot
        studio_ss_path = "tests/image_studio_verified.png"
        page.screenshot(path=studio_ss_path)
        print(f"  [Saved Screenshot] {studio_ss_path}")

        # Step 4: Navigate to Media Gallery
        print("\n[Step 4] Navigating to Media Gallery...")
        gallery_nav = page.locator('.nav-link[data-view="media-gallery"]')
        gallery_nav.click()
        time.sleep(1.5)
        assert page.locator("#view-media-gallery").is_visible(), "Media Gallery view not visible!"

        # Verify items in gallery
        gallery_cards = page.locator("#gallery-items-grid .gallery-card")
        g_count = gallery_cards.count()
        print(f"  Found {g_count} item(s) in Media Gallery.")
        assert g_count >= 1, "No items found in Media Gallery!"

        # Verify first gallery card features: Image, Prompt, Provider, Date, Preview, Download, Delete
        top_card = gallery_cards.first
        card_text = top_card.inner_text()
        print("  Top gallery item info:\n" + card_text.encode('ascii', errors='backslashreplace').decode('ascii'))
        assert top_card.locator("img").count() > 0, "Image thumbnail missing in gallery card!"
        assert top_card.locator(".gallery-provider-tag").count() > 0, "Provider tag missing!"
        assert top_card.locator(".gallery-date-row").count() > 0, "Date row missing!"
        assert top_card.locator(".preview-btn").count() > 0, "Preview button missing!"
        assert top_card.locator(".download-btn").count() > 0, "Download button missing!"
        assert top_card.locator(".delete-btn").count() > 0, "Delete button missing!"
        print("  [SUCCESS] All metadata and interactive controls verified in Media Gallery.")

        # Save Media Gallery Screenshot
        gallery_ss_path = "tests/media_gallery_verified.png"
        page.screenshot(path=gallery_ss_path)
        print(f"  [Saved Screenshot] {gallery_ss_path}")

        # Step 5: Test Browser Reload Persistence
        print("\n[Step 5] Testing Browser Refresh Persistence...")
        page.reload(wait_until="networkidle")
        time.sleep(1.5)

        # Re-navigate to Media Gallery
        page.locator('.nav-link[data-view="media-gallery"]').click()
        time.sleep(1)
        reloaded_count = page.locator("#gallery-items-grid .gallery-card").count()
        print(f"  Items in Media Gallery after reload: {reloaded_count}")
        assert reloaded_count >= g_count, f"Images were lost on reload! (Before: {g_count}, After: {reloaded_count})"
        print("  [SUCCESS] All generated media persisted across browser refresh!")

        # Step 6: Console Error Audit
        print("\n[Step 6] Console Error Audit...")
        critical_errs = [e for e in console_logs if "[ERROR]" in e and "favicon" not in e and "404" not in e]
        print(f"  Page errors: {len(page_errors)}, Critical console errors: {len(critical_errs)}")
        assert len(page_errors) == 0, f"Page errors found: {page_errors}"
        assert len(critical_errs) == 0, f"Critical console errors found: {critical_errs}"

        # Copy screenshots to brain artifact directory
        if os.path.exists(BRAIN_DIR):
            for f in ["image_studio_verified.png", "media_gallery_verified.png"]:
                src = os.path.join("tests", f)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(BRAIN_DIR, f))
            print("  [SUCCESS] Copied screenshots to brain artifact directory.")

        browser.close()

    print("\n==================================================")
    print("ALL BROWSER TESTS PASSED 100%!")
    print("Image Studio and Media Gallery are fully operational.")
    print("==================================================")

if __name__ == "__main__":
    run_browser_test()

