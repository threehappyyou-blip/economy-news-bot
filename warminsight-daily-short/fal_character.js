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
//
// IMPORTANT: Ideogram Character returns a flat opaque (white-background) PNG,
// not a transparent one, even when the prompt asks for "transparent
// background" — it's a raster model, not an alpha-aware one. The first real
// render showed exactly this: an ugly white square around the mascot. So every
// generated pose is run through a background-removal model (fal-ai/bria/
// background/remove) before being saved, producing a true alpha-transparent
// PNG that composites cleanly in scene_template.html.
//   model: fal-ai/bria/background/remove
//   input: { image_url }
//   result: result.data.image.url
const fs = require('fs');
const path = require('path');
const https = require('https');

const MODEL = 'fal-ai/ideogram/character';
const BG_REMOVE_MODEL = 'fal-ai/bria/background/remove';
const ASSETS_DIR = path.join(__dirname, 'assets');
const REFERENCE_PNG = path.join(__dirname, 'mascot_reference.png');

// Style note: the daily video now composites this mascot onto a cinematic
// AI-generated video background (soft bokeh, gradient light streaks, warm
// amber/navy palette — see fal_video.js), not a flat CSS color. A flat
// "minimalist vector illustration" mascot looked jarringly out of place
// against that — like a sticker pasted on a photo. So every pose prompt now
// explicitly asks for a soft 3D glossy render (think Pixar-style / Apple
// emoji 3D icon) with the SAME identity (round egg body, warm cream-peach
// color, big sparkling eyes, rosy cheeks, glowing insight-spark accent) —
// Ideogram Character keeps the character's identity from the reference
// image while still following the prompt's rendering-style instructions, so
// this keeps the approved look but renders it in a way that blends with a
// photoreal/cinematic backdrop instead of clashing with it.
const STYLE = 'rendered in a soft 3D glossy toy-like style (like a Pixar character or a 3D emoji), smooth matte-glossy plastic/clay material, gentle cinematic rim lighting and soft contact shadow, warm cream-to-peach gradient shading on the body, NOT flat, NOT 2D vector, NOT a flat illustration';

const POSES = [
  { file: 'mascot_hype.png', prompt: `the same cute round egg-shaped mascot character, big sparkling round eyes with a bright catchlight, rosy cheeks, open cheerful mouth, a small glowing golden spark accent near its head, both arms raised up excitedly in celebration, ${STYLE}, floating against a plain neutral softly-lit background, no text` },
  { file: 'mascot_present.png', prompt: `the same cute round egg-shaped mascot character, big sparkling round eyes with a bright catchlight, rosy cheeks, warm smile, a small glowing golden spark accent near its head, right arm raised up in a friendly presenting gesture, left arm relaxed down, ${STYLE}, floating against a plain neutral softly-lit background, no text` },
  { file: 'mascot_wave.png', prompt: `the same cute round egg-shaped mascot character, big sparkling round eyes with a bright catchlight, rosy cheeks, warm smile, a small glowing golden spark accent near its head, right arm raised waving hello, left arm relaxed down, ${STYLE}, floating against a plain neutral softly-lit background, no text` },
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

    console.log(`  Removing background from ${pose.file} ...`);
    let finalUrl = url;
    try {
      const bgResult = await fal.subscribe(BG_REMOVE_MODEL, {
        input: { image_url: url },
        logs: true,
      });
      const transparentUrl = bgResult?.data?.image?.url;
      if (transparentUrl) {
        finalUrl = transparentUrl;
      } else {
        console.error(`  Background removal returned no URL for ${pose.file}, saving the opaque version instead:`, JSON.stringify(bgResult, null, 2));
      }
    } catch (err) {
      console.error(`  Background removal failed for ${pose.file}, saving the opaque version instead:`, err.message || err);
    }

    const dest = path.join(ASSETS_DIR, pose.file);
    await downloadFile(finalUrl, dest);
    console.log(`Saved ${dest}`);
  }
  console.log('Done. Commit the assets/ folder so the daily workflow reuses these images at zero extra cost.');
})();
