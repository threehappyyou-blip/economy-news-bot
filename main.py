#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — Ultimate Masterpiece Edition (v46.9.59)
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
#   9. [언어 픽스] Action Plan 박스 내 하드코딩된 한글 서브타이틀 영문으로 완전 교체
#  10. [엔진 픽스] Money Hack 무한 주제 생성 엔진(Infinite Topic Engine) 탑재
#  11. [SEO 픽스] 전 카테고리 H2/H3 태그에 포커스 키워드(SEO_KEYWORD) 동적 결합
#  12. [통신 픽스] Imunify360 WAF 차단 원천 해결: WP 내부 통신을 Cloudscraper로 100% 교체
#  13. [API 픽스] Imagen 모델 안정화 버전(imagen-3.0-generate-001)으로 404 NOT_FOUND 에러 해결
#  14. [마케팅 확장] 미디엄 Teaser Draft 이메일 및 레딧/쿼라 타겟 바이럴 게릴라 포스팅 이메일 자동 발송
#  15. [이메일 누락 픽스] 🚨 숏폼 영상 비트레이트 2500k 다이어트로 구글 메일 사전 차단(Silent Drop) 완벽 해결
#  16. [숏폼 엔진 완벽 이식] 🔥 대표님께서 제공해주신 "다이내믹 4 AI Image + 줌 애니메이션" 완벽 적용
#  17. [치명적 버그 픽스] 🚨 _upload_image 함수 누락으로 인한 NameError 완벽 복구 (발행 정상화)
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
# 🧠 1. FOUNDATION DATABASE & PROMPTS (ANTI-FATIGUE UPGRADED)
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
- ALWAYS use specific, concrete examples.
You MUST wrap your content EXACTLY in the XML tags requested."""

FOUNDATION_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write an SEO-optimized beginner's guide on the following topic in English:
TOPIC: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD.)</EXCERPT>
<DEFINITION>(Simple 2-paragraph definition using an UNEXPECTED everyday analogy.)</DEFINITION>
<WHY_MATTERS>(Explain in 2 paragraphs why a beginner should care. Use concrete amounts.)</WHY_MATTERS>
<HOW_TO_START>(3 ACTIONABLE steps. Format as a bulleted list.)</HOW_TO_START>
<POLL_QUESTION>(A provocative multiple-choice question)</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>"""

# ═══════════════════════════════════════════════
# 🧠 2. PHILOSOPHY DATABASE & PROMPTS (ANTI-FATIGUE UPGRADED)
# ═══════════════════════════════════════════════
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
- BANNED WORDS: "Delve into", "Unleash", "Game-changer", "In today's fast-paced world", "Embark on this journey".
- DO NOT sound like a generic self-help guru. Be harsh, direct, and unapologetic. 
You MUST wrap your content EXACTLY in the XML tags requested."""

PHILOSOPHY_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write a philosophical daily insight based on the following theme in English:
THEME: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD.)</EXCERPT>
<ANCHOR>(A one-sentence philosophical principle based on the theme.)</ANCHOR>
<REFLECTION>(3-4 paragraphs explaining how this principle connects to modern reality.)</REFLECTION>
<CATALYST>(A single, highly provocative and specific question.)</CATALYST>
<POLL_QUESTION>(A provocative multiple-choice question)</POLL_QUESTION>
<POLL_OPT1>(Option 1, max 6 words)</POLL_OPT1>
<POLL_OPT2>(Option 2, max 6 words)</POLL_OPT2>
<POLL_OPT3>(Option 3, max 6 words)</POLL_OPT3>"""

# ═══════════════════════════════════════════════
# 🧠 3. MONEY HACK (SIDE HUSTLE) 무한 생성 엔진
# ═══════════════════════════════════════════════
MH_NICHES = ["Digital Products & Templates", "E-commerce & Dropshipping", "Freelancing & Agency", "Content Creation & Faceless Channels", "Micro-SaaS & Software", "Domain & Asset Flipping", "Affiliate Marketing", "Consulting & Coaching", "Paid Newsletter & Community", "Print on Demand"]
MH_PLATFORMS = ["Gumroad", "Shopify", "Canva", "Notion", "Fiverr", "Upwork", "YouTube", "TikTok", "Twitter/X", "LinkedIn", "Pinterest", "Substack", "Etsy", "Amazon KDP", "WordPress"]
MH_AI_TOOLS = ["ChatGPT", "Midjourney", "Claude", "ElevenLabs", "Zapier/Make", "CapCut AI", "Perplexity", "RunwayML", "HeyGen", "OpusClip"]

MONEY_HACK_SYS_INST = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
You are an elite side-hustle expert and digital business coach. Your objective is to write a highly actionable, step-by-step 'Money Hack' guide that helps normal people make an extra $1,000/month.
🔥 ANTI-CLICHÉ & ZERO-FLUFF POLICY: No "Passive income machine" or "Get rich quick". Acknowledge the grind. Be ruthlessly practical. Use specific tool names and actual dollar amounts."""

MONEY_HACK_PROMPT = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write an SEO-optimized, step-by-step side hustle guide based on this randomly generated framework:
FRAMEWORK: {theme}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the SEO_KEYWORD.)</EXCERPT>
<CONCEPT>(2 paragraphs explaining what this side hustle is and why it's profitable.)</CONCEPT>
<STEP_BY_STEP_TOOL>(A clear 1-2-3 checklist to execute today. Exact instructions.)</STEP_BY_STEP_TOOL>
<PRO_TIP>(1 paragraph revealing a secret tip that top 1% earners use.)</PRO_TIP>
<POLL_QUESTION>(A provocative multiple-choice question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

# ═══════════════════════════════════════════════
# 🎨 4. TWO-PART PROMPTS (REGULAR NEWS)
# ═══════════════════════════════════════════════
PROMPT_UNIFIED_P1 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write PART 1 of an Insight newsletter on {cat} in ENGLISH. Target length: 900-1100 words across both parts.
News Context: {news}
<TITLE>(Max 60 chars. MUST include the exact SEO_KEYWORD.)</TITLE>
<SEO_KEYWORD>(Write a highly specific LONG-TAIL focus keyword, 4-6 words)</SEO_KEYWORD>
<EXCERPT>(Max 150 chars. MUST include the exact SEO_KEYWORD.)</EXCERPT>
<WARM_INDEX_SCORE>(0-100 integer)</WARM_INDEX_SCORE>
<WARM_INDEX_REASON>(5-10 word explanation)</WARM_INDEX_REASON>
<IMPACT>(HIGH, MEDIUM, or LOW)</IMPACT>
<DATA_TABLE>(Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight under 12 words)</DATA_TABLE>
<HEATMAP>(Sector Name | Number)</HEATMAP>
<EXECUTIVE_SUMMARY>(3 sentences capturing your COUNTERINTUITIVE thesis. Use 1 emoji.)</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>(3-4 sentences with your ONE specific analogy.)</PLAIN_ENGLISH>
<HEADLINE>(Analytical headline)</HEADLINE>
<MACRO>(2 PARAGRAPHS. What's happening and WHY it's happening.)</MACRO>
<HERD>(What retail investors are doing wrong RIGHT NOW.)</HERD>
<CONTRARIAN>(What smart money is doing differently.)</CONTRARIAN>
<QUICK_FLOW>(Chain of events with arrows ➡️ 5-6 steps.)</QUICK_FLOW>"""

PROMPT_UNIFIED_P2 = """CRITICAL RULE: ALL OUTPUT MUST BE IN 100% NATIVE ENGLISH. NO KOREAN.
Write PART 2 of the Insight newsletter for {cat} in ENGLISH.
Context from Part 1: {ctx}
<BULL_CASE>(Optimistic scenario. 3-4 sentences.)</BULL_CASE>
<BEAR_CASE>(Pessimistic scenario. 3-4 sentences.)</BEAR_CASE>
<HISTORICAL_PARALLEL>(Name the year + event. What's different.)</HISTORICAL_PARALLEL>
<QUICK_HITS>(EXACTLY 3 bullet points starting with emojis: 🚨 / 👀 / 🤔 / 💸)</QUICK_HITS>
<SMART_MONEY_MOVE>(1 paragraph. NAME 1 specific ETF ticker.)</SMART_MONEY_MOVE>
<DO_ACTION>(Provide exactly ONE highly specific, actionable strategy for absolute beginners with precise numbers.)</DO_ACTION>
<DONT_ACTION>(1 critical mistake to avoid. Be blunt.)</DONT_ACTION>
<TAKEAWAY>(The bottom line insight. Under 20 words.)</TAKEAWAY>
<PS>(One-line veteran advice with historical context.)</PS>
<POLL_QUESTION>(A provocative multiple-choice question)</POLL_QUESTION>
<POLL_OPT1>(Option 1)</POLL_OPT1>
<POLL_OPT2>(Option 2)</POLL_OPT2>
<POLL_OPT3>(Option 3)</POLL_OPT3>"""

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

# 🚨 이 함수가 누락되어 썸네일 업로드 시 발행이 뻗었던 문제를 완벽히 복구했습니다!
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

# ═══════════════════════════════════════════════
# 🎬 EMAIL & YOUTUBE ENGINE
# ═══════════════════════════════════════════════
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
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; padding-bottom:10px; display:inline-block;">Executive Summary</h2>"""
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
    html += f"""<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; padding-bottom:10px; display:inline-block; margin-top:30px;">Market Drivers & Flow</h2>"""
    html += f"""<h3 style="font-size:24px; color:{DARK}; margin-top:20px;">{xtag(raw, "HEADLINE")}</h3>"""
    html += f"""<div style="background:#fff; border:1px solid {BORDER}; border-left:5px solid {GOLD}; padding:30px; border-radius:8px; margin:30px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <p><strong>🧐 The Big Picture:</strong> {xtag(raw, "MACRO")}</p><hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
        <p><strong>🐑 What Most People Are Doing:</strong> {xtag(raw, "HERD")}</p><hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
        <p><strong>🦅 What Smart Money Is Doing:</strong> {xtag(raw, "CONTRARIAN")}</p>
    </div><div id="warm-ad-middle" style="margin: 40px 0; text-align: center;"></div>"""
    html += f"""<div style="background:#fffbeb; border:1px solid #fde68a; border-left:5px solid {AMBER}; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;">
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
    html += f"""<div style="background:#ffffff; border:2px solid {GOLD}; padding:30px; border-radius:8px; margin:45px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; color:{GOLD}; font-size:24px;">💎 Smart Money Move</h3><p style="margin:0;">{xtag(raw, "SMART_MONEY_MOVE")}</p>
    </div>"""
    if xtag(raw, "HISTORICAL_PARALLEL"):
        html += f"""<div style="background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding:35px; border-radius:12px; margin:45px 0; border-left:5px solid {GOLD};">
            <h3 style="color:{GOLD}; margin-top:0; font-size:24px; display:flex; align-items:center; gap:10px;">📜 Historical Parallel</h3>
            <p style="color:#cbd5e1; font-size:17px; line-height:1.8; margin:15px 0 0;">{xtag(raw, "HISTORICAL_PARALLEL")}</p>
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
        <p style="color:#e2e8f0; font-size:18px; margin:0; line-height:1.6;"><strong style="color:{GOLD};">P.S.</strong> {xtag(raw, "PS")}</p>
    </div>"""
    html += _build_pillar_link("Insight") + _build_poll(raw, cat) + _build_branded_footer()
    html += f"""<p style="font-size:17px; font-weight:800; color:{DARK}; text-align:center; margin-top:50px; margin-bottom:10px;">💬 Click to join the discussion below! 👇</p>
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:20px; text-transform:uppercase; letter-spacing:0.5px;">Disclaimer: AI-generated, human-edited educational content. Not financial advice. All decisions are your own.</p></div>"""
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
# 🎬 6-슬라이드 다크 심리학 숏폼 비디오 엔진 (완벽 이식)
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

        # 🚨 비트레이트를 2500k로 세팅하여 구글 이메일 차단 방어
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
    
    # 🚨 1번 영상 스타일 고정: 기승전결(문맥)에 맞춰 변하는 4개의 다크 심리학 이미지 프롬프트
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

    # 🚨 429 에러(서버 차단)를 피하기 위한 5초 딜레이 필수 적용
    print("    [AI] Requesting 4 unique images for Dynamic Storytelling...")
    img_hook_ai = fetch_dark_psy_image(vp1, random.randint(1, 100000))
    time.sleep(5)
    img_stat_ai = fetch_dark_psy_image(vp2, random.randint(1, 100000))
    time.sleep(5)
    img_data_ai = fetch_dark_psy_image(vp3, random.randint(1, 100000))
    time.sleep(5)
    img_out_ai  = fetch_dark_psy_image(vp4, random.randint(1, 100000))

    # 스마트 폴백 (성공한 고퀄 이미지가 있다면, 실패한 곳에 덮어쓰기)
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

    # 1. 훅 (Hook) 슬라이드
    img1 = Image.new("RGB", (W, H), BG)
    paste_bg(img1, img_hook_ai)
    d1 = ImageDraw.Draw(img1)
    d1.rounded_rectangle([300, 1150, 780, 1250], radius=20, fill=RED)
    d1.text((W//2, 1200), f"🚨 {cat.upper()} ALERT", fill=WHITE, font=font_alert, anchor="mm")
    
    # 🚨 텍스트 좌우 여백을 850px로 넉넉하게 설정
    hook_lines = wrap_lines(hook_text.upper(), font_title, 850) 
    y_text = 1350
    for i, ln in enumerate(hook_lines[:4]):
        color = RED if i == len(hook_lines)-1 else WHITE
        d1.text((W//2, y_text), ln, fill=color, font=font_title, anchor="mm")
        y_text += 105 
    d1.text((W//2, 1800), "↓ SWIPE TO SEE WHY ↓", fill=GRAY, font=font_sub, anchor="mm")

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
        
        # 🚨 데이터 글자 길이에 따라 폰트 사이즈가 동적으로 줄어들게 처리
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

    image_bytes_list = []
    all_frames = [img1, img2] + data_imgs + [img6]
    video_mp4_bytes = generate_video_mp4(cat, hook_text, data_points, all_frames)

    return image_bytes_list, data_points, hook_text, question_text, reels_script, ig_caption, smart_comment, video_mp4_bytes

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

    print(f"🚀 Starting v46.9.59 Unified News Pipeline | Category: {cat}")
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
