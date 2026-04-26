#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v40.19 (Hide X/Twitter Button)
# v40.19 대비 변경점:
#   1) 사용하지 않는 X(트위터) 소셜 공유 버튼 숨김 처리
#   2) v40.18의 썸네일 제목 필터링 및 밀크로드 디자인 100% 유지
# ═══════════════════════════════════════════════════════════════
import os, sys, traceback, time, random, re, datetime, io, math
import urllib.request
import requests
import feedparser
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
WP_URL         = os.environ.get("WP_URL", "https://warminsight.com").rstrip("/")
WP_USER        = os.environ.get("WP_USERNAME", "")
WP_APP_PASS    = os.environ.get("WP_APP_PASSWORD", "")
SITE_URL       = "https://warminsight.com"

MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
    "Premium": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
}
FAST_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]

CATEGORIES  = ["Economy", "Politics", "Tech", "Health", "Energy"]
TIERS       = ["premium", "vip"]
TIER_LABELS = {"premium": "PRO", "vip": "VIP"} 
TIER_SLEEP  = {"premium": 45, "vip": 60}

F = "font-size:18px;line-height:1.8;color:#374151;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"
GOLD   = "#b8974d"
AMBER  = "#f59e0b"
DARK   = "#1a252c"
SLATE  = "#334155"
MUTED  = "#64748b"
BORDER = "#e2e8f0"
BG_LIGHT = "#f8fafc"

PILLAR_PAGES = {
    "Economy":  {"url": SITE_URL + "/category/economy/",  "anchor": "Economy Analysis"},
    "Politics": {"url": SITE_URL + "/category/politics/", "anchor": "Politics & Policy"},
    "Tech":     {"url": SITE_URL + "/category/tech/",     "anchor": "Tech & Innovation"},
    "Health":   {"url": SITE_URL + "/category/health/",   "anchor": "Health & Markets"},
    "Energy":   {"url": SITE_URL + "/category/energy/",   "anchor": "Energy & Resources"},
}
CAT_RELATED = {
    "Economy":  ["Tech", "Energy"],
    "Politics": ["Economy", "Tech"],
    "Tech":     ["Economy", "Health"],
    "Health":   ["Economy", "Politics"],
    "Energy":   ["Economy", "Politics"],
}

VIP_AUTHORS = {
    "Economy":  "Oliver Grant & The Warm Insight Panel",
    "Politics": "Elena Vasquez & The Warm Insight Panel",
    "Tech":     "Marcus Chen & The Warm Insight Panel",
    "Health":   "Sarah Mitchell & The Warm Insight Panel",
    "Energy":   "Alexander Vance & The Warm Insight Panel",
    "The Daily Catalyst": "Arthur Sterling", 
    "Foundation": "Clara Bennett"            
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
            if "404" in err or "not found" in err.lower(): return None
            if "503" in err or "UNAVAILABLE" in err:
                wait = (15 * i) + random.uniform(-2, 5)
                print(f"    ⏳ 503 Overload. Jitter Wait {wait:.1f}s...")
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
        res = re.sub(r"^```(html|xml|text|markdown)?\n", "", res, flags=re.IGNORECASE)
        res = re.sub(r"\n```$", "", res)
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
# 🧠 1. FOUNDATION (SEO 초보자 가이드) DATABASE & PROMPTS
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

FOUNDATION_SYS_INST = """You are a friendly, highly skilled financial educator for Warm Insight.
Your goal is to write a comprehensive, easy-to-understand 'Evergreen SEO Guide' for absolute beginners.
Tone: Encouraging, clear, jargon-free. Use analogies and simple examples.
Your writing must rank well on Google by answering common beginner questions clearly.
Do NOT use overly complex institutional jargon.
You MUST wrap your content EXACTLY in the XML tags requested."""

FOUNDATION_PROMPT = """Write an SEO-optimized beginner's guide on the following topic:
TOPIC: {theme}

OUTPUT FORMAT REQUIREMENT:
You MUST output your response by wrapping your content EXACTLY in the XML tags listed below.

<TITLE>(Write a clear, SEO-friendly title targeting beginners, max 80 chars)</TITLE>
<SEO_KEYWORD>(Write the primary search keyword, e.g., "What is an ETF")</SEO_KEYWORD>
<EXCERPT>(Write a 2-sentence meta description summarizing the guide for Google search results)</EXCERPT>
<DEFINITION>(The 'What is it?' section. Provide a simple, 2-paragraph definition using an easy everyday analogy. e.g., "Think of it like a fruit basket...")</DEFINITION>
<WHY_MATTERS>(The 'Why it matters' section. Explain in 2 paragraphs why a beginner should care about this concept and how it builds wealth.)</WHY_MATTERS>
<HOW_TO_START>(The 'How to apply it' section. Provide 3 simple, actionable steps for a beginner to start using this concept today. Format as a bulleted list or numbered steps within the paragraph.)</HOW_TO_START>
"""

# ═══════════════════════════════════════════════
# 🧠 2. PHILOSOPHY DATABASE & PROMPTS (The Daily Catalyst)
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

<TITLE>(Write a punchy, 3-to-6 word title)</TITLE>
<SEO_KEYWORD>(Write focus keyphrase here)</SEO_KEYWORD>
<ANCHOR>(The Classical Anchor: A one-sentence philosophical principle based on the theme)</ANCHOR>
<REFLECTION>(The Modern Reflection: 3-4 paragraphs explaining how this principle connects to modern reality, financial anxiety, or career stagnation. Criticize passive excuses and logically argue for voluntary fatigue and action.)</REFLECTION>
<CATALYST>(The Daily Catalyst: A single, highly provocative and specific question that requires the reader to write down an actionable answer immediately.)</CATALYST>
"""

# ═══════════════════════════════════════════════
# 🎨 3. TWO-PART PROMPTS (REGULAR NEWS)
# ═══════════════════════════════════════════════
VIP_P1 = """You are Warm Insight's senior analyst. Write PART 1 of a VIP deep-dive on {cat}.
Audience: Sophisticated investors paying premium.
News Context:
{news}
OUTPUT FORMAT REQUIREMENT:
You MUST wrap your content EXACTLY in the XML tags listed below. Do not miss any tags!
<TITLE>(Write Institutional title here, max 90 chars. No tickers)</TITLE>
<SEO_KEYWORD>(Write focus keyphrase here)</SEO_KEYWORD>
<IMPACT>(Write HIGH, MEDIUM, or LOW here)</IMPACT>
<DATA_TABLE>
(Extract 3-4 key market metrics. Format exactly: Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight)
</DATA_TABLE>
<HEATMAP>
(Invent 3-4 sector risk levels (0-100%) based on news. Format exactly: Sector Name | Number)
</HEATMAP>
<EXECUTIVE_SUMMARY>(Write 3 powerful sentences summarizing the systemic shift)</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>(Write 3-4 sentences using a vivid, memorable analogy for non-experts)</PLAIN_ENGLISH>
<HEADLINE>(Write Analytical headline for market drivers here)</HEADLINE>
<MACRO>(Write 2 full paragraphs (150+ words) on Global forces)</MACRO>
<HERD>(Write 1 full paragraph (80+ words) on Cognitive bias and retail panic)</HERD>
<CONTRARIAN>(Write 1 full paragraph (80+ words) on Smart money moves)</CONTRARIAN>
<QUICK_FLOW>(Write Chain of events with arrows ➡️ 5-6 steps)</QUICK_FLOW>"""

VIP_P2 = """You are Warm Insight's senior analyst. Write PART 2 of the VIP strategy for {cat}.
Context from Part 1:
{ctx}
OUTPUT FORMAT REQUIREMENT:
You MUST wrap your content EXACTLY in the XML tags listed below.
<BULL_CASE>(Write Bullish scenario. Full paragraph 80+ words)</BULL_CASE>
<BEAR_CASE>(Write Bearish scenario. Full paragraph 80+ words)</BEAR_CASE>
<VIP_T1>(Write a full paragraph explaining the current market sentiment balance: Fear vs Greed)</VIP_T1>
<VIP_T2>(Write a full paragraph on how to deploy capital now, mentioning specific ETF sectors)</VIP_T2>
<VIP_T3>(Write a full paragraph comparing US vs International exposure)</VIP_T3>
<VIP_T4>(Write a full paragraph on DCA and risk management)</VIP_T4>
<VIP_DO>(Write 2 specific actions with ETF sectors and triggers)</VIP_DO>
<VIP_DONT>(Write 1 critical mistake to avoid)</VIP_DONT>
<TAKEAWAY>(Write One calming, profound insight)</TAKEAWAY>
<PS>(Write Historical perspective in 2-3 sentences)</PS>"""

PROMPT_PREMIUM = """You are Warm Insight's senior analyst. Write a PRO newsletter on {cat} for an intermediate audience. Total length should be 600-800 words.
News Context:
{news}
OUTPUT FORMAT REQUIREMENT:
You MUST wrap your content EXACTLY in the XML tags listed below.
<TITLE>(Write Compelling headline here, max 80 chars. No tickers)</TITLE>
<EXCERPT>(Write 2 sentence SEO summary here)</EXCERPT>
<SEO_KEYWORD>(Write focus keyphrase here)</SEO_KEYWORD>
<IMPACT>(Write HIGH, MEDIUM, or LOW here)</IMPACT>
<DATA_TABLE>
(Extract 3-4 key market metrics. Format exactly: Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight)
</DATA_TABLE>
<EXECUTIVE_SUMMARY>(Write 3 sentences capturing the core thesis)</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>(Write 3-4 sentences using a vivid, relatable analogy)</PLAIN_ENGLISH>
<HEADLINE>(Write Analytical headline for drivers here)</HEADLINE>
<DEPTH>(Write 3-4 sentences on deeper structural pattern, followed by 2-3 sentences on Herd Trap)</DEPTH>
<QUICK_FLOW>(Write Chain of events with arrows ➡️)</QUICK_FLOW>
<BULL_CASE>(Write 3-4 sentences optimistic outlook)</BULL_CASE>
<BEAR_CASE>(Write 3-4 sentences pessimistic outlook)</BEAR_CASE>
<QUICK_HITS>
(Write 3 bullet points of other relevant news. 1 sentence per line)
</QUICK_HITS>
<PRO_INSIGHT>(Write 1-2 paragraphs cross-sector connection and second-order thinking. Name sectors)</PRO_INSIGHT>
<PRO_DO>(Write 1 specific action with reasoning)</PRO_DO>
<PRO_DONT>(Write 1 specific mistake to avoid)</PRO_DONT>
<TAKEAWAY>(Write The bottom line insight here)</TAKEAWAY>
<PS>(Write One-line veteran advice here)</PS>"""

# ═══════════════════════════════════════════════
# 📊 VISUAL DATA BUILDERS & HTML
# ═══════════════════════════════════════════════
def _build_data_table(raw_data, title="Market Data Overview"):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""
    
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
    items = "".join(f'<li style="margin-bottom:12px; color:{SLATE};">{l.replace("-", "").replace("*", "").strip()}</li>' for l in lines[:3])
    return f"""
    <div style="background:#f1f5f9; border:1px solid {BORDER}; border-radius:8px; padding:25px; margin:35px 0;">
        <h3 style="margin-top:0; font-size:20px; color:{DARK}; text-transform:uppercase; letter-spacing:1px;">⚡ Quick Hits</h3>
        <ul style="{F} margin:0; padding-left:20px;">{items}</ul>
    </div>
    """

def _build_pie_chart(s, b, c, accent):
    circ = 565.49
    sd, bd, cd = circ*s/100, circ*b/100, circ*c/100
    pie = f'<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;"><circle cx="100" cy="100" r="90" fill="none" stroke="{accent}" stroke-width="30" stroke-dasharray="{sd} {circ}" stroke-dashoffset="0"/><circle cx="100" cy="100" r="90" fill="none" stroke="#64748b" stroke-width="30" stroke-dasharray="{bd} {circ}" stroke-dashoffset="-{sd}"/><circle cx="100" cy="100" r="90" fill="none" stroke="#b8974d" stroke-width="30" stroke-dasharray="{cd} {circ}" stroke-dashoffset="-{sd+bd}"/><text x="100" y="95" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">{s}/{b}/{c}</text><text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>'
    pie += f'<div style="display:flex;justify-content:center;gap:20px;"><span style="color:{accent};font-weight:bold;">● Stocks {s}%</span><span style="color:#64748b;font-weight:bold;">● Safe {b}%</span><span style="color:#b8974d;font-weight:bold;">● Cash {c}%</span></div>'
    return pie

# ═══════════════════════════════════════════════
# 📎 ENGAGEMENT & FOOTER BUILDERS
# ═══════════════════════════════════════════════
SOCIAL_LINKS = {
    "youtube": "https://www.youtube.com/@WarmInsightyou",
    # "x": "https://x.com/warminsight", # X(트위터) 임시 비활성화
}

def _build_upgrade_cta():
    return f"""
    <div style="text-align:center; margin:45px 0;">
        <a href="{SITE_URL}/warm-insight-vip-membership/" style="display:inline-block; background:{GOLD}; color:#fff; padding:16px 40px; border-radius:10px; font-size:18px; font-weight:bold; text-decoration:none; letter-spacing:0.5px;">
            🔒 Want institutional analysis? <strong>Upgrade to VIP</strong>
        </a>
    </div>
    """

def _build_social_share(title, slug):
    si = ""
    if SOCIAL_LINKS.get("youtube"):
        si += f'<a href="{SOCIAL_LINKS["youtube"]}" target="_blank" style="display:inline-block; background:#FF0000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">▶ YouTube</a>'
    if SOCIAL_LINKS.get("x"):
        si += f'<a href="{SOCIAL_LINKS["x"]}" target="_blank" style="display:inline-block; background:#000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">𝕏 Follow</a>'
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
    if SOCIAL_LINKS.get("x"):
        si += f'<a href="{SOCIAL_LINKS["x"]}" target="_blank" style="display:inline-block; background:#000; color:#fff; padding:8px 16px; border-radius:20px; font-size:13px; font-weight:bold; text-decoration:none; margin:0 4px;">𝕏 Follow</a>'
    return f"""
    <div style="background:{DARK}; padding:35px; border-radius:10px; margin-top:30px;">
        <p style="font-size:24px; font-weight:bold; color:{GOLD}; margin:0 0 12px; text-align:center;">Warm Insight</p>
        <p style="font-size:14px; color:#94a3b8; text-align:center; margin:0 0 16px;">AI-Driven Global Market Analysis</p>
        <div style="text-align:center; margin-bottom:16px;">{si}</div>
        <div style="text-align:center; margin-bottom:16px; font-size:13px;">
            <a href="{SITE_URL}/about-us/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">About</a>
            <a href="{SITE_URL}/privacy-policy/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">Privacy</a>
            <a href="{SITE_URL}/terms/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">Terms</a>
            <a href="{SITE_URL}/warm-insight-vip-membership/" style="color:#cbd5e1; text-decoration:none; margin:0 8px;">VIP</a>
        </div>
        <p style="font-size:13px; color:#64748b; margin:0; text-align:center;">
            All analysis is for informational purposes only. Not financial advice.<br>
            &copy; 2026 Warm Insight. All rights reserved.
        </p>
    </div>
    """

def _build_internal_links(cat):
    if cat in ["The Daily Catalyst", "Foundation"]: return ""
    pillar = PILLAR_PAGES.get(cat, PILLAR_PAGES["Economy"])
    related = CAT_RELATED.get(cat, ["Economy", "Tech"])
    html = f"""
    <div style="margin:35px 0; padding:20px 24px; background:{BG_LIGHT}; border-left:4px solid {GOLD}; border-radius:0 10px 10px 0;">
        <p style="margin:0 0 12px; font-size:16px; font-weight:700; color:{DARK};">Explore More from Warm Insight</p>
        <p style="margin:0 0 8px;"><a href="{pillar['url']}" style="color:{GOLD}; text-decoration:underline; font-weight:600;">{pillar['anchor']}</a></p>
    """
    for rc in related[:2]:
        rp = PILLAR_PAGES.get(rc)
        if rp:
            html += f'        <p style="margin:0 0 8px;"><a href="{rp["url"]}" style="color:{MUTED}; text-decoration:underline;">{rc} Analysis</a></p>\n'
    html += "    </div>"
    return html

def _build_author_bio(cat):
    author = VIP_AUTHORS.get(cat, "The Warm Insight Panel")
    first_name = author.split("&")[0].strip().split()[-1]
    return f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:10px; padding:24px; margin:35px 0; display:flex; gap:20px; align-items:center;">
        <div style="min-width:56px; height:56px; border-radius:50%; background:{GOLD}; display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:700; color:#fff;">
            {first_name[0]}
        </div>
        <div>
            <p style="font-size:17px; font-weight:700; color:{DARK}; margin:0 0 6px;">{author}</p>
            <p style="font-size:14px; color:{MUTED}; margin:0; line-height:1.6;">
                Senior analyst at Warm Insight with deep expertise in global macro-trends, geopolitics, and asset strategy. 
                Our insights combine analytical intelligence for everyday investors.
            </p>
        </div>
    </div>
    """

# ═══════════════════════════════════════════════
# 🎨 1. HTML BUILDER (FOUNDATION / SEO)
# ═══════════════════════════════════════════════
def build_foundation_html(raw, author, tf, title):
    html = f"<div style=\"{F}\">\n"
    
    html += f"""
    <div style="border-top:4px solid #10b981; border-bottom:1px solid {BORDER}; padding:16px 0; margin-bottom:35px;">
        <p style="margin:0; font-size:15px; color:{MUTED};">
            <strong style="color:{DARK};">{author}</strong> &nbsp;|&nbsp; {tf}
            <span style="background:#10b981; color:#fff; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">BEGINNER'S GUIDE</span>
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
    
    slug = make_slug(xtag(raw, "SEO_KEYWORD"), title, "foundation")
    html += _build_social_share(title, slug)
    html += _build_branded_footer()
    
    html += f"""
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: Educational content only.
    </p>
    </div>
    """
    return sanitize(html)

# ═══════════════════════════════════════════════
# 🎨 2. HTML BUILDER (PHILOSOPHY 3-PART STRUCTURE)
# ═══════════════════════════════════════════════
def build_philosophy_html(raw, author, tf, title):
    html = f"<div style=\"{F}\">\n"
    
    html += f"""
    <div style="border-top:4px solid {GOLD}; border-bottom:1px solid {BORDER}; padding:16px 0; margin-bottom:35px;">
        <p style="margin:0; font-size:15px; color:{MUTED};">
            <strong style="color:{DARK};">{author}</strong> &nbsp;|&nbsp; {tf}
            <span style="background:{DARK}; color:{GOLD}; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">DAILY INSIGHT</span>
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
    
    html += f"""
    <div style="background:#fefce8; border:2px solid #fde047; padding:35px; border-radius:12px; margin:50px 0; text-align:center; box-shadow:0 10px 15px -3px rgba(0, 0, 0, 0.05);">
        <p style="font-size:14px; font-weight:800; color:#b45309; text-transform:uppercase; letter-spacing:2px; margin:0 0 15px;">⚡ The Daily Catalyst</p>
        <p style="font-size:22px; font-weight:700; color:#92400e; margin:0 0 20px; line-height:1.4;">
            {xtag(raw, "CATALYST")}
        </p>
        <p style="font-size:15px; color:#b45309; margin:0; font-style:italic;">
            Don't just read. Take out a pen and write your answer now.
        </p>
    </div>
    """
    
    slug = make_slug(xtag(raw, "SEO_KEYWORD"), title, "catalyst")
    html += _build_social_share(title, slug)
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
    
    badge = "VIP EXCLUSIVE" if tier == "vip" else "PRO EXCLUSIVE"
    badge_bg = GOLD if tier == "vip" else "#3b82f6"
    
    html += f"""
    <div style="border-top:4px solid {badge_bg}; border-bottom:1px solid {BORDER}; padding:16px 0; margin-bottom:35px;">
        <p style="margin:0; font-size:15px; color:{MUTED};">
            <strong style="color:{DARK};">{author}</strong> &nbsp;|&nbsp; {tf}
            <span style="background:{badge_bg}; color:#fff; padding:4px 12px; border-radius:4px; font-size:12px; font-weight:800; letter-spacing:1px; margin-left:10px;">{badge}</span>
        </p>
    </div>
    """
    
    if tier == "vip":
        html += f'<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; padding-bottom:10px; display:inline-block;">Executive Summary</h2>'
        html += f'<p style="font-size:19px; font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>'
        
        html += _build_data_table(xtag(raw, "DATA_TABLE"), "Institutional Market Dashboard")
        html += _build_progress_bars(xtag(raw, "HEATMAP"), "Systemic Risk Heatmap")
        
        html += f"""
        <div style="background:#faf5ff; border-left:5px solid #8b5cf6; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;">
            <p style="font-size:20px; font-weight:800; color:#4c1d95; margin:0 0 12px;">💡 Viral Social Insights</p>
            <p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p>
        </div>
        """
        
        html += f'<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; padding-bottom:10px; display:inline-block; margin-top:30px;">Market Drivers & Deep Flow</h2>'
        html += f'<h3 style="font-size:24px; color:{DARK}; margin-top:20px;">{xtag(raw, "HEADLINE")}</h3>'
        
        html += f"""
        <div style="background:#fff; border:1px solid {BORDER}; border-left:5px solid {badge_bg}; padding:30px; border-radius:8px; margin:30px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
            <p><strong>🧐 MACRO:</strong> {xtag(raw, "MACRO")}</p>
            <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
            <p><strong>🐑 HERD:</strong> {xtag(raw, "HERD")}</p>
            <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
            <p><strong>🦅 CONTRARIAN:</strong> {xtag(raw, "CONTRARIAN")}</p>
        </div>
        """
        
        html += f"""
        <div style="background:#fffbeb; border:1px solid #fde68a; border-left:5px solid {AMBER}; padding:25px; margin:40px 0; border-radius:0 8px 8px 0;">
            <strong style="color:#92400e; font-size:20px;">🔗 Institutional Flow:</strong><br>
            <span style="font-weight:bold; font-size:19px; color:{DARK}; display:inline-block; margin-top:12px;">{xtag(raw, "QUICK_FLOW")}</span>
        </div>
        """

        html += f"""
        <div style="display:flex; flex-wrap:wrap; gap:20px; margin:40px 0;">
            <div style="flex:1; min-width:250px; background:#ecfdf5; border:2px solid #10b981; border-radius:8px; padding:25px;">
                <h4 style="margin-top:0; font-size:22px; color:#065f46;">🐂 Institutional Bull</h4>
                <p style="margin:0; color:#064e3b;">{xtag(raw, "BULL_CASE")}</p>
            </div>
            <div style="flex:1; min-width:250px; background:#fef2f2; border:2px solid #ef4444; border-radius:8px; padding:25px;">
                <h4 style="margin-top:0; font-size:22px; color:#991b1b;">🐻 Institutional Bear</h4>
                <p style="margin:0; color:#7f1d1d;">{xtag(raw, "BEAR_CASE")}</p>
            </div>
        </div>
        """

        al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
        pie = _build_pie_chart(al["s"], al["b"], al["c"], GOLD)
        
        html += f'<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid {GOLD}; padding-bottom:10px; display:inline-block; margin-top:30px;">The Titan\'s Playbook</h2>'
        html += f"""
        <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; padding:30px; border-radius:8px; margin-bottom:25px;">
            <h3 style="margin-top:0; font-size:22px; color:{DARK};">1. The Generational Bargain</h3>
            <p>{xtag(raw, "VIP_T1")}</p>
        </div>
        <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; padding:30px; border-radius:8px; margin-bottom:25px;">
            <h3 style="margin-top:0; font-size:22px; color:{DARK};">2. Asset Allocation Seesaw</h3>
            {pie}
            <p style="margin-top:20px;">{xtag(raw, "VIP_T2")}</p>
        </div>
        <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; padding:30px; border-radius:8px; margin-bottom:25px;">
            <h3 style="margin-top:0; font-size:22px; color:{DARK};">3. The Global Shield</h3>
            <p>{xtag(raw, "VIP_T3")}</p>
        </div>
        <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; padding:30px; border-radius:8px; margin-bottom:40px;">
            <h3 style="margin-top:0; font-size:22px; color:{DARK};">4. Survival Mechanics</h3>
            <p>{xtag(raw, "VIP_T4")}</p>
        </div>
        """
        
        html += f"""
        <div style="background:#1e293b; padding:40px; border-radius:12px; margin:45px 0;">
            <h3 style="color:{GOLD}; margin-top:0; font-size:26px; border-bottom:2px solid #475569; padding-bottom:15px;">✅ VIP Action Plan</h3>
            <div style="background:#ecfdf5; border:2px solid #10b981; padding:20px; border-radius:8px; margin:25px 0 15px;">
                <p style="margin:0; color:#065f46; font-size:18px;"><strong>🟢 DO (Action):</strong> {xtag(raw, "VIP_DO")}</p>
            </div>
            <div style="background:#fef2f2; border:2px solid #ef4444; padding:20px; border-radius:8px;">
                <p style="margin:0; color:#7f1d1d; font-size:18px;"><strong>🔴 DON'T (Avoid):</strong> {xtag(raw, "VIP_DONT")}</p>
            </div>
        </div>
        """

    else: 
        html += f'<h2 style="font-size:28px; color:{DARK}; border-bottom:3px solid #3b82f6; padding-bottom:10px; display:inline-block;">Executive Summary</h2>'
        html += f'<p style="font-size:19px; font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>'
        
        html += _build_data_table(xtag(raw, "DATA_TABLE"), "Market Movers Dashboard")
        
        html += f"""
        <div style="background:#f4f4f5; border-left:5px solid #8b5cf6; padding:25px; border-radius:8px; margin:40px 0;">
            <h3 style="margin-top:0; font-size:20px; color:{DARK}; margin-bottom:12px;">📱 Viral Social Insights</h3>
            <p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p>
        </div>
        """
        
        html += f'<h2 style="font-family:Georgia,serif; font-size:28px; color:{DARK}; margin:45px 0 20px;">Market Drivers & Insights</h2>'
        html += f'<h3 style="font-size:24px; color:{DARK}; margin-bottom:15px;">{xtag(raw, "HEADLINE")}</h3>'
        html += f'<p>{xtag(raw, "DEPTH")}</p>'
        
        html += f"""
        <div style="background:#fffbeb; border:1px solid #fde68a; padding:25px; border-radius:8px; margin:40px 0;">
            <strong style="font-size:18px; color:#d97706; text-transform:uppercase;">💡 Quick Flow:</strong>
            <p style="font-size:19px; font-weight:bold; color:{DARK}; margin:12px 0 0;">{xtag(raw, "QUICK_FLOW")}</p>
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
        html += _build_quick_hits(xtag(raw, "QUICK_HITS"))
        
        html += f"""
        <div style="background:#ffffff; border:2px solid #3b82f6; padding:30px; border-radius:8px; margin:45px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top:0; color:#1e40af; font-size:24px;">💎 Pro-Only Insight</h3>
            <p style="margin:0;">{xtag(raw, "PRO_INSIGHT")}</p>
        </div>
        <div style="background:#ecfdf5; border:2px solid #10b981; padding:25px; border-radius:8px; margin-bottom:15px;">
            <p style="margin:0; color:#065f46; font-size:18px;"><strong>🟢 DO (Action):</strong> {xtag(raw, "PRO_DO")}</p>
        </div>
        <div style="background:#fef2f2; border:2px solid #ef4444; padding:25px; border-radius:8px; margin-bottom:40px;">
            <p style="margin:0; color:#7f1d1d; font-size:18px;"><strong>🔴 DON'T (Avoid):</strong> {xtag(raw, "PRO_DONT")}</p>
        </div>
        """
    
    if tier == "premium":
        html += _build_upgrade_cta()

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

    html += _build_social_share(title, slug)
    html += _build_branded_footer()
    html += _build_internal_links(cat)
    html += _build_author_bio(cat)

    html += f"""
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: This article is for informational purposes only. All decisions are your own.
    </p>
    </div>
    """
    return sanitize(html)

# ═══════════════════════════════════════════════════════════════
# 🤖 🚨 밀크로드 스타일 고퀄리티 썸네일 엔진 
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
        "Foundation": {"bg1": "#047857", "bg2": "#10b981", "acc": "#fde047"} 
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
            draw.line([(cx_p-100*S, cy_p+100*S), (cx_p-50*S, cy_p+100*S), (cx_p-25*S, cy_p+50*S), (cx_p+25*S, cy_p+150*S), (cx_p+50*S, cy_p+100*S), (cx_p+100*S, cy_p+100*S)], fill="#ffffff", width=6*S)
        elif cat == "Energy":
            draw.polygon([(cx_p+30*S, cy_p-90*S), (cx_p-50*S, cy_p+10*S), (cx_p+10*S, cy_p+10*S), (cx_p-30*S, cy_p+90*S), (cx_p+50*S, cy_p-10*S), (cx_p-10*S, cy_p-10*S)], fill="#fde047")
        elif cat == "The Daily Catalyst":
            draw.ellipse([cx_p-50*S, cy_p-70*S, cx_p+50*S, cy_p+30*S], fill="#cbd5e1")
            draw.polygon([(cx_p-25*S, cy_p+20*S), (cx_p+25*S, cy_p+20*S), (cx_p+15*S, cy_p+70*S), (cx_p-15*S, cy_p+70*S)], fill="#94a3b8")
            draw.line([(cx_p-30*S, cy_p-100*S), (cx_p-20*S, cy_p-80*S)], fill="#fde047", width=6*S)
            draw.line([(cx_p+30*S, cy_p-100*S), (cx_p+20*S, cy_p-80*S)], fill="#fde047", width=6*S)
            draw.line([(cx_p, cy_p-110*S), (cx_p, cy_p-85*S)], fill="#fde047", width=6*S)
        elif cat == "Foundation":
            draw.rectangle([cx_p-70*S, cy_p-50*S, cx_p, cy_p+70*S], fill="#6ee7b7", outline="#ffffff", width=6*S)
            draw.rectangle([cx_p, cy_p-50*S, cx_p+70*S, cy_p+70*S], fill="#34d399", outline="#ffffff", width=6*S)
            draw.line([(cx_p-50*S, cy_p-20*S), (cx_p-20*S, cy_p-20*S)], fill="#ffffff", width=5*S)
            draw.line([(cx_p+20*S, cy_p-20*S), (cx_p+50*S, cy_p-20*S)], fill="#ffffff", width=5*S)
            draw.line([(cx_p-50*S, cy_p+10*S), (cx_p-20*S, cy_p+10*S)], fill="#ffffff", width=5*S)

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

    try: cat_w = draw.textlength(cat.upper(), font=fb)
    except: cat_w = len(cat) * 15 * S
    
    bx = 40 * S + date_w + 30 * S
    draw.rounded_rectangle(
        [(bx, 36 * S), (bx + cat_w + 60 * S, 86 * S)],
        radius=25 * S, fill="#ffffff"
    )
    draw.text((bx + 30 * S, 44 * S), cat.upper(), font=fb, fill="#1e293b")

    if cat not in ["Foundation", "The Daily Catalyst"]:
        tl = "VIP" if tier == "vip" else "PRO"
        t_bg = "#b8974d" if tier == "vip" else "#3b82f6" 
        t_tc = "#ffffff"
        
        try: tier_w = draw.textlength(tl, font=f_badge)
        except: tier_w = len(tl) * 18 * S
        
        badge_x = w - 40 * S - tier_w - 40 * S
        draw.rounded_rectangle(
            [(badge_x, 36 * S), (w - 40 * S, 86 * S)],
            radius=25 * S, fill=t_bg
        )
        draw.text((badge_x + 20 * S, 44 * S), tl, font=f_badge, fill=t_tc)

    # 🚨 중복/잘림 문제 완벽 해결: 원본 전체 제목 사용 + 불필요한 Prefix 스마트 제거
    clean_title = _clean_seo_title(title_text).upper()
    # AI가 'Warm Insight:' 혹은 'Warm Insight -'를 붙이면 썸네일에서는 지움
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
# PUBLISHER
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

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, author_name):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat) 
    
    tag_name = "VIP" if tier == "vip" else "Pro"
    tag_id = get_or_create_wp_tag(tag_name)
    
    author_id = get_wp_author_id(author_name)

    if cat in ["Foundation", "The Daily Catalyst"]:
        display_title = title
    elif tier == "vip":
        display_title = f"[VIP] {title}"
    else:
        display_title = f"[Pro] {title}"

    post_data = {
        "title": display_title,
        "content": html,
        "status": "publish",
        "slug": slug,
    }
    
    if author_id: post_data["author"] = author_id
    
    if media_id: post_data["featured_media"] = media_id
    if cat_id: post_data["categories"] = [cat_id]
    if tag_id: post_data["tags"] = [tag_id] 
    
    seo_title = _clean_seo_title(title)
    
    is_premium = "no" if cat == "Foundation" else "yes"
    pms_restrict = "0" if cat == "Foundation" else "1"

    post_data["meta"] = {
        "rank_math_title": (seo_title + " | " + cat + " | Warm Insight")[:60],
        "rank_math_description": ((exc or "")[:120] + f" Insightful {cat.lower()} analysis.")[:155],
        "rank_math_focus_keyword": kw or "",
        "is_premium": is_premium,
        "pms_content_restrict": pms_restrict,
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
            print(f"   ✅ Published: {r.json().get('link')}")
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
    print(f"🚀 Starting v40.18 SEO Foundation Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return
    
    theme = random.choice(FOUNDATION_TOPICS)
    print(f"   💡 Selected Topic: {theme}")
    
    tier = "premium" 
    
    print("    [AI] Calling Foundation Guide Generation...")
    raw = gem_fb(tier, FOUNDATION_PROMPT.replace("{theme}", theme), FOUNDATION_SYS_INST)
    
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "EXCERPT")
        slug = make_slug(kw, title, cat)
        
        author = VIP_AUTHORS.get(cat, "Warm Insight Education Team")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_foundation_html(raw, author, tf, title)
        
        print("    🖌️ Generating Foundation Thumbnail...")
        img_bytes = make_thumbnail(title, cat, tier)
        
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author)

def run_philosophy_pipeline():
    cat = "The Daily Catalyst"
    print(f"🚀 Starting v40.18 Catalyst Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return
    
    theme = random.choice(PHILOSOPHY_TOPICS)
    print(f"   💡 Selected Theme: {theme}")
    
    tier = "premium" 
    
    print("    [AI] Calling Philosophy Generation...")
    raw = gem_fb(tier, PHILOSOPHY_PROMPT.replace("{theme}", theme), PHILOSOPHY_SYS_INST)
    
    if raw:
        title = xtag(raw, "TITLE")
        kw = xtag(raw, "SEO_KEYWORD")
        exc = xtag(raw, "ANCHOR")
        slug = make_slug(kw, title, cat)
        
        author = VIP_AUTHORS.get(cat, "Warm Insight Philosophical Desk")
        tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        html = build_philosophy_html(raw, author, tf, title)
        
        print("    🖌️ Generating Philosophy Thumbnail...")
        img_bytes = make_thumbnail(title, cat, tier)
        
        publish(title, html, exc, kw, cat, slug, tier, img_bytes, author)

def run_news_pipeline():
    cat = CATEGORIES[(datetime.datetime.utcnow().hour // 3) % len(CATEGORIES)]
    print(f"🚀 Starting v40.18 News Pipeline | Category: {cat}")
    if not check_env_vars() or not verify_wp_credentials(): return
    
    all_news = fetch_news_pool(cat)
    total_news = len(all_news)
    print(f"   📥 Fetched {total_news} total news items from RSS.")
    
    if total_news < 2:
        print("   🛑 No news found. Aborting.")
        return
        
    mid = total_news // 2
    news_map = {
        "vip": "\n".join(all_news[:mid]),
        "premium": "\n".join(all_news[mid:])
    }
    
    for tier in TIERS:
        print(f"\n--- Processing {tier.upper()} ---")
        assigned_news = news_map[tier]
        
        if tier == "vip":
            print("    [AI] Calling VIP Part 1...")
            raw1 = gem_fb(tier, VIP_P1.replace("{cat}", cat).replace("{news}", assigned_news))
            if not raw1: continue
            
            print("    [AI] Calling VIP Part 2...")
            ctx = "Title: " + xtag(raw1, "TITLE") + "\nSummary: " + xtag(raw1, "EXECUTIVE_SUMMARY")
            alloc = f"{CAT_ALLOC[cat]['s']}% Stocks, {CAT_ALLOC[cat]['b']}% Safe"
            raw2 = gem_fb(tier, VIP_P2.replace("{cat}", cat).replace("{ctx}", ctx).replace("{alloc}", alloc))
            raw = raw1 + "\n" + raw2
        else:
            print("    [AI] Calling PRO Full Gen...")
            raw = gem_fb(tier, PROMPT_PREMIUM.replace("{cat}", cat).replace("{news}", assigned_news))
        
        if raw:
            title = xtag(raw, "TITLE")
            kw = xtag(raw, "SEO_KEYWORD")
            exc = xtag(raw, "EXECUTIVE_SUMMARY") if tier == "vip" else xtag(raw, "EXCERPT")
            slug = make_slug(kw, title, cat)
            
            author = VIP_AUTHORS.get(cat, "The Warm Insight Panel")
            tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
            
            html = build_html(tier, cat, raw, author, tf, title)
            
            print("    🖌️ Generating Warmy Robot Thumbnail...")
            img_bytes = make_thumbnail(title, cat, tier)
            
            publish(title, html, exc, kw, cat, slug, tier, img_bytes, author)
            time.sleep(TIER_SLEEP[tier])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "philosophy":
            run_philosophy_pipeline()
        elif sys.argv[1] == "foundation":
            run_foundation_pipeline()
    else:
        run_news_pipeline()
