#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — Ultimate Masterpiece Edition (v46.9.36)
#
# 핵심 복구 및 변경 사항:
#   1. [언어 통제] 글로벌 오디언스를 위한 100% 영문(English) 출력 프롬프트 강제 적용
#   2. [신규 카테고리] 'On-Chain' 카테고리 추가 및 영미권 최상위 크립토 RSS 연동
#   3. [스마트 스케줄링] 매주 화요일, 목요일 'On-Chain' 고정 발행 알고리즘 탑재
#   4. [디자인 픽스] Founder Note를 최상단(Warm Index 직후)으로 이동 및 하단 중복 제거
#   5. [디자인 픽스] On-Chain 등 텍스트 누락 시 Poll(투표창)이 깨지지 않도록 강력한 Fallback 추가
#   6. [SEO 픽스] Foundation 카테고리 롱테일(Long-tail) 키워드 타겟팅 및 클릭 유도 프롬프트 강화
#   7. [SEO 픽스] 전 카테고리(Insight, On-Chain, Catalyst) 프리미엄 호기심 유발(Curiosity Gap) 로직 적용
#   8. [UX 픽스] 실전 중심 Action Plan 프롬프트 강화 및 Executive Summary 바로 밑으로 배치 변경
#   9. [언어 픽스] Action Plan 박스 내 하드코딩된 한글 서브타이틀 영문으로 완전 교체 및 하단 중복 코드 제거
#  10. [신규 파이프라인] 'Money Hack' 카테고리 전용 부업/실전 챌린지 자동화 파이프라인 추가 탑재
#  11. [엔진 픽스] Money Hack 무한 주제 생성 엔진(Infinite Topic Engine) 탑재 (5년+ 무중단 자동화)
#  12. [UX 픽스] 투표창 하단 댓글 유도 문구를 실제 댓글창 바로 위(뉴스레터 최하단)로 이동
#  13. [SEO 픽스] 전 카테고리 H2/H3 태그에 포커스 키워드(SEO_KEYWORD)를 동적으로 결합하여 On-Page SEO 극대화
#  14. [통신 픽스] Imunify360 WAF 차단 원천 해결: WP 내부 통신(Loopback)으로 위장하는 WordPress User-Agent 탑재
#  15. [API 픽스] 404 NOT_FOUND 에러 해결을 위해 Imagen 모델을 최신 버전(imagen-3.0-generate-002)으로 업데이트
#  16. [신규 파이프라인] Medium(미디엄) 유기적 트래픽 유입을 위한 Teaser Draft 이메일 자동 발송 기능 추가
#  17. [버그 픽스] SOCIAL_LINKS 변수를 최상단 CONFIG 영역에 고정하여 NameError 완벽 해결
#  18. [UX 픽스] Medium Draft 이메일의 복사 영역을 미디엄 에디터에 완벽 호환되는 '순정 HTML' 구조로 개조 및 클렌징
#  19. [마케팅 기능] Medium 이메일 내에 '대형+소형 SEO 키워드' 기반의 추천 태그(Topics) 5개 자동 생성 기능 추가
#  20. [마케팅 픽스] Medium 썸네일 누락 해결을 위해, 생성된 AI 썸네일 이미지를 Draft 이메일에 파일로 자동 첨부
#  21. [유튜브 픽스] 유튜브 썸네일 프롬프트에 시선을 사로잡는 강력한 텍스트(Text/Copy) 추천 항목 추가
#  22. [마케팅 기능] 미디엄 전용(Medium Only) 하이엔드 에디토리얼 썸네일 독립 생성 엔진 탑재
#  23. [버그 픽스] AI 썸네일 생성 실패 시 웹사이트 썸네일을 재사용하지 않고, 파이썬 기반의 '텍스트 없는' 추상적 디자인 썸네일 강제 생성 로직 추가
#  24. [확장] 365 챌린지 유입 극대화를 위해 Foundation, Catalyst, Money Hack 카테고리도 모두 Medium Draft 이메일 발송되도록 파이프라인 전면 개조
# ═══════════════════════════════════════════════════════════════

import os, sys, traceback, time, random, re, datetime, io, math
import urllib.request
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

[CONTENT]
{raw_content}

[REQUIREMENTS]
You must strictly use these XML tags:

<METADATA>
[VIRAL TITLES]
(Exactly 3 options. Make them hyper-clickable using a 'Curiosity Gap' or 'Ultimate Benefit'.)
- Option A: 
- Option B: 
- Option C: 

[THUMBNAIL IDEAS]
1. Visual Prompt: (Generate a HYPER-DETAILED, professional AI image generation prompt for Midjourney/Vrew.)
2. Text/Copy: (Write 2-4 words of MASSIVE IMPACT, click-inducing text to place directly ON the thumbnail. e.g., "SELL NOW?", "IT'S OVER.", "THE TRUTH")

[SEO HASHTAGS]
(10 highly searched global tags, e.g. #investing #economy)
</METADATA>"""

YT_SCRIPT_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are a top-tier YouTube Scriptwriter for "Warm Insight". Write PART 1 of a massive 20,000+ character documentary script based on the newsletter in ENGLISH.
Focus on: Cold Open Hook, Greeting, and Chapter 1 (Current Situation Analysis).
EXPAND DEEPLY. Use analogies and psychological insights.
[NEWSLETTER]
{raw_content}

Rules: 
- OUTPUT ONLY SPOKEN WORDS IN ENGLISH. NO structural tags like [VO], [Scene 1]. ONLY text to be read by TTS.
- Start immediately with a provocative cold open hook, followed by: "Hello, this is Warm Insight. Today, we're going to talk about [Topic]. Leaving a like and subscribing is a huge help to us!"
Wrap in <PART1> tags."""

YT_SCRIPT_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Continue the English script from Part 1 seamlessly. Write PART 2: Chapter 2 & 3 (Historical Context & Deep Dive).
You MUST expand massively using verified historical context (compare it to 2008, 1999, or 1970s).
Do not summarize; spend at least 500 words on EACH historical comparison or context point.
Rules: Spoken words ONLY in English. NO structural tags.
Wrap in <PART2> tags."""

YT_SCRIPT_P3 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Complete the English script. Write PART 3: Chapter 4 & Outro (Future Prediction & Action Plan).
Provide concrete strategies.
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
# ✉️ Medium Teaser Draft 자동 생성 및 발송 엔진 (범용 카테고리 지원)
# ═══════════════════════════════════════════════
def send_medium_draft_email(title, original_link, raw_content, cat, kw, img_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS: return
    print(f"   📧 Generating and Sending Medium Draft to {MEDIUM_EMAIL_RECEIVER}...")
    
    # 🚨 카테고리별로 각기 다른 XML 구조를 해석하여 미디엄 초안 생성
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
        # Insight, On-Chain 등 정규 뉴스 카테고리
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
# ✉️ 슬림 이메일 (인스타/숏폼용)
# ═══════════════════════════════════════════════
def send_social_style_email(title, link, image_bytes_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS or not EMAIL_RECEIVER:
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
                <p style="color: #10b981; font-weight: 900; font-size: 18px; margin-top: 0; text-transform: uppercase;">🎬 20-Sec Reels Video Attached!</p>
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
                pass

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
        return False
    return True

def verify_wp_credentials():
    print(f"   🔍 [System] Checking WP Connection to: {WP_URL}")
    try:
        resp = requests.get(f"{WP_URL}/wp-json/wp/v2/users/me", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=25)
        try:
            resp_json = resp.json()
            is_valid_json = isinstance(resp_json, dict) and "id" in resp_json
        except:
            is_valid_json = False

        if resp.status_code == 200 and is_valid_json: 
            print("   ✅ WP Auth Successful!")
            return True
        else:
            print(f"   ❌ WP Auth Failed! (HTTP Status: {resp.status_code})")
    except Exception as e: 
        print(f"   ❌ WP Connection Error: {e}")
    return False

def call_gemini(client, model, prompt, sys_inst=None, retries=5):
    if not sys_inst:
        sys_inst = "You are an elite financial analyst. ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN."

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
            if "credits are depleted" in err or "billing" in err.lower(): return None
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

def _get_latest_post_category_name():
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/posts?per_page=1&status=publish", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200:
            try: r_json = r.json()
            except: return None
            
            if isinstance(r_json, list) and len(r_json) > 0:
                cat_ids = r_json[0].get('categories', [])
                if not cat_ids: return None
                
                r_cats = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=100", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
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
        pass
    return None

def already_published_today(cat):
    try:
        cat_slug = cat.lower().replace(" ", "-")
        r = requests.get(
            f"{WP_URL}/wp-json/wp/v2/categories?slug={cat_slug}", headers=WP_API_HEADERS,
            auth=(WP_USER, WP_APP_PASS), timeout=15
        )
        if r.status_code != 200: return False
        
        try:
            r_json = r.json()
            if not isinstance(r_json, list) or not r_json: return False
            cat_id = r_json[0]["id"]
        except: return False

        r2 = requests.get(
            f"{WP_URL}/wp-json/wp/v2/posts", headers=WP_API_HEADERS,
            params={"categories": cat_id, "per_page": 1, "status": "publish"},
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
                        print(f"   ⏭️  [{cat}] Anti-spam logic: Already published today.")
                        return True
            except: pass
    except Exception as e:
        pass
    return False

# ═══════════════════════════════════════════════
# 📰 NEWS POOLING
# ═══════════════════════════════════════════════
def fetch_news_pool(cat, max_items=15):
    feeds = RSS_FEEDS.get(cat, RSS_FEEDS["Economy"])
    items = set()
    for url in feeds:
        try:
            resp = requests.get(url, headers=EXTERNAL_HEADERS, timeout=15)
            if resp.status_code == 200:
                d = feedparser.parse(resp.text)
                for e in d.entries[:40]:
                    title = getattr(e, 'title', '').strip()
                    summary = re.sub(r'<[^>]+>', '', getattr(e, 'summary', ''))[:200].strip()
                    if title and len(title) > 10: items.add(f"• {title}: {summary}")
        except Exception as ex:
            pass
            
    items_list = list(items)
    random.shuffle(items_list)
    return items_list[:max_items]

# ═══════════════════════════════════════════════
# 🧠 PROMPTS
# ═══════════════════════════════════════════════
FOUNDATION_TOPICS = [
    "ETF vs Mutual Funds: Which is actually safer for absolute beginners?",
    "How to start investing in S&P 500 ETFs with exactly $100",
    "The hidden risks of Dollar Cost Averaging (DCA) you must know"
]
FOUNDATION_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are the "smart friend" who explains money to absolute beginners. Use specific analogies. Format EXACTLY using the provided XML tags."""
FOUNDATION_PROMPT = """Write an SEO-optimized beginner's guide on: {theme}
<TITLE>(Max 60 chars. Include SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Specific long-tail keyword)</SEO_KEYWORD>
<EXCERPT>(Curiosity gap meta description)</EXCERPT>
<DEFINITION>(2 paragraphs with an analogy)</DEFINITION>
<WHY_MATTERS>(2 paragraphs)</WHY_MATTERS>
<HOW_TO_START>(3 actionable steps)</HOW_TO_START>
<POLL_QUESTION>(Question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

PHILOSOPHY_TOPICS = [
    "Love money through action, not just unrequited longing",
    "The psychological vessel of wealth and the weight of responsibility"
]
PHILOSOPHY_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are an elite philosophical life strategist. Direct, concise, unapologetic."""
PHILOSOPHY_PROMPT = """Write a philosophical daily insight on: {theme}
<TITLE>(Max 60 chars. Include SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Specific long-tail keyword)</SEO_KEYWORD>
<EXCERPT>(Curiosity gap meta description)</EXCERPT>
<ANCHOR>(One-sentence principle)</ANCHOR>
<REFLECTION>(3-4 paragraphs)</REFLECTION>
<CATALYST>(One provocative question)</CATALYST>
<POLL_QUESTION>(Question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

MH_NICHES = ["Digital Products", "E-commerce", "Content Creation"]
MH_PLATFORMS = ["Gumroad", "Shopify", "YouTube"]
MH_AI_TOOLS = ["ChatGPT", "Midjourney", "Claude"]
MONEY_HACK_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are an elite side-hustle expert."""
MONEY_HACK_PROMPT = """Write a side hustle guide based on: {theme}
<TITLE>(Max 60 chars. Include SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Specific long-tail keyword)</SEO_KEYWORD>
<EXCERPT>(Curiosity gap meta description)</EXCERPT>
<CONCEPT>(2 paragraphs)</CONCEPT>
<STEP_BY_STEP_TOOL>(1-2-3 checklist)</STEP_BY_STEP_TOOL>
<PRO_TIP>(1 paragraph secret tip)</PRO_TIP>
<POLL_QUESTION>(Question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

PROMPT_UNIFIED_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write PART 1 of an Insight newsletter on {cat} in ENGLISH based on this news:
{news}
<TITLE>(Max 60 chars. Include SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Specific long-tail keyword)</SEO_KEYWORD>
<EXCERPT>(Curiosity gap meta description)</EXCERPT>
<WARM_INDEX_SCORE>(0-100 number)</WARM_INDEX_SCORE>
<WARM_INDEX_REASON>(5-10 word explanation)</WARM_INDEX_REASON>
<IMPACT>(HIGH, MEDIUM, or LOW)</IMPACT>
<DATA_TABLE>(Asset | Price | UP/DOWN/SIDEWAYS | Insight)</DATA_TABLE>
<HEATMAP>(Sector | Number)</HEATMAP>
<EXECUTIVE_SUMMARY>(3 sentences. Counterintuitive thesis)</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>(3-4 sentences. Specific analogy)</PLAIN_ENGLISH>
<HEADLINE>(Analytical headline)</HEADLINE>
<MACRO>(2 paragraphs. What and Why)</MACRO>
<HERD>(1 paragraph. Retail behavior)</HERD>
<CONTRARIAN>(1 paragraph. Smart money behavior)</CONTRARIAN>
<QUICK_FLOW>(Chain of events ➡️)</QUICK_FLOW>"""

PROMPT_UNIFIED_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write PART 2 of the Insight newsletter for {cat} in ENGLISH. Context:
{ctx}
<BULL_CASE>(3-4 sentences)</BULL_CASE>
<BEAR_CASE>(3-4 sentences)</BEAR_CASE>
<HISTORICAL_PARALLEL>(2 sentences)</HISTORICAL_PARALLEL>
<QUICK_HITS>(3 bullets starting with emoji)</QUICK_HITS>
<SMART_MONEY_MOVE>(1 paragraph. Name ticker)</SMART_MONEY_MOVE>
<DO_ACTION>(Specific strategy for beginners)</DO_ACTION>
<DONT_ACTION>(1 critical mistake to avoid)</DONT_ACTION>
<TAKEAWAY>(Bottom line under 20 words)</TAKEAWAY>
<PS>(One-line veteran advice)</PS>
<POLL_QUESTION>(Question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

# ═══════════════════════════════════════════════
# 📊 VISUAL DATA BUILDERS & HTML
# ═══════════════════════════════════════════════
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
            <div style="background:{grad}; height:100%; width:{score}%; border-radius:5px;"></div>
        </div>
        <p style="margin:0; font-size:14px; color:{SLATE}; font-style:italic; text-align:center;">"{reason}"</p>
    </div>
    """

def _build_poll(raw_data, cat="Market"):
    question = xtag(raw_data, "POLL_QUESTION").strip() or f"What is your perspective on today's {cat} news?"
    opt1 = xtag(raw_data, "POLL_OPT1").strip() or "Bullish – I see an opportunity."
    opt2 = xtag(raw_data, "POLL_OPT2").strip() or "Neutral – Waiting for more signals."
    opt3 = xtag(raw_data, "POLL_OPT3").strip()
    opt3_html = f"""<a href="#respond" style="display:block; background:#ffffff; border:2px solid {BORDER}; color:{DARK}; padding:14px; border-radius:8px; text-decoration:none; font-weight:700; font-size:16px;">{opt3}</a>""" if opt3 else ""

    return f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:12px; padding:30px; margin:50px 0; text-align:center;">
        <h3 style="margin-top:0; font-size:22px; color:{DARK}; margin-bottom:20px;">🗳️ What's your take?</h3>
        <p style="font-size:18px; font-weight:600; color:{SLATE}; margin-bottom:25px;">"{question}"</p>
        <div style="display:flex; flex-direction:column; gap:12px; max-width:400px; margin:0 auto;">
            <a href="#respond" style="display:block; background:#ffffff; border:2px solid {BORDER}; color:{DARK}; padding:14px; border-radius:8px; text-decoration:none; font-weight:700; font-size:16px;">{opt1}</a>
            <a href="#respond" style="display:block; background:#ffffff; border:2px solid {BORDER}; color:{DARK}; padding:14px; border-radius:8px; text-decoration:none; font-weight:700; font-size:16px;">{opt2}</a>
            {opt3_html}
        </div>
    </div>
    """

def _build_data_table(raw_data, title="Market Dashboard"):
    if not raw_data: raw_data = "S&P 500 | 5,234 | UP | Index near recent highs\nNasdaq 100 | 18,200 | UP | Tech leading"
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    
    html = f"""
    <div style="background:#ffffff; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; font-size:20px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:12px;">📊 {title}</h3>
        <div style="overflow-x:auto; margin-top:15px;">
        <table style="width:100%; border-collapse:collapse; font-family:-apple-system,sans-serif;">
            <thead>
                <tr style="background:{BG_LIGHT}; text-align:left; border-bottom:2px solid {BORDER};">
                    <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Asset</th>
                    <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Status</th>
                    <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Trend</th>
                    <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Insight</th>
                </tr>
            </thead>
            <tbody>
    """
    for line in lines[:5]:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            asset, value, trend, insight = parts[:4]
            t_upper = trend.upper()
            if "UP" in t_upper or "BULL" in t_upper: t_color, t_icon = "#10b981", "🟢"
            elif "DOWN" in t_upper or "BEAR" in t_upper: t_color, t_icon = "#ef4444", "🔴"
            else: t_color, t_icon = "#f59e0b", "🟡"
            html += f"""<tr style="border-bottom:1px solid {BORDER};">
                <td style="padding:14px; font-weight:600; color:{DARK};">{asset}</td>
                <td style="padding:14px; color:{SLATE}; font-family:monospace; font-weight:bold;">{value}</td>
                <td style="padding:14px; font-weight:bold; color:{t_color};">{t_icon} {trend.upper()}</td>
                <td style="padding:14px; color:{MUTED};">{insight}</td>
            </tr>"""
    html += "</tbody></table></div></div>"
    return html

def _build_progress_bars(raw_data, title="Sector Risk Heatmap"):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""

    html = f"""<div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;">
        <h3 style="margin-top:0; font-size:20px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:12px;">🌡️ {title}</h3>"""
    colors = ["#dc2626", "#ea580c", "#ca8a04", "#059669", "#3b82f6"]

    for line in lines[:5]:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:
            name = parts[0]
            try: pct = int(re.sub(r'[^0-9]', '', parts[1]))
            except: pct = 50
            pct = max(0, min(100, pct))
            c = colors[0] if pct > 75 else (colors[1] if pct > 50 else (colors[3] if pct < 30 else colors[2]))
            html += f"""<div style="margin-top:18px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="font-weight:600; font-size:15px; color:{DARK};">{name}</span>
                    <span style="font-weight:900; font-size:15px; color:{c};">{pct}%</span>
                </div>
                <div style="background:#e2e8f0; height:12px; border-radius:6px; overflow:hidden;">
                    <div style="background:{c}; height:100%; width:{pct}%;"></div>
                </div>
            </div>"""
    html += "</div>"
    return html

def _build_quick_hits(raw_data):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if l.strip()]
    if not lines: return ""
    items_html = ""
    for line in lines[:3]:
        clean = line.replace("-", "").replace("*", "").strip()
        items_html += f"""<li style="margin-bottom:12px; color:{SLATE};">{clean}</li>"""
    return f"""<div style="background:#f1f5f9; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;">
        <h3 style="margin-top:0; font-size:20px; color:{DARK};">⚡ Quick Hits</h3>
        <ul style="{F} margin:0; padding-left:20px;">{items_html}</ul>
    </div>"""

def _build_pie_chart(s, b, c, cat):
    c_s, c_b, c_c = ("#b8974d", "#cbd5e1", "#f1f5f9")
    circ = 565.49
    sd, bd, cd = circ*s/100, circ*b/100, circ*c/100
    pie = f"""<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;">
        <circle cx="100" cy="100" r="90" fill="none" stroke="{c_s}" stroke-width="30" stroke-dasharray="{sd} {circ}" stroke-dashoffset="0"/>
        <circle cx="100" cy="100" r="90" fill="none" stroke="{c_b}" stroke-width="30" stroke-dasharray="{bd} {circ}" stroke-dashoffset="-{sd}"/>
        <circle cx="100" cy="100" r="90" fill="none" stroke="{c_c}" stroke-width="30" stroke-dasharray="{cd} {circ}" stroke-dashoffset="-{sd+bd}"/>
        <text x="100" y="95" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">{s}/{b}/{c}</text>
        <text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>
        <div style="display:flex;justify-content:center;gap:20px;">
        <span style="color:{c_s};font-weight:bold;">● Stocks {s}%</span>
        <span style="color:{c_b};font-weight:bold;">● Safe {b}%</span>
        <span style="color:{c_c};font-weight:bold;">● Cash {c}%</span></div>"""
    return pie

def _build_pillar_link(target_cat):
    pillar = PILLAR_PAGES.get(target_cat)
    if not pillar: return ""
    return f"""<div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:20px; margin:40px 0; border-radius:4px;">
        <p style="margin:0; font-size:16px; color:#1e293b;">
            <strong style="color:#2563eb;">📚 Deep Dive:</strong> Want to master this topic? Check out our complete guide to <a href="{pillar['url']}" style="color:#2563eb; text-decoration:underline; font-weight:700;">{pillar['anchor']}</a>.
        </p></div>"""

def _build_branded_footer():
    return f"""<div style="background:{DARK}; padding:35px; border-radius:10px; margin-top:30px;">
        <p style="font-size:24px; font-weight:bold; color:{GOLD}; margin:0 0 12px; text-align:center;">Warm Insight</p>
        <p style="font-size:14px; color:#94a3b8; text-align:center; margin:0 0 16px;">AI-Driven Global Market Analysis</p>
        <p style="font-size:13px; color:#64748b; margin:0; text-align:center;">All analysis is for informational purposes only. Not financial advice.</p>
    </div>"""

def _build_founder_note():
    return f"""<div style="background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%); border:2px solid {GOLD}; border-radius:14px; padding:30px; margin:40px 0;">
        <div style="display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap;">
            <div style="min-width:70px; height:70px; border-radius:50%; background:{GOLD}; display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:900; color:#fff;">J</div>
            <div style="flex:1; min-width:250px;">
                <p style="font-size:13px; font-weight:800; color:#92400e; margin:0 0 6px; text-transform:uppercase; letter-spacing:1.5px;">A NOTE FROM THE FOUNDER</p>
                <p style="font-size:18px; font-weight:700; color:{DARK}; margin:0 0 10px; line-height:1.4;">Hey, I'm Jiho. I built Warm Insight because I was tired of finance content being either too dumbed-down or too academic.</p>
            </div>
        </div>
    </div>"""

# ═══════════════════════════════════════════════
# 🎨 HTML BUILDERS
# ═══════════════════════════════════════════════
def build_foundation_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n""" + _build_founder_note()
    def_text = xtag(raw, "DEFINITION").replace("\n", "<br><br>")
    html += f"""<div style="background:#f0fdf4; border-left:5px solid #10b981; padding:25px; margin:30px 0; border-radius:0 8px 8px 0;"><h3 style="margin-top:0; font-size:22px; color:#065f46;">📖 What is it? (Definition)</h3><div style="color:#064e3b; font-size:18px;">{def_text}</div></div>"""
    why_text = xtag(raw, "WHY_MATTERS").replace("\n", "<br><br>")
    html += f"""<div style="margin:40px 0;"><h3 style="font-size:24px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">💡 Why It Matters</h3><p>{why_text}</p></div>"""
    how_text = xtag(raw, "HOW_TO_START").replace("\n", "<br><br>")
    html += f"""<div style="background:#ffffff; border:2px solid #3b82f6; padding:30px; border-radius:12px; margin:40px 0;"><h3 style="margin-top:0; color:#1e40af; font-size:24px;">🚀 How to Start Today</h3><div style="color:{SLATE}; font-size:18px;">{how_text}</div></div>"""
    html += _build_pillar_link("Foundation") + _build_poll(raw, cat) + _build_branded_footer() + "</div>"
    return sanitize(html)

def build_philosophy_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n""" + _build_founder_note()
    html += f"""<div style="text-align:center; margin:50px 0;"><span style="font-size:40px; color:{GOLD};">❝</span><h2 style="font-family:Georgia,serif; font-size:26px; color:{DARK}; margin:10px 0;">{xtag(raw, "ANCHOR")}</h2><span style="font-size:40px; color:{GOLD};">❞</span></div>"""
    reflection_text = xtag(raw, "REFLECTION").replace("\n", "<br><br>")
    html += f"""<div style="margin:40px 0;"><h3 style="font-size:22px; color:{DARK}; border-left:4px solid {GOLD}; padding-left:12px;">The Reflection</h3><div style="color:{SLATE}; font-size:18px;">{reflection_text}</div></div>"""
    catalyst_text = re.sub(r'<[^>]+>', '', xtag(raw, "CATALYST"))
    html += f"""<div style="background:#fefce8; border:2px solid #fde047; padding:35px; border-radius:12px; margin:50px 0; text-align:center;"><p style="font-size:14px; font-weight:800; color:#b45309;">⚡ The Daily Catalyst</p><p style="font-size:24px; font-weight:900; color:#92400e;">{catalyst_text}</p></div>"""
    html += _build_pillar_link("The Daily Catalyst") + _build_poll(raw, cat) + _build_branded_footer() + "</div>"
    return sanitize(html)

def build_money_hack_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n""" + _build_founder_note()
    concept = xtag(raw, "CONCEPT").replace("\n", "<br><br>")
    html += f"""<div style="margin:40px 0;"><h3 style="font-size:24px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">💡 The Concept</h3><p>{concept}</p></div>"""
    tools = xtag(raw, "STEP_BY_STEP_TOOL").replace("\n", "<br><br>")
    html += f"""<div style="background:#f0fdf4; border:2px solid #10b981; padding:30px; border-radius:12px; margin:40px 0;"><h3 style="margin-top:0; color:#065f46; font-size:24px;">🛠️ Step-by-Step Execution</h3><div style="color:#064e3b; font-size:17px;">{tools}</div></div>"""
    pro_tip = xtag(raw, "PRO_TIP").replace("\n", "<br>")
    html += f"""<div style="background:#fffbeb; border-left:5px solid #f59e0b; padding:25px; margin:40px 0;"><p style="margin:0; font-size:18px; font-weight:800; color:#b45309;">🔥 Pro Tip</p><p style="margin:0; color:#92400e;">{pro_tip}</p></div>"""
    html += _build_pillar_link("Money Hack") + _build_poll(raw, cat) + _build_branded_footer() + "</div>"
    return sanitize(html)

def build_html(tier, cat, raw, author, tf, title):
    html = f"""<div style="{F}">\n""" + _build_warm_index(raw) + _build_founder_note()
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; padding-bottom:10px;">Executive Summary</h2><p style="font-size:19px; font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>"""
    do_act = xtag(raw, "DO_ACTION").replace('\n', '<br>')
    dont_act = xtag(raw, "DONT_ACTION").replace('\n', '<br>')
    html += f"""<div style="background:#fffbeb; border:2px solid #f59e0b; padding:25px; margin:35px 0; border-radius:12px;">
        <h3 style="margin-top:0; color:#b45309; font-size:22px;">⚠️ One-Point Action Plan for Beginners</h3>
        <div style="background:#ffffff; border-left:5px solid #10b981; padding:20px; border-radius:6px; margin-bottom:15px;">
            <p style="margin:0; color:#065f46; font-size:18px; font-weight:800;">🟢 DO THIS:</p>
            <p style="margin:8px 0 0; color:#064e3b; font-size:17px;">{do_act}</p></div>
        <div style="background:#ffffff; border-left:5px solid #ef4444; padding:20px; border-radius:6px;">
            <p style="margin:0; color:#991b1b; font-size:18px; font-weight:800;">🔴 AVOID THIS:</p>
            <p style="margin:8px 0 0; color:#7f1d1d; font-size:17px;">{dont_act}</p></div></div>"""
    html += _build_data_table(xtag(raw, "DATA_TABLE"), "Market Dashboard") + _build_progress_bars(xtag(raw, "HEATMAP"), "Sector Risk Heatmap")
    html += f"""<div style="background:#faf5ff; border-left:5px solid #8b5cf6; padding:25px; margin:40px 0;"><p style="font-size:20px; font-weight:800; color:#4c1d95; margin:0 0 12px;">💡 Plain English</p><p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p></div>"""
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; margin-top:30px;">Market Drivers & Flow</h2><h3 style="font-size:24px; color:{DARK};">{xtag(raw, "HEADLINE")}</h3>"""
    html += f"""<div style="background:#fff; border:1px solid {BORDER}; border-left:5px solid {GOLD}; padding:30px; border-radius:8px; margin:30px 0;">
        <p><strong>🧐 The Big Picture:</strong> {xtag(raw, "MACRO")}</p>
        <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
        <p><strong>🐑 What Most People Are Doing:</strong> {xtag(raw, "HERD")}</p>
        <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
        <p><strong>🦅 What Smart Money Is Doing:</strong> {xtag(raw, "CONTRARIAN")}</p></div>"""
    html += f"""<div style="background:#fffbeb; border:1px solid #fde68a; border-left:5px solid {AMBER}; padding:25px; margin:40px 0;"><strong style="color:#92400e; font-size:20px;">🔗 Chain of Events:</strong><br><span style="font-weight:bold; font-size:19px; color:{DARK};">{xtag(raw, "QUICK_FLOW")}</span></div>"""
    html += f"""<div style="display:flex; flex-wrap:wrap; gap:20px; margin:40px 0;">
        <div style="flex:1; min-width:250px; background:#ecfdf5; border:2px solid #10b981; border-radius:8px; padding:25px;"><h4 style="margin-top:0; font-size:22px; color:#065f46;">🐂 Bull Case</h4><p style="margin:0; color:#064e3b;">{xtag(raw, "BULL_CASE")}</p></div>
        <div style="flex:1; min-width:250px; background:#fef2f2; border:2px solid #ef4444; border-radius:8px; padding:25px;"><h4 style="margin-top:0; font-size:22px; color:#991b1b;">🐻 Bear Case</h4><p style="margin:0; color:#7f1d1d;">{xtag(raw, "BEAR_CASE")}</p></div></div>"""
    html += _build_quick_hits(xtag(raw, "QUICK_HITS"))
    html += f"""<div style="background:#ffffff; border:2px solid {GOLD}; padding:30px; border-radius:8px; margin:45px 0;"><h3 style="margin-top:0; color:{GOLD}; font-size:24px;">💎 Smart Money Move</h3><p style="margin:0;">{xtag(raw, "SMART_MONEY_MOVE")}</p></div>"""
    al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
    html += f"""<div style="background:{BG_LIGHT}; border:1px solid {BORDER}; padding:30px; border-radius:8px; margin-bottom:40px;"><h3 style="margin-top:0; font-size:22px; color:{DARK};">📊 Suggested Allocation</h3>{_build_pie_chart(al["s"], al["b"], al["c"], cat)}</div>"""
    html += f"""<hr style="border:0; height:1px; background:{BORDER}; margin:50px 0;"><h2 style="font-family:Georgia,serif; font-size:28px; color:{DARK}; margin-bottom:20px;">Today's Warm Insight</h2><p style="{F} font-size:19px; font-style:italic; border-left:3px solid #cbd5e1; padding-left:16px;">"{xtag(raw, "TAKEAWAY")}"</p>"""
    html += _build_pillar_link("Insight") + _build_poll(raw, cat) + _build_branded_footer() + "</div>"
    return sanitize(html)

# ═══════════════════════════════════════════════════════════════
# 🖼️ 웹사이트용 썸네일 엔진 
# ═══════════════════════════════════════════════════════════════
def get_font(url, filename):
    if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            resp = requests.get(url, headers=EXTERNAL_HEADERS, timeout=15)
            resp.raise_for_status()
            with open(filename, 'wb') as f: f.write(resp.content)
        except Exception as e: pass
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
        client = _get_gemini_client()
        result = client.models.generate_images(
            model='imagen-3.0-generate-002', prompt=AI_PROMPTS.get(cat, AI_PROMPTS["Economy"]),
            config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg")
        )
        bg_bytes = result.generated_images[0].image.image_bytes
        img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
        img = img.resize((w, h), Image.LANCZOS)
        use_ai_bg = True
    except Exception as e:
        img = Image.new("RGBA", (w, h), style["bg1"])
        draw = ImageDraw.Draw(img)
        draw.ellipse([w*0.35, -h*0.5, w*1.5, h*1.5], fill=style["bg2"])
        cx = w * 0.88
        cy = h * 0.65
        S = SCALE
        cx_p = cx - 180 * S
        cy_p = cy
        R = S * 1.4
        draw.ellipse([cx - 40*R, cy + 65*R, cx + 40*R, cy + 85*R], fill="#00000030")
        draw.line([(cx - 30*R, cy + 10*R), (cx - 70*R, cy - 35*R)], fill="#f8fafc", width=int(12*R))
        draw.line([(cx - 70*R, cy - 35*R), (cx - 85*R, cy - 35*R)], fill="#cbd5e1", width=int(12*R))
        draw.line([(cx + 30*R, cy + 10*R), (cx + 45*R, cy + 40*R)], fill="#f8fafc", width=int(12*R))
        draw.rounded_rectangle([cx - 40*R, cy - 30*R, cx + 40*R, cy + 70*R], radius=int(15*R), fill="#f8fafc", outline="#cbd5e1", width=int(4*R))
        draw.rounded_rectangle([cx - 50*R, cy - 100*R, cx + 50*R, cy - 35*R], radius=int(20*R), fill="#f8fafc", outline="#cbd5e1", width=int(4*R))
        draw.rounded_rectangle([cx - 40*R, cy - 85*R, cx + 40*R, cy - 45*R], radius=int(10*R), fill="#0f172a")

    draw = ImageDraw.Draw(img)
    if use_ai_bg: draw.rectangle([(0, 0), (w, h)], fill="#1a252c70")
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

    clean_title = re.sub(r'^WARM INSIGHT\s*[:\-–]\s*', '', _clean_seo_title(title_text).upper()).strip()
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

# ═══════════════════════════════════════════════
# 🖼️ 미디엄 전용 하이엔드 썸네일 엔진 (완벽 분리/텍스트 제거 폴백 탑재)
# ═══════════════════════════════════════════════
def make_medium_thumbnail(cat):
    print(f"    [AI] Generating Premium Editorial Thumbnail for Medium...")
    client = _get_gemini_client()
    
    # 🚨 잡지 커버 수준의 미디엄 전용 고품질 프롬프트 (글씨 절대 금지)
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
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg"
            )
        )
        print("    ✅ Medium Editorial Thumbnail Generated Successfully!")
        return result.generated_images[0].image.image_bytes
    except Exception as e:
        # 🚨 AI 서버 거부 시, 글씨 있는 웹사이트용이 아니라 파이썬 자체의 '글씨 없는 추상화' 그리기
        print(f"    ⚠️ Medium AI Image Gen failed. Generating custom abstract fallback... ({e})")
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

        # 고급스럽고 추상적인 기하학적 배경 구성 (글씨 절대 없음)
        draw.ellipse([W*0.5, -H*0.2, W*1.3, H*1.2], fill=style["bg2"])
        draw.ellipse([-W*0.1, H*0.4, W*0.4, H*1.5], fill="#00000030")
        
        # 엣지 있는 포인트 악센트 선과 도형
        draw.line([(W*0.15, H*0.2), (W*0.25, H*0.2)], fill=style.get("acc", "#ffffff"), width=8)
        draw.ellipse([W*0.8, H*0.75, W*0.82, H*0.75+W*0.02], fill=style.get("acc", "#ffffff"))
        draw.rectangle([W*0.15, H*0.8, W*0.4, H*0.82], fill=style.get("acc", "#ffffff"))

        img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

# ═══════════════════════════════════════════════
# PUBLISHER & CORE LOGIC
# ═══════════════════════════════════════════════
def _upload_image(img_bytes, filename):
    try:
        headers = {
            "User-Agent": "WordPress/6.5; " + SITE_URL,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/jpeg"
        }
        resp = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers=headers,
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
        r = requests.post(
            f"{WP_URL}/wp-json/wp/v2/posts",
            headers=WP_API_HEADERS,
            json=post_data, auth=(WP_USER, WP_APP_PASS), timeout=30
        )
        if r.status_code in (200, 201):
            try:
                resp_json = r.json()
                link = resp_json.get('link') if isinstance(resp_json, dict) else None
            except: link = None
            
            if link:
                print(f"   ✅ Published: {link}")
                
                # 🚨 미디엄 이메일 발송은 теперь 모든 카테고리(365챌린지 포함)에서 작동합니다!
                if raw_for_cards:
                    # 소셜 비디오/유튜브 스크립트는 정규 뉴스에만 발송
                    if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
                        if tier == "vip" or tier == "unified":
                            img_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes = generate_vip_carousel(raw_for_cards, cat)
                            if video_mp4_bytes:
                                send_social_style_email(display_title, link, img_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes)
                        
                        yt_meta, yt_script = generate_youtube_masterpiece(raw_for_cards, title)
                        if yt_script: send_youtube_script_email(title, yt_meta, yt_script)

                    # 미디엄은 전체 카테고리 발송
                    send_medium_draft_email(display_title, link, raw_for_cards, cat, kw, med_img_bytes)
                
                return True
            else:
                print(f"   ❌ [WAF Block Detected] Server returned 200 but no link was created.")
                return False
        else:
            print(f"   ❌ Publish failed. HTTP Status: {r.status_code}")
    except Exception as e:
        print(f"   ❌ Network error: {e}")
    return False

# ═══════════════════════════════════════════════
# 🔄 PIPELINES
# ═══════════════════════════════════════════════
def run_foundation_pipeline():
    cat = "Foundation"
    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    
    print(f"🚀 Starting v46.9.36 SEO Foundation Pipeline | Category: {cat}")
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
    
    print(f"🚀 Starting v46.9.36 Catalyst Pipeline | Category: {cat}")
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
    
    print(f"🚀 Starting v46.9.36 Money Hack Pipeline | Category: {cat}")
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
        print(f"🚀 Starting v46.9.36 Unified News Pipeline | TEST MODE (Force Publish)")
    else:
        print(f"🚀 Starting v46.9.36 Unified News Pipeline | Category: {cat}")

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
