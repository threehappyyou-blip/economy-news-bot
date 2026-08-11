#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — Ultimate Masterpiece Edition (v46.9.123_MARSHMALLOW_MASCOT_ENGINE)
# ═══════════════════════════════════════════════════════════════

import os, sys, traceback, time, random, re, datetime, io, math, base64
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

EXTERNAL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 🚨 Imunify360 방화벽 우회 전용 스크래퍼 (모든 WP 통신에 적용)
try:
    import cloudscraper
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    scraper.headers.update({
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1'
    })
except ImportError:
    print("❌ [System Error] 'cloudscraper' 라이브러리가 설치되지 않았습니다.")
    sys.exit(1)

# 워드프레스 통신 전용 인증 헤더
def _get_wp_headers():
    auth_str = f"{WP_USER}:{WP_APP_PASS}"
    b64_auth = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    return {
        'Accept': 'application/json',
        'Authorization': f'Basic {b64_auth}',
        'Cache-Control': 'no-cache',
        'Connection': 'close' 
    }

# 🚨 엔터프라이즈급 API 랩퍼 (500 Error, 403 Error 자동 복구 로직)
def wp_api_call(method, endpoint, json_data=None, data_bytes=None, filename=None):
    url = f"{WP_URL}{endpoint}" if endpoint.startswith("/") else f"{WP_URL}/wp-json/wp/v2/{endpoint}"
    headers = _get_wp_headers()
    
    if filename:
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        headers['Content-Type'] = 'image/jpeg'
        
    for attempt in range(1, 4):
        try:
            scraper.cookies.clear() 
            if method == 'GET':
                resp = scraper.get(url, headers=headers, timeout=30)
            elif method == 'POST' and json_data is not None:
                resp = scraper.post(url, headers=headers, json=json_data, timeout=30)
            elif method == 'POST' and data_bytes is not None:
                resp = scraper.post(url, headers=headers, data=data_bytes, timeout=45)
            else:
                return None
                
            if resp.status_code in (200, 201):
                return resp
            elif resp.status_code >= 500:
                print(f"      ⚠️ Server Overloaded ({resp.status_code}) on attempt {attempt}. Cooling down for 5s...")
                time.sleep(5)
            elif resp.status_code in (401, 403):
                print(f"      ⚠️ WAF/Auth Blocked ({resp.status_code}) on attempt {attempt}. Retrying...")
                time.sleep(3)
            else:
                return resp 
        except Exception as e:
            print(f"      ⚠️ Network Error ({e}) on attempt {attempt}. Retrying...")
            time.sleep(5)
    return None

MODEL_PRI = {
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
    "Economy": {"s": 55, "b": 35, "c": 10}, "Politics": {"s": 50, "b": 35, "c": 15},
    "Tech": {"s": 70, "b": 20, "c": 10}, "Health": {"s": 60, "b": 30, "c": 10},
    "Energy": {"s": 65, "b": 25, "c": 10}, "On-Chain": {"s": 25, "b": 15, "c": 60}
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
- AT LEAST 3 specific numbers (percentages, dollar amounts, dates, exact ticker prices).
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
(REQUIRED — extract OR estimate 3-4 key market metrics. NO MARKDOWN TABLES. NO '---' lines. Format EXACTLY on separate lines: Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight under 12 words)
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
<COMMENT_QUESTION>(A highly provocative and engaging question related to today's topic to encourage readers to leave a comment. Max 15 words.)</COMMENT_QUESTION>
"""

# ═══════════════════════════════════════════════
# 🎬 1. YOUTUBE CHAPTERING ENGINE
# ═══════════════════════════════════════════════
YT_META_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Based on the following newsletter content, generate a YouTube Metadata package in ENGLISH.
[NEWSLETTER]
{raw_content}

OUTPUT REQUIREMENT: Wrap your response EXACTLY in <METADATA> and </METADATA> tags.
<METADATA>
[VIRAL TITLES]
- Option A: 
- Option B: 
- Option C: 
[THUMBNAIL IDEAS]
1. Visual Prompt: (Generate a HYPER-DETAILED, professional AI image generation prompt for Midjourney/Vrew. NO TEXT IN PROMPT.)
2. Text/Copy: (Write 2-4 words of MASSIVE IMPACT, click-inducing text to place directly ON the thumbnail.)
[SEO HASHTAGS]
(10 highly searched global tags)
</METADATA>"""

YT_SCRIPT_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are a top-tier YouTube Scriptwriter for "Warm Insight". Write PART 1 (Introduction & The Hook) of a MASSIVE documentary script based on the newsletter in ENGLISH.
[NEWSLETTER]
{raw_content}
Rules: NO structural tags inside the text. Wrap everything in <PART1> tags. Minimum 1500 words."""

YT_SCRIPT_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are a top-tier YouTube Scriptwriter. Write PART 2: Chapter 2 & 3 (Historical Context & Deep Dive).
[NEWSLETTER]
{raw_content}
[PREVIOUS SCRIPT (PART 1)]
{p1}
Rules: NO structural tags inside the text. Wrap everything in <PART2> tags. Minimum 1500 words."""

YT_SCRIPT_P3 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are a top-tier YouTube Scriptwriter. Write PART 3: Chapter 4 & Outro.
[NEWSLETTER]
{raw_content}
[PREVIOUS SCRIPT (PART 2)]
{p2}
Rules: NO structural tags inside the text. Wrap everything in <PART3> tags. Minimum 1500 words."""

def generate_youtube_masterpiece(raw_content, title):
    print(f"   🎬 [YouTube Engine] Starting 3-Phase Chaptering for '{title[:30]}...'")
    client = _get_gemini_client()
    meta = xtag(gem_fb("Premium", YT_META_PROMPT.replace("{raw_content}", raw_content)), "METADATA")
    
    print("      - Generating Part 1...")
    p1 = xtag(gem_fb("Premium", YT_SCRIPT_P1.replace("{raw_content}", raw_content)), "PART1")
    
    print("      - Generating Part 2...")
    p2 = xtag(gem_fb("Premium", YT_SCRIPT_P2.replace("{raw_content}", raw_content).replace("{p1}", p1)), "PART2")
    
    print("      - Generating Part 3...")
    p3 = xtag(gem_fb("Premium", YT_SCRIPT_P3.replace("{raw_content}", raw_content).replace("{p2}", p2)), "PART3")
    
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
                    <h3 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-top: 35px;">🎙️ Vrew Script (Copy & Paste)</h3>
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
# ✉️ 커뮤니티 바이럴 포스팅 (Reddit/Quora) 엔진 
# ═══════════════════════════════════════════════
def generate_reddit_post(raw_content, cat, original_link):
    print(f"   🤖 [AI] Crafting 100% Human-tone Reddit Post...")
    sys_inst = """CRITICAL RULE: Write entirely in ENGLISH. You are a 20-something retail investor posting on Reddit. You are NOT an AI.
    TONE: Casual, cynical, conversational "bro" tone. Use slang (tbh, ngl, crazy, wild, fwiw, bros).
    BANNED: Bullet points, bold text, "Executive Summary", "TL;DR", emojis (max 1).
    CRITICAL: YOU MUST WRAP YOUR ENTIRE OUTPUT IN <REDDIT_TITLE> and <REDDIT_BODY> XML TAGS."""
    prompt = f"Rewrite this core insight into a viral Reddit post for {cat} subreddits.\n[ANALYSIS]\n{raw_content}\n[OUTPUT FORMAT]\n<REDDIT_TITLE>(Max 12 words)</REDDIT_TITLE>\n<REDDIT_BODY>(2-3 paragraphs. Drop this link at the end: {original_link})</REDDIT_BODY>"
    raw = gem_fb("Premium", prompt, sys_inst)
    return xtag(raw, "REDDIT_TITLE"), xtag(raw, "REDDIT_BODY")

def send_community_viral_email(title, original_link, raw_content, cat):
    if not EMAIL_SENDER or not EMAIL_RECEIVER: return
    print(f"   📧 Generating and Sending Human-like Community Viral Draft to {EMAIL_RECEIVER}...")

    target_subreddits = "r/povertyfinance, r/sidehustle, r/stocks, r/CryptoCurrency"
    r_title, r_body = generate_reddit_post(raw_content, cat, original_link)
    
    if not r_title or not r_body:
        r_title = f"tbh people are sleeping on {cat} right now"
        r_body = f"Honestly makes a lot of sense when u look at the bigger picture. btw found this deep dive here: <a href='{original_link}'>{original_link}</a> if u care."
    else:
        r_body = r_body.replace(original_link, f'<a href="{original_link}" style="color: #2563eb; text-decoration: underline;">{original_link}</a>')
        r_body = r_body.replace('[link]', f'<a href="{original_link}" style="color: #2563eb; text-decoration: underline;">here</a>')
        r_body = r_body.replace('\n', '<br>')
        
    clean_title = r_title.replace('<REDDIT_TITLE>', '').replace('</REDDIT_TITLE>', '')

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
                    <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 8px; margin-top: 15px;">
                        <span style="font-size: 14px; opacity: 0.9; display: block; margin-bottom: 4px;">🎯 AI 추천 타겟 커뮤니티:</span>
                        <strong style="font-size: 18px;">{target_subreddits}</strong>
                    </div>
                </div>
                <div style="padding: 30px;">
                    <h3 style="color: #64748b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; font-size: 13px; text-transform: uppercase;">Title 👇</h3>
                    <div style="padding: 15px; background: #f8fafc; color: #1e293b; font-weight: bold; font-size: 16px; border-left: 4px solid #ef4444; margin-bottom: 25px;">{clean_title}</div>
                    <h3 style="color: #64748b; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; font-size: 13px; text-transform: uppercase;">Body 👇</h3>
                    <div style="padding: 20px; background: #ffffff; color: #334155; border: 1px dashed #cbd5e1; line-height: 1.6;">{r_body}</div>
                </div>
            </div>
        </div>
        """
        msg.attach(MIMEText(body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ Community Viral Draft Email Sent!")
    except Exception as e: print(f"   ❌ Community Viral Draft Email Failed: {e}")

# ═══════════════════════════════════════════════
# ✉️ 슬림 이메일 (인스타/숏폼용)
# ═══════════════════════════════════════════════
def send_social_style_email(title, link, image_bytes_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes=None):
    if not EMAIL_SENDER or not EMAIL_RECEIVER: return
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
            <div style="text-align:center; margin-bottom: 20px;">
                <a href="{link}" style="display: inline-block; background-color: #0f1419; color: #ffffff; padding: 12px 24px; border-radius: 9999px; text-decoration: none; font-weight: bold; font-size: 15px;">Read Full Post on Website →</a>
            </div>
        </div>
        """
        msg.attach(MIMEText(body, 'html'))

        if video_mp4_bytes:
            part = MIMEBase('video', 'mp4')
            part.set_payload(video_mp4_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=f'WarmInsight_{cat}_Video.mp4')
            msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ Social Email Sent Successfully!")
    except Exception as e: print(f"   ❌ Social Email Failed: {e}")

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
    print(f"   🔍 [System] Bypassing WAF & Checking WP Connection to: {WP_URL}")
    try:
        scraper.get(WP_URL, timeout=30)
        time.sleep(2) 
    except Exception as e: pass
    
    resp = wp_api_call('GET', 'users/me')
    if resp and resp.status_code == 200:
        print("   ✅ WP Auth Successful! (Network Stable)")
        return True
    print(f"   ❌ WP Connection Failed.")
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
                time.sleep((15 * i) + random.uniform(-2, 5))
            elif "429" in err:
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
    r = wp_api_call('GET', f'categories?slug={slug}')
    if r and r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
    r2 = wp_api_call('POST', 'categories', json_data={"name": cat_name, "slug": slug})
    if r2 and r2.status_code in (200, 201): return r2.json()["id"]
    return None

def get_or_create_wp_tag(tag_name):
    slug = tag_name.lower().replace(" ", "-")
    r = wp_api_call('GET', f'tags?slug={slug}')
    if r and r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
    r2 = wp_api_call('POST', 'tags', json_data={"name": tag_name, "slug": slug})
    if r2 and r2.status_code in (200, 201): return r2.json()["id"]
    return None

def get_wp_author_id(author_full_string):
    search_name = author_full_string.split("&")[0].strip()
    r = wp_api_call('GET', f'users?search={search_name}')
    if r and r.status_code == 200:
        users = r.json()
        if len(users) > 0: return users[0]["id"]
    return None

def _get_latest_post_category_name():
    r = wp_api_call('GET', 'posts?per_page=1&status=publish')
    if r and r.status_code == 200:
        try: r_json = r.json()
        except: return None
        
        if isinstance(r_json, list) and len(r_json) > 0:
            cat_ids = r_json[0].get('categories', [])
            if not cat_ids: return None
            
            r_cats = wp_api_call('GET', 'categories?per_page=100')
            if r_cats and r_cats.status_code == 200:
                try: r_cats_json = r_cats.json()
                except: return None
                
                if isinstance(r_cats_json, list):
                    cat_map = {c['id']: c['name'] for c in r_cats_json}
                    for cid in cat_ids:
                        name = cat_map.get(cid)
                        if name in CATEGORIES:
                            return name
    except Exception as e: pass
    return None

def already_published_today(cat):
    cat_slug = cat.lower().replace(" ", "-")
    r = wp_api_call('GET', f'categories?slug={cat_slug}')
    if not r or r.status_code != 200: return False
    
    try:
        r_json = r.json()
        if not isinstance(r_json, list) or not r_json: return False
        cat_id = r_json[0]["id"]
    except: return False

    r2 = wp_api_call('GET', f'posts?categories={cat_id}&per_page=1&status=publish')
    if r2 and r2.status_code == 200:
        try:
            r2_json = r2.json()
            if isinstance(r2_json, list) and len(r2_json) > 0:
                latest_post = r2_json[0]
                post_date_gmt = latest_post.get("date_gmt", "")[:10] 
                today_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d")
                if post_date_gmt == today_utc:
                    print(f"   ⏭️  [{cat}] Anti-spam logic: Already published today.")
                    return True
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
        except Exception: pass
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

def _build_comment_cta(raw_data, cat="Market"):
    question = xtag(raw_data, "COMMENT_QUESTION").strip() or f"What are your thoughts on today's {cat} market? Let us know below!"
    return f"""
    <div style="background:{BG_LIGHT}; border:2px solid {GOLD}; border-radius:12px; padding:35px; margin:50px 0; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
        <p style="font-size:14px; font-weight:800; color:{GOLD}; text-transform:uppercase; letter-spacing:1.5px; margin:0 0 10px;">💬 Join the Conversation</p>
        <h3 style="margin-top:0; font-size:22px; color:{DARK}; margin-bottom:20px; line-height:1.4;">{question}</h3>
        <p style="font-size:16px; color:{SLATE}; margin-bottom:25px;">Share your insights or portfolio strategy with the Warm Insight community.</p>
        <a href="#respond" style="display:inline-block !important; background:{DARK} !important; color:#ffffff !important; padding:16px 35px !important; border-radius:8px !important; text-decoration:none !important; font-weight:700 !important; font-size:16px !important; line-height:normal !important; margin:0 auto !important; box-shadow:0 4px 6px rgba(0,0,0,0.1) !important;">Leave a Comment 👇</a>
    </div>
    """

def _build_data_table(raw_data, title="Market Dashboard"):
    if not raw_data: raw_data = "S&P 500 | 5,234 | UP | Index near recent highs"
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l and '---' not in l and 'Asset Name' not in l and 'Asset/Metric' not in l]
    if len(lines) < 2: lines = lines + ["S&P 500 | 5,234 | UP | Tech earnings boost", "Nasdaq 100 | 18,200 | UP | AI infrastructure growth"][:max(0, 2 - len(lines))]
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
        parts = [p.strip() for p in line.split('|') if p.strip()]
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

def build_html(tier, cat, raw, author, tf, title):
    html = f"""<div style="{F}">\n{_build_warm_index(raw)}"""
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
    html += f"""<p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:20px; text-transform:uppercase; letter-spacing:0.5px;">Disclaimer: AI-generated, human-edited educational content. Not financial advice. All decisions are your own.</p></div>"""
    return sanitize(html)

def get_font(url, filename):
    if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            resp = scraper.get(url, timeout=15)
            resp.raise_for_status()
            with open(filename, 'wb') as f: f.write(resp.content)
        except Exception: pass
    return filename

# 🚨 괴물 생성 원천 차단: 마시멜로/유령 캐릭터(해부학적 구조가 없는 둥근 형태) 적용 🚨
def generate_carousel_image(prompt_text):
    try:
        client = _get_gemini_client()
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt_text,
            config=types.GenerateImagesConfig(
                number_of_images=1, aspect_ratio="1:1", output_mime_type="image/jpeg"
            )
        )
        img_data = result.generated_images[0].image.image_bytes
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
        print(f"    ⚠️ Gemini Image Gen failed: {e}. Trying Pollinations...")

    prompt_encoded = urllib.parse.quote(prompt_text)
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1080&height=1080&nologo=true&seed={random.randint(1,100000)}"
    
    for attempt in range(3):
        try:
            resp = scraper.get(url, timeout=45)
            if resp.status_code == 200:
                ai_img_raw = Image.open(io.BytesIO(resp.content)).convert("RGBA")
                ai_img_raw = ai_img_raw.resize((1080, 1080), Image.LANCZOS)
                mask = Image.new("L", (1080, 1080), 255)
                mask_draw = ImageDraw.Draw(mask)
                for y in range(780, 1080):
                    alpha = int(255 - (y - 780) * (255 / 300))
                    mask_draw.line([(0, y), (1080, y)], fill=alpha)
                ai_img_raw.putalpha(mask)
                return ai_img_raw
        except Exception: time.sleep(3)
    return None

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
        "Economy": "A highly aesthetic, conceptual 3D illustration about global economy and stock markets. Cinematic lighting, minimalist composition, deep rich blue and gold colors. High-end financial magazine cover style. No text, no words, no letters.",
        "Politics": "A highly aesthetic, conceptual 3D illustration about geopolitics and global policy. Cinematic lighting, minimalist composition, deep red and dark slate colors. High-end political magazine cover style. No text, no words, no letters."
    }
    prompt = AI_PROMPTS.get(cat, AI_PROMPTS["Economy"])

    img = None
    use_ai_bg = False
    try:
        client = _get_gemini_client()
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg")
        )
        bg_bytes = result.generated_images[0].image.image_bytes
        img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA").resize((w, h), Image.LANCZOS)
        use_ai_bg = True
    except Exception as e:
        img = Image.new("RGBA", (w, h), style["bg1"])
        draw = ImageDraw.Draw(img)
        draw.ellipse([w*0.35, -h*0.5, w*1.5, h*1.5], fill=style["bg2"])

    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, h - 80 * SCALE), (w, h)], fill="#00000060")

    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    def lf(p, s):
        try: return ImageFont.truetype(p, s * SCALE)
        except: return ImageFont.load_default()

    ft, fs, fb = lf(ft_path, 85), lf(ft_path, 34), lf(ft_path, 28)
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
        try: bb = draw.textbbox((0, 0), ln, font=ft); y += (bb[3] - bb[1]) + 15 * S
        except: y += 100 * S

    date_bottom = datetime.datetime.utcnow().strftime("%B %d, %Y")
    draw.text((40 * S, h - 70 * S), f"WARM INSIGHT  |  {date_bottom}", font=fs, fill="#ffffff80")

    tagline = "AI-DRIVEN GLOBAL MARKET ANALYSIS"
    try: tw_t = draw.textlength(tagline, font=fs)
    except: tw_t = len(tagline) * 15 * S
    draw.text((w - 40 * S - tw_t, h - 70 * S), tagline, font=fs, fill="#ffffff80")

    img = img.convert("RGB").resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def make_medium_thumbnail(cat):
    print(f"    [AI] Generating Premium Editorial Thumbnail for Medium...")
    client = _get_gemini_client()
    prompt = "A highly aesthetic, conceptual 3D illustration about global economy and stock markets. Cinematic lighting, minimalist composition, deep rich blue and gold colors. High-end financial magazine cover style. No text, no words, no letters."
    try:
        result = client.models.generate_images(
            model='imagen-3.0-generate-002', prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg")
        )
        return result.generated_images[0].image.image_bytes
    except Exception as e:
        print(f"    ⚠️ Medium AI Image Gen failed. Generating fallback. ({e})")
        W, H = 1200, 630
        img = Image.new("RGBA", (W, H), "#0284c7")
        draw = ImageDraw.Draw(img)
        draw.ellipse([W*0.5, -H*0.2, W*1.3, H*1.2], fill="#0369a1")
        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

def generate_video_mp4(cat, hook_text, data_points, bg_frames, text_frames):
    print("   🎥 Generating 15-Sec Dynamic Dark Psychology Reels Video (Separated Layers)...")
    try:
        import numpy as np
        from moviepy.editor import ImageClip, CompositeVideoClip, concatenate_videoclips
    except ImportError as e:
        print(f"   ❌ MoviePy import failed: {e}")
        return None
    try:
        SLIDE_DURATION, CROSSFADE_DURATION = 2.6, 0.3
        ZOOM_START, ZOOM_END = 1.0, 1.06 
        clips = []
        for i in range(len(bg_frames)):
            bg_np = np.array(bg_frames[i].convert('RGB'))
            bg_clip = ImageClip(bg_np).set_duration(SLIDE_DURATION)
            if i % 2 == 0: bg_clip = bg_clip.resize(lambda t: ZOOM_START + (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            else: bg_clip = bg_clip.resize(lambda t: ZOOM_END - (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            bg_clip = bg_clip.set_position(('center', 'center'))

            txt_np = np.array(text_frames[i].convert('RGBA'))
            txt_clip = ImageClip(txt_np).set_duration(SLIDE_DURATION).set_position(('center', 'center'))
            
            comp_clip = CompositeVideoClip([bg_clip, txt_clip], size=(1080, 1920)).set_duration(SLIDE_DURATION)
            if i > 0: comp_clip = comp_clip.crossfadein(CROSSFADE_DURATION)
            clips.append(comp_clip)

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
        print(f"   ✅ Dark Psychology 15s Layered Video Extracted! ({len(mp4_bytes)/1024/1024:.1f}MB)")
        return mp4_bytes
    except Exception as e:
        print(f"   ❌ Video Encoding Failed: {e}")
        return None

def generate_vip_carousel(raw_content, cat):
    print("   🎨 Generating DYNAMIC 4-IMAGE Dark Psychology Carousel...")
    
    sys_inst = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
    You are a TOP-TIER viral content creator for finance Instagram/TikTok. 
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
    raw_data = gem_fb("Premium", raw_content, sys_inst)

    hook_text = xtag(raw_data, "HOOK") or "Wall Street Just Did THIS 🚨"
    shock_stat = xtag(raw_data, "SHOCK_STAT") or "$2.3T MOVED OVERNIGHT"
    question_text = xtag(raw_data, "QUESTION") or "Where's YOUR money going? 👇"
    insight_line = xtag(raw_data, "INSIGHT_LINE") or "SMART MONEY IS MOVING NOW"
    cta_hook = xtag(raw_data, "CTA_HOOK") or "DONT MISS THE NEXT MOVE"
    reels_script = xtag(raw_data, "REELS_SCRIPT") or "Script generation failed."
    ig_caption = xtag(raw_data, "IG_CAPTION") or f"{hook_text}\n\nLink in bio for the full breakdown."
    smart_comment = xtag(raw_data, "SMART_COMMENT") or "Interesting market shift."
    
    colors_neon = [
        ("neon red", "red"), ("neon orange", "orange"),
        ("neon purple", "purple"), ("neon green", "green"),
        ("neon yellow", "yellow")
    ]
    random.shuffle(colors_neon)
    
    # 🚨 가장 확실한 해결책: 인간형 '졸라맨'을 버리고 '마시멜로 캐릭터'로 종(Species)을 완전히 교체
    # 관절, 손가락, 얼굴 이목구비의 디테일을 요구하지 않는 부드러운 덩어리 형태(마시멜로)로 지정하여 기괴한 환각을 0%로 만듭니다.
    vp_base = "A masterpiece 3D render of an incredibly cute, friendly little white marshmallow mascot character. It has a smooth, perfectly round body, two big adorable black eyes, and tiny stubby arms. It looks like a high-end designer art toy. Pitch-black studio background."

    vp1 = f"{vp_base} The cute marshmallow mascot is enthusiastically holding a brightly glowing {colors_neon[0][0]} neon upward arrow. The vibrant {colors_neon[0][1]} light reflects beautifully on its glossy white face. Ultra-cute, pop-mart blind box style."

    vp2 = f"{vp_base} The cute marshmallow mascot is holding a brightly glowing {colors_neon[1][0]} neon laser wand, pointing it forward like a friendly guide. The vibrant {colors_neon[1][1]} light reflects beautifully on its glossy white face. Ultra-cute, pop-mart blind box style."

    vp3 = f"{vp_base} The cute marshmallow mascot is looking at a brightly glowing {colors_neon[2][0]} neon chart line hovering in the air. The vibrant {colors_neon[2][1]} light reflects beautifully on its glossy white face. Ultra-cute, pop-mart blind box style."

    vp4 = f"{vp_base} The cute marshmallow mascot is standing happily next to a brightly glowing {colors_neon[3][0]} neon light beam. The vibrant {colors_neon[3][1]} light reflects beautifully on its glossy white face. Ultra-cute, pop-mart blind box style."

    data_points = []
    for i in range(1, 6):
        item = xtag(raw_data, f"ITEM{i}")
        if item and "|" in item:
            parts = item.split("|")
            raw_ticker = parts[0].strip()
            if len(raw_ticker) > 20: raw_ticker = raw_ticker[:18] + ".."
            data_points.append({"ticker": raw_ticker, "val": parts[1].strip()})

    if len(data_points) < 5:
        data_points = [
            {"ticker": "$NVDA", "val": "+6.2%"}, {"ticker": "$AAPL", "val": "+5.3%"},
            {"ticker": "$MSFT", "val": "+4.9%"}, {"ticker": "$BTC", "val": "+4.2%"},
            {"ticker": "$ETH", "val": "+2.3%"}
        ]

    W, H = 1080, 1920
    BG, WHITE, RED, GRAY = "#000000", "#ffffff", "#ef4444", "#94a3b8"

    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    def lf(p, s):
        try: return ImageFont.truetype(p, s)
        except: return ImageFont.load_default()

    font_title, font_mega, font_sub, font_data, font_alert = lf(ft_path, 95), lf(ft_path, 200), lf(ft_path, 55), lf(ft_path, 50), lf(ft_path, 75)

    print("    [AI] Requesting 4 unique images for Dynamic Storytelling...")
    img_hook_ai = generate_carousel_image(vp1)
    img_stat_ai = generate_carousel_image(vp2)
    img_data_ai = generate_carousel_image(vp3)
    img_out_ai  = generate_carousel_image(vp4)

    last_good_img = None
    for img in [img_hook_ai, img_stat_ai, img_data_ai, img_out_ai]:
        if img: last_good_img = img; break
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
            for r in range(400, 0, -10):
                alpha = int(255 * (1 - r/400))
                d.ellipse([540-r, 500-r, 540+r, 500+r], fill=(245, 158, 11, alpha))
            mask = Image.new("L", (1080, 1080), 255)
            mask_draw = ImageDraw.Draw(mask)
            for y in range(780, 1080):
                alpha = int(255 - (y - 780) * (255 / 300))
                mask_draw.line([(0, y), (1080, y)], fill=alpha)
            fallback_img.putalpha(mask)
            d_img.paste(fallback_img, (0, 100), fallback_img)
            
        dark_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 75)) 
        d_img.paste(dark_overlay, (0, 0), dark_overlay)

    def wrap_lines(text, font, max_width):
        words = text.split()
        lines, line, d = [], [], ImageDraw.Draw(Image.new("RGB", (1,1)))
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

    bg_frames, text_frames = [], []

    # Slide 1
    bg1 = Image.new("RGB", (W, H), BG)
    paste_bg(bg1, img_hook_ai)
    bg_frames.append(bg1)

    txt1 = Image.new("RGBA", (W, H), (0,0,0,0)) 
    d1 = ImageDraw.Draw(txt1)
    d1.rounded_rectangle([300, 1150, 780, 1250], radius=20, fill=RED)
    d1.text((W//2, 1200), f"🚨 {cat.upper()} ALERT", fill=WHITE, font=font_alert, anchor="mm")
    hook_lines = wrap_lines(hook_text.upper(), font_title, 950) 
    y_text = 1350
    for i, ln in enumerate(hook_lines[:4]):
        d1.text((W//2, y_text), ln, fill=(RED if i == len(hook_lines)-1 else WHITE), font=font_title, anchor="mm")
        y_text += 105 
    d1.text((W//2, 1800), "↓ SWIPE TO SEE WHY ↓", fill=GRAY, font=font_sub, anchor="mm")
    text_frames.append(txt1)

    # Slide 2
    bg2 = Image.new("RGB", (W, H), BG)
    paste_bg(bg2, img_stat_ai)
    bg_frames.append(bg2)

    txt2 = Image.new("RGBA", (W, H), (0,0,0,0))
    d2 = ImageDraw.Draw(txt2)
    d2.text((W//2, 1180), "THE NUMBER", fill=RED, font=font_sub, anchor="mm")
    shock_lines = wrap_lines(shock_stat.upper(), font_mega, 950)
    y_text = 1350
    for ln in shock_lines[:3]:
        d2.text((W//2, y_text), ln, fill=WHITE, font=font_mega, anchor="mm")
        y_text += 140 
    d2.text((W//2, 1800), "WAIT FOR IT...", fill=GRAY, font=font_sub, anchor="mm")
    text_frames.append(txt2)

    # Data Slides
    for idx in range(3):
        if idx >= len(data_points): break
        item = data_points[idx]
        
        bg_d = Image.new("RGB", (W, H), BG)
        paste_bg(bg_d, img_data_ai)
        bg_frames.append(bg_d)

        txt_d = Image.new("RGBA", (W, H), (0,0,0,0))
        d = ImageDraw.Draw(txt_d)
        d.text((W//2, 1150), cat.upper(), fill=RED, font=font_sub, anchor="mm")
        d.text((W//2, 1250), f"WATCH THIS → {idx+1}/3", fill=GRAY, font=font_data, anchor="mm")
        
        t_size = min(95, int(95 * (12 / max(len(item['ticker']), 1))))
        d.text((W//2, 1400), item['ticker'], fill=WHITE, font=lf(ft_path, max(45, t_size)), anchor="mm")
        
        v_size = min(200, int(200 * (6 / max(len(item['val']), 1))))
        d.text((W//2, 1550), item['val'], fill=(RED if '-' in item['val'] else WHITE), font=lf(ft_path, max(70, v_size)), anchor="mm")
        
        for di in range(3):
            dx = W//2 + (di - 1) * 60
            d.ellipse([dx-15, 1800-15, dx+15, 1800+15], fill=(RED if di == idx else "#3f3f46"))
        text_frames.append(txt_d)

    # Slide 6
    bg6 = Image.new("RGB", (W, H), BG)
    paste_bg(bg6, img_out_ai)
    bg_frames.append(bg6)

    txt6 = Image.new("RGBA", (W, H), (0,0,0,0))
    d6 = ImageDraw.Draw(txt6)
    d6.text((W//2, 1150), "THE TAKEAWAY", fill=RED, font=font_sub, anchor="mm")
    insight_lines = wrap_lines(insight_line.upper(), font_title, 950)
    y_text = 1250
    for ln in insight_lines[:3]:
        d6.text((W//2, y_text), ln, fill=WHITE, font=font_title, anchor="mm")
        y_text += 105
    d6.text((W//2, 1650), cta_hook.upper(), fill=RED, font=font_alert, anchor="mm")
    d6.text((W//2, 1780), "LINK IN BIO → @WARMINSIGHT", fill=GRAY, font=font_sub, anchor="mm")
    text_frames.append(txt6)

    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, bg_frames, text_frames)
    return [], data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes

def _upload_image(img_bytes, filename):
    try:
        headers = _get_wp_headers()
        headers.update({"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"})
        resp = scraper.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers=headers, 
            data=img_bytes, timeout=30
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

    tag_id = get_or_create_wp_tag("Insight") if tier == "unified" else get_or_create_wp_tag("Pro")
    author_id = get_wp_author_id(author_name)
    display_title = title if cat in ["Foundation", "The Daily Catalyst", "Money Hack"] or tier == "unified" else f"[Pro] {title}"

    post_data = {
        "title": display_title, "content": html, "status": "publish", "slug": slug,
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
        r = scraper.post(f"{WP_URL}/wp-json/wp/v2/posts", headers=_get_wp_headers(), json=post_data, timeout=30)
        if r.status_code in (200, 201):
            try: link = r.json().get('link')
            except: link = None
            if link:
                print(f"   ✅ Published: {link}")
                if raw_for_cards:
                    if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
                        if tier in ["Premium", "unified"]:
                            img_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes = generate_vip_carousel(raw_for_cards, cat)
                            if video_mp4_bytes:
                                send_social_style_email(display_title, link, img_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes)
                        yt_meta, yt_script = generate_youtube_masterpiece(raw_for_cards, title)
                        if yt_script: send_youtube_script_email(title, yt_meta, yt_script)
                    send_medium_draft_email(display_title, link, raw_for_cards, cat, kw, med_img_bytes)
                    send_community_viral_email(display_title, link, raw_for_cards, cat)
                return True
        else: print(f"   ❌ Publish failed. HTTP Status: {r.status_code}")
    except Exception as e: print(f"   ❌ Network error: {e}")
    return False

def run_news_pipeline(forced_cat=None):
    current_time = datetime.datetime.utcnow()
    day_of_week = current_time.weekday()
    day_of_year = current_time.timetuple().tm_yday
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"

    if forced_cat: cat = forced_cat
    elif day_of_week in (1, 3): cat = "On-Chain"
    else:
        base_cats = [c for c in CATEGORIES if c not in ["On-Chain", "Money Hack"]]
        cat = base_cats[day_of_year % len(base_cats)]

    print(f"🚀 Starting v46.9.123_MARSHMALLOW_MASCOT_ENGINE Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    if not force and already_published_today(cat): return

    all_news = fetch_news_pool(cat)
    if len(all_news) < 2: return

    news_str = "\n".join(all_news)
    tier = "unified"

    raw1 = gem_fb(tier, PROMPT_UNIFIED_P1.replace("{cat}", cat).replace("{news}", news_str))
    if not raw1: return

    ctx = "Title: " + xtag(raw1, "TITLE") + "\nSummary: " + xtag(raw1, "EXECUTIVE_SUMMARY")
    raw2 = gem_fb(tier, PROMPT_UNIFIED_P2.replace("{cat}", cat).replace("{ctx}", ctx))
    raw = raw1 + "\n" + raw2 if raw2 else raw1

    title, kw, exc = xtag(raw, "TITLE"), xtag(raw, "SEO_KEYWORD"), xtag(raw, "EXCERPT") or xtag(raw, "EXECUTIVE_SUMMARY")
    slug = make_slug(kw, title, cat)
    author = VIP_AUTHORS.get(cat, "Warm Insight Editorial Team")
    tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
    
    html = build_html(tier, cat, raw, author, tf, title)
    img_bytes = make_thumbnail(title, cat, tier)
    if not img_bytes or len(img_bytes) < 1000: return
        
    med_img_bytes = make_medium_thumbnail(cat)
    publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)
    time.sleep(TIER_SLEEP[tier])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "philosophy": pass
        elif arg == "foundation": pass
        elif arg == "moneyhack": pass
        elif arg == "onchain": run_news_pipeline("On-Chain")
        elif arg == "insight": run_news_pipeline()
    else:
        run_news_pipeline()
