import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent.parent

async def run_verification():
    print("Launching Chromium browser to test Nexora AI Video & Image Studios...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("Navigating to http://127.0.0.1:5500...")
        await page.goto("http://127.0.0.1:5500", wait_until="networkidle")
        await asyncio.sleep(2)

        # -------------------------------------------------------------
        # 1. VERIFY VIDEO STUDIO & VIDEO PLAYBACK
        # -------------------------------------------------------------
        print("\n--- TEST 1: Video Studio & Video Playback ---")
        video_nav = page.locator('.nav-link[data-view="video-studio"]')
        await video_nav.click()
        await asyncio.sleep(2)

        # Check video cards
        video_elements = page.locator("#vid-studio-results-grid video")
        count = await video_elements.count()
        print(f"Found {count} video elements in Video Studio results grid.")
        assert count > 0, "No videos found in Video Studio results grid!"

        first_video = video_elements.first
        # Evaluate HTML5 video playback state in browser
        video_diagnostics = await first_video.evaluate("""(v) => {
            return {
                src: v.src,
                currentSrc: v.currentSrc,
                readyState: v.readyState,
                networkState: v.networkState,
                duration: v.duration,
                videoWidth: v.videoWidth,
                videoHeight: v.videoHeight,
                paused: v.paused,
                error: v.error ? { code: v.error.code, message: v.error.message } : null
            };
        }""")

        print(f"Video Diagnostics: {video_diagnostics}")
        assert video_diagnostics["error"] is None, f"Video element has playback error: {video_diagnostics['error']}"
        assert video_diagnostics["duration"] > 0, f"Video duration is {video_diagnostics['duration']} (expected > 0)"
        assert video_diagnostics["videoWidth"] > 0, f"Video width is {video_diagnostics['videoWidth']} (expected > 0)"
        print(f"SUCCESS: Video loaded and playable! Duration: {video_diagnostics['duration']}s, Resolution: {video_diagnostics['videoWidth']}x{video_diagnostics['videoHeight']}")

        # Screenshot Video Studio
        video_shot_path = "C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/video_studio_working.png"
        await page.screenshot(path=video_shot_path)
        print(f"Saved Video Studio screenshot to: {video_shot_path}")

        # -------------------------------------------------------------
        # 2. VERIFY IMAGE STUDIO & MULTIPLE IMAGE CARDS
        # -------------------------------------------------------------
        print("\n--- TEST 2: Image Studio & Multiple Image Cards ---")
        image_nav = page.locator('.nav-link[data-view="image-studio"]')
        await image_nav.click()
        await asyncio.sleep(2)

        # Check all image cards
        img_elements = page.locator("#img-studio-results-grid img")
        img_count = await img_elements.count()
        print(f"Found {img_count} image elements in Image Studio results grid.")
        assert img_count >= 3, f"Expected at least 3 images, but found {img_count}"

        # Check images load with real dimensions
        img_diagnostics = await page.evaluate("""() => {
            const imgs = document.querySelectorAll('#img-studio-results-grid img');
            return Array.from(imgs).slice(0, 5).map(img => ({
                src: img.src,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                complete: img.complete
            }));
        }""")
        print(f"Image Diagnostics (first 5): {img_diagnostics}")
        for idx, d in enumerate(img_diagnostics):
            assert d["complete"] is True, f"Image {idx} is not complete"
            assert d["naturalWidth"] > 0, f"Image {idx} naturalWidth is 0"
        print("SUCCESS: All Image Studio cards loaded real images!")

        # Screenshot Image Studio
        image_shot_path = "C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/image_studio_working.png"
        await page.screenshot(path=image_shot_path)
        print(f"Saved Image Studio screenshot to: {image_shot_path}")

        # -------------------------------------------------------------
        # 3. VERIFY CHAT STUDIO & 3D ROBOT INTACT
        # -------------------------------------------------------------
        print("\n--- TEST 3: Chat Studio & 3D Robot ---")
        chat_nav = page.locator('.nav-link[data-view="chat-studio"]')
        await chat_nav.click()
        await asyncio.sleep(2)

        robot_canvas = page.locator("#robot-canvas-container canvas")
        is_visible = await robot_canvas.is_visible()
        print(f"3D Robot Canvas visible: {is_visible}")
        assert is_visible, "3D Robot canvas is not visible!"

        e2e_shot_path = "C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/full_system_verified.png"
        await page.screenshot(path=e2e_shot_path)
        print(f"Saved E2E verified screenshot to: {e2e_shot_path}")

        print("\nALL AUTOMATED TESTS PASSED!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_verification())

