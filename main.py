#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — Ultimate Masterpiece Edition (v46.9.58)
#
# [안내] 
# 이 코드는 전체 1,100줄 중 절반에 해당하는 [1부]입니다.
# 이어지는 [2부] 코드와 합쳐서 사용해 주세요.
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
# 🎬 1. YOUTUBE CHAPTERING & EMAIL ENGINE
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
# 🧠 PROMPTS (ANTI-FATIGUE UPGRADED)
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
# 📊 VISUAL DATA BUILDERS & HTML
# ═══════════════════════════════════════════════

def _build_warm_index(raw_data):
    score_str = xtag(raw_data, "WARM_INDEX_SCORE")
    reason = xtag(raw_data, "WARM_INDEX_REASON")
    
    if not score_str: return ""
    
    try: score = int(re.sub(r'[^0-9]', '', score_str))
    except: return ""
    score = max(0, min(100, score))
    
    if score < 30:
        c_main, label, icon = "#3b82f6", "Fear Zone", "❄️"
        grad = "linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%)"
    elif score > 70:
        c_main, label, icon = "#ef4444", "Greed Zone", "🔥"
        grad = "linear-gradient(90deg, #b91c1c 0%, #ef4444 100%)"
    else:
        c_main, label, icon = "#f59e0b", "Neutral", "⚖️"
        grad = "linear-gradient(90deg, #b45309 0%, #f59e0b 100%)"

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
    question = xtag(raw_data, "POLL_QUESTION").strip()
    opt1 = xtag(raw_data, "POLL_OPT1").strip()
    opt2 = xtag(raw_data, "POLL_OPT2").strip()
    opt3 = xtag(raw_data, "POLL_OPT3").strip()
    
    if not question:
        question = f"What is your perspective on today's {cat} news?"
    if not opt1: opt1 = "Bullish – I see an opportunity."
    if not opt2: opt2 = "Neutral – Waiting for more signals."
    if not opt3: opt3 = "Bearish – Taking a cautious stance."

    opt3_html = ""
    if opt3:
        opt3_html = f"""<a href="#respond" style="display:block; background:#ffffff; border:2px solid {BORDER}; color:{DARK}; padding:14px; border-radius:8px; text-decoration:none; font-weight:700; font-size:16px; transition:all 0.2s;" onmouseover="this.style.borderColor='{GOLD}'; this.style.backgroundColor='#fefce8';" onmouseout="this.style.borderColor='{BORDER}'; this.style.backgroundColor='#ffffff';">{opt3}</a>"""

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
        items_html += f"""<li style="margin-bottom:12px; color:{SLATE};">{clean}</li>"""

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
        "Energy": ("#d97706", "#fbbf24", "#fef3c7"),
        "On-Chain": ("#8b5cf6", "#a78bfa", "#ede9fe")
    }
    c_s, c_b, c_c = cat_colors.get(cat, ("#b8974d", "#cbd5e1", "#f1f5f9"))

    circ = 565.49
    sd, bd, cd = circ*s/100, circ*b/100, circ*c/100

    pie = f"""<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;">"""
    pie += f"""<circle cx="100" cy="100" r="90" fill="none" stroke="{c_s}" stroke-width="30" stroke-dasharray="{sd} {circ}" stroke-dashoffset="0"/>"""
    pie += f"""<circle cx="100" cy="100" r="90" fill="none" stroke="{c_b}" stroke-width="30" stroke-dasharray="{bd} {circ}" stroke-dashoffset="-{sd}"/>"""
    pie += f"""<circle cx="100" cy="100" r="90" fill="none" stroke="{c_c}" stroke-width="30" stroke-dasharray="{cd} {circ}" stroke-dashoffset="-{sd+bd}"/>"""
    pie += f"""<text x="100" y="95" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">{s}/{b}/{c}</text>"""
    pie += f"""<text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>"""

    pie += f"""<div style="display:flex;justify-content:center;gap:20px;">"""
    pie += f"""<span style="color:{c_s};font-weight:bold;">● Stocks/Assets {s}%</span>"""
    pie += f"""<span style="color:{c_b};font-weight:bold;">● Safe {b}%</span>"""
    pie += f"""<span style="color:{c_c};font-weight:bold;">● Cash {c}%</span></div>"""

    return pie

def _build_pillar_link(target_cat):
    pillar = PILLAR_PAGES.get(target_cat)
    if not pillar: return ""
    return f"""
    <div style="background:#f8fafc; border-left:4px solid #3b82f6; padding:20px; margin:40px 0; border-radius:4px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
        <p style="margin:0; font-size:16px; color:#1e293b;">
            <strong style="color:#2563eb;">📚 Deep Dive:</strong> Want to master this topic? Check out our complete guide to <a href="{pillar['url']}" style="color:#2563eb; text-decoration:underline; font-weight:700;">{pillar['anchor']}</a>.
        </p>
    </div>
    """

def _build_branded_footer():
    si = ""
    if SOCIAL_LINKS.get("youtube"):
        si += f"""<a href="{SOCIAL_LINKS["youtube"]}" target="_blank" style="display:inline-block; background:#FF0000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">▶ YouTube</a>"""
    if SOCIAL_LINKS.get("tiktok"):
        si += f"""<a href="{SOCIAL_LINKS["tiktok"]}" target="_blank" style="display:inline-block; background:#000000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">🎵 TikTok</a>"""
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
            &copy; {datetime.datetime.utcnow().year} Warm Insight. All rights reserved.
        </p>
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
# 🎨 HTML BUILDERS
# ═══════════════════════════════════════════════
def build_foundation_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n"""
    kw = xtag(raw, "SEO_KEYWORD").title()
    k_suf = f": {kw}" if kw else ""
    html += _build_founder_note()
    def_text = xtag(raw, "DEFINITION").replace("\n", "<br><br>")
    html += f"""
    <div style="background:#f0fdf4; border-left:5px solid #10b981; padding:25px; margin:30px 0; border-radius:0 8px 8px 0;">
        <h3 style="margin-top:0; font-size:22px; color:#065f46;">📖 What is it? (Definition){k_suf}</h3>
        <div style="color:#064e3b; font-size:18px; line-height:1.8;">{def_text}</div>
    </div>
    """
    why_text = xtag(raw, "WHY_MATTERS").replace("\n", "<br><br>")
    html += f"""
    <div style="margin:40px 0;">
        <h3 style="font-size:24px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">💡 Why It Matters{k_suf}</h3>
        <p>{why_text}</p>
    </div>
    """
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    how_text = xtag(raw, "HOW_TO_START").replace("\n", "<br><br>")
    html += f"""
    <div style="background:#ffffff; border:2px solid #3b82f6; padding:30px; border-radius:12px; margin:40px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; color:#1e40af; font-size:24px;">🚀 How to Start Today{k_suf}</h3>
        <div style="color:{SLATE}; font-size:18px; line-height:1.8;">{how_text}</div>
    </div>
    """
    html += _build_pillar_link("Foundation") 
    html += _build_poll(raw, cat)
    html += _build_branded_footer()
    html += f"""
    <p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">
        💬 Click to join the discussion below! 👇
    </p>
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:20px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: Educational content only.
    </p>
    </div>
    """
    return sanitize(html)

def build_philosophy_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n"""
    kw = xtag(raw, "SEO_KEYWORD").title()
    k_suf = f" — {kw}" if kw else ""
    html += _build_founder_note()
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
        <h3 style="font-size:22px; color:{DARK}; border-left:4px solid {GOLD}; padding-left:12px; margin-bottom:20px;">The Reflection{k_suf}</h3>
        <div style="color:{SLATE}; font-size:18px; line-height:1.8;">{reflection_text}</div>
    </div>
    """
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    catalyst_raw = xtag(raw, "CATALYST")
    catalyst_text = re.sub(r'<[^>]+>', '', catalyst_raw)
    html += f"""
    <div style="background:#fefce8; border:2px solid #fde047; padding:35px; border-radius:12px; margin:50px 0; text-align:center; box-shadow:0 10px 15px -3px rgba(0, 0, 0, 0.05);">
        <p style="font-size:14px; font-weight:800; color:#b45309; text-transform:uppercase; letter-spacing:2px; margin:0 0 15px;">⚡ The Daily Catalyst</p>
        <p style="font-size:24px; font-weight:900; color:#92400e; margin:0 0 20px; line-height:1.5;">{catalyst_text}</p>
        <p style="font-size:15px; color:#b45309; margin:0; font-style:italic;">
            Don't just read. Take out a pen and write your answer now.
        </p>
    </div>
    """
    html += _build_pillar_link("The Daily Catalyst") 
    html += _build_poll(raw, cat)
    html += _build_branded_footer()
    html += f"""
    <p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">
        💬 Click to join the discussion below! 👇
    </p>
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:20px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: This article is for informational purposes only.
    </p>
    </div>
    """
    return sanitize(html)

def build_money_hack_html(raw, author, tf, title, cat):
    html = f"""<div style="{F}">\n"""
    kw = xtag(raw, "SEO_KEYWORD").title()
    k_suf = f": {kw}" if kw else ""
    html += _build_founder_note()
    concept = xtag(raw, "CONCEPT").replace("\n", "<br><br>")
    html += f"""
    <div style="margin:40px 0;">
        <h3 style="font-size:24px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">💡 The Concept{k_suf}</h3>
        <p>{concept}</p>
    </div>
    """
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    tools = xtag(raw, "STEP_BY_STEP_TOOL").replace("\n", "<br><br>")
    html += f"""
    <div style="background:#f0fdf4; border:2px solid #10b981; padding:30px; border-radius:12px; margin:40px 0; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; color:#065f46; font-size:24px; display:flex; align-items:center; gap:8px;">🛠️ Step-by-Step Execution{k_suf}</h3>
        <div style="color:#064e3b; font-size:17px; line-height:1.8;">{tools}</div>
    </div>
    """
    pro_tip = xtag(raw, "PRO_TIP").replace("\n", "<br>")
    html += f"""
    <div style="background:#fffbeb; border-left:5px solid #f59e0b; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;">
        <p style="margin:0; font-size:18px; font-weight:800; color:#b45309; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px;">🔥 Pro Tip</p>
        <p style="margin:0; color:#92400e; font-style:italic;">{pro_tip}</p>
    </div>
    """
    html += _build_pillar_link("Money Hack")
    html += _build_poll(raw, cat)
    html += _build_branded_footer()
    html += f"""
    <p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">
        💬 Click to join the discussion below! 👇
    </p>
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:20px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: Educational content only. Results may vary based on individual effort.
    </p>
    </div>
    """
    return sanitize(html)

def build_html(tier, cat, raw, author, tf, title):
    html = f"""<div style="{F}">\n"""
    badge = "WARM INSIGHT"
    badge_bg = GOLD
    kw = xtag(raw, "SEO_KEYWORD").title()
    k_suf = f": {kw}" if kw else ""
    html += _build_warm_index(raw)
    html += _build_founder_note()
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {badge_bg}; padding-bottom:10px; display:inline-block;">Executive Summary{k_suf}</h2>"""
    html += f"""<p style="font-size:19px; font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>"""
    do_act = xtag(raw, "DO_ACTION").replace('\n', '<br>')
    dont_act = xtag(raw, "DONT_ACTION").replace('\n', '<br>')
    html += f"""
    <div style="background:#fffbeb; border:2px solid #f59e0b; padding:25px; margin:35px 0; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; color:#b45309; font-size:22px; display:flex; align-items:center; gap:8px;">
            ⚠️ One-Point Action Plan for Beginners
        </h3>
        <p style="font-size:15px; color:#92400e; margin-top:-10px; margin-bottom:20px;">Today's specific, actionable strategy for absolute beginners</p>
        <div style="background:#ffffff; border-left:5px solid #10b981; padding:20px; border-radius:6px; margin-bottom:15px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
            <p style="margin:0; color:#065f46; font-size:18px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">🟢 DO THIS:</p>
            <p style="margin:8px 0 0; color:#064e3b; font-size:17px; line-height:1.6; font-weight:500;">{do_act}</p>
        </div>
        <div style="background:#ffffff; border-left:5px solid #ef4444; padding:20px; border-radius:6px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
            <p style="margin:0; color:#991b1b; font-size:18px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">🔴 AVOID THIS:</p>
            <p style="margin:8px 0 0; color:#7f1d1d; font-size:17px; line-height:1.6; font-weight:500;">{dont_act}</p>
        </div>
    </div>
    """
    html += _build_data_table(xtag(raw, "DATA_TABLE"), "Market Dashboard")
    html += _build_progress_bars(xtag(raw, "HEATMAP"), "Sector Risk Heatmap")
    html += f"""
    <div style="background:#faf5ff; border-left:5px solid #8b5cf6; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;">
        <p style="font-size:20px; font-weight:800; color:#4c1d95; margin:0 0 12px;">💡 Plain English{k_suf}</p>
        <p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p>
    </div>
    """
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {badge_bg}; padding-bottom:10px; display:inline-block; margin-top:30px;">Market Drivers & Flow{k_suf}</h2>"""
    html += f"""<h3 style="font-size:24px; color:{DARK}; margin-top:20px;">{xtag(raw, "HEADLINE")}</h3>"""
    html += f"""
    <div style="background:#fff; border:1px solid {BORDER}; border-left:5px solid {badge_bg}; padding:30px; border-radius:8px; margin:30px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <p><strong>🧐 The Big Picture:</strong> {xtag(raw, "MACRO")}</p>
        <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
        <p><strong>🐑 What Most People Are Doing:</strong> {xtag(raw, "HERD")}</p>
        <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
        <p><strong>🦅 What Smart Money Is Doing:</strong> {xtag(raw, "CONTRARIAN")}</p>
    </div>
    """
    html += """<div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
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
            <h3 style="color:{badge_bg}; margin-top:0; font-size:24px; display:flex; align-items:center; gap:10px;">📜 Historical Parallel</h3>
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
    html += _build_pillar_link("Insight") 
    html += _build_poll(raw, cat)
    html += _build_branded_footer()
    html += f"""
    <p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">
        💬 Click to join the discussion below! 👇
    </p>
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:20px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: AI-generated, human-edited educational content. Not financial advice. All decisions are your own.
    </p>
    </div>
    """
    return sanitize(html)

def get_font(url, filename):
    if not os.path.exists(filename) or os.path.getsize(filename) < 1000:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            resp = scraper.get(url, timeout=15)
            resp.raise_for_status()
            with open(filename, 'wb') as f: f.write(resp.content)
        except: pass
    return filename

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

# ═══════════════════════════════════════════════
# 🎬 6-슬라이드 다크 심리학 숏폼 비디오 엔진 (완벽 교체 부분)
# ═══════════════════════════════════════════════
def generate_video_mp4(cat, hook_text, data_points, frames_images):
    print("   🎥 Generating 15-Sec Dark Psychology Dynamic Reels Video...")
    try:
        import numpy as np
        from moviepy.editor import ImageClip, concatenate_videoclips
    except ImportError as e:
        print(f"   ❌ MoviePy import failed: {e}")
        return None
    try:
        # 🚨 슬라이드마다 줌인/줌아웃 애니메이션 교차 적용
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
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        # 🚨 비트레이트를 2500k로 세팅하여 구글 이메일 차단(Drop) 방어
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
        print(f"   ✅ Dynamic Dark Psychology 15s Video Extracted! ({len(mp4_bytes)/1024/1024:.1f}MB)")
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
    
    # 🚨 4개의 다이내믹 다크 심리학 이미지 프롬프트 (기승전결)
    vp_base = f"A creepy pale featureless white mannequin humanoid figure, pitch black background, surrounded by glowing red abstract objects representing {cat}. Dark psychology aesthetic, mysterious, highly detailed 3D render. No text."
    vp1 = vp_base + " The humanoid is reacting in shock, holding its head, looking at a crashing red graph."
    vp2 = vp_base + " The humanoid is carefully analyzing a glowing red data sphere in its hands."
    vp3 = vp_base + " The humanoid is touching and manipulating floating red digital nodes and charts."
    vp4 = vp_base + " The humanoid is standing confidently looking forward with a powerful glowing red aura."

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
    RED = "#ef4444"
    GRAY = "#94a3b8"

    import urllib.request, urllib.parse
    ft_path = get_font("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "fonts/BebasNeue-Regular.ttf")

    def lf(p, s):
        try: return ImageFont.truetype(p, s)
        except: return ImageFont.load_default()

    # 🚨 폰트 사이즈 다이어트 (글자 잘림 100% 방지)
    font_title = lf(ft_path, 95)    
    font_huge = lf(ft_path, 200)    
    font_mega = lf(ft_path, 135)    
    font_sub = lf(ft_path, 55)
    font_data = lf(ft_path, 50)
    font_alert = lf(ft_path, 75)

    def fetch_dark_psy_image(prompt_text, seed):
        try:
            prompt_encoded = urllib.parse.quote(prompt_text)
            url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1080&height=1080&nologo=true&seed={seed}"
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

    # 🚨 429 에러(서버 차단) 피하기 위한 5초 딜레이
    print("    [AI] Requesting 4 unique images for Dynamic Storytelling...")
    img_hook_ai = fetch_dark_psy_image(vp1, random.randint(1, 100000))
    time.sleep(5)
    img_stat_ai = fetch_dark_psy_image(vp2, random.randint(1, 100000))
    time.sleep(5)
    img_data_ai = fetch_dark_psy_image(vp3, random.randint(1, 100000))
    time.sleep(5)
    img_out_ai  = fetch_dark_psy_image(vp4, random.randint(1, 100000))

    # 🚨 스마트 폴백 (성공한 고퀄 이미지가 있다면, 실패한 곳에 덮어쓰기)
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

    frames = []

    # 1. 훅 (Hook) 슬라이드
    img1 = Image.new("RGB", (W, H), BG)
    paste_bg(img1, img_hook_ai)
    d1 = ImageDraw.Draw(img1)
    d1.rounded_rectangle([300, 1150, 780, 1250], radius=20, fill=RED)
    d1.text((W//2, 1200), f"🚨 {cat.upper()} ALERT", fill=WHITE, font=font_alert, anchor="mm")
    
    # 🚨 좌우 여백을 850px로 넉넉하게 설정
    hook_lines = wrap_lines(hook_text.upper(), font_title, 850) 
    y_text = 1350
    for i, ln in enumerate(hook_lines[:4]):
        color = RED if i == len(hook_lines)-1 else WHITE
        d1.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 105 
    d1.text((W//2, 1800), "↓ SWIPE TO SEE WHY ↓", fill=GRAY, font=font_sub, anchor="mm")
    frames.append(img1)

    # 2. 충격 스탯 (Shock Stat) 슬라이드
    img2 = Image.new("RGB", (W, H), BG)
    paste_bg(img2, img_stat_ai)
    d2 = ImageDraw.Draw(img2)
    d2.text((W//2, 1180), "THE NUMBER", fill=RED, font=font_sub, anchor="mm")
    shock_lines = wrap_lines(shock_stat.upper(), font_mega, 850)
    y_text = 1350
    for ln in shock_lines[:3]:
        d2.text((W//2, y_text), ln, fill=WHITE, font=font_mega, anchor="mm")
        y_text += 140 
    d2.text((W//2, 1800), "WAIT FOR IT...", fill=GRAY, font=font_sub, anchor="mm")
    frames.append(img2)

    # 3~5. 데이터포인트 슬라이드
    data_imgs = []
    for idx in range(3):
        if idx >= len(data_points): break
        item = data_points[idx]
        img_d = Image.new("RGB", (W, H), BG)
        paste_bg(img_d, img_data_ai)
        d = ImageDraw.Draw(img_d)
        d.text((W//2, 1150), cat.upper(), fill=RED, font=font_sub, anchor="mm")
        d.text((W//2, 1250), f"WATCH THIS → {idx+1}/3", fill=GRAY, font=font_data, anchor="mm")
        d.text((W//2, 1400), item['ticker'], fill=WHITE, font=font_title, anchor="mm")
        
        val_str = item['val']
        val_color = RED if '-' in val_str else WHITE
        
        # 🚨 데이터 글자 길이에 따라 폰트 사이즈가 동적으로 축소
        current_huge_size = 200
        if len(val_str) > 6:
            current_huge_size = int(200 * (6 / len(val_str)))
        current_font_huge = lf(ft_path, max(90, current_huge_size))
        
        d.text((W//2, 1550), val_str, fill=val_color, font=current_font_huge, anchor="mm")
        
        dot_y = 1800
        for di in range(3):
            dx = W//2 + (di - 1) * 60
            color = RED if di == idx else "#3f3f46"
            d.ellipse([dx-15, dot_y-15, dx+15, dot_y+15], fill=color)
        data_imgs.append(img_d)
    frames.extend(data_imgs)

    # 6. 통찰 및 CTA 슬라이드
    img6 = Image.new("RGB", (W, H), BG)
    paste_bg(img6, img_out_ai)
    d6 = ImageDraw.Draw(img6)
    d6.text((W//2, 1150), "THE TAKEAWAY", fill=RED, font=font_sub, anchor="mm")
    insight_lines = wrap_lines(insight_line.upper(), font_title, 850)
    y_text = 1250
    for ln in insight_lines[:3]:
        d6.text((W//2, y_text), ln, fill=WHITE, font=font_title, anchor="mm")
        y_text += 105
    d6.text((W//2, 1650), cta_hook.upper(), fill=RED, font=font_alert, anchor="mm")
    d6.text((W//2, 1780), "LINK IN BIO → @WARMINSIGHT", fill=GRAY, font=font_sub, anchor="mm")
    frames.append(img6)

    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, frames)
    return [], data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes

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

    print(f"🚀 Starting v46.9.58 Unified News Pipeline | Category: {cat}")
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
