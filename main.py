#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v39 (Warmy Robot Restored + v38 Full Spec)
# v38 대비 변경점 (최소 변경 원칙):
#   1) make_thumbnail() → Warmy 로봇 캐릭터 + 밝은 배경 (4/12 이전 스타일)
#   2) publish() → 타이틀에 [👑 VIP] / [💎 Pro] 접두사 복원
#   3) _clean_seo_title() → 새 접두사 인식 추가
#   ※ 나머지 build_html, 프롬프트, 데이터빌더 등은 v38 원본 그대로 유지
# ═══════════════════════════════════════════════════════════════
import os, sys, traceback, time, random, re, datetime, io, math
import urllib.request
import requests
import feedparser
from PIL import Image, ImageDraw, ImageFont
from google import genai

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
    "Energy":   "Oliver Grant & The Warm Insight Panel",
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
# 🛡️ SYSTEM UTILS & API ENGINE (v38 원본)
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

def call_gemini(client, model, prompt, retries=5):
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt)
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

def gem_fb(tier, prompt):
    client = _get_gemini_client()
    for m in MODEL_PRI.get(tier, FAST_MODELS):
        print(f"    [AI] Trying {m}...")
        r = call_gemini(client, m, prompt)
        if r: return r
    return ""

def xtag(raw, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""

def sanitize(html):
    html = re.sub(r"<script(?!\s+type=['\"]application/ld\+json['\"])[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    return re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.DOTALL)

def make_slug(kw, title, cat):
    base = kw if (kw and len(kw) > 4) else title
    slug = re.sub(r"[^\w\s-]", "", base.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:55]
    return f"{slug}-{datetime.datetime.utcnow().strftime('%m%d%H%M')}"

def _clean_seo_title(title):
    # v39: 새 접두사 패턴도 인식
    for p in ["[👑 VIP] ", "[💎 Pro] ", "[PRO] ", "[VIP] ", "[PRO]", "[VIP]", "[Pro] "]:
        title = title.replace(p, "")
    return title.strip()

# ═══════════════════════════════════════════════
# 📰 NEWS POOLING (v38 원본)
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
# 🎨 TWO-PART PROMPTS (v38 원본 — 1200줄 퀄리티 보장)
# ═══════════════════════════════════════════════
VIP_P1 = """You are Warm Insight's senior analyst. Write PART 1 of a VIP deep-dive on {cat}.
Audience: Sophisticated investors paying premium.
Write REAL, deep analysis paragraphs. Do not use placeholders.

<TITLE>Institutional title, max 90 chars. No tickers in title.</TITLE>
<SEO_KEYWORD>focus keyphrase</SEO_KEYWORD>
<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>

<DATA_TABLE>
Extract 3-4 key market metrics from the news.
Format exactly: Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight
</DATA_TABLE>

<HEATMAP>
Invent 3-4 sector risk levels (0-100%) based on the news.
Format exactly: Sector Name | Number
</HEATMAP>

<EXECUTIVE_SUMMARY>3 powerful sentences summarizing the systemic shift.</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>3-4 sentences using a vivid, memorable analogy for non-experts.</PLAIN_ENGLISH>
<HEADLINE>Analytical headline for market drivers</HEADLINE>

<MACRO><strong>🧐 MACRO:</strong> Systems view. Global forces. Write 2 full, rich paragraphs (150+ words).</MACRO>
<HERD><strong>🐑 HERD:</strong> Cognitive bias and retail panic. Write 1 full paragraph (80+ words).</HERD>
<CONTRARIAN><strong>🦅 CONTRARIAN:</strong> 2nd-order thinking. Smart money moves. Write 1 full paragraph (80+ words).</CONTRARIAN>
<QUICK_FLOW>Chain of events with arrows ➡️ (5-6 steps)</QUICK_FLOW>

News Context:
{news}"""

VIP_P2 = """You are Warm Insight's senior analyst. Write PART 2 of the VIP strategy for {cat}.
Write REAL, deep analysis paragraphs. Do not use placeholders.

Context from Part 1:
{ctx}

<BULL_CASE>Bullish scenario. Full paragraph (80+ words).</BULL_CASE>
<BEAR_CASE>Bearish scenario. Full paragraph (80+ words).</BEAR_CASE>

<VIP_T1>1. The Generational Bargain (Fear vs Greed): Explain the current market sentiment balance. Full paragraph.</VIP_T1>
<VIP_T2>2. The {alloc} Seesaw (Asset Allocation): How to deploy capital now. Full paragraph mentioning specific ETF sectors.</VIP_T2>
<VIP_T3>3. The Global Shield: Compare US vs International exposure. Full paragraph.</VIP_T3>
<VIP_T4>4. Survival Mechanics: DCA and risk management. Full paragraph.</VIP_T4>

<VIP_DO>2 specific actions with ETF sectors and triggers.</VIP_DO>
<VIP_DONT>1 critical mistake to avoid.</VIP_DONT>

<TAKEAWAY>One calming, profound insight.</TAKEAWAY>
<PS>Historical perspective in 2-3 sentences.</PS>"""

PROMPT_PREMIUM = """You are Warm Insight's senior analyst. Write a PRO newsletter on {cat} for an intermediate audience.
Write REAL, deep analysis paragraphs. Do not use placeholders. Total length should be 600-800 words.

<TITLE>Compelling headline, max 80 chars. No tickers in title.</TITLE>
<EXCERPT>2 sentence SEO summary.</EXCERPT>
<SEO_KEYWORD>focus keyphrase</SEO_KEYWORD>
<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>

<DATA_TABLE>
Extract 3-4 key market metrics from the news.
Format exactly: Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight
</DATA_TABLE>

<EXECUTIVE_SUMMARY>3 sentences capturing the core thesis.</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>3-4 sentences using a vivid, relatable analogy (e.g., "Think of it like...").</PLAIN_ENGLISH>

<HEADLINE>Analytical headline for drivers</HEADLINE>
<DEPTH><strong>🧐 WHY:</strong> Deeper structural pattern (3-4 sentences).<br><br><strong>🐑 HERD TRAP:</strong> Cognitive bias (2-3 sentences).</DEPTH>
<QUICK_FLOW>Chain of events with arrows ➡️</QUICK_FLOW>

<BULL_CASE>3-4 sentences optimistic outlook.</BULL_CASE>
<BEAR_CASE>3-4 sentences pessimistic outlook.</BEAR_CASE>

<QUICK_HITS>3 bullet points of other relevant news from the context. 1 sentence per line.</QUICK_HITS>

<PRO_INSIGHT><strong>💎 Pro-Only Insight:</strong> 1-2 paragraphs cross-sector connection and second-order thinking. Name sectors.</PRO_INSIGHT>
<PRO_DO>1 specific action with reasoning.</PRO_DO>
<PRO_DONT>1 specific mistake to avoid.</PRO_DONT>

<TAKEAWAY>The bottom line insight.</TAKEAWAY>
<PS>One-line veteran advice.</PS>

News Context:
{news}"""

# ═══════════════════════════════════════════════
# 📊 VISUAL DATA BUILDERS (v38 원본 — 펼친 HTML 구조 유지)
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
# 📎 ENGAGEMENT & FOOTER BUILDERS (v39 추가 — 사진4 퀄리티 복원)
# ═══════════════════════════════════════════════
SOCIAL_LINKS = {
    "youtube": "https://www.youtube.com/@WarmInsightyou",
    "x": "https://x.com/warminsight",
}

def _build_upgrade_cta():
    """PRO 글 하단 VIP 업그레이드 버튼"""
    return f"""
    <div style="text-align:center; margin:45px 0;">
        <a href="{SITE_URL}/warm-insight-vip-membership/" style="display:inline-block; background:{GOLD}; color:#fff; padding:16px 40px; border-radius:10px; font-size:18px; font-weight:bold; text-decoration:none; letter-spacing:0.5px;">
            🔒 Want institutional analysis? <strong>Upgrade to VIP</strong>
        </a>
    </div>
    """

def _build_social_share(title, slug):
    """공유 섹션 (Found this useful?)"""
    url = f"{SITE_URL}/{slug}/"
    et = title.replace(" ", "%20").replace("&", "%26")[:100]
    eu = url.replace(":", "%3A").replace("/", "%2F")
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
    """Warm Insight 브랜드 다크 푸터"""
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
    """Explore More from Warm Insight 내부 링크"""
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
    """저자 바이오 섹션 (아바타 + 이름 + 소개)"""
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
# 🎨 HTML BUILDERS (v38 원본 — 펼친 구조 유지, 압축 금지)
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
            <p>{xtag(raw, "MACRO")}</p>
            <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
            <p>{xtag(raw, "HERD")}</p>
            <hr style="border:0; height:1px; background:{BORDER}; margin:20px 0;">
            <p>{xtag(raw, "CONTRARIAN")}</p>
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
        """
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
    
    # ── PRO 전용: VIP 업그레이드 CTA ──
    if tier == "premium":
        html += _build_upgrade_cta()

    # ── 공통 Footer (v39: 사진4 퀄리티 복원 — 5개 섹션 추가) ──
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

    # ── v39 추가: 사진4에 있었던 engagement 섹션들 ──
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
# 🤖 v39 변경: Warmy 로봇 썸네일 복원 (4/12 이전 작동 버전)
# ═══════════════════════════════════════════════════════════════
def get_font(url, filename):
    if not os.path.exists(filename):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as resp, open(filename, 'wb') as f:
                f.write(resp.read())
        except Exception as e: print(f"Font error: {e}")
    return filename

def make_thumbnail(title_text, cat, tier):
    """
    v39: 4월 12일 이전 작동 확인된 Warmy 로봇 + 밝은 배경 스타일 복원.
    v38의 다크 배경 + Apple 이모지 방식은 폐기.
    """
    W, H, SCALE = 1200, 630, 2
    w, h = W * SCALE, H * SCALE

    # 카테고리별 밝은 배경 + 악센트 색상
    CAT_STYLES = {
        "Economy":  {"bg": "#0ea5e9", "acc": "#fde047"},
        "Politics": {"bg": "#dc2626", "acc": "#fde047"},
        "Tech":     {"bg": "#6366f1", "acc": "#a78bfa"},
        "Health":   {"bg": "#059669", "acc": "#fef08a"},
        "Energy":   {"bg": "#d97706", "acc": "#fef3c7"},
    }
    style = CAT_STYLES.get(cat, CAT_STYLES["Economy"])

    img = Image.new("RGBA", (w, h), style["bg"])
    draw = ImageDraw.Draw(img)

    # 폰트 다운로드
    ft_path = get_font(
        "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
        "fonts/BebasNeue-Regular.ttf"
    )

    def lf(p, s):
        try: return ImageFont.truetype(p, s * SCALE)
        except: return ImageFont.load_default()

    ft = lf(ft_path, 85)   # 타이틀
    fs = lf(ft_path, 34)   # 푸터
    fb = lf(ft_path, 30)   # 뱃지

    # ── 1. 배경 차트 라인 (VIP: 빨강 하락선 / PRO: 초록 상승선) ──
    if tier == "vip":
        ex, ey = w * 0.75, h * 0.55
        draw.line([(w * 0.4, h * 0.35), (ex, ey)], fill="#ef4444", width=8 * SCALE)
        draw.polygon([(ex, ey), (ex - 25 * SCALE, ey - 5 * SCALE), (ex - 5 * SCALE, ey - 25 * SCALE)], fill="#ef4444")
        # 경고 삼각형
        tx, ty = w * 0.45, h * 0.25
        draw.polygon([(tx, ty - 30 * SCALE), (tx - 30 * SCALE, ty + 20 * SCALE), (tx + 30 * SCALE, ty + 20 * SCALE)], fill="#fde047")
        draw.line([(tx, ty - 10 * SCALE), (tx, ty + 5 * SCALE)], fill="#1e293b", width=6 * SCALE)
        draw.ellipse([(tx - 4 * SCALE, ty + 10 * SCALE), (tx + 4 * SCALE, ty + 18 * SCALE)], fill="#1e293b")
    else:
        ex, ey = w * 0.8, h * 0.35
        draw.line([(w * 0.4, h * 0.45), (w * 0.6, h * 0.4), (ex, ey)], fill="#4ade80", width=6 * SCALE)
        draw.polygon([(ex, ey), (ex - 25 * SCALE, ey + 5 * SCALE), (ex - 5 * SCALE, ey + 25 * SCALE)], fill="#4ade80")
        # 지구본
        gx, gy = w * 0.65, h * 0.2
        gr = 35 * SCALE
        draw.ellipse([(gx - gr, gy - gr), (gx + gr, gy + gr)], outline="#ffffff60", width=4 * SCALE)
        draw.ellipse([(gx - gr / 3, gy - gr), (gx + gr / 3, gy + gr)], outline="#ffffff60", width=4 * SCALE)
        draw.line([(gx - gr, gy), (gx + gr, gy)], fill="#ffffff60", width=4 * SCALE)
        draw.line([(gx, gy - gr), (gx, gy + gr)], fill="#ffffff60", width=4 * SCALE)

    # ── 2. 🤖 Warmy 로봇 캐릭터 ──
    cx = w * 0.85
    cy = h * 0.7
    S = SCALE

    # 다리
    draw.ellipse([cx - 45 * S, cy + 60 * S, cx - 15 * S, cy + 90 * S], fill="#047857")
    draw.ellipse([cx + 15 * S, cy + 60 * S, cx + 45 * S, cy + 90 * S], fill="#047857")
    # 팔
    draw.rounded_rectangle([cx - 85 * S, cy - 10 * S, cx - 50 * S, cy + 15 * S], radius=12 * S, fill="#10b981")
    draw.rounded_rectangle([cx + 50 * S, cy - 30 * S, cx + 85 * S, cy - 5 * S], radius=12 * S, fill="#10b981")
    # 몸통
    draw.rounded_rectangle([cx - 50 * S, cy - 70 * S, cx + 50 * S, cy + 70 * S], radius=25 * S, fill="#10b981")
    # 눈 (흰자 + 동공)
    draw.ellipse([cx - 25 * S, cy - 30 * S, cx - 5 * S, cy - 10 * S], fill="#ffffff")
    draw.ellipse([cx + 5 * S, cy - 30 * S, cx + 25 * S, cy - 10 * S], fill="#ffffff")
    draw.ellipse([cx - 18 * S, cy - 22 * S, cx - 10 * S, cy - 14 * S], fill="#1e293b")
    draw.ellipse([cx + 12 * S, cy - 22 * S, cx + 20 * S, cy - 14 * S], fill="#1e293b")
    # 볼터치
    draw.ellipse([cx - 40 * S, cy + 5 * S, cx - 25 * S, cy + 20 * S], fill="#f472b6")
    draw.ellipse([cx + 25 * S, cy + 5 * S, cx + 40 * S, cy + 20 * S], fill="#f472b6")
    # 입
    draw.rounded_rectangle([cx - 25 * S, cy + 30 * S, cx + 25 * S, cy + 50 * S], radius=8 * S, fill="#ffffff")

    # ── 3. 카테고리별 악세사리 ──
    if cat == "Economy":
        # 빨간 넥타이
        draw.polygon([
            (cx - 5 * S, cy + 55 * S), (cx + 5 * S, cy + 55 * S),
            (cx + 8 * S, cy + 80 * S), (cx, cy + 90 * S), (cx - 8 * S, cy + 80 * S)
        ], fill="#ef4444")
    elif cat == "Politics":
        # 뿔테 안경
        draw.rectangle([cx - 35 * S, cy - 35 * S, cx + 35 * S, cy - 5 * S], outline="#1e293b", width=4 * S)
        draw.line([(cx - 5 * S, cy - 20 * S), (cx + 5 * S, cy - 20 * S)], fill="#1e293b", width=4 * S)
    elif cat == "Tech":
        # 파란 안테나
        draw.line([(cx, cy - 70 * S), (cx, cy - 110 * S)], fill="#94a3b8", width=6 * S)
        draw.ellipse([(cx - 12 * S, cy - 125 * S), (cx + 12 * S, cy - 100 * S)], fill="#60a5fa")
    elif cat == "Health":
        # 간호사/의사 모자
        draw.rounded_rectangle([cx - 35 * S, cy - 95 * S, cx + 35 * S, cy - 65 * S], radius=5 * S, fill="#ffffff")
        draw.rectangle([cx - 5 * S, cy - 90 * S, cx + 5 * S, cy - 70 * S], fill="#ef4444")
        draw.rectangle([cx - 15 * S, cy - 85 * S, cx + 15 * S, cy - 75 * S], fill="#ef4444")
    elif cat == "Energy":
        # 노란 안전모
        draw.chord([cx - 55 * S, cy - 110 * S, cx + 55 * S, cy - 30 * S], start=180, end=0, fill="#f59e0b")
        draw.line([(cx - 65 * S, cy - 70 * S), (cx + 65 * S, cy - 70 * S)], fill="#f59e0b", width=8 * S)

    # ── 4. VIP 전용 왕관 ──
    if tier == "vip":
        cx_c = cx + 25 * S
        cy_c = cy - 65 * S
        draw.polygon([
            (cx_c - 15 * S, cy_c), (cx_c - 25 * S, cy_c - 30 * S),
            (cx_c, cy_c - 15 * S), (cx_c + 15 * S, cy_c - 35 * S),
            (cx_c + 20 * S, cy_c - 10 * S), (cx_c + 35 * S, cy_c - 25 * S),
            (cx_c + 25 * S, cy_c + 5 * S)
        ], fill="#fde047")

    # ── 5. 하단 반투명 바 ──
    draw.rectangle([(0, h - 80 * SCALE), (w, h)], fill="#00000040")

    # ── 6. 상단 뱃지 (카테고리 + 날짜 + 티어) ──
    date_badge = datetime.datetime.utcnow().strftime("%Y.%m.%d")
    draw.text((40 * SCALE, 44 * SCALE), date_badge, font=fb, fill="#ffffff")
    date_w = draw.textlength(date_badge, font=fb)

    # 카테고리 뱃지 (둥근 흰색 캡슐)
    cat_w = draw.textlength(cat.upper(), font=fb)
    bx = 40 * SCALE + date_w + 30 * SCALE
    draw.rounded_rectangle(
        [(bx, 36 * SCALE), (bx + cat_w + 60 * SCALE, 86 * SCALE)],
        radius=25 * SCALE, fill="#ffffff"
    )
    draw.text((bx + 30 * SCALE, 44 * SCALE), cat.upper(), font=fb, fill="#1e293b")

    # VIP/PRO 뱃지 (우상단)
    tl = "VIP" if tier == "vip" else "PRO"
    t_bg = "#b8974d" if tier == "vip" else "#ffffff"
    t_tc = "#ffffff" if tier == "vip" else "#1e293b"
    tier_w = draw.textlength(tl, font=fb)
    draw.rounded_rectangle(
        [(w - 40 * SCALE - tier_w - 60 * SCALE, 36 * SCALE), (w - 40 * SCALE, 86 * SCALE)],
        radius=25 * SCALE, fill=t_bg
    )
    draw.text((w - 40 * SCALE - tier_w - 30 * SCALE, 44 * SCALE), tl, font=fb, fill=t_tc)

    # ── 7. 타이틀 텍스트 (최대 3줄) ──
    clean_title = _clean_seo_title(title_text).upper().split(':')[0]
    words = clean_title.split()
    lines, line = [], []
    mw = w - 400 * SCALE  # 캐릭터 침범 방지

    for word in words:
        t = " ".join(line + [word])
        try:
            tw2 = draw.textlength(t, font=ft)
        except:
            tw2 = len(t) * 40 * SCALE
        if tw2 < mw:
            line.append(word)
        else:
            if line: lines.append(" ".join(line))
            line = [word]
    if line: lines.append(" ".join(line))

    y = 180 * SCALE
    for i, ln in enumerate(lines[:3]):
        # 2번째 줄은 카테고리 악센트 색상으로 강조
        color = style["acc"] if i == 1 else "#ffffff"
        draw.text((40 * SCALE, y), ln, font=ft, fill=color)
        try:
            bb = draw.textbbox((0, 0), ln, font=ft)
            y += (bb[3] - bb[1]) + 15 * SCALE
        except:
            y += 100 * SCALE

    # ── 8. 하단 푸터 ──
    draw.text((40 * SCALE, h - 60 * SCALE), "WARM INSIGHT", font=fs, fill="#ffffff")
    tagline = "AI-Driven Global Market Analysis"
    tw_t = draw.textlength(tagline, font=fs)
    draw.text((w - 40 * SCALE - tw_t, h - 60 * SCALE), tagline, font=fs, fill="#ffffff")

    # ── 최종 변환 ──
    img = img.convert("RGB")
    img = img.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

# ═══════════════════════════════════════════════
# PUBLISHER (v39 변경: 타이틀 접두사 복원)
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
    slug = cat_name.lower()
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
    slug = tag_name.lower()
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/tags?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0:
            return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/tags", json={"name": tag_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201):
            return r2.json()["id"]
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat) 
    tag_name = "VIP" if tier == "vip" else "Pro"
    tag_id = get_or_create_wp_tag(tag_name)

    # ✅ v39: 타이틀에 티어 접두사 복원 (4/12까지 작동했던 방식)
    prefix = "👑 VIP" if tier == "vip" else "💎 Pro"
    display_title = f"[{prefix}] {title}"

    post_data = {
        "title": display_title,
        "content": html,
        "status": "publish",
        "slug": slug,
    }
    if media_id: post_data["featured_media"] = media_id
    if cat_id: post_data["categories"] = [cat_id]
    if tag_id: post_data["tags"] = [tag_id] 
    
    seo_title = _clean_seo_title(title)
    post_data["meta"] = {
        "rank_math_title": (seo_title + " | " + cat + " | Warm Insight")[:60],
        "rank_math_description": ((exc or "")[:120] + f" Expert {cat.lower()} analysis.")[:155],
        "rank_math_focus_keyword": kw or "",
        "is_premium": "yes",
        "pms_content_restrict": "1",
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
# 🔄 PIPELINE (v38 원본)
# ═══════════════════════════════════════════════
def run_pipeline():
    cat = CATEGORIES[(datetime.datetime.utcnow().hour // 3) % len(CATEGORIES)]
    print(f"🚀 Starting v39 Pipeline (Warmy Robot + v38 Full Spec) | Category: {cat}")
    
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
            
            publish(title, html, exc, kw, cat, slug, tier, img_bytes)
            time.sleep(TIER_SLEEP[tier])

if __name__ == "__main__":
    run_pipeline()
