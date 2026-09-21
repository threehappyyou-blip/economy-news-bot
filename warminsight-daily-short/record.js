const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const outDir = path.resolve(__dirname, 'raw_video');
  const browser = await chromium.launch({
    args: ['--autoplay-policy=no-user-gesture-required']
  });
  const context = await browser.newContext({
    viewport: { width: 1080, height: 1920 },
    recordVideo: { dir: outDir, size: { width: 1080, height: 1920 } }
  });
  const page = await context.newPage();
  const filePath = 'file://' + path.resolve(__dirname, 'scene.html');
  await page.goto(filePath);

  const doneAt = await page.evaluate(() => window.__DONE_AT__ || 15300);
  await page.waitForTimeout(doneAt);

  await context.close();
  await browser.close();
  console.log('DONE');
})();
