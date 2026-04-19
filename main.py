#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v35 (Imagen 3 AI Background + Overlay)
# ═══════════════════════════════════════════════════════════════
import os, sys, traceback, time, random, re, datetime, io
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

# API 모델 설정
MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
    "Premium": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
}
FAST_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]

CATEGORIES  = ["Economy", "Politics", "Tech", "Health", "Energy"]
TIERS       = ["premium", "vip"]
TIER_LABELS = {"premium": "PRO", "vip": "VIP"} 
TIER_SLEEP  = {"premium": 45, "vip": 60}

# 🎨 디자인 시스템 컬러
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
# 🛡️ API ENGINE (JITTER BACKOFF SURVIVAL)
# ═══════════════════════════════════════════════
_gemini_client = None
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None: _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client

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
    for p in ["[PRO] ", "[VIP] ", "[PRO]", "[VIP]", "[Pro] "]: title = title.replace(p, "")
    return title.strip()

# ═══════════════════════════════════════════════
# 📰 NEWS POOLING ENGINE (No Skipping)
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
# 🎨 TWO-PART PROMPTS (1200-Line Quality Restored)
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
# 📊 VISUAL DATA BUILDERS (HTML Tables/Bars)
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
# 🎨 HTML BUILDERS (PRO & VIP)
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
    
    tw = xtag(raw, "TAKEAWAY")
    ps = xtag(raw, "PS")
    
    html += f"""
    <hr style="border:0; height:1px; background:{BORDER}; margin:50px 0;">
    <h2 style="font-family:Georgia,serif; font-size:28px; color:{DARK}; margin-bottom:20px;">Today's Warm Insight</h2>
    <p style="{F} font-size:19px;">{tw}</p>
    <div style="background:{DARK}; padding:30px; border-radius:10px; border-left:5px solid {badge_bg}; margin-top:35px;">
        <p style="color:#e2e8f0; font-size:18px; margin:0; line-height:1.6;">
            <strong style="color:{badge_bg};">P.S.</strong> {ps}
        </p>
    </div>
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:40px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: This article is for informational purposes only. All decisions are your own.
    </p>
    </div>
    """
    return sanitize(html)

# ═══════════════════════════════════════════════
# 🎨 THUMBNAIL (AI Background + Text Overlay)
# ═══════════════════════════════════════════════
def get_font(url, filename):
    if not os.path.exists(filename):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
                out_file.write(response.read())
        except: pass
    return filename

def generate_ai_background(client, cat):
    """구글 Imagen 3를 사용하여 텍스트가 없는 고품질 3D 배경을 생성합니다."""
    prompt = f"Abstract 3D cinematic rendering representing global {cat}, professional financial tone, highly detailed, 8k resolution, clean composition, NO text, NO words."
    print(f"    🎨 Requesting Imagen 3 AI background for {cat}...")
    
    for attempt in range(1, 6):
        try:
            result = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    output_mime_type="image/jpeg"
                )
            )
            if result.generated_images:
                print("    ✅ Imagen 3 background generated successfully!")
                return result.generated_images[0].image.image_bytes
        except Exception as e:
            err = str(e)
            if "503" in err or "UNAVAILABLE" in err or "429" in err:
                wait = (15 * attempt) + random.uniform(0, 5)
                print(f"    ⏳ Imagen API busy. Waiting {wait:.1f}s...")
                time.sleep(wait)
            else:
                print(f"    ⚠️ Imagen error: {err[:100]}")
                time.sleep(5)
    print("    ❌ Failed to generate AI background after retries.")
    return None

def make_thumbnail(client, title_text, cat, tier):
    W, H, SCALE = 1200, 630, 2
    w, h = W * SCALE, H * SCALE
    
    # AI 이미지 생성 시도
    ai_img_bytes = generate_ai_background(client, cat)
    
    if ai_img_bytes:
        base_img = Image.open(io.BytesIO(ai_img_bytes)).convert("RGBA")
        base_img = base_img.resize((w, h), Image.LANCZOS)
    else:
        # 실패 시 사용할 안전한 폴백 다크 배경
        base_img = Image.new("RGBA", (w, h), "#0f172a")

    # 가독성을 위한 그라데이션 오버레이 생성 (왼쪽에서 오른쪽으로 페이드아웃)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    
    for x in range(int(w * 0.7)):
        # 비선형(곡선)으로 자연스럽게 어두워지게 처리하여 텍스트가 무조건 보이도록 함
        alpha = int(240 * (1 - (x / (w * 0.7))) ** 1.2) 
        draw_ov.line([(x, 0), (x, h)], fill=(0, 0, 0, alpha))
    
    # 합성
    img = Image.alpha_composite(base_img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 폰트 세팅
    font_url_bebas = "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf"
    font_url_roboto = "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Bold.ttf"
    fs_path = get_font(font_url_bebas, "fonts/BebasNeue-Regular.ttf")
    fr_path = get_font(font_url_roboto, "fonts/Roboto-Bold.ttf")
    
    def lf(p, s):
        try: return ImageFont.truetype(p, s * SCALE)
        except: return ImageFont.load_default()
        
    font_title = lf(fs_path, 95)
    font_badge = lf(fr_path, 28)
    font_logo  = lf(fs_path, 40)

    pad = 70 * SCALE
    
    # 뱃지 (Category / Date)
    date_str = datetime.datetime.utcnow().strftime("%b %d, %Y").upper()
    badge_text = f"  {cat.upper()}  |  {date_str}  "
    badge_w = draw.textlength(badge_text, font=font_badge)
    
    # 반투명 뱃지 배경
    draw.rounded_rectangle([pad, pad, pad + badge_w + 40*SCALE, pad + 60*SCALE], radius=10*SCALE, fill="#000000CC")
    draw.text((pad + 20*SCALE, pad + 12*SCALE), badge_text, font=font_badge, fill="#ffffff")
    
    # VIP / PRO 뱃지
    tier_text = " VIP REPORT " if tier == "vip" else " PRO REPORT "
    tier_bg = GOLD if tier == "vip" else "#3b82f6"
    tier_w = draw.textlength(tier_text, font=font_badge)
    draw.rounded_rectangle([w - pad - tier_w - 40*SCALE, pad, w - pad, pad + 60*SCALE], radius=10*SCALE, fill=tier_bg)
    draw.text((w - pad - tier_w - 20*SCALE, pad + 12*SCALE), tier_text, font=font_badge, fill="#ffffff")

    # 메인 타이틀
    clean_title = _clean_seo_title(title_text).replace('"', '').replace("'", "")
    words = clean_title.upper().split()
    lines, current_line = [], []
    max_w = w * 0.6  # 좌측 60% 영역만 사용
    
    for word in words:
        test_line = " ".join(current_line + [word])
        try: tw = draw.textlength(test_line, font=font_title)
        except: tw = len(test_line) * 50 * SCALE
        
        if tw <= max_w: current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line: lines.append(" ".join(current_line))

    y_pos = h * 0.35
    for i, line in enumerate(lines[:4]): 
        # 타이틀 두 번째 줄에 포인트를 주어 세련미 강화
        t_color = GOLD if (i == 1 and tier == "vip") else ("#60a5fa" if (i == 1 and tier == "premium") else "#ffffff")
        
        # 텍스트에 얇은 검은색 그림자를 주어 가독성을 200% 보장
        draw.text((pad + 4*SCALE, y_pos + 4*SCALE), line, font=font_title, fill="#000000")
        draw.text((pad, y_pos), line, font=font_title, fill=t_color)
        y_pos += 100 * SCALE

    # 하단 로고
    draw.text((pad, h - pad - 40*SCALE), "WARM INSIGHT", font=font_logo, fill="#cbd5e1")

    img = img.convert("RGB")
    img = img.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

# ═══════════════════════════════════════════════
# PUBLISHER 
# ═══════════════════════════════════════════════
def _upload_image(img_bytes, filename):
    try:
        resp = requests.post(f"{WP_URL}/wp-json/wp/v2/media", headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"}, data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30)
        if resp.status_code in (200, 201): return resp.json().get("id")
    except: pass
    return None

def get_or_create_wp_category(cat_name):
    slug = cat_name.lower()
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/categories", json={"name": cat_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def get_or_create_wp_tag(tag_name):
    slug = tag_name.lower()
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/tags?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/tags", json={"name": tag_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat) 
    
    tag_name = "VIP" if tier == "vip" else "Pro"
    tag_id = get_or_create_wp_tag(tag_name)

    post_data = {"title": title, "content": html, "status": "publish", "slug": slug}
    if media_id: post_data["featured_media"] = media_id
    if cat_id: post_data["categories"] = [cat_id]
    if tag_id: post_data["tags"] = [tag_id] 

    try:
        r = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", json=post_data, auth=(WP_USER, WP_APP_PASS), timeout=30)
        if r.status_code in (200, 201):
            print(f"   ✅ Published: {r.json().get('link')}")
            return True
        else:
            print(f"   ❌ Publish failed: {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Network error: {e}")
    return False

def run_pipeline():
    cat = CATEGORIES[(datetime.datetime.utcnow().hour // 3) % len(CATEGORIES)]
    print(f"🚀 Starting v35 Pipeline (Imagen 3 AI Backgrounds + Text Overlay) | Category: {cat}")
    
    if not check_env_vars() or not verify_wp_credentials(): return
    client = _get_gemini_client()
    
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
            
            print("    🖌️ Generating AI Thumbnail Overlay...")
            img_bytes = make_thumbnail(client, title, cat, tier)
            
            publish(title, html, exc, kw, cat, slug, tier, img_bytes)
            time.sleep(TIER_SLEEP[tier])

if __name__ == "__main__":
    run_pipeline()
