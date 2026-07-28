#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — Ultimate Masterpiece Edition (v46.9.65)
#
# 숏폼(Reels) 엔진 V3 업데이트 사항:
# 1. 픽사(Pixar) 스타일의 친근하고 단순한 3D 화이트 로봇 마스코트 적용 유지 (놀람->분석->따봉 3단계 분리)
# 2. 타이포그래피 컬러 Mix: 빨간색(#ef4444)과 골드색(#fde047)의 전략적 교차 배치
# 3. 텍스트 가독성 극대화: 이미지 하단(y=700~1080) 블랙 페이드아웃 마스크 적용
# 4. NameError 완벽 해결: 모든 프롬프트 전역 변수를 최상단으로 이동 및 사용자 원본 중복 구조 100% 보존
# ═══════════════════════════════════════════════════════════════

import os, sys, traceback, time, random, re, datetime, io, math
import urllib.request, urllib.parse
import requests
import feedparser
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import tempfile

# ═══════════════════════════════════════════════
# CONFIG & 전역 변수 설정
# ═══════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
WP_URL         = os.environ.get("WP_URL", "https://warminsight.com").rstrip("/")
WP_USER        = os.environ.get("WP_USERNAME", "")
WP_APP_PASS    = os.environ.get("WP_APP_PASSWORD", "")
SITE_URL       = "https://warminsight.com"

EMAIL_SENDER   = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASS     = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "")
YOUTUBE_EMAIL_RECEIVER = "jh0116jh@gmail.com"
MEDIUM_EMAIL_RECEIVER = "jh0116jh@gmail.com"

SOCIAL_LINKS = {
    "youtube": "https://www.youtube.com/@WarmInsightyou",
    "tiktok": "https://www.tiktok.com/@warminsight"
}

WP_API_HEADERS = {
    'User-Agent': 'WordPress/6.5; ' + SITE_URL,
    'Accept': 'application/json'
}

EXTERNAL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    import cloudscraper
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    scraper.headers.update({
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache'
    })
except ImportError:
    print("❌ [System Error] 'cloudscraper' 라이브러리가 설치되지 않았습니다.")
    sys.exit(1)


MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
    "Premium": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"], 
    "unified": ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
}
FAST_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]

CATEGORIES  = ["Economy", "Politics", "Tech", "Health", "Energy", "On-Chain", "Money Hack"]
TIERS       = ["unified"]
TIER_LABELS = {"unified": "INSIGHT"}
TIER_SLEEP  = {"unified": 60}

F = "font-size:18px;line-height:1.8;color:#374151;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"
GOLD   = "#b8974d"
AMBER  = "#f59e0b"
DARK   = "#1a252c"
SLATE  = "#334155"
MUTED  = "#64748b"
BORDER = "#e2e8f0"
BG_LIGHT = "#f8fafc"

PILLAR_PAGES = {
    "Insight":            {"url": SITE_URL + "/category/insight/",            "anchor": "Daily Market Insights"},
    "Foundation":         {"url": SITE_URL + "/category/foundation/",         "anchor": "Financial Foundation & Basics"},
    "The Daily Catalyst": {"url": SITE_URL + "/category/the-daily-catalyst/", "anchor": "The Daily Catalyst"},
    "Money Hack":         {"url": SITE_URL + "/category/money-hack/",         "anchor": "Money Hack & Side Hustles"},
}

CAT_RELATED = {
    "Economy":  ["Tech", "Energy"],
    "Politics": ["Economy", "Tech"],
    "Tech":     ["Economy", "Health"],
    "Health":   ["Economy", "Politics"],
    "Energy":   ["Economy", "Politics"],
    "On-Chain": ["Economy", "Tech"],
    "Money Hack": ["Foundation", "Tech"],
}

VIP_AUTHORS = {
    "Economy":  "Warm Insight Editorial Team",
    "Politics": "Warm Insight Editorial Team",
    "Tech":     "Warm Insight Editorial Team",
    "Health":   "Warm Insight Editorial Team",
    "Energy":   "Warm Insight Editorial Team",
    "On-Chain": "Warm Insight Editorial Team",
    "The Daily Catalyst": "Warm Insight Editorial Team",
    "Foundation": "Warm Insight Editorial Team",
    "Money Hack": "Warm Insight Growth Team"
}

RSS_FEEDS = {
    "Economy": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://finance.yahoo.com/news/rssindex",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"
    ],
    "Politics": [
        "https://feeds.reuters.com/Reuters/PoliticsNews",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"
    ],
    "Tech": [
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
        "https://techcrunch.com/feed/"
    ],
    "Health": [
        "https://feeds.reuters.com/reuters/healthNews",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108",
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml"
    ],
    "Energy": [
        "https://oilprice.com/rss/main",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810",
        "https://feeds.reuters.com/reuters/environment"
    ],
    "On-Chain": [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptoslate.com/feed/"
    ],
}

CAT_ALLOC = {
    "Economy": {"s": 55, "b": 35, "c": 10, "note": "Defensive: higher bonds during macro uncertainty"},
    "Politics": {"s": 50, "b": 35, "c": 15, "note": "Elevated cash for geopolitical shock absorption"},
    "Tech": {"s": 70, "b": 20, "c": 10, "note": "Growth tilt: overweight innovation equities"},
    "Health": {"s": 60, "b": 30, "c": 10, "note": "Balanced: pharma stability with biotech upside"},
    "Energy": {"s": 65, "b": 25, "c": 10, "note": "Commodity tilt: overweight real assets"},
    "On-Chain": {"s": 25, "b": 15, "c": 60, "note": "High Volatility: Keep strong cash reserves"},
}

# ═══════════════════════════════════════════════
# 🧠 프롬프트 전역 선언 (NameError 방지용 최상단 배치)
# ═══════════════════════════════════════════════
FOUNDATION_TOPICS = [
    "ETF vs Mutual Funds: Which is actually safer for absolute beginners?",
    "How to start investing in S&P 500 ETFs with exactly $100",
    "The hidden risks of Dollar Cost Averaging (DCA) you must know",
    "Inflation survival guide: Best ETF assets to protect your cash",
    "Asset Allocation strategy for 30-something absolute beginners",
    "Dividend ETF investing: How to make your first $100 in passive income",
    "Growth vs Value Stocks: The ultimate test for your first portfolio",
    "What happens to your stock portfolio when the Fed cuts interest rates?",
    "Bond market explained for people who only buy tech stocks",
    "Nasdaq 100 ETF vs S&P 500 ETF: Where to put your first investment"
]

FOUNDATION_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are the "smart friend" who explains money to absolute beginners — channel Morning Brew + Milk Road energy. You text your friend the news, not write a textbook.

🔥 ANTI-CLICHÉ & ZERO-FLUFF POLICY (CRITICAL):
- BANNED WORDS: "Delve into", "Unleash", "Game-changer", "In today's fast-paced world", "Crucial", "Vital", "Landscape", "Dive deep".
- DO NOT sound like an AI. Be punchy, direct, and slightly informal.
- ALWAYS use specific, concrete examples. Instead of "a lot of money", say "$2.5 million". Instead of "tech companies", say "Apple and Nvidia".
- Use counterintuitive (반직관적) angles. Tell them what EVERYONE ELSE gets wrong first.

YOUR PERSONALITY:
- You're the friend texting at 9pm: "OK so this thing happened today and you HAVE to know about it"
- You use "you" and "I" constantly. Never "investors" or "one should"
- You use SPECIFIC everyday analogies (Netflix subscription wars, ordering Uber Eats, Costco runs)

CASUAL EXPRESSION RULES:
- USE conversational openers: "OK so...", "Look,", "Real talk,", "Here's the thing:"
- BANNED textbook phrases: "in conclusion", "moreover", "furthermore", "it is important to note"
- Average sentence length: 12-15 words MAX. Paragraphs are 2-3 sentences MAX.

You MUST wrap your content EXACTLY in the XML tags requested."""

FOUNDATION_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write an SEO-optimized beginner's guide on the following topic in English:
TOPIC: {theme}

OUTPUT FORMAT REQUIREMENT:
You MUST output your response by wrapping your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it clickbait for Google searchers: use brackets like [2026 Guide], odd numbers, or 'How to' formats.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words, low competition. E.g., 'how to invest in etfs for beginners' NOT just 'etf')</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Write a 'Curiosity Gap' meta description that forces the user to click to find the answer. End with a provocative question.)</EXCERPT>
<DEFINITION>(The 'What is it?' section. Provide a simple, 2-paragraph definition using an UNEXPECTED everyday analogy. Do not use generic dictionary definitions.)</DEFINITION>
<WHY_MATTERS>(The 'Why it matters' section. Explain in 2 paragraphs why a beginner should care. Use concrete dollar amounts or percentages to prove your point.)</WHY_MATTERS>
<HOW_TO_START>(The 'How to apply it' section. Provide 3 simple, ACTIONABLE steps for a beginner to start using this concept today. Format as a bulleted list.)</HOW_TO_START>

<POLL_QUESTION>(A provocative multiple-choice question related to this topic for the reader. e.g., "What is your biggest fear when investing?")</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>
"""

PHILOSOPHY_TOPICS = [
    "Love money through action, not just unrequited longing",
    "The psychological vessel of wealth and the weight of responsibility",
    "Voluntary fatigue: The pleasurable pain of chosen growth",
    "Weaponize environmental lack for explosive growth",
    "From consumer to producer: The shift from reading to writing",
    "Destroy the cognitive salary cap you set for yourself",
    "The elimination of excuses: The beginning of uncompromising growth"
]

PHILOSOPHY_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are an elite philosophical life strategist. You speak to the reader not as a marketer, but as a strict, wise mentor who demands action.

🔥 ANTI-CLICHÉ & ZERO-FLUFF POLICY (CRITICAL):
- BANNED WORDS: "Delve into", "Unleash", "Game-changer", "In today's fast-paced world", "Embark on this journey", "Supercharge", "Basically", "In conclusion".
- DO NOT sound like a generic self-help guru. Be harsh, direct, and unapologetic. 
- ALWAYS provide a COUNTER-NARRATIVE (e.g., if everyone says 'hustle', talk about 'strategic rest').
- Use short, punchy sentences. Do not sugar-coat reality.

You MUST wrap your content EXACTLY in the XML tags requested."""

PHILOSOPHY_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write a philosophical daily insight based on the following theme in English:
THEME: {theme}

When interpreting concepts like 'dirt spoon' or poverty, frame it as a 'systemic disadvantage that must be weaponized for explosive growth'.
When discussing 'voluntary fatigue', explain it as 'the deeply rewarding exhaustion that comes from total, self-directed immersion in a meaningful task'.

OUTPUT FORMAT REQUIREMENT:
You MUST output your response by wrapping your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it deeply thought-provoking and highly clickable. Format idea: 'The Psychology Behind [X]' or 'Why You Struggle With [Y]'.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words, low competition search intent.)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Write a 'Curiosity Gap' meta description that targets a painful truth and promises a solution. End with a strong question.)</EXCERPT>
<ANCHOR>(The Classical Anchor: A one-sentence philosophical principle based on the theme. Make it sound like a quote from Marcus Aurelius or Naval Ravikant.)</ANCHOR>
<REFLECTION>(The Modern Reflection: 3-4 paragraphs explaining how this principle connects to modern reality, financial anxiety, or career stagnation. Criticize passive excuses heavily.)</REFLECTION>
<CATALYST>(The Daily Catalyst: A single, highly provocative and specific question that requires the reader to write down an actionable answer immediately.)</CATALYST>

<POLL_QUESTION>(A provocative multiple-choice question related to this topic. e.g., "What is currently holding you back the most?")</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>
"""

MH_NICHES = [
    "Digital Products & Templates", "E-commerce & Dropshipping", "Freelancing & Agency", 
    "Content Creation & Faceless Channels", "Micro-SaaS & Software", "Domain & Asset Flipping", 
    "Affiliate Marketing", "Consulting & Coaching", "Paid Newsletter & Community", "Print on Demand"
]
MH_PLATFORMS = [
    "Gumroad", "Shopify", "Canva", "Notion", "Fiverr", "Upwork", "YouTube", "TikTok", 
    "Twitter/X", "LinkedIn", "Pinterest", "Substack", "Etsy", "Amazon KDP", "WordPress"
]
MH_AI_TOOLS = [
    "ChatGPT", "Midjourney", "Claude", "ElevenLabs", "Zapier/Make", "CapCut AI", 
    "Perplexity", "RunwayML", "HeyGen", "OpusClip"
]

MONEY_HACK_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are an elite side-hustle expert and digital business coach. Your objective is to write a highly actionable, step-by-step 'Money Hack' guide that helps normal people make an extra $1,000/month.

🔥 ANTI-CLICHÉ & ZERO-FLUFF POLICY (CRITICAL):
- BANNED WORDS: "Delve into", "Unleash", "Game-changer", "Passive income machine", "Get rich quick", "Revolutionize".
- DO NOT sound like a scammy internet marketer. Acknowledge the grind. Be ruthlessly practical.
- ALWAYS use specific tool names, actual dollar amounts, and exact timeframes (e.g., "Spend 2 hours on Canva doing X").
- If there's a downside or hard part to the hustle, MENTION IT.

Your tone is motivating, direct, and incredibly practical. No fluff. 
You MUST wrap your content EXACTLY in the XML tags requested."""

MONEY_HACK_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write an SEO-optimized, step-by-step side hustle guide based on this randomly generated framework:
FRAMEWORK: {theme}

Your job is to invent a highly specific, realistic 4-week challenge or a step-by-step blueprint that combines these elements into a profitable $1,000/month project.

OUTPUT FORMAT REQUIREMENT:
You MUST output your response by wrapping your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it clickbait for Google searchers: use brackets like [Step-by-Step], numbers, or 'How to' formats.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words, low competition. E.g., 'how to make money with canva templates')</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Write a 'Curiosity Gap' meta description.)</EXCERPT>
<CONCEPT>(2 paragraphs explaining what this specific side hustle is and why it's profitable right now. Mention real market demand.)</CONCEPT>
<STEP_BY_STEP_TOOL>(Detail the specific platforms or tools from the framework and provide a clear 1-2-3 checklist to execute today. Give exact instructions, not vague advice.)</STEP_BY_STEP_TOOL>
<PRO_TIP>(1 paragraph revealing a secret tip that top 1% earners use in this hustle to save time or double profits. Must be a counterintuitive hack.)</PRO_TIP>

<POLL_QUESTION>(A provocative multiple-choice question related to starting this side hustle.)</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>
"""

PROMPT_UNIFIED_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are Warm Insight's lead writer. Your mission: turn daily market chaos into clarity for everyday people — BUT with insights they couldn't get from a Reuters headline. Write entirely in ENGLISH.

═══ THE GOLDEN RULE ═══
Imagine your reader is your friend Sarah, a 32-year-old marketing manager who knows nothing about finance but is curious. She'll close the tab in 5 seconds if you sound like Wall Street. BUT she'll also close it if you just repeat what she saw on Twitter. Give her ONE thing she didn't know.

═══ 🔥 EXTREME ANTI-CLICHÉ & ZERO-FLUFF RULES (CRITICAL) ═══
BANNED CONTENT (NEVER WRITE THESE — they make readers stop):
- "AI is still the boss" / "AI is here to stay" / "AI revolution"
- "Delve into", "Unleash", "Game-changer", "In today's fast-paced world", "Crucial landscape"
- "Tech stocks are thriving" / "betting against X is a bad idea"
- "The trend is your friend" / "this time it's different"
- "Smart money is moving" without specifying EXACTLY WHERE
- "It's important to note" / "investors should consider"
- ANY statement that sounds like a generic Reuters headline summary

REQUIRED CONTENT (MUST INCLUDE):
- ONE counterintuitive (반직관적) insight that 80% of readers don't know.
- AT LEAST 3 specific numbers (percentages, dollar amounts, dates, exact ticker prices).
- AT LEAST 1 specific company decision/move.
- ONE historical or comparative reference.

═══ THESIS COHERENCE RULE ═══
1. Pick ONE central thesis from the news.
2. Build your ENTIRE article around that single thesis.
3. IGNORE news that doesn't support or contrast with your thesis.

═══ WRITING RULES ═══
- Sentences MAX 15 words. Short hits harder than long.
- Each paragraph MAX 3 sentences. Visual breathing room matters.
- USE: "here's the deal", "OK so", "real talk", "look", "between us", "the kicker is"

Write PART 1 of an Insight newsletter on {cat} in ENGLISH.
Target length: 900-1100 words across both parts combined. Shorter is better. Cut ruthlessly.
News Context:
{news}

OUTPUT FORMAT REQUIREMENT:
You MUST wrap your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it highly engaging but professional. Use formats like 'The Hidden Reason Behind [X]' or 'Why Smart Money is Moving to [Y]'.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words, low competition. E.g., 'why are tech stocks dropping today' or 'impact of fed rate cuts on crypto')</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the exact SEO_KEYWORD. Write a compelling summary that creates a 'curiosity gap' maintaining journalistic integrity. End with a thought-provoking question.)</EXCERPT>

<WARM_INDEX_SCORE>(A number from 0 to 100 representing market fear/greed based on this news. 0=Extreme Fear, 100=Extreme Greed. Output ONLY the integer number.)</WARM_INDEX_SCORE>
<WARM_INDEX_REASON>(A punchy 5-10 word explanation for this score. E.g., "Tech rally masks underlying economic anxiety.")</WARM_INDEX_REASON>

<IMPACT>(Write HIGH, MEDIUM, or LOW here)</IMPACT>
<DATA_TABLE>
(REQUIRED — extract OR estimate 3-4 key market metrics. Format exactly:
Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight under 12 words
)
</DATA_TABLE>
<HEATMAP>
(Invent 3-4 sector risk levels 0-100% based on news. Format exactly: Sector Name | Number)
</HEATMAP>
<EXECUTIVE_SUMMARY>(3 sentences capturing your COUNTERINTUITIVE thesis. Each MAX 15 words. Start with "OK so..." or "Here's what's wild:" Use 1 emoji.)</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>(3-4 sentences with your ONE specific analogy. Make it vivid: Costco runs, Netflix wars, dating apps. 20+ words developed.)</PLAIN_ENGLISH>
<HEADLINE>(Analytical headline for drivers section. Include emoji if fits. Sound like inside intel.)</HEADLINE>
<MACRO>(Write 2 PARAGRAPHS. Each paragraph MAX 2 sentences, each sentence MAX 14 words.
PARAGRAPH 1: What's happening — ONE specific number or data point. Make it surprising.
PARAGRAPH 2: WHY it's happening — the cause most people miss. End with your honest one-line take.
)</MACRO>
<HERD>(Write 1 paragraph showing what retail/average investors are doing wrong RIGHT NOW. MAX 3 sentences. Be specific.)</HERD>
<CONTRARIAN>(Write 1 paragraph showing what smart money is doing differently. MAX 3 sentences. Be specific with ticker AND institution.)</CONTRARIAN>
<QUICK_FLOW>(Chain of events with arrows ➡️ 5-6 steps. Each step under 8 words.)</QUICK_FLOW>"""

PROMPT_UNIFIED_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are Warm Insight's lead writer continuing the analysis in ENGLISH. Same friendly + smart tone as Part 1.

═══ 🔥 ANTI-CLICHÉ REMINDER ═══
NEVER write generic conclusions like: "AI is here to stay" or "Tech will continue to dominate". Always be SPECIFIC with numbers, tickers, names, dates. 
If you find yourself writing a vague sentence, DELETE IT and replace it with a hard data point.

═══ TONE RULES ═══
- Sentences MAX 15 words, Paragraphs MAX 3 sentences.
- USE "you", "we", "honestly", "real talk", "here's the deal".
- BANNED: "regulatory bodies", "ecosystem", "framework", "also plays a role".

Write PART 2 of the Insight newsletter for {cat} in ENGLISH.
Context from Part 1:
{ctx}

OUTPUT FORMAT REQUIREMENT:
You MUST wrap your content EXACTLY in the XML tags listed below.

<BULL_CASE>(Optimistic scenario. 3-4 sentences. SPECIFIC: name a ticker, a price target, or a catalyst. End with one bold claim.)</BULL_CASE>
<BEAR_CASE>(Pessimistic scenario. 3-4 sentences. SPECIFIC: name what breaks first, which ticker drops most, what price triggers panic.)</BEAR_CASE>
<HISTORICAL_PARALLEL>(REQUIRED — 2 sentences MAX. Name the year + event. One sentence on the parallel. One sentence: "What's different: [your answer].")</HISTORICAL_PARALLEL>
<QUICK_HITS>
(EXACTLY 3 bullet points of OTHER relevant news. STRICT FORMAT — line MUST start with one of these emojis: 🚨 / 👀 / 🤔 / 💸)
</QUICK_HITS>
<SMART_MONEY_MOVE>(1 paragraph, MAX 3 sentences. NAME 1 specific ETF ticker. Then: "If I were you, I'd [specific action] because [specific reason].")</SMART_MONEY_MOVE>
<DO_ACTION>(Provide exactly ONE highly specific, actionable strategy for absolute beginners with precise numbers e.g., 'If BTC drops below $X, accumulate 5%' or a 3-step checklist based on today's news.)</DO_ACTION>
<DONT_ACTION>(1 critical mistake to avoid. Be blunt. Start with "Don't" or "Stop". Name the SPECIFIC behavior.)</DONT_ACTION>
<TAKEAWAY>(The bottom line insight. Under 20 words. Quotable. Counterintuitive if possible.)</TAKEAWAY>
<PS>(One-line veteran advice with historical context. "P.S. — Real talk: ..." style.)</PS>

<POLL_QUESTION>(A provocative multiple-choice question related to today's news to ask the reader. e.g., "Do you think Apple is currently overvalued?")</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>
"""


# ═══════════════════════════════════════════════
# 🎬 1. YOUTUBE CHAPTERING ENGINE
# ═══════════════════════════════════════════════

def generate_youtube_masterpiece(raw_content, title):
    print(f"   🎬 [YouTube Engine] Starting 3-Phase Chaptering for '{title[:30]}...'")
    client = _get_gemini_client()
    
    meta_raw = gem_fb("Premium", YT_META_PROMPT.replace("{raw_content}", raw_content))
    meta = xtag(meta_raw, "METADATA")
    
    p1_raw = gem_fb("Premium", YT_SCRIPT_P1.replace("{raw_content}", raw_content))
    p1 = xtag(p1_raw, "PART1")
    
    p2_raw = gem_fb("Premium", YT_SCRIPT_P2)
    p2 = xtag(p2_raw, "PART2")
    
    p3_raw = gem_fb("Premium", YT_SCRIPT_P3)
    p3 = xtag(p3_raw, "PART3")
    
    full_script = f"{p1}\n\n{p2}\n\n{p3}"
    print(f"      🎯 Masterpiece Complete: {len(full_script):,} characters!")
    
    return meta, full_script

def send_youtube_script_email(post_title, meta, script):
    if not EMAIL_SENDER or not EMAIL_PASS: return
    print(f"   📧 Sending YouTube Script to {YOUTUBE_EMAIL_RECEIVER}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = YOUTUBE_EMAIL_RECEIVER
        msg['Subject'] = f"🎬 [YouTube Script Ready] {post_title[:40]}"

        body = f"""
        <div style="font-family: -apple-system, sans-serif; background: #f8fafc; padding: 20px;">
            <div style="max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <div style="background: #ef4444; padding: 25px; text-align: center; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 24px;">🎬 Warm Insight YouTube Vrew Script</h2>
                    <p style="margin: 10px 0 0; opacity: 0.9;">Total Characters: <strong>{len(script):,}</strong></p>
                </div>
                <div style="padding: 30px;">
                    <h3 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">📋 YouTube Metadata & Thumbnail Copy</h3>
                    <div style="background: #f1f5f9; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-size: 15px; color: #334155; line-height: 1.6;">{meta}</div>
                    
                    <h3 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-top: 35px;">🔗 Cross-Pollination (For Description/Pinned Comment)</h3>
                    <div style="background: #e0f2fe; border-left: 5px solid #0284c7; padding: 15px; border-radius: 4px; font-weight: bold; font-size: 16px; color: #0369a1; line-height: 1.5;">
                        👇 Check out the Warm Insight newsletter for a deeper dive and the full text summary: www.warminsight.com
                    </div>
                    
                    <h3 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-top: 40px;">🎙️ Vrew Script (Copy & Paste)</h3>
                    <div style="background: #fefce8; padding: 20px; border: 1px solid #fde047; border-radius: 8px; white-space: pre-wrap; font-size: 16px; color: #1c1917; line-height: 1.8;">{script}</div>
                </div>
            </div>
        </div>
        """
        msg.attach(MIMEText(body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ YouTube Script Email Sent!")
    except Exception as e:
        print(f"   ❌ YouTube Script Email Failed: {e}")

# ═══════════════════════════════════════════════
# ✉️ Medium Teaser Draft 자동 생성 및 발송 엔진
# ═══════════════════════════════════════════════
def send_medium_draft_email(title, original_link, raw_content, cat, kw, img_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS: return
    print(f"   📧 Generating and Sending Medium Draft to {MEDIUM_EMAIL_RECEIVER}...")
    
    if cat == "Foundation":
        sec1_title = "📖 What is it?"
        sec1_body = xtag(raw_content, "DEFINITION").replace('\n', '<br>')
        sec2_title = "💡 Why It Matters"
        sec2_body = xtag(raw_content, "WHY_MATTERS").replace('\n', '<br>')
        sec3_title = "🚀 How to Start Today"
        sec3_body = xtag(raw_content, "HOW_TO_START").replace('\n', '<br>')
    elif cat == "The Daily Catalyst":
        sec1_title = "❝ The Anchor ❞"
        sec1_body = xtag(raw_content, "ANCHOR").replace('\n', '<br>')
        sec2_title = "The Reflection"
        sec2_body = xtag(raw_content, "REFLECTION").replace('\n', '<br>')
        sec3_title = "⚡ The Daily Catalyst"
        sec3_body = xtag(raw_content, "CATALYST").replace('\n', '<br>')
    elif cat == "Money Hack":
        sec1_title = "💡 The Concept"
        sec1_body = xtag(raw_content, "CONCEPT").replace('\n', '<br>')
        sec2_title = "🛠️ Step-by-Step Execution"
        sec2_body = xtag(raw_content, "STEP_BY_STEP_TOOL").replace('\n', '<br>')
        sec3_title = "🔥 Pro Tip"
        sec3_body = xtag(raw_content, "PRO_TIP").replace('\n', '<br>')
    else:
        sec1_title = "Executive Summary"
        sec1_body = xtag(raw_content, "EXECUTIVE_SUMMARY").replace('\n', '<br>')
        sec2_title = "💡 Plain English"
        sec2_body = xtag(raw_content, "PLAIN_ENGLISH").replace('\n', '<br>')
        sec3_title = xtag(raw_content, "HEADLINE")
        raw_m = xtag(raw_content, "MACRO").replace("PARAGRAPH 1:", "").replace("PARAGRAPH 2:", "").replace("PARAGRAPH 3:", "")
        sec3_body = raw_m.strip().replace('\n', '<br><br>')
    
    kw_tag = kw.title() if kw else "Market Trends"
    if len(kw_tag) > 25: kw_tag = kw_tag[:25].strip() 
    cat_tag = cat.replace("-", " ")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = MEDIUM_EMAIL_RECEIVER
        msg['Subject'] = f"✍️ [Medium Draft] {title[:40]}..."

        body = f"""
        <div style="font-family: -apple-system, sans-serif; background: #f4f4f5; padding: 20px;">
            <div style="max-width: 700px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                
                <div style="background: #10b981; padding: 25px; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 22px;">✍️ Medium Teaser Post Ready</h2>
                    <p style="margin: 10px 0 0; opacity: 0.9; font-size: 14px;">Copy the content below to drive traffic back to Warm Insight.</p>
                </div>
                
                <div style="background: #ecfdf5; padding: 20px 25px; border-bottom: 1px solid #e2e8f0;">
                    <h3 style="color: #065f46; margin-top: 0; font-size: 16px;">🚨 CRITICAL SEO STEP (Canonical URL)</h3>
                    <ol style="color: #064e3b; font-size: 14px; margin: 0; padding-left: 20px; line-height: 1.6;">
                        <li>Go to Medium and paste the Title & Body below.</li>
                        <li>Click the <strong>3 dots (...)</strong> at the top right -> <strong>More Settings</strong> -> <strong>Advanced Settings</strong>.</li>
                        <li>Check <em>"This story was originally published elsewhere"</em>.</li>
                        <li>Paste this Exact URL: <strong><a href="{original_link}" style="color: #059669;">{original_link}</a></strong></li>
                    </ol>
                    
                    <h3 style="color: #065f46; margin-top: 25px; font-size: 16px;">🖼️ Don't forget the Thumbnail!</h3>
                    <p style="color: #064e3b; font-size: 14px; margin: 0;">
                        Download the attached image (<strong>thumbnail.jpg</strong>) and drag-and-drop it right under your Title in the Medium editor. Medium will automatically use it as the cover image!
                    </p>

                    <h3 style="color: #065f46; margin-top: 25px; font-size: 16px;">🏷️ Recommended Medium Tags (Topics)</h3>
                    <p style="color: #064e3b; font-size: 14px; margin: 0; background: #d1fae5; padding: 10px; border-radius: 4px; font-weight: bold;">
                        Investing, Finance, {cat_tag}, Market Analysis, {kw_tag}
                    </p>
                </div>

                <div style="padding: 30px;">
                    <h3 style="color: #64748b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Copy From Here 👇</h3>
                    
                    <div style="padding: 20px; background: #ffffff; color: #222222; font-family: Georgia, serif; border: 1px dashed #cbd5e1;">
                        <h1>{title}</h1>
                        <br>
                        <h2>{sec1_title}</h2>
                        <p>{sec1_body}</p>
                        <br>
                        <h2>{sec2_title}</h2>
                        <p>{sec2_body}</p>
                        <br>
                        <h2>{sec3_title}</h2>
                        <p>{sec3_body}</p>
                        <br>
                        <hr>
                        <br>
                        <h2>🚀 Read the Full Deep Dive</h2>
                        <p>This is just the tip of the iceberg. To see the full deep dive, dashboard, and strategies, read the complete analysis on Warm Insight.</p>
                        <p><a href="{original_link}">👉 Click here to read the full report</a></p>
                    </div>
                </div>

            </div>
        </div>
        """
        msg.attach(MIMEText(body, 'html'))
        
        if img_bytes:
            image_part = MIMEImage(img_bytes, name="thumbnail.jpg")
            image_part.add_header('Content-Disposition', 'attachment', filename="thumbnail.jpg")
            msg.attach(image_part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ Medium Teaser Draft Email Sent (with Medium Exclusive Thumbnail)!")
    except Exception as e:
        print(f"   ❌ Medium Teaser Draft Email Failed: {e}")

# ═══════════════════════════════════════════════
# ✉️ 커뮤니티 바이럴 포스팅 (Reddit/Quora) 자동 발송 엔진
# ═══════════════════════════════════════════════
def send_community_viral_email(title, original_link, raw_content, cat):
    if not EMAIL_SENDER or not EMAIL_PASS or not EMAIL_RECEIVER: return
    print(f"   📧 Generating and Sending Community Viral Draft to {EMAIL_RECEIVER}...")

    if cat == "Foundation":
        content_body = f"📖 What is it?\n{xtag(raw_content, 'DEFINITION')}\n\n💡 Why It Matters\n{xtag(raw_content, 'WHY_MATTERS')}\n\n🚀 How to Start Today\n{xtag(raw_content, 'HOW_TO_START')}"
        tldr = xtag(raw_content, "EXCERPT")
    elif cat == "The Daily Catalyst":
        content_body = f"❝ The Anchor ❞\n{xtag(raw_content, 'ANCHOR')}\n\nThe Reflection\n{xtag(raw_content, 'REFLECTION')}\n\n⚡ The Daily Catalyst\n{xtag(raw_content, 'CATALYST')}"
        tldr = xtag(raw_content, "EXCERPT")
    elif cat == "Money Hack":
        content_body = f"💡 The Concept\n{xtag(raw_content, 'CONCEPT')}\n\n🛠️ Step-by-Step Execution\n{xtag(raw_content, 'STEP_BY_STEP_TOOL')}\n\n🔥 Pro Tip\n{xtag(raw_content, 'PRO_TIP')}"
        tldr = xtag(raw_content, "EXCERPT")
    else:
        raw_m = xtag(raw_content, "MACRO").replace("PARAGRAPH 1:", "").replace("PARAGRAPH 2:", "").replace("PARAGRAPH 3:", "")
        content_body = f"Executive Summary\n{xtag(raw_content, 'EXECUTIVE_SUMMARY')}\n\n💡 Plain English\n{xtag(raw_content, 'PLAIN_ENGLISH')}\n\n{xtag(raw_content, 'HEADLINE')}\n{raw_m.strip()}"
        tldr = xtag(raw_content, "TAKEAWAY") or xtag(raw_content, "EXECUTIVE_SUMMARY")

    content_body_html = content_body.replace('\n', '<br>')
    
    clean_title = _clean_seo_title(title)

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"📢 [Reddit/Quora Draft] Viral Post Ready: {clean_title[:30]}..."

        body = f"""
        <div style="font-family: -apple-system, sans-serif; background: #f4f4f5; padding: 20px;">
            <div style="max-width: 700px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <div style="background: #ef4444; padding: 25px; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 22px;">📢 Reddit/Quora Viral Post Ready</h2>
                    <p style="margin: 10px 0 0; opacity: 0.9; font-size: 14px;">Copy & Paste to r/povertyfinance, r/sidehustle, or Quora!</p>
                </div>
                <div style="padding: 30px;">
                    <h3 style="color: #64748b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Title 👇</h3>
                    <div style="padding: 15px; background: #f8fafc; color: #1e293b; font-weight: bold; font-size: 16px; border-left: 4px solid #ef4444; margin-bottom: 25px;">
                        I wrote a 5-minute guide for absolute beginners on {cat}: {clean_title} — Hope this helps someone today!
                    </div>
                    <h3 style="color: #64748b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Body 👇</h3>
                    <div style="padding: 20px; background: #ffffff; color: #334155; font-family: Georgia, serif; border: 1px dashed #cbd5e1; line-height: 1.6;">
                        Hey guys, I know finance jargon can be super overwhelming when you're just starting out. Here is a super plain-English breakdown I put together:<br><br>
                        {content_body_html}<br><br>
                        ---<br>
                        <strong>TL;DR:</strong> {tldr}<br><br>
                        <em>(P.S. I break down daily market news and finance basics like this over at my blog <a href="{original_link}" style="color: #2563eb; text-decoration: underline;">Warm Insight</a> if anyone wants to read more!)</em>
                    </div>
                </div>
            </div>
        </div>
        """
        msg.attach(MIMEText(body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ Community Viral Draft Email Sent!")
    except Exception as e:
        print(f"   ❌ Community Viral Draft Email Failed: {e}")

# =====================================================================
# ★ BLOCK 1: 첫 번째 반복 블록 (원본 보존용) ★
# =====================================================================

def send_social_style_email(title, link, image_bytes_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS or not EMAIL_RECEIVER:
        print("   ⚠️ Missing email credentials. Skipping email dispatch.")
        return

    print(f"   📧 Sending Social Slim Package to {EMAIL_RECEIVER}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"🚨 {cat.upper()} REELS READY: {hook_text[:40]}..."

        vid_tag = ""
        if video_mp4_bytes:
            vid_tag = f"""
            <div style="margin-bottom: 25px; text-align:center; padding: 25px; background: #0f172a; border-radius: 16px; border: 2px solid #10b981;">
                <p style="color: #10b981; font-weight: 900; font-size: 18px; margin-top: 0; text-transform: uppercase;">🎬 15-Sec Viral Reels Attached!</p>
                <div style="font-size: 45px; margin: 15px 0;">✨ 📹 ✨</div>
                <p style="color: #ffffff; font-size: 15px; font-weight: bold; margin: 5px 0;">100% Compatible with IG Reels / TikTok / YT Shorts.</p>
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0; margin-top: 10px;">Download <strong>WarmInsight_{cat}_Video.mp4</strong> attached below.</p>
            </div>
            """

        body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f4f4f5; padding: 20px; color: #0f1419;">
            {vid_tag}
            <div style="background: #ffffff; border-left: 5px solid #eab308; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #ca8a04; font-size: 18px;">🎬 1-Min Reels Script</h3>
                <p style="font-size: 14px; color: #52525b; margin-bottom: 15px;">Read this directly or plug into AI Voice.</p>
                <div style="background: #fefce8; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; font-style: italic;">
                    {reels_script.replace(chr(10), '<br>')}
                </div>
            </div>
            <div style="background: #ffffff; border-left: 5px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #2563eb; font-size: 18px;">💬 Smart Community Comment</h3>
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; font-size: 15px; font-weight: bold; color: #1e3a8a;">
                    "{smart_comment}"
                </div>
            </div>
            <div style="background: #ffffff; border-left: 5px solid #10b981; padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #059669; font-size: 18px;">📱 Instagram Feed Caption</h3>
                <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; white-space: pre-wrap;">{ig_caption}</div>
            </div>
            <hr style="border:0; height:2px; background:#d4d4d8; margin: 30px 0;">
            <div style="text-align:center; margin-bottom: 20px;">
                <a href="{link}" style="display: inline-block; background-color: #0f1419; color: #ffffff; padding: 12px 24px; border-radius: 9999px; text-decoration: none; font-weight: bold; font-size: 15px;">
                    Read Full Post on Website →
                </a>
            </div>
        </div>
        """
        msg.attach(MIMEText(body, 'html'))

        if video_mp4_bytes:
            try:
                part = MIMEBase('video', 'mp4')
                part.set_payload(video_mp4_bytes)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=f'WarmInsight_{cat}_Video.mp4')
                msg.attach(part)
            except Exception as e:
                print(f"   ⚠️ MP4 Attachment Error: {e}")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ Social Email Sent Successfully!")
    except Exception as e:
        print(f"   ❌ Social Email Failed: {e}")

_gemini_client = None
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None: _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client

def check_env_vars():
    missing = [v for v, k in zip(["GEMINI_API_KEY", "WP_USERNAME", "WP_APP_PASSWORD"], [GEMINI_API_KEY, WP_USER, WP_APP_PASS]) if not k]
    if missing:
        print(f"❌ Missing Secrets: {missing}")
        return False
    return True

def verify_wp_credentials():
    print(f"   🔍 [System] Checking WP Connection to: {WP_URL}")
    try:
        resp = scraper.get(f"{WP_URL}/wp-json/wp/v2/users/me", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=25)
        try:
            resp_json = resp.json()
            is_valid_json = isinstance(resp_json, dict) and "id" in resp_json
        except:
            is_valid_json = False

        if resp.status_code == 200 and is_valid_json: 
            print("   ✅ WP Auth Successful!")
            return True
        else:
            print(f"   ❌ WP Auth Failed or Blocked by WAF! (HTTP Status: {resp.status_code})")
    except Exception as e: 
        print(f"   ❌ WP Connection Error (Timeout/Firewall): {e}")
    return False

def call_gemini(client, model, prompt, sys_inst=None, retries=5):
    if not sys_inst:
        sys_inst = "You are an elite financial analyst. ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN. You MUST strictly follow the required output format. You MUST wrap EVERY section of your response in the exact XML tags requested."

    config = types.GenerateContentConfig(
        system_instruction=sys_inst,
        temperature=0.7,
        max_output_tokens=8192
    )
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt, config=config)
            if r.text: return str(r.text)
        except Exception as e:
            err = str(e)
            if "credits are depleted" in err or "billing" in err.lower():
                print("   🚨 Credits depleted!")
                return None
            if "404" in err or "not found" in err.lower(): return None
            if "503" in err or "UNAVAILABLE" in err:
                wait = (15 * i) + random.uniform(-2, 5)
                time.sleep(wait)
            elif "429" in err:
                time.sleep(30 + random.uniform(0, 10))
            elif i < retries: time.sleep(5 * i)
    return None

def gem_fb(tier, prompt, sys_inst=None):
    client = _get_gemini_client()
    for m in MODEL_PRI.get(tier, FAST_MODELS):
        r = call_gemini(client, m, prompt, sys_inst)
        if r: return r
    return ""

def xtag(raw, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL | re.IGNORECASE)
    if m:
        res = m.group(1).strip()
        res = re.sub(r"^`{3}(html|xml|text|markdown)?\n", "", res, flags=re.IGNORECASE)
        res = re.sub(r"\n`{3}$", "", res)
        return res.strip()
    return ""

def sanitize(html):
    html = re.sub(r"<script(?!\s+type=['\"]application/ld\+json['\"])[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    return re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.DOTALL)

def make_slug(kw, title, cat):
    base = kw if (kw and len(kw) > 4) else title
    slug = re.sub(r"[^\w\s-]", "", base.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:55]
    return f"{slug}-{datetime.datetime.utcnow().strftime('%m%d%H%M')}"

def _clean_seo_title(title):
    for p in ["[👑 VIP] ", "[💎 Pro] ", "[PRO] ", "[VIP] ", "[PRO]", "[VIP]", "[Pro] ", "[VIP] ", "[Pro] "]:
        title = title.replace(p, "")
    return title.strip()

def get_or_create_wp_category(cat_name):
    slug = cat_name.lower().replace(" ", "-")
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = scraper.post(f"{WP_URL}/wp-json/wp/v2/categories", headers=WP_API_HEADERS, json={"name": cat_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_or_create_wp_tag(tag_name):
    slug = tag_name.lower().replace(" ", "-")
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/tags?slug={slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = scraper.post(f"{WP_URL}/wp-json/wp/v2/tags", headers=WP_API_HEADERS, json={"name": tag_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_wp_author_id(author_full_string):
    search_name = author_full_string.split("&")[0].strip()
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/users", headers=WP_API_HEADERS, params={"search": search_name}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200:
            users = r.json()
            if len(users) > 0: return users[0]["id"]
    except: pass
    return None

def _get_latest_post_category_name():
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/posts?per_page=1&status=publish", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200:
            try: r_json = r.json()
            except: return None
            if isinstance(r_json, list) and len(r_json) > 0:
                cat_ids = r_json[0].get('categories', [])
                if not cat_ids: return None
                r_cats = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=100", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
                if r_cats.status_code == 200:
                    try: r_cats_json = r_cats.json()
                    except: return None
                    if isinstance(r_cats_json, list):
                        cat_map = {c['id']: c['name'] for c in r_cats_json}
                        for cid in cat_ids:
                            name = cat_map.get(cid)
                            if name in CATEGORIES: return name
    except: pass
    return None

def already_published_today(cat):
    try:
        cat_slug = cat.lower().replace(" ", "-")
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={cat_slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code != 200: return False
        try:
            r_json = r.json()
            if not isinstance(r_json, list) or not r_json: return False
            cat_id = r_json[0]["id"]
        except: return False

        r2 = scraper.get(f"{WP_URL}/wp-json/wp/v2/posts", headers=WP_API_HEADERS, params={"categories": cat_id, "per_page": 1, "status": "publish"}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code == 200:
            try:
                r2_json = r2.json()
                if isinstance(r2_json, list) and len(r2_json) > 0:
                    latest_post = r2_json[0]
                    post_date_gmt = latest_post.get("date_gmt", "")[:10] 
                    today_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d")
                    if post_date_gmt == today_utc: return True
            except: pass
    except: pass
    return False

def fetch_news_pool(cat, max_items=15):
    feeds = RSS_FEEDS.get(cat, RSS_FEEDS["Economy"])
    items = set()
    for url in feeds:
        try:
            resp = scraper.get(url, headers=EXTERNAL_HEADERS, timeout=15)
            if resp.status_code == 200:
                d = feedparser.parse(resp.text)
                for e in d.entries[:40]:
                    title = getattr(e, 'title', '').strip()
                    summary = re.sub(r'<[^>]+>', '', getattr(e, 'summary', ''))[:200].strip()
                    if title and len(title) > 10: items.add(f"• {title}: {summary}")
            else:
                print(f"   ⚠️ RSS feed blocked by WAF or returned {resp.status_code}: {url}")
        except Exception as ex:
            print(f"   ⚠️ RSS feed error on {url}: {ex}")
            pass
            
    items_list = list(items)
    random.shuffle(items_list)
    return items_list[:max_items]

def generate_video_mp4(cat, hook_text, data_points, frames_images):
    print("   🎥 Generating 15-Sec Pixar Style Character Reels Video...")
    try:
        import numpy as np
        from moviepy.editor import ImageClip, concatenate_videoclips
    except ImportError as e:
        print(f"   ❌ MoviePy import failed: {e}")
        return None
    try:
        SLIDE_DURATION = 2.6
        CROSSFADE_DURATION = 0.2
        ZOOM_START = 1.0
        ZOOM_END = 1.08

        clips = []
        for i, frame in enumerate(frames_images):
            frame_np = np.array(frame.convert('RGB'))
            clip = ImageClip(frame_np).set_duration(SLIDE_DURATION)
            if i % 2 == 0: clip = clip.resize(lambda t: ZOOM_START + (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            else: clip = clip.resize(lambda t: ZOOM_END - (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            clip = clip.set_position(('center', 'center'))
            if i > 0: clip = clip.crossfadein(CROSSFADE_DURATION)
            clips.append(clip)

        video = concatenate_videoclips(clips, padding=-CROSSFADE_DURATION, method="compose")
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        video.write_videofile(
            temp_path, fps=30, codec='libx264', bitrate='2500k', audio=False, preset='fast',
            ffmpeg_params=[
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1:1',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-profile:v', 'main', '-level', '4.0',
                '-x264-params', 'colorprim=bt709:transfer=bt709:colormatrix=bt709'
            ],
            logger=None
        )
        with open(temp_path, 'rb') as f: mp4_bytes = f.read()
        os.remove(temp_path)
        print(f"   ✅ Friendly Character 15s Video Extracted! ({len(mp4_bytes)/1024/1024:.1f}MB)")
        return mp4_bytes
    except Exception as e:
        print(f"   ❌ Video Encoding Failed: {e}")
        return None

def generate_vip_carousel(raw_content, cat):
    print("    🎨 Generating DYNAMIC 3-IMAGE Friendly Character Carousel (Red & Gold Mix)...")
    client = _get_gemini_client()

    sys_inst = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
    You are a TOP-TIER viral content creator for finance Instagram/TikTok. Write entirely in ENGLISH.
    Your job: Extract data + write COPY THAT STOPS THE SCROLL.

    OUTPUT RULES (CRITICAL):
    - HOOK: Pattern interrupt opener. Use shocking number, contrarian take, or curiosity gap. Max 7 words.
    - SHOCK_STAT: One jaw-dropping statistic that proves the hook. Max 6 words. Include numbers.
    - INSIGHT_LINE: The "aha moment" payoff. Max 8 words. Confident, declarative.
    - CTA_HOOK: Urgency/FOMO trigger for the last slide. Max 6 words.

    Format EXACTLY:
    <MAIN_TITLE>Main viral headline, max 5 words, ALL CAPS, energetic</MAIN_TITLE>
    <BADGE>e.g. IMPACT: HIGH</BADGE>
    <HOOK>Scroll-stopping opener (max 7 words)</HOOK>
    <SHOCK_STAT>Jaw-dropping stat (max 6 words, with numbers)</SHOCK_STAT>
    <QUESTION>Engagement question for comments</QUESTION>
    <INSIGHT_LINE>The aha moment (max 8 words)</INSIGHT_LINE>
    <CTA_HOOK>FOMO trigger (max 6 words)</CTA_HOOK>
    <REELS_SCRIPT>60-second spoken script with hook-stat-story-CTA structure</REELS_SCRIPT>
    <IG_CAPTION>Caption with hook, value, CTA, 15+ hashtags</IG_CAPTION>
    <SMART_COMMENT>Bloomberg/WSJ-style comment for free traffic</SMART_COMMENT>
    <ITEM1>TICKER | Value with % or $</ITEM1>
    <ITEM2>TICKER | Value with % or $</ITEM2>
    <ITEM3>TICKER | Value with % or $</ITEM3>
    <ITEM4>TICKER | Value with % or $</ITEM4>
    <ITEM5>TICKER | Value with % or $</ITEM5>
    """
    raw_data = gem_fb("vip", raw_content, sys_inst)

    main_title = xtag(raw_data, "MAIN_TITLE") or f"{cat.upper()} ALERT"
    badge_text = xtag(raw_data, "BADGE") or "IMPACT: HIGH"
    hook_text = xtag(raw_data, "HOOK") or "Wall Street Just Did THIS 🚨"
    shock_stat = xtag(raw_data, "SHOCK_STAT") or "$2.3T MOVED OVERNIGHT"
    question_text = xtag(raw_data, "QUESTION") or "Where's YOUR money going? 👇"
    insight_line = xtag(raw_data, "INSIGHT_LINE") or "SMART MONEY IS MOVING NOW"
    cta_hook = xtag(raw_data, "CTA_HOOK") or "DONT MISS THE NEXT MOVE"
    reels_script = xtag(raw_data, "REELS_SCRIPT") or "Script generation failed."
    ig_caption = xtag(raw_data, "IG_CAPTION") or f"{hook_text}\n\nLink in bio for the full breakdown. #investing #finance #stocks"
    smart_comment = xtag(raw_data, "SMART_COMMENT") or "Interesting market shift. Just published a full breakdown on this."

    data_points = []
    for i in range(1, 6):
        item = xtag(raw_data, f"ITEM{i}")
        if item and "|" in item:
            parts = item.split("|")
            raw_ticker = parts[0].strip()
            if len(raw_ticker) > 10: raw_ticker = raw_ticker[:8] + ".."
            data_points.append({"ticker": raw_ticker, "val": parts[1].strip()})

    if len(data_points) < 5:
        data_points = [
            {"ticker": "$NVDA", "val": "+6.2%"}, {"ticker": "$AAPL", "val": "+5.3%"},
            {"ticker": "$MSFT", "val": "+4.9%"}, {"ticker": "$BTC", "val": "+4.2%"},
            {"ticker": "$ETH", "val": "+2.3%"}
        ]

    W, H = 1080, 1920
    BG = "#000000"
    WHITE = "#ffffff"
    GOLD = "#fde047"    # 가독성 및 프리미엄 상징
    RED = "#ef4444"     # 긴급성 및 강조 상징
    GRAY = "#94a3b8"

    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    def lf(p, s):
        try: return ImageFont.truetype(p, s)
        except: return ImageFont.load_default()

    font_title = lf(ft_path, 115)    
    font_huge = lf(ft_path, 220)    
    font_mega = lf(ft_path, 150)    
    font_sub = lf(ft_path, 65)
    font_data = lf(ft_path, 60)
    font_alert = lf(ft_path, 90)

    vp_base = "A cute, friendly, extremely simple 3D white robot mascot with a smooth round head and simple smiling eyes. Pixar animation style. Clean dark minimalist studio background. Soft cinematic lighting. No text, no letters."
    vp1 = vp_base + f" The cute robot is looking surprised, putting its hands on its cheeks in shock. {cat} theme."
    vp2 = vp_base + f" The cute robot is holding a glowing magnifying glass, looking closely at a floating digital chart."
    vp3 = vp_base + f" The cute robot is confidently pointing forward and giving a thumbs up, with a bright glowing aura."

    def fetch_friendly_image(prompt_text, seed):
        try:
            res = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt_text,
                config=types.GenerateImagesConfig(
                    number_of_images=1, aspect_ratio="1:1", output_mime_type="image/jpeg"
                )
            )
            img_bytes = res.generated_images[0].image.image_bytes
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        except Exception as e:
            print(f"    ⚠️ Gemini failed, trying Pollinations: {e}")
            try:
                prompt_encoded = urllib.parse.quote(prompt_text)
                url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1080&height=1080&nologo=true&seed={seed}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    img = Image.open(io.BytesIO(response.read())).convert("RGBA")
            except Exception as e2:
                print(f"    ⚠️ Pollinations failed: {e2}")
                return None
        
        img = img.resize((1080, 1080), Image.LANCZOS)
        mask = Image.new("L", (1080, 1080), 255)
        mask_draw = ImageDraw.Draw(mask)
        for y in range(700, 1080):
            alpha = int(255 - (y - 700) * (255 / 380))
            mask_draw.line([(0, y), (1080, y)], fill=alpha)
        img.putalpha(mask)
        return img

    print("    [AI] Requesting 3 UNIQUE Friendly Character images (Sequential)...")
    img_hook_ai = fetch_friendly_image(vp1, random.randint(1, 100000))
    time.sleep(2)
    img_stat_ai = fetch_friendly_image(vp2, random.randint(1, 100000))
    time.sleep(2)
    img_out_ai  = fetch_friendly_image(vp3, random.randint(1, 100000))

    def paste_bg(d_img, target_ai_img):
        if target_ai_img:
            d_img.paste(target_ai_img, (0, 0), target_ai_img)
        else:
            fallback_img = Image.new("RGBA", (1080, 1080), "#09090b")
            d = ImageDraw.Draw(fallback_img)
            d.ellipse([440, 250, 640, 450], fill="#f8fafc") 
            d.rounded_rectangle([460, 470, 620, 750], radius=40, fill="#f8fafc") 
            mask = Image.new("L", (1080, 1080), 255)
            mask_draw = ImageDraw.Draw(mask)
            for y in range(700, 1080):
                alpha = int(255 - (y - 700) * (255 / 380))
                mask_draw.line([(0, y), (1080, y)], fill=alpha)
            fallback_img.putalpha(mask)
            d_img.paste(fallback_img, (0, 0), fallback_img)

    def wrap_lines(text, font, max_width):
        words = text.split()
        lines, line = [], []
        d = ImageDraw.Draw(Image.new("RGB", (1,1)))
        for ww in words:
            test_str = " ".join(line + [ww])
            try: tw = d.textlength(test_str, font=font)
            except: tw = len(test_str) * 40  
            if tw < max_width: line.append(ww)
            else:
                if line: lines.append(" ".join(line))
                line = [ww]
        if line: lines.append(" ".join(line))
        return lines

    # --- Slide 1 (Hook) ---
    img1 = Image.new("RGB", (W, H), BG)
    paste_bg(img1, img_hook_ai)
    d1 = ImageDraw.Draw(img1)
    
    # 🚨 상단 경고 배지: 긴급성을 위한 RED
    d1.rounded_rectangle([300, 1100, 780, 1200], radius=20, fill=RED) 
    d1.text((W//2, 1150), f"🚨 {cat.upper()} ALERT", fill=WHITE, font=font_alert, anchor="mm")
    
    # 💡 훅 텍스트: 마지막 줄만 시선 집중을 위해 GOLD 강조
    hook_lines = wrap_lines(hook_text.upper(), font_title, 850) 
    y_text = 1330
    for i, ln in enumerate(hook_lines[:4]):
        color = GOLD if i == len(hook_lines[:4])-1 else WHITE
        d1.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 120 
    d1.text((W//2, 1800), "↓ SWIPE TO SEE WHY ↓", fill=GRAY, font=font_sub, anchor="mm")

    # --- Slide 2 (Shock Stat) ---
    img2 = Image.new("RGB", (W, H), BG)
    paste_bg(img2, img_stat_ai)
    d2 = ImageDraw.Draw(img2)
    
    # 💡 소제목: 고급스러운 GOLD
    d2.text((W//2, 1150), "THE NUMBER", fill=GOLD, font=font_sub, anchor="mm")
    
    # 🚨 충격 수치: 마지막 줄만 충격 효과를 위해 RED 강조
    shock_lines = wrap_lines(shock_stat.upper(), font_mega, 850)
    y_text = 1350
    for i, ln in enumerate(shock_lines[:3]):
        color = RED if i == len(shock_lines[:3])-1 else WHITE
        d2.text((W//2, y_text), ln, fill=color, font=font_mega, anchor="mm")
        y_text += 160 
    d2.text((W//2, 1800), "WAIT FOR IT...", fill=GRAY, font=font_sub, anchor="mm")

    # --- Slides 3~5 (Data Points) ---
    data_imgs = []
    for idx in range(3):
        if idx >= len(data_points): break
        item = data_points[idx]
        img_d = Image.new("RGB", (W, H), BG)
        paste_bg(img_d, img_stat_ai)
        d = ImageDraw.Draw(img_d)
        
        # 🚨 카테고리 알림: RED
        d.text((W//2, 1100), cat.upper(), fill=RED, font=font_sub, anchor="mm")
        d.text((W//2, 1200), f"WATCH THIS → {idx+1}/3", fill=GRAY, font=font_data, anchor="mm")
        d.text((W//2, 1380), item['ticker'], fill=WHITE, font=font_title, anchor="mm")
        
        # 💡 지표 컬러: 하락(-)이면 RED, 상승/중립이면 GOLD
        val_str = item['val']
        val_color = RED if '-' in val_str else GOLD
        
        current_huge_size = 220
        if len(val_str) > 6: current_huge_size = int(220 * (6 / len(val_str)))
        current_font_huge = lf(ft_path, max(100, current_huge_size))
        
        d.text((W//2, 1550), val_str, fill=val_color, font=current_font_huge, anchor="mm")
        
        # 💡 페이지 도트: 활성화된 페이지는 GOLD
        dot_y = 1800
        for di in range(3):
            dx = W//2 + (di - 1) * 60
            color = GOLD if di == idx else "#3f3f46"
            d.ellipse([dx-15, dot_y-15, dx+15, dot_y+15], fill=color)
        data_imgs.append(img_d)

    # --- Slide 6 (Takeaway) ---
    img6 = Image.new("RGB", (W, H), BG)
    paste_bg(img6, img_out_ai)
    d6 = ImageDraw.Draw(img6)
    
    # 💡 결론 소제목: GOLD
    d6.text((W//2, 1100), "THE TAKEAWAY", fill=GOLD, font=font_sub, anchor="mm")
    
    # 💡 핵심 문장: 마지막 줄 GOLD 강조
    insight_lines = wrap_lines(insight_line.upper(), font_title, 850)
    y_text = 1250
    for i, ln in enumerate(insight_lines[:3]):
        color = GOLD if i == len(insight_lines[:3])-1 else WHITE
        d6.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 120
        
    # 🚨 마지막 행동 촉구(CTA): 가장 강력한 RED
    d6.text((W//2, 1650), cta_hook.upper(), fill=RED, font=font_alert, anchor="mm")
    d6.text((W//2, 1780), "LINK IN BIO → @WARMINSIGHT", fill=GRAY, font=font_sub, anchor="mm")

    image_bytes_list = []
    all_frames = [img1, img2] + data_imgs + [img6]
    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, all_frames)

    return image_bytes_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes

def _upload_image(img_bytes, filename):
    try:
        resp = scraper.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"}, 
            data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30
        )
        if resp.status_code in (200, 201): return resp.json().get("id")
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, author_name, raw_for_cards=None, med_img_bytes=None):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat)

    insight_cat_id = None
    if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
        insight_cat_id = get_or_create_wp_category("Insight")

    if tier == "unified": tag_id = get_or_create_wp_tag("Insight")
    elif tier == "vip": tag_id = get_or_create_wp_tag("VIP")
    else: tag_id = get_or_create_wp_tag("Pro")

    author_id = get_wp_author_id(author_name)
    display_title = title if cat in ["Foundation", "The Daily Catalyst", "Money Hack"] or tier == "unified" else (f"[VIP] {title}" if tier == "vip" else f"[Pro] {title}")

    post_data = {
        "title": display_title,
        "content": html,
        "status": "publish",
        "slug": slug,
    }

    if author_id: post_data["author"] = author_id
    if media_id: post_data["featured_media"] = media_id

    cats = []
    if cat_id: cats.append(cat_id)
    if insight_cat_id: cats.append(insight_cat_id)

    if cats: post_data["categories"] = cats
    if tag_id: post_data["tags"] = [tag_id]

    seo_title = _clean_seo_title(title)
    rm_title = seo_title if len(seo_title) > 50 else f"{seo_title} | Warm Insight"

    post_data["meta"] = {
        "rank_math_title": rm_title[:60],
        "rank_math_description": (exc or "")[:160],
        "rank_math_focus_keyword": kw.lower() if kw else "",
        "is_premium": "no" if cat in ["Foundation", "Money Hack"] else "yes",
        "pms_content_restrict": "0" if cat in ["Foundation", "Money Hack"] else "1",
        "post_tier": tier.upper(),
    }

    try:
        r = scraper.post(
            f"{WP_URL}/wp-json/wp/v2/posts",
            json=post_data, auth=(WP_USER, WP_APP_PASS), timeout=30
        )
        if r.status_code in (200, 201):
            try:
                resp_json = r.json()
                link = resp_json.get('link') if isinstance(resp_json, dict) else None
            except: link = None
            
            if link:
                print(f"   ✅ Published: {link}")
                
                if raw_for_cards:
                    if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
                        if tier == "vip" or tier == "unified":
                            img_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes = generate_vip_carousel(raw_for_cards, cat)
                            if video_mp4_bytes:
                                send_social_style_email(display_title, link, img_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes)
                        
                        yt_meta, yt_script = generate_youtube_masterpiece(raw_for_cards, title)
                        if yt_script: send_youtube_script_email(title, yt_meta, yt_script)

                send_medium_draft_email(display_title, link, raw_for_cards, cat, kw, med_img_bytes)
                send_community_viral_email(display_title, link, raw_for_cards, cat)
                
                return True
            else:
                print(f"   ❌ [WAF Block Detected] Server returned 200 but no link was created.")
                return False
        else:
            print(f"   ❌ Publish failed. HTTP Status: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Network error: {e}")
    return False

def run_foundation_pipeline():
    cat = "Foundation"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 SEO Foundation Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    theme = random.choice(FOUNDATION_TOPICS)
    tier = "premium"
    raw = gem_fb(tier, FOUNDATION_PROMPT.replace("{theme}", theme), FOUNDATION_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Education Team")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_foundation_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return
            
        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_philosophy_pipeline():
    cat = "The Daily Catalyst"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 Catalyst Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    theme = random.choice(PHILOSOPHY_TOPICS)
    tier = "premium"
    raw = gem_fb(tier, PHILOSOPHY_PROMPT.replace("{theme}", theme), PHILOSOPHY_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Philosophical Desk")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_philosophy_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return

        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_moneyhack_pipeline():
    cat = "Money Hack"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 Money Hack Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    niche = random.choice(MH_NICHES)
    platform = random.choice(MH_PLATFORMS)
    ai_tool = random.choice(MH_AI_TOOLS)
    theme = f"Niche: {niche} | Core Platform: {platform} | AI Automation Tool: {ai_tool}"
    print(f"   🎲 Random Framework Selected: {theme}")

    tier = "premium"
    raw = gem_fb(tier, MONEY_HACK_PROMPT.replace("{theme}", theme), MONEY_HACK_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Growth Team")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_money_hack_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return

        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_news_pipeline(forced_cat=None):
    current_time = datetime.datetime.utcnow()
    day_of_week = current_time.weekday()
    day_of_year = current_time.timetuple().tm_yday
    
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"

    if forced_cat:
        cat = forced_cat
        print(f"🎯 [Command Override] Forcing category to: {cat}")
    elif day_of_week in (1, 3):
        cat = "On-Chain"
        print(f"📅 [Smart Schedule] Today is Tue/Thu. Locking category to: {cat}")
    else:
        base_cats = [c for c in CATEGORIES if c not in ["On-Chain", "Money Hack"]]
        cat = base_cats[day_of_year % len(base_cats)]

    if force:
        print(f"🚀 Starting v46.9.60 Unified News Pipeline | TEST MODE (Force Publish)")
    else:
        print(f"🚀 Starting v46.9.60 Unified News Pipeline | Category: {cat}")

    if not check_env_vars() or not verify_wp_credentials(): return

    if force:
        if forced_cat:
            pass
        else:
            latest_cat = _get_latest_post_category_name()
            available_cats = [c for c in CATEGORIES if c not in [latest_cat, "Money Hack"]]
            if not available_cats: available_cats = [c for c in CATEGORIES if c != "Money Hack"]
            
            random.shuffle(available_cats)
            cat = available_cats[0]
            for fallback_cat in available_cats:
                if not already_published_today(fallback_cat):
                    cat = fallback_cat
                    break
            print(f"   ⚡ [TEST MODE] Forcing random category '{cat}' avoiding '{latest_cat}'.")
    else:
        if already_published_today(cat):
            print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
            return

    all_news = fetch_news_pool(cat)
    total_news = len(all_news)
    if total_news < 2:
        print(f"   ❌ Not enough news for {cat} ({total_news}). Aborting.")
        return

    news_str = "\n".join(all_news)
    tier = "unified"

    raw1 = gem_fb(tier, PROMPT_UNIFIED_P1.replace("{cat}", cat).replace("{news}", news_str))
    if not raw1:
        print("   ❌ Part 1 generation failed.")
        return

    ctx = "Title: " + xtag(raw1, "TITLE") + "\nSummary: " + xtag(raw1, "EXECUTIVE_SUMMARY")
    raw2 = gem_fb(tier, PROMPT_UNIFIED_P2.replace("{cat}", cat).replace("{ctx}", ctx))
    if not raw2:
        print("   ⚠️ Part 2 failed. Using Part 1 only.")
        raw = raw1
    else:
        raw = raw1 + "\n" + raw2

    title = xtag(raw, "TITLE")
    kw = xtag(raw, "SEO_KEYWORD")
    exc = xtag(raw, "EXCERPT") or xtag(raw, "EXECUTIVE_SUMMARY")
    slug = make_slug(kw, title, cat)
    author = VIP_AUTHORS.get(cat, "Warm Insight Editorial Team")
    tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
    
    html = build_html(tier, cat, raw, author, tf, title)

    img_bytes = make_thumbnail(title, cat, tier)
    if not img_bytes or len(img_bytes) < 1000:
        print(f"   ❌ Thumbnail error. Aborting.")
        return
        
    med_img_bytes = make_medium_thumbnail(cat)

    publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)
    time.sleep(TIER_SLEEP[tier])

# =====================================================================
# ★ BLOCK 2: 두 번째 반복 블록 (원본 보존용) ★
# =====================================================================

# ═══════════════════════════════════════════════
# ✉️ 슬림 이메일 (인스타/숏폼용)
# ═══════════════════════════════════════════════
def send_social_style_email(title, link, image_bytes_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS or not EMAIL_RECEIVER:
        print("   ⚠️ Missing email credentials. Skipping email dispatch.")
        return

    print(f"   📧 Sending Social Slim Package to {EMAIL_RECEIVER}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"🚨 {cat.upper()} REELS READY: {hook_text[:40]}..."

        vid_tag = ""
        if video_mp4_bytes:
            vid_tag = f"""
            <div style="margin-bottom: 25px; text-align:center; padding: 25px; background: #0f172a; border-radius: 16px; border: 2px solid #10b981;">
                <p style="color: #10b981; font-weight: 900; font-size: 18px; margin-top: 0; text-transform: uppercase;">🎬 15-Sec Viral Reels Attached!</p>
                <div style="font-size: 45px; margin: 15px 0;">✨ 📹 ✨</div>
                <p style="color: #ffffff; font-size: 15px; font-weight: bold; margin: 5px 0;">100% Compatible with IG Reels / TikTok / YT Shorts.</p>
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0; margin-top: 10px;">Download <strong>WarmInsight_{cat}_Video.mp4</strong> attached below.</p>
            </div>
            """

        body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f4f4f5; padding: 20px; color: #0f1419;">
            {vid_tag}
            <div style="background: #ffffff; border-left: 5px solid #eab308; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #ca8a04; font-size: 18px;">🎬 1-Min Reels Script</h3>
                <p style="font-size: 14px; color: #52525b; margin-bottom: 15px;">Read this directly or plug into AI Voice.</p>
                <div style="background: #fefce8; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; font-style: italic;">
                    {reels_script.replace(chr(10), '<br>')}
                </div>
            </div>
            <div style="background: #ffffff; border-left: 5px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #2563eb; font-size: 18px;">💬 Smart Community Comment</h3>
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; font-size: 15px; font-weight: bold; color: #1e3a8a;">
                    "{smart_comment}"
                </div>
            </div>
            <div style="background: #ffffff; border-left: 5px solid #10b981; padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #059669; font-size: 18px;">📱 Instagram Feed Caption</h3>
                <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; white-space: pre-wrap;">{ig_caption}</div>
            </div>
            <hr style="border:0; height:2px; background:#d4d4d8; margin: 30px 0;">
            <div style="text-align:center; margin-bottom: 20px;">
                <a href="{link}" style="display: inline-block; background-color: #0f1419; color: #ffffff; padding: 12px 24px; border-radius: 9999px; text-decoration: none; font-weight: bold; font-size: 15px;">
                    Read Full Post on Website →
                </a>
            </div>
        </div>
        """
        msg.attach(MIMEText(body, 'html'))

        if video_mp4_bytes:
            try:
                part = MIMEBase('video', 'mp4')
                part.set_payload(video_mp4_bytes)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=f'WarmInsight_{cat}_Video.mp4')
                msg.attach(part)
            except Exception as e:
                print(f"   ⚠️ MP4 Attachment Error: {e}")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ Social Email Sent Successfully!")
    except Exception as e:
        print(f"   ❌ Social Email Failed: {e}")

# ═══════════════════════════════════════════════
# 🛡️ SYSTEM UTILS & API ENGINE
# ═══════════════════════════════════════════════
_gemini_client = None
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None: _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client

def check_env_vars():
    missing = [v for v, k in zip(["GEMINI_API_KEY", "WP_USERNAME", "WP_APP_PASSWORD"], [GEMINI_API_KEY, WP_USER, WP_APP_PASS]) if not k]
    if missing:
        print(f"❌ Missing Secrets: {missing}")
        return False
    return True

def verify_wp_credentials():
    print(f"   🔍 [System] Checking WP Connection to: {WP_URL}")
    try:
        resp = scraper.get(f"{WP_URL}/wp-json/wp/v2/users/me", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=25)
        try:
            resp_json = resp.json()
            is_valid_json = isinstance(resp_json, dict) and "id" in resp_json
        except:
            is_valid_json = False

        if resp.status_code == 200 and is_valid_json: 
            print("   ✅ WP Auth Successful!")
            return True
        else:
            print(f"   ❌ WP Auth Failed or Blocked by WAF! (HTTP Status: {resp.status_code})")
    except Exception as e: 
        print(f"   ❌ WP Connection Error (Timeout/Firewall): {e}")
    return False

def call_gemini(client, model, prompt, sys_inst=None, retries=5):
    if not sys_inst:
        sys_inst = "You are an elite financial analyst. ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN. You MUST strictly follow the required output format. You MUST wrap EVERY section of your response in the exact XML tags requested."

    config = types.GenerateContentConfig(
        system_instruction=sys_inst,
        temperature=0.7,
        max_output_tokens=8192
    )
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt, config=config)
            if r.text: return str(r.text)
        except Exception as e:
            err = str(e)
            if "credits are depleted" in err or "billing" in err.lower():
                print("   🚨 Credits depleted!")
                return None
            if "404" in err or "not found" in err.lower(): return None
            if "503" in err or "UNAVAILABLE" in err:
                wait = (15 * i) + random.uniform(-2, 5)
                time.sleep(wait)
            elif "429" in err:
                time.sleep(30 + random.uniform(0, 10))
            elif i < retries: time.sleep(5 * i)
    return None

def gem_fb(tier, prompt, sys_inst=None):
    client = _get_gemini_client()
    for m in MODEL_PRI.get(tier, FAST_MODELS):
        r = call_gemini(client, m, prompt, sys_inst)
        if r: return r
    return ""

def xtag(raw, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL | re.IGNORECASE)
    if m:
        res = m.group(1).strip()
        res = re.sub(r"^`{3}(html|xml|text|markdown)?\n", "", res, flags=re.IGNORECASE)
        res = re.sub(r"\n`{3}$", "", res)
        return res.strip()
    return ""

def sanitize(html):
    html = re.sub(r"<script(?!\s+type=['\"]application/ld\+json['\"])[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    return re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.DOTALL)

def make_slug(kw, title, cat):
    base = kw if (kw and len(kw) > 4) else title
    slug = re.sub(r"[^\w\s-]", "", base.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:55]
    return f"{slug}-{datetime.datetime.utcnow().strftime('%m%d%H%M')}"

def _clean_seo_title(title):
    for p in ["[👑 VIP] ", "[💎 Pro] ", "[PRO] ", "[VIP] ", "[PRO]", "[VIP]", "[Pro] ", "[VIP] ", "[Pro] "]:
        title = title.replace(p, "")
    return title.strip()

def get_or_create_wp_category(cat_name):
    slug = cat_name.lower().replace(" ", "-")
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = scraper.post(f"{WP_URL}/wp-json/wp/v2/categories", headers=WP_API_HEADERS, json={"name": cat_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_or_create_wp_tag(tag_name):
    slug = tag_name.lower().replace(" ", "-")
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/tags?slug={slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = scraper.post(f"{WP_URL}/wp-json/wp/v2/tags", headers=WP_API_HEADERS, json={"name": tag_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_wp_author_id(author_full_string):
    search_name = author_full_string.split("&")[0].strip()
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/users", headers=WP_API_HEADERS, params={"search": search_name}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200:
            users = r.json()
            if len(users) > 0: return users[0]["id"]
    except: pass
    return None

def _get_latest_post_category_name():
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/posts?per_page=1&status=publish", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200:
            try: r_json = r.json()
            except: return None
            if isinstance(r_json, list) and len(r_json) > 0:
                cat_ids = r_json[0].get('categories', [])
                if not cat_ids: return None
                r_cats = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=100", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
                if r_cats.status_code == 200:
                    try: r_cats_json = r_cats.json()
                    except: return None
                    if isinstance(r_cats_json, list):
                        cat_map = {c['id']: c['name'] for c in r_cats_json}
                        for cid in cat_ids:
                            name = cat_map.get(cid)
                            if name in CATEGORIES: return name
    except: pass
    return None

def already_published_today(cat):
    try:
        cat_slug = cat.lower().replace(" ", "-")
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={cat_slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code != 200: return False
        try:
            r_json = r.json()
            if not isinstance(r_json, list) or not r_json: return False
            cat_id = r_json[0]["id"]
        except: return False

        r2 = scraper.get(f"{WP_URL}/wp-json/wp/v2/posts", headers=WP_API_HEADERS, params={"categories": cat_id, "per_page": 1, "status": "publish"}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code == 200:
            try:
                r2_json = r2.json()
                if isinstance(r2_json, list) and len(r2_json) > 0:
                    latest_post = r2_json[0]
                    post_date_gmt = latest_post.get("date_gmt", "")[:10] 
                    today_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d")
                    if post_date_gmt == today_utc: return True
            except: pass
    except: pass
    return False

def fetch_news_pool(cat, max_items=15):
    feeds = RSS_FEEDS.get(cat, RSS_FEEDS["Economy"])
    items = set()
    for url in feeds:
        try:
            resp = scraper.get(url, headers=EXTERNAL_HEADERS, timeout=15)
            if resp.status_code == 200:
                d = feedparser.parse(resp.text)
                for e in d.entries[:40]:
                    title = getattr(e, 'title', '').strip()
                    summary = re.sub(r'<[^>]+>', '', getattr(e, 'summary', ''))[:200].strip()
                    if title and len(title) > 10: items.add(f"• {title}: {summary}")
            else:
                print(f"   ⚠️ RSS feed blocked by WAF or returned {resp.status_code}: {url}")
        except Exception as ex:
            print(f"   ⚠️ RSS feed error on {url}: {ex}")
            pass
            
    items_list = list(items)
    random.shuffle(items_list)
    return items_list[:max_items]

def generate_video_mp4(cat, hook_text, data_points, frames_images):
    print("   🎥 Generating 15-Sec Pixar Style Character Reels Video...")
    try:
        import numpy as np
        from moviepy.editor import ImageClip, concatenate_videoclips
    except ImportError as e:
        print(f"   ❌ MoviePy import failed: {e}")
        return None
    try:
        SLIDE_DURATION = 2.6
        CROSSFADE_DURATION = 0.2
        ZOOM_START = 1.0
        ZOOM_END = 1.08

        clips = []
        for i, frame in enumerate(frames_images):
            frame_np = np.array(frame.convert('RGB'))
            clip = ImageClip(frame_np).set_duration(SLIDE_DURATION)
            if i % 2 == 0: clip = clip.resize(lambda t: ZOOM_START + (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            else: clip = clip.resize(lambda t: ZOOM_END - (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            clip = clip.set_position(('center', 'center'))
            if i > 0: clip = clip.crossfadein(CROSSFADE_DURATION)
            clips.append(clip)

        video = concatenate_videoclips(clips, padding=-CROSSFADE_DURATION, method="compose")
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        video.write_videofile(
            temp_path, fps=30, codec='libx264', bitrate='2500k', audio=False, preset='fast',
            ffmpeg_params=[
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1:1',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-profile:v', 'main', '-level', '4.0',
                '-x264-params', 'colorprim=bt709:transfer=bt709:colormatrix=bt709'
            ],
            logger=None
        )
        with open(temp_path, 'rb') as f: mp4_bytes = f.read()
        os.remove(temp_path)
        print(f"   ✅ Friendly Character 15s Video Extracted! ({len(mp4_bytes)/1024/1024:.1f}MB)")
        return mp4_bytes
    except Exception as e:
        print(f"   ❌ Video Encoding Failed: {e}")
        return None

def generate_vip_carousel(raw_content, cat):
    print("    🎨 Generating DYNAMIC 3-IMAGE Friendly Character Carousel (Red & Gold Mix)...")
    client = _get_gemini_client()

    sys_inst = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
    You are a TOP-TIER viral content creator for finance Instagram/TikTok. Write entirely in ENGLISH.
    Your job: Extract data + write COPY THAT STOPS THE SCROLL.

    OUTPUT RULES (CRITICAL):
    - HOOK: Pattern interrupt opener. Use shocking number, contrarian take, or curiosity gap. Max 7 words.
    - SHOCK_STAT: One jaw-dropping statistic that proves the hook. Max 6 words. Include numbers.
    - INSIGHT_LINE: The "aha moment" payoff. Max 8 words. Confident, declarative.
    - CTA_HOOK: Urgency/FOMO trigger for the last slide. Max 6 words.

    Format EXACTLY:
    <MAIN_TITLE>Main viral headline, max 5 words, ALL CAPS, energetic</MAIN_TITLE>
    <BADGE>e.g. IMPACT: HIGH</BADGE>
    <HOOK>Scroll-stopping opener (max 7 words)</HOOK>
    <SHOCK_STAT>Jaw-dropping stat (max 6 words, with numbers)</SHOCK_STAT>
    <QUESTION>Engagement question for comments</QUESTION>
    <INSIGHT_LINE>The aha moment (max 8 words)</INSIGHT_LINE>
    <CTA_HOOK>FOMO trigger (max 6 words)</CTA_HOOK>
    <REELS_SCRIPT>60-second spoken script with hook-stat-story-CTA structure</REELS_SCRIPT>
    <IG_CAPTION>Caption with hook, value, CTA, 15+ hashtags</IG_CAPTION>
    <SMART_COMMENT>Bloomberg/WSJ-style comment for free traffic</SMART_COMMENT>
    <ITEM1>TICKER | Value with % or $</ITEM1>
    <ITEM2>TICKER | Value with % or $</ITEM2>
    <ITEM3>TICKER | Value with % or $</ITEM3>
    <ITEM4>TICKER | Value with % or $</ITEM4>
    <ITEM5>TICKER | Value with % or $</ITEM5>
    """
    raw_data = gem_fb("vip", raw_content, sys_inst)

    main_title = xtag(raw_data, "MAIN_TITLE") or f"{cat.upper()} ALERT"
    badge_text = xtag(raw_data, "BADGE") or "IMPACT: HIGH"
    hook_text = xtag(raw_data, "HOOK") or "Wall Street Just Did THIS 🚨"
    shock_stat = xtag(raw_data, "SHOCK_STAT") or "$2.3T MOVED OVERNIGHT"
    question_text = xtag(raw_data, "QUESTION") or "Where's YOUR money going? 👇"
    insight_line = xtag(raw_data, "INSIGHT_LINE") or "SMART MONEY IS MOVING NOW"
    cta_hook = xtag(raw_data, "CTA_HOOK") or "DONT MISS THE NEXT MOVE"
    reels_script = xtag(raw_data, "REELS_SCRIPT") or "Script generation failed."
    ig_caption = xtag(raw_data, "IG_CAPTION") or f"{hook_text}\n\nLink in bio for the full breakdown. #investing #finance #stocks"
    smart_comment = xtag(raw_data, "SMART_COMMENT") or "Interesting market shift. Just published a full breakdown on this."

    data_points = []
    for i in range(1, 6):
        item = xtag(raw_data, f"ITEM{i}")
        if item and "|" in item:
            parts = item.split("|")
            raw_ticker = parts[0].strip()
            if len(raw_ticker) > 10: raw_ticker = raw_ticker[:8] + ".."
            data_points.append({"ticker": raw_ticker, "val": parts[1].strip()})

    if len(data_points) < 5:
        data_points = [
            {"ticker": "$NVDA", "val": "+6.2%"}, {"ticker": "$AAPL", "val": "+5.3%"},
            {"ticker": "$MSFT", "val": "+4.9%"}, {"ticker": "$BTC", "val": "+4.2%"},
            {"ticker": "$ETH", "val": "+2.3%"}
        ]

    W, H = 1080, 1920
    BG = "#000000"
    WHITE = "#ffffff"
    GOLD = "#fde047"    # 가독성 및 프리미엄 상징
    RED = "#ef4444"     # 긴급성 및 강조 상징
    GRAY = "#94a3b8"

    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    def lf(p, s):
        try: return ImageFont.truetype(p, s)
        except: return ImageFont.load_default()

    font_title = lf(ft_path, 115)    
    font_huge = lf(ft_path, 220)    
    font_mega = lf(ft_path, 150)    
    font_sub = lf(ft_path, 65)
    font_data = lf(ft_path, 60)
    font_alert = lf(ft_path, 90)

    vp_base = "A cute, friendly, extremely simple 3D white robot mascot with a smooth round head and simple smiling eyes. Pixar animation style. Clean dark minimalist studio background. Soft cinematic lighting. No text, no letters."
    vp1 = vp_base + f" The cute robot is looking surprised, putting its hands on its cheeks in shock. {cat} theme."
    vp2 = vp_base + f" The cute robot is holding a glowing magnifying glass, looking closely at a floating digital chart."
    vp3 = vp_base + f" The cute robot is confidently pointing forward and giving a thumbs up, with a bright glowing aura."

    def fetch_friendly_image(prompt_text, seed):
        try:
            res = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt_text,
                config=types.GenerateImagesConfig(
                    number_of_images=1, aspect_ratio="1:1", output_mime_type="image/jpeg"
                )
            )
            img_bytes = res.generated_images[0].image.image_bytes
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        except Exception as e:
            print(f"    ⚠️ Gemini failed, trying Pollinations: {e}")
            try:
                prompt_encoded = urllib.parse.quote(prompt_text)
                url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1080&height=1080&nologo=true&seed={seed}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    img = Image.open(io.BytesIO(response.read())).convert("RGBA")
            except Exception as e2:
                print(f"    ⚠️ Pollinations failed: {e2}")
                return None
        
        img = img.resize((1080, 1080), Image.LANCZOS)
        mask = Image.new("L", (1080, 1080), 255)
        mask_draw = ImageDraw.Draw(mask)
        for y in range(700, 1080):
            alpha = int(255 - (y - 700) * (255 / 380))
            mask_draw.line([(0, y), (1080, y)], fill=alpha)
        img.putalpha(mask)
        return img

    print("    [AI] Requesting 3 UNIQUE Friendly Character images (Sequential)...")
    img_hook_ai = fetch_friendly_image(vp1, random.randint(1, 100000))
    time.sleep(2)
    img_stat_ai = fetch_friendly_image(vp2, random.randint(1, 100000))
    time.sleep(2)
    img_out_ai  = fetch_friendly_image(vp3, random.randint(1, 100000))

    def paste_bg(d_img, target_ai_img):
        if target_ai_img:
            d_img.paste(target_ai_img, (0, 0), target_ai_img)
        else:
            fallback_img = Image.new("RGBA", (1080, 1080), "#09090b")
            d = ImageDraw.Draw(fallback_img)
            d.ellipse([440, 250, 640, 450], fill="#f8fafc") 
            d.rounded_rectangle([460, 470, 620, 750], radius=40, fill="#f8fafc") 
            mask = Image.new("L", (1080, 1080), 255)
            mask_draw = ImageDraw.Draw(mask)
            for y in range(700, 1080):
                alpha = int(255 - (y - 700) * (255 / 380))
                mask_draw.line([(0, y), (1080, y)], fill=alpha)
            fallback_img.putalpha(mask)
            d_img.paste(fallback_img, (0, 0), fallback_img)

    def wrap_lines(text, font, max_width):
        words = text.split()
        lines, line = [], []
        d = ImageDraw.Draw(Image.new("RGB", (1,1)))
        for ww in words:
            test_str = " ".join(line + [ww])
            try: tw = d.textlength(test_str, font=font)
            except: tw = len(test_str) * 40  
            if tw < max_width: line.append(ww)
            else:
                if line: lines.append(" ".join(line))
                line = [ww]
        if line: lines.append(" ".join(line))
        return lines

    # --- Slide 1 (Hook) ---
    img1 = Image.new("RGB", (W, H), BG)
    paste_bg(img1, img_hook_ai)
    d1 = ImageDraw.Draw(img1)
    
    # 🚨 상단 경고 배지: 긴급성을 위한 RED
    d1.rounded_rectangle([300, 1100, 780, 1200], radius=20, fill=RED) 
    d1.text((W//2, 1150), f"🚨 {cat.upper()} ALERT", fill=WHITE, font=font_alert, anchor="mm")
    
    # 💡 훅 텍스트: 마지막 줄만 시선 집중을 위해 GOLD 강조
    hook_lines = wrap_lines(hook_text.upper(), font_title, 850) 
    y_text = 1330
    for i, ln in enumerate(hook_lines[:4]):
        color = GOLD if i == len(hook_lines[:4])-1 else WHITE
        d1.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 120 
    d1.text((W//2, 1800), "↓ SWIPE TO SEE WHY ↓", fill=GRAY, font=font_sub, anchor="mm")

    # --- Slide 2 (Shock Stat) ---
    img2 = Image.new("RGB", (W, H), BG)
    paste_bg(img2, img_stat_ai)
    d2 = ImageDraw.Draw(img2)
    
    # 💡 소제목: 고급스러운 GOLD
    d2.text((W//2, 1150), "THE NUMBER", fill=GOLD, font=font_sub, anchor="mm")
    
    # 🚨 충격 수치: 마지막 줄만 충격 효과를 위해 RED 강조
    shock_lines = wrap_lines(shock_stat.upper(), font_mega, 850)
    y_text = 1350
    for i, ln in enumerate(shock_lines[:3]):
        color = RED if i == len(shock_lines[:3])-1 else WHITE
        d2.text((W//2, y_text), ln, fill=color, font=font_mega, anchor="mm")
        y_text += 160 
    d2.text((W//2, 1800), "WAIT FOR IT...", fill=GRAY, font=font_sub, anchor="mm")

    # --- Slides 3~5 (Data Points) ---
    data_imgs = []
    for idx in range(3):
        if idx >= len(data_points): break
        item = data_points[idx]
        img_d = Image.new("RGB", (W, H), BG)
        paste_bg(img_d, img_stat_ai)
        d = ImageDraw.Draw(img_d)
        
        # 🚨 카테고리 알림: RED
        d.text((W//2, 1100), cat.upper(), fill=RED, font=font_sub, anchor="mm")
        d.text((W//2, 1200), f"WATCH THIS → {idx+1}/3", fill=GRAY, font=font_data, anchor="mm")
        d.text((W//2, 1380), item['ticker'], fill=WHITE, font=font_title, anchor="mm")
        
        # 💡 지표 컬러: 하락(-)이면 RED, 상승/중립이면 GOLD
        val_str = item['val']
        val_color = RED if '-' in val_str else GOLD
        
        current_huge_size = 220
        if len(val_str) > 6: current_huge_size = int(220 * (6 / len(val_str)))
        current_font_huge = lf(ft_path, max(100, current_huge_size))
        
        d.text((W//2, 1550), val_str, fill=val_color, font=current_font_huge, anchor="mm")
        
        # 💡 페이지 도트: 활성화된 페이지는 GOLD
        dot_y = 1800
        for di in range(3):
            dx = W//2 + (di - 1) * 60
            color = GOLD if di == idx else "#3f3f46"
            d.ellipse([dx-15, dot_y-15, dx+15, dot_y+15], fill=color)
        data_imgs.append(img_d)

    # --- Slide 6 (Takeaway) ---
    img6 = Image.new("RGB", (W, H), BG)
    paste_bg(img6, img_out_ai)
    d6 = ImageDraw.Draw(img6)
    
    # 💡 결론 소제목: GOLD
    d6.text((W//2, 1100), "THE TAKEAWAY", fill=GOLD, font=font_sub, anchor="mm")
    
    # 💡 핵심 문장: 마지막 줄 GOLD 강조
    insight_lines = wrap_lines(insight_line.upper(), font_title, 850)
    y_text = 1250
    for i, ln in enumerate(insight_lines[:3]):
        color = GOLD if i == len(insight_lines[:3])-1 else WHITE
        d6.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 120
        
    # 🚨 마지막 행동 촉구(CTA): 가장 강력한 RED
    d6.text((W//2, 1650), cta_hook.upper(), fill=RED, font=font_alert, anchor="mm")
    d6.text((W//2, 1780), "LINK IN BIO → @WARMINSIGHT", fill=GRAY, font=font_sub, anchor="mm")

    image_bytes_list = []
    all_frames = [img1, img2] + data_imgs + [img6]
    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, all_frames)

    return image_bytes_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes

def _upload_image(img_bytes, filename):
    try:
        resp = scraper.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"}, 
            data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30
        )
        if resp.status_code in (200, 201): return resp.json().get("id")
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, author_name, raw_for_cards=None, med_img_bytes=None):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat)

    insight_cat_id = None
    if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
        insight_cat_id = get_or_create_wp_category("Insight")

    if tier == "unified": tag_id = get_or_create_wp_tag("Insight")
    elif tier == "vip": tag_id = get_or_create_wp_tag("VIP")
    else: tag_id = get_or_create_wp_tag("Pro")

    author_id = get_wp_author_id(author_name)
    display_title = title if cat in ["Foundation", "The Daily Catalyst", "Money Hack"] or tier == "unified" else (f"[VIP] {title}" if tier == "vip" else f"[Pro] {title}")

    post_data = {
        "title": display_title,
        "content": html,
        "status": "publish",
        "slug": slug,
    }

    if author_id: post_data["author"] = author_id
    if media_id: post_data["featured_media"] = media_id

    cats = []
    if cat_id: cats.append(cat_id)
    if insight_cat_id: cats.append(insight_cat_id)

    if cats: post_data["categories"] = cats
    if tag_id: post_data["tags"] = [tag_id]

    seo_title = _clean_seo_title(title)
    rm_title = seo_title if len(seo_title) > 50 else f"{seo_title} | Warm Insight"

    post_data["meta"] = {
        "rank_math_title": rm_title[:60],
        "rank_math_description": (exc or "")[:160],
        "rank_math_focus_keyword": kw.lower() if kw else "",
        "is_premium": "no" if cat in ["Foundation", "Money Hack"] else "yes",
        "pms_content_restrict": "0" if cat in ["Foundation", "Money Hack"] else "1",
        "post_tier": tier.upper(),
    }

    try:
        r = scraper.post(
            f"{WP_URL}/wp-json/wp/v2/posts",
            json=post_data, auth=(WP_USER, WP_APP_PASS), timeout=30
        )
        if r.status_code in (200, 201):
            try:
                resp_json = r.json()
                link = resp_json.get('link') if isinstance(resp_json, dict) else None
            except: link = None
            
            if link:
                print(f"   ✅ Published: {link}")
                
                if raw_for_cards:
                    if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
                        if tier == "vip" or tier == "unified":
                            img_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes = generate_vip_carousel(raw_for_cards, cat)
                            if video_mp4_bytes:
                                send_social_style_email(display_title, link, img_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes)
                        
                        yt_meta, yt_script = generate_youtube_masterpiece(raw_for_cards, title)
                        if yt_script: send_youtube_script_email(title, yt_meta, yt_script)

                send_medium_draft_email(display_title, link, raw_for_cards, cat, kw, med_img_bytes)
                send_community_viral_email(display_title, link, raw_for_cards, cat)
                
                return True
            else:
                print(f"   ❌ [WAF Block Detected] Server returned 200 but no link was created.")
                return False
        else:
            print(f"   ❌ Publish failed. HTTP Status: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Network error: {e}")
    return False

def run_foundation_pipeline():
    cat = "Foundation"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 SEO Foundation Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    theme = random.choice(FOUNDATION_TOPICS)
    tier = "premium"
    raw = gem_fb(tier, FOUNDATION_PROMPT.replace("{theme}", theme), FOUNDATION_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Education Team")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_foundation_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return
            
        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_philosophy_pipeline():
    cat = "The Daily Catalyst"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 Catalyst Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    theme = random.choice(PHILOSOPHY_TOPICS)
    tier = "premium"
    raw = gem_fb(tier, PHILOSOPHY_PROMPT.replace("{theme}", theme), PHILOSOPHY_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Philosophical Desk")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_philosophy_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return

        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_moneyhack_pipeline():
    cat = "Money Hack"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 Money Hack Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    niche = random.choice(MH_NICHES)
    platform = random.choice(MH_PLATFORMS)
    ai_tool = random.choice(MH_AI_TOOLS)
    theme = f"Niche: {niche} | Core Platform: {platform} | AI Automation Tool: {ai_tool}"
    print(f"   🎲 Random Framework Selected: {theme}")

    tier = "premium"
    raw = gem_fb(tier, MONEY_HACK_PROMPT.replace("{theme}", theme), MONEY_HACK_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Growth Team")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_money_hack_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return

        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_news_pipeline(forced_cat=None):
    current_time = datetime.datetime.utcnow()
    day_of_week = current_time.weekday()
    day_of_year = current_time.timetuple().tm_yday
    
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"

    if forced_cat:
        cat = forced_cat
        print(f"🎯 [Command Override] Forcing category to: {cat}")
    elif day_of_week in (1, 3):
        cat = "On-Chain"
        print(f"📅 [Smart Schedule] Today is Tue/Thu. Locking category to: {cat}")
    else:
        base_cats = [c for c in CATEGORIES if c not in ["On-Chain", "Money Hack"]]
        cat = base_cats[day_of_year % len(base_cats)]

    if force:
        print(f"🚀 Starting v46.9.60 Unified News Pipeline | TEST MODE (Force Publish)")
    else:
        print(f"🚀 Starting v46.9.60 Unified News Pipeline | Category: {cat}")

    if not check_env_vars() or not verify_wp_credentials(): return

    if force:
        if forced_cat:
            pass
        else:
            latest_cat = _get_latest_post_category_name()
            available_cats = [c for c in CATEGORIES if c not in [latest_cat, "Money Hack"]]
            if not available_cats: available_cats = [c for c in CATEGORIES if c != "Money Hack"]
            
            random.shuffle(available_cats)
            cat = available_cats[0]
            for fallback_cat in available_cats:
                if not already_published_today(fallback_cat):
                    cat = fallback_cat
                    break
            print(f"   ⚡ [TEST MODE] Forcing random category '{cat}' avoiding '{latest_cat}'.")
    else:
        if already_published_today(cat):
            print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
            return

    all_news = fetch_news_pool(cat)
    total_news = len(all_news)
    if total_news < 2:
        print(f"   ❌ Not enough news for {cat} ({total_news}). Aborting.")
        return

    news_str = "\n".join(all_news)
    tier = "unified"

    raw1 = gem_fb(tier, PROMPT_UNIFIED_P1.replace("{cat}", cat).replace("{news}", news_str))
    if not raw1:
        print("   ❌ Part 1 generation failed.")
        return

    ctx = "Title: " + xtag(raw1, "TITLE") + "\nSummary: " + xtag(raw1, "EXECUTIVE_SUMMARY")
    raw2 = gem_fb(tier, PROMPT_UNIFIED_P2.replace("{cat}", cat).replace("{ctx}", ctx))
    if not raw2:
        print("   ⚠️ Part 2 failed. Using Part 1 only.")
        raw = raw1
    else:
        raw = raw1 + "\n" + raw2

    title = xtag(raw, "TITLE")
    kw = xtag(raw, "SEO_KEYWORD")
    exc = xtag(raw, "EXCERPT") or xtag(raw, "EXECUTIVE_SUMMARY")
    slug = make_slug(kw, title, cat)
    author = VIP_AUTHORS.get(cat, "Warm Insight Editorial Team")
    tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
    
    html = build_html(tier, cat, raw, author, tf, title)

    img_bytes = make_thumbnail(title, cat, tier)
    if not img_bytes or len(img_bytes) < 1000:
        print(f"   ❌ Thumbnail error. Aborting.")
        return
        
    med_img_bytes = make_medium_thumbnail(cat)

    publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)
    time.sleep(TIER_SLEEP[tier])

# =====================================================================
# ★ BLOCK 3: 세 번째 반복 블록 (원본 보존용) ★
# =====================================================================

# ═══════════════════════════════════════════════
# ✉️ 슬림 이메일 (인스타/숏폼용)
# ═══════════════════════════════════════════════
def send_social_style_email(title, link, image_bytes_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS or not EMAIL_RECEIVER:
        print("   ⚠️ Missing email credentials. Skipping email dispatch.")
        return

    print(f"   📧 Sending Social Slim Package to {EMAIL_RECEIVER}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"🚨 {cat.upper()} REELS READY: {hook_text[:40]}..."

        vid_tag = ""
        if video_mp4_bytes:
            vid_tag = f"""
            <div style="margin-bottom: 25px; text-align:center; padding: 25px; background: #0f172a; border-radius: 16px; border: 2px solid #10b981;">
                <p style="color: #10b981; font-weight: 900; font-size: 18px; margin-top: 0; text-transform: uppercase;">🎬 15-Sec Viral Reels Attached!</p>
                <div style="font-size: 45px; margin: 15px 0;">✨ 📹 ✨</div>
                <p style="color: #ffffff; font-size: 15px; font-weight: bold; margin: 5px 0;">100% Compatible with IG Reels / TikTok / YT Shorts.</p>
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0; margin-top: 10px;">Download <strong>WarmInsight_{cat}_Video.mp4</strong> attached below.</p>
            </div>
            """

        body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f4f4f5; padding: 20px; color: #0f1419;">
            {vid_tag}
            <div style="background: #ffffff; border-left: 5px solid #eab308; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #ca8a04; font-size: 18px;">🎬 1-Min Reels Script</h3>
                <p style="font-size: 14px; color: #52525b; margin-bottom: 15px;">Read this directly or plug into AI Voice.</p>
                <div style="background: #fefce8; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; font-style: italic;">
                    {reels_script.replace(chr(10), '<br>')}
                </div>
            </div>
            <div style="background: #ffffff; border-left: 5px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #2563eb; font-size: 18px;">💬 Smart Community Comment</h3>
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; font-size: 15px; font-weight: bold; color: #1e3a8a;">
                    "{smart_comment}"
                </div>
            </div>
            <div style="background: #ffffff; border-left: 5px solid #10b981; padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #059669; font-size: 18px;">📱 Instagram Feed Caption</h3>
                <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; white-space: pre-wrap;">{ig_caption}</div>
            </div>
            <hr style="border:0; height:2px; background:#d4d4d8; margin: 30px 0;">
            <div style="text-align:center; margin-bottom: 20px;">
                <a href="{link}" style="display: inline-block; background-color: #0f1419; color: #ffffff; padding: 12px 24px; border-radius: 9999px; text-decoration: none; font-weight: bold; font-size: 15px;">
                    Read Full Post on Website →
                </a>
            </div>
        </div>
        """
        msg.attach(MIMEText(body, 'html'))

        if video_mp4_bytes:
            try:
                part = MIMEBase('video', 'mp4')
                part.set_payload(video_mp4_bytes)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=f'WarmInsight_{cat}_Video.mp4')
                msg.attach(part)
            except Exception as e:
                print(f"   ⚠️ MP4 Attachment Error: {e}")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ Social Email Sent Successfully!")
    except Exception as e:
        print(f"   ❌ Social Email Failed: {e}")

# ═══════════════════════════════════════════════
# 🛡️ SYSTEM UTILS & API ENGINE
# ═══════════════════════════════════════════════
_gemini_client = None
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None: _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client

def check_env_vars():
    missing = [v for v, k in zip(["GEMINI_API_KEY", "WP_USERNAME", "WP_APP_PASSWORD"], [GEMINI_API_KEY, WP_USER, WP_APP_PASS]) if not k]
    if missing:
        print(f"❌ Missing Secrets: {missing}")
        return False
    return True

def verify_wp_credentials():
    print(f"   🔍 [System] Checking WP Connection to: {WP_URL}")
    try:
        resp = scraper.get(f"{WP_URL}/wp-json/wp/v2/users/me", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=25)
        try:
            resp_json = resp.json()
            is_valid_json = isinstance(resp_json, dict) and "id" in resp_json
        except:
            is_valid_json = False

        if resp.status_code == 200 and is_valid_json: 
            print("   ✅ WP Auth Successful!")
            return True
        else:
            print(f"   ❌ WP Auth Failed or Blocked by WAF! (HTTP Status: {resp.status_code})")
    except Exception as e: 
        print(f"   ❌ WP Connection Error (Timeout/Firewall): {e}")
    return False

def call_gemini(client, model, prompt, sys_inst=None, retries=5):
    if not sys_inst:
        sys_inst = "You are an elite financial analyst. ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN. You MUST strictly follow the required output format. You MUST wrap EVERY section of your response in the exact XML tags requested."

    config = types.GenerateContentConfig(
        system_instruction=sys_inst,
        temperature=0.7,
        max_output_tokens=8192
    )
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt, config=config)
            if r.text: return str(r.text)
        except Exception as e:
            err = str(e)
            if "credits are depleted" in err or "billing" in err.lower():
                print("   🚨 Credits depleted!")
                return None
            if "404" in err or "not found" in err.lower(): return None
            if "503" in err or "UNAVAILABLE" in err:
                wait = (15 * i) + random.uniform(-2, 5)
                time.sleep(wait)
            elif "429" in err:
                time.sleep(30 + random.uniform(0, 10))
            elif i < retries: time.sleep(5 * i)
    return None

def gem_fb(tier, prompt, sys_inst=None):
    client = _get_gemini_client()
    for m in MODEL_PRI.get(tier, FAST_MODELS):
        r = call_gemini(client, m, prompt, sys_inst)
        if r: return r
    return ""

def xtag(raw, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL | re.IGNORECASE)
    if m:
        res = m.group(1).strip()
        res = re.sub(r"^`{3}(html|xml|text|markdown)?\n", "", res, flags=re.IGNORECASE)
        res = re.sub(r"\n`{3}$", "", res)
        return res.strip()
    return ""

def sanitize(html):
    html = re.sub(r"<script(?!\s+type=['\"]application/ld\+json['\"])[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    return re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.DOTALL)

def make_slug(kw, title, cat):
    base = kw if (kw and len(kw) > 4) else title
    slug = re.sub(r"[^\w\s-]", "", base.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:55]
    return f"{slug}-{datetime.datetime.utcnow().strftime('%m%d%H%M')}"

def _clean_seo_title(title):
    for p in ["[👑 VIP] ", "[💎 Pro] ", "[PRO] ", "[VIP] ", "[PRO]", "[VIP]", "[Pro] ", "[VIP] ", "[Pro] "]:
        title = title.replace(p, "")
    return title.strip()

def get_or_create_wp_category(cat_name):
    slug = cat_name.lower().replace(" ", "-")
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = scraper.post(f"{WP_URL}/wp-json/wp/v2/categories", headers=WP_API_HEADERS, json={"name": cat_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_or_create_wp_tag(tag_name):
    slug = tag_name.lower().replace(" ", "-")
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/tags?slug={slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = scraper.post(f"{WP_URL}/wp-json/wp/v2/tags", headers=WP_API_HEADERS, json={"name": tag_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_wp_author_id(author_full_string):
    search_name = author_full_string.split("&")[0].strip()
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/users", headers=WP_API_HEADERS, params={"search": search_name}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200:
            users = r.json()
            if len(users) > 0: return users[0]["id"]
    except: pass
    return None

def _get_latest_post_category_name():
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/posts?per_page=1&status=publish", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200:
            try: r_json = r.json()
            except: return None
            if isinstance(r_json, list) and len(r_json) > 0:
                cat_ids = r_json[0].get('categories', [])
                if not cat_ids: return None
                r_cats = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=100", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
                if r_cats.status_code == 200:
                    try: r_cats_json = r_cats.json()
                    except: return None
                    if isinstance(r_cats_json, list):
                        cat_map = {c['id']: c['name'] for c in r_cats_json}
                        for cid in cat_ids:
                            name = cat_map.get(cid)
                            if name in CATEGORIES: return name
    except: pass
    return None

def already_published_today(cat):
    try:
        cat_slug = cat.lower().replace(" ", "-")
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={cat_slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code != 200: return False
        try:
            r_json = r.json()
            if not isinstance(r_json, list) or not r_json: return False
            cat_id = r_json[0]["id"]
        except: return False

        r2 = scraper.get(f"{WP_URL}/wp-json/wp/v2/posts", headers=WP_API_HEADERS, params={"categories": cat_id, "per_page": 1, "status": "publish"}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code == 200:
            try:
                r2_json = r2.json()
                if isinstance(r2_json, list) and len(r2_json) > 0:
                    latest_post = r2_json[0]
                    post_date_gmt = latest_post.get("date_gmt", "")[:10] 
                    today_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d")
                    if post_date_gmt == today_utc: return True
            except: pass
    except: pass
    return False

def fetch_news_pool(cat, max_items=15):
    feeds = RSS_FEEDS.get(cat, RSS_FEEDS["Economy"])
    items = set()
    for url in feeds:
        try:
            resp = scraper.get(url, headers=EXTERNAL_HEADERS, timeout=15)
            if resp.status_code == 200:
                d = feedparser.parse(resp.text)
                for e in d.entries[:40]:
                    title = getattr(e, 'title', '').strip()
                    summary = re.sub(r'<[^>]+>', '', getattr(e, 'summary', ''))[:200].strip()
                    if title and len(title) > 10: items.add(f"• {title}: {summary}")
            else:
                print(f"   ⚠️ RSS feed blocked by WAF or returned {resp.status_code}: {url}")
        except Exception as ex:
            print(f"   ⚠️ RSS feed error on {url}: {ex}")
            pass
            
    items_list = list(items)
    random.shuffle(items_list)
    return items_list[:max_items]

def generate_video_mp4(cat, hook_text, data_points, frames_images):
    print("   🎥 Generating 15-Sec Pixar Style Character Reels Video...")
    try:
        import numpy as np
        from moviepy.editor import ImageClip, concatenate_videoclips
    except ImportError as e:
        print(f"   ❌ MoviePy import failed: {e}")
        return None
    try:
        SLIDE_DURATION = 2.6
        CROSSFADE_DURATION = 0.2
        ZOOM_START = 1.0
        ZOOM_END = 1.08

        clips = []
        for i, frame in enumerate(frames_images):
            frame_np = np.array(frame.convert('RGB'))
            clip = ImageClip(frame_np).set_duration(SLIDE_DURATION)
            if i % 2 == 0: clip = clip.resize(lambda t: ZOOM_START + (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            else: clip = clip.resize(lambda t: ZOOM_END - (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            clip = clip.set_position(('center', 'center'))
            if i > 0: clip = clip.crossfadein(CROSSFADE_DURATION)
            clips.append(clip)

        video = concatenate_videoclips(clips, padding=-CROSSFADE_DURATION, method="compose")
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        video.write_videofile(
            temp_path, fps=30, codec='libx264', bitrate='2500k', audio=False, preset='fast',
            ffmpeg_params=[
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1:1',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-profile:v', 'main', '-level', '4.0',
                '-x264-params', 'colorprim=bt709:transfer=bt709:colormatrix=bt709'
            ],
            logger=None
        )
        with open(temp_path, 'rb') as f: mp4_bytes = f.read()
        os.remove(temp_path)
        print(f"   ✅ Friendly Character 15s Video Extracted! ({len(mp4_bytes)/1024/1024:.1f}MB)")
        return mp4_bytes
    except Exception as e:
        print(f"   ❌ Video Encoding Failed: {e}")
        return None

def generate_vip_carousel(raw_content, cat):
    print("    🎨 Generating DYNAMIC 3-IMAGE Friendly Character Carousel (Red & Gold Mix)...")
    client = _get_gemini_client()

    sys_inst = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
    You are a TOP-TIER viral content creator for finance Instagram/TikTok. Write entirely in ENGLISH.
    Your job: Extract data + write COPY THAT STOPS THE SCROLL.

    OUTPUT RULES (CRITICAL):
    - HOOK: Pattern interrupt opener. Use shocking number, contrarian take, or curiosity gap. Max 7 words.
    - SHOCK_STAT: One jaw-dropping statistic that proves the hook. Max 6 words. Include numbers.
    - INSIGHT_LINE: The "aha moment" payoff. Max 8 words. Confident, declarative.
    - CTA_HOOK: Urgency/FOMO trigger for the last slide. Max 6 words.

    Format EXACTLY:
    <MAIN_TITLE>Main viral headline, max 5 words, ALL CAPS, energetic</MAIN_TITLE>
    <BADGE>e.g. IMPACT: HIGH</BADGE>
    <HOOK>Scroll-stopping opener (max 7 words)</HOOK>
    <SHOCK_STAT>Jaw-dropping stat (max 6 words, with numbers)</SHOCK_STAT>
    <QUESTION>Engagement question for comments</QUESTION>
    <INSIGHT_LINE>The aha moment (max 8 words)</INSIGHT_LINE>
    <CTA_HOOK>FOMO trigger (max 6 words)</CTA_HOOK>
    <REELS_SCRIPT>60-second spoken script with hook-stat-story-CTA structure</REELS_SCRIPT>
    <IG_CAPTION>Caption with hook, value, CTA, 15+ hashtags</IG_CAPTION>
    <SMART_COMMENT>Bloomberg/WSJ-style comment for free traffic</SMART_COMMENT>
    <ITEM1>TICKER | Value with % or $</ITEM1>
    <ITEM2>TICKER | Value with % or $</ITEM2>
    <ITEM3>TICKER | Value with % or $</ITEM3>
    <ITEM4>TICKER | Value with % or $</ITEM4>
    <ITEM5>TICKER | Value with % or $</ITEM5>
    """
    raw_data = gem_fb("vip", raw_content, sys_inst)

    main_title = xtag(raw_data, "MAIN_TITLE") or f"{cat.upper()} ALERT"
    badge_text = xtag(raw_data, "BADGE") or "IMPACT: HIGH"
    hook_text = xtag(raw_data, "HOOK") or "Wall Street Just Did THIS 🚨"
    shock_stat = xtag(raw_data, "SHOCK_STAT") or "$2.3T MOVED OVERNIGHT"
    question_text = xtag(raw_data, "QUESTION") or "Where's YOUR money going? 👇"
    insight_line = xtag(raw_data, "INSIGHT_LINE") or "SMART MONEY IS MOVING NOW"
    cta_hook = xtag(raw_data, "CTA_HOOK") or "DONT MISS THE NEXT MOVE"
    reels_script = xtag(raw_data, "REELS_SCRIPT") or "Script generation failed."
    ig_caption = xtag(raw_data, "IG_CAPTION") or f"{hook_text}\n\nLink in bio for the full breakdown. #investing #finance #stocks"
    smart_comment = xtag(raw_data, "SMART_COMMENT") or "Interesting market shift. Just published a full breakdown on this."

    data_points = []
    for i in range(1, 6):
        item = xtag(raw_data, f"ITEM{i}")
        if item and "|" in item:
            parts = item.split("|")
            raw_ticker = parts[0].strip()
            if len(raw_ticker) > 10: raw_ticker = raw_ticker[:8] + ".."
            data_points.append({"ticker": raw_ticker, "val": parts[1].strip()})

    if len(data_points) < 5:
        data_points = [
            {"ticker": "$NVDA", "val": "+6.2%"}, {"ticker": "$AAPL", "val": "+5.3%"},
            {"ticker": "$MSFT", "val": "+4.9%"}, {"ticker": "$BTC", "val": "+4.2%"},
            {"ticker": "$ETH", "val": "+2.3%"}
        ]

    W, H = 1080, 1920
    BG = "#000000"
    WHITE = "#ffffff"
    GOLD = "#fde047"    # 가독성 및 프리미엄 상징
    RED = "#ef4444"     # 긴급성 및 강조 상징
    GRAY = "#94a3b8"

    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    def lf(p, s):
        try: return ImageFont.truetype(p, s)
        except: return ImageFont.load_default()

    font_title = lf(ft_path, 115)    
    font_huge = lf(ft_path, 220)    
    font_mega = lf(ft_path, 150)    
    font_sub = lf(ft_path, 65)
    font_data = lf(ft_path, 60)
    font_alert = lf(ft_path, 90)

    vp_base = "A cute, friendly, extremely simple 3D white robot mascot with a smooth round head and simple smiling eyes. Pixar animation style. Clean dark minimalist studio background. Soft cinematic lighting. No text, no letters."
    vp1 = vp_base + f" The cute robot is looking surprised, putting its hands on its cheeks in shock. {cat} theme."
    vp2 = vp_base + f" The cute robot is holding a glowing magnifying glass, looking closely at a floating digital chart."
    vp3 = vp_base + f" The cute robot is confidently pointing forward and giving a thumbs up, with a bright glowing aura."

    def fetch_friendly_image(prompt_text, seed):
        try:
            res = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt_text,
                config=types.GenerateImagesConfig(
                    number_of_images=1, aspect_ratio="1:1", output_mime_type="image/jpeg"
                )
            )
            img_bytes = res.generated_images[0].image.image_bytes
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        except Exception as e:
            print(f"    ⚠️ Gemini failed, trying Pollinations: {e}")
            try:
                prompt_encoded = urllib.parse.quote(prompt_text)
                url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1080&height=1080&nologo=true&seed={seed}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    img = Image.open(io.BytesIO(response.read())).convert("RGBA")
            except Exception as e2:
                print(f"    ⚠️ Pollinations failed: {e2}")
                return None
        
        img = img.resize((1080, 1080), Image.LANCZOS)
        mask = Image.new("L", (1080, 1080), 255)
        mask_draw = ImageDraw.Draw(mask)
        for y in range(700, 1080):
            alpha = int(255 - (y - 700) * (255 / 380))
            mask_draw.line([(0, y), (1080, y)], fill=alpha)
        img.putalpha(mask)
        return img

    print("    [AI] Requesting 3 UNIQUE Friendly Character images (Sequential)...")
    img_hook_ai = fetch_friendly_image(vp1, random.randint(1, 100000))
    time.sleep(2)
    img_stat_ai = fetch_friendly_image(vp2, random.randint(1, 100000))
    time.sleep(2)
    img_out_ai  = fetch_friendly_image(vp3, random.randint(1, 100000))

    def paste_bg(d_img, target_ai_img):
        if target_ai_img:
            d_img.paste(target_ai_img, (0, 0), target_ai_img)
        else:
            fallback_img = Image.new("RGBA", (1080, 1080), "#09090b")
            d = ImageDraw.Draw(fallback_img)
            d.ellipse([440, 250, 640, 450], fill="#f8fafc") 
            d.rounded_rectangle([460, 470, 620, 750], radius=40, fill="#f8fafc") 
            mask = Image.new("L", (1080, 1080), 255)
            mask_draw = ImageDraw.Draw(mask)
            for y in range(700, 1080):
                alpha = int(255 - (y - 700) * (255 / 380))
                mask_draw.line([(0, y), (1080, y)], fill=alpha)
            fallback_img.putalpha(mask)
            d_img.paste(fallback_img, (0, 0), fallback_img)

    def wrap_lines(text, font, max_width):
        words = text.split()
        lines, line = [], []
        d = ImageDraw.Draw(Image.new("RGB", (1,1)))
        for ww in words:
            test_str = " ".join(line + [ww])
            try: tw = d.textlength(test_str, font=font)
            except: tw = len(test_str) * 40  
            if tw < max_width: line.append(ww)
            else:
                if line: lines.append(" ".join(line))
                line = [ww]
        if line: lines.append(" ".join(line))
        return lines

    # --- Slide 1 (Hook) ---
    img1 = Image.new("RGB", (W, H), BG)
    paste_bg(img1, img_hook_ai)
    d1 = ImageDraw.Draw(img1)
    
    # 🚨 상단 경고 배지: 긴급성을 위한 RED
    d1.rounded_rectangle([300, 1100, 780, 1200], radius=20, fill=RED) 
    d1.text((W//2, 1150), f"🚨 {cat.upper()} ALERT", fill=WHITE, font=font_alert, anchor="mm")
    
    # 💡 훅 텍스트: 마지막 줄만 시선 집중을 위해 GOLD 강조
    hook_lines = wrap_lines(hook_text.upper(), font_title, 850) 
    y_text = 1330
    for i, ln in enumerate(hook_lines[:4]):
        color = GOLD if i == len(hook_lines[:4])-1 else WHITE
        d1.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 120 
    d1.text((W//2, 1800), "↓ SWIPE TO SEE WHY ↓", fill=GRAY, font=font_sub, anchor="mm")

    # --- Slide 2 (Shock Stat) ---
    img2 = Image.new("RGB", (W, H), BG)
    paste_bg(img2, img_stat_ai)
    d2 = ImageDraw.Draw(img2)
    
    # 💡 소제목: 고급스러운 GOLD
    d2.text((W//2, 1150), "THE NUMBER", fill=GOLD, font=font_sub, anchor="mm")
    
    # 🚨 충격 수치: 마지막 줄만 충격 효과를 위해 RED 강조
    shock_lines = wrap_lines(shock_stat.upper(), font_mega, 850)
    y_text = 1350
    for i, ln in enumerate(shock_lines[:3]):
        color = RED if i == len(shock_lines[:3])-1 else WHITE
        d2.text((W//2, y_text), ln, fill=color, font=font_mega, anchor="mm")
        y_text += 160 
    d2.text((W//2, 1800), "WAIT FOR IT...", fill=GRAY, font=font_sub, anchor="mm")

    # --- Slides 3~5 (Data Points) ---
    data_imgs = []
    for idx in range(3):
        if idx >= len(data_points): break
        item = data_points[idx]
        img_d = Image.new("RGB", (W, H), BG)
        paste_bg(img_d, img_stat_ai)
        d = ImageDraw.Draw(img_d)
        
        # 🚨 카테고리 알림: RED
        d.text((W//2, 1100), cat.upper(), fill=RED, font=font_sub, anchor="mm")
        d.text((W//2, 1200), f"WATCH THIS → {idx+1}/3", fill=GRAY, font=font_data, anchor="mm")
        d.text((W//2, 1380), item['ticker'], fill=WHITE, font=font_title, anchor="mm")
        
        # 💡 지표 컬러: 하락(-)이면 RED, 상승/중립이면 GOLD
        val_str = item['val']
        val_color = RED if '-' in val_str else GOLD
        
        current_huge_size = 220
        if len(val_str) > 6: current_huge_size = int(220 * (6 / len(val_str)))
        current_font_huge = lf(ft_path, max(100, current_huge_size))
        
        d.text((W//2, 1550), val_str, fill=val_color, font=current_font_huge, anchor="mm")
        
        # 💡 페이지 도트: 활성화된 페이지는 GOLD
        dot_y = 1800
        for di in range(3):
            dx = W//2 + (di - 1) * 60
            color = GOLD if di == idx else "#3f3f46"
            d.ellipse([dx-15, dot_y-15, dx+15, dot_y+15], fill=color)
        data_imgs.append(img_d)

    # --- Slide 6 (Takeaway) ---
    img6 = Image.new("RGB", (W, H), BG)
    paste_bg(img6, img_out_ai)
    d6 = ImageDraw.Draw(img6)
    
    # 💡 결론 소제목: GOLD
    d6.text((W//2, 1100), "THE TAKEAWAY", fill=GOLD, font=font_sub, anchor="mm")
    
    # 💡 핵심 문장: 마지막 줄 GOLD 강조
    insight_lines = wrap_lines(insight_line.upper(), font_title, 850)
    y_text = 1250
    for i, ln in enumerate(insight_lines[:3]):
        color = GOLD if i == len(insight_lines[:3])-1 else WHITE
        d6.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 120
        
    # 🚨 마지막 행동 촉구(CTA): 가장 강력한 RED
    d6.text((W//2, 1650), cta_hook.upper(), fill=RED, font=font_alert, anchor="mm")
    d6.text((W//2, 1780), "LINK IN BIO → @WARMINSIGHT", fill=GRAY, font=font_sub, anchor="mm")

    image_bytes_list = []
    all_frames = [img1, img2] + data_imgs + [img6]
    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, all_frames)

    return image_bytes_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes

def _upload_image(img_bytes, filename):
    try:
        resp = scraper.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"}, 
            data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30
        )
        if resp.status_code in (200, 201): return resp.json().get("id")
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, author_name, raw_for_cards=None, med_img_bytes=None):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat)

    insight_cat_id = None
    if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
        insight_cat_id = get_or_create_wp_category("Insight")

    if tier == "unified": tag_id = get_or_create_wp_tag("Insight")
    elif tier == "vip": tag_id = get_or_create_wp_tag("VIP")
    else: tag_id = get_or_create_wp_tag("Pro")

    author_id = get_wp_author_id(author_name)
    display_title = title if cat in ["Foundation", "The Daily Catalyst", "Money Hack"] or tier == "unified" else (f"[VIP] {title}" if tier == "vip" else f"[Pro] {title}")

    post_data = {
        "title": display_title,
        "content": html,
        "status": "publish",
        "slug": slug,
    }

    if author_id: post_data["author"] = author_id
    if media_id: post_data["featured_media"] = media_id

    cats = []
    if cat_id: cats.append(cat_id)
    if insight_cat_id: cats.append(insight_cat_id)

    if cats: post_data["categories"] = cats
    if tag_id: post_data["tags"] = [tag_id]

    seo_title = _clean_seo_title(title)
    rm_title = seo_title if len(seo_title) > 50 else f"{seo_title} | Warm Insight"

    post_data["meta"] = {
        "rank_math_title": rm_title[:60],
        "rank_math_description": (exc or "")[:160],
        "rank_math_focus_keyword": kw.lower() if kw else "",
        "is_premium": "no" if cat in ["Foundation", "Money Hack"] else "yes",
        "pms_content_restrict": "0" if cat in ["Foundation", "Money Hack"] else "1",
        "post_tier": tier.upper(),
    }

    try:
        r = scraper.post(
            f"{WP_URL}/wp-json/wp/v2/posts",
            json=post_data, auth=(WP_USER, WP_APP_PASS), timeout=30
        )
        if r.status_code in (200, 201):
            try:
                resp_json = r.json()
                link = resp_json.get('link') if isinstance(resp_json, dict) else None
            except: link = None
            
            if link:
                print(f"   ✅ Published: {link}")
                
                if raw_for_cards:
                    if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
                        if tier == "vip" or tier == "unified":
                            img_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes = generate_vip_carousel(raw_for_cards, cat)
                            if video_mp4_bytes:
                                send_social_style_email(display_title, link, img_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes)
                        
                        yt_meta, yt_script = generate_youtube_masterpiece(raw_for_cards, title)
                        if yt_script: send_youtube_script_email(title, yt_meta, yt_script)

                send_medium_draft_email(display_title, link, raw_for_cards, cat, kw, med_img_bytes)
                send_community_viral_email(display_title, link, raw_for_cards, cat)
                
                return True
            else:
                print(f"   ❌ [WAF Block Detected] Server returned 200 but no link was created.")
                return False
        else:
            print(f"   ❌ Publish failed. HTTP Status: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Network error: {e}")
    return False

def run_foundation_pipeline():
    cat = "Foundation"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 SEO Foundation Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    theme = random.choice(FOUNDATION_TOPICS)
    tier = "premium"
    raw = gem_fb(tier, FOUNDATION_PROMPT.replace("{theme}", theme), FOUNDATION_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Education Team")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_foundation_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return
            
        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_philosophy_pipeline():
    cat = "The Daily Catalyst"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 Catalyst Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    theme = random.choice(PHILOSOPHY_TOPICS)
    tier = "premium"
    raw = gem_fb(tier, PHILOSOPHY_PROMPT.replace("{theme}", theme), PHILOSOPHY_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Philosophical Desk")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_philosophy_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return

        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_moneyhack_pipeline():
    cat = "Money Hack"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.60 Money Hack Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if force: print(f"   ⚡ [TEST MODE] FORCE_PUBLISH=true")
    elif already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    niche = random.choice(MH_NICHES)
    platform = random.choice(MH_PLATFORMS)
    ai_tool = random.choice(MH_AI_TOOLS)
    theme = f"Niche: {niche} | Core Platform: {platform} | AI Automation Tool: {ai_tool}"
    print(f"   🎲 Random Framework Selected: {theme}")

    tier = "premium"
    raw = gem_fb(tier, MONEY_HACK_PROMPT.replace("{theme}", theme), MONEY_HACK_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        author = VIP_AUTHORS.get(cat, "Warm Insight Growth Team")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_money_hack_html(raw, author, tf, title, cat)
        img_bytes = make_thumbnail(title, cat, tier)
        if not img_bytes or len(img_bytes) < 1000:
            print(f"   ❌ Thumbnail error. Aborting.")
            return

        med_img_bytes = make_medium_thumbnail(cat)
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

def run_news_pipeline(forced_cat=None):
    current_time = datetime.datetime.utcnow()
    day_of_week = current_time.weekday()
    day_of_year = current_time.timetuple().tm_yday
    
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"

    if forced_cat:
        cat = forced_cat
        print(f"🎯 [Command Override] Forcing category to: {cat}")
    elif day_of_week in (1, 3):
        cat = "On-Chain"
        print(f"📅 [Smart Schedule] Today is Tue/Thu. Locking category to: {cat}")
    else:
        base_cats = [c for c in CATEGORIES if c not in ["On-Chain", "Money Hack"]]
        cat = base_cats[day_of_year % len(base_cats)]

    if force:
        print(f"🚀 Starting v46.9.60 Unified News Pipeline | TEST MODE (Force Publish)")
    else:
        print(f"🚀 Starting v46.9.60 Unified News Pipeline | Category: {cat}")

    if not check_env_vars() or not verify_wp_credentials(): return

    if force:
        if forced_cat:
            pass
        else:
            latest_cat = _get_latest_post_category_name()
            available_cats = [c for c in CATEGORIES if c not in [latest_cat, "Money Hack"]]
            if not available_cats: available_cats = [c for c in CATEGORIES if c != "Money Hack"]
            
            random.shuffle(available_cats)
            cat = available_cats[0]
            for fallback_cat in available_cats:
                if not already_published_today(fallback_cat):
                    cat = fallback_cat
                    break
            print(f"   ⚡ [TEST MODE] Forcing random category '{cat}' avoiding '{latest_cat}'.")
    else:
        if already_published_today(cat):
            print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
            return

    all_news = fetch_news_pool(cat)
    total_news = len(all_news)
    if total_news < 2:
        print(f"   ❌ Not enough news for {cat} ({total_news}). Aborting.")
        return

    news_str = "\n".join(all_news)
    tier = "unified"

    raw1 = gem_fb(tier, PROMPT_UNIFIED_P1.replace("{cat}", cat).replace("{news}", news_str))
    if not raw1:
        print("   ❌ Part 1 generation failed.")
        return

    ctx = "Title: " + xtag(raw1, "TITLE") + "\nSummary: " + xtag(raw1, "EXECUTIVE_SUMMARY")
    raw2 = gem_fb(tier, PROMPT_UNIFIED_P2.replace("{cat}", cat).replace("{ctx}", ctx))
    if not raw2:
        print("   ⚠️ Part 2 failed. Using Part 1 only.")
        raw = raw1
    else:
        raw = raw1 + "\n" + raw2

    title = xtag(raw, "TITLE")
    kw = xtag(raw, "SEO_KEYWORD")
    exc = xtag(raw, "EXCERPT") or xtag(raw, "EXECUTIVE_SUMMARY")
    slug = make_slug(kw, title, cat)
    author = VIP_AUTHORS.get(cat, "Warm Insight Editorial Team")
    tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
    
    html = build_html(tier, cat, raw, author, tf, title)

    img_bytes = make_thumbnail(title, cat, tier)
    if not img_bytes or len(img_bytes) < 1000:
        print(f"   ❌ Thumbnail error. Aborting.")
        return
        
    med_img_bytes = make_medium_thumbnail(cat)

    publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)
    time.sleep(TIER_SLEEP[tier])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "philosophy": 
            run_philosophy_pipeline()
        elif arg == "foundation": 
            run_foundation_pipeline()
        elif arg == "moneyhack":
            run_moneyhack_pipeline()
        elif arg == "onchain": 
            run_news_pipeline("On-Chain")
        elif arg == "insight":
            current_time = datetime.datetime.utcnow()
            day_of_year = current_time.timetuple().tm_yday
            base_cats = [c for c in CATEGORIES if c not in ["On-Chain", "Money Hack"]]
            cat = base_cats[day_of_year % len(base_cats)]
            run_news_pipeline(cat)
    else:
        run_news_pipeline()
