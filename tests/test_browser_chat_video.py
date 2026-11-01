import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def run_chat_video_test():
    print("Launching Chromium browser to test Chat Studio Video Generation...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("Navigating to http://127.0.0.1:5500...")
        await page.goto("http://127.0.0.1:5500", wait_until="networkidle")
        await asyncio.sleep(2)

        # Ensure we are in Chat Studio
        chat_nav = page.locator('.nav-link[data-view="chat-studio"]')
        await chat_nav.click()
        await asyncio.sleep(1)

        # Inspect existing chat messages - check last assistant message
        last_asst_bubble = page.locator(".chat-bubble.assistant").last
        video_el = last_asst_bubble.locator("video")
        has_video = await video_el.count() > 0

        if not has_video:
            # Type the video generation prompt if not already present
            prompt = "generate the video of lions in a jungle"
            print(f"Submitting prompt in Chat Studio: '{prompt}'...")
            chat_input = page.locator("#chat-input")
            await chat_input.fill(prompt)
            send_btn = page.locator("#send-btn")
            await send_btn.click()
            await page.wait_for_selector(".chat-bubble.assistant video", timeout=60000)
            await asyncio.sleep(2)
            video_el = page.locator(".chat-bubble.assistant video").last

        video_info = await video_el.evaluate("""(v) => {
            return {
                src: v.src,
                currentSrc: v.currentSrc,
                readyState: v.readyState,
                duration: v.duration,
                videoWidth: v.videoWidth,
                videoHeight: v.videoHeight,
                paused: v.paused,
                error: v.error ? { code: v.error.code, message: v.error.message } : null
            };
        }""")

        print(f"Video Element Info in Chat: {video_info}")
        assert video_info["error"] is None, f"Video has playback error: {video_info['error']}"
        assert video_info["duration"] > 0, f"Duration is {video_info['duration']} (expected > 0)"
        assert video_info["videoWidth"] > 0, f"Video width is {video_info['videoWidth']} (expected > 0)"
        assert ".webm" in video_info["src"], f"Expected WebM video source, got {video_info['src']}"

        # Check action buttons (safe ascii encode for console)
        actions = page.locator(".chat-bubble.assistant .generated-media-actions").last
        actions_text = await actions.inner_text()
        print(f"Action buttons: {actions_text.encode('ascii', 'replace').decode('ascii')}")
        assert "Download Video" in actions_text, "Download Video button missing!"
        assert "Open in Video Studio" in actions_text, "Open in Video Studio button missing!"

        # Take screenshot
        shot_path = "C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/chat_video_generation_verified.png"
        await page.screenshot(path=shot_path)
        print(f"SUCCESS: Chat Studio video verified! Screenshot saved to: {shot_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_chat_video_test())
