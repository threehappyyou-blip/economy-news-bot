// ONE-OFF script: generates the 3 static mascot pose images via fal.ai's
// Ideogram Character model, using our own hand-drawn mascot (rendered by
// render_mascot_reference.js) as the character reference so the AI poses stay
// visually consistent with the design already approved, rather than inventing
// an unrelated look. NOT part of the daily workflow — run manually once:
//
//   FAL_KEY=xxxxx node render_mascot_reference.js && FAL_KEY=xxxxx node fal_character.js
//
// The daily pipeline just reuses the resulting 3 cached PNGs in assets/
// forever (ongoing cost: $0 — only the background clip is generated daily).
//
// Verified against fal.ai's own docs (docs.fal.ai / fal.ai/models/.../api):
//   model: fal-ai/ideogram/character
//   input: { prompt, reference_image_urls: [url], image_size }
//   result: result.data.images[0].url
const fs = require('fs');
const path = require('path');
const https = require('https');

const MODEL = 'fal-ai/ideogram/character';
const ASSETS_DIR = path.join(__dirname, 'assets');
const REFERENCE_PNG = path.join(__dirname, 'mascot_reference.png');

const POSES = [
  { file: 'mascot_hype.png', prompt: 'the same cute round egg-shaped mascot character, both arms raised up excitedly in celebration, open cheerful mouth, sparkling eyes, minimalist flat vector illustration, plain transparent/white background, no text' },
  { file: 'mascot_present.png', prompt: 'the same cute round egg-shaped mascot character, right arm raised up in a friendly presenting gesture, left arm relaxed down, warm smile, sparkling eyes, minimalist flat vector illustration, plain transparent/white background, no text' },
  { file: 'mascot_wave.png', prompt: 'the same cute round egg-shaped mascot character, right arm raised waving hello, left arm relaxed down, warm smile, sparkling eyes, minimalist flat vector illustration, plain transparent/white background, no text' },
];

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
    console.error('Set FAL_KEY before running this script.');
    process.exit(1);
  }
  if (!fs.existsSync(REFERENCE_PNG)) {
    console.error(`${REFERENCE_PNG} not found — run "node render_mascot_reference.js" first.`);
    process.exit(1);
  }
  fs.mkdirSync(ASSETS_DIR, { recursive: true });

  const { fal } = require('@fal-ai/client');
  // FAL_KEY env var is picked up automatically, no explicit config() call needed.

  console.log('Uploading reference image to fal storage...');
  const refBuffer = fs.readFileSync(REFERENCE_PNG);
  const refFile = new File([refBuffer], 'mascot_reference.png', { type: 'image/png' });
  const refUrl = await fal.storage.upload(refFile);
  console.log('Reference image URL:', refUrl);

  for (const pose of POSES) {
    console.log(`Generating ${pose.file} ...`);
    const result = await fal.subscribe(MODEL, {
      input: {
        prompt: pose.prompt,
        reference_image_urls: [refUrl],
        image_size: 'square_hd',
      },
      logs: true,
      onQueueUpdate: (status) => console.log(`  [${pose.file}]`, status.status),
    });
    const url = result?.data?.images?.[0]?.url;
    if (!url) {
      console.error(`No image URL in result for ${pose.file}:`, JSON.stringify(result, null, 2));
      continue;
    }
    const dest = path.join(ASSETS_DIR, pose.file);
    await downloadFile(url, dest);
    console.log(`Saved ${dest}`);
  }
  console.log('Done. Commit the assets/ folder so the daily workflow reuses these images at zero extra cost.');
})();
