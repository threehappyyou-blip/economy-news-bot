// ONE-OFF script: generates the 3 static mascot pose images via Higgsfield's
// "Soul" character model and saves them into assets/. This is NOT part of the
// daily workflow — run it manually once (locally, or as a one-time manual
// GitHub Actions dispatch) whenever you want to (re)generate the mascot look.
// The daily pipeline just reuses these 3 cached PNGs forever, so the ongoing
// Soul cost is $0 — only the video clip is generated daily.
//
// Usage:
//   HF_API_KEY_ID=... HF_API_KEY_SECRET=... node higgsfield_soul.js
//
// NOTE: exact model slug / response shape unverified — see the comment in
// higgsfield_video.js. Check the logged raw result on first run and adjust
// findImageUrl() below if needed.
const fs = require('fs');
const path = require('path');
const https = require('https');

const HF_MODEL = process.env.HF_SOUL_MODEL || 'soul-2'; // TODO: confirm exact slug
const ASSETS_DIR = path.join(__dirname, 'assets');

// Keep one consistent character description across all 3 poses so Soul's
// character-consistency feature keeps them looking like the same mascot.
// Direction (per user feedback): cuter, and should visually read as "insight" /
// a moment of realization — not just a plain cute blob — matching the
// "Warm Insight" brand. The hand-drawn SVG fallback already prototypes this
// with bigger sparkling eyes + a small glowing spark/star accent near the head;
// carry that same idea into the Soul prompt so the look stays consistent
// whichever renders (SVG fallback or the real Soul image).
const CHARACTER = 'an extremely cute, round egg-shaped mascot character for a warm personal-finance brand, glossy warm cream-to-amber gradient skin, two tiny stubby legs, big bright sparkling eyes with a tiny white highlight in each (conveys sudden understanding / "aha" clarity, not a blank stare), soft rosy cheeks, a small glowing amber 4-point spark/star icon floating just beside its head like a lightbulb moment, soft warm glow around the character, minimalist flat vector illustration style, adorable chibi proportions, centered, plain transparent background, no text';

const POSES = [
  { file: 'mascot_hype.png', prompt: `${CHARACTER}, both arms raised up excitedly, open cheerful mouth, celebrating pose` },
  { file: 'mascot_present.png', prompt: `${CHARACTER}, right arm raised up in a friendly presenting gesture, left arm relaxed down, warm smile` },
  { file: 'mascot_wave.png', prompt: `${CHARACTER}, right arm raised waving hello, left arm relaxed down, warm smile` },
];

function findImageUrl(result) {
  const candidates = [
    result?.image?.url,
    result?.images?.[0]?.url,
    result?.output?.url,
    result?.output?.image?.url,
    result?.results?.[0]?.url,
    result?.result?.image?.url,
    result?.url,
    typeof result?.output === 'string' ? result.output : undefined,
  ];
  return candidates.find(u => typeof u === 'string' && u.startsWith('http'));
}

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
  if (!process.env.HF_API_KEY_ID || !process.env.HF_API_KEY_SECRET) {
    console.error('Set HF_API_KEY_ID and HF_API_KEY_SECRET before running this script.');
    process.exit(1);
  }
  fs.mkdirSync(ASSETS_DIR, { recursive: true });

  const { config, higgsfield } = require('@higgsfield/client/v2');
  config({ credentials: `${process.env.HF_API_KEY_ID}:${process.env.HF_API_KEY_SECRET}` });

  for (const pose of POSES) {
    console.log(`Generating ${pose.file} ...`);
    const result = await higgsfield.subscribe(HF_MODEL, {
      input: { prompt: pose.prompt, aspect_ratio: '1:1' },
      withPolling: true,
    });
    console.log('Raw result:', JSON.stringify(result, null, 2));
    const url = findImageUrl(result);
    if (!url) {
      console.error(`Could not find an image URL for ${pose.file} — see raw result above and fix findImageUrl().`);
      continue;
    }
    const dest = path.join(ASSETS_DIR, pose.file);
    await downloadFile(url, dest);
    console.log(`Saved ${dest}`);
  }
  console.log('Done. Commit the assets/ folder so the daily workflow can reuse these images at zero extra cost.');
})();
