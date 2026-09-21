const fs = require('fs');
const path = require('path');
const hooks = JSON.parse(fs.readFileSync(path.join(__dirname, 'hooks.json'), 'utf8'));

// deterministic daily pick: day-of-year mod bank length (KST date, so it matches the 07:00 KST send)
const now = new Date();
const kstNow = new Date(now.getTime() + 9 * 60 * 60 * 1000); // shift to KST
const startOfYear = new Date(Date.UTC(kstNow.getUTCFullYear(), 0, 0));
const doy = Math.floor((kstNow - startOfYear) / 86400000);
const idx = doy % hooks.length;
const h = hooks[idx];

let tpl = fs.readFileSync(path.join(__dirname, 'scene_template.html'), 'utf8');
tpl = tpl.replace('__S1_KICKER__', h.kicker).replace('__S1_HOOK__', h.hook_html);
fs.writeFileSync(path.join(__dirname, 'scene.html'), tpl);
fs.writeFileSync(path.join(__dirname, 'today.json'), JSON.stringify(h));
console.log(`Using hook #${idx} of ${hooks.length}: "${h.hook_plain}"`);
