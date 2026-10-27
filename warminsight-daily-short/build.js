const fs = require('fs');
const path = require('path');
const hooks = JSON.parse(fs.readFileSync(path.join(__dirname, 'hooks.json'), 'utf8'));
const content = JSON.parse(fs.readFileSync(path.join(__dirname, 'scene_content.json'), 'utf8'));

// Every generation picks a fresh, random combination — scene 1's hook, scene
// 2/3/4's headline+sub, and scene 5's kicker line are each drawn
// independently from their own bank. That means every single run (not just
// every day) produces a different script, which matters now that this video
// is being used as an ad: running the workflow multiple times gives multiple
// genuinely different creatives instead of the same video over and over.
function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

const s1 = pick(hooks);
const s2 = pick(content.s2);
const s3 = pick(content.s3);
const s4 = pick(content.s4);
const s5Kicker = pick(content.s5_kicker);
const teaser = pick(content.teaser);

let tpl = fs.readFileSync(path.join(__dirname, 'scene_template.html'), 'utf8');
tpl = tpl
  .replace('__S1_KICKER__', s1.kicker)
  .replace('__S1_HOOK__', s1.hook_html)
  .replace('__S2_HEADLINE__', s2.headline_html)
  .replace('__S2_SUB__', s2.sub)
  .replace('__S3_HEADLINE__', s3.headline_html)
  .replace('__S3_SUB__', s3.sub)
  .replace('__S4_HEADLINE__', s4.headline_html)
  .replace('__S4_SUB__', s4.sub)
  .replace('__S5_KICKER__', s5Kicker)
  .replace('__TEASER__', teaser);
fs.writeFileSync(path.join(__dirname, 'scene.html'), tpl);

// today.json carries everything downstream steps need: fal_video.js logs the
// hook, gen_caption.js builds the social captions from hook_plain + the
// scene 2-4 sub lines (so captions/hashtag copy stay in sync with what's
// actually on screen this run instead of always describing the same fixed
// script).
const today = {
  kicker: s1.kicker,
  hook_html: s1.hook_html,
  hook_plain: s1.hook_plain,
  s2_sub: s2.sub,
  s3_sub: s3.sub,
  s4_sub: s4.sub,
  s5_kicker: s5Kicker,
  teaser,
};
fs.writeFileSync(path.join(__dirname, 'today.json'), JSON.stringify(today));
console.log(`Hook: "${s1.hook_plain}"`);
console.log(`Scene 2: "${s2.sub}"`);
console.log(`Scene 3: "${s3.sub}"`);
console.log(`Scene 4: "${s4.sub}"`);
console.log(`Scene 5 kicker: "${s5Kicker}"`);
console.log(`Teaser: "${teaser}"`);
