// Generates today's AI background clip for scene 1 via fal.ai (Kling 2.5
// Turbo Pro, text-to-video), and saves it as fal_bg.mp4 in this folder.
// Runs daily as part of the GitHub Actions workflow.
//
// Requires env var FAL_KEY (set as a GitHub Actions secret), picked up
// automatically by the @fal-ai/client SDK.
//
// Verified against fal.ai's own docs (fal.ai/models/fal-ai/kling-video/
// v2.5-turbo/pro/text-to-video/api):
//   model: fal-ai/kling-video/v2.5-turbo/pro/text-to-video
//   input: { prompt, duration: "5"|"10", aspect_ratio: "16:9"|"9:16"|"1:1" }
//   result: result.data.video.url
// Note: Kling only supports 5s or 10s clips (no 3s option) — we generate a
// 5s clip and the compositing step (ffmpeg -t 3) trims it to the 3s scene 1
// slot, so this still fits the per-video cost target (~$0.35 for 5s).
const fs = require('fs');
const path = require('path');
const https = require('https');

const MODEL = 'fal-ai/kling-video/v2.5-turbo/pro/text-to-video';
const OUT_FILE = path.join(__dirname, 'ai_bg.mp4');

const today = JSON.parse(fs.readFileSync(path.join(__dirname, 'today.json'), 'utf8'));

// Generic/brand-safe energetic backdrop — this just sits behind the existing
// text+mascot overlay for 3s, it doesn't need to "mean" anything on its own.
const PROMPT = `Abstract energetic financial growth motion background, warm amber and deep navy gradient light streaks, soft bokeh particles drifting upward, subtle glowing lines like a stock chart trending up, cinematic, smooth camera drift, no text, no logos, no people`;

async function downloadFile(url, destPath) {
  await new Promise((resolve, reject) => {
    const file = fs.createWriteStream(destPath);
    https.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        downloadFile(res.headers.location, destPath).then(resolve).catch(reject);
        return;
      }
      if (res.statusCode !== 200) {
        reject(new Error(`Download failed: HTTP ${res.statusCode} for ${url}`));
        return;
      }
      res.pipe(file);
      file.on('finish', () => file.close(resolve));
    }).on('error', reject);
  });
}

(async () => {
  if (!process.env.FAL_KEY) {
    console.log('FAL_KEY not set — skipping AI background generation, scene 1 will use the plain gradient fallback instead.');
    process.exitCode = 0;
    return;
  }

  const { fal } = require('@fal-ai/client');

  console.log(`Requesting fal.ai Kling clip for hook: "${today.hook_plain}"`);

  let result;
  try {
    result = await fal.subscribe(MODEL, {
      input: {
        prompt: PROMPT,
        duration: '5',
        aspect_ratio: '9:16',
      },
      logs: true,
      onQueueUpdate: (status) => console.log('  ', status.status),
    });
  } catch (err) {
    console.error('fal.ai generation failed:', err.message || err);
    console.log('Falling back to the plain gradient background for scene 1.');
    process.exitCode = 0; // non-fatal: workflow falls back to a plain bg
    return;
  }

  const videoUrl = result?.data?.video?.url;
  if (!videoUrl) {
    console.error('No video URL in fal.ai result:', JSON.stringify(result, null, 2));
    process.exitCode = 0; // non-fatal
    return;
  }

  console.log('Downloading generated clip from:', videoUrl);
  await downloadFile(videoUrl, OUT_FILE);
  console.log('Saved fal.ai background clip to', OUT_FILE);
})();
