// Generates today's 3-second AI background clip for scene 1 via Higgsfield AI,
// and saves it as higgsfield_bg.mp4 in this folder.
//
// Requires env vars (set as GitHub Actions secrets):
//   HF_API_KEY_ID, HF_API_KEY_SECRET  (from the Higgsfield Console -> API Keys)
//
// NOTE: the exact model id slug and the exact shape of the result object are
// not yet verified against a live Higgsfield account (no API key was available
// while writing this). This script is defensive: it logs the full raw result
// so a failure is diagnosable, and it tries several plausible field names for
// the output video URL before giving up. If Higgsfield's API differs from what's
// assumed here, update HF_MODEL / the field-name list below after checking one
// real response (console.log output from a manual `node higgsfield_video.js` run
// will show exactly what came back).
const fs = require('fs');
const path = require('path');
const https = require('https');

const HF_MODEL = process.env.HF_MODEL || 'wan2.7-text-to-video'; // TODO: confirm exact slug in Higgsfield Console / docs
const OUT_FILE = path.join(__dirname, 'higgsfield_bg.mp4');

// today's hook (build.js already ran and wrote today.json before this script runs)
const today = JSON.parse(fs.readFileSync(path.join(__dirname, 'today.json'), 'utf8'));

// Keep the prompt generic/brand-safe and visually energetic — this is just a
// 3-second abstract/motion backdrop that the existing text+mascot overlay sits
// on top of, not a scene that needs to "mean" anything on its own.
const PROMPT = `Abstract energetic financial growth motion background, warm amber and deep navy gradient light streaks, soft bokeh particles drifting upward, subtle glowing lines like a stock chart trending up, cinematic, smooth camera drift, vertical 9:16 framing, no text, no logos, no people`;

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

function findVideoUrl(result) {
  // Try the plausible shapes the Higgsfield API might return, in order.
  const candidates = [
    result?.video?.url,
    result?.videos?.[0]?.url,
    result?.output?.url,
    result?.output?.video?.url,
    result?.results?.[0]?.url,
    result?.result?.video?.url,
    result?.url,
    typeof result?.output === 'string' ? result.output : undefined,
  ];
  return candidates.find(u => typeof u === 'string' && u.startsWith('http'));
}

(async () => {
  if (!process.env.HF_API_KEY_ID || !process.env.HF_API_KEY_SECRET) {
    console.log('HF_API_KEY_ID / HF_API_KEY_SECRET not set — skipping Higgsfield generation, scene 1 will use the plain gradient background instead.');
    process.exitCode = 0;
    return;
  }

  const { config, higgsfield } = require('@higgsfield/client/v2');
  config({ credentials: `${process.env.HF_API_KEY_ID}:${process.env.HF_API_KEY_SECRET}` });

  console.log(`Requesting Higgsfield clip (model: ${HF_MODEL}) for hook: "${today.hook_plain}"`);

  let result;
  try {
    result = await higgsfield.subscribe(HF_MODEL, {
      input: {
        prompt: PROMPT,
        duration: 3,
        aspect_ratio: '9:16',
      },
      withPolling: true,
    });
  } catch (err) {
    console.error('Higgsfield generation failed:', err.message || err);
    console.log('Falling back to the plain gradient background for scene 1.');
    process.exitCode = 0; // non-fatal: the workflow will fall back to a plain bg
    return;
  }

  console.log('Raw Higgsfield result:', JSON.stringify(result, null, 2));

  const videoUrl = findVideoUrl(result);
  if (!videoUrl) {
    console.error('Could not find a video URL in the Higgsfield response. See the raw result logged above and update findVideoUrl() in higgsfield_video.js accordingly.');
    process.exitCode = 0; // non-fatal
    return;
  }

  console.log('Downloading generated clip from:', videoUrl);
  await downloadFile(videoUrl, OUT_FILE);
  console.log('Saved Higgsfield background clip to', OUT_FILE);
})();
