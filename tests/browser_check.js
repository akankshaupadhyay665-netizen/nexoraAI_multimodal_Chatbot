const { chromium } = require('playwright');

(async () => {
  console.log('Launching browser to inspect http://127.0.0.1:5500 ...');
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', msg => console.log(`[BROWSER CONSOLE ${msg.type()}]`, msg.text()));
  page.on('pageerror', err => console.error('[BROWSER UNCAUGHT ERROR]', err.message));

  try {
    const res = await page.goto('http://127.0.0.1:5500/', { waitUntil: 'networkidle', timeout: 15000 });
    console.log('Page loaded with status:', res.status());

    await page.waitForTimeout(2000);

    // Check globals
    const globals = await page.evaluate(() => ({
      hasTHREE: typeof THREE !== 'undefined',
      hasNexoraApp: typeof window.nexoraApp !== 'undefined',
      hasNexoraChat: typeof window.nexoraChat !== 'undefined',
      hasNexoraRobot: typeof window.nexoraRobotInstance !== 'undefined',
      canvasCount: document.querySelectorAll('canvas').length,
      sendBtnVisible: !!document.getElementById('send-btn'),
      chatInputVal: document.getElementById('chat-input')?.value
    }));
    console.log('Evaluated Globals in Browser:', globals);

    // Try typing in chat and clicking Send
    console.log('Testing chat input and send button in browser...');
    await page.fill('#chat-input', 'Hello, how are you?');
    await page.click('#send-btn');

    await page.waitForTimeout(3000);

    const chatMessages = await page.evaluate(() => {
      const msgs = document.querySelectorAll('.chat-bubble-row');
      return Array.from(msgs).map(m => ({
        class: m.className,
        text: m.innerText
      }));
    });
    console.log('Chat messages after send:', chatMessages);

  } catch (e) {
    console.error('Test error:', e);
  } finally {
    await browser.close();
  }
})();
