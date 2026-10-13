// Captures a true-alpha PNG sequence (0-3000ms, ~30fps) of ONLY the scene-1
// overlay (chip/badge/progress-bar/kicker/headline/mascot) with a transparent
// backdrop, for later compositing onto an AI-generated background clip.
//
// Strategy: instead of trying to screenshot a live video at precise
// wall-clock offsets (unreliable timing), we freeze the page's animation
// clock via the Web Animations API by setting each Animation's
// `currentTime` directly after disabling the natural ticking. Simpler and
// much more deterministic: we just load the page, and for each target
// frame time we seek every running Animation to that time with
// `animation.currentTime = t`, then screenshot. This avoids real-time
// drift entirely.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const FPS = 30;
const DURATION_MS = 3000;
const NUM_FRAMES = Math.round(DURATION_MS / 1000 * FPS); // 90

(async () => {
  const outDir = path.resolve(__dirname, 'overlay_frames');
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();

  const context = await browser.newContext({
    viewport: { width: 1080, height: 1920 },
  });
  const page = await context.newPage();
  const filePath = 'file://' + path.resolve(__dirname, 'scene.html') + '?transparent=1';
  await page.goto(filePath);

  // Let the page's own script run (it kicks off WAAPI animations immediately on load).
  await page.waitForTimeout(50);

  for (let i = 0; i < NUM_FRAMES; i++) {
    const t = Math.round(i * (1000 / FPS));
    // Seek every running animation on the page to time t (ms), pausing it first.
    await page.evaluate((tt) => {
      document.getAnimations().forEach(a => {
        try { a.pause(); a.currentTime = tt; } catch (e) {}
      });
    }, t);
    const frameFile = path.join(outDir, `frame_${String(i).padStart(4, '0')}.png`);
    await page.screenshot({ path: frameFile, omitBackground: true });
  }

  await context.close();
  await browser.close();
  console.log(`DONE: ${NUM_FRAMES} frames in ${outDir}`);
})();
