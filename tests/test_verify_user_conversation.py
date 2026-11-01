import asyncio
from playwright.async_api import async_playwright

async def verify_chat():
    print("Launching Chromium browser to test active conversation...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        print("Navigating to http://127.0.0.1:5500...")
        await page.goto("http://127.0.0.1:5500", wait_until="networkidle")
        await asyncio.sleep(2)

        # Click the top conversation in the sidebar history
        conv_items = page.locator("#chat-history-list .history-item")
        count = await conv_items.count()
        print(f"Conversations found in sidebar: {count}")
        if count > 0:
            await conv_items.first.click()
            await asyncio.sleep(2)

        # Check for video elements in chat messages
        videos = page.locator(".chat-bubble.assistant video")
        vid_count = await videos.count()
        print(f"Found {vid_count} video elements in chat messages.")
        assert vid_count > 0, "No video elements found in chat!"

        last_video = videos.last
        video_diag = await last_video.evaluate("""(v) => {
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

        print(f"Video Diagnostics: {video_diag}")
        assert video_diag["error"] is None, f"Video element has error: {video_diag['error']}"
        assert video_diag["duration"] > 0, f"Duration is {video_diag['duration']} (expected > 0)"
        assert video_diag["videoWidth"] > 0, f"Video width is {video_diag['videoWidth']} (expected > 0)"

        # Save screenshot
        shot_path = "C:/Users/Hp/.gemini/antigravity/brain/8ae4ae20-391d-4302-8aeb-5150ef4d3f19/chat_video_fixed_verified.png"
        await page.screenshot(path=shot_path)
        print(f"SUCCESS: Video verified playing cleanly in chat! Screenshot saved to: {shot_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_chat())

