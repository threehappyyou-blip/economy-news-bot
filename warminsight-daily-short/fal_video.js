// Generates today's AI background clip via fal.ai (Kling 2.5 Turbo Pro,
// text-to-video), and saves it as ai_bg_raw.mp4 in this folder. Runs daily
// as part of the GitHub Actions workflow.
//
// This raw 5s clip is NOT the final background by itself anymore — a later
// workflow step ("Extend AI background to full 15s") boomerang-loops it
// (forward + reverse + forward) into a seamless 15s clip that now runs
// behind the ENTIRE video, not just the opening 3s scene. That's what fixes
// the old "AI background only in scene 1, flat CSS gradient after that"
// quality drop. Since it's the same single generated clip just looped, the
// per-video AI cost is unchanged (~$0.35 for one 5s Kling generation).
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
// 5s clip and loop/extend it to cover the full 15s video (see above).
const fs = require('fs');
const path = require('path');
const https = require('https');

const MODEL = 'fal-ai/kling-video/v2.5-turbo/pro/text-to-video';
const OUT_FILE = path.join(__dirname, 'ai_bg_raw.mp4');

const today = JSON.parse(fs.readFileSync(path.join(__dirname, 'today.json'), 'utf8'));

// A bank of visual themes, not one fixed prompt — the video is used as an ad
// now, so every generation should look different, not just the copy. All of
// them stay on-brand (warm amber on deep navy, cinematic) and all of them
// describe slow, continuous motion with no sudden cuts, which is what lets
// the boomerang-loop step (forward+reverse+forward) extend a 5s clip to 15s
// with no visible seam.
const BG_THEMES = [
  'Abstract energetic financial growth motion background, warm amber and deep navy gradient light streaks, soft bokeh particles drifting slowly upward, subtle glowing lines like a stock chart trending up, cinematic, slow continuous smooth camera drift with no sudden cuts or fast motion, seamless loopable ambience, no text, no logos, no people',
  'Abstract glowing candlestick chart bars rising gently in warm amber light against a deep navy night sky, soft depth-of-field bokeh, subtle upward camera drift, cinematic financial growth atmosphere, slow continuous motion, seamless loopable ambience, no text, no logos, no people',
  'A vast glowing network of golden connected nodes and lines pulsing softly like a financial data constellation, deep navy background, warm amber highlights, slow cinematic camera drift, seamless loopable ambience, no text, no logos, no people',
  'Warm amber aurora-like light waves flowing slowly across a deep navy gradient sky, soft glowing particles drifting, cinematic and premium, slow continuous camera drift, seamless loopable ambience, no text, no logos, no people',
  'An abstract upward-trending glowing line chart made of light, warm amber on deep navy, soft bokeh stars in the background, subtle cinematic camera drift, premium financial growth atmosphere, seamless loopable ambience, no text, no logos, no people',
  'Soft glowing geometric grid lines receding into a deep navy horizon with warm amber light accents, gentle floating particles, cinematic depth, slow continuous camera drift, seamless loopable ambience, no text, no logos, no people',
  'Warm golden light trails flowing slowly like a river of light through a deep navy abstract space, soft bokeh, cinematic premium finance aesthetic, slow continuous camera drift, seamless loopable ambience, no text, no logos, no people',
];
const PROMPT = BG_THEMES[Math.floor(Math.random() * BG_THEMES.length)];

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
