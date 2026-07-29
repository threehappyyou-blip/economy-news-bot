#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — Ultimate Masterpiece Edition (v46.9.52_FIXED)
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
    "Economy": ["https://feeds.reuters.com/reuters/businessNews", "https://finance.yahoo.com/news/rssindex", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"],
    "Politics": ["https://feeds.reuters.com/Reuters/PoliticsNews", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113", "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"],
    "Tech": ["https://feeds.reuters.com/reuters/technologyNews", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910", "https://techcrunch.com/feed/"],
    "Health": ["https://feeds.reuters.com/reuters/healthNews", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108", "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml"],
    "Energy": ["https://oilprice.com/rss/main", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810", "https://feeds.reuters.com/reuters/environment"],
    "On-Chain": ["https://cointelegraph.com/rss", "https://www.coindesk.com/arc/outboundfeeds/rss/", "https://cryptoslate.com/feed/"],
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
# 🧠 프롬프트 설정
# ═══════════════════════════════════════════════
PROMPT_UNIFIED_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are Warm Insight's lead writer. Your mission: turn daily market chaos into clarity for everyday people — BUT with insights they couldn't get from a Reuters headline. Write entirely in ENGLISH.

═══ 🔥 EXTREME ANTI-CLICHÉ & ZERO-FLUFF RULES (CRITICAL) ═══
BANNED CONTENT (NEVER WRITE THESE):
- "AI is still the boss" / "AI is here to stay" / "AI revolution"
- "Delve into", "Unleash", "Game-changer", "In today's fast-paced world"

REQUIRED CONTENT (MUST INCLUDE):
- ONE counterintuitive (반직관적) insight that 80% of readers don't know.
- AT LEAST 3 specific numbers (percentages, dollar amounts, dates).
- AT LEAST 1 specific company decision/move.

Write PART 1 of an Insight newsletter on {cat} in ENGLISH. Target length: 900-1100 words across both parts combined.
News Context:
{news}

OUTPUT FORMAT REQUIREMENT:
You MUST wrap your content EXACTLY in the XML tags listed below.
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it clickbait for Google searchers.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words, low competition.)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the exact SEO_KEYWORD. Write a 'curiosity gap' summary.)</EXCERPT>
<WARM_INDEX_SCORE>(A number from 0 to 100 representing market fear/greed based on this news. Output ONLY the integer.)</WARM_INDEX_SCORE>
<WARM_INDEX_REASON>(A punchy 5-10 word explanation for this score.)</WARM_INDEX_REASON>
<IMPACT>(Write HIGH, MEDIUM, or LOW here)</IMPACT>
<DATA_TABLE>
(REQUIRED — extract OR estimate 3-4 key market metrics. Format exactly: Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight under 12 words)
</DATA_TABLE>
<HEATMAP>
(Invent 3-4 sector risk levels 0-100% based on news. Format exactly: Sector Name | Number)
</HEATMAP>
<EXECUTIVE_SUMMARY>(3 sentences capturing your COUNTERINTUITIVE thesis. Each MAX 15 words. Start with "OK so..." or "Here's what's wild:" Use 1 emoji.)</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>(3-4 sentences with your ONE specific analogy. Make it vivid. 20+ words developed.)</PLAIN_ENGLISH>
<HEADLINE>(Analytical headline for drivers section. Include emoji if fits. Sound like inside intel.)</HEADLINE>
<MACRO>(Write 2 PARAGRAPHS. Each paragraph MAX 2 sentences, each sentence MAX 14 words.
PARAGRAPH 1: What's happening — ONE specific number or data point.
PARAGRAPH 2: WHY it's happening — the cause most people miss. End with your honest one-line take.)</MACRO>
<HERD>(Write 1 paragraph showing what retail/average investors are doing wrong RIGHT NOW. MAX 3 sentences. Be specific.)</HERD>
<CONTRARIAN>(Write 1 paragraph showing what smart money is doing differently. MAX 3 sentences. Be specific with ticker AND institution.)</CONTRARIAN>
<QUICK_FLOW>(Chain of events with arrows ➡️ 5-6 steps. Each step under 8 words.)</QUICK_FLOW>"""

PROMPT_UNIFIED_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are Warm Insight's lead writer continuing the analysis in ENGLISH. Same friendly + smart tone as Part 1.

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

FOUNDATION_TOPICS = ["ETF vs Mutual Funds: Which is actually safer for absolute beginners?", "How to start investing in S&P 500 ETFs with exactly $100", "The hidden risks of Dollar Cost Averaging (DCA) you must know"]
FOUNDATION_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN. You are the "smart friend" who explains money to absolute beginners. Use counterintuitive angles. Wrap your content EXACTLY in the XML tags requested."""
FOUNDATION_PROMPT = """Write an SEO-optimized beginner's guide on the following topic in English: TOPIC: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it clickbait for Google searchers: use brackets, odd numbers, or 'How to' formats.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words, low competition.)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Write a 'Curiosity Gap' meta description.)</EXCERPT>
<DEFINITION>(Provide a simple, 2-paragraph definition using an UNEXPECTED everyday analogy.)</DEFINITION>
<WHY_MATTERS>(Explain in 2 paragraphs why a beginner should care. Use concrete dollar amounts or percentages.)</WHY_MATTERS>
<HOW_TO_START>(Provide 3 simple, ACTIONABLE steps for a beginner to start using this concept today. Format as a bulleted list.)</HOW_TO_START>
<POLL_QUESTION>(A provocative multiple-choice question related to this topic.)</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>"""

PHILOSOPHY_TOPICS = ["Love money through action, not just unrequited longing", "The psychological vessel of wealth and the weight of responsibility", "Voluntary fatigue: The pleasurable pain of chosen growth"]
PHILOSOPHY_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN. You are an elite philosophical life strategist. Be harsh, direct, and unapologetic. Wrap your content EXACTLY in the XML tags requested."""
PHILOSOPHY_PROMPT = """Write a philosophical daily insight based on the following theme in English: THEME: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words.)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Write a 'Curiosity Gap' meta description.)</EXCERPT>
<ANCHOR>(A one-sentence philosophical principle based on the theme.)</ANCHOR>
<REFLECTION>(3-4 paragraphs explaining how this principle connects to modern reality. Criticize passive excuses heavily.)</REFLECTION>
<CATALYST>(A single, highly provocative and specific question that requires the reader to write down an actionable answer immediately.)</CATALYST>
<POLL_QUESTION>(A provocative multiple-choice question related to this topic.)</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>"""

MH_NICHES = ["Digital Products & Templates", "E-commerce & Dropshipping", "Freelancing & Agency", "Micro-SaaS & Software", "Affiliate Marketing"]
MH_PLATFORMS = ["Gumroad", "Shopify", "Canva", "Notion", "Fiverr", "Upwork", "YouTube", "TikTok", "Substack"]
MH_AI_TOOLS = ["ChatGPT", "Midjourney", "Claude", "ElevenLabs", "Zapier/Make", "CapCut AI", "HeyGen"]

MONEY_HACK_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN. You are an elite side-hustle expert and digital business coach. Wrap your content EXACTLY in the XML tags requested."""
MONEY_HACK_PROMPT = """Write an SEO-optimized, step-by-step side hustle guide based on this framework: FRAMEWORK: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it clickbait.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words, low competition.)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Write a 'Curiosity Gap' meta description.)</EXCERPT>
<CONCEPT>(2 paragraphs explaining what this specific side hustle is and why it's profitable right now. Mention real market demand.)</CONCEPT>
<STEP_BY_STEP_TOOL>(Detail the specific platforms or tools from the framework and provide a clear 1-2-3 checklist to execute today. Give exact instructions, not vague advice.)</STEP_BY_STEP_TOOL>
<PRO_TIP>(1 paragraph revealing a secret tip that top 1% earners use in this hustle to save time or double profits. Must be a counterintuitive hack.)</PRO_TIP>
<POLL_QUESTION>(A provocative multiple-choice question related to starting this side hustle.)</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>"""

# ═══════════════════════════════════════════════
# 🎬 1. YOUTUBE CHAPTERING ENGINE
# ═══════════════════════════════════════════════
YT_META_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Based on the following newsletter content, generate a YouTube Metadata package in ENGLISH.
<METADATA>
[VIRAL TITLES]
- Option A: 
- Option B: 
- Option C: 
[THUMBNAIL IDEAS]
1. Visual Prompt: (Generate a HYPER-DETAILED, professional AI image generation prompt for Midjourney/Vrew. NO TEXT IN PROMPT.)
2. Text/Copy: (Write 2-4 words of MASSIVE IMPACT, click-inducing text to place directly ON the thumbnail.)
[SEO HASHTAGS]
(10 highly searched global tags, e.g. #investing #economy)
</METADATA>"""

YT_SCRIPT_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are a top-tier YouTube Scriptwriter for "Warm Insight". Write PART 1 of a massive documentary script based on the newsletter in ENGLISH.
[NEWSLETTER]
{raw_content}
Rules: OUTPUT ONLY SPOKEN WORDS IN ENGLISH. NO structural tags. Wrap in <PART1> tags."""

YT_SCRIPT_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Continue the English script from Part 1 seamlessly. Write PART 2: Chapter 2 & 3 (Historical Context & Deep Dive).
Rules: Spoken words ONLY in English. NO structural tags. Wrap in <PART2> tags."""

YT_SCRIPT_P3 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Complete the English script. Write PART 3: Chapter 4 & Outro (Future Prediction & Action Plan).
Rules: Spoken words ONLY in English. NO structural tags. Wrap in <PART3> tags."""

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
        sec1_title, sec1_body = "📖 What is it?", xtag(raw_content, "DEFINITION").replace('\n', '<br>')
        sec2_title, sec2_body = "💡 Why It Matters", xtag(raw_content, "WHY_MATTERS").replace('\n', '<br>')
        sec3_title, sec3_body = "🚀 How to Start Today", xtag(raw_content, "HOW_TO_START").replace('\n', '<br>')
    elif cat == "The Daily Catalyst":
        sec1_title, sec1_body = "❝ The Anchor ❞", xtag(raw_content, "ANCHOR").replace('\n', '<br>')
        sec2_title, sec2_body = "The Reflection", xtag(raw_content, "REFLECTION").replace('\n', '<br>')
        sec3_title, sec3_body = "⚡ The Daily Catalyst", xtag(raw_content, "CATALYST").replace('\n', '<br>')
    elif cat == "Money Hack":
        sec1_title, sec1_body = "💡 The Concept", xtag(raw_content, "CONCEPT").replace('\n', '<br>')
        sec2_title, sec2_body = "🛠️ Step-by-Step Execution", xtag(raw_content, "STEP_BY_STEP_TOOL").replace('\n', '<br>')
        sec3_title, sec3_body = "🔥 Pro Tip", xtag(raw_content, "PRO_TIP").replace('\n', '<br>')
    else:
        sec1_title, sec1_body = "Executive Summary", xtag(raw_content, "EXECUTIVE_SUMMARY").replace('\n', '<br>')
        sec2_title, sec2_body = "💡 Plain English", xtag(raw_content, "PLAIN_ENGLISH").replace('\n', '<br>')
        sec3_title, sec3_body = xtag(raw_content, "HEADLINE"), xtag(raw_content, "MACRO").replace("PARAGRAPH 1:", "").replace("PARAGRAPH 2:", "").replace("PARAGRAPH 3:", "").strip().replace('\n', '<br><br>')
    
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
                        <h1>{title}</h1><br>
                        <h2>{sec1_title}</h2><p>{sec1_body}</p><br>
                        <h2>{sec2_title}</h2><p>{sec2_body}</p><br>
                        <h2>{sec3_title}</h2><p>{sec3_body}</p><br>
                        <hr><br>
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

# ═══════════════════════════════════════════════
# ✉️ 슬림 이메일 (인스타/숏폼용) -> 🚨 1-Min Reels 대본 삭제 완료
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
                <p style="color: #10b981; font-weight: 900; font-size: 18px; margin-top: 0; text-transform: uppercase;">🎬 15-Sec Dark Psychology Reels Attached!</p>
                <div style="font-size: 45px; margin: 15px 0;">✨ 📹 ✨</div>
                <p style="color: #ffffff; font-size: 15px; font-weight: bold; margin: 5px 0;">100% Compatible with IG Reels / TikTok / YT Shorts.</p>
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0; margin-top: 10px;">Download <strong>WarmInsight_{cat}_Video.mp4</strong> attached below.</p>
            </div>
            """

        body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f4f4f5; padding: 20px; color: #0f1419;">
            {vid_tag}
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
            print(f"   💬 Server Response: {resp.text[:250]}")
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
            print(f"    ⚠️ [Gemini API Error] {err}")
            if "credits are depleted" in err or "billing" in err.lower():
                print("    🚨 Credits depleted!")
                return None
            if "404" in err or "not found" in err.lower(): return None
            if "503" in err or "UNAVAILABLE" in err:
                wait = (15 * i) + random.uniform(-2, 5)
                print(f"    ⏳ 503 Overload. Jitter Wait {wait:.1f}s...")
                time.sleep(wait)
            elif "429" in err:
                print(f"    ⏳ 429 Quota Exceeded. Waiting...")
                time.sleep(30 + random.uniform(0, 10))
            elif i < retries: time.sleep(5 * i)
    return None

def gem_fb(tier, prompt, sys_inst=None):
    client = _get_gemini_client()
    for m in MODEL_PRI.get(tier, FAST_MODELS):
        print(f"    [AI] Trying {m}...")
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
                            if name in CATEGORIES:
                                return name
    except Exception as e:
        print(f"   ⚠️ Failed to get latest category: {e}")
    return None

def already_published_today(cat):
    try:
        cat_slug = cat.lower().replace(" ", "-")
        r = scraper.get(
            f"{WP_URL}/wp-json/wp/v2/categories?slug={cat_slug}", headers=WP_API_HEADERS,
            auth=(WP_USER, WP_APP_PASS), timeout=15
        )
        if r.status_code != 200: return False
        
        try:
            r_json = r.json()
            if not isinstance(r_json, list) or not r_json: return False
            cat_id = r_json[0]["id"]
        except: return False

        r2 = scraper.get(
            f"{WP_URL}/wp-json/wp/v2/posts", headers=WP_API_HEADERS,
            params={
                "categories": cat_id,
                "per_page": 1,
                "status": "publish"
            },
            auth=(WP_USER, WP_APP_PASS), timeout=15
        )
        if r2.status_code == 200:
            try:
                r2_json = r2.json()
                if isinstance(r2_json, list) and len(r2_json) > 0:
                    latest_post = r2_json[0]
                    post_date_gmt = latest_post.get("date_gmt", "")[:10] 
                    today_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d")
                    if post_date_gmt == today_utc:
                        print(f"   ⏭️  [{cat}] Anti-spam logic: Already published today. ({latest_post.get('link')})")
                        return True
            except: pass
    except Exception as e:
        print(f"   ⚠️ already_published_today check failed: {e}")
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

def _build_warm_index(raw_data):
    score_str = xtag(raw_data, "WARM_INDEX_SCORE")
    reason = xtag(raw_data, "WARM_INDEX_REASON")
    if not score_str: return ""
    try: score = int(re.sub(r'[^0-9]', '', score_str))
    except: return ""
    score = max(0, min(100, score))
    if score < 30: c_main, label, icon, grad = "#3b82f6", "Fear Zone", "❄️", "linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%)"
    elif score > 70: c_main, label, icon, grad = "#ef4444", "Greed Zone", "🔥", "linear-gradient(90deg, #b91c1c 0%, #ef4444 100%)"
    else: c_main, label, icon, grad = "#f59e0b", "Neutral", "⚖️", "linear-gradient(90deg, #b45309 0%, #f59e0b 100%)"
    return f"""
    <div style="background:#ffffff; border:2px solid {BORDER}; border-radius:12px; padding:25px; margin:0 0 35px 0; box-shadow:0 4px 6px rgba(0,0,0,0.02);">
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:12px;">
            <div>
                <span style="font-size:13px; font-weight:800; color:{MUTED}; text-transform:uppercase; letter-spacing:1px;">Today's Warm Index</span>
                <div style="font-size:20px; font-weight:800; color:{DARK}; margin-top:4px;">{icon} {label}</div>
            </div>
            <div style="text-align:right;">
                <span style="font-size:32px; font-weight:900; color:{c_main}; line-height:1;">{score}</span>
                <span style="font-size:14px; color:{MUTED}; font-weight:600;">/ 100</span>
            </div>
        </div>
        <div style="background:#e2e8f0; height:10px; border-radius:5px; overflow:hidden; position:relative; margin-bottom:12px;">
            <div style="background:{grad}; height:100%; width:{score}%; border-radius:5px; transition:width 1s ease-in-out;"></div>
        </div>
        <p style="margin:0; font-size:14px; color:{SLATE}; font-style:italic; text-align:center;">"{reason}"</p>
    </div>
    """

def _build_poll(raw_data, cat="Market"):
    question = xtag(raw_data, "POLL_QUESTION").strip() or f"What is your perspective on today's {cat} news?"
    opt1 = xtag(raw_data, "POLL_OPT1").strip() or "Bullish – I see an opportunity."
    opt2 = xtag(raw_data, "POLL_OPT2").strip() or "Neutral – Waiting for more signals."
    opt3 = xtag(raw_data, "POLL_OPT3").strip() or "Bearish – Taking a cautious stance."
    opt3_html = f"""<a href="#respond" style="display:block; background:#ffffff; border:2px solid {BORDER}; color:{DARK}; padding:14px; border-radius:8px; text-decoration:none; font-weight:700; font-size:16px; transition:all 0.2s;" onmouseover="this.style.borderColor='{GOLD}'; this.style.backgroundColor='#fefce8';" onmouseout="this.style.borderColor='{BORDER}'; this.style.backgroundColor='#ffffff';">{opt3}</a>""" if opt3 else ""
    return f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:12px; padding:30px; margin:50px 0; text-align:center;">
        <h3 style="margin-top:0; font-size:22px; color:{DARK}; margin-bottom:20px;">🗳️ What's your take?</h3>
        <p style="font-size:18px; font-weight:600; color:{SLATE}; margin-bottom:25px;">"{question}"</p>
        <div style="display:flex; flex-direction:column; gap:12px; max-width:400px; margin:0 auto;">
            <a href="#respond" style="display:block; background:#ffffff; border:2px solid {BORDER}; color:{DARK}; padding:14px; border-radius:8px; text-decoration:none; font-weight:700; font-size:16px; transition:all 0.2s;" onmouseover="this.style.borderColor='{GOLD}'; this.style.backgroundColor='#fefce8';" onmouseout="this.style.borderColor='{BORDER}'; this.style.backgroundColor='#ffffff';">{opt1}</a>
            <a href="#respond" style="display:block; background:#ffffff; border:2px solid {BORDER}; color:{DARK}; padding:14px; border-radius:8px; text-decoration:none; font-weight:700; font-size:16px; transition:all 0.2s;" onmouseover="this.style.borderColor='{GOLD}'; this.style.backgroundColor='#fefce8';" onmouseout="this.style.borderColor='{BORDER}'; this.style.backgroundColor='#ffffff';">{opt2}</a>
            {opt3_html}
        </div>
    </div>
    """

def _build_data_table(raw_data, title="Market Dashboard"):
    if not raw_data: raw_data = "S&P 500 | 5,234 | UP | Index near recent highs"
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if len(lines) < 2: lines = lines + ["S&P 500 | 5,234 | UP | Index near recent highs", "Nasdaq 100 | 18,200 | UP | Tech leading the broader market"][:max(2, 3 - len(lines))]
    html = f"""
    <div style="background:#ffffff; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; font-size:20px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:12px; display:inline-block;">📊 {title}</h3>
        <div style="overflow-x:auto; margin-top:15px;">
        <table style="width:100%; border-collapse:collapse; font-family:-apple-system,sans-serif;">
            <thead><tr style="background:{BG_LIGHT}; text-align:left; border-bottom:2px solid {BORDER};">
                <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px; white-space:nowrap;">Asset/Metric</th>
                <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px; white-space:nowrap;">Status</th>
                <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px; white-space:nowrap;">Trend</th>
                <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Key Insight</th>
            </tr></thead><tbody>
    """
    for line in lines[:5]:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            asset, value, trend, insight = parts[:4]
            t_upper = trend.upper()
            if "UP" in t_upper or "BULL" in t_upper or "HIGH" in t_upper: t_color, t_icon = "#10b981", "🟢"
            elif "DOWN" in t_upper or "BEAR" in t_upper or "LOW" in t_upper: t_color, t_icon = "#ef4444", "🔴"
            else: t_color, t_icon = "#f59e0b", "🟡"
            html += f"""<tr style="border-bottom:1px solid {BORDER};"><td style="padding:14px; font-weight:600; color:{DARK};">{asset}</td><td style="padding:14px; color:{SLATE}; font-family:monospace; font-size:15px; font-weight:bold;">{value}</td><td style="padding:14px; font-weight:bold; color:{t_color};">{t_icon} {trend.upper()}</td><td style="padding:14px; color:{MUTED}; font-size:15px; line-height:1.6;">{insight}</td></tr>"""
    html += "</tbody></table></div></div>"
    return html

def _build_progress_bars(raw_data, title="Sector Risk Heatmap"):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""
    html = f"""<div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;"><h3 style="margin-top:0; font-size:20px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:12px;">🌡️ {title}</h3>"""
    colors = ["#dc2626", "#ea580c", "#ca8a04", "#059669", "#3b82f6"]
    for i, line in enumerate(lines[:5]):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:
            name = parts[0]
            try: pct = int(re.sub(r'[^0-9]', '', parts[1]))
            except: pct = 50
            pct = max(0, min(100, pct))
            c = colors[0] if pct > 75 else (colors[1] if pct > 50 else (colors[3] if pct < 30 else colors[2]))
            html += f"""<div style="margin-top:18px;"><div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span style="font-weight:600; font-size:15px; color:{DARK};">{name}</span><span style="font-weight:900; font-size:15px; color:{c};">{pct}%</span></div><div style="background:#e2e8f0; height:12px; border-radius:6px; overflow:hidden;"><div style="background:{c}; height:100%; width:{pct}%; border-radius:6px;"></div></div></div>"""
    html += "</div>"
    return html

def _build_quick_hits(raw_data):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if l.strip()]
    if not lines: return ""
    items_html = ""
    for i, line in enumerate(lines[:3]):
        clean = line.replace("-", "").replace("*", "").strip()
        if clean and clean[0] not in "🚨👀🤔💸📈📉🔥💡🤯": clean = f"{['🚨', '👀', '💸'][i % 3]} {clean}"
        items_html += f"""<li style="margin-bottom:12px; color:{SLATE};">{clean}</li>"""
    return f"""<div style="background:#f1f5f9; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;"><h3 style="margin-top:0; font-size:20px; color:{DARK}; text-transform:uppercase; letter-spacing:1px;">⚡ Quick Hits</h3><ul style="{F} margin:0; padding-left:20px;">{items_html}</ul></div>"""

def _build_pie_chart(s, b, c, cat):
    c_s, c_b, c_c = {"Economy": ("#2563eb", "#60a5fa", "#dbeafe"), "Politics": ("#dc2626", "#f87171", "#fee2e2"), "Tech": ("#7c3aed", "#a78bfa", "#ede9fe"), "Health": ("#059669", "#34d399", "#d1fae5"), "Energy": ("#d97706", "#fbbf24", "#fef3c7"), "On-Chain": ("#8b5cf6", "#a78bfa", "#ede9fe")}.get(cat, ("#b8974d", "#cbd5e1", "#f1f5f9"))
    circ = 565.49
    sd, bd, cd = circ*s/100, circ*b/100, circ*c/100
    pie = f"""<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;"><circle cx="100" cy="100" r="90" fill="none" stroke="{c_s}" stroke-width="30" stroke-dasharray="{sd} {circ}" stroke-dashoffset="0"/><circle cx="100" cy="100" r="90" fill="none" stroke="{c_b}" stroke-width="30" stroke-dasharray="{bd} {circ}" stroke-dashoffset="-{sd}"/><circle cx="100" cy="100" r="90" fill="none" stroke="{c_c}" stroke-width="30" stroke-dasharray="{cd} {circ}" stroke-dashoffset="-{sd+bd}"/><text x="100" y="95" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">{s}/{b}/{c}</text><text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg><div style="display:flex;justify-content:center;gap:20px;"><span style="color:{c_s};font-weight:bold;">● Stocks/Assets {s}%</span><span style="color:{c_b};font-weight:bold;">● Safe {b}%</span><span style="color:{c_c};font-weight:bold;">● Cash {c}%</span></div>"""
    return pie

def _build_pillar_link(target_cat):
    pillar = PILLAR_PAGES.get(target_cat)
    if not pillar: return ""
    return f"""<div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:20px; margin:40px 0; border-radius:4px; box-shadow:0 2px 4px rgba(0,0,0,0.02);"><p style="margin:0; font-size:16px; color:#1e293b;"><strong style="color:#2563eb;">📚 Deep Dive:</strong> Want to master this topic? Check out our complete guide to <a href="{pillar['url']}" style="color:#2563eb; text-decoration:underline; font-weight:700;">{pillar['anchor']}</a>.</p></div>"""

def _build_branded_footer():
    si = ""
    if SOCIAL_LINKS.get("youtube"): si += f"""<a href="{SOCIAL_LINKS["youtube"]}" target="_blank" style="display:inline-block; background:#FF0000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">▶ YouTube</a>"""
    if SOCIAL_LINKS.get("tiktok"): si += f"""<a href="{SOCIAL_LINKS["tiktok"]}" target="_blank" style="display:inline-block; background:#000000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">🎵 TikTok</a>"""
    return f"""<div style="background:{DARK}; padding:35px; border-radius:10px; margin-top:30px;"><p style="font-size:24px; font-weight:bold; color:{GOLD}; margin:0 0 12px; text-align:center;">Warm Insight</p><p style="font-size:14px; color:#94a3b8; text-align:center; margin:0 0 16px;">AI-Driven Global Market Analysis</p><div style="text-align:center; margin-bottom:16px;">{si}</div><div style="text-align:center; margin-bottom:16px; font-size:13px;"><a href="{SITE_URL}/about-us/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">About</a><a href="{SITE_URL}/privacy-policy/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">Privacy</a><a href="{SITE_URL}/terms/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">Terms</a></div><p style="font-size:13px; color:#64748b; margin:0; text-align:center;">All analysis is for informational purposes only. Not financial advice.<br>&copy; {datetime.datetime.utcnow().year} Warm Insight. All rights reserved.</p></div>"""

def _build_founder_note():
    return f"""<div style="background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%); border:2px solid {GOLD}; border-radius:14px; padding:30px; margin:40px 0;"><div style="display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap;"><div style="min-width:70px; height:70px; border-radius:50%; background:{GOLD}; display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:900; color:#fff;">J</div><div style="flex:1; min-width:250px;"><p style="font-size:13px; font-weight:800; color:#92400e; margin:0 0 6px; text-transform:uppercase; letter-spacing:1.5px;">A NOTE FROM THE FOUNDER</p><p style="font-size:18px; font-weight:700; color:{DARK}; margin:0 0 10px; line-height:1.4;">Hey, I'm Jiho. I built Warm Insight because I was tired of finance content being either too dumbed-down or too academic.</p><p style="font-size:15px; color:{SLATE}; margin:0; line-height:1.6;">Every article here is designed to give you ONE thing: a clearer view of your money than you had 5 minutes ago. If it ever stops doing that, tell me directly. I read every reply.</p></div></div></div>"""

def build_foundation_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n{_build_founder_note()}"""
    html += f"""<div style="background:#f0fdf4; border-left:5px solid #10b981; padding:25px; margin:30px 0; border-radius:0 8px 8px 0;"><h3 style="margin-top:0; font-size:22px; color:#065f46;">📖 What is it?</h3><div style="color:#064e3b; font-size:18px; line-height:1.8;">{xtag(raw, "DEFINITION").replace(chr(10), '<br><br>')}</div></div>"""
    html += f"""<div style="margin:40px 0;"><h3 style="font-size:24px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">💡 Why It Matters</h3><p>{xtag(raw, "WHY_MATTERS").replace(chr(10), '<br><br>')}</p></div>"""
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    html += f"""<div style="background:#ffffff; border:2px solid #3b82f6; padding:30px; border-radius:12px; margin:40px 0;"><h3 style="margin-top:0; color:#1e40af; font-size:24px;">🚀 How to Start Today</h3><div style="color:{SLATE}; font-size:18px; line-height:1.8;">{xtag(raw, "HOW_TO_START").replace(chr(10), '<br><br>')}</div></div>"""
    html += _build_pillar_link("Foundation") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p></div>"""
    return sanitize(html)

def build_philosophy_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n{_build_founder_note()}"""
    html += f"""<div style="text-align:center; margin:50px 0;"><span style="font-size:40px; color:{GOLD}; line-height:1;">❝</span><h2 style="font-family:Georgia,serif; font-size:26px; color:{DARK}; margin:10px 0; font-weight:600; line-height:1.4;">{xtag(raw, "ANCHOR")}</h2><span style="font-size:40px; color:{GOLD}; line-height:1;">❞</span></div>"""
    html += f"""<div style="margin:40px 0;"><h3 style="font-size:22px; color:{DARK}; border-left:4px solid {GOLD}; padding-left:12px; margin-bottom:20px;">The Reflection</h3><div style="color:{SLATE}; font-size:18px; line-height:1.8;">{xtag(raw, "REFLECTION").replace(chr(10), '<br><br>')}</div></div>"""
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    html += f"""<div style="background:#fefce8; border:2px solid #fde047; padding:35px; border-radius:12px; margin:50px 0; text-align:center;"><p style="font-size:14px; font-weight:800; color:#b45309; text-transform:uppercase; letter-spacing:2px; margin:0 0 15px;">⚡ The Daily Catalyst</p><p style="font-size:24px; font-weight:900; color:#92400e; margin:0 0 20px; line-height:1.5;">{re.sub(r'<[^>]+>', '', xtag(raw, "CATALYST"))}</p><p style="font-size:15px; color:#b45309; margin:0; font-style:italic;">Don't just read. Take out a pen and write your answer now.</p></div>"""
    html += _build_pillar_link("The Daily Catalyst") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p></div>"""
    return sanitize(html)

def build_money_hack_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n{_build_founder_note()}"""
    html += f"""<div style="margin:40px 0;"><h3 style="font-size:24px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">💡 The Concept</h3><p>{xtag(raw, "CONCEPT").replace(chr(10), '<br><br>')}</p></div>"""
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    html += f"""<div style="background:#f0fdf4; border:2px solid #10b981; padding:30px; border-radius:12px; margin:40px 0;"><h3 style="margin-top:0; color:#065f46; font-size:24px; display:flex; align-items:center; gap:8px;">🛠️ Step-by-Step Execution</h3><div style="color:#064e3b; font-size:17px; line-height:1.8;">{xtag(raw, "STEP_BY_STEP_TOOL").replace(chr(10), '<br><br>')}</div></div>"""
    html += f"""<div style="background:#fffbeb; border-left:5px solid #f59e0b; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;"><p style="margin:0; font-size:18px; font-weight:800; color:#b45309; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">🔥 Pro Tip</p><p style="margin:0; color:#92400e; font-style:italic;">{xtag(raw, "PRO_TIP").replace(chr(10), '<br>')}</p></div>"""
    html += _build_pillar_link("Money Hack") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p></div>"""
    return sanitize(html)

def build_html(tier, cat, raw, author, tf, title):
    html = f"""<div style="{F}">\n{_build_warm_index(raw)}{_build_founder_note()}"""
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; padding-bottom:10px;">Executive Summary</h2>"""
    html += f"""<p style="font-size:19px; font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>"""
    html += f"""<div style="background:#fffbeb; border:2px solid #f59e0b; padding:25px; margin:35px 0; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; color:#b45309; font-size:22px; display:flex; align-items:center; gap:8px;">⚠️ One-Point Action Plan for Beginners</h3>
        <p style="font-size:15px; color:#92400e; margin-top:-10px; margin-bottom:20px;">Today's specific, actionable strategy for absolute beginners</p>
        <div style="background:#ffffff; border-left:5px solid #10b981; padding:20px; border-radius:6px; margin-bottom:15px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
            <p style="margin:0; color:#065f46; font-size:18px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">🟢 DO THIS:</p>
            <p style="margin:8px 0 0; color:#064e3b; font-size:17px; line-height:1.6; font-weight:500;">{xtag(raw, "DO_ACTION").replace(chr(10), '<br>')}</p>
        </div>
        <div style="background:#ffffff; border-left:5px solid #ef4444; padding:20px; border-radius:6px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
            <p style="margin:0; color:#991b1b; font-size:18px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">🔴 AVOID THIS:</p>
            <p style="margin:8px 0 0; color:#7f1d1d; font-size:17px; line-height:1.6; font-weight:500;">{xtag(raw, "DONT_ACTION").replace(chr(10), '<br>')}</p>
        </div>
    </div>"""
    html += _build_data_table(xtag(raw, "DATA_TABLE"), "Market Dashboard")
    html += _build_progress_bars(xtag(raw, "HEATMAP"), "Sector Risk Heatmap")
    html += f"""<div style="background:#faf5ff; border-left:5px solid #8b5cf6; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;">
        <p style="font-size:20px; font-weight:800; color:#4c1d95; margin:0 0 12px;">💡 Plain English</p><p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p>
    </div>"""
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; margin-top:30px;">Market Drivers & Flow</h2>"""
    html += f"""<h3 style="font-size:24px; color:{DARK}; margin-top:20px;">{xtag(raw, "HEADLINE")}</h3>"""
    html += f"""<div style="background:#fff; border:1px solid {BORDER}; border-left:5px solid {GOLD}; padding:30px; border-radius:8px; margin:30px 0;">
        <p><strong>🧐 The Big Picture:</strong> {xtag(raw, "MACRO")}</p><hr><p><strong>🐑 What Most People Are Doing:</strong> {xtag(raw, "HERD")}</p><hr><p><strong>🦅 What Smart Money Is Doing:</strong> {xtag(raw, "CONTRARIAN")}</p>
    </div><div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    html += f"""<div style="background:#fffbeb; border:1px solid #fde68a; border-left:5px solid {AMBER}; padding:25px; margin:40px 0;">
        <strong style="color:#92400e; font-size:20px;">🔗 Chain of Events:</strong><br><span style="font-weight:bold; font-size:19px; color:{DARK}; display:inline-block; margin-top:12px;">{xtag(raw, "QUICK_FLOW")}</span>
    </div>"""
    html += f"""<div style="display:flex; flex-wrap:wrap; gap:20px; margin:40px 0;">
        <div style="flex:1; min-width:250px; background:#ecfdf5; border:2px solid #10b981; border-radius:8px; padding:25px;">
            <h4 style="margin-top:0; font-size:22px; color:#065f46;">🐂 Bull Case</h4><p style="margin:0; color:#064e3b;">{xtag(raw, "BULL_CASE")}</p>
        </div>
        <div style="flex:1; min-width:250px; background:#fef2f2; border:2px solid #ef4444; border-radius:8px; padding:25px;">
            <h4 style="margin-top:0; font-size:22px; color:#991b1b;">🐻 Bear Case</h4><p style="margin:0; color:#7f1d1d;">{xtag(raw, "BEAR_CASE")}</p>
        </div>
    </div>"""
    html += _build_quick_hits(xtag(raw, "QUICK_HITS"))
    html += f"""<div style="background:#ffffff; border:2px solid {GOLD}; padding:30px; border-radius:8px; margin:45px 0;">
        <h3 style="margin-top:0; color:{GOLD}; font-size:24px;">💎 Smart Money Move</h3><p style="margin:0;">{xtag(raw, "SMART_MONEY_MOVE")}</p>
    </div>"""
    if xtag(raw, "HISTORICAL_PARALLEL"):
        html += f"""<div style="background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding:35px; border-radius:12px; margin:45px 0; border-left:5px solid {GOLD};">
            <h3 style="color:{GOLD}; margin-top:0; font-size:24px;">📜 Historical Parallel</h3><p style="color:#cbd5e1; font-size:17px; margin:15px 0 0;">{xtag(raw, "HISTORICAL_PARALLEL")}</p>
        </div>"""
    al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
    html += f"""<div style="background:{BG_LIGHT}; border:1px solid {BORDER}; padding:30px; border-radius:8px; margin-bottom:40px;">
        <h3 style="margin-top:0; font-size:22px; color:{DARK};">📊 Suggested Allocation</h3>{_build_pie_chart(al["s"], al["b"], al["c"], cat)}
        <p style="margin-top:15px; color:{MUTED}; font-size:14px; text-align:center; font-style:italic;">General guideline based on current {cat} outlook. Not personalized advice.</p>
    </div>"""
    html += f"""<hr style="border:0; height:1px; background:{BORDER}; margin:50px 0;">
    <h2 style="font-family:Georgia,serif; font-size:28px; color:{DARK}; margin-bottom:20px;">Today's Warm Insight</h2>
    <p style="{F} font-size:19px; font-style:italic; border-left:3px solid #cbd5e1; padding-left:16px;">"{xtag(raw, "TAKEAWAY")}"</p>
    <div style="background:{DARK}; padding:30px; border-radius:10px; border-left:5px solid {GOLD}; margin-top:35px;">
        <p style="color:#e2e8f0; font-size:18px; margin:0;"><strong style="color:{GOLD};">P.S.</strong> {xtag(raw, "PS")}</p>
    </div>"""
    html += _build_pillar_link("Insight") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p>
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:20px; text-transform:uppercase; letter-spacing:0.5px;">Disclaimer: AI-generated, human-edited educational content. Not financial advice. All decisions are your own.</p></div>"""
    return sanitize(html)

def get_font(url, filename):
    if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            print(f"    📥 Downloading font from {url}...")
            resp = scraper.get(url, timeout=15)
            resp.raise_for_status()
            with open(filename, 'wb') as f: f.write(resp.content)
            print("    ✅ Font downloaded successfully.")
        except Exception as e:
            print(f"    ❌ Font download error: {e}")
    return filename

def make_thumbnail(title_text, cat, tier):
    W, H, SCALE = 1200, 630, 2
    w, h = W * SCALE, H * SCALE

    CAT_STYLES = {
        "Economy":  {"bg1": "#0284c7", "bg2": "#0369a1", "acc": "#fde047"},
        "Politics": {"bg1": "#dc2626", "bg2": "#991b1b", "acc": "#fde047"},
        "Tech":     {"bg1": "#6366f1", "bg2": "#4338ca", "acc": "#a78bfa"},
        "Health":   {"bg1": "#059669", "bg2": "#047857", "acc": "#fef08a"},
        "Energy":   {"bg1": "#ea580c", "bg2": "#c2410c", "acc": "#fef3c7"},
        "On-Chain": {"bg1": "#8b5cf6", "bg2": "#5b21b6", "acc": "#fde047"},
        "The Daily Catalyst": {"bg1": "#1e293b", "bg2": "#0f172a", "acc": "#b8974d"},
        "Foundation": {"bg1": "#1e3a5f", "bg2": "#0f2040", "acc": "#f59e0b"},
        "Money Hack": {"bg1": "#f59e0b", "bg2": "#b45309", "acc": "#fef3c7"}
    }
    style = CAT_STYLES.get(cat, CAT_STYLES["Economy"])

    AI_PROMPTS = {
        "Economy": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot standing enthusiastically and pointing at a floating stock market chart, acting as a friendly guide. Vibrant colors, clean gradient background. No text.",
        "Politics": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot standing enthusiastically and pointing at a glowing globe, acting as a friendly guide. Vibrant colors, clean gradient background. No text.",
        "Tech": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot standing enthusiastically and pointing at a glowing microchip, acting as a friendly guide. Vibrant colors, clean gradient background. No text.",
        "Health": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot standing enthusiastically and pointing at a glowing DNA helix, acting as a friendly guide. Vibrant colors, clean gradient background. No text.",
        "Energy": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot standing enthusiastically and pointing at a bright lightning bolt, acting as a friendly guide. Vibrant colors, clean gradient background. No text.",
        "On-Chain": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot standing enthusiastically and pointing at a glowing Bitcoin and blockchain network nodes, acting as a friendly guide. Vibrant purple colors, clean gradient background. No text, no words.",
        "The Daily Catalyst": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot enthusiastically presenting a classic book. Dark premium colors. No text.",
        "Foundation": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot enthusiastically pointing at a gold coin and a guide book. Vibrant colors. No text.",
        "Money Hack": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large sleek white robot mascot enthusiastically holding a glowing laptop and money. Vibrant yellow and green colors. No text."
    }

    img = None
    use_ai_bg = False
    try:
        print(f"    [AI] Requesting Mascot Vector Background for {cat}...")
        client = _get_gemini_client()
        result = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=AI_PROMPTS.get(cat, AI_PROMPTS["Economy"]),
            config=types.GenerateImagesConfig(
                number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg"
            )
        )
        bg_bytes = result.generated_images[0].image.image_bytes
        img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
        img = img.resize((w, h), Image.LANCZOS)
        use_ai_bg = True
        print("    ✅ AI Mascot Generated!")
    except Exception as e:
        print(f"    ⚠️ AI Image Gen skipped/failed. Using custom Pillow fallback. ({e})")
        img = Image.new("RGBA", (w, h), style["bg1"])
        draw = ImageDraw.Draw(img)
        draw.ellipse([w*0.35, -h*0.5, w*1.5, h*1.5], fill=style["bg2"])

        cx = w * 0.88
        cy = h * 0.65
        S = SCALE
        cx_p = cx - 180 * S
        cy_p = cy

        if cat == "Economy":
            draw.rectangle([cx_p-60*S, cy_p+20*S, cx_p-20*S, cy_p+80*S], fill="#38bdf8")
            draw.rectangle([cx_p-10*S, cy_p-20*S, cx_p+30*S, cy_p+80*S], fill="#38bdf8")
            draw.rectangle([cx_p+40*S, cy_p-60*S, cx_p+80*S, cy_p+80*S], fill="#fde047")
            draw.line([cx_p-80*S, cy_p+40*S, cx_p*S, cy_p-20*S, cx_p+90*S, cy_p-90*S], fill="#ffffff", width=8*S)
        elif cat == "Politics":
            draw.polygon([(cx_p, cy_p-80*S), (cx_p-80*S, cy_p-20*S), (cx_p+80*S, cy_p-20*S)], fill="#fca5a5")
            draw.rectangle([cx_p-70*S, cy_p-20*S, cx_p+70*S, cy_p], fill="#ef4444")
            draw.rectangle([cx_p-60*S, cy_p, cx_p-40*S, cy_p+80*S], fill="#fca5a5")
            draw.rectangle([cx_p-10*S, cy_p, cx_p+10*S, cy_p+80*S], fill="#fca5a5")
            draw.rectangle([cx_p+40*S, cy_p, cx_p+60*S, cy_p+80*S], fill="#fca5a5")
            draw.rectangle([cx_p-80*S, cy_p+80*S, cx_p+80*S, cy_p+100*S], fill="#ef4444")
        elif cat == "Tech":
            draw.rounded_rectangle([cx_p-60*S, cy_p-60*S, cx_p+60*S, cy_p+60*S], radius=15*S, fill="#818cf8")
            draw.rectangle([cx_p-30*S, cy_p-30*S, cx_p+30*S, cy_p+30*S], fill="#312e81")
            for offset in [-40, 0, 40]:
                draw.line([(cx_p+offset*S, cy_p-60*S), (cx_p+offset*S, cy_p-90*S)], fill="#c7d2fe", width=8*S)
                draw.line([(cx_p+offset*S, cy_p+60*S), (cx_p+offset*S, cy_p+90*S)], fill="#c7d2fe", width=8*S)
                draw.line([(cx_p-60*S, cy_p+offset*S), (cx_p-90*S, cy_p+offset*S)], fill="#c7d2fe", width=8*S)
                draw.line([(cx_p+60*S, cy_p+offset*S), (cx_p+90*S, cy_p+offset*S)], fill="#c7d2fe", width=8*S)
        elif cat == "Health":
            draw.rounded_rectangle([cx_p-20*S, cy_p-70*S, cx_p+20*S, cy_p+70*S], radius=10*S, fill="#a7f3d0")
            draw.rounded_rectangle([cx_p-70*S, cy_p-20*S, cx_p+70*S, cy_p+20*S], radius=10*S, fill="#a7f3d0")
        elif cat == "Energy":
            draw.polygon([(cx_p+30*S, cy_p-90*S), (cx_p-50*S, cy_p+10*S), (cx_p+10*S, cy_p+10*S), (cx_p-30*S, cy_p+90*S), (cx_p+50*S, cy_p-10*S), (cx_p-10*S, cy_p-10*S)], fill="#fde047")
        elif cat == "On-Chain":
            draw.ellipse([cx_p-50*S, cy_p-50*S, cx_p+50*S, cy_p+50*S], fill="#a78bfa")
            draw.polygon([(cx_p, cy_p-30*S), (cx_p-20*S, cy_p+15*S), (cx_p+20*S, cy_p+15*S)], fill="#fde047")
            draw.polygon([(cx_p, cy_p+30*S), (cx_p-20*S, cy_p+20*S), (cx_p+20*S, cy_p+20*S)], fill="#fde047")
        elif cat == "The Daily Catalyst":
            draw.ellipse([cx_p-50*S, cy_p-70*S, cx_p+50*S, cy_p+30*S], fill="#cbd5e1")
            draw.polygon([(cx_p-25*S, cy_p+20*S), (cx_p+25*S, cy_p+20*S), (cx_p+15*S, cy_p+70*S), (cx_p-15*S, cy_p+70*S)], fill="#94a3b8")
        elif cat == "Foundation" or cat == "Money Hack":
            draw.rectangle([cx_p-70*S, cy_p-60*S, cx_p+70*S, cy_p+80*S], fill="#1e3a5f", outline="#f59e0b", width=6*S)
            draw.rectangle([cx_p-55*S, cy_p-40*S, cx_p+55*S, cy_p-20*S], fill="#f59e0b")
            draw.rectangle([cx_p-55*S, cy_p-10*S, cx_p+55*S, cy_p+10*S], fill="#f59e0b")
            draw.rectangle([cx_p-55*S, cy_p+20*S, cx_p+20*S, cy_p+40*S], fill="#f59e0b")

        R = S * 1.4
        draw.ellipse([cx - 40*R, cy + 65*R, cx + 40*R, cy + 85*R], fill="#00000030")
        draw.line([(cx - 30*R, cy + 10*R), (cx - 70*R, cy - 35*R)], fill="#f8fafc", width=int(12*R))
        draw.line([(cx - 70*R, cy - 35*R), (cx - 85*R, cy - 35*R)], fill="#cbd5e1", width=int(12*R))
        draw.line([(cx + 30*R, cy + 10*R), (cx + 45*R, cy + 40*R)], fill="#f8fafc", width=int(12*R))
        draw.rounded_rectangle([cx - 40*R, cy - 30*R, cx + 40*R, cy + 70*R], radius=int(15*R), fill="#f8fafc", outline="#cbd5e1", width=int(4*R))
        draw.rounded_rectangle([cx - 50*R, cy - 100*R, cx + 50*R, cy - 35*R], radius=int(20*R), fill="#f8fafc", outline="#cbd5e1", width=int(4*R))
        draw.rounded_rectangle([cx - 40*R, cy - 85*R, cx + 40*R, cy - 45*R], radius=int(10*R), fill="#0f172a")
        draw.line([(cx - 25*R, cy - 65*R), (cx - 10*R, cy - 65*R)], fill="#38bdf8", width=int(6*R))
        draw.line([(cx + 10*R, cy - 65*R), (cx + 25*R, cy - 65*R)], fill="#38bdf8", width=int(6*R))
        draw.line([(cx, cy - 100*R), (cx, cy - 120*R)], fill="#cbd5e1", width=int(4*R))
        draw.ellipse([cx - 8*R, cy - 130*R, cx + 8*R, cy - 114*R], fill="#f59e0b")
        draw.ellipse([cx - 30*R, cy - 50*R, cx - 20*R, cy - 40*R], fill="#fca5a5")
        draw.ellipse([cx + 20*R, cy - 50*R, cx + 30*R, cy - 40*R], fill="#fca5a5")

    draw.rectangle([(0, h - 80 * SCALE), (w, h)], fill="#00000060")

    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    def lf(p, s):
        try: return ImageFont.truetype(p, s * SCALE)
        except: return ImageFont.load_default()

    ft = lf(ft_path, 85)
    fs = lf(ft_path, 34)
    fb = lf(ft_path, 28)

    S = SCALE
    date_badge = datetime.datetime.utcnow().strftime("%Y.%m.%d")
    draw.text((40 * S, 44 * S), date_badge, font=fb, fill="#ffffff")

    try: date_w = draw.textlength(date_badge, font=fb)
    except: date_w = len(date_badge) * 15 * S

    bx = 40 * S + date_w + 30 * S
    try: cat_w = draw.textlength(cat.upper(), font=fb)
    except: cat_w = len(cat) * 15 * S

    draw.rounded_rectangle([(bx, 36 * S), (bx + cat_w + 60 * S, 86 * S)], radius=25 * S, fill="#ffffff")
    draw.text((bx + 30 * S, 44 * S), cat.upper(), font=fb, fill="#1e293b")

    clean_title = _clean_seo_title(title_text).upper()
    clean_title = re.sub(r'^WARM INSIGHT\s*[:\-–]\s*', '', clean_title).strip()

    words = clean_title.split()
    lines, line = [], []
    mw = w - 100 * SCALE if use_ai_bg else w - 380 * SCALE

    for word in words:
        t = " ".join(line + [word])
        try: tw2 = draw.textlength(t, font=ft)
        except: tw2 = len(t) * 40 * SCALE
        if tw2 < mw: line.append(word)
        else:
            if line: lines.append(" ".join(line))
            line = [word]
    if line: lines.append(" ".join(line))

    y = 160 * SCALE
    for i, ln in enumerate(lines[:4]):
        draw.text((40 * S + 4 * S, y + 4 * S), ln, font=ft, fill="#00000060")
        color = "#ffffff" if use_ai_bg else (style.get("acc", "#ffffff") if i == 1 else "#ffffff")
        draw.text((40 * S, y), ln, font=ft, fill=color)
        try:
            bb = draw.textbbox((0, 0), ln, font=ft)
            y += (bb[3] - bb[1]) + 15 * S
        except: y += 100 * S

    date_bottom = datetime.datetime.utcnow().strftime("%B %d, %Y")
    draw.text((40 * S, h - 70 * S), f"WARM INSIGHT  |  {date_bottom}", font=fs, fill="#ffffff80")

    tagline = "AI-DRIVEN GLOBAL MARKET ANALYSIS"
    try: tw_t = draw.textlength(tagline, font=fs)
    except: tw_t = len(tagline) * 15 * S
    draw.text((w - 40 * S - tw_t, h - 70 * S), tagline, font=fs, fill="#ffffff80")

    img = img.convert("RGB")
    img = img.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def make_medium_thumbnail(cat):
    print(f"    [AI] Generating Premium Editorial Thumbnail for Medium...")
    client = _get_gemini_client()
    
    prompts = {
        "Economy": "A highly aesthetic, conceptual 3D illustration about global economy and stock markets. Cinematic lighting, minimalist composition, deep rich blue and gold colors. High-end financial magazine cover style. No text, no words, no letters.",
        "Politics": "A highly aesthetic, conceptual 3D illustration about geopolitics and global policy. Cinematic lighting, minimalist composition, deep red and dark slate colors. High-end political magazine cover style. No text, no words, no letters.",
        "Tech": "A highly aesthetic, conceptual 3D illustration about artificial intelligence and future technology. Cinematic lighting, minimalist composition, glowing neon purple and cyan colors. High-end tech magazine cover style. No text, no words, no letters.",
        "Health": "A highly aesthetic, conceptual 3D illustration about biotechnology and healthcare innovation. Cinematic lighting, minimalist composition, clean emerald green and white colors. High-end medical magazine cover style. No text, no words, no letters.",
        "Energy": "A highly aesthetic, conceptual 3D illustration about global energy transition and power resources. Cinematic lighting, minimalist composition, vibrant orange and amber colors. High-end energy magazine cover style. No text, no words, no letters.",
        "On-Chain": "A highly aesthetic, conceptual 3D illustration about blockchain, crypto, and decentralized finance. Cinematic lighting, minimalist composition, glowing purple and gold accents. High-end crypto magazine cover style. No text, no words, no letters.",
        "The Daily Catalyst": "A highly aesthetic, conceptual 3D illustration about wealth building and mental growth. Cinematic lighting, minimalist composition, deep rich colors with warm glowing accents. High-end magazine cover style. No text, no words, no letters.",
        "Foundation": "A highly aesthetic, conceptual 3D illustration about financial foundation and investment basics. Cinematic lighting, minimalist composition, deep rich colors with glowing gold accents. High-end magazine cover style. No text, no words, no letters.",
        "Money Hack": "A highly aesthetic, conceptual 3D illustration about digital wealth and side hustles. Cinematic lighting, minimalist composition, deep rich colors with vibrant glowing accents. High-end magazine cover style. No text, no words, no letters."
    }
    prompt = prompts.get(cat, prompts["Economy"])
    
    try:
        result = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg"
            )
        )
        print("    ✅ Medium Editorial Thumbnail Generated Successfully!")
        return result.generated_images[0].image.image_bytes
    except Exception as e:
        print(f"    ⚠️ Medium AI Image Gen failed. Trying Pollinations AI... ({e})")
        try:
            prompt_encoded = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1200&height=630&nologo=true"
            resp = scraper.get(url, timeout=30)
            if resp.status_code == 200:
                print("    ✅ Medium Pollinations Thumbnail Generated Successfully!")
                return resp.content
        except:
            pass
        W, H = 1200, 630
        CAT_STYLES = {
            "Economy":  {"bg1": "#0284c7", "bg2": "#0369a1", "acc": "#fde047"},
            "Politics": {"bg1": "#dc2626", "bg2": "#991b1b", "acc": "#fde047"},
            "Tech":     {"bg1": "#6366f1", "bg2": "#4338ca", "acc": "#a78bfa"},
            "Health":   {"bg1": "#059669", "bg2": "#047857", "acc": "#fef08a"},
            "Energy":   {"bg1": "#ea580c", "bg2": "#c2410c", "acc": "#fef3c7"},
            "On-Chain": {"bg1": "#8b5cf6", "bg2": "#5b21b6", "acc": "#fde047"},
            "The Daily Catalyst": {"bg1": "#1e293b", "bg2": "#0f172a", "acc": "#b8974d"},
            "Foundation": {"bg1": "#1e3a5f", "bg2": "#0f2040", "acc": "#f59e0b"},
            "Money Hack": {"bg1": "#f59e0b", "bg2": "#b45309", "acc": "#fef3c7"}
        }
        style = CAT_STYLES.get(cat, CAT_STYLES["Economy"])
        img = Image.new("RGBA", (W, H), style["bg1"])
        draw = ImageDraw.Draw(img)

        draw.ellipse([W*0.5, -H*0.2, W*1.3, H*1.2], fill=style["bg2"])
        draw.ellipse([-W*0.1, H*0.4, W*0.4, H*1.5], fill="#00000030")
        
        draw.line([(W*0.15, H*0.2), (W*0.25, H*0.2)], fill=style.get("acc", "#ffffff"), width=8)
        draw.ellipse([W*0.8, H*0.75, W*0.82, H*0.75+W*0.02], fill=style.get("acc", "#ffffff"))
        draw.rectangle([W*0.15, H*0.8, W*0.4, H*0.82], fill=style.get("acc", "#ffffff"))

        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

def generate_video_mp4(cat, hook_text, data_points, frames_images):
    print("   🎥 Generating 15-Sec Dark Psychology Reels Video (Optimized)...")
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
        print(f"   ✅ Dark Psychology 15s Video Extracted! ({len(mp4_bytes)/1024/1024:.1f}MB)")
        return mp4_bytes
    except Exception as e:
        print(f"   ❌ Video Encoding Failed: {e}")
        return None

def generate_vip_carousel(raw_content, cat):
    print("   🎨 Generating DYNAMIC 4-IMAGE Dark Psychology Carousel...")
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
    
    # 🚨 영상 피로도 개선 1 & 2: 매번 다른 컬러를 랜덤으로 픽업하여 다양성 부여 & 친근한 캐릭터(졸라맨/호빵맨) 도입
    colors = ["glowing neon blue", "vibrant emerald green", "striking neon purple", "bright amber gold", "intense crimson red"]
    random.shuffle(colors)
    vp_base = f"A cute, approachable, smooth 3D minimalist character with a round friendly head, resembling a high-end polished stickman or Anpanman. Pitch black void background. Engaging, clean cinematic 8k render. No creepy vibes. No text."
    vp1 = vp_base + f" The character is looking surprised, pointing at a downward {colors[0]} line graph."
    vp2 = vp_base + f" Close up profile. The friendly character is carefully analyzing a floating {colors[1]} data sphere."
    vp3 = vp_base + f" Medium shot. The character is dynamically touching floating {colors[2]} digital nodes and charts."
    vp4 = vp_base + f" The character is standing confidently with a powerful {colors[3]} aura."

    data_points = []
    for i in range(1, 6):
        item = xtag(raw_data, f"ITEM{i}")
        if item and "|" in item:
            parts = item.split("|")
            raw_ticker = parts[0].strip()
            # 🚨 텍스트 잘림 방지 1: 글자 길이 제한을 10 -> 20자로 넉넉하게 확장
            if len(raw_ticker) > 20: raw_ticker = raw_ticker[:18] + ".."
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
    RED = "#ef4444"
    GRAY = "#94a3b8"

    import urllib.request, urllib.parse
    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    def lf(p, s):
        try: return ImageFont.truetype(p, s)
        except: return ImageFont.load_default()

    font_title = lf(ft_path, 95)    
    font_huge = lf(ft_path, 200)    
    font_mega = lf(ft_path, 135)    
    font_sub = lf(ft_path, 55)
    font_data = lf(ft_path, 50)
    font_alert = lf(ft_path, 75)

    def fetch_dark_psy_image(prompt_text, seed):
        try:
            prompt_encoded = urllib.parse.quote(prompt_text)
            # 🚨 캐시 우회를 위해 random.random() 난수 강제 주입
            url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1080&height=1080&nologo=true&seed={seed}&random={random.random()}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                img_data = response.read()
                ai_img_raw = Image.open(io.BytesIO(img_data)).convert("RGBA")
                ai_img_raw = ai_img_raw.resize((1080, 1080), Image.LANCZOS)
                mask = Image.new("L", (1080, 1080), 255)
                mask_draw = ImageDraw.Draw(mask)
                for y in range(780, 1080):
                    alpha = int(255 - (y - 780) * (255 / 300))
                    mask_draw.line([(0, y), (1080, y)], fill=alpha)
                ai_img_raw.putalpha(mask)
                return ai_img_raw
        except Exception as e:
            print(f"    ⚠️ Image Gen failed: {e}")
            return None

    print("    [AI] Requesting 4 unique images for Dynamic Storytelling...")
    img_hook_ai = fetch_dark_psy_image(vp1, random.randint(1, 100000))
    time.sleep(5)
    img_stat_ai = fetch_dark_psy_image(vp2, random.randint(1, 100000))
    time.sleep(5)
    img_data_ai = fetch_dark_psy_image(vp3, random.randint(1, 100000))
    time.sleep(5)
    img_out_ai  = fetch_dark_psy_image(vp4, random.randint(1, 100000))

    last_good_img = None
    for img in [img_hook_ai, img_stat_ai, img_data_ai, img_out_ai]:
        if img:
            last_good_img = img
            break

    if not img_hook_ai: img_hook_ai = last_good_img
    if not img_stat_ai: img_stat_ai = last_good_img
    if not img_data_ai: img_data_ai = last_good_img
    if not img_out_ai: img_out_ai = last_good_img

    def paste_bg(d_img, target_ai_img):
        if target_ai_img:
            d_img.paste(target_ai_img, (0, 100), target_ai_img)
        else:
            fallback_img = Image.new("RGBA", (1080, 1080), "#09090b")
            d = ImageDraw.Draw(fallback_img)
            d.ellipse([440, 200, 640, 400], fill="#ffffff") 
            d.rounded_rectangle([400, 430, 680, 750], radius=50, fill="#ffffff") 
            d.ellipse([500, 500, 580, 580], fill="#ef4444") 
            mask = Image.new("L", (1080, 1080), 255)
            mask_draw = ImageDraw.Draw(mask)
            for y in range(780, 1080):
                alpha = int(255 - (y - 780) * (255 / 300))
                mask_draw.line([(0, y), (1080, y)], fill=alpha)
            fallback_img.putalpha(mask)
            d_img.paste(fallback_img, (0, 100), fallback_img)
            
        # 🚨 가독성 향상: 60% 다크 블랙 필터 오버레이 적용 (붉은 빛 등 컬러가 텍스트를 방해하지 않음)
        dark_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 153))
        d_img.paste(dark_overlay, (0, 0), dark_overlay)

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

    img1 = Image.new("RGB", (W, H), BG)
    paste_bg(img1, img_hook_ai)
    d1 = ImageDraw.Draw(img1)
    d1.rounded_rectangle([300, 1150, 780, 1250], radius=20, fill=RED)
    d1.text((W//2, 1200), f"🚨 {cat.upper()} ALERT", fill=WHITE, font=font_alert, anchor="mm")
    
    # 🚨 텍스트 잘림 방지 2: 좌우 여백을 넓힘 (max_width 850 -> 950 적용)
    hook_lines = wrap_lines(hook_text.upper(), font_title, 950) 
    y_text = 1350
    for i, ln in enumerate(hook_lines[:4]):
        color = RED if i == len(hook_lines)-1 else WHITE
        d1.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 105 
    d1.text((W//2, 1800), "↓ SWIPE TO SEE WHY ↓", fill=GRAY, font=font_sub, anchor="mm")

    img2 = Image.new("RGB", (W, H), BG)
    paste_bg(img2, img_stat_ai)
    d2 = ImageDraw.Draw(img2)
    d2.text((W//2, 1180), "THE NUMBER", fill=RED, font=font_sub, anchor="mm")
    shock_lines = wrap_lines(shock_stat.upper(), font_mega, 950)
    y_text = 1350
    for ln in shock_lines[:3]:
        d2.text((W//2, y_text), ln, fill=WHITE, font=font_mega, anchor="mm")
        y_text += 145 
    d2.text((W//2, 1800), "WAIT FOR IT...", fill=GRAY, font=font_sub, anchor="mm")

    data_imgs = []
    for idx in range(3):
        if idx >= len(data_points): break
        item = data_points[idx]
        img_d = Image.new("RGB", (W, H), BG)
        paste_bg(img_d, img_data_ai)
        d = ImageDraw.Draw(img_d)
        d.text((W//2, 1150), cat.upper(), fill=RED, font=font_sub, anchor="mm")
        d.text((W//2, 1250), f"WATCH THIS → {idx+1}/3", fill=GRAY, font=font_data, anchor="mm")
        
        # 🚨 텍스트 잘림 방지 3: 글자 길이에 따른 동적 스케일링(Dynamic Font Sizing) 완벽 적용
        ticker_str = item['ticker']
        t_size = 95
        if len(ticker_str) > 12: t_size = int(95 * (12 / len(ticker_str)))
        d.text((W//2, 1400), ticker_str, fill=WHITE, font=lf(ft_path, max(45, t_size)), anchor="mm")
        
        val_str = item['val']
        val_color = RED if '-' in val_str else WHITE
        v_size = 200
        if len(val_str) > 6: v_size = int(200 * (6 / len(val_str)))
        d.text((W//2, 1550), val_str, fill=val_color, font=lf(ft_path, max(70, v_size)), anchor="mm")
        
        dot_y = 1800
        for di in range(3):
            dx = W//2 + (di - 1) * 60
            color = RED if di == idx else "#3f3f46"
            d.ellipse([dx-15, dot_y-15, dx+15, dot_y+15], fill=color)
        data_imgs.append(img_d)

    img6 = Image.new("RGB", (W, H), BG)
    paste_bg(img6, img_out_ai)
    d6 = ImageDraw.Draw(img6)
    d6.text((W//2, 1150), "THE TAKEAWAY", fill=RED, font=font_sub, anchor="mm")
    insight_lines = wrap_lines(insight_line.upper(), font_title, 950)
    y_text = 1250
    for ln in insight_lines[:3]:
        d6.text((W//2, y_text), ln, fill=WHITE, font=font_title, anchor="mm")
        y_text += 105
    d6.text((W//2, 1650), cta_hook.upper(), fill=RED, font=font_alert, anchor="mm")
    d6.text((W//2, 1780), "LINK IN BIO → @WARMINSIGHT", fill=GRAY, font=font_sub, anchor="mm")

    image_bytes_list = []
    all_frames = [img1, img2] + data_imgs + [img6]
    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, all_frames)

    return image_bytes_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes

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

# ═══════════════════════════════════════════════
# ✉️ 슬림 이메일 (인스타/숏폼용) -> 🚨 1-Min Reels 대본 삭제 완료
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
                <p style="color: #10b981; font-weight: 900; font-size: 18px; margin-top: 0; text-transform: uppercase;">🎬 15-Sec Dark Psychology Reels Attached!</p>
                <div style="font-size: 45px; margin: 15px 0;">✨ 📹 ✨</div>
                <p style="color: #ffffff; font-size: 15px; font-weight: bold; margin: 5px 0;">100% Compatible with IG Reels / TikTok / YT Shorts.</p>
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0; margin-top: 10px;">Download <strong>WarmInsight_{cat}_Video.mp4</strong> attached below.</p>
            </div>
            """

        body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f4f4f5; padding: 20px; color: #0f1419;">
            {vid_tag}
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
# 🚨 _upload_image 함수 복구 완료!
# ═══════════════════════════════════════════════
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
    
    print(f"🚀 Starting v46.9.52 SEO Foundation Pipeline | Category: {cat}")
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
    
    print(f"🚀 Starting v46.9.52 Catalyst Pipeline | Category: {cat}")
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
    
    print(f"🚀 Starting v46.9.52 Money Hack Pipeline | Category: {cat}")
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
        print(f"🚀 Starting v46.9.52 Unified News Pipeline | TEST MODE (Force Publish)")
    else:
        print(f"🚀 Starting v46.9.52 Unified News Pipeline | Category: {cat}")

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
