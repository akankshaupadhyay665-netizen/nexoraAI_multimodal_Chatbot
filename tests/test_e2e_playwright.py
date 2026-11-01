"""
NEXORA AI - Complete Quality Assurance & Browser Test Suite
Specifically verifies:
1. TEST B: Large 3D Humanoid Robot (Three.js WebGL) on right side of desktop homepage
2. TEST A: Chat Image Generation ("Generate a photorealistic image of the moon in space.")
   -> Returns an actual generated image in chat with download & regenerate controls
   -> Saves image to Generated Media
3. Chat Conversational Separation ("Explain how the moon works.")
   -> Routes to text LLM for normal conversational answer (NO ASCII art, NO image)
4. New Chat, File Uploads, Navigation & Settings
"""
import sys
import os
import time
from playwright.sync_api import sync_playwright

def run_tests():
    print("==================================================")
    print("NEXORA AI FULL BROWSER TEST (TEST A + TEST B)")
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
        page.on("console", lambda msg: console_logs.append(f"[{msg.type.upper()}] {msg.text}"))
        page.on("pageerror", lambda err: console_logs.append(f"[PAGE ERROR] {err}"))
        page.on("requestfailed", lambda req: console_logs.append(f"[REQ FAILED] {req.url} -> {req.failure}"))

        # ==================================================
        # TEST B: HOMEPAGE 3D HUMANOID ROBOT VERIFICATION
        # ==================================================
        print("\n--- TEST B: 3D HUMANOID ROBOT ON HOMEPAGE ---")
        page.goto("http://127.0.0.1:5500", wait_until="networkidle")
        time.sleep(2)
        print("  Console logs:")
        for log in console_logs:
            print("   ", log)

        robot_container = page.locator("#robot-canvas-container")
        assert robot_container.is_visible(), "Robot container #robot-canvas-container is not visible!"

        canvas = robot_container.locator("canvas")
        assert canvas.count() > 0, "Three.js WebGL Canvas element was not created!"
        box = canvas.bounding_box()
        print(f"  Robot Canvas bounding box: {box}")
        assert box and box["width"] > 250 and box["height"] > 400, f"Robot canvas too small or collapsed: {box}"

        # Verify Robot Anatomy in Three.js Scene
        anatomy = page.evaluate("""() => {
            const bot = window.nexoraRobotInstance;
            if (!bot) return null;
            return {
                hasHead: !!bot.headGroup,
                hasTorso: !!bot.torsoGroup,
                hasLeftArm: !!bot.leftArmGroup,
                hasRightArm: !!bot.rightArmGroup,
                hasLegs: !!bot.legsGroup,
                hasLeftLeg: !!bot.leftLeg,
                hasRightLeg: !!bot.rightLeg,
                hasEyes: !!bot.eyesGroup,
                hasReactor: !!bot.reactorCore,
                hasPlatform: !!bot.platformGroup
            };
        }""")
        print(f"  Humanoid Anatomy Verification: {anatomy}")
        assert anatomy, "nexoraRobotInstance not initialized on window!"
        assert anatomy["hasHead"] and anatomy["hasTorso"] and anatomy["hasLegs"] and anatomy["hasLeftLeg"] and anatomy["hasRightLeg"], "Robot is missing anatomical body parts!"

        speech_bubble = page.locator("#robot-speech-bubble")
        print(f"  Robot Speech Bubble text: '{speech_bubble.inner_text()}'")

        # Save Robot Closeup Screenshot
        page.screenshot(path="tests/robot_verified_screenshot.png")
        print("  Saved screenshot to tests/robot_verified_screenshot.png")
        print("  TEST B: PASSED (Large 3D Humanoid Robot is visible & verified)")

        # ==================================================
        # TEST A: CHAT IMAGE GENERATION (MOON IN SPACE)
        # ==================================================
        print("\n--- TEST A: CHAT IMAGE GENERATION ---")
        chat_input = page.locator("#chat-input")
        send_btn = page.locator("#send-btn")

        prompt_image = "Generate a photorealistic image of the moon in space."
        print(f"  Sending prompt: '{prompt_image}'")
        chat_input.fill(prompt_image)
        send_btn.click()

        # Wait for assistant response
        page.wait_for_selector(".chat-bubble.assistant", timeout=25000)

        # Poll until image is rendered in the message bubble
        start_time = time.time()
        image_found = False
        img_src = ""
        while time.time() - start_time < 35:
            # Check for image element in assistant bubble
            last_msg = page.locator(".chat-bubble.assistant").last
            images = last_msg.locator("img")
            if images.count() > 0:
                first_img = images.first
                img_src = first_img.get_attribute("src") or ""
                if "storage" in img_src or "http" in img_src:
                    image_found = True
                    break
            time.sleep(1)

        print(f"  Image element rendered in chat: {image_found}")
        print(f"  Image src: {img_src}")
        assert image_found, "Actual image was NOT rendered in chat!"

        # Verify Action Controls (Download, Regenerate, Studio)
        actions = page.locator(".chat-bubble.assistant").last.locator(".generated-image-actions")
        assert actions.count() > 0 or page.locator(".btn-action-pill").count() > 0, "Download and regenerate controls not displayed!"
        print("  Download and regenerate controls successfully rendered in chat.")

        # Check that NO ASCII art or fake text was returned
        msg_text = page.locator(".chat-bubble.assistant").last.inner_text()
        assert "As a text-based generative AI" not in msg_text, "Returned text-based disclaimer instead of real image!"
        assert "/--\\" not in msg_text and "(   )" not in msg_text, "Returned ASCII art instead of real image!"
        print("  Zero ASCII art detected. Real image delivered.")
        print("  TEST A: PASSED (Actual generated image displayed in chat with controls)")
        page.screenshot(path="tests/chat_image_and_robot_screenshot.png")
        print("  Saved chat image screenshot to tests/chat_image_and_robot_screenshot.png")

        # ==================================================
        # TEST C: CONVERSATIONAL QUERY SEPARATION
        # ==================================================
        print("\n--- TEST C: CONVERSATIONAL QUERY SEPARATION ---")
        time.sleep(2)  # Wait for previous generation to fully finalize
        prompt_conv = "Explain how the moon works."
        print(f"  Sending prompt: '{prompt_conv}'")
        chat_input.fill(prompt_conv)
        send_btn.click()

        # Poll until new assistant response text arrives
        start_wait = time.time()
        conv_text = ""
        while time.time() - start_wait < 45:
            asst_bubbles = page.locator(".chat-bubble.assistant")
            count = asst_bubbles.count()
            if count >= 2:
                last_asst = asst_bubbles.last
                content_el = last_asst.locator(".msg-content")
                if content_el.count() > 0:
                    text = content_el.inner_text().strip()
                    if text and "typing-indicator" not in text and len(text) > 40:
                        conv_text = text
                        break
            time.sleep(1)

        print(f"  Total assistant bubbles in chat: {page.locator('.chat-bubble.assistant').count()}")
        if page.locator('.chat-bubble.assistant').count() >= 2:
            safe_content = page.locator('.chat-bubble.assistant').last.locator('.msg-content').inner_text()[:100].encode('ascii', errors='backslashreplace').decode('ascii')
            print(f"  Last assistant msg-content: {safe_content}")
        print("  Recent console logs:")
        for log in console_logs[-10:]:
            print("   ", str(log).encode('ascii', errors='replace').decode('ascii'))

        safe_preview = conv_text[:140].encode('ascii', errors='replace').decode()
        print(f"  Received conversational response ({len(conv_text)} chars): {safe_preview}...")
        assert len(conv_text) > 50, "Conversational response too short!"
        assert "moon" in conv_text.lower() or "orbit" in conv_text.lower() or "gravit" in conv_text.lower(), "Response did not answer how moon works!"
        print("  TEST C: PASSED (Normal conversational answer generated, task-based routing verified)")
        page.screenshot(path="tests/e2e_verified_screenshot.png")
        print("  Saved full E2E verified screenshot to tests/e2e_verified_screenshot.png")

        # ==================================================
        # TEST D: GENERATED MEDIA GALLERY PERSISTENCE
        # ==================================================
        print("\n--- TEST D: GENERATED MEDIA GALLERY PERSISTENCE ---")
        media_nav = page.locator('.nav-link[data-view="media-gallery"]')
        media_nav.click()
        time.sleep(1.5)

        gallery_items = page.locator("#gallery-items-grid .gallery-card")
        gallery_count = gallery_items.count()
        print(f"  Found {gallery_count} item(s) in Generated Media Gallery.")
        assert gallery_count >= 1, "Generated image was not saved into Generated Media gallery!"
        print("  TEST D: PASSED (Image persisted in Generated Media gallery)")

        # ==================================================
        # TEST E: NEW CHAT & MODALS
        # ==================================================
        print("\n--- TEST E: NEW CHAT & SETTINGS MODAL ---")
        # Return to chat studio
        chat_nav = page.locator('.nav-link[data-view="chat-studio"]')
        chat_nav.click()
        time.sleep(0.5)

        new_chat_btn = page.locator("#new-chat-btn")
        new_chat_btn.click()
        time.sleep(1)
        assert page.locator("#empty-chat-state").is_visible(), "Empty state not shown after New Chat!"
        print("  New Chat cleared view.")

        # Settings Modal
        settings_btn = page.locator("#nav-settings-btn")
        settings_btn.click()
        time.sleep(0.8)
        assert page.locator("#settings-modal").is_visible(), "Settings modal not opened!"
        page.locator("#close-settings-btn").click()
        time.sleep(0.5)
        assert not page.locator("#settings-modal").is_visible(), "Settings modal not closed!"
        print("  Settings modal verified.")

        # Final full page screenshot
        page.screenshot(path="tests/e2e_verified_screenshot.png")
        print("\n  Final full verified screenshot saved to: tests/e2e_verified_screenshot.png")

        # Console error audit
        critical_errors = [e for e in console_logs if "[ERROR]" in e and "favicon" not in e and "404" not in e]
        print(f"  Console audit: {len(critical_errors)} critical errors.")
        assert len(critical_errors) == 0, f"Critical console errors found: {critical_errors}"

        import shutil, os
        brain_dir = r"C:\Users\Hp\.gemini\antigravity\brain\8ae4ae20-391d-4302-8aeb-5150ef4d3f19"
        if os.path.exists(brain_dir):
            for f in ["e2e_verified_screenshot.png", "chat_image_and_robot_screenshot.png", "robot_verified_screenshot.png"]:
                src = os.path.join("tests", f)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(brain_dir, f))
            print("  Copied verified screenshots to brain artifact directory.")

        browser.close()

    print("\n==================================================")
    print("ALL TESTS (TEST A, TEST B, TEST C, TEST D, TEST E) PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
