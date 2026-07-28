#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — Ultimate Masterpiece Edition (v46.9.64)
#
# 숏폼(Reels) 엔진 V3 업데이트 사항:
# 1. 픽사(Pixar) 스타일의 친근하고 단순한 3D 화이트 로봇 마스코트 적용 유지 (놀람->분석->따봉 3단계 분리)
# 2. 타이포그래피 컬러 Mix: 빨간색(#ef4444)과 골드색(#fde047)의 전략적 교차 배치
#    (알림/경고/하락/CTA는 빨간색 + 주요텍스트/상승/페이지도트는 골드색으로 혼합하여 다이내믹 & 가독성 극대화)
# 3. 텍스트 가독성 극대화: 이미지 하단(y=700~1080) 블랙 페이드아웃 마스크 적용
# 4. NameError 방지: 사용자의 3중 반복 원본 구조를 100% 완벽 보존하여 스코프 에러 원천 차단
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
    print("❌ [System Error] 'cloudscraper' 라이브러리가 설치되지 않았습니다. GitHub Actions의 pip install에 cloudscraper를 추가해주세요.")
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
# 🎬 1. YOUTUBE CHAPTERING ENGINE
# ═══════════════════════════════════════════════
YT_META_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Based on the following newsletter content, generate a YouTube Metadata package in ENGLISH.
Avoid generic AI buzzwords. Sound like a human growth hacker.

[CONTENT]
{raw_content}

[REQUIREMENTS]
You must strictly use these XML tags:

<METADATA>
[VIRAL TITLES]
(Exactly 3 options. Make them hyper-clickable using a 'Curiosity Gap' or 'Ultimate Benefit'. Use specific numbers. Banned words: 'Unleash', 'Discover', 'Secret')
- Option A: 
- Option B: 
- Option C: 

[THUMBNAIL IDEAS]
1. Visual Prompt: (Generate a HYPER-DETAILED, professional AI image generation prompt for Midjourney/Vrew. NO TEXT IN PROMPT.)
2. Text/Copy: (Write 2-4 words of MASSIVE IMPACT, click-inducing text to place directly ON the thumbnail. e.g., "SELL NOW?", "IT'S OVER.", "THE TRUTH")

[SEO HASHTAGS]
(10 highly searched global tags, e.g. #investing #economy)
</METADATA>"""

YT_SCRIPT_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are a top-tier YouTube Scriptwriter for "Warm Insight". Write PART 1 of a massive 20,000+ character documentary script based on the newsletter in ENGLISH.
Focus on: Cold Open Hook, Greeting, and Chapter 1 (Current Situation Analysis).
ANTI-AI FATIGUE: Do NOT sound like an AI. Be punchy, direct, and slightly informal. Use analogies.
[NEWSLETTER]
{raw_content}

Rules: 
- OUTPUT ONLY SPOKEN WORDS IN ENGLISH. NO structural tags like [VO], [Scene 1]. ONLY text to be read by TTS.
- Start immediately with a provocative cold open hook (e.g. "If you think [X] is safe, look at this number..."), followed by: "Hello, this is Warm Insight. Today, we're going to talk about [Topic]. Leaving a like and subscribing is a huge help to us!"
Wrap in <PART1> tags."""

YT_SCRIPT_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Continue the English script from Part 1 seamlessly. Write PART 2: Chapter 2 & 3 (Historical Context & Deep Dive).
You MUST expand massively using verified historical context (compare it to 2008, 1999, or 1970s). Provide CONCRETE numbers, not generalizations.
Do not summarize; spend at least 500 words on EACH historical comparison or context point.
Rules: Spoken words ONLY in English. NO structural tags. NO AI fluff ("in today's ever-changing landscape").
Wrap in <PART2> tags."""

YT_SCRIPT_P3 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Complete the English script. Write PART 3: Chapter 4 & Outro (Future Prediction & Action Plan).
Provide concrete, counterintuitive strategies. Tell them exactly what NOT to do.
Rules: Spoken words ONLY in English. NO structural tags.
End exactly with: "We couldn't fit all the deep-dive details and practical strategies into this video. Check out the Warm Insight newsletter in the pinned comment and description for the full text summary. Visit www.warminsight.com. See you there."
Wrap in <PART3> tags."""

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
