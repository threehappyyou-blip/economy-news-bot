#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v45.9 (YouTube Script Automation Update)
#
# v45.8 → v45.9 핵심 변경 사항:
#   1. 유튜브 롱폼 대본(20,000자 이상) 자동 생성 및 이메일 전송 기능 추가
#   2. 대본 분량 미달 시 AI 자동 재시도(Validation) 로직 추가
#   3. 유튜브 전용 프롬프트(알고리즘 최적화, 극사실주의 썸네일, 3단 훅 제목) 적용
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
# CONFIG
# ═══════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
WP_URL         = os.environ.get("WP_URL", "https://warminsight.com").rstrip("/")
WP_USER        = os.environ.get("WP_USERNAME", "")
WP_APP_PASS    = os.environ.get("WP_APP_PASSWORD", "")
SITE_URL       = "https://warminsight.com"

# 🚨 이메일 발송용 정보
EMAIL_SENDER   = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASS     = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "")
YOUTUBE_EMAIL_RECEIVER = "jh0116jh@gmail.com" # 유튜브 대본을 받을 전용 이메일

# 유튜브 대본처럼 매우 긴 글을 쓰기 위해 2.5-pro 모델 우선 배정
MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
    "Premium": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"], # Pro 모델 우선
    "unified": ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
}
FAST_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]

CATEGORIES  = ["Economy", "Politics", "Tech", "Health", "Energy"]
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
}

CAT_RELATED = {
    "Economy":  ["Tech", "Energy"],
    "Politics": ["Economy", "Tech"],
    "Tech":     ["Economy", "Health"],
    "Health":   ["Economy", "Politics"],
    "Energy":   ["Economy", "Politics"],
}

VIP_AUTHORS = {
    "Economy":  "Warm Insight Editorial Team",
    "Politics": "Warm Insight Editorial Team",
    "Tech":     "Warm Insight Editorial Team",
    "Health":   "Warm Insight Editorial Team",
    "Energy":   "Warm Insight Editorial Team",
    "The Daily Catalyst": "Warm Insight Editorial Team",
    "Foundation": "Warm Insight Editorial Team"
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
}

CAT_ALLOC = {
    "Economy": {"s": 55, "b": 35, "c": 10, "note": "Defensive: higher bonds during macro uncertainty"},
    "Politics": {"s": 50, "b": 35, "c": 15, "note": "Elevated cash for geopolitical shock absorption"},
    "Tech": {"s": 70, "b": 20, "c": 10, "note": "Growth tilt: overweight innovation equities"},
    "Health": {"s": 60, "b": 30, "c": 10, "note": "Balanced: pharma stability with biotech upside"},
    "Energy": {"s": 65, "b": 25, "c": 10, "note": "Commodity tilt: overweight real assets"},
}

# ═══════════════════════════════════════════════
# 🎬 1. YOUTUBE SCRIPT ENGINE (NEW)
# ═══════════════════════════════════════════════
YOUTUBE_SYS_INST = """You are a top-tier YouTube Scriptwriter and Growth Hacker for an economics/investment channel named "Warm Insight".
Your objective is to convert the provided newsletter text into a HIGHLY ENGAGING, FACT-BASED, FEATURE-LENGTH DOCUMENTARY YouTube script.

[STRICT CRITICAL REQUIREMENTS]
1. LENGTH CONSTRAINT: The VREW_SCRIPT section MUST BE MASSIVE. It must exceed 20,000 characters. To achieve this, do not just summarize. You must EXPAND deeply:
   - For every single point, provide rich historical context (e.g., comparing it to 2008, 1999, or 1970s).
   - Use vivid, highly descriptive analogies for normal people.
   - Explain the psychological reasons behind the market moves.
   - Speak slowly, deeply, and thoughtfully in the prose.
2. ACCURACY & VALUE: NO hallucinations. 100% factual. The script must genuinely help viewers understand the global economy. Explain complex terms simply.
3. OUTPUT FORMAT: You MUST wrap your response exactly in the XML tags requested."""

YOUTUBE_PROMPT = """Based on the following newsletter content, generate a YouTube Metadata package and a massive 20,000+ character documentary script.

[NEWSLETTER CONTENT]
{raw_content}

[OUTPUT FORMAT]
You must strictly use these XML tags:

<METADATA>
1. VIRAL TITLES (Exactly 3 options. Make them hyper-clickable using a 'Curiosity Gap' or 'Ultimate Benefit'. NO clichés like 'What 90% don't know'. Must be very punchy.)
- Option A: 
- Option B: 
- Option C: 

2. THUMBNAIL PROMPT (MUST be Highly Realistic/Cinematic Style. Detail the exact text overlay taking up the top third of the image. E.g., 'A highly realistic cinematic shot of... The text is bright yellow with black outline saying [PUNCHY 3 WORDS]')

3. CROSS-POLLINATION (Use this exact text): "👇 Check out the Warm Insight newsletter for a deeper dive: www.warminsight.com"

4. SEO HASHTAGS: (10 highly searched global tags)
</METADATA>

<VREW_SCRIPT>
(OUTPUT ONLY SPOKEN WORDS. NO structural tags like [VO], [Scene 1], etc. ONLY text to be read by TTS.
Start immediately with a provocative cold open hook, followed by: "Hello, this is Warm Insight. Today, we're going to talk about [Topic]. Leaving a like and subscribing is a huge help to us!"
EXPAND MASSIVELY. Use deep storytelling, historical facts, and analogies. The script must be incredibly long and detailed.
End exactly with: "We couldn't fit all the deep-dive details and practical strategies into this video. Check out the Warm Insight newsletter in the pinned comment and description for the full text summary. Visit www.warminsight.com. See you there.")
</VREW_SCRIPT>
"""

def generate_youtube_script(raw_content, title):
    print(f"   🎬 [YouTube] Generating 20,000+ character documentary script for '{title[:30]}...'")
    client = _get_gemini_client()
    prompt = YOUTUBE_PROMPT.replace("{raw_content}", raw_content)
    
    best_meta = ""
    best_script = ""
    
    # 20,000자 달성을 위한 Validation 루프 (최대 3회 재시도)
    for attempt in range(1, 4):
        print(f"      ▶ Attempt {attempt}/3 to generate massive script...")
        response = gem_fb("Premium", prompt, YOUTUBE_SYS_INST) # 가장 똑똑한 모델 사용
        
        meta = xtag(response, "METADATA")
        script = xtag(response, "VREW_SCRIPT")
        
        char_count = len(script)
        print(f"      ✅ Generated {char_count:,} characters.")
        
        # 가장 긴 스크립트 저장
        if char_count > len(best_script):
            best_script = script
            best_meta = meta
            
        # 15,000자(API 한계 고려 현실적 타협선) 이상이면 성공으로 간주하고 루프 종료
        # (프롬프트에는 2만자로 강제하여 최대한 길게 뽑아냄)
        if char_count >= 15000:
            print("      🎯 Script length validation passed!")
            break
        else:
            print("      ⚠️ Script too short. Asking AI to expand deeper...")
            prompt += "\n\n[CRITICAL FEEDBACK] Your previous script was too short. You MUST dive much deeper into the historical contexts and analogies to make the script significantly longer."

    return best_meta, best_script

def send_youtube_script_email(post_title, meta, script):
    if not EMAIL_SENDER or not EMAIL_PASS:
        return
        
    print(f"   📧 Sending YouTube Script to {YOUTUBE_EMAIL_RECEIVER}...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = YOUTUBE_EMAIL_RECEIVER
        msg['Subject'] = f"🎬 [유튜브 대본 완성] {post_title[:40]}"

        body = f"""
        <div style="font-family: -apple-system, sans-serif; background: #f8fafc; padding: 20px;">
            <div style="max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                
                <div style="background: #ef4444; padding: 25px; text-align: center; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 24px;">🎬 Warm Insight YouTube Vrew Script</h2>
                    <p style="margin: 10px 0 0; opacity: 0.9;">Total Characters: <strong>{len(script):,}</strong></p>
                </div>
                
                <div style="padding: 30px;">
                    <h3 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">📋 YouTube Metadata</h3>
                    <div style="background: #f1f5f9; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-size: 15px; color: #334155; line-height: 1.6;">{meta}</div>
                    
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
        print("   ✅ 유튜브 대본 이메일 발송 완료!")
    except Exception as e:
        print(f"   ❌ 유튜브 대본 이메일 전송 실패: {e}")

# ═══════════════════════════════════════════════
# ✉️ 슬림 이메일 (인스타/숏폼용)
# ═══════════════════════════════════════════════
def send_social_style_email(title, link, image_bytes_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS or not EMAIL_RECEIVER:
        return

    print(f"   📧 {EMAIL_RECEIVER}로 인스타/숏폼 패키지를 전송합니다...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = f"📱 {cat.upper()} SHORTS READY: {hook_text[:40]}..."

        vid_tag = ""
        if video_mp4_bytes:
            vid_tag = f"""
            <div style="margin-bottom: 25px; text-align:center; padding: 25px; background: #0f172a; border-radius: 16px; border: 2px solid #10b981;">
                <p style="color: #10b981; font-weight: 900; font-size: 18px; margin-top: 0; text-transform: uppercase;">🎬 20-Sec Reels Video Attached!</p>
                <div style="font-size: 45px; margin: 15px 0;">✨ 📹 ✨</div>
                <p style="color: #ffffff; font-size: 15px; font-weight: bold; margin: 5px 0;">인스타 릴스 / 틱톡 / 유튜브 쇼츠 100% 호환 영상입니다.</p>
                <p style="color: #94a3b8; font-size: 13px; margin-bottom: 0; margin-top: 10px;">하단 첨부파일 <strong>WarmInsight_{cat}_Video.mp4</strong> 를 다운로드 후 바로 업로드하세요.</p>
            </div>
            """

        body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f4f4f5; padding: 20px; color: #0f1419;">
            {vid_tag}
            <div style="background: #ffffff; border-left: 5px solid #eab308; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #ca8a04; font-size: 18px;">🎬 1-Min Reels Script</h3>
                <p style="font-size: 14px; color: #52525b; margin-bottom: 15px;">이 대본을 보고 말하거나 AI 보이스에 넣어 릴스를 제작하세요.</p>
                <div style="background: #fefce8; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; font-style: italic;">
                    {reels_script.replace(chr(10), '<br>')}
                </div>
            </div>
            <div style="background: #ffffff; border-left: 5px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #2563eb; font-size: 18px;">💬 Smart Community Comment</h3>
                <p style="font-size: 14px; color: #52525b; margin-bottom: 15px;">Bloomberg, WSJ 등 유명 인스타 계정 최신 글에 이 댓글을 복사해 붙여넣으세요.</p>
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; font-size: 15px; font-weight: bold; color: #1e3a8a;">
                    "{smart_comment}"
                </div>
            </div>
            <div style="background: #ffffff; border-left: 5px solid #10b981; padding: 20px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h3 style="margin-top: 0; color: #059669; font-size: 18px;">📱 Instagram Feed Caption</h3>
                <p style="font-size: 14px; color: #52525b; margin-bottom: 15px;">영상 업로드 시 아래 텍스트를 그대로 복사해서 쓰세요.</p>
                <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; font-size: 15px; line-height: 1.6; white-space: pre-wrap;">{ig_caption}</div>
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
        print("   ✅ 인스타/숏폼 이메일 발송 완료!")
    except Exception as e:
        print(f"   ❌ 인스타/숏폼 이메일 전송 실패: {e}")

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
    try:
        resp = requests.get(f"{WP_URL}/wp-json/wp/v2/users/me", auth=(WP_USER, WP_APP_PASS), timeout=10)
        if resp.status_code == 200: return True
    except: pass
    print("❌ WP Auth Failed. Check your App Password.")
    return False

def call_gemini(client, model, prompt, sys_inst=None, retries=5):
    if not sys_inst:
        sys_inst = "You are an elite financial analyst. You MUST strictly follow the required output format. You MUST wrap EVERY section of your response in the exact XML tags requested."

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
                print("    🚨 크레딧이 모두 소진되었습니다!")
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

# ═══════════════════════════════════════════════
# 🆕 이미 발행된 카테고리 체크
# ═══════════════════════════════════════════════
def already_published_today(cat):
    try:
        today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        cat_slug = cat.lower().replace(" ", "-")

        r = requests.get(
            f"{WP_URL}/wp-json/wp/v2/categories?slug={cat_slug}",
            auth=(WP_USER, WP_APP_PASS), timeout=10
        )
        if r.status_code != 200 or not r.json():
            return False
        cat_id = r.json()[0]["id"]

        r2 = requests.get(
            f"{WP_URL}/wp-json/wp/v2/posts",
            params={
                "categories": cat_id,
                "after": f"{today_str}T00:00:00",
                "before": f"{today_str}T23:59:59",
                "per_page": 1,
                "status": "publish"
            },
            auth=(WP_USER, WP_APP_PASS), timeout=10
        )
        if r2.status_code == 200 and len(r2.json()) > 0:
            print(f"   ⏭️  [{cat}] Already published today: {r2.json()[0].get('link', '')}")
            return True
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
            d = feedparser.parse(url)
            for e in d.entries[:40]:
                title = getattr(e, 'title', '').strip()
                summary = re.sub(r'<[^>]+>', '', getattr(e, 'summary', ''))[:200].strip()
                if title and len(title) > 10: items.add(f"• {title}: {summary}")
        except: pass
    items_list = list(items)
    random.shuffle(items_list)
    return items_list[:max_items]

# ═══════════════════════════════════════════════
# 🧠 1. FOUNDATION DATABASE & PROMPTS
# ═══════════════════════════════════════════════
FOUNDATION_TOPICS = [
    "What is an ETF? The Beginner's Guide to Exchange Traded Funds",
    "Dollar Cost Averaging (DCA): How to Invest Safely in Volatile Markets",
    "Understanding Inflation: How it Affects Your Savings and Investments",
    "Bull Market vs Bear Market: Simple Explanations for Beginners",
    "Asset Allocation 101: Why You Shouldn't Put All Your Eggs in One Basket",
    "Compound Interest Explained: The Magic of Growing Your Wealth Over Time",
    "What are Dividends? Building a Passive Income Stream",
    "Growth Stocks vs Value Stocks: Which Investing Style is Right for You?",
    "Understanding Interest Rates: How the Federal Reserve Moves the Market",
    "The Difference Between Stocks and Bonds: A Beginner's Overview"
]

FOUNDATION_SYS_INST = """You are the "smart friend" who explains money to absolute beginners.
YOUR PERSONALITY: Text your friend the news, not write a textbook.
EMOJI POLICY: 💡 👀 🚨 🤔 💸 (3-5 per article).
WRITING RULES: Max 15 words per sentence. Max 3 sentences per paragraph. Start sentences with "And", "But", "So".
You MUST wrap your content EXACTLY in the XML tags requested."""

FOUNDATION_PROMPT = """Write an SEO-optimized beginner's guide on the following topic:
TOPIC: {theme}

OUTPUT FORMAT REQUIREMENT:
You MUST output your response by wrapping your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include SEO_KEYWORD.)</TITLE>
<SEO_KEYWORD>(LONG-TAIL focus keyword, 3-5 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. Strong hook.)</EXCERPT>
<DEFINITION>(2-paragraph definition using an easy everyday analogy.)</DEFINITION>
<WHY_MATTERS>(Explain in 2 paragraphs why a beginner should care.)</WHY_MATTERS>
<HOW_TO_START>(3 simple actionable steps.)</HOW_TO_START>
"""

# ═══════════════════════════════════════════════
# 🧠 2. PHILOSOPHY DATABASE & PROMPTS
# ═══════════════════════════════════════════════
PHILOSOPHY_TOPICS = [
    "돈을 짝사랑하지 말고 행동으로 사랑하라",
    "부를 담을 심리적 그릇과 책임의 무게",
    "자발적 피로: 성장을 위한 쾌락적 고통",
    "환경적 결핍을 폭발적 성장의 무기로 삼아라",
    "소비자에서 생산자로: 읽기에서 쓰기로의 전환",
    "스스로 설정한 인지적 연봉 상한선을 파괴하라",
    "핑계의 소거: 타협 없는 성장의 시작"
]

PHILOSOPHY_SYS_INST = """You are an elite philosophical life strategist.
Speak to the reader as a strict, wise mentor who demands action. Short, plain sentences.
You MUST wrap your content EXACTLY in the XML tags requested."""

PHILOSOPHY_PROMPT = """Write a philosophical daily insight based on the following theme:
THEME: {theme}

OUTPUT FORMAT REQUIREMENT:
You MUST output your response by wrapping your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include SEO_KEYWORD.)</TITLE>
<SEO_KEYWORD>(LONG-TAIL focus keyword, 3-5 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. Strong hook.)</EXCERPT>
<ANCHOR>(One-sentence philosophical principle.)</ANCHOR>
<REFLECTION>(3-4 paragraphs explaining modern reality vs this principle.)</REFLECTION>
<CATALYST>(A single, highly provocative question for action.)</CATALYST>
"""

# ═══════════════════════════════════════════════
# 🎨 3. TWO-PART PROMPTS (REGULAR NEWS)
# ═══════════════════════════════════════════════
PROMPT_UNIFIED_P1 = """You are Warm Insight's lead writer.
Imagine your reader is Sarah, a 32-year-old manager. Give her ONE thing she didn't know.
REQUIRED: ONE counterintuitive insight, AT LEAST 3 specific numbers, AT LEAST 1 company move, ONE historical reference.
RULES: Sentences MAX 15 words. Paragraphs MAX 3 sentences. No clichés.

Write PART 1 of an Insight newsletter on {cat}.
News Context: {news}

OUTPUT FORMAT REQUIREMENT (WRAP EXACTLY IN XML):

<TITLE>(Max 60 chars. Highly clickable.)</TITLE>
<SEO_KEYWORD>(LONG-TAIL keyword, 3-5 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. Hook.)</EXCERPT>
<IMPACT>(HIGH, MEDIUM, or LOW)</IMPACT>
<DATA_TABLE>(Asset Name | Value | UP/DOWN/SIDEWAYS | 1 sentence insight)</DATA_TABLE>
<HEATMAP>(Sector Name | Number 0-100)</HEATMAP>
<EXECUTIVE_SUMMARY>(3 sentences capturing your thesis. Start with "OK so...")</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>(ONE specific vivid analogy. 20+ words.)</PLAIN_ENGLISH>
<HEADLINE>(Analytical headline.)</HEADLINE>
<MACRO>(2 PARAGRAPHS. What's happening + WHY it's happening.)</MACRO>
<HERD>(1 paragraph showing retail investor mistakes.)</HERD>
<CONTRARIAN>(1 paragraph showing smart money moves.)</CONTRARIAN>
<QUICK_FLOW>(Chain of events with ➡️ arrows.)</QUICK_FLOW>"""

PROMPT_UNIFIED_P2 = """Write PART 2 of the Insight newsletter for {cat}.
Context from Part 1: {ctx}

OUTPUT FORMAT REQUIREMENT (WRAP EXACTLY IN XML):

<BULL_CASE>(Optimistic scenario. 3-4 sentences.)</BULL_CASE>
<BEAR_CASE>(Pessimistic scenario. 3-4 sentences.)</BEAR_CASE>
<HISTORICAL_PARALLEL>(2 sentences MAX. Name year+event. What's different.)</HISTORICAL_PARALLEL>
<QUICK_HITS>(3 bullet points starting with 🚨 / 👀 / 🤔 / 💸)</QUICK_HITS>
<SMART_MONEY_MOVE>(1 paragraph. Specific ETF ticker + Action.)</SMART_MONEY_MOVE>
<DO_ACTION>(1-2 specific actions. Include ticker, price, or date.)</DO_ACTION>
<DONT_ACTION>(1 critical mistake to avoid. Start with "Don't" or "Stop".)</DONT_ACTION>
<TAKEAWAY>(Bottom line insight. Under 20 words.)</TAKEAWAY>
<PS>(One-line veteran advice.)</PS>"""

# ═══════════════════════════════════════════════
# 📊 VISUAL DATA BUILDERS & HTML
# ═══════════════════════════════════════════════
def _build_data_table(raw_data, title="Market Dashboard"):
    if not raw_data:
        raw_data = """S&P 500 | 5,234 | UP | Index near recent highs
Nasdaq 100 | 18,200 | UP | Tech leading the broader market
10Y Treasury Yield | 4.25% | SIDEWAYS | Rate cut bets keeping yields contained
VIX | 14.2 | DOWN | Volatility surprisingly low"""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if len(lines) < 2:
        lines = ["S&P 500 | 5,234 | UP | Index near recent highs", "Nasdaq 100 | 18,200 | UP | Tech leading the broader market"]
    html = f"""<div style="background:#ffffff; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; font-size:20px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:12px;">📊 {title}</h3>
        <div style="overflow-x:auto; margin-top:15px;"><table style="width:100%; border-collapse:collapse; font-family:-apple-system,sans-serif;">
            <thead><tr style="background:{BG_LIGHT}; text-align:left; border-bottom:2px solid {BORDER};">
                <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Asset/Metric</th>
                <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Status</th>
                <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Trend</th>
                <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Key Insight</th>
            </tr></thead><tbody>"""
    for line in lines[:5]:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            asset, value, trend, insight = parts[:4]
            t_upper = trend.upper()
            if "UP" in t_upper or "BULL" in t_upper or "HIGH" in t_upper: t_color, t_icon = "#10b981", "🟢"
            elif "DOWN" in t_upper or "BEAR" in t_upper or "LOW" in t_upper: t_color, t_icon = "#ef4444", "🔴"
            else: t_color, t_icon = "#f59e0b", "🟡"
            html += f'<tr style="border-bottom:1px solid {BORDER};"><td style="padding:14px; font-weight:600; color:{DARK};">{asset}</td><td style="padding:14px; color:{SLATE}; font-family:monospace; font-size:15px; font-weight:bold;">{value}</td><td style="padding:14px; font-weight:bold; color:{t_color};">{t_icon} {trend.upper()}</td><td style="padding:14px; color:{MUTED}; font-size:15px; line-height:1.6;">{insight}</td></tr>'
    html += "</tbody></table></div></div>"
    return html

def _build_progress_bars(raw_data, title="Sector Risk Heatmap"):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""
    html = f'<div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;"><h3 style="margin-top:0; font-size:20px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:12px;">🌡️ {title}</h3>'
    colors = ["#dc2626", "#ea580c", "#ca8a04", "#059669", "#3b82f6"]
    for line in lines[:5]:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:
            name = parts[0]
            try: pct = max(0, min(100, int(re.sub(r'[^0-9]', '', parts[1]))))
            except: pct = 50
            c = colors[0] if pct > 75 else (colors[1] if pct > 50 else (colors[3] if pct < 30 else colors[2]))
            html += f'<div style="margin-top:18px;"><div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span style="font-weight:600; font-size:15px; color:{DARK};">{name}</span><span style="font-weight:900; font-size:15px; color:{c};">{pct}%</span></div><div style="background:#e2e8f0; height:12px; border-radius:6px; overflow:hidden;"><div style="background:{c}; height:100%; width:{pct}%; border-radius:6px;"></div></div></div>'
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
        items_html += f'<li style="margin-bottom:12px; color:{SLATE};">{clean}</li>'
    return f'<div style="background:#f1f5f9; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;"><h3 style="margin-top:0; font-size:20px; color:{DARK}; text-transform:uppercase; letter-spacing:1px;">⚡ Quick Hits</h3><ul style="{F} margin:0; padding-left:20px;">{items_html}</ul></div>'

def _build_pie_chart(s, b, c, cat):
    cat_colors = {"Economy": ("#2563eb", "#60a5fa", "#dbeafe"), "Politics": ("#dc2626", "#f87171", "#fee2e2"), "Tech": ("#7c3aed", "#a78bfa", "#ede9fe"), "Health": ("#059669", "#34d399", "#d1fae5"), "Energy": ("#d97706", "#fbbf24", "#fef3c7")}
    c_s, c_b, c_c = cat_colors.get(cat, ("#b8974d", "#cbd5e1", "#f1f5f9"))
    circ = 565.49
    sd, bd, cd = circ*s/100, circ*b/100, circ*c/100
    pie = f'<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;"><circle cx="100" cy="100" r="90" fill="none" stroke="{c_s}" stroke-width="30" stroke-dasharray="{sd} {circ}" stroke-dashoffset="0"/><circle cx="100" cy="100" r="90" fill="none" stroke="{c_b}" stroke-width="30" stroke-dasharray="{bd} {circ}" stroke-dashoffset="-{sd}"/><circle cx="100" cy="100" r="90" fill="none" stroke="{c_c}" stroke-width="30" stroke-dasharray="{cd} {circ}" stroke-dashoffset="-{sd+bd}"/><text x="100" y="95" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">{s}/{b}/{c}</text><text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>'
    pie += f'<div style="display:flex;justify-content:center;gap:20px;"><span style="color:{c_s};font-weight:bold;">● Stocks {s}%</span><span style="color:{c_b};font-weight:bold;">● Safe {b}%</span><span style="color:{c_c};font-weight:bold;">● Cash {c}%</span></div>'
    return pie

def _build_pillar_link(target_cat):
    pillar = PILLAR_PAGES.get(target_cat)
    if not pillar: return ""
    return f'<div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:20px; margin:40px 0; border-radius:4px; box-shadow:0 2px 4px rgba(0,0,0,0.02);"><p style="margin:0; font-size:16px; color:#1e293b;"><strong style="color:#2563eb;">📚 Deep Dive:</strong> Want to master this topic? Check out our complete guide to <a href="{pillar["url"]}" style="color:#2563eb; text-decoration:underline; font-weight:700;">{pillar["anchor"]}</a>.</p></div>'

def _build_social_share(title, slug):
    si = '<a href="https://www.youtube.com/@WarmInsightyou" target="_blank" style="display:inline-block; background:#FF0000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">▶ YouTube</a><a href="https://www.tiktok.com/@warminsight" target="_blank" style="display:inline-block; background:#000000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">🎵 TikTok</a>'
    return f'<div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:10px; padding:28px; margin:40px 0; text-align:center;"><p style="font-size:20px; font-weight:bold; color:{DARK}; margin:0 0 10px;">Found this useful? Share the insight.</p><p style="font-size:15px; color:{MUTED}; margin:0 0 18px;">Forward to a friend who wants smarter market analysis.</p><div style="margin-bottom:14px;">{si}</div><p style="margin:0;"><a href="{SITE_URL}" style="color:{GOLD}; font-weight:600; text-decoration:underline;">Subscribe at warminsight.com</a></p></div>'

def _build_branded_footer():
    si = '<a href="https://www.youtube.com/@WarmInsightyou" target="_blank" style="display:inline-block; background:#FF0000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">▶ YouTube</a><a href="https://www.tiktok.com/@warminsight" target="_blank" style="display:inline-block; background:#000000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">🎵 TikTok</a>'
    return f'<div style="background:{DARK}; padding:35px; border-radius:10px; margin-top:30px;"><p style="font-size:24px; font-weight:bold; color:{GOLD}; margin:0 0 12px; text-align:center;">Warm Insight</p><p style="font-size:14px; color:#94a3b8; text-align:center; margin:0 0 16px;">AI-Driven Global Market Analysis</p><div style="text-align:center; margin-bottom:16px;">{si}</div><div style="text-align:center; margin-bottom:16px; font-size:13px;"><a href="{SITE_URL}/about-us/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">About</a><a href="{SITE_URL}/privacy-policy/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">Privacy</a><a href="{SITE_URL}/terms/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">Terms</a></div><p style="font-size:13px; color:#64748b; margin:0; text-align:center;">All analysis is for informational purposes only. Not financial advice.<br>&copy; 2026 Warm Insight. All rights reserved.</p></div>'

def _build_author_bio(cat):
    author = VIP_AUTHORS.get(cat, "Warm Insight Editorial Team")
    return f'<div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:10px; padding:24px; margin:35px 0; display:flex; gap:20px; align-items:center;"><div style="min-width:56px; height:56px; border-radius:50%; background:{GOLD}; display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:700; color:#fff;">W</div><div><p style="font-size:17px; font-weight:700; color:{DARK}; margin:0 0 6px;">{author}</p><p style="font-size:14px; color:{MUTED}; margin:0; line-height:1.6;">AI-powered financial analysis, curated and edited by Jiho, founder of Warm Insight. We translate Wall Street complexity into clear insights for everyday investors.</p></div></div>'

def _build_founder_note():
    return f'<div style="background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%); border:2px solid {GOLD}; border-radius:14px; padding:30px; margin:40px 0;"><div style="display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap;"><div style="min-width:70px; height:70px; border-radius:50%; background:{GOLD}; display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:900; color:#fff;">J</div><div style="flex:1; min-width:250px;"><p style="font-size:13px; font-weight:800; color:#92400e; margin:0 0 6px; text-transform:uppercase; letter-spacing:1.5px;">A NOTE FROM THE FOUNDER</p><p style="font-size:18px; font-weight:700; color:{DARK}; margin:0 0 10px; line-height:1.4;">Hey, I\'m Jiho. I built Warm Insight because I was tired of finance content being either too dumbed-down or too academic.</p><p style="font-size:15px; color:{SLATE}; margin:0; line-height:1.6;">Every article here is designed to give you ONE thing: a clearer view of your money than you had 5 minutes ago. If it ever stops doing that, tell me directly. I read every reply.</p></div></div></div>'

# ═══════════════════════════════════════════════
# 🎨 HTML BUILDERS
# ═══════════════════════════════════════════════
def build_foundation_html(raw, author, tf, title, cat):
    html = f'<div style="{F}"><div style="border-top:4px solid #10b981; border-bottom:1px solid {BORDER}; padding:18px 0; margin-bottom:35px;"><p style="margin:0 0 6px; font-size:15px; color:{MUTED};"><strong style="color:{DARK};">By {author}</strong> &nbsp;|&nbsp; {tf} <span style="background:#10b981; color:#fff; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">BEGINNER\'S GUIDE</span></p><p style="margin:0; font-size:13px; color:{MUTED}; font-style:italic;">Edited by Jiho, Founder</p></div>'
    html += f'<div style="background:#f0fdf4; border-left:5px solid #10b981; padding:25px; margin:30px 0; border-radius:0 8px 8px 0;"><h3 style="margin-top:0; font-size:22px; color:#065f46;">📖 What is it? (Definition)</h3><div style="color:#064e3b; font-size:18px; line-height:1.8;">{xtag(raw, "DEFINITION").replace(chr(10), "<br><br>")}</div></div>'
    html += f'<div style="margin:40px 0;"><h3 style="font-size:24px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">💡 Why It Matters</h3><p>{xtag(raw, "WHY_MATTERS").replace(chr(10), "<br><br>")}</p></div>'
    html += f'<div style="background:#ffffff; border:2px solid #3b82f6; padding:30px; border-radius:12px; margin:40px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);"><h3 style="margin-top:0; color:#1e40af; font-size:24px;">🚀 How to Start Today</h3><div style="color:{SLATE}; font-size:18px; line-height:1.8;">{xtag(raw, "HOW_TO_START").replace(chr(10), "<br><br>")}</div></div>'
    html += _build_pillar_link("Foundation") 
    html += '<div style="margin: 40px 0; text-align: center;"><a href="#respond" style="display: flex; justify-content: center; align-items: center; width: 100%; max-width: 400px; margin: 0 auto; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; padding: 18px 20px; border-radius: 50px; font-family: \'Inter\', sans-serif; font-size: 1.15rem; font-weight: 800; text-decoration: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); line-height: 1;">💬 Share Your Thoughts ↓</a></div>'
    html += _build_social_share(title, make_slug(xtag(raw, "SEO_KEYWORD"), title, "foundation"))
    html += _build_founder_note()
    html += _build_branded_footer()
    html += f'<p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">Disclaimer: Educational content only.</p></div>'
    return sanitize(html)

def build_philosophy_html(raw, author, tf, title, cat):
    html = f'<div style="{F}"><div style="border-top:4px solid {GOLD}; border-bottom:1px solid {BORDER}; padding:18px 0; margin-bottom:35px;"><p style="margin:0 0 6px; font-size:15px; color:{MUTED};"><strong style="color:{DARK};">By {author}</strong> &nbsp;|&nbsp; {tf} <span style="background:{DARK}; color:{GOLD}; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">DAILY INSIGHT</span></p><p style="margin:0; font-size:13px; color:{MUTED}; font-style:italic;">Edited by Jiho, Founder</p></div>'
    html += f'<div style="text-align:center; margin:50px 0;"><span style="font-size:40px; color:{GOLD}; line-height:1;">❝</span><h2 style="font-family:Georgia,serif; font-size:26px; color:{DARK}; margin:10px 0; font-weight:600; line-height:1.4;">{xtag(raw, "ANCHOR")}</h2><span style="font-size:40px; color:{GOLD}; line-height:1;">❞</span></div>'
    html += f'<div style="margin:40px 0;"><h3 style="font-size:22px; color:{DARK}; border-left:4px solid {GOLD}; padding-left:12px; margin-bottom:20px;">The Reflection</h3><div style="color:{SLATE}; font-size:18px; line-height:1.8;">{xtag(raw, "REFLECTION").replace(chr(10), "<br><br>")}</div></div>'
    html += f'<div style="background:#fefce8; border:2px solid #fde047; padding:35px; border-radius:12px; margin:50px 0; text-align:center; box-shadow:0 10px 15px -3px rgba(0, 0, 0, 0.05);"><p style="font-size:14px; font-weight:800; color:#b45309; text-transform:uppercase; letter-spacing:2px; margin:0 0 15px;">⚡ The Daily Catalyst</p><p style="font-size:24px; font-weight:900; color:#92400e; margin:0 0 20px; line-height:1.5;">{re.sub(r"<[^>]+>", "", xtag(raw, "CATALYST"))}</p><p style="font-size:15px; color:#b45309; margin:0; font-style:italic;">Don\'t just read. Take out a pen and write your answer now.</p></div>'
    html += _build_pillar_link("The Daily Catalyst") 
    html += '<div style="margin: 40px 0; text-align: center;"><a href="#respond" style="display: flex; justify-content: center; align-items: center; width: 100%; max-width: 400px; margin: 0 auto; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; padding: 18px 20px; border-radius: 50px; font-family: \'Inter\', sans-serif; font-size: 1.15rem; font-weight: 800; text-decoration: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); line-height: 1;">💬 Share Your Thoughts ↓</a></div>'
    html += _build_social_share(title, make_slug(xtag(raw, "SEO_KEYWORD"), title, "catalyst"))
    html += _build_founder_note()
    html += _build_branded_footer()
    html += f'<p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">Disclaimer: This article is for informational purposes only.</p></div>'
    return sanitize(html)

def build_html(tier, cat, raw, author, tf, title):
    badge_bg = GOLD
    html = f'<div style="{F}"><div style="border-top:4px solid {badge_bg}; border-bottom:1px solid {BORDER}; padding:18px 0; margin-bottom:35px;"><p style="margin:0 0 6px; font-size:15px; color:{MUTED};"><strong style="color:{DARK};">By {author}</strong> &nbsp;|&nbsp; {tf} <span style="background:{badge_bg}; color:#fff; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">WARM INSIGHT</span></p><p style="margin:0; font-size:13px; color:{MUTED}; font-style:italic;">Edited by Jiho, Founder</p></div>'
    html += f'<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {badge_bg}; padding-bottom:10px; display:inline-block;">Executive Summary</h2><p style="font-size:19px; font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>'
    html += _build_founder_note()
    html += _build_data_table(xtag(raw, "DATA_TABLE"), "Market Dashboard")
    html += _build_progress_bars(xtag(raw, "HEATMAP"), "Sector Risk Heatmap")
    html += f'<div style="background:#faf5ff; border-left:5px solid #8b5cf6; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;"><p style="font-size:20px; font-weight:800; color:#4c1d95; margin:0 0 12px;">💡 Plain English</p><p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p></div>'
    html += f'<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {badge_bg}; padding-bottom:10px; display:inline-block; margin-top:30px;">Market Drivers & Flow</h2><h3 style="font-size:24px; color:{DARK}; margin-top:20px;">{xtag(raw, "HEADLINE")}</h3>'
    html += f'<div style="background:#fff; border:1px solid {BORDER}; border-left:5px solid {badge_bg}; padding:30px; border-radius:8px; margin:30px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);"><p><strong>🧐 The Big Picture:</strong> {xtag(raw, "MACRO")}</p><hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;"><p><strong>🐑 What Most People Are Doing:</strong> {xtag(raw, "HERD")}</p><hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;"><p><strong>🦅 What Smart Money Is Doing:</strong> {xtag(raw, "CONTRARIAN")}</p></div>'
    html += f'<div style="background:#fffbeb; border:1px solid #fde68a; border-left:5px solid {AMBER}; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;"><strong style="color:#92400e; font-size:20px;">🔗 Chain of Events:</strong><br><span style="font-weight:bold; font-size:19px; color:{DARK}; display:inline-block; margin-top:12px;">{xtag(raw, "QUICK_FLOW")}</span></div>'
    html += f'<div style="display:flex; flex-wrap:wrap; gap:20px; margin:40px 0;"><div style="flex:1; min-width:250px; background:#ecfdf5; border:2px solid #10b981; border-radius:8px; padding:25px;"><h4 style="margin-top:0; font-size:22px; color:#065f46;">🐂 Bull Case</h4><p style="margin:0; color:#064e3b;">{xtag(raw, "BULL_CASE")}</p></div><div style="flex:1; min-width:250px; background:#fef2f2; border:2px solid #ef4444; border-radius:8px; padding:25px;"><h4 style="margin-top:0; font-size:22px; color:#991b1b;">🐻 Bear Case</h4><p style="margin:0; color:#7f1d1d;">{xtag(raw, "BEAR_CASE")}</p></div></div>'
    html += _build_quick_hits(xtag(raw, "QUICK_HITS"))
    html += f'<div style="background:#ffffff; border:2px solid {badge_bg}; padding:30px; border-radius:8px; margin:45px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);"><h3 style="margin-top:0; color:{badge_bg}; font-size:24px;">💎 Smart Money Move</h3><p style="margin:0;">{xtag(raw, "SMART_MONEY_MOVE")}</p></div>'
    if historical := xtag(raw, "HISTORICAL_PARALLEL"):
        html += f'<div style="background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding:35px; border-radius:12px; margin:45px 0; border-left:5px solid {badge_bg};"><h3 style="color:{badge_bg}; margin-top:0; font-size:24px; display:flex; align-items:center; gap:10px;">📜 Historical Parallel</h3><p style="color:#cbd5e1; font-size:17px; line-height:1.8; margin:15px 0 0;">{historical}</p></div>'
    al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
    html += f'<div style="background:{BG_LIGHT}; border:1px solid {BORDER}; padding:30px; border-radius:8px; margin-bottom:40px;"><h3 style="margin-top:0; font-size:22px; color:{DARK};">📊 Suggested Allocation</h3>{_build_pie_chart(al["s"], al["b"], al["c"], cat)}<p style="margin-top:15px; color:{MUTED}; font-size:14px; text-align:center; font-style:italic;">General guideline based on current {cat} outlook. Not personalized advice.</p></div>'
    html += f'<div style="background:#1e293b; padding:40px; border-radius:12px; margin:45px 0;"><h3 style="color:{badge_bg}; margin-top:0; font-size:26px; border-bottom:2px solid #475569; padding-bottom:15px;">✅ Action Plan</h3><div style="background:#ecfdf5; border:2px solid #10b981; padding:20px; border-radius:8px; margin:25px 0 15px;"><p style="margin:0; color:#065f46; font-size:18px;"><strong>🟢 DO:</strong> {xtag(raw, "DO_ACTION")}</p></div><div style="background:#fef2f2; border:2px solid #ef4444; padding:20px; border-radius:8px;"><p style="margin:0; color:#7f1d1d; font-size:18px;"><strong>🔴 DON\'T:</strong> {xtag(raw, "DONT_ACTION")}</p></div></div>'
    html += f'<hr style="border:0; height:1px; background:{BORDER}; margin:50px 0;"><h2 style="font-family:Georgia,serif; font-size:28px; color:{DARK}; margin-bottom:20px;">Today\'s Warm Insight</h2><p style="{F} font-size:19px; font-style:italic; border-left:3px solid #cbd5e1; padding-left:16px;">"{xtag(raw, "TAKEAWAY")}"</p><div style="background:{DARK}; padding:30px; border-radius:10px; border-left:5px solid {badge_bg}; margin-top:35px;"><p style="color:#e2e8f0; font-size:18px; margin:0; line-height:1.6;"><strong style="color:{badge_bg};">P.S.</strong> {xtag(raw, "PS")}</p></div>'
    html += _build_pillar_link("Insight") 
    html += '<div style="margin: 40px 0; text-align: center;"><a href="#respond" style="display: flex; justify-content: center; align-items: center; width: 100%; max-width: 400px; margin: 0 auto; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; padding: 18px 20px; border-radius: 50px; font-family: \'Inter\', sans-serif; font-size: 1.15rem; font-weight: 800; text-decoration: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); line-height: 1;">💬 Share Your Thoughts ↓</a></div>'
    html += _build_social_share(title, make_slug(xtag(raw, "SEO_KEYWORD"), xtag(raw, "TITLE"), cat))
    html += _build_branded_footer()
    html += _build_author_bio(cat)
    html += f'<p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">Disclaimer: AI-generated, human-edited educational content. Not financial advice. All decisions are your own.</p></div>'
    return sanitize(html)

# ═══════════════════════════════════════════════════════════════
# 🖼️ 썸네일 엔진 
# ═══════════════════════════════════════════════════════════════
def get_font(url, filename):
    if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            resp.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(resp.content)
        except: pass
    return filename

def make_thumbnail(title_text, cat, tier):
    W, H, SCALE = 1200, 630, 2
    w, h = W * SCALE, H * SCALE
    CAT_STYLES = {"Economy": {"bg1": "#0284c7", "bg2": "#0369a1", "acc": "#fde047"}, "Politics": {"bg1": "#dc2626", "bg2": "#991b1b", "acc": "#fde047"}, "Tech": {"bg1": "#6366f1", "bg2": "#4338ca", "acc": "#a78bfa"}, "Health": {"bg1": "#059669", "bg2": "#047857", "acc": "#fef08a"}, "Energy": {"bg1": "#ea580c", "bg2": "#c2410c", "acc": "#fef3c7"}, "The Daily Catalyst": {"bg1": "#1e293b", "bg2": "#0f172a", "acc": "#b8974d"}, "Foundation": {"bg1": "#1e3a5f", "bg2": "#0f2040", "acc": "#f59e0b"}}
    style = CAT_STYLES.get(cat, CAT_STYLES["Economy"])
    AI_PROMPTS = {"Economy": "A minimalist flat vector illustration...", "Politics": "A minimalist...", "Tech": "...", "Health": "...", "Energy": "...", "The Daily Catalyst": "...", "Foundation": "..."}
    img = None
    use_ai_bg = False
    try:
        client = _get_gemini_client()
        result = client.models.generate_images(model='imagen-3.0-generate-001', prompt=AI_PROMPTS.get(cat, AI_PROMPTS["Economy"]), config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg"))
        img = Image.open(io.BytesIO(result.generated_images[0].image.image_bytes)).convert("RGBA").resize((w, h), Image.LANCZOS)
        use_ai_bg = True
    except:
        img = Image.new("RGBA", (w, h), style["bg1"])
        draw = ImageDraw.Draw(img)
        draw.ellipse([w*0.35, -h*0.5, w*1.5, h*1.5], fill=style["bg2"])
    
    draw = ImageDraw.Draw(img)
    if use_ai_bg: draw.rectangle([(0, 0), (w, h)], fill="#1a252c70")
    draw.rectangle([(0, h - 80 * SCALE), (w, h)], fill="#00000060")

    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")
    def lf(p, s):
        try: return ImageFont.truetype(p, s * SCALE)
        except: return ImageFont.load_default()
    ft = lf(ft_path, 85); fs = lf(ft_path, 34); fb = lf(ft_path, 28); f_badge = lf(ft_path, 36); S = SCALE

    date_badge = datetime.datetime.utcnow().strftime("%Y.%m.%d")
    draw.text((40 * S, 44 * S), date_badge, font=fb, fill="#ffffff")
    try: bx = 40 * S + draw.textlength(date_badge, font=fb) + 30 * S
    except: bx = 40 * S + len(date_badge) * 15 * S + 30 * S
    try: cat_w = draw.textlength(cat.upper(), font=fb)
    except: cat_w = len(cat) * 15 * S
    draw.rounded_rectangle([(bx, 36 * S), (bx + cat_w + 60 * S, 86 * S)], radius=25 * S, fill="#ffffff")
    draw.text((bx + 30 * S, 44 * S), cat.upper(), font=fb, fill="#1e293b")

    clean_title = re.sub(r'^WARM INSIGHT\s*[:\-–]\s*', '', _clean_seo_title(title_text).upper()).strip()
    words, lines, line = clean_title.split(), [], []
    mw = w - 100 * S if use_ai_bg else w - 380 * S
    for word in words:
        t = " ".join(line + [word])
        try: tw2 = draw.textlength(t, font=ft)
        except: tw2 = len(t) * 40 * S
        if tw2 < mw: line.append(word)
        else:
            if line: lines.append(" ".join(line))
            line = [word]
    if line: lines.append(" ".join(line))

    y = 160 * S
    for i, ln in enumerate(lines[:4]):
        draw.text((40 * S + 4 * S, y + 4 * S), ln, font=ft, fill="#00000060")
        draw.text((40 * S, y), ln, font=ft, fill="#ffffff" if use_ai_bg else (style.get("acc", "#ffffff") if i == 1 else "#ffffff"))
        try: y += (draw.textbbox((0, 0), ln, font=ft)[3] - draw.textbbox((0, 0), ln, font=ft)[1]) + 15 * S
        except: y += 100 * S

    draw.text((40 * S, h - 70 * S), f"WARM INSIGHT  |  {datetime.datetime.utcnow().strftime('%B %d, %Y')}", font=fs, fill="#ffffff80")
    img = img.convert("RGB").resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

# ═══════════════════════════════════════════════
# 🎬 6-슬라이드 숏폼 카루셀 & 비디오 생성
# ═══════════════════════════════════════════════
def generate_video_mp4(cat, hook_text, data_points, frames_images):
    try:
        import numpy as np
        from moviepy.editor import ImageClip, concatenate_videoclips
    except: return None
    try:
        clips = []
        for i, frame in enumerate(frames_images):
            clip = ImageClip(np.array(frame.convert('RGB'))).set_duration(3.3).set_position(('center', 'center'))
            if i > 0: clip = clip.crossfadein(0.5)
            clips.append(clip)
        video = concatenate_videoclips(clips, padding=-0.5, method="compose")
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False); temp_path = temp_file.name; temp_file.close()
        video.write_videofile(temp_path, fps=30, codec='libx264', bitrate='6000k', audio=False, preset='medium', ffmpeg_params=['-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1:1', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-profile:v', 'main', '-level', '4.0', '-x264-params', 'colorprim=bt709:transfer=bt709:colormatrix=bt709'], logger=None)
        with open(temp_path, 'rb') as f: mp4_bytes = f.read()
        os.remove(temp_path)
        return mp4_bytes
    except: return None

def generate_vip_carousel(raw_content, cat):
    sys_inst = """You are a TOP-TIER viral content creator. Extract data + write COPY THAT STOPS THE SCROLL.
    <MAIN_TITLE>Main viral headline, max 5 words, ALL CAPS</MAIN_TITLE>
    <BADGE>e.g. IMPACT: HIGH</BADGE>
    <HOOK>Scroll-stopping opener (max 7 words)</HOOK>
    <SHOCK_STAT>Jaw-dropping stat (max 6 words, with numbers)</SHOCK_STAT>
    <QUESTION>Engagement question</QUESTION>
    <INSIGHT_LINE>The aha moment (max 8 words)</INSIGHT_LINE>
    <CTA_HOOK>FOMO trigger (max 6 words)</CTA_HOOK>
    <REELS_SCRIPT>60-second spoken script</REELS_SCRIPT>
    <IG_CAPTION>Caption with hook, value, CTA, 15+ hashtags</IG_CAPTION>
    <SMART_COMMENT>Bloomberg/WSJ-style comment for free traffic</SMART_COMMENT>
    <ITEM1>TICKER | Value</ITEM1>
    <ITEM2>TICKER | Value</ITEM2>
    <ITEM3>TICKER | Value</ITEM3>"""
    raw_data = gem_fb("unified", raw_content, sys_inst)
    
    hook_text = xtag(raw_data, "HOOK") or "Wall Street Just Did THIS 🚨"
    data_points = []
    for i in range(1, 4):
        item = xtag(raw_data, f"ITEM{i}")
        if item and "|" in item: data_points.append({"ticker": item.split("|")[0].strip()[:8], "val": item.split("|")[1].strip()})
    if len(data_points) < 3: data_points = [{"ticker": "$NVDA", "val": "+6.2%"}, {"ticker": "$AAPL", "val": "+5.3%"}, {"ticker": "$MSFT", "val": "+4.9%"}]

    W, H, BG, ACCENT, ACCENT_LIGHT, RED, YELLOW = 1080, 1920, "#09090b", "#10b981", "#6ee7b7", "#ef4444", "#fbbf24"
    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")
    def lf(s):
        try: return ImageFont.truetype(ft_path, s)
        except: return ImageFont.load_default()
    font_title, font_mega, font_sub, font_alert = lf(130), lf(160), lf(65), lf(80)

    img1 = Image.new("RGB", (W, H), BG)
    d1 = ImageDraw.Draw(img1)
    d1.rounded_rectangle([60, 280, W-60, 400], radius=60, fill=RED)
    d1.text((W//2, 340), f"🚨 {cat.upper()} ALERT", fill="#ffffff", font=font_alert, anchor="mm")
    
    # 숏폼 영상용 심플 프레임
    all_frames = [img1, img1.copy()] 
    return [], data_points, hook_text, xtag(raw_data, "QUESTION"), xtag(raw_data, "REELS_SCRIPT"), xtag(raw_data, "IG_CAPTION"), xtag(raw_data, "SMART_COMMENT"), generate_video_mp4(cat, hook_text, data_points, all_frames)

# ═══════════════════════════════════════════════
# PUBLISHER & CORE LOGIC
# ═══════════════════════════════════════════════
def _upload_image(img_bytes, filename):
    try:
        resp = requests.post(f"{WP_URL}/wp-json/wp/v2/media", headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"}, data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30)
        if resp.status_code in (200, 201): return resp.json().get("id")
    except: pass
    return None

def get_or_create_wp_category(cat_name):
    slug = cat_name.lower().replace(" ", "-")
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/categories", json={"name": cat_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_or_create_wp_tag(tag_name):
    slug = tag_name.lower().replace(" ", "-")
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/tags?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/tags", json={"name": tag_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_wp_author_id(author_full_string):
    search_name = author_full_string.split("&")[0].strip()
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/users", params={"search": search_name}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, author_name, raw_for_cards=None):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat)
    insight_cat_id = get_or_create_wp_category("Insight") if cat not in ["Foundation", "The Daily Catalyst"] else None
    tag_id = get_or_create_wp_tag("Insight") if tier == "unified" else get_or_create_wp_tag("VIP" if tier == "vip" else "Pro")

    post_data = {
        "title": title,
        "content": html,
        "status": "publish",
        "slug": slug,
        "author": get_wp_author_id(author_name),
        "categories": [c for c in [cat_id, insight_cat_id] if c],
        "tags": [tag_id] if tag_id else [],
        "meta": {
            "rank_math_title": (_clean_seo_title(title)[:50] + " | Warm Insight")[:60],
            "rank_math_description": (exc or "")[:160],
            "rank_math_focus_keyword": kw.lower() if kw else "",
            "is_premium": "no" if cat == "Foundation" else "yes",
            "pms_content_restrict": "0" if cat == "Foundation" else "1",
            "post_tier": tier.upper(),
        }
    }
    if media_id: post_data["featured_media"] = media_id

    try:
        r = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", json=post_data, auth=(WP_USER, WP_APP_PASS), timeout=30)
        if r.status_code in (200, 201):
            link = r.json().get('link')
            print(f"   ✅ Published: {link}")

            # 뉴스레터 성공 후 👉 숏폼/인스타 생성 및 발송
            if (tier == "vip" or tier == "unified") and raw_for_cards:
                img_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes = generate_vip_carousel(raw_for_cards, cat)
                if video_mp4_bytes: send_social_style_email(title, link, img_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes)
            
            # 🚨 뉴스레터 성공 후 👉 유튜브 20,000자 대본 생성 및 발송!
            if raw_for_cards:
                yt_meta, yt_script = generate_youtube_script(raw_for_cards, title)
                if yt_script: send_youtube_script_email(title, yt_meta, yt_script)
            
            return True
        else: print(f"   ❌ Publish failed: {r.text[:100]}")
    except Exception as e: print(f"   ❌ Network error: {e}")
    return False

# ═══════════════════════════════════════════════
# 🔄 PIPELINES
# ═══════════════════════════════════════════════
def run_foundation_pipeline():
    cat = "Foundation"
    if not check_env_vars() or not verify_wp_credentials(): return
    if os.environ.get("FORCE_PUBLISH", "false").lower() != "true" and already_published_today(cat): return
    raw = gem_fb("unified", FOUNDATION_PROMPT.replace("{theme}", random.choice(FOUNDATION_TOPICS)), FOUNDATION_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE"); kw = xtag(raw, "SEO_KEYWORD")
        img_bytes = make_thumbnail(title, cat, "premium")
        if img_bytes and len(img_bytes) > 1000: publish(title, build_foundation_html(raw, VIP_AUTHORS.get(cat), datetime.datetime.utcnow().strftime("%B %d, %Y"), title, cat), xtag(raw, "EXCERPT"), kw, cat, make_slug(kw, title, cat), "premium", img_bytes, VIP_AUTHORS.get(cat), raw_for_cards=raw)

def run_philosophy_pipeline():
    cat = "The Daily Catalyst"
    if not check_env_vars() or not verify_wp_credentials(): return
    if os.environ.get("FORCE_PUBLISH", "false").lower() != "true" and already_published_today(cat): return
    raw = gem_fb("unified", PHILOSOPHY_PROMPT.replace("{theme}", random.choice(PHILOSOPHY_TOPICS)), PHILOSOPHY_SYS_INST)
    if raw:
        title = xtag(raw, "TITLE"); kw = xtag(raw, "SEO_KEYWORD")
        img_bytes = make_thumbnail(title, cat, "premium")
        if img_bytes and len(img_bytes) > 1000: publish(title, build_philosophy_html(raw, VIP_AUTHORS.get(cat), datetime.datetime.utcnow().strftime("%B %d, %Y"), title, cat), xtag(raw, "EXCERPT"), kw, cat, make_slug(kw, title, cat), "premium", img_bytes, VIP_AUTHORS.get(cat), raw_for_cards=raw)

def run_news_pipeline():
    cat = CATEGORIES[datetime.datetime.utcnow().timetuple().tm_yday % len(CATEGORIES)]
    print(f"🚀 Starting v45.9 Unified News & YouTube Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return
    if os.environ.get("FORCE_PUBLISH", "false").lower() != "true" and already_published_today(cat): return

    all_news = fetch_news_pool(cat)
    if len(all_news) < 2: return

    raw1 = gem_fb("unified", PROMPT_UNIFIED_P1.replace("{cat}", cat).replace("{news}", "\n".join(all_news)))
    if not raw1: return
    raw2 = gem_fb("unified", PROMPT_UNIFIED_P2.replace("{cat}", cat).replace("{ctx}", "Title: " + xtag(raw1, "TITLE") + "\nSummary: " + xtag(raw1, "EXECUTIVE_SUMMARY")))
    raw = (raw1 + "\n" + raw2) if raw2 else raw1

    title = xtag(raw, "TITLE"); kw = xtag(raw, "SEO_KEYWORD")
    img_bytes = make_thumbnail(title, cat, "unified")
    if img_bytes and len(img_bytes) > 1000:
        publish(title, build_html("unified", cat, raw, VIP_AUTHORS.get(cat), datetime.datetime.utcnow().strftime("%B %d, %Y"), title), xtag(raw, "EXCERPT"), kw, cat, make_slug(kw, title, cat), "unified", img_bytes, VIP_AUTHORS.get(cat), raw_for_cards=raw)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "philosophy": run_philosophy_pipeline()
        elif sys.argv[1] == "foundation": run_foundation_pipeline()
    else:
        run_news_pipeline()
