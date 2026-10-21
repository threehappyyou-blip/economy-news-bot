// Captures a true-alpha PNG sequence (0-15000ms, 30fps) of the ENTIRE 5-scene
// overlay (chip/badge/progress-bar/kicker/headline/mascot, across all 5
// scenes) with a transparent backdrop, for compositing onto a single
// AI-generated background clip that now runs for the whole video — not just
// scene 1 — so the visual quality stays consistent start to finish instead of
// dropping to a flat CSS gradient after the opening 3 seconds.
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
const DURATION_MS = 15000;
const NUM_FRAMES = Math.round(DURATION_MS / 1000 * FPS); // 450

(async () => {
  const outDir = path.resolve(__dirname, 'overlay_frames');
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();

  const context = await browser.newContext({
    viewport: { width: 1080, height: 1920 },
    // Capture at 2x pixel density (2160x3840 physical pixels, same 1080x1920
    // CSS layout) — this is pure supersampling: the text and mascot edges
    // get anti-aliased at a higher resolution, then the compositing step
    // (daily-short.yml) downsamples back to 1080x1920 with a high-quality
    // scaler, which is what actually produces the crisper look in the final
    // video. Zero extra AI cost, just a bit more render/encode time.
    deviceScaleFactor: 2,
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
      // force a synchronous style/layout flush so the seek is fully applied
      // before we ask the compositor to paint it
      void document.body.offsetHeight;
    }, t);
    // Wait two animation frames so the browser has actually painted the
    // post-seek state before we screenshot. Without this, under slower/busier
    // CI runners the screenshot can land mid-repaint and capture a blend of
    // the old and new frame — visible as "ghosted"/doubled text.
    await page.evaluate(() => new Promise((resolve) => {
      requestAnimationFrame(() => requestAnimationFrame(resolve));
    }));
    const frameFile = path.join(outDir, `frame_${String(i).padStart(4, '0')}.png`);
    await page.screenshot({ path: frameFile, omitBackground: true });
  }

  await context.close();
  await browser.close();
  console.log(`DONE: ${NUM_FRAMES} frames in ${outDir}`);
})();
