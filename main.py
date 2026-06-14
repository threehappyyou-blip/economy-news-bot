#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v45.7 (SEO & CTR Optimization Update)
#
# v45.6 → v45.7 핵심 변경 사항:
#   1. 자동 내부 링크(Deep Dive) 대상 URL을 현재 활성 카테고리(Insight, Foundation, The Daily Catalyst)로 전면 통합 및 수정
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

EMAIL_SENDER   = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASS     = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "")

MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
    "Premium": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
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

# 🚨 v45.7 PATCH: 딥다이브 내부 링크를 현재 웹사이트 메뉴 구조에 맞게 완벽 통합
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
# ✉️ 슬림 이메일
# ═══════════════════════════════════════════════
def send_social_style_email(title, link, image_bytes_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes=None):
    if not EMAIL_SENDER or not EMAIL_PASS or not EMAIL_RECEIVER:
        print("   ⚠️ 이메일 인증 정보가 없어 발송을 생략합니다.")
        return

    print(f"   📧 {EMAIL_RECEIVER}로 슬림 마케팅 패키지를 전송합니다...")
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
            <hr style="border:0; height:2px; background:#d4d4d8; margin: 30px 0;">
            <div style="text-align:center; margin-bottom: 20px;">
                <a href="{link}" style="display: inline-block; background-color: #0f1419; color: #ffffff; padding: 12px 24px; border-radius: 9999px; text-decoration: none; font-weight: bold; font-size: 15px;">
                    웹사이트에서 확인하기 →
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
                print(f"   ⚠️ MP4 첨부 오류: {e}")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASS)
            server.send_message(msg)
        print("   ✅ 슬림 마케팅 이메일 발송 완료!")
    except Exception as e:
        print(f"   ❌ 이메일 전송 실패: {e}")

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
        sys_inst = "You are an elite financial analyst. You MUST strictly follow the required output format. You MUST wrap EVERY section of your response in the exact XML tags requested. DO NOT omit any requested XML tags. Failure to include tags will break the system."

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
        print(f"   ⚠️ already_published_today check failed: {e}")
    return False

# ═══════════════════════════════════════════════
# 📰 NEWS POOLING
# ═══════════════════════════════════════════════
def fetch_news_pool(cat, max_items=30):
    feeds = RSS_FEEDS.get(cat, RSS_FEEDS["Economy"])
    items = set()
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for e in d.entries[:10]:
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

FOUNDATION_SYS_INST = """You are the "smart friend" who explains money to absolute beginners — channel Morning Brew + Milk Road energy. You text your friend the news, not write a textbook.

YOUR PERSONALITY:
- You're the friend texting at 9pm: "OK so this thing happened today and you HAVE to know about it"
- You use "you" and "I" constantly. Never "investors" or "one should"
- You're allowed to admit when something's weird: "OK this part is honestly kinda boring, but stay with me"
- You use SPECIFIC everyday analogies (Netflix subscription wars, ordering Uber Eats, dating apps, Costco runs)
- You're funny without trying too hard. Warm, not cold. Smart, not nerdy.

EMOJI POLICY (USE FREELY):
- Headlines can have emojis: "Bitcoin Just Did THIS 🚀"
- Body emojis welcome: 💡 for insights, 👀 for "look at this", 🚨 for alerts, 🤔 for "let's think", 💸 for money
- Don't overdo it — 3-5 emojis per article is the sweet spot
- Use them where they actually help readability, not as decoration

CASUAL EXPRESSION RULES (BALANCED):
- USE contractions freely: it's, that's, you'd, won't, didn't, here's, that'll
- USE conversational openers: "OK so...", "Look,", "Real talk,", "Here's the thing:"
- USE personal opinion phrases: "Honestly,", "My take?", "If you ask me,"
- BANNED slang: gonna, wanna, kinda, lol, lmao, fr, ngl (too informal for finance)
- BANNED textbook phrases: "in conclusion", "moreover", "furthermore", "it is important to note"

WRITING RULES (NON-NEGOTIABLE):
- Average sentence length: 12-15 words MAX
- One idea per paragraph. Paragraphs are 2-3 sentences MAX
- Start sentences with "And", "But", "So", "Here's the thing" — conversational openers
- BANNED words: leverage, utilize, paradigm, robust, optimize, synergy, holistic, deep-dive, unpack, navigate, ecosystem, framework, stakeholders
- USE instead: "look", "okay so", "here's why", "the truth is", "real talk", "the kicker is"
- Drop a relatable joke or aside ONCE per article. Not more. Not less.

You MUST wrap your content EXACTLY in the XML tags requested."""

FOUNDATION_PROMPT = """Write an SEO-optimized beginner's guide on the following topic:
TOPIC: {theme}

OUTPUT FORMAT REQUIREMENT:
You MUST output your response by wrapping your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it highly clickable using numbers or brackets like [2026] or [Guide].)</TITLE>
<SEO_KEYWORD>(Write a LONG-TAIL focus keyword, 3-5 words, low competition, high search intent. E.g., "how fed rate cuts affect tech stocks" NOT just "interest rates")</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the exact SEO_KEYWORD. End with a strong hook or question to drive clicks from Google search.)</EXCERPT>
<DEFINITION>(The 'What is it?' section. Provide a simple, 2-paragraph definition using an easy everyday analogy. e.g., "Think of it like a fruit basket...")</DEFINITION>
<WHY_MATTERS>(The 'Why it matters' section. Explain in 2 paragraphs why a beginner should care about this concept and how it builds wealth.)</WHY_MATTERS>
<HOW_TO_START>(The 'How to apply it' section. Provide 3 simple, actionable steps for a beginner to start using this concept today. Format as a bulleted list or numbered steps within the paragraph.)</HOW_TO_START>
"""

# ═══════════════════════════════════════════════
# 🧠 2. PHILOSOPHY DATABASE & PROMPTS
# ═══════════════════════════════════════════════
PHILOSOPHY_TOPICS = [
    "돈을 짝사랑하지 말고 행동으로 사랑하라 (Love money through action, not just unrequited longing)",
    "부를 담을 심리적 그릇과 책임의 무게 (The psychological vessel of wealth and the weight of responsibility)",
    "자발적 피로: 성장을 위한 쾌락적 고통 (Voluntary fatigue: The pleasurable pain of chosen growth)",
    "환경적 결핍을 폭발적 성장의 무기로 삼아라 (Weaponize environmental lack for explosive growth)",
    "소비자에서 생산자로: 읽기에서 쓰기로의 전환 (From consumer to producer: The shift from reading to writing)",
    "스스로 설정한 인지적 연봉 상한선을 파괴하라 (Destroy the cognitive salary cap you set for yourself)",
    "핑계의 소거: 타협 없는 성장의 시작 (The elimination of excuses: The beginning of uncompromising growth)"
]

PHILOSOPHY_SYS_INST = """You are an elite philosophical life strategist and writer, heavily influenced by classical literature and pragmatic wealth philosophies.
Your objective is to create a daily insight post that delivers profound, unfiltered truths about personal growth, wealth accumulation, and psychological resilience.
You speak to the reader not as a marketer, but as a strict, wise mentor who demands action.
Your writing must be direct, concise, and unapologetic. Use short, plain sentences. Do not sugar-coat reality.
NEVER use the following words or phrases: 'dive into', 'unleash', 'game-changing', 'buckle up', 'embark on this journey', 'delve', 'explore', 'supercharge', 'basically', 'in conclusion'.
You MUST wrap your content EXACTLY in the XML tags requested."""

PHILOSOPHY_PROMPT = """Write a philosophical daily insight based on the following theme:
THEME: {theme}

When interpreting concepts like 'dirt spoon' or poverty, frame it as a 'systemic disadvantage that must be weaponized for explosive growth'.
When discussing 'voluntary fatigue', explain it as 'the deeply rewarding exhaustion that comes from total, self-directed immersion in a meaningful task'.

OUTPUT FORMAT REQUIREMENT:
You MUST output your response by wrapping your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it punchy and intriguing but highly searchable on Google.)</TITLE>
<SEO_KEYWORD>(Write a LONG-TAIL focus keyword, 3-5 words, related to psychology, wealth, or personal growth. e.g. "psychology of wealth building")</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the exact SEO_KEYWORD. End with a strong hook or question to drive clicks from Google search.)</EXCERPT>
<ANCHOR>(The Classical Anchor: A one-sentence philosophical principle based on the theme)</ANCHOR>
<REFLECTION>(The Modern Reflection: 3-4 paragraphs explaining how this principle connects to modern reality, financial anxiety, or career stagnation. Criticize passive excuses and logically argue for voluntary fatigue and action.)</REFLECTION>
<CATALYST>(The Daily Catalyst: A single, highly provocative and specific question that requires the reader to write down an actionable answer immediately.)</CATALYST>
"""

# ═══════════════════════════════════════════════
# 🎨 3. TWO-PART PROMPTS (REGULAR NEWS)
# ═══════════════════════════════════════════════

PROMPT_UNIFIED_P1 = """You are Warm Insight's lead writer. Your mission: turn daily market chaos into clarity for everyday people — BUT with insights they couldn't get from a Reuters headline.

═══ THE GOLDEN RULE ═══
Imagine your reader is your friend Sarah, a 32-year-old marketing manager who knows nothing about finance but is curious. She'll close the tab in 5 seconds if you sound like Wall Street. BUT she'll also close it if you just repeat what she saw on Twitter. Give her ONE thing she didn't know.

═══ ⛔ ANTI-CLICHÉ RULES (CRITICAL) ═══

BANNED CONTENT (NEVER WRITE THESE — they make readers stop):
- "AI is still the boss" / "AI is here to stay" / "AI revolution"
- "Tech stocks are thriving" / "betting against X is a bad idea"
- "The trend is your friend" / "this time it's different"
- "Smart money is moving" without specifying WHERE
- "It's important to note" / "investors should consider"
- ANY statement that sounds like a Reuters headline summary

REQUIRED CONTENT (MUST INCLUDE):
- ONE counterintuitive insight that 80% of readers don't know
- AT LEAST 3 specific numbers (percentages, dollar amounts, dates, ticker prices)
- AT LEAST 1 specific company decision/move 
- ONE historical or comparative reference

═══ THESIS COHERENCE RULE ═══
1. Pick ONE central thesis from the news
2. Build your ENTIRE article around that single thesis
3. IGNORE news that doesn't support or contrast with your thesis

═══ WRITING RULES ═══
- Sentences MAX 15 words. Short hits harder than long.
- Each paragraph MAX 3 sentences. Visual breathing room matters.
- BANNED words: leverage, paradigm, robust, holistic, deep-dive, navigate, unpack, optimize, regulatory bodies, ecosystem, framework, stakeholders
- USE: "here's the deal", "OK so", "real talk", "look", "between us", "the kicker is"

Write PART 1 of an Insight newsletter on {cat}.
Target length: 900-1100 words across both parts combined. Shorter is better. Cut ruthlessly.
News Context:
{news}

OUTPUT FORMAT REQUIREMENT:
You MUST wrap your content EXACTLY in the XML tags listed below.

<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD. Make it highly clickable using numbers or brackets like [2026] or [Alert].)</TITLE>
<SEO_KEYWORD>(Write a LONG-TAIL focus keyword, 3-5 words, specific to the news event. E.g., "impact of fed rate cuts on tech" NOT just "fed rate cut")</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the exact SEO_KEYWORD. End with a strong hook or question to drive clicks from Google search.)</EXCERPT>
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

PROMPT_UNIFIED_P2 = """You are Warm Insight's lead writer continuing the analysis. Same friendly + smart tone as Part 1.

═══ ANTI-CLICHÉ REMINDER ═══
NEVER write generic conclusions like: "AI is here to stay" or "Tech will continue to dominate". Always be SPECIFIC with numbers, tickers, names, dates.

═══ TONE RULES ═══
- Sentences MAX 15 words, Paragraphs MAX 3 sentences.
- USE "you", "we", "honestly", "real talk", "here's the deal".
- BANNED: "regulatory bodies", "ecosystem", "framework", "also plays a role".

Write PART 2 of the Insight newsletter for {cat}.
Context from Part 1:
{ctx}

OUTPUT FORMAT REQUIREMENT:
You MUST wrap your content EXACTLY in the XML tags listed below.

<BULL_CASE>(Optimistic scenario. 3-4 sentences. SPECIFIC: name a ticker, a price target, or a catalyst. End with one bold claim.)</BULL_CASE>
<BEAR_CASE>(Pessimistic scenario. 3-4 sentences. SPECIFIC: name what breaks first, which ticker drops most, what price triggers panic.)</BEAR_CASE>
<HISTORICAL_PARALLEL>(REQUIRED — 2 sentences MAX. Name the year + event. One sentence on the parallel. One sentence: "What's different: [your answer].")</HISTORICAL_PARALLEL>
<QUICK_HITS>
(EXACTLY 3 bullet points of OTHER relevant news. STRICT FORMAT — each line MUST start with one of these emojis: 🚨 / 👀 / 🤔 / 💸)
</QUICK_HITS>
<SMART_MONEY_MOVE>(1 paragraph, MAX 3 sentences. NAME 1 specific ETF ticker. Then: "If I were you, I'd [specific action] because [specific reason].")</SMART_MONEY_MOVE>
<DO_ACTION>(1-2 specific actions. Must include either a ticker, a price level, OR a date trigger.)</DO_ACTION>
<DONT_ACTION>(1 critical mistake to avoid. Be blunt. Start with "Don't" or "Stop". Name the SPECIFIC behavior.)</DONT_ACTION>
<TAKEAWAY>(The bottom line insight. Under 20 words. Quotable. Counterintuitive if possible.)</TAKEAWAY>
<PS>(One-line veteran advice with historical context. "P.S. — Real talk: ..." style.)</PS>"""

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
        fallback_lines = [
            "S&P 500 | 5,234 | UP | Index near recent highs",
            "Nasdaq 100 | 18,200 | UP | Tech leading the broader market",
            "10Y Treasury | 4.25% | SIDEWAYS | Rate cut bets keeping yields contained"
        ]
        lines = lines + fallback_lines[:max(2, 3 - len(lines))]

    html = f"""
    <div style="background:#ffffff; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; font-size:20px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:12px; display:inline-block;">📊 {title}</h3>
        <div style="overflow-x:auto; margin-top:15px;">
        <table style="width:100%; border-collapse:collapse; font-family:-apple-system,sans-serif;">
            <thead>
                <tr style="background:{BG_LIGHT}; text-align:left; border-bottom:2px solid {BORDER};">
                    <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px; white-space:nowrap;">Asset/Metric</th>
                    <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px; white-space:nowrap;">Status</th>
                    <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px; white-space:nowrap;">Trend</th>
                    <th style="padding:14px; color:{SLATE}; font-weight:700; font-size:15px;">Key Insight</th>
                </tr>
            </thead>
            <tbody>
    """
    for line in lines[:5]:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            asset, value, trend, insight = parts[:4]
            t_upper = trend.upper()
            if "UP" in t_upper or "BULL" in t_upper or "HIGH" in t_upper: t_color, t_icon = "#10b981", "🟢"
            elif "DOWN" in t_upper or "BEAR" in t_upper or "LOW" in t_upper: t_color, t_icon = "#ef4444", "🔴"
            else: t_color, t_icon = "#f59e0b", "🟡"

            html += f"""
                <tr style="border-bottom:1px solid {BORDER};">
                    <td style="padding:14px; font-weight:600; color:{DARK};">{asset}</td>
                    <td style="padding:14px; color:{SLATE}; font-family:monospace; font-size:15px; font-weight:bold;">{value}</td>
                    <td style="padding:14px; font-weight:bold; color:{t_color};">{t_icon} {trend.upper()}</td>
                    <td style="padding:14px; color:{MUTED}; font-size:15px; line-height:1.6;">{insight}</td>
                </tr>
            """
    html += "</tbody></table></div></div>"
    return html

def _build_progress_bars(raw_data, title="Sector Risk Heatmap"):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""

    html = f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;">
        <h3 style="margin-top:0; font-size:20px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:12px;">🌡️ {title}</h3>
    """
    colors = ["#dc2626", "#ea580c", "#ca8a04", "#059669", "#3b82f6"]

    for i, line in enumerate(lines[:5]):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:
            name = parts[0]
            try: pct = int(re.sub(r'[^0-9]', '', parts[1]))
            except: pct = 50
            pct = max(0, min(100, pct))
            c = colors[0] if pct > 75 else (colors[1] if pct > 50 else (colors[3] if pct < 30 else colors[2]))

            html += f"""
            <div style="margin-top:18px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="font-weight:600; font-size:15px; color:{DARK};">{name}</span>
                    <span style="font-weight:900; font-size:15px; color:{c};">{pct}%</span>
                </div>
                <div style="background:#e2e8f0; height:12px; border-radius:6px; overflow:hidden;">
                    <div style="background:{c}; height:100%; width:{pct}%; border-radius:6px;"></div>
                </div>
            </div>
            """
    html += "</div>"
    return html

def _build_quick_hits(raw_data):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if l.strip()]
    if not lines: return ""

    default_emojis = ["🚨", "👀", "💸"]
    emoji_chars = "🚨👀🤔💸📈📉🔥💡🤯"

    items_html = ""
    for i, line in enumerate(lines[:3]):
        clean = line.replace("-", "").replace("*", "").strip()
        if clean and clean[0] not in emoji_chars:
            clean = f"{default_emojis[i % 3]} {clean}"
        items_html += f'<li style="margin-bottom:12px; color:{SLATE};">{clean}</li>'

    return f"""
    <div style="background:#f1f5f9; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;">
        <h3 style="margin-top:0; font-size:20px; color:{DARK}; text-transform:uppercase; letter-spacing:1px;">⚡ Quick Hits</h3>
        <ul style="{F} margin:0; padding-left:20px;">{items_html}</ul>
    </div>
    """

def _build_pie_chart(s, b, c, cat):
    cat_colors = {
        "Economy": ("#2563eb", "#60a5fa", "#dbeafe"),
        "Politics": ("#dc2626", "#f87171", "#fee2e2"),
        "Tech": ("#7c3aed", "#a78bfa", "#ede9fe"),
        "Health": ("#059669", "#34d399", "#d1fae5"),
        "Energy": ("#d97706", "#fbbf24", "#fef3c7")
    }
    c_s, c_b, c_c = cat_colors.get(cat, ("#b8974d", "#cbd5e1", "#f1f5f9"))

    circ = 565.49
    sd, bd, cd = circ*s/100, circ*b/100, circ*c/100

    pie = f'<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;">'
    pie += f'<circle cx="100" cy="100" r="90" fill="none" stroke="{c_s}" stroke-width="30" stroke-dasharray="{sd} {circ}" stroke-dashoffset="0"/>'
    pie += f'<circle cx="100" cy="100" r="90" fill="none" stroke="{c_b}" stroke-width="30" stroke-dasharray="{bd} {circ}" stroke-dashoffset="-{sd}"/>'
    pie += f'<circle cx="100" cy="100" r="90" fill="none" stroke="{c_c}" stroke-width="30" stroke-dasharray="{cd} {circ}" stroke-dashoffset="-{sd+bd}"/>'
    pie += f'<text x="100" y="95" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">{s}/{b}/{c}</text>'
    pie += f'<text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>'

    pie += f'<div style="display:flex;justify-content:center;gap:20px;">'
    pie += f'<span style="color:{c_s};font-weight:bold;">● Stocks {s}%</span>'
    pie += f'<span style="color:{c_b};font-weight:bold;">● Safe {b}%</span>'
    pie += f'<span style="color:{c_c};font-weight:bold;">● Cash {c}%</span></div>'

    return pie

# 🚨 v45.7: 내부 링크 URL 완벽 매핑
def _build_pillar_link(target_cat):
    """v45.7: 본문 하단에 자동 내부 링크 박스 추가 (Insight, Foundation, Catalyst로 완벽 통합)"""
    pillar = PILLAR_PAGES.get(target_cat)
    if not pillar: return ""
    return f"""
    <div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:20px; margin:40px 0; border-radius:4px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
        <p style="margin:0; font-size:16px; color:#1e293b;">
            <strong style="color:#2563eb;">📚 Deep Dive:</strong> Want to master this topic? Check out our complete guide to <a href="{pillar['url']}" style="color:#2563eb; text-decoration:underline; font-weight:700;">{pillar['anchor']}</a>.
        </p>
    </div>
    """

# ═══════════════════════════════════════════════
# 📎 ENGAGEMENT & FOOTER BUILDERS
# ═══════════════════════════════════════════════
SOCIAL_LINKS = {
    "youtube": "https://www.youtube.com/@WarmInsightyou",
    "tiktok": "https://www.tiktok.com/@warminsight"
}

def _build_social_share(title, slug):
    si = ""
    if SOCIAL_LINKS.get("youtube"):
        si += f'<a href="{SOCIAL_LINKS["youtube"]}" target="_blank" style="display:inline-block; background:#FF0000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">▶ YouTube</a>'
    if SOCIAL_LINKS.get("tiktok"):
        si += f'<a href="{SOCIAL_LINKS["tiktok"]}" target="_blank" style="display:inline-block; background:#000000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">🎵 TikTok</a>'
    return f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:10px; padding:28px; margin:40px 0; text-align:center;">
        <p style="font-size:20px; font-weight:bold; color:{DARK}; margin:0 0 10px;">Found this useful? Share the insight.</p>
        <p style="font-size:15px; color:{MUTED}; margin:0 0 18px;">Forward to a friend who wants smarter market analysis.</p>
        <div style="margin-bottom:14px;">{si}</div>
        <p style="margin:0;"><a href="{SITE_URL}" style="color:{GOLD}; font-weight:600; text-decoration:underline;">Subscribe at warminsight.com</a></p>
    </div>
    """

def _build_branded_footer():
    si = ""
    if SOCIAL_LINKS.get("youtube"):
        si += f'<a href="{SOCIAL_LINKS["youtube"]}" target="_blank" style="display:inline-block; background:#FF0000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">▶ YouTube</a>'
    if SOCIAL_LINKS.get("tiktok"):
        si += f'<a href="{SOCIAL_LINKS["tiktok"]}" target="_blank" style="display:inline-block; background:#000000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">🎵 TikTok</a>'
    return f"""
    <div style="background:{DARK}; padding:35px; border-radius:10px; margin-top:30px;">
        <p style="font-size:24px; font-weight:bold; color:{GOLD}; margin:0 0 12px; text-align:center;">Warm Insight</p>
        <p style="font-size:14px; color:#94a3b8; text-align:center; margin:0 0 16px;">AI-Driven Global Market Analysis</p>
        <div style="text-align:center; margin-bottom:16px;">{si}</div>
        <div style="text-align:center; margin-bottom:16px; font-size:13px;">
            <a href="{SITE_URL}/about-us/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">About</a>
            <a href="{SITE_URL}/privacy-policy/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">Privacy</a>
            <a href="{SITE_URL}/terms/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">Terms</a>
        </div>
        <p style="font-size:13px; color:#64748b; margin:0; text-align:center;">
            All analysis is for informational purposes only. Not financial advice.<br>
            &copy; 2026 Warm Insight. All rights reserved.
        </p>
    </div>
    """

def _build_author_bio(cat):
    author = VIP_AUTHORS.get(cat, "Warm Insight Editorial Team")
    return f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:10px; padding:24px; margin:35px 0; display:flex; gap:20px; align-items:center;">
        <div style="min-width:56px; height:56px; border-radius:50%; background:{GOLD}; display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:700; color:#fff;">
            W
        </div>
        <div>
            <p style="font-size:17px; font-weight:700; color:{DARK}; margin:0 0 6px;">{author}</p>
            <p style="font-size:14px; color:{MUTED}; margin:0; line-height:1.6;">
                AI-powered financial analysis, curated and edited by Jiho, founder of Warm Insight. 
                We translate Wall Street complexity into clear insights for everyday investors.
            </p>
        </div>
    </div>
    """

def _build_founder_note():
    return f"""
    <div style="background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%); border:2px solid {GOLD}; border-radius:14px; padding:30px; margin:40px 0;">
        <div style="display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap;">
            <div style="min-width:70px; height:70px; border-radius:50%; background:{GOLD}; display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:900; color:#fff;">
                J
            </div>
            <div style="flex:1; min-width:250px;">
                <p style="font-size:13px; font-weight:800; color:#92400e; margin:0 0 6px; text-transform:uppercase; letter-spacing:1.5px;">A NOTE FROM THE FOUNDER</p>
                <p style="font-size:18px; font-weight:700; color:{DARK}; margin:0 0 10px; line-height:1.4;">
                    Hey, I'm Jiho. I built Warm Insight because I was tired of finance content being either too dumbed-down or too academic.
                </p>
                <p style="font-size:15px; color:{SLATE}; margin:0; line-height:1.6;">
                    Every article here is designed to give you ONE thing: a clearer view of your money than you had 5 minutes ago. 
                    If it ever stops doing that, tell me directly. I read every reply.
                </p>
            </div>
        </div>
    </div>
    """

# ═══════════════════════════════════════════════
# 🎨 1. HTML BUILDER (FOUNDATION / SEO)
# ═══════════════════════════════════════════════
def build_foundation_html(raw, author, tf, title, cat):
    html = f"<div style=\"{F}\">\n"

    html += f"""
    <div style="border-top:4px solid #10b981; border-bottom:1px solid {BORDER}; padding:18px 0; margin-bottom:35px;">
        <p style="margin:0 0 6px; font-size:15px; color:{MUTED};">
            <strong style="color:{DARK};">By {author}</strong> &nbsp;|&nbsp; {tf}
            <span style="background:#10b981; color:#fff; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">BEGINNER'S GUIDE</span>
        </p>
        <p style="margin:0; font-size:13px; color:{MUTED}; font-style:italic;">
            Edited by Jiho, Founder
        </p>
    </div>
    """

    def_text = xtag(raw, "DEFINITION").replace("\n", "<br><br>")
    html += f"""
    <div style="background:#f0fdf4; border-left:5px solid #10b981; padding:25px; margin:30px 0; border-radius:0 8px 8px 0;">
        <h3 style="margin-top:0; font-size:22px; color:#065f46;">📖 What is it? (Definition)</h3>
        <div style="color:#064e3b; font-size:18px; line-height:1.8;">
            {def_text}
        </div>
    </div>
    """

    why_text = xtag(raw, "WHY_MATTERS").replace("\n", "<br><br>")
    html += f"""
    <div style="margin:40px 0;">
        <h3 style="font-size:24px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">💡 Why It Matters</h3>
        <p>{why_text}</p>
    </div>
    """

    how_text = xtag(raw, "HOW_TO_START").replace("\n", "<br><br>")
    html += f"""
    <div style="background:#ffffff; border:2px solid #3b82f6; padding:30px; border-radius:12px; margin:40px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; color:#1e40af; font-size:24px;">🚀 How to Start Today</h3>
        <div style="color:{SLATE}; font-size:18px; line-height:1.8;">
            {how_text}
        </div>
    </div>
    """

    # 🚨 v45.7 내부 링크 적용 (Foundation)
    html += _build_pillar_link("Foundation") 

    html += """
    <div style="margin: 40px 0; text-align: center;">
        <a href="#respond" style="display: flex; justify-content: center; align-items: center; width: 100%; max-width: 400px; margin: 0 auto; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; padding: 18px 20px; border-radius: 50px; font-family: 'Inter', sans-serif; font-size: 1.15rem; font-weight: 800; text-decoration: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); line-height: 1;">
            💬 Share Your Thoughts ↓
        </a>
    </div>
    """

    slug = make_slug(xtag(raw, "SEO_KEYWORD"), title, "foundation")
    html += _build_social_share(title, slug)
    html += _build_founder_note()
    html += _build_branded_footer()

    html += f"""
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: Educational content only.
    </p>
    </div>
    """
    return sanitize(html)

# ═══════════════════════════════════════════════
# 🎨 2. HTML BUILDER (PHILOSOPHY)
# ═══════════════════════════════════════════════
def build_philosophy_html(raw, author, tf, title, cat):
    html = f"<div style=\"{F}\">\n"

    html += f"""
    <div style="border-top:4px solid {GOLD}; border-bottom:1px solid {BORDER}; padding:18px 0; margin-bottom:35px;">
        <p style="margin:0 0 6px; font-size:15px; color:{MUTED};">
            <strong style="color:{DARK};">By {author}</strong> &nbsp;|&nbsp; {tf}
            <span style="background:{DARK}; color:{GOLD}; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">DAILY INSIGHT</span>
        </p>
        <p style="margin:0; font-size:13px; color:{MUTED}; font-style:italic;">
            Edited by Jiho, Founder
        </p>
    </div>
    """

    html += f"""
    <div style="text-align:center; margin:50px 0;">
        <span style="font-size:40px; color:{GOLD}; line-height:1;">❝</span>
        <h2 style="font-family:Georgia,serif; font-size:26px; color:{DARK}; margin:10px 0; font-weight:600; line-height:1.4;">
            {xtag(raw, "ANCHOR")}
        </h2>
        <span style="font-size:40px; color:{GOLD}; line-height:1;">❞</span>
    </div>
    """

    reflection_text = xtag(raw, "REFLECTION").replace("\n", "<br><br>")
    html += f"""
    <div style="margin:40px 0;">
        <h3 style="font-size:22px; color:{DARK}; border-left:4px solid {GOLD}; padding-left:12px; margin-bottom:20px;">The Reflection</h3>
        <div style="color:{SLATE}; font-size:18px; line-height:1.8;">
            {reflection_text}
        </div>
    </div>
    """

    catalyst_raw = xtag(raw, "CATALYST")
    catalyst_text = re.sub(r'<[^>]+>', '', catalyst_raw)

    html += f"""
    <div style="background:#fefce8; border:2px solid #fde047; padding:35px; border-radius:12px; margin:50px 0; text-align:center; box-shadow:0 10px 15px -3px rgba(0, 0, 0, 0.05);">
        <p style="font-size:14px; font-weight:800; color:#b45309; text-transform:uppercase; letter-spacing:2px; margin:0 0 15px;">⚡ The Daily Catalyst</p>
        <p style="font-size:24px; font-weight:900; color:#92400e; margin:0 0 20px; line-height:1.5;">
            {catalyst_text}
        </p>
        <p style="font-size:15px; color:#b45309; margin:0; font-style:italic;">
            Don't just read. Take out a pen and write your answer now.
        </p>
    </div>
    """

    # 🚨 v45.7 내부 링크 적용 (The Daily Catalyst)
    html += _build_pillar_link("The Daily Catalyst") 

    html += """
    <div style="margin: 40px 0; text-align: center;">
        <a href="#respond" style="display: flex; justify-content: center; align-items: center; width: 100%; max-width: 400px; margin: 0 auto; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; padding: 18px 20px; border-radius: 50px; font-family: 'Inter', sans-serif; font-size: 1.15rem; font-weight: 800; text-decoration: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); line-height: 1;">
            💬 Share Your Thoughts ↓
        </a>
    </div>
    """

    slug = make_slug(xtag(raw, "SEO_KEYWORD"), title, "catalyst")
    html += _build_social_share(title, slug)
    html += _build_founder_note()
    html += _build_branded_footer()

    html += f"""
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: This article is for informational purposes only.
    </p>
    </div>
    """
    return sanitize(html)

# ═══════════════════════════════════════════════
# 🎨 3. HTML BUILDER (REGULAR NEWS)
# ═══════════════════════════════════════════════
def build_html(tier, cat, raw, author, tf, title):
    html = f"<div style=\"{F}\">\n"

    badge = "WARM INSIGHT"
    badge_bg = GOLD

    html += f"""
    <div style="border-top:4px solid {badge_bg}; border-bottom:1px solid {BORDER}; padding:18px 0; margin-bottom:35px;">
        <p style="margin:0 0 6px; font-size:15px; color:{MUTED};">
            <strong style="color:{DARK};">By {author}</strong> &nbsp;|&nbsp; {tf}
            <span style="background:{badge_bg}; color:#fff; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">{badge}</span>
        </p>
        <p style="margin:0; font-size:13px; color:{MUTED}; font-style:italic;">
            Edited by Jiho, Founder
        </p>
    </div>
    """

    html += f'<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {badge_bg}; padding-bottom:10px; display:inline-block;">Executive Summary</h2>'
    html += f'<p style="font-size:19px; font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>'

    html += _build_founder_note()

    html += _build_data_table(xtag(raw, "DATA_TABLE"), "Market Dashboard")
    html += _build_progress_bars(xtag(raw, "HEATMAP"), "Sector Risk Heatmap")

    html += f"""
    <div style="background:#faf5ff; border-left:5px solid #8b5cf6; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;">
        <p style="font-size:20px; font-weight:800; color:#4c1d95; margin:0 0 12px;">💡 Plain English</p>
        <p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p>
    </div>
    """

    html += f'<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {badge_bg}; padding-bottom:10px; display:inline-block; margin-top:30px;">Market Drivers & Flow</h2>'
    html += f'<h3 style="font-size:24px; color:{DARK}; margin-top:20px;">{xtag(raw, "HEADLINE")}</h3>'

    html += f"""
    <div style="background:#fff; border:1px solid {BORDER}; border-left:5px solid {badge_bg}; padding:30px; border-radius:8px; margin:30px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <p><strong>🧐 The Big Picture:</strong> {xtag(raw, "MACRO")}</p>
        <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
        <p><strong>🐑 What Most People Are Doing:</strong> {xtag(raw, "HERD")}</p>
        <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
        <p><strong>🦅 What Smart Money Is Doing:</strong> {xtag(raw, "CONTRARIAN")}</p>
    </div>
    """

    html += f"""
    <div style="background:#fffbeb; border:1px solid #fde68a; border-left:5px solid {AMBER}; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;">
        <strong style="color:#92400e; font-size:20px;">🔗 Chain of Events:</strong><br>
        <span style="font-weight:bold; font-size:19px; color:{DARK}; display:inline-block; margin-top:12px;">{xtag(raw, "QUICK_FLOW")}</span>
    </div>
    """

    html += f"""
    <div style="display:flex; flex-wrap:wrap; gap:20px; margin:40px 0;">
        <div style="flex:1; min-width:250px; background:#ecfdf5; border:2px solid #10b981; border-radius:8px; padding:25px;">
            <h4 style="margin-top:0; font-size:22px; color:#065f46;">🐂 Bull Case</h4>
            <p style="margin:0; color:#064e3b;">{xtag(raw, "BULL_CASE")}</p>
        </div>
        <div style="flex:1; min-width:250px; background:#fef2f2; border:2px solid #ef4444; border-radius:8px; padding:25px;">
            <h4 style="margin-top:0; font-size:22px; color:#991b1b;">🐻 Bear Case</h4>
            <p style="margin:0; color:#7f1d1d;">{xtag(raw, "BEAR_CASE")}</p>
        </div>
    </div>
    """

    html += _build_quick_hits(xtag(raw, "QUICK_HITS"))

    html += f"""
    <div style="background:#ffffff; border:2px solid {badge_bg}; padding:30px; border-radius:8px; margin:45px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; color:{badge_bg}; font-size:24px;">💎 Smart Money Move</h3>
        <p style="margin:0;">{xtag(raw, "SMART_MONEY_MOVE")}</p>
    </div>
    """

    historical = xtag(raw, "HISTORICAL_PARALLEL")
    if historical:
        html += f"""
        <div style="background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding:35px; border-radius:12px; margin:45px 0; border-left:5px solid {badge_bg};">
            <h3 style="color:{badge_bg}; margin-top:0; font-size:24px; display:flex; align-items:center; gap:10px;">
                📜 Historical Parallel
            </h3>
            <p style="color:#cbd5e1; font-size:17px; line-height:1.8; margin:15px 0 0;">{historical}</p>
        </div>
        """

    al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
    pie = _build_pie_chart(al["s"], al["b"], al["c"], cat)
    html += f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; padding:30px; border-radius:8px; margin-bottom:40px;">
        <h3 style="margin-top:0; font-size:22px; color:{DARK};">📊 Suggested Allocation</h3>
        {pie}
        <p style="margin-top:15px; color:{MUTED}; font-size:14px; text-align:center; font-style:italic;">
            General guideline based on current {cat} outlook. Not personalized advice.
        </p>
    </div>
    """

    html += f"""
    <div style="background:#1e293b; padding:40px; border-radius:12px; margin:45px 0;">
        <h3 style="color:{badge_bg}; margin-top:0; font-size:26px; border-bottom:2px solid #475569; padding-bottom:15px;">✅ Action Plan</h3>
        <div style="background:#ecfdf5; border:2px solid #10b981; padding:20px; border-radius:8px; margin:25px 0 15px;">
            <p style="margin:0; color:#065f46; font-size:18px;"><strong>🟢 DO:</strong> {xtag(raw, "DO_ACTION")}</p>
        </div>
        <div style="background:#fef2f2; border:2px solid #ef4444; padding:20px; border-radius:8px;">
            <p style="margin:0; color:#7f1d1d; font-size:18px;"><strong>🔴 DON'T:</strong> {xtag(raw, "DONT_ACTION")}</p>
        </div>
    </div>
    """

    slug = make_slug(xtag(raw, "SEO_KEYWORD"), xtag(raw, "TITLE"), cat)
    tw = xtag(raw, "TAKEAWAY")
    ps = xtag(raw, "PS")

    html += f"""
    <hr style="border:0; height:1px; background:{BORDER}; margin:50px 0;">
    <h2 style="font-family:Georgia,serif; font-size:28px; color:{DARK}; margin-bottom:20px;">Today's Warm Insight</h2>
    <p style="{F} font-size:19px; font-style:italic; border-left:3px solid #cbd5e1; padding-left:16px;">"{tw}"</p>
    <div style="background:{DARK}; padding:30px; border-radius:10px; border-left:5px solid {badge_bg}; margin-top:35px;">
        <p style="color:#e2e8f0; font-size:18px; margin:0; line-height:1.6;">
            <strong style="color:{badge_bg};">P.S.</strong> {ps}
        </p>
    </div>
    """

    # 🚨 v45.7 내부 링크 적용 (Insight 통합)
    html += _build_pillar_link("Insight") 

    html += """
    <div style="margin: 40px 0; text-align: center;">
        <a href="#respond" style="display: flex; justify-content: center; align-items: center; width: 100%; max-width: 400px; margin: 0 auto; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; padding: 18px 20px; border-radius: 50px; font-family: 'Inter', sans-serif; font-size: 1.15rem; font-weight: 800; text-decoration: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); line-height: 1;">
            💬 Share Your Thoughts ↓
        </a>
    </div>
    """

    html += _build_social_share(title, slug)
    html += _build_branded_footer()
    html += _build_author_bio(cat)

    html += f"""
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: AI-generated, human-edited educational content. Not financial advice. All decisions are your own.
    </p>
    </div>
    """
    return sanitize(html)


# ═══════════════════════════════════════════════════════════════
# 🖼️ 썸네일 엔진 
# ═══════════════════════════════════════════════════════════════
def get_font(url, filename):
    if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            print(f"    📥 Downloading font from {url}...")
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            resp.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(resp.content)
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
        "The Daily Catalyst": {"bg1": "#1e293b", "bg2": "#0f172a", "acc": "#b8974d"},
        "Foundation": {"bg1": "#1e3a5f", "bg2": "#0f2040", "acc": "#f59e0b"}
    }
    style = CAT_STYLES.get(cat, CAT_STYLES["Economy"])

    AI_PROMPTS = {
        "Economy": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large (taking up 40% of the right side) sleek, cute white robot mascot standing enthusiastically and pointing at a floating stock market chart, acting as a friendly guide. Vibrant colors, clean gradient background, perfect for a newsletter thumbnail. No text, no words.",
        "Politics": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large (taking up 40% of the right side) sleek white robot mascot standing enthusiastically and pointing at a glowing globe or chess piece, acting as a friendly guide. Vibrant colors, clean gradient background. No text, no words.",
        "Tech": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large (taking up 40% of the right side) sleek white robot mascot standing enthusiastically and pointing at a glowing microchip, acting as a friendly guide. Vibrant colors, clean gradient background. No text, no words.",
        "Health": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large (taking up 40% of the right side) sleek white robot mascot standing enthusiastically and pointing at a glowing DNA helix, acting as a friendly guide. Vibrant colors, clean gradient background. No text, no words.",
        "Energy": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large (taking up 40% of the right side) sleek white robot mascot standing enthusiastically and pointing at a bright lightning bolt, acting as a friendly guide. Vibrant colors, clean gradient background. No text, no words.",
        "The Daily Catalyst": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large (taking up 40% of the right side) sleek white robot mascot enthusiastically presenting a classic book, acting as a friendly guide. Dark premium colors, clean gradient background. No text, no words.",
        "Foundation": "A minimalist flat vector illustration in corporate memphis style featuring a prominent, very large (taking up 40% of the right side) sleek white robot mascot enthusiastically pointing at a gold coin and a guide book, acting as a friendly educational guide. Vibrant colors, clean gradient background. No text, no words."
    }

    img = None
    use_ai_bg = False

    try:
        print(f"    [AI] Requesting BIG Explaining Mascot Vector Background for {cat}...")
        client = _get_gemini_client()
        result = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=AI_PROMPTS.get(cat, AI_PROMPTS["Economy"]),
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type="image/jpeg"
            )
        )
        bg_bytes = result.generated_images[0].image.image_bytes
        img = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
        img = img.resize((w, h), Image.LANCZOS)
        use_ai_bg = True
        print("    ✅ AI BIG Explaining Mascot Generated!")
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
        elif cat == "The Daily Catalyst":
            draw.ellipse([cx_p-50*S, cy_p-70*S, cx_p+50*S, cy_p+30*S], fill="#cbd5e1")
            draw.polygon([(cx_p-25*S, cy_p+20*S), (cx_p+25*S, cy_p+20*S), (cx_p+15*S, cy_p+70*S), (cx_p-15*S, cy_p+70*S)], fill="#94a3b8")
        elif cat == "Foundation":
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

    draw = ImageDraw.Draw(img)
    if use_ai_bg:
        draw.rectangle([(0, 0), (w, h)], fill="#1a252c70")
    draw.rectangle([(0, h - 80 * SCALE), (w, h)], fill="#00000060")

    ft_path = get_font(
        "https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf",
        "fonts/BebasNeue-Regular.ttf"
    )

    def lf(p, s):
        try: return ImageFont.truetype(p, s * SCALE)
        except:
            fallbacks = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "arial.ttf"
            ]
            for fb in fallbacks:
                try: return ImageFont.truetype(fb, s * SCALE)
                except: pass
            return ImageFont.load_default()

    ft = lf(ft_path, 85)
    fs = lf(ft_path, 34)
    fb = lf(ft_path, 28)
    f_badge = lf(ft_path, 36)

    S = SCALE

    date_badge = datetime.datetime.utcnow().strftime("%Y.%m.%d")
    draw.text((40 * S, 44 * S), date_badge, font=fb, fill="#ffffff")

    try: date_w = draw.textlength(date_badge, font=fb)
    except: date_w = len(date_badge) * 15 * S

    bx = 40 * S + date_w + 30 * S
    try: cat_w = draw.textlength(cat.upper(), font=fb)
    except: cat_w = len(cat) * 15 * S

    draw.rounded_rectangle(
        [(bx, 36 * S), (bx + cat_w + 60 * S, 86 * S)],
        radius=25 * S, fill="#ffffff"
    )
    draw.text((bx + 30 * S, 44 * S), cat.upper(), font=fb, fill="#1e293b")

    if tier == "vip":
        tl = "VIP"
        t_bg = "#b8974d"
        t_tc = "#ffffff"
        try: tier_w = draw.textlength(tl, font=f_badge)
        except: tier_w = len(tl) * 18 * S
        badge_x = w - 40 * S - tier_w - 40 * S
        draw.rounded_rectangle(
            [(badge_x, 36 * S), (w - 40 * S, 86 * S)],
            radius=25 * S, fill=t_bg
        )
        draw.text((badge_x + 20 * S, 44 * S), tl, font=f_badge, fill=t_tc)

    clean_title = _clean_seo_title(title_text).upper()
    clean_title = re.sub(r'^WARM INSIGHT\s*[:\-–]\s*', '', clean_title).strip()

    words = clean_title.split()
    lines, line = [], []
    mw = w - 100 * SCALE if use_ai_bg else w - 380 * SCALE

    for word in words:
        t = " ".join(line + [word])
        try: tw2 = draw.textlength(t, font=ft)
        except: tw2 = len(t) * 40 * SCALE

        if tw2 < mw:
            line.append(word)
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
        except:
            y += 100 * S

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
# 🎬 틱톡 호환 영상 생성
# ═══════════════════════════════════════════════
def generate_video_mp4(cat, hook_text, data_points, frames_images):
    print("   🎥 Generating SMOOTH 20-second TikTok-Compatible Reels Video...")
    try:
        import numpy as np
        from moviepy.editor import ImageClip, concatenate_videoclips
    except ImportError as e:
        print(f"   ❌ MoviePy import 실패: {e}")
        return None

    try:
        SLIDE_DURATION = 3.3
        CROSSFADE_DURATION = 0.5
        ZOOM_START = 1.0
        ZOOM_END = 1.08

        clips = []
        for i, frame in enumerate(frames_images):
            frame_np = np.array(frame.convert('RGB'))
            clip = ImageClip(frame_np).set_duration(SLIDE_DURATION)

            if i % 2 == 0:
                clip = clip.resize(lambda t: ZOOM_START + (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))
            else:
                clip = clip.resize(lambda t: ZOOM_END - (ZOOM_END - ZOOM_START) * (t / SLIDE_DURATION))

            clip = clip.set_position(('center', 'center'))

            if i > 0:
                clip = clip.crossfadein(CROSSFADE_DURATION)

            clips.append(clip)

        video = concatenate_videoclips(clips, padding=-CROSSFADE_DURATION, method="compose")

        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        video.write_videofile(
            temp_path,
            fps=30,
            codec='libx264',
            bitrate='6000k',
            audio=False,
            preset='medium',
            ffmpeg_params=[
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1:1',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                '-profile:v', 'main',
                '-level', '4.0',
                '-x264-params', 'colorprim=bt709:transfer=bt709:colormatrix=bt709'
            ],
            logger=None
        )

        with open(temp_path, 'rb') as f:
            mp4_bytes = f.read()
        os.remove(temp_path)

        print(f"   ✅ 틱톡 호환 20초 세로 영상 추출 완료! ({len(mp4_bytes)/1024/1024:.1f}MB)")
        return mp4_bytes
    except Exception as e:
        print(f"   ❌ MoviePy 비디오 인코딩 실패: {e}")
        traceback.print_exc()
        return None

# ═══════════════════════════════════════════════
# 🎨 6-슬라이드 카루셀
# ═══════════════════════════════════════════════
def generate_vip_carousel(raw_content, cat):
    print("   🎨 Generating ENGAGING 6-Slide Vertical Carousel...")
    client = _get_gemini_client()

    sys_inst = """You are a TOP-TIER viral content creator for finance Instagram/TikTok (think @morning.brew, @theinsidertt).
    Your job: Extract data + write COPY THAT STOPS THE SCROLL.

    OUTPUT RULES (CRITICAL):
    - HOOK: Pattern interrupt opener. Use shocking number, contrarian take, or curiosity gap. Max 7 words.
    - SHOCK_STAT: One jaw-dropping statistic that proves the hook. Max 6 words. Include numbers.
    - INSIGHT_LINE: The "aha moment" payoff. Max 8 words. Confident, declarative.
    - CTA_HOOK: Urgency/FOMO trigger for the last slide. Max 6 words.

    TICKER FORMAT:
    - Max 8 chars per ticker ($AAPL, $VIX, Gold)
    - Values: include direction (+/-) and % or value

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
    cta_hook = xtag(raw_data, "CTA_HOOK") or "DON'T MISS THE NEXT MOVE"
    reels_script = xtag(raw_data, "REELS_SCRIPT") or "Script generation failed."
    ig_caption = xtag(raw_data, "IG_CAPTION") or f"{hook_text}\n\nLink in bio for the full breakdown. #investing #finance #stocks"
    smart_comment = xtag(raw_data, "SMART_COMMENT") or "Interesting market shift. Just published a full breakdown on this."

    data_points = []
    for i in range(1, 6):
        item = xtag(raw_data, f"ITEM{i}")
        if item and "|" in item:
            parts = item.split("|")
            raw_ticker = parts[0].strip()
            if len(raw_ticker) > 10:
                raw_ticker = raw_ticker[:8] + ".."
            data_points.append({"ticker": raw_ticker, "val": parts[1].strip()})

    if len(data_points) < 5:
        data_points = [
            {"ticker": "$NVDA", "val": "+6.2%"}, {"ticker": "$AAPL", "val": "+5.3%"},
            {"ticker": "$MSFT", "val": "+4.9%"}, {"ticker": "$GOOG", "val": "+4.2%"},
            {"ticker": "$AMZN", "val": "+2.3%"}
        ]

    W, H = 1080, 1920
    BG = "#09090b"
    ACCENT = "#10b981"
    ACCENT_LIGHT = "#6ee7b7"
    RED = "#ef4444"
    YELLOW = "#fbbf24"

    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    try: font_title = ImageFont.truetype(ft_path, 130)
    except: font_title = ImageFont.load_default()
    try: font_huge = ImageFont.truetype(ft_path, 240)
    except: font_huge = ImageFont.load_default()
    try: font_mega = ImageFont.truetype(ft_path, 160)
    except: font_mega = ImageFont.load_default()
    try: font_sub = ImageFont.truetype(ft_path, 65)
    except: font_sub = ImageFont.load_default()
    try: font_data = ImageFont.truetype(ft_path, 55)
    except: font_data = ImageFont.load_default()
    try: font_alert = ImageFont.truetype(ft_path, 80)
    except: font_alert = ImageFont.load_default()

    def wrap_lines(text, font, max_width):
        words = text.split()
        lines, line = [], []
        d = ImageDraw.Draw(Image.new("RGB", (1,1)))
        for ww in words:
            test_str = " ".join(line + [ww])
            try: tw = d.textlength(test_str, font=font)
            except: tw = len(test_str) * 50
            if tw < max_width:
                line.append(ww)
            else:
                if line: lines.append(" ".join(line))
                line = [ww]
        if line: lines.append(" ".join(line))
        return lines

    img1 = Image.new("RGB", (W, H), BG)
    d1 = ImageDraw.Draw(img1)
    d1.rounded_rectangle([60, 280, W-60, 400], radius=60, fill=RED)
    d1.text((W//2, 340), f"🚨 {cat.upper()} ALERT", fill="#ffffff", font=font_alert, anchor="mm")
    hook_lines = wrap_lines(hook_text.upper(), font_title, 980)
    y_text = H//2 - (len(hook_lines[:4]) * 75)
    for i, ln in enumerate(hook_lines[:4]):
        color = YELLOW if i == 0 else "#ffffff"
        d1.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 150
    d1.text((W//2, H - 380), "↓ SWIPE TO SEE WHY ↓", fill=ACCENT_LIGHT, font=font_sub, anchor="mm")

    img2 = Image.new("RGB", (W, H), BG)
    d2 = ImageDraw.Draw(img2)
    d2.text((W//2, 380), "THE NUMBER", fill=ACCENT, font=font_sub, anchor="mm")
    shock_lines = wrap_lines(shock_stat.upper(), font_mega, 980)
    y_text = H//2 - (len(shock_lines[:3]) * 90)
    for ln in shock_lines[:3]:
        d2.text((W//2, y_text), ln, fill=YELLOW, font=font_mega, anchor="mm")
        y_text += 180
    d2.text((W//2, H - 380), "WAIT FOR IT...", fill="#94a3b8", font=font_sub, anchor="mm")

    data_imgs = []
    for idx in range(3):
        if idx >= len(data_points): break
        item = data_points[idx]
        img_d = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img_d)
        d.text((W//2, 380), cat.upper(), fill=ACCENT, font=font_sub, anchor="mm")
        d.text((W//2, 500), f"WATCH THIS → {idx+1}/3", fill="#94a3b8", font=font_data, anchor="mm")
        d.text((W//2, 880), item['ticker'], fill="#ffffff", font=font_title, anchor="mm")
        val_str = item['val']
        val_color = RED if '-' in val_str else ACCENT_LIGHT
        d.text((W//2, 1200), val_str, fill=val_color, font=font_huge, anchor="mm")
        dot_y = H - 380
        for di in range(3):
            dx = W//2 + (di - 1) * 60
            color = ACCENT if di == idx else "#3f3f46"
            d.ellipse([dx-20, dot_y-20, dx+20, dot_y+20], fill=color)
        data_imgs.append(img_d)

    img6 = Image.new("RGB", (W, H), BG)
    d6 = ImageDraw.Draw(img6)
    d6.text((W//2, 380), "THE TAKEAWAY", fill=ACCENT, font=font_sub, anchor="mm")
    insight_lines = wrap_lines(insight_line.upper(), font_title, 980)
    y_text = 700 - (len(insight_lines[:3]) * 75)
    for ln in insight_lines[:3]:
        d6.text((W//2, y_text), ln, fill="#ffffff", font=font_title, anchor="mm")
        y_text += 150
    d6.text((W//2, 1200), cta_hook.upper(), fill=YELLOW, font=font_alert, anchor="mm")
    d6.rounded_rectangle([180, 1380, 900, 1580], radius=100, fill=ACCENT)
    d6.text((W//2, 1480), "LINK IN BIO →", fill="#ffffff", font=font_title, anchor="mm")
    d6.text((W//2, H - 200), "@WARMINSIGHT", fill=ACCENT_LIGHT, font=font_sub, anchor="mm")

    image_bytes_list = []
    all_frames = [img1, img2] + data_imgs + [img6]
    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, all_frames)

    return image_bytes_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes

# ═══════════════════════════════════════════════
# PUBLISHER (v45.7: Rank Math SEO 최적화)
# ═══════════════════════════════════════════════
def _upload_image(img_bytes, filename):
    try:
        resp = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"},
            data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30
        )
        if resp.status_code in (200, 201):
            return resp.json().get("id")
    except: pass
    return None

def get_or_create_wp_category(cat_name):
    slug = cat_name.lower().replace(" ", "-")
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0:
            return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/categories", json={"name": cat_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201):
            return r2.json()["id"]
    except: pass
    return None

def get_or_create_wp_tag(tag_name):
    slug = tag_name.lower().replace(" ", "-")
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/tags?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0:
            return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/tags", json={"name": tag_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201):
            return r2.json()["id"]
    except: pass
    return None

def get_wp_author_id(author_full_string):
    search_name = author_full_string.split("&")[0].strip()
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/users", params={"search": search_name}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200:
            users = r.json()
            if len(users) > 0:
                return users[0]["id"]
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, author_name, raw_for_cards=None):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None

    cat_id = get_or_create_wp_category(cat)

    insight_cat_id = None
    if cat not in ["Foundation", "The Daily Catalyst"]:
        insight_cat_id = get_or_create_wp_category("Insight")

    if tier == "unified":
        tag_id = get_or_create_wp_tag("Insight")
    elif tier == "vip":
        tag_id = get_or_create_wp_tag("VIP")
    else:
        tag_id = get_or_create_wp_tag("Pro")

    author_id = get_wp_author_id(author_name)

    if cat in ["Foundation", "The Daily Catalyst"] or tier == "unified":
        display_title = title
    else:
        display_title = f"[VIP] {title}" if tier == "vip" else f"[Pro] {title}"

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
    if len(seo_title) > 50:
         rm_title = seo_title
    else:
         rm_title = f"{seo_title} | Warm Insight"

    post_data["meta"] = {
        "rank_math_title": rm_title[:60],
        "rank_math_description": (exc or "")[:160],
        "rank_math_focus_keyword": kw.lower() if kw else "",
        "is_premium": "no" if cat == "Foundation" else "yes",
        "pms_content_restrict": "0" if cat == "Foundation" else "1",
        "post_tier": tier.upper(),
    }

    try:
        r = requests.post(
            f"{WP_URL}/wp-json/wp/v2/posts",
            json=post_data,
            auth=(WP_USER, WP_APP_PASS),
            timeout=30
        )
        if r.status_code in (200, 201):
            link = r.json().get('link')
            print(f"   ✅ Published: {link}")

            if (tier == "vip" or tier == "unified") and raw_for_cards:
                img_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes = generate_vip_carousel(raw_for_cards, cat)
                if video_mp4_bytes:
                    send_social_style_email(display_title, link, img_list, data_points, cat, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes)
            return True
        else:
            print(f"   ❌ Publish failed: {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Network error: {e}")
    return False

# ═══════════════════════════════════════════════
# 🔄 PIPELINES
# ═══════════════════════════════════════════════
def run_foundation_pipeline():
    cat = "Foundation"
    print(f"🚀 Starting v45.7 SEO Foundation Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    if not force and already_published_today(cat):
        print(f"   ⏭️  Skipping {cat} — already published today.")
        return
    if force:
        print(f"   ⚡ FORCE_PUBLISH=true — 중복 체크 건너뜀 (테스트 모드)")

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
            print(f"   ❌ Thumbnail too small or empty ({len(img_bytes) if img_bytes else 0} bytes).")
            print(f"   ⏳ Aborting publish. Next cron slot will retry.")
            return

        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author)

def run_philosophy_pipeline():
    cat = "The Daily Catalyst"
    print(f"🚀 Starting v45.7 Catalyst Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return

    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    if not force and already_published_today(cat):
        print(f"   ⏭️  Skipping {cat} — already published today.")
        return
    if force:
        print(f"   ⚡ FORCE_PUBLISH=true — 중복 체크 건너뜀 (테스트 모드)")

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
            print(f"   ❌ Thumbnail too small or empty ({len(img_bytes) if img_bytes else 0} bytes).")
            print(f"   ⏳ Aborting publish. Next cron slot will retry.")
            return

        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author)

def run_news_pipeline():
    day_of_year = datetime.datetime.utcnow().timetuple().tm_yday
    cat = CATEGORIES[day_of_year % len(CATEGORIES)]

    print(f"🚀 Starting v45.7 Unified News Pipeline | Category: {cat} (Day {day_of_year})")
    if not check_env_vars() or not verify_wp_credentials(): return

    force = os.environ.get("FORCE_PUBLISH", "false").lower() == "true"
    if not force and already_published_today(cat):
        print(f"   ⏭️  Skipping {cat} — already published today.")
        return
    if force:
        print(f"   ⚡ FORCE_PUBLISH=true — 중복 체크 건너뜀 (테스트 모드)")

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
        print("   ⚠️ Part 2 generation failed. Using Part 1 only.")
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
        print(f"   ❌ Thumbnail too small or empty ({len(img_bytes) if img_bytes else 0} bytes).")
        print(f"   ⏳ Aborting publish. Next cron slot will retry.")
        return

    publish(title, html, exc, kw, cat, slug, tier, img_bytes, author, raw_for_cards=raw)
    time.sleep(TIER_SLEEP[tier])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "philosophy": run_philosophy_pipeline()
        elif sys.argv[1] == "foundation": run_foundation_pipeline()
    else:
        run_news_pipeline()
