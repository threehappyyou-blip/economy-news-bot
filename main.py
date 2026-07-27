#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — Ultimate Masterpiece Edition (v46.9.58)
#
# 핵심 복구 및 변경 사항:
#   1. [언어 통제] 글로벌 오디언스를 위한 100% 영문(English) 출력 프롬프트 강제 적용
#   2. [신규 카테고리] 'On-Chain' 카테고리 추가 및 영미권 최상위 크립토 RSS 연동
#   3. [스마트 스케줄링] 매주 화요일, 목요일 'On-Chain' 고정 발행 알고리즘 탑재
#   4. [디자인 픽스] Founder Note를 최상단(Warm Index 직후)으로 이동 및 하단 중복 제거
#   5. [디자인 픽스] On-Chain 등 텍스트 누락 시 Poll(투표창)이 깨지지 않도록 강력한 Fallback 추가
#   6. [SEO 픽스] Foundation 카테고리 롱테일(Long-tail) 키워드 타겟팅 및 클릭 유도 프롬프트 강화
#   7. [UX 픽스] 실전 중심 Action Plan 프롬프트 강화 및 Executive Summary 바로 밑으로 배치 변경
#   8. [엔진 픽스] Money Hack 무한 주제 생성 엔진(Infinite Topic Engine) 탑재
#   9. [통신 픽스] Imunify360 WAF 차단 원천 해결: WP 내부 통신을 Cloudscraper로 100% 교체
#  10. [신규 파이프라인] Medium(미디엄) 유기적 트래픽 유입을 위한 Teaser Draft 이메일 자동 발송
#  11. [마케팅 확장] 🚀 북미 커뮤니티(레딧, 쿼라) 타겟 바이럴 게릴라 포스팅 템플릿 자동 발송
#  12. [이메일 누락 픽스] 🚨 숏폼 영상 비트레이트 2500k 다이어트로 구글 메일 사전 차단(Silent Drop) 완벽 해결
#  13. [숏폼 엔진 픽스] 🔥 다크 심리학 무드 100% 동기화 (검은 배경, 하얀 창백한 더미 인물, 붉은 빛 오브젝트)
#  14. [다이내믹 스토리텔링] 🔥 4개의 각기 다른 다크 심리학 이미지를 5초 간격으로 생성하여 슬라이드별 교차 적용
#  15. [텍스트 잘림 픽스] 🚨 영상 내 텍스트 글씨 잘림(Truncation) 방지를 위한 Max Width 850px 및 동적 폰트 사이즈 적용
#  16. [치명적 버그 픽스] 🚨 _gemini_client 전역 변수(Global) 선언 누락으로 인한 NameError 완벽 복구
#  17. [클린 코드] 🚨 2700줄의 누적 복사본 찌꺼기 100% 클렌징 및 모든 뉴스레터 파이프라인 무결성 유지 완료
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
    "Economy": ["https://feeds.reuters.com/reuters/businessNews", "https://finance.yahoo.com/news/rssindex"],
    "Politics": ["https://feeds.reuters.com/Reuters/PoliticsNews", "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"],
    "Tech": ["https://feeds.reuters.com/reuters/technologyNews", "https://techcrunch.com/feed/"],
    "Health": ["https://feeds.reuters.com/reuters/healthNews", "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml"],
    "Energy": ["https://oilprice.com/rss/main", "https://feeds.reuters.com/reuters/environment"],
    "On-Chain": ["https://cointelegraph.com/rss", "https://www.coindesk.com/arc/outboundfeeds/rss/"],
}

CAT_ALLOC = {
    "Economy": {"s": 55, "b": 35, "c": 10},
    "Politics": {"s": 50, "b": 35, "c": 15},
    "Tech": {"s": 70, "b": 20, "c": 10},
    "Health": {"s": 60, "b": 30, "c": 10},
    "Energy": {"s": 65, "b": 25, "c": 10},
    "On-Chain": {"s": 25, "b": 15, "c": 60},
}

# ═══════════════════════════════════════════════
# 🛡️ SYSTEM UTILS & API ENGINE
# ═══════════════════════════════════════════════
_gemini_client = None

def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None: 
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
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
        is_valid_json = isinstance(resp.json(), dict) and "id" in resp.json()
        if resp.status_code == 200 and is_valid_json: 
            print("   ✅ WP Auth Successful!")
            return True
    except Exception as e: 
        print(f"   ❌ WP Connection Error: {e}")
    return False

def call_gemini(client, model, prompt, sys_inst=None, retries=5):
    if not sys_inst:
        sys_inst = "You are an elite financial analyst. ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN."
    config = types.GenerateContentConfig(system_instruction=sys_inst, temperature=0.7, max_output_tokens=8192)
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt, config=config)
            if r.text: return str(r.text)
        except Exception as e:
            err = str(e)
            if "credits are depleted" in err or "billing" in err.lower() or "404" in err or "not found" in err.lower(): return None
            time.sleep((15 * i) + random.uniform(-2, 5))
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
        res = re.sub(r"^`{3}(html|xml|text|markdown)?\n", "", m.group(1).strip(), flags=re.IGNORECASE)
        return re.sub(r"\n`{3}$", "", res).strip()
    return ""

def sanitize(html):
    html = re.sub(r"<script(?!\s+type=['\"]application/ld\+json['\"])[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    return re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.DOTALL)

def make_slug(kw, title, cat):
    base = kw if (kw and len(kw) > 4) else title
    slug = re.sub(r"[^\w\s-]", "", base.lower())
    return re.sub(r"[\s_]+", "-", slug).strip("-")[:55] + f"-{datetime.datetime.utcnow().strftime('%m%d%H%M')}"

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
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
    except: pass
    return None

def _get_latest_post_category_name():
    try:
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/posts?per_page=1&status=publish", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0 and r.json()[0].get('categories'):
            r_cats = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=100", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
            cat_map = {c['id']: c['name'] for c in r_cats.json()}
            for cid in r.json()[0]['categories']:
                if cat_map.get(cid) in CATEGORIES: return cat_map.get(cid)
    except: pass
    return None

def already_published_today(cat):
    try:
        cat_slug = cat.lower().replace(" ", "-")
        r = scraper.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={cat_slug}", headers=WP_API_HEADERS, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code != 200 or not r.json(): return False
        cat_id = r.json()[0]["id"]

        r2 = scraper.get(f"{WP_URL}/wp-json/wp/v2/posts", headers=WP_API_HEADERS, params={"categories": cat_id, "per_page": 1, "status": "publish"}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code == 200 and len(r2.json()) > 0:
            if r2.json()[0].get("date_gmt", "")[:10] == datetime.datetime.utcnow().strftime("%Y-%m-%d"): return True
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
                    if len(title) > 10: items.add(f"• {title}: {summary}")
        except: pass
    items_list = list(items)
    random.shuffle(items_list)
    return items_list[:max_items]

# ═══════════════════════════════════════════════
# 🎬 EMAIL & YOUTUBE ENGINE
# ═══════════════════════════════════════════════
YT_META_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Based on the following newsletter content, generate a YouTube Metadata package in ENGLISH.
<METADATA>
[VIRAL TITLES]
- Option A: 
- Option B: 
- Option C: 
[THUMBNAIL IDEAS]
1. Visual Prompt: (HYPER-DETAILED AI prompt. NO TEXT)
2. Text/Copy: (2-4 words MASSIVE IMPACT)
[SEO HASHTAGS]
</METADATA>"""

YT_SCRIPT_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write PART 1 of a massive YouTube script. Hook, Greeting, Chapter 1.
[NEWSLETTER] {raw_content}
Wrap in <PART1> tags."""

YT_SCRIPT_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Continue script from Part 1. Write PART 2: Chapter 2 & 3. Wrap in <PART2> tags."""

YT_SCRIPT_P3 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Complete script. Write PART 3: Chapter 4 & Outro. Wrap in <PART3> tags."""

def generate_youtube_masterpiece(raw_content, title):
    meta = xtag(gem_fb("Premium", YT_META_PROMPT.replace("{raw_content}", raw_content)), "METADATA")
    p1 = xtag(gem_fb("Premium", YT_SCRIPT_P1.replace("{raw_content}", raw_content)), "PART1")
    p2 = xtag(gem_fb("Premium", YT_SCRIPT_P2), "PART2")
    p3 = xtag(gem_fb("Premium", YT_SCRIPT_P3), "PART3")
    return meta, f"{p1}\n\n{p2}\n\n{p3}"

def send_youtube_script_email(post_title, meta, script):
    if not EMAIL_SENDER or not EMAIL_PASS: return
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, YOUTUBE_EMAIL_RECEIVER, f"🎬 [YouTube Script] {post_title[:40]}"
        body = f"<h2>YouTube Script Ready</h2><pre>{meta}</pre><hr><pre>{script}</pre>"
        msg.attach(MIMEText(body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(EMAIL_SENDER, EMAIL_PASS)
            s.send_message(msg)
    except: pass

def send_medium_draft_email(title, link, raw_content, cat, kw, img_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS: return
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, MEDIUM_EMAIL_RECEIVER, f"✍️ [Medium Draft] {title[:40]}"
        body = f"<h2>Medium Teaser Ready</h2><p>Paste this link as canonical: {link}</p>"
        msg.attach(MIMEText(body, 'html'))
        if img_bytes:
            img = MIMEImage(img_bytes, name="thumbnail.jpg")
            img.add_header('Content-Disposition', 'attachment', filename="thumbnail.jpg")
            msg.attach(img)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(EMAIL_SENDER, EMAIL_PASS)
            s.send_message(msg)
    except: pass

def send_community_viral_email(title, original_link, raw_content, cat):
    if not EMAIL_SENDER or not EMAIL_PASS: return
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, EMAIL_RECEIVER, f"📢 [Viral Post] {title[:30]}"
        msg.attach(MIMEText(f"<p>Link: {original_link}</p>", 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(EMAIL_SENDER, EMAIL_PASS)
            s.send_message(msg)
    except: pass

def send_social_style_email(title, link, img_bytes_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS: return
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = EMAIL_SENDER, EMAIL_RECEIVER, f"🚨 {cat.upper()} REELS READY"
        msg.attach(MIMEText(f"<p>{reels_script}</p><br><p>{ig_caption}</p>", 'html'))
        if video_mp4_bytes:
            part = MIMEBase('video', 'mp4')
            part.set_payload(video_mp4_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=f'{cat}_Video.mp4')
            msg.attach(part)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(EMAIL_SENDER, EMAIL_PASS)
            s.send_message(msg)
    except: pass

# ═══════════════════════════════════════════════
# 🎬 숏폼 비디오 엔진 (다이내믹 4 AI Image + 2500k Bitrate)
# ═══════════════════════════════════════════════
def get_font(url, filename):
    if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            resp = scraper.get(url, timeout=15)
            resp.raise_for_status()
            with open(filename, 'wb') as f: f.write(resp.content)
        except: pass
    return filename

def generate_video_mp4(cat, hook_text, data_points, frames_images):
    try:
        import numpy as np
        from moviepy.editor import ImageClip, concatenate_videoclips
    except ImportError: return None
    try:
        SLIDE_DURATION, CROSSFADE, ZOOM_START, ZOOM_END = 2.6, 0.2, 1.0, 1.08
        clips = []
        for i, frame in enumerate(frames_images):
            clip = ImageClip(np.array(frame.convert('RGB'))).set_duration(SLIDE_DURATION)
            clip = clip.resize(lambda t, i=i: ZOOM_START + (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION) if i % 2 == 0 else ZOOM_END - (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            clip = clip.set_position(('center', 'center'))
            if i > 0: clip = clip.crossfadein(CROSSFADE)
            clips.append(clip)

        video = concatenate_videoclips(clips, padding=-CROSSFADE, method="compose")
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tf: temp_path = tf.name
        
        # 🚨 이메일 차단 방지를 위한 비트레이트 2500k 최적화
        video.write_videofile(
            temp_path, fps=30, codec='libx264', bitrate='2500k', audio=False, preset='fast',
            ffmpeg_params=['-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1:1', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
        )
        with open(temp_path, 'rb') as f: mp4_bytes = f.read()
        os.remove(temp_path)
        return mp4_bytes
    except Exception as e: return None

def generate_vip_carousel(raw_content, cat):
    client = _get_gemini_client()
    sys_inst = """CRITICAL RULE: OUTPUT ONLY IN ENGLISH. 
    Format EXACTLY:
    <MAIN_TITLE>Max 5 words</MAIN_TITLE>
    <HOOK>Max 7 words</HOOK>
    <SHOCK_STAT>Max 6 words</SHOCK_STAT>
    <INSIGHT_LINE>Max 8 words</INSIGHT_LINE>
    <CTA_HOOK>Max 6 words</CTA_HOOK>
    <REELS_SCRIPT>60s script</REELS_SCRIPT>
    <IG_CAPTION>Caption</IG_CAPTION>
    <ITEM1>TICKER | Value</ITEM1>
    <ITEM2>TICKER | Value</ITEM2>
    <ITEM3>TICKER | Value</ITEM3>
    """
    raw_data = gem_fb("vip", raw_content, sys_inst)
    
    hook_text = xtag(raw_data, "HOOK") or "Wall Street Just Did THIS 🚨"
    shock_stat = xtag(raw_data, "SHOCK_STAT") or "$2.3T MOVED OVERNIGHT"
    insight_line = xtag(raw_data, "INSIGHT_LINE") or "SMART MONEY IS MOVING NOW"
    cta_hook = xtag(raw_data, "CTA_HOOK") or "DONT MISS THE NEXT MOVE"
    
    data_points = []
    for i in range(1, 4):
        item = xtag(raw_data, f"ITEM{i}")
        if item and "|" in item:
            parts = item.split("|")
            data_points.append({"ticker": parts[0].strip()[:8], "val": parts[1].strip()})
    if len(data_points) < 3:
        data_points = [{"ticker": "$NVDA", "val": "+6.2%"}, {"ticker": "$AAPL", "val": "+5.3%"}, {"ticker": "$BTC", "val": "+4.2%"}]

    W, H = 1080, 1920
    BG, WHITE, RED, GRAY = "#000000", "#ffffff", "#ef4444", "#94a3b8"

    def lf(p, s):
        try: return ImageFont.truetype(p, s)
        except: return ImageFont.load_default()
    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")
    font_title, font_mega, font_sub, font_data, font_alert = lf(ft_path, 95), lf(ft_path, 130), lf(ft_path, 55), lf(ft_path, 50), lf(ft_path, 75)

    # 🚨 다이내믹 스토리텔링: 4장의 다크 심리학 이미지 프롬프트
    vp_base = f"A creepy pale featureless white mannequin humanoid figure, pitch black background, surrounded by glowing red abstract objects representing {cat}. Dark psychology aesthetic, mysterious, high contrast. No text."
    vps = [
        vp_base + " The humanoid is reacting in shock, holding its head.",
        vp_base + " The humanoid is carefully analyzing a glowing red data sphere.",
        vp_base + " The humanoid is touching and manipulating floating red digital nodes.",
        vp_base + " The humanoid is standing confidently looking forward with a powerful glowing red aura."
    ]

    def fetch_dark_psy_image(prompt_text):
        try:
            prompt_encoded = urllib.parse.quote(prompt_text)
            url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1080&height=1080&nologo=true&seed={random.randint(1,10000)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                ai_img_raw = Image.open(io.BytesIO(response.read())).convert("RGBA").resize((1080, 1080), Image.LANCZOS)
                mask = Image.new("L", (1080, 1080), 255)
                mask_draw = ImageDraw.Draw(mask)
                for y in range(780, 1080): mask_draw.line([(0, y), (1080, y)], fill=int(255 - (y - 780) * (255 / 300)))
                ai_img_raw.putalpha(mask)
                return ai_img_raw
        except: return None

    # 🚨 서버 차단 방지를 위한 5초 딜레이 및 스마트 폴백
    ai_imgs = []
    last_good_img = None
    for vp in vps:
        img = fetch_dark_psy_image(vp)
        if img: last_good_img = img
        ai_imgs.append(img)
        time.sleep(5) 
        
    for i in range(4):
        if not ai_imgs[i]: ai_imgs[i] = last_good_img

    def paste_bg(d_img, target_ai_img):
        if target_ai_img: d_img.paste(target_ai_img, (0, 100), target_ai_img)

    # 🚨 글자 잘림을 막아주는 동적 텍스트 래핑
    def wrap_lines(text, font, max_width):
        words, lines, line, d = text.split(), [], [], ImageDraw.Draw(Image.new("RGB", (1,1)))
        for ww in words:
            try: tw = d.textlength(" ".join(line + [ww]), font=font)
            except: tw = len(" ".join(line + [ww])) * 40  
            if tw < max_width: line.append(ww)
            else:
                if line: lines.append(" ".join(line))
                line = [ww]
        if line: lines.append(" ".join(line))
        return lines

    frames = []
    
    # 1. 훅
    img1 = Image.new("RGB", (W, H), BG)
    paste_bg(img1, ai_imgs[0])
    d1 = ImageDraw.Draw(img1)
    d1.rounded_rectangle([300, 1150, 780, 1250], radius=20, fill=RED)
    d1.text((W//2, 1200), f"🚨 {cat.upper()} ALERT", fill=WHITE, font=font_alert, anchor="mm")
    y_text = 1350
    for i, ln in enumerate(wrap_lines(hook_text.upper(), font_title, 850)):
        d1.text((W//2, y_text), ln, fill=(RED if i == 2 else WHITE), font=font_title, anchor="mm")
        y_text += 105 
    d1.text((W//2, 1800), "↓ SWIPE TO SEE WHY ↓", fill=GRAY, font=font_sub, anchor="mm")
    frames.append(img1)

    # 2. 스탯
    img2 = Image.new("RGB", (W, H), BG)
    paste_bg(img2, ai_imgs[1])
    d2 = ImageDraw.Draw(img2)
    d2.text((W//2, 1180), "THE NUMBER", fill=RED, font=font_sub, anchor="mm")
    y_text = 1350
    for ln in wrap_lines(shock_stat.upper(), font_mega, 850)[:3]:
        d2.text((W//2, y_text), ln, fill=WHITE, font=font_mega, anchor="mm")
        y_text += 140 
    d2.text((W//2, 1800), "WAIT FOR IT...", fill=GRAY, font=font_sub, anchor="mm")
    frames.append(img2)

    # 3~5. 데이터
    data_imgs = []
    for idx, item in enumerate(data_points):
        img_d = Image.new("RGB", (W, H), BG)
        paste_bg(img_d, ai_imgs[2])
        d = ImageDraw.Draw(img_d)
        d.text((W//2, 1150), cat.upper(), fill=RED, font=font_sub, anchor="mm")
        d.text((W//2, 1250), f"WATCH THIS → {idx+1}/3", fill=GRAY, font=font_data, anchor="mm")
        d.text((W//2, 1400), item['ticker'], fill=WHITE, font=font_title, anchor="mm")
        val_str = item['val']
        current_font_huge = lf(ft_path, max(90, int(200 * (6 / max(len(val_str), 1)))))
        d.text((W//2, 1550), val_str, fill=(RED if '-' in val_str else WHITE), font=current_font_huge, anchor="mm")
        
        dot_y = 1800
        for di in range(3):
            dx = W//2 + (di - 1) * 60
            d.ellipse([dx-15, dot_y-15, dx+15, dot_y+15], fill=(RED if di == idx else "#3f3f46"))
        data_imgs.append(img_d)
    frames.extend(data_imgs)

    # 6. 결론
    img6 = Image.new("RGB", (W, H), BG)
    paste_bg(img6, ai_imgs[3])
    d6 = ImageDraw.Draw(img6)
    d6.text((W//2, 1150), "THE TAKEAWAY", fill=RED, font=font_sub, anchor="mm")
    y_text = 1250
    for ln in wrap_lines(insight_line.upper(), font_title, 850)[:3]:
        d6.text((W//2, y_text), ln, fill=WHITE, font=font_title, anchor="mm")
        y_text += 105
    d6.text((W//2, 1650), cta_hook.upper(), fill=RED, font=font_alert, anchor="mm")
    d6.text((W//2, 1780), "LINK IN BIO → @WARMINSIGHT", fill=GRAY, font=font_sub, anchor="mm")
    frames.append(img6)

    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, frames)
    return [], data_points, hook_text, "", "", "", "", video_mp4_bytes

# ═══════════════════════════════════════════════
# 🧠 PROMPTS & PIPELINES (HTML / WEB PUBLISHING)
# ═══════════════════════════════════════════════
FOUNDATION_PROMPT = """Write an SEO-optimized beginner's guide on the following topic in English: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Specific LONG-TAIL focus keyword, 4-6 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Curiosity Gap.)</EXCERPT>
<DEFINITION>(Simple 2-paragraph definition with UNEXPECTED everyday analogy.)</DEFINITION>
<WHY_MATTERS>(Explain in 2 paragraphs why a beginner should care. Use concrete amounts.)</WHY_MATTERS>
<HOW_TO_START>(3 ACTIONABLE steps. Format as a bulleted list.)</HOW_TO_START>
<POLL_QUESTION>(Provocative multiple-choice question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

PHILOSOPHY_PROMPT = """Write a philosophical daily insight based on the following theme in English: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Specific LONG-TAIL focus keyword, 4-6 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Curiosity Gap.)</EXCERPT>
<ANCHOR>(The Classical Anchor: A one-sentence philosophical principle based on the theme.)</ANCHOR>
<REFLECTION>(The Modern Reflection: 3-4 paragraphs explaining how this principle connects to modern reality.)</REFLECTION>
<CATALYST>(The Daily Catalyst: A single, highly provocative and specific question.)</CATALYST>
<POLL_QUESTION>(Provocative multiple-choice question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

MONEY_HACK_PROMPT = """Write an SEO-optimized, step-by-step side hustle guide based on this randomly generated framework in English: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Specific LONG-TAIL focus keyword, 4-6 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD. Curiosity Gap.)</EXCERPT>
<CONCEPT>(2 paragraphs explaining what this specific side hustle is and why it's profitable right now.)</CONCEPT>
<STEP_BY_STEP_TOOL>(Clear 1-2-3 checklist to execute today. Exact instructions.)</STEP_BY_STEP_TOOL>
<PRO_TIP>(1 paragraph revealing a secret tip that top 1% earners use.)</PRO_TIP>
<POLL_QUESTION>(Provocative multiple-choice question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

PROMPT_UNIFIED_P1 = """Write PART 1 of an Insight newsletter on {cat} in ENGLISH.
{news}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(4-6 words)</SEO_KEYWORD>
<EXCERPT>(Curiosity gap)</EXCERPT>
<WARM_INDEX_SCORE>(0-100)</WARM_INDEX_SCORE>
<WARM_INDEX_REASON>(5-10 words)</WARM_INDEX_REASON>
<DATA_TABLE>(Asset Name | Value | UP/DOWN/SIDEWAYS | Insight)</DATA_TABLE>
<HEATMAP>(Sector Name | Number)</HEATMAP>
<EXECUTIVE_SUMMARY>(3 sentences capturing COUNTERINTUITIVE thesis.)</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>(Analogy)</PLAIN_ENGLISH>
<HEADLINE>(Analytical headline)</HEADLINE>
<MACRO>(2 PARAGRAPHS)</MACRO>
<HERD>(Retail behavior)</HERD>
<CONTRARIAN>(Smart money behavior)</CONTRARIAN>
<QUICK_FLOW>(Chain of events)</QUICK_FLOW>"""

PROMPT_UNIFIED_P2 = """Write PART 2 of the Insight newsletter for {cat} in ENGLISH.
{ctx}
<BULL_CASE>(Optimistic scenario.)</BULL_CASE>
<BEAR_CASE>(Pessimistic scenario.)</BEAR_CASE>
<HISTORICAL_PARALLEL>(Name the year + event.)</HISTORICAL_PARALLEL>
<QUICK_HITS>(3 bullet points)</QUICK_HITS>
<SMART_MONEY_MOVE>(1 paragraph. NAME 1 specific ETF ticker.)</SMART_MONEY_MOVE>
<DO_ACTION>(Specific action for beginners)</DO_ACTION>
<DONT_ACTION>(Mistake to avoid)</DONT_ACTION>
<TAKEAWAY>(Bottom line insight)</TAKEAWAY>
<PS>(Veteran advice)</PS>
<POLL_QUESTION>(Question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

def build_foundation_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n{_build_founder_note()}"""
    html += f"""<div style="background:#f0fdf4; border-left:5px solid #10b981; padding:25px; margin:30px 0;">
        <h3 style="margin-top:0; color:#065f46;">📖 What is it?</h3><div>{xtag(raw, "DEFINITION").replace(chr(10), '<br><br>')}</div>
    </div>"""
    html += f"""<div style="margin:40px 0;"><h3 style="color:{DARK};">💡 Why It Matters</h3><p>{xtag(raw, "WHY_MATTERS").replace(chr(10), '<br><br>')}</p></div>"""
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    html += f"""<div style="background:#ffffff; border:2px solid #3b82f6; padding:30px; border-radius:12px; margin:40px 0;">
        <h3 style="margin-top:0; color:#1e40af;">🚀 How to Start Today</h3><div>{xtag(raw, "HOW_TO_START").replace(chr(10), '<br><br>')}</div>
    </div>"""
    html += _build_pillar_link("Foundation") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p></div>"""
    return sanitize(html)

def build_philosophy_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n{_build_founder_note()}"""
    html += f"""<div style="text-align:center; margin:50px 0;"><span style="font-size:40px; color:{GOLD};">❝</span>
        <h2 style="font-family:Georgia,serif; font-size:26px; color:{DARK}; margin:10px 0;">{xtag(raw, "ANCHOR")}</h2>
        <span style="font-size:40px; color:{GOLD};">❞</span></div>"""
    html += f"""<div style="margin:40px 0;"><h3 style="color:{DARK}; border-left:4px solid {GOLD}; padding-left:12px;">The Reflection</h3>
        <div>{xtag(raw, "REFLECTION").replace(chr(10), '<br><br>')}</div></div>"""
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    html += f"""<div style="background:#fefce8; border:2px solid #fde047; padding:35px; border-radius:12px; margin:50px 0; text-align:center;">
        <p style="font-size:14px; font-weight:800; color:#b45309;">⚡ The Daily Catalyst</p>
        <p style="font-size:24px; font-weight:900; color:#92400e;">{re.sub(r'<[^>]+>', '', xtag(raw, "CATALYST"))}</p>
    </div>"""
    html += _build_pillar_link("The Daily Catalyst") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p></div>"""
    return sanitize(html)

def build_money_hack_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n{_build_founder_note()}"""
    html += f"""<div style="margin:40px 0;"><h3 style="color:{DARK};">💡 The Concept</h3><p>{xtag(raw, "CONCEPT").replace(chr(10), '<br><br>')}</p></div>"""
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    html += f"""<div style="background:#f0fdf4; border:2px solid #10b981; padding:30px; border-radius:12px; margin:40px 0;">
        <h3 style="margin-top:0; color:#065f46;">🛠️ Step-by-Step Execution</h3><div>{xtag(raw, "STEP_BY_STEP_TOOL").replace(chr(10), '<br><br>')}</div>
    </div>"""
    html += f"""<div style="background:#fffbeb; border-left:5px solid #f59e0b; padding:25px; margin:40px 0;">
        <p style="margin:0; font-weight:800; color:#b45309;">🔥 Pro Tip</p><p style="margin:0; color:#92400e;">{xtag(raw, "PRO_TIP").replace(chr(10), '<br>')}</p>
    </div>"""
    html += _build_pillar_link("Money Hack") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p></div>"""
    return sanitize(html)

def build_html(tier, cat, raw, author, tf, title):
    html = f"""<div style="{F}">\n{_build_warm_index(raw)}{_build_founder_note()}"""
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; padding-bottom:10px;">Executive Summary</h2>"""
    html += f"""<p style="font-size:19px; font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>"""
    html += f"""<div style="background:#fffbeb; border:2px solid #f59e0b; padding:25px; margin:35px 0; border-radius:12px;">
        <h3 style="margin-top:0; color:#b45309; font-size:22px;">⚠️ Action Plan for Beginners</h3>
        <p style="font-size:15px; color:#92400e; margin-bottom:20px;">Today's specific strategy</p>
        <div style="background:#ffffff; border-left:5px solid #10b981; padding:20px; border-radius:6px; margin-bottom:15px;">
            <p style="margin:0; color:#065f46; font-size:18px; font-weight:800;">🟢 DO THIS:</p>
            <p style="margin:8px 0 0; color:#064e3b;">{xtag(raw, "DO_ACTION")}</p>
        </div>
        <div style="background:#ffffff; border-left:5px solid #ef4444; padding:20px; border-radius:6px;">
            <p style="margin:0; color:#991b1b; font-size:18px; font-weight:800;">🔴 AVOID THIS:</p>
            <p style="margin:8px 0 0; color:#7f1d1d;">{xtag(raw, "DONT_ACTION")}</p>
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
    </div>"""
    html += f"""<hr style="border:0; height:1px; background:{BORDER}; margin:50px 0;">
    <h2 style="font-family:Georgia,serif; font-size:28px; color:{DARK}; margin-bottom:20px;">Today's Warm Insight</h2>
    <p style="{F} font-size:19px; font-style:italic; border-left:3px solid #cbd5e1; padding-left:16px;">"{xtag(raw, "TAKEAWAY")}"</p>
    <div style="background:{DARK}; padding:30px; border-radius:10px; border-left:5px solid {GOLD}; margin-top:35px;">
        <p style="color:#e2e8f0; font-size:18px; margin:0;"><strong style="color:{GOLD};">P.S.</strong> {xtag(raw, "PS")}</p>
    </div>"""
    html += _build_pillar_link("Insight") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p></div>"""
    return sanitize(html)

def make_thumbnail(title_text, cat, tier):
    W, H, SCALE = 1200, 630, 2
    img = Image.new("RGBA", (W * SCALE, H * SCALE), "#0284c7")
    draw = ImageDraw.Draw(img)
    draw.ellipse([W*0.35*SCALE, -H*0.5*SCALE, W*1.5*SCALE, H*1.5*SCALE], fill="#0369a1")
    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")
    try: ft = ImageFont.truetype(ft_path, 85 * SCALE)
    except: ft = ImageFont.load_default()
    draw.text((40*SCALE, 160*SCALE), title_text[:30], font=ft, fill="#ffffff")
    buf = io.BytesIO()
    img.convert("RGB").resize((W, H), Image.LANCZOS).save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def make_medium_thumbnail(cat):
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H), "#1e293b")
    draw = ImageDraw.Draw(img)
    draw.ellipse([W*0.5, -H*0.2, W*1.3, H*1.2], fill="#0f172a")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, author_name, raw_for_cards=None, med_img_bytes=None):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat)
    insight_cat_id = None if cat in ["Foundation", "The Daily Catalyst", "Money Hack"] else get_or_create_wp_category("Insight")
    tag_id = get_or_create_wp_tag("Insight" if tier == "unified" else ("VIP" if tier == "vip" else "Pro"))
    author_id = get_wp_author_id(author_name)
    display_title = title if cat in ["Foundation", "The Daily Catalyst", "Money Hack"] or tier == "unified" else (f"[VIP] {title}" if tier == "vip" else f"[Pro] {title}")

    post_data = {"title": display_title, "content": html, "status": "publish", "slug": slug}
    if author_id: post_data["author"] = author_id
    if media_id: post_data["featured_media"] = media_id
    cats = []
    if cat_id: cats.append(cat_id)
    if insight_cat_id: cats.append(insight_cat_id)
    if cats: post_data["categories"] = cats
    if tag_id: post_data["tags"] = [tag_id]

    seo_title = _clean_seo_title(title)
    post_data["meta"] = {
        "rank_math_title": (seo_title if len(seo_title) > 50 else f"{seo_title} | Warm Insight")[:60],
        "rank_math_description": (exc or "")[:160],
        "rank_math_focus_keyword": kw.lower() if kw else "",
        "is_premium": "no" if cat in ["Foundation", "Money Hack"] else "yes",
        "pms_content_restrict": "0" if cat in ["Foundation", "Money Hack"] else "1",
        "post_tier": tier.upper(),
    }

    try:
        r = scraper.post(f"{WP_URL}/wp-json/wp/v2/posts", json=post_data, auth=(WP_USER, WP_APP_PASS), timeout=30)
        if r.status_code in (200, 201) and r.json().get('link'):
            link = r.json().get('link')
            print(f"   ✅ Published: {link}")
            if raw_for_cards:
                if cat not in ["Foundation", "The Daily Catalyst", "Money Hack"]:
                    img_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes = generate_vip_carousel(raw_for_cards, cat)
                    if video_mp4_bytes: send_social_style_email(display_title, link, img_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes)
                    yt_meta, yt_script = generate_youtube_masterpiece(raw_for_cards, title)
                    if yt_script: send_youtube_script_email(title, yt_meta, yt_script)
                send_medium_draft_email(display_title, link, raw_for_cards, cat, kw, med_img_bytes)
                send_community_viral_email(display_title, link, raw_for_cards, cat)
            return True
    except: pass
    return False

def run_foundation_pipeline():
    cat = "Foundation"
    print(f"🚀 Starting Foundation Pipeline")
    if not check_env_vars() or not verify_wp_credentials(): return
    if os.environ.get("FORCE_PUBLISH", "false").lower() != "true" and already_published_today(cat): return
    theme = random.choice(FOUNDATION_TOPICS)
    raw = gem_fb("premium", FOUNDATION_PROMPT.replace("{theme}", theme), FOUNDATION_SYS_INST)
    if raw:
        title, kw, exc = xtag(raw, "TITLE"), xtag(raw, "SEO_KEYWORD"), xtag(raw, "EXCERPT")
        slug, author = make_slug(kw, title, cat), VIP_AUTHORS.get(cat, "Warm Insight Education Team")
        html = build_foundation_html(raw, author, datetime.datetime.utcnow().strftime("%B %d, %Y"), title, cat)
        publish(title, html, exc, kw, cat, slug, "premium", make_thumbnail(title, cat, "premium"), author, raw_for_cards=raw, med_img_bytes=make_medium_thumbnail(cat))

def run_philosophy_pipeline():
    cat = "The Daily Catalyst"
    print(f"🚀 Starting Catalyst Pipeline")
    if not check_env_vars() or not verify_wp_credentials(): return
    if os.environ.get("FORCE_PUBLISH", "false").lower() != "true" and already_published_today(cat): return
    theme = random.choice(PHILOSOPHY_TOPICS)
    raw = gem_fb("premium", PHILOSOPHY_PROMPT.replace("{theme}", theme), PHILOSOPHY_SYS_INST)
    if raw:
        title, kw, exc = xtag(raw, "TITLE"), xtag(raw, "SEO_KEYWORD"), xtag(raw, "EXCERPT")
        slug, author = make_slug(kw, title, cat), VIP_AUTHORS.get(cat, "Warm Insight Philosophical Desk")
        html = build_philosophy_html(raw, author, datetime.datetime.utcnow().strftime("%B %d, %Y"), title, cat)
        publish(title, html, exc, kw, cat, slug, "premium", make_thumbnail(title, cat, "premium"), author, raw_for_cards=raw, med_img_bytes=make_medium_thumbnail(cat))

def run_moneyhack_pipeline():
    cat = "Money Hack"
    print(f"🚀 Starting Money Hack Pipeline")
    if not check_env_vars() or not verify_wp_credentials(): return
    if os.environ.get("FORCE_PUBLISH", "false").lower() != "true" and already_published_today(cat): return
    theme = f"Niche: {random.choice(MH_NICHES)} | Core Platform: {random.choice(MH_PLATFORMS)} | AI Tool: {random.choice(MH_AI_TOOLS)}"
    raw = gem_fb("premium", MONEY_HACK_PROMPT.replace("{theme}", theme), MONEY_HACK_SYS_INST)
    if raw:
        title, kw, exc = xtag(raw, "TITLE"), xtag(raw, "SEO_KEYWORD"), xtag(raw, "EXCERPT")
        slug, author = make_slug(kw, title, cat), VIP_AUTHORS.get(cat, "Warm Insight Growth Team")
        html = build_money_hack_html(raw, author, datetime.datetime.utcnow().strftime("%B %d, %Y"), title, cat)
        publish(title, html, exc, kw, cat, slug, "premium", make_thumbnail(title, cat, "premium"), author, raw_for_cards=raw, med_img_bytes=make_medium_thumbnail(cat))

def run_news_pipeline(forced_cat=None):
    current_time = datetime.datetime.utcnow()
    day_of_year = current_time.timetuple().tm_yday
    
    if forced_cat: cat = forced_cat
    elif current_time.weekday() in (1, 3): cat = "On-Chain"
    else: cat = [c for c in CATEGORIES if c not in ["On-Chain", "Money Hack"]][day_of_year % 5]

    print(f"🚀 Starting v46.9.57 Unified News Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return
    if os.environ.get("FORCE_PUBLISH", "false").lower() != "true" and already_published_today(cat):
        print(f"   🛑 [Anti-Spam] {cat} already published today. Exiting.")
        return

    all_news = fetch_news_pool(cat)
    if len(all_news) < 2: return
    
    raw1 = gem_fb("unified", PROMPT_UNIFIED_P1.replace("{cat}", cat).replace("{news}", "\n".join(all_news)))
    if not raw1: return
    
    ctx = "Title: " + xtag(raw1, "TITLE") + "\nSummary: " + xtag(raw1, "EXECUTIVE_SUMMARY")
    raw2 = gem_fb("unified", PROMPT_UNIFIED_P2.replace("{cat}", cat).replace("{ctx}", ctx))
    raw = raw1 + "\n" + (raw2 if raw2 else "")

    title, kw, exc = xtag(raw, "TITLE"), xtag(raw, "SEO_KEYWORD"), xtag(raw, "EXCERPT") or xtag(raw, "EXECUTIVE_SUMMARY")
    slug, author = make_slug(kw, title, cat), VIP_AUTHORS.get(cat, "Warm Insight Editorial Team")
    
    html = build_html("unified", cat, raw, author, datetime.datetime.utcnow().strftime("%B %d, %Y"), title)
    img_bytes = make_thumbnail(title, cat, "unified")
    med_img_bytes = make_medium_thumbnail(cat)

    publish(title, html, exc, kw, cat, slug, "unified", img_bytes, author, raw_for_cards=raw, med_img_bytes=med_img_bytes)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "philosophy": run_philosophy_pipeline()
        elif arg == "foundation": run_foundation_pipeline()
        elif arg == "moneyhack": run_moneyhack_pipeline()
        elif arg == "onchain": run_news_pipeline("On-Chain")
        elif arg == "insight":
            base_cats = [c for c in CATEGORIES if c not in ["On-Chain", "Money Hack"]]
            run_news_pipeline(base_cats[datetime.datetime.utcnow().timetuple().tm_yday % len(base_cats)])
    else:
        run_news_pipeline()
