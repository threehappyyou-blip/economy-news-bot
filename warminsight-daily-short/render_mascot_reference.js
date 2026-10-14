// ONE-OFF helper: rasterizes the hand-drawn SVG mascot (the "hype" pose, which
// already has the big sparkling eyes + insight-spark accent the user approved)
// into a clean PNG. This PNG becomes the character REFERENCE image fed into
// fal.ai's Ideogram Character model (fal_character.js), so the AI-generated
// poses stay visually consistent with the character we already designed and
// previewed, rather than fal inventing its own unrelated look from text alone.
//
// Usage: node render_mascot_reference.js
// Output: mascot_reference.png (not committed — only the 3 final AI-generated
// poses in assets/ are committed; this is just an intermediate input).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  // Reuse the exact same mascotSVG()/constants from scene_template.html by
  // extracting just that function's source — keeps the reference image
  // perfectly in sync with whatever the live fallback mascot looks like.
  const tpl = fs.readFileSync(path.join(__dirname, 'scene_template.html'), 'utf8');
  const fnMatch = tpl.match(/function mascotSVG[\s\S]*?\n}/);
  const constMatch = tpl.match(/const ARM_UP_RIGHT[\s\S]*?const HAND_DOWN_LEFT.*?;/);
  if (!fnMatch || !constMatch) {
    console.error('Could not extract mascotSVG() from scene_template.html — has it changed shape?');
    process.exit(1);
  }

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"></head>
  <body style="margin:0;width:600px;height:700px;display:flex;align-items:center;justify-content:center;background:transparent;">
    <div id="root"></div>
    <script>
      ${constMatch[0]}
      ${fnMatch[0]}
      document.getElementById('root').innerHTML = mascotSVG(1, 'hype');
      const svg = document.querySelector('svg');
      svg.setAttribute('width', '500');
      svg.setAttribute('height', '615');
    </script>
  </body></html>`;

  const tmpFile = path.join(__dirname, '_mascot_ref_tmp.html');
  fs.writeFileSync(tmpFile, html);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 600, height: 700 } });
  await page.goto('file://' + tmpFile);
  await page.waitForTimeout(100);
  const outPath = path.join(__dirname, 'mascot_reference.png');
  await page.screenshot({ path: outPath, omitBackground: true });
  await browser.close();
  fs.unlinkSync(tmpFile);

  console.log('Saved reference image to', outPath);
})();
