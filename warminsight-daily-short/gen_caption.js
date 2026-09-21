const fs = require('fs');
const path = require('path');
const h = JSON.parse(fs.readFileSync(path.join(__dirname, 'today.json'), 'utf8'));
const hook = h.hook_plain;
const dateStr = new Date().toISOString().slice(0, 10);

const tiktokCaption = `${hook} Markets explained in 5 minutes, zero jargon — free daily newsletter. → https://warminsight.com`;
const reelsCaption = `${hook} 👀 Markets explained in 5 minutes — no jargon, ever. Free daily newsletter for total beginners.\nLink in bio → https://warminsight.com`;
const ytTitle = `${hook} #Shorts`;
const ytDesc = `${hook}\n\nMarkets explained in plain English — no jargon, ever. Warm Insight is a free 5-minute daily newsletter that breaks down what's actually moving markets, written for total beginners.\n\nJoin free → https://warminsight.com\n\n#Shorts #PersonalFinance #MoneyTips #FinancialLiteracy #InvestingForBeginners #MoneyExplained`;
const ytTags = 'personal finance, money tips, financial literacy, investing for beginners, finance newsletter, money explained simply, beginner investing, financial education, market news explained, warm insight, how markets work, money 101';
const hashtagsTikTok = '#PersonalFinance #MoneyTips #FinancialLiteracy #InvestingForBeginners #FinTok #MoneyExplained #Newsletter';
const hashtagsIG = '#PersonalFinance #MoneyTips #FinancialLiteracy #InvestingForBeginners #MoneyExplained #WealthBuilding #FinanceTips #MoneyMindset #BeginnerInvesting #FinancialFreedom #Newsletter #ReelsFinance';

const out = `# Warm Insight Daily Short — ${dateStr}
Hook used today: "${hook}"

## TikTok
${tiktokCaption}

${hashtagsTikTok}

## Instagram Reels
${reelsCaption}

${hashtagsIG}

## YouTube Shorts
Title: ${ytTitle}

Description:
${ytDesc}

Tags (paste into YouTube Studio tags field):
${ytTags}

---
Reminder: the video ships silent on purpose — add a trending native sound in-app after upload for better reach than baked-in music.
No watermark. 1080x1920, 15s, MP4.
`;

fs.writeFileSync(path.join(__dirname, 'caption_and_tags.md'), out);
console.log(out);
