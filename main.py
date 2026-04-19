#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v37 (HTML2Image Thumbnail & Full-Spec UI Restored)
# ═══════════════════════════════════════════════════════════════
import os, sys, traceback, time, random, re, datetime
import requests
import feedparser
from google import genai
from html2image import Html2Image

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
WP_URL         = os.environ.get("WP_URL", "https://warminsight.com").rstrip("/")
WP_USER        = os.environ.get("WP_USERNAME", "")
WP_APP_PASS    = os.environ.get("WP_APP_PASSWORD", "")
SITE_URL       = "https://warminsight.com"

MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash"],
    "Premium": ["gemini-2.5-flash", "gemini-2.5-pro"],
}

CATEGORIES  = ["Economy", "Politics", "Tech", "Health", "Energy"]
TIERS       = ["premium", "vip"]
TIER_LABELS = {"premium": "PRO", "vip": "VIP"} 

# UI 디자인 시스템 (과거 완벽했던 버전 복구)
F = "font-size:17px;line-height:1.85;color:#334155;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
GOLD   = "#b8974d"
AMBER  = "#f59e0b"
DARK   = "#0f172a"
SLATE  = "#334155"
MUTED  = "#64748b"
BORDER = "#e2e8f0"
BG_LIGHT = "#f8fafc"

RSS_FEEDS = {
    "Economy": ["https://feeds.reuters.com/reuters/businessNews", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"],
    "Politics": ["https://feeds.reuters.com/Reuters/PoliticsNews", "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"],
    "Tech": ["https://feeds.reuters.com/reuters/technologyNews", "https://techcrunch.com/feed/"],
    "Health": ["https://feeds.reuters.com/reuters/healthNews", "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml"],
    "Energy": ["https://oilprice.com/rss/main", "https://feeds.reuters.com/reuters/environment"],
}

# ═══════════════════════════════════════════════
# 🛡️ SYSTEM UTILS & API ENGINE
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
            if "404" in err: return None
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
    for m in MODEL_PRI.get(tier, ["gemini-2.5-flash"]):
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
# 📰 NEWS POOLING
# ═══════════════════════════════════════════════
def fetch_news_pool(cat, max_items=20):
    feeds = RSS_FEEDS.get(cat, RSS_FEEDS["Economy"])
    items = set()
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for e in d.entries[:8]: 
                title = getattr(e, 'title', '').strip()
                summary = re.sub(r'<[^>]+>', '', getattr(e, 'summary', ''))[:200].strip()
                if title: items.add(f"• {title}: {summary}")
        except: pass
    items_list = list(items)
    random.shuffle(items_list)
    return items_list[:max_items]

# ═══════════════════════════════════════════════
# 🎨 PROMPTS (과거 1200줄 시절의 완벽한 스펙 복구)
# ═══════════════════════════════════════════════
VIP_P1 = """You are Warm Insight's senior analyst. Write PART 1 of a VIP deep-dive on {cat}.
Respond ONLY with XML tags. Do not use placeholders.

<TITLE>Institutional title, max 90 chars. No tickers.</TITLE>
<SEO_KEYWORD>focus keyphrase</SEO_KEYWORD>
<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>

<BIG_NUMBER>A striking statistic (e.g. "5.2%" or "$4T")</BIG_NUMBER>
<BIG_NUMBER_DESC>1 sentence explaining why this number shifts the market.</BIG_NUMBER_DESC>

<FEAR_GREED>Score 0-100</FEAR_GREED>

<MARKET_DASHBOARD>
Extract 4 market indicators (e.g., S&P 500, 10Y Yield).
Format: Name | UP or DOWN or SIDEWAYS | 1 sentence reason
</MARKET_DASHBOARD>

<EXECUTIVE_SUMMARY>3 sentences summarizing systemic shift.</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>3 sentences using a vivid analogy.</PLAIN_ENGLISH>

<MACRO>2 full paragraphs on global forces and central banks.</MACRO>
<HERD>1 paragraph on retail cognitive bias.</HERD>
<CONTRARIAN>1 paragraph on smart money moves.</CONTRARIAN>

<QUICK_FLOW>Chain of events with arrows ➡️</QUICK_FLOW>

News Context:
{news}"""

VIP_P2 = """You are Warm Insight's senior analyst. Write PART 2 of the VIP strategy for {cat}.
Context from Part 1: {ctx}

<BULL_CASE>Bullish scenario. Full paragraph.</BULL_CASE>
<BEAR_CASE>Bearish scenario. Full paragraph.</BEAR_CASE>

<SECTOR_RADAR>
List 4 specific sectors.
Format: Sector Name | BULLISH or BEARISH or NEUTRAL | 1 sentence why
</SECTOR_RADAR>

<VIP_T1>1. The Generational Bargain (Fear vs Greed). Full paragraph.</VIP_T1>
<VIP_T2>2. Asset Allocation Seesaw. Full paragraph.</VIP_T2>
<VIP_T3>3. The Global Shield. Full paragraph.</VIP_T3>
<VIP_T4>4. Survival Mechanics. Full paragraph.</VIP_T4>

<VIP_DO>2 specific actions with ETF sectors and triggers.</VIP_DO>
<VIP_DONT>1 critical mistake to avoid.</VIP_DONT>

<TAKEAWAY>One profound insight.</TAKEAWAY>
<PS>Historical perspective in 2-3 sentences.</PS>"""

PROMPT_PREMIUM = """You are Warm Insight's senior analyst. Write a PRO newsletter on {cat}.
Respond ONLY with XML tags. 600-800 words total.

<TITLE>Compelling headline, max 80 chars. No tickers.</TITLE>
<SEO_KEYWORD>focus keyphrase</SEO_KEYWORD>
<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>

<BIG_NUMBER>A striking statistic (e.g. "5.2%")</BIG_NUMBER>
<BIG_NUMBER_DESC>1 sentence explaining why this number shifts the market.</BIG_NUMBER_DESC>

<EXECUTIVE_SUMMARY>3 sentences capturing the core thesis.</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>3-4 sentences using a vivid, relatable analogy.</PLAIN_ENGLISH>

<HEADLINE>Analytical headline for drivers</HEADLINE>
<DEPTH><strong>🧐 WHY:</strong> Deeper structural pattern (3-4 sentences).<br><br><strong>🐑 HERD TRAP:</strong> Cognitive bias (2-3 sentences).</DEPTH>
<QUICK_FLOW>Chain of events with arrows ➡️</QUICK_FLOW>

<BULL_CASE>3-4 sentences optimistic outlook.</BULL_CASE>
<BEAR_CASE>3-4 sentences pessimistic outlook.</BEAR_CASE>

<QUICK_HITS>3 bullet points of other relevant news. 1 sentence per line.</QUICK_HITS>

<PRO_INSIGHT>1-2 paragraphs cross-sector connection.</PRO_INSIGHT>
<PRO_DO>1 specific action with reasoning.</PRO_DO>
<PRO_DONT>1 specific mistake to avoid.</PRO_DONT>

<TAKEAWAY>The bottom line insight.</TAKEAWAY>
<PS>One-line veteran advice.</PS>

News Context:
{news}"""

# ═══════════════════════════════════════════════
# 📊 FULL-SPEC UI BUILDERS (과거 UI 100% 복원)
# ═══════════════════════════════════════════════
def _ui_big_number(num, desc):
    if not num: return ""
    return f"""
    <div style="background:#fff; border:1px solid {AMBER}; border-radius:10px; margin:30px auto; text-align:center; max-width:600px; padding:40px 20px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.08);">
        <p style="font-weight:900; color:#ea580c; margin:0; line-height:1; font-family:Impact,sans-serif; font-size:72px;">{num}</p>
        <p style="font-size:16px; color:#475569; margin:16px 0 0; line-height:1.6;">{desc}</p>
    </div>
    """

def _ui_fear_greed(score_str):
    try: s = int(re.sub(r'[^0-9]', '', score_str))
    except: s = 50
    s = max(0, min(100, s))
    if s <= 25: label, color = "EXTREME FEAR", "#dc2626"
    elif s <= 45: label, color = "FEAR", "#ea580c"
    elif s <= 55: label, color = "NEUTRAL", "#eab308"
    elif s <= 75: label, color = "GREED", "#84cc16"
    else: label, color = "EXTREME GREED", "#10b981"
    
    return f"""
    <div style="background:#fff; border:1px solid {BORDER}; border-radius:10px; padding:24px; margin:30px 0; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
        <p style="font-size:18px; font-weight:700; color:{DARK}; margin:0 0 16px;">🧭 Fear & Greed Meter</p>
        <div style="display:flex; gap:2px; height:16px; border-radius:8px; overflow:hidden; margin-bottom:10px;">
            <div style="flex:25; background:#dc2626;"></div><div style="flex:20; background:#ea580c;"></div>
            <div style="flex:10; background:#eab308;"></div><div style="flex:20; background:#84cc16;"></div>
            <div style="flex:25; background:#10b981;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; color:{MUTED}; margin-bottom:12px;">
            <span>Fear</span><span>Greed</span>
        </div>
        <p style="text-align:center; font-size:24px; font-weight:800; color:{color}; margin:0;">{s} – {label}</p>
    </div>
    """

def _ui_dashboard(raw_data):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""
    cells = ""
    for line in lines[:4]:
        p = line.split('|')
        if len(p) >= 3:
            name, dr, desc = p[0].strip(), p[1].strip().upper(), p[2].strip()
            color, arrow = ("#10b981", "▲") if "UP" in dr else (("#ef4444", "▼") if "DOWN" in dr else ("#64748b", "—"))
            cells += f"""
            <div style="text-align:center; padding:16px 10px; background:#1e293b; border-radius:8px; min-width:120px; flex:1;">
                <p style="font-size:12px; color:#94a3b8; margin:0 0 8px; font-weight:600; text-transform:uppercase;">{name}</p>
                <p style="font-size:24px; font-weight:800; color:{color}; margin:0;">{arrow} {dr}</p>
                <p style="font-size:11px; color:#64748b; margin:6px 0 0;">{desc}</p>
            </div>
            """
    return f'<div style="display:flex; flex-wrap:wrap; gap:10px; background:{DARK}; border-radius:12px; padding:20px; margin:30px 0;">{cells}</div>'

def _ui_radar(raw_data):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""
    html = f"""
    <div style="background:#fff; border:1px solid {AMBER}; border-radius:10px; padding:24px; margin:30px 0; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
        <p style="font-size:20px; font-weight:700; color:#d97706; margin:0 0 20px;">🎯 Sector Radar</p>
        <table style="width:100%; border-collapse:collapse;">
    """
    for line in lines[:4]:
        p = line.split('|')
        if len(p) >= 3:
            name, sent, desc = p[0].strip(), p[1].strip().upper(), p[2].strip()
            if "BULL" in sent: color, label, bg = "#10b981", "BULL", "#ecfdf5"
            elif "BEAR" in sent: color, label, bg = "#ef4444", "BEAR", "#fef2f2"
            else: color, label, bg = "#f59e0b", "NEUT", "#fffbeb"
            
            html += f"""
            <tr style="border-bottom:1px solid {BORDER};">
                <td style="padding:14px 0; font-size:15px; color:{DARK};"><strong>{name}</strong> – <span style="color:{MUTED}">{desc}</span></td>
                <td style="padding:14px 0 14px 16px; text-align:right;">
                    <div style="background:{bg}; padding:8px; border-radius:6px; border:1px solid {color}40; display:inline-block; text-align:center;">
                        <span style="font-size:11px; font-weight:800; color:{color};">{label}</span>
                    </div>
                </td>
            </tr>
            """
    html += '</table></div>'
    return html

def _ui_plain_english(text):
    if not text: return ""
    return f"""
    <div style="background:#faf5ff; border-left:4px solid #8b5cf6; border-radius:0 10px 10px 0; padding:24px; margin:30px 0;">
        <p style="font-size:18px; font-weight:700; color:#4c1d95; margin:0 0 12px;">💡 In Plain English</p>
        <p style="font-size:16px; line-height:1.75; color:{SLATE}; margin:0;">{text}</p>
    </div>
    """

def _ui_bull_bear(bull, bear):
    if not bull and not bear: return ""
    return f"""
    <div style="display:flex; flex-wrap:wrap; gap:20px; margin:35px 0;">
        <div style="flex:1; min-width:250px; background:#ecfdf5; border:1px solid #a7f3d0; border-radius:10px; padding:24px;">
            <p style="font-size:18px; font-weight:700; color:#065f46; margin:0 0 12px;">🐂 Market Bull</p>
            <p style="font-size:15px; line-height:1.75; color:#064e3b; margin:0;">{bull}</p>
        </div>
        <div style="flex:1; min-width:250px; background:#fef2f2; border:1px solid #fecaca; border-radius:10px; padding:24px;">
            <p style="font-size:18px; font-weight:700; color:#991b1b; margin:0 0 12px;">🐻 Market Bear</p>
            <p style="font-size:15px; line-height:1.75; color:#7f1d1d; margin:0;">{bear}</p>
        </div>
    </div>
    """

# ═══════════════════════════════════════════════
# 🎨 HTML INTEGRATION
# ═══════════════════════════════════════════════
def build_html(tier, cat, raw, author, tf, title):
    html = f"<div style=\"{F}\">\n"
    badge = "VIP EXCLUSIVE" if tier == "vip" else "PRO EXCLUSIVE"
    badge_bg = GOLD if tier == "vip" else "#3b82f6"
    
    html += f"""
    <div style="margin-bottom:28px; border-bottom:2px solid {BORDER}; padding-bottom:22px;">
        <p style="font-size:15px; color:{MUTED}; margin:0 0 12px;">
            <strong style="color:{DARK};">{author}</strong> &nbsp;|&nbsp; {tf} 
            <span style="background:{badge_bg}; color:#fff; padding:4px 12px; border-radius:4px; font-size:11px; font-weight:800; letter-spacing:1.5px; margin-left:10px;">{badge}</span>
        </p>
    </div>
    """
    
    html += _ui_big_number(xtag(raw, "BIG_NUMBER"), xtag(raw, "BIG_NUMBER_DESC"))
    
    if tier == "vip":
        html += f'<h2 style="font-size:24px; color:{DARK}; margin:35px 0 16px; border-bottom:2px solid {GOLD}; padding-bottom:8px; display:inline-block;">Executive Summary</h2>'
        html += f'<p style="font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>'
        
        html += _ui_fear_greed(xtag(raw, "FEAR_GREED"))
        html += _ui_dashboard(xtag(raw, "MARKET_DASHBOARD"))
        html += _ui_plain_english(xtag(raw, "PLAIN_ENGLISH"))
        
        html += f'<h2 style="font-size:24px; color:{DARK}; margin:40px 0 20px; border-bottom:2px solid {GOLD}; padding-bottom:8px; display:inline-block;">Market Drivers</h2>'
        
        # 3가지 드라이버
        html += f'<div style="background:#eff6ff; border-left:4px solid #3b82f6; border-radius:0 10px 10px 0; padding:20px 24px; margin:16px 0;"><p style="font-size:14px; font-weight:800; color:#3b82f6; margin:0 0 10px; letter-spacing:1px;">🧭 MACRO</p><p style="margin:0;">{xtag(raw, "MACRO")}</p></div>'
        html += f'<div style="background:#faf5ff; border-left:4px solid #8b5cf6; border-radius:0 10px 10px 0; padding:20px 24px; margin:16px 0;"><p style="font-size:14px; font-weight:800; color:#8b5cf6; margin:0 0 10px; letter-spacing:1px;">🐑 HERD</p><p style="margin:0;">{xtag(raw, "HERD")}</p></div>'
        html += f'<div style="background:#ecfdf5; border-left:4px solid #059669; border-radius:0 10px 10px 0; padding:20px 24px; margin:16px 0;"><p style="font-size:14px; font-weight:800; color:#059669; margin:0 0 10px; letter-spacing:1px;">🏛️ CONTRARIAN</p><p style="margin:0;">{xtag(raw, "CONTRARIAN")}</p></div>'
        
        html += f"""
        <div style="background:#fffbeb; border-left:4px solid {AMBER}; border-radius:0 10px 10px 0; padding:24px; margin:30px 0;">
            <p style="font-size:18px; font-weight:700; color:#92400e; margin:0 0 12px;">🔗 Quick Flow</p>
            <p style="font-size:16px; line-height:2.2; color:{SLATE}; margin:0;">{xtag(raw, "QUICK_FLOW")}</p>
        </div>
        """
        
        html += _ui_radar(xtag(raw, "SECTOR_RADAR"))
        html += _ui_bull_bear(xtag(raw, "BULL_CASE"), xtag(raw, "BEAR_CASE"))
        
        html += f'<h2 style="font-size:24px; color:{DARK}; margin:40px 0 8px; border-bottom:2px solid {GOLD}; padding-bottom:8px; display:inline-block;">The Titans Playbook</h2>'
        html += f'<div style="border-left:4px solid {GOLD}; padding:24px; margin:20px 0; background:linear-gradient(135deg,#fffbeb,#fef3c7); border-radius:0 10px 10px 0;"><h3 style="font-size:20px; color:#92400e; margin:0 0 14px;">1. The Generational Bargain</h3><p style="margin:0;">{xtag(raw, "VIP_T1")}</p></div>'
        html += f'<div style="border-left:4px solid {GOLD}; padding:24px; margin:20px 0; background:linear-gradient(135deg,#fffbeb,#fef3c7); border-radius:0 10px 10px 0;"><h3 style="font-size:20px; color:#92400e; margin:0 0 14px;">2. Asset Allocation Seesaw</h3><p style="margin:0;">{xtag(raw, "VIP_T2")}</p></div>'
        html += f'<div style="border-left:4px solid {GOLD}; padding:24px; margin:20px 0; background:linear-gradient(135deg,#fffbeb,#fef3c7); border-radius:0 10px 10px 0;"><h3 style="font-size:20px; color:#92400e; margin:0 0 14px;">3. The Global Shield</h3><p style="margin:0;">{xtag(raw, "VIP_T3")}</p></div>'
        
        html += f"""
        <div style="background:#eff6ff; border:2px solid #93c5fd; border-radius:10px; padding:24px; margin:35px 0; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <p style="font-size:18px; font-weight:700; color:#1e3a5f; margin:0 0 14px;">⚡ Investor Action Items</p>
            <p style="margin:0 0 10px; color:#065f46;"><strong>🟢 DO:</strong> {xtag(raw, "VIP_DO")}</p>
            <p style="margin:0; color:#991b1b;"><strong>🔴 DON'T:</strong> {xtag(raw, "VIP_DONT")}</p>
        </div>
        """

    else: # Premium (PRO)
        html += f'<h2 style="font-size:24px; color:{DARK}; margin:35px 0 16px; border-bottom:2px solid #3b82f6; padding-bottom:8px; display:inline-block;">Executive Summary</h2>'
        html += f'<p style="font-weight:500;">{xtag(raw, "EXECUTIVE_SUMMARY")}</p>'
        
        html += _ui_plain_english(xtag(raw, "PLAIN_ENGLISH"))
        
        html += f'<h2 style="font-size:24px; color:{DARK}; margin:40px 0 20px; border-bottom:2px solid #3b82f6; padding-bottom:8px; display:inline-block;">Market Drivers</h2>'
        html += f'<h3 style="font-size:22px; color:{DARK}; margin-bottom:15px;">{xtag(raw, "HEADLINE")}</h3>'
        html += f'<p>{xtag(raw, "DEPTH")}</p>'
        
        html += f"""
        <div style="background:#fffbeb; border-left:4px solid {AMBER}; border-radius:0 10px 10px 0; padding:24px; margin:30px 0;">
            <p style="font-size:18px; font-weight:700; color:#92400e; margin:0 0 12px;">🔗 Quick Flow</p>
            <p style="font-size:16px; line-height:2.2; color:{SLATE}; margin:0;">{xtag(raw, "QUICK_FLOW")}</p>
        </div>
        """
        
        html += _ui_bull_bear(xtag(raw, "BULL_CASE"), xtag(raw, "BEAR_CASE"))
        
        lines = [l.strip() for l in xtag(raw, "QUICK_HITS").split('\n') if l.strip()]
        if lines:
            items = "".join(f'<li style="margin-bottom:10px;">{l.replace("-", "").replace("*", "").strip()}</li>' for l in lines[:3])
            html += f'<div style="background:#f1f5f9; border:1px solid {BORDER}; border-radius:10px; padding:24px; margin:35px 0;"><h3 style="margin-top:0; font-size:18px; color:{DARK};">⚡ Quick Hits</h3><ul style="margin:0; padding-left:20px;">{items}</ul></div>'
        
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
    <p style="{F} font-size:19px; font-style:italic; border-left:3px solid #cbd5e1; padding-left:16px;">"{tw}"</p>
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
# 🖼️ HTML2IMAGE THUMBNAIL (Milk Road Style)
# ═══════════════════════════════════════════════
def get_svg_icon(cat):
    # 밀크로드 스타일의 고화질 SVG 아이콘
    icons = {
        "Economy": '<svg viewBox="0 0 24 24" fill="#fbbf24"><circle cx="12" cy="12" r="10" fill="#f59e0b"/><circle cx="12" cy="12" r="7" fill="#fbbf24"/><path d="M12 6v12m-3-9h6m-6 4h6" stroke="#b45309" stroke-width="2" stroke-linecap="round"/></svg>',
        "Politics": '<svg viewBox="0 0 24 24" fill="#3b82f6"><circle cx="12" cy="12" r="10" fill="#1e40af"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="#60a5fa" stroke-width="1.5" fill="none"/></svg>',
        "Tech": '<svg viewBox="0 0 24 24" fill="#8b5cf6"><rect x="4" y="4" width="16" height="16" rx="2" fill="#4c1d95"/><rect x="8" y="8" width="8" height="8" rx="1" fill="#8b5cf6"/><path d="M12 2v2m0 16v2m-10-10h2m16 0h2" stroke="#c4b5fd" stroke-width="2" stroke-linecap="round"/></svg>',
        "Health": '<svg viewBox="0 0 24 24" fill="#10b981"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="#064e3b"/><path d="M12 8v8m-4-4h8" stroke="#34d399" stroke-width="3" stroke-linecap="round"/></svg>',
        "Energy": '<svg viewBox="0 0 24 24" fill="#f59e0b"><circle cx="12" cy="12" r="10" fill="#1e293b"/><path d="M13 3l-6 10h5l-1 8 6-10h-5l1-8z" fill="#fbbf24"/></svg>'
    }
    return icons.get(cat, icons["Economy"])

def make_thumbnail(title_text, cat, tier):
    # HTML/CSS 기반의 완벽한 렌더링
    STYLES = {
        "Economy":  {"bg": "#0f172a", "acc": "#2563eb", "tbg": "#1e3a8a"}, 
        "Politics": {"bg": "#0f172a", "acc": "#dc2626", "tbg": "#7f1d1d"}, 
        "Tech":     {"bg": "#0f172a", "acc": "#7c3aed", "tbg": "#4c1d95"}, 
        "Health":   {"bg": "#0f172a", "acc": "#059669", "tbg": "#064e3b"}, 
        "Energy":   {"bg": "#0f172a", "acc": "#d97706", "tbg": "#78350f"}, 
    }
    style = STYLES.get(cat, STYLES["Economy"])
    tier_label = "VIP REPORT" if tier == "vip" else "PRO REPORT"
    tier_bg = GOLD if tier == "vip" else "#3b82f6"
    date_str = datetime.datetime.utcnow().strftime("%b %d, %Y").upper()
    
    clean_title = _clean_seo_title(title_text).replace('"', '').replace("'", "")
    
    html_content = f"""
    <html><head>
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        body {{ width: 1200px; height: 630px; margin: 0; padding: 0; background: {style['bg']}; font-family: 'Inter', sans-serif; overflow: hidden; display: flex; color: white; }}
        .bg-slant {{ position: absolute; right: 0; top: 0; width: 55%; height: 100%; background: {style['acc']}; clip-path: polygon(15% 0, 100% 0, 100% 100%, 0% 100%); z-index: 1; }}
        .bg-slant-shadow {{ position: absolute; right: 0; top: 0; width: 58%; height: 100%; background: rgba(0,0,0,0.3); clip-path: polygon(15% 0, 100% 0, 100% 100%, 0% 100%); z-index: 0; }}
        .content {{ position: relative; z-index: 2; padding: 70px; width: 100%; display: flex; flex-direction: column; justify-content: space-between; background: linear-gradient(90deg, {style['tbg']} 40%, transparent); }}
        .top-bar {{ display: flex; justify-content: space-between; align-items: center; width: 100%; padding-right: 140px; box-sizing: border-box; }}
        .badges {{ display: flex; gap: 15px; }}
        .badge {{ background: rgba(0,0,0,0.8); padding: 10px 25px; border-radius: 12px; font-family: 'Bebas Neue', sans-serif; font-size: 28px; letter-spacing: 2px; display:flex; align-items:center; }}
        .badge-tier {{ background: {tier_bg}; color: #fff; }}
        .title {{ font-family: 'Bebas Neue', sans-serif; font-size: 95px; line-height: 1.05; text-transform: uppercase; width: 65%; text-shadow: 2px 4px 10px rgba(0,0,0,0.5); margin-top: -40px; }}
        .logo {{ font-family: 'Bebas Neue', sans-serif; font-size: 40px; color: #cbd5e1; letter-spacing: 2px; }}
        .icon-container {{ position: absolute; right: 12%; top: 50%; transform: translateY(-50%); z-index: 3; filter: drop-shadow(10px 20px 25px rgba(0,0,0,0.5)); }}
        .icon-container svg {{ width: 350px; height: 350px; transform: rotate(15deg); }}
    </style>
    </head><body>
        <div class="bg-slant-shadow"></div>
        <div class="bg-slant"></div>
        <div class="content">
            <div class="top-bar">
                <div class="badge">{cat.upper()} &nbsp;|&nbsp; {date_str}</div>
                <div class="badge badge-tier">{tier_label}</div>
            </div>
            <div class="title">{clean_title}</div>
            <div class="logo">WARM INSIGHT</div>
        </div>
        <div class="icon-container">
            {get_svg_icon(cat)}
        </div>
    </body></html>
    """
    
    try:
        # html2image 라이브러리를 사용하여 렌더링 (Github Actions 환경 대응 플래그 적용)
        hti = Html2Image(custom_flags=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
        hti.output_path = '/tmp' if os.path.exists('/tmp') else '.'
        filename = f"thumb_{random.randint(1000,9999)}.jpg"
        hti.screenshot(html_str=html_content, save_as=filename, size=(1200, 630))
        
        filepath = os.path.join(hti.output_path, filename)
        with open(filepath, 'rb') as f:
            img_bytes = f.read()
        os.remove(filepath) # 임시 파일 삭제
        return img_bytes
    except Exception as e:
        print(f"    ⚠️ html2image failed: {e}")
        # 실패 시 단색 배경으로 fallback
        img = Image.new("RGB", (1200, 630), style["bg"])
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
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
    
    post_data["meta"] = {
        "rank_math_title": (kw + " | " + cat + " | Warm Insight")[:60],
        "rank_math_description": (exc[:120] + f" Expert {cat.lower()} analysis.")[:155],
        "rank_math_focus_keyword": kw,
        "is_premium": "yes",
        "pms_content_restrict": "1",
        "post_tier": tier.upper()
    }

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
    print(f"🚀 Starting v37 Pipeline (Full-Spec & HTML2Image Thumbnail) | Category: {cat}")
    
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
            
            print("    🖌️ Generating HTML2Image Thumbnail...")
            img_bytes = make_thumbnail(title, cat, tier)
            
            publish(title, html, exc, kw, cat, slug, tier, img_bytes)
            time.sleep(TIER_SLEEP[tier])

if __name__ == "__main__":
    run_pipeline()
