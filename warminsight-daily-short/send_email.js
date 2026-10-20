const fs = require('fs');
const path = require('path');
const nodemailer = require('nodemailer');

(async () => {
  const today = JSON.parse(fs.readFileSync(path.join(__dirname, 'today.json'), 'utf8'));
  const caption = fs.readFileSync(path.join(__dirname, 'caption_and_tags.md'), 'utf8');
  const dateStr = new Date().toISOString().slice(0, 10);
  const videoFiles = fs.readdirSync(__dirname).filter(f => f.startsWith('warminsight_short_') && f.endsWith('.mp4'));
  if (videoFiles.length === 0) {
    throw new Error('No warminsight_short_*.mp4 file found to attach — did build/record/encode run first?');
  }
  const videoPath = path.join(__dirname, videoFiles[0]);

  const GMAIL_USER = process.env.GMAIL_USER;
  const GMAIL_APP_PASSWORD = process.env.GMAIL_APP_PASSWORD;
  const TO_EMAIL = process.env.TO_EMAIL || 'jh0116jh@gmail.com';

  if (!GMAIL_USER || !GMAIL_APP_PASSWORD) {
    throw new Error('Missing GMAIL_USER or GMAIL_APP_PASSWORD environment variables (set as GitHub repo secrets).');
  }

  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: { user: GMAIL_USER, pass: GMAIL_APP_PASSWORD },
  });

  await transporter.sendMail({
    from: `"Warm Insight Daily Short" <${GMAIL_USER}>`,
    to: TO_EMAIL,
    subject: `Warm Insight Daily Short — ${dateStr} — ${today.hook_plain}`,
    text: caption,
    attachments: [
      {
        filename: `warminsight_short_${dateStr}.mp4`,
        path: videoPath,
        contentType: 'video/mp4',
      },
    ],
  });

  console.log(`Email sent to ${TO_EMAIL} with attachment ${videoFiles[0]}`);
})().catch(err => {
  console.error(err);
  process.exit(1);
});
