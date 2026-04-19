#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v33 (Milk Road UI & WP Tag Sync)
# ═══════════════════════════════════════════════════════════════
import os, json, time, random, re, datetime, io, math
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
TIER_LABELS = {"premium": "Pro", "vip": "VIP"} 

F = "font-size:17px;line-height:1.85;color:#334155;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,sans-serif;"
GOLD   = "#b8974d"
AMBER  = "#f59e0b"
DARK   = "#0f172a"
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
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://www.wsj.com/xml/rss/3_7031.xml",
    ],
    "Politics": [
        "https://feeds.reuters.com/Reuters/PoliticsNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    ],
    "Tech": [
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://techcrunch.com/feed/",
    ],
    "Health": [
        "https://feeds.reuters.com/reuters/healthNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
    ],
    "Energy": [
        "https://oilprice.com/rss/main",
        "https://feeds.reuters.com/reuters/environment",
    ],
}

# ═══════════════════════════════════════════════
# UTILS & API
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
    return False

def xtag(raw, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
    return m.group(1).strip() if m else ""

def make_slug(kw, title, cat):
    base = kw if (kw and len(kw) > 4) else title
    slug = re.sub(r"[^\w\s-]", "", base.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:55]
    return f"{slug}-{datetime.datetime.utcnow().strftime('%m%d%H%M')}"

def sanitize(html):
    html = re.sub(r"<script(?!\s+type=['\"]application/ld\+json['\"])[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    return re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.DOTALL)

def _clean_seo_title(title):
    for p in ["[PRO] ", "[VIP] ", "[PRO]", "[VIP]", "[Pro] "]: title = title.replace(p, "")
    return title.strip()

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

# ═══════════════════════════════════════════════
# 📊 VISUAL DATA BUILDERS (HTML Tables/Bars)
# ═══════════════════════════════════════════════
def _build_data_table(raw_data, title="Market Data Overview"):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""
    html = f"""
    <div style="background:#ffffff; border:1px solid {BORDER}; border-radius:12px; padding:20px; margin:30px 0; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
        <h3 style="margin-top:0; font-size:18px; color:{DARK}; border-bottom:2px solid {GOLD}; padding-bottom:10px; display:inline-block;">{title}</h3>
        <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; margin-top:10px; font-family:-apple-system,sans-serif;">
            <thead>
                <tr style="background:{BG_LIGHT}; text-align:left; border-bottom:2px solid {BORDER};">
                    <th style="padding:12px; color:{SLATE}; font-weight:700; font-size:14px; white-space:nowrap;">Asset/Metric</th>
                    <th style="padding:12px; color:{SLATE}; font-weight:700; font-size:14px; white-space:nowrap;">Status</th>
                    <th style="padding:12px; color:{SLATE}; font-weight:700; font-size:14px; white-space:nowrap;">Trend</th>
                    <th style="padding:12px; color:{SLATE}; font-weight:700; font-size:14px;">Key Insight</th>
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
                    <td style="padding:12px; font-weight:600; color:{DARK};">{asset}</td>
                    <td style="padding:12px; color:{SLATE}; font-family:monospace; font-size:15px; font-weight:bold;">{value}</td>
                    <td style="padding:12px; font-weight:bold; color:{t_color};">{t_icon} {trend.upper()}</td>
                    <td style="padding:12px; color:{MUTED}; font-size:14px; line-height:1.5;">{insight}</td>
                </tr>
            """
    html += "</tbody></table></div></div>"
    return html

def _build_progress_bars(raw_data, title="Sector Risk Heatmap"):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""
    html = f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:12px; padding:24px; margin:30px 0;">
        <h3 style="margin-top:0; font-size:18px; color:{DARK}; border-bottom:2px solid {BORDER}; padding-bottom:10px;">{title}</h3>
    """
    colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"]
    for i, line in enumerate(lines[:4]):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:
            name = parts[0]
            try: pct = int(re.sub(r'[^0-9]', '', parts[1]))
            except: pct = 50
            pct = max(0, min(100, pct))
            c = colors[i % len(colors)]
            html += f"""
            <div style="margin-top:15px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="font-weight:600; font-size:14px; color:{DARK};">{name}</span>
                    <span style="font-weight:900; font-size:14px; color:{c};">{pct}%</span>
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
    items = "".join(f'<li style="margin-bottom:10px; color:{SLATE};">{l.replace("-", "").replace("*", "").strip()}</li>' for l in lines[:3])
    return f"""
    <div style="background:#f1f5f9; border:1px solid {BORDER}; border-radius:10px; padding:24px; margin:35px 0;">
        <h3 style="margin-top:0; font-size:18px; color:{DARK}; text-transform:uppercase; letter-spacing:1px;">⚡ Quick Hits</h3>
        <ul style="{F} margin:0; padding-left:20px;">{items}</ul>
    </div>
    """

# ═══════════════════════════════════════════════
# 🎨 HTML BUILDERS (PRO & VIP)
# ═══════════════════════════════════════════════
def build_html(tier, cat, raw, title, author, tf, slug, exc, kw):
    html = f"<div style=\"{F}\">\n"
    badge = "VIP EXCLUSIVE" if tier == "vip" else "PRO EXCLUSIVE"
    badge_bg = GOLD if tier == "vip" else "#3b82f6"
    
    html += f"""
    <div style="border-top:3px solid {badge_bg}; border-bottom:1px solid {BORDER}; padding:14px 0; margin-bottom:30px;">
        <p style="margin:0; font-size:15px; color:{MUTED};">
            <strong style="color:{DARK};">{author}</strong> &nbsp;|&nbsp; {tf}
            <span style="background:{badge_bg}; color:#fff; padding:4px 12px; border-radius:4px; font-size:11px; font-weight:800; letter-spacing:1px; margin-left:10px;">{badge}</span>
        </p>
    </div>
    """
    
    if tier == "vip":
        html += f'<h2 style="font-size:26px; color:{DARK}; border-bottom:2px solid {GOLD}; padding-bottom:8px; display:inline-block;">Executive Summary</h2>'
        html += f'<p><strong>{xtag(raw, "EXECUTIVE_SUMMARY")}</strong></p>'
        html += _build_data_table(xtag(raw, "DATA_TABLE"), "Global Macro Dashboard")
        html += _build_progress_bars(xtag(raw, "HEATMAP"), "Sector Risk Heatmap")
        
        html += f"""
        <div style="background:#faf5ff; border-left:4px solid #8b5cf6; padding:24px; margin:35px 0; border-radius:0 10px 10px 0;">
            <p style="font-size:18px; font-weight:700; color:#4c1d95; margin:0 0 10px;">💡 Viral Social Insights</p>
            <p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p>
        </div>
        """
        html += f'<h2 style="font-size:26px; color:{DARK}; border-bottom:2px solid {GOLD}; padding-bottom:8px; display:inline-block; margin-top:20px;">Market Drivers & Analysis</h2>'
        html += f'<h3 style="font-size:22px; color:{DARK}; margin-top:15px;">{xtag(raw, "MARKET_HEADLINE")}</h3>'
        html += f'<p>{xtag(raw, "MACRO")}</p><p>{xtag(raw, "HERD")}</p><p>{xtag(raw, "CONTRARIAN")}</p>'
        html += f"""
        <div style="background:#fffbeb; border:1px solid #fde68a; border-left:4px solid {AMBER}; padding:20px; margin:35px 0; border-radius:4px 10px 10px 4px;">
            <strong style="color:#92400e; font-size:18px;">🔗 Quick Flow:</strong><br>
            <span style="font-weight:600; color:{DARK}; display:inline-block; margin-top:8px;">{xtag(raw, "QUICK_FLOW")}</span>
        </div>
        """
    else: 
        html += f'<h2 style="font-size:26px; color:{DARK}; border-bottom:2px solid #3b82f6; padding-bottom:8px; display:inline-block;">Executive Summary</h2>'
        html += f'<p><strong>{xtag(raw, "EXECUTIVE_SUMMARY")}</strong></p>'
        html += _build_data_table(xtag(raw, "DATA_TABLE"), "Market Movers Dashboard")
        
        html += f"""
        <div style="background:#f4f4f5; border-left:5px solid #8b5cf6; padding:24px; border-radius:8px; margin:35px 0;">
            <h3 style="margin-top:0; font-size:20px; color:{DARK}; margin-bottom:12px;">📱 Viral Social Insights</h3>
            <p style="margin:0;">{xtag(raw, "PLAIN_ENGLISH")}</p>
        </div>
        """
        html += f'<h2 style="font-family:Georgia,serif; font-size:28px; color:{DARK}; margin:40px 0 15px;">Market Drivers & Insights</h2>'
        html += f'<h3 style="font-size:22px; color:{DARK}; margin-bottom:15px;">{xtag(raw, "MARKET_HEADLINE")}</h3>'
        html += f'<p>{xtag(raw, "DEPTH")}</p>'
        
        html += f"""
        <div style="background:#fffbeb; border:1px solid #fde68a; padding:20px; border-radius:8px; margin:35px 0;">
            <strong style="font-size:18px; color:#d97706; text-transform:uppercase;">💡 Quick Flow:</strong>
            <p style="font-size:18px; font-weight:bold; color:{DARK}; margin:10px 0 0;">{xtag(raw, "QUICK_FLOW")}</p>
        </div>
        """
        html += f"""
        <div style="display:flex; flex-wrap:wrap; gap:20px; margin:35px 0;">
            <div style="flex:1; min-width:250px; background:#ecfdf5; border:2px solid #10b981; border-radius:10px; padding:24px;">
                <h4 style="margin-top:0; font-size:20px; color:#065f46;">🐂 Bull Case</h4>
                <p style="margin:0; color:#064e3b;">{xtag(raw, "BULL_CASE")}</p>
            </div>
            <div style="flex:1; min-width:250px; background:#fef2f2; border:2px solid #ef4444; border-radius:10px; padding:24px;">
                <h4 style="margin-top:0; font-size:20px; color:#991b1b;">🐻 Bear Case</h4>
                <p style="margin:0; color:#7f1d1d;">{xtag(raw, "BEAR_CASE")}</p>
            </div>
        </div>
        """
        html += _build_quick_hits(xtag(raw, "QUICK_HITS"))
        html += f"""
        <div style="background:#ffffff; border:2px solid #3b82f6; padding:28px; border-radius:10px; margin:35px 0; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top:0; color:#1e40af; font-size:22px;">💎 Pro-Only Insight</h3>
            <p style="margin:0;">{xtag(raw, "PRO_INSIGHT")}</p>
        </div>
        <div style="background:#ecfdf5; border:2px solid #10b981; padding:24px; border-radius:8px; margin-bottom:15px;">
            <p style="margin:0; color:#065f46;"><strong>🟢 DO (Action):</strong> {xtag(raw, "PRO_DO")}</p>
        </div>
        <div style="background:#fef2f2; border:2px solid #ef4444; padding:24px; border-radius:8px; margin-bottom:35px;">
            <p style="margin:0; color:#7f1d1d;"><strong>🔴 DON'T (Avoid):</strong> {xtag(raw, "PRO_DONT")}</p>
        </div>
        """
    
    tw = xtag(raw, "KEY_TAKEAWAY") if tier == "premium" else xtag(raw, "BULL_CASE")
    ps = xtag(raw, "PS")
    html += f"""
    <hr style="border:0; height:1px; background:{BORDER}; margin:45px 0;">
    <h2 style="font-family:Georgia,serif; font-size:26px; color:{DARK}; margin-bottom:15px;">Today's Warm Insight</h2>
    <p style="{F}">{tw}</p>
    <div style="background:{DARK}; padding:28px; border-radius:10px; border-left:4px solid {badge_bg}; margin-top:30px;">
        <p style="color:#e2e8f0; font-size:18px; margin:0; line-height:1.6;">
            <strong style="color:{badge_bg};">P.S.</strong> {ps}
        </p>
    </div>
    <p style="font-size:13px; color:{MUTED}; text-align:center; margin-top:35px; text-transform:uppercase; letter-spacing:0.5px;">
        Disclaimer: This article is for informational purposes only. All decisions are your own.
    </p>
    </div>
    """
    return sanitize(html)

# ═══════════════════════════════════════════════
# 🎨 MILK ROAD STYLE FLAT THUMBNAIL (100% Vector-like)
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

def _draw_flat_icon(draw, icon_type, cx, cy, S):
    """밀크로드 스타일의 강렬하고 거대한 플랫 벡터 아이콘을 그립니다."""
    if icon_type == "Economy":
        # 황금 동전 (Coin)
        r = 130 * S
        draw.ellipse([cx-r+15*S, cy-r+15*S, cx+r+15*S, cy+r+15*S], fill="#00000040") # Drop shadow
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#f59e0b") # Base
        draw.ellipse([cx-r*0.75, cy-r*0.75, cx+r*0.75, cy+r*0.75], fill="#fbbf24") # Inner
        draw.rectangle([cx-15*S, cy-r*0.5, cx+15*S, cy+r*0.5], fill="#b45309") # $ pillar
        draw.chord([cx-r*0.4, cy-r*0.4, cx+r*0.4, cy], start=90, end=270, fill="#b45309")
        draw.chord([cx-r*0.4, cy, cx+r*0.4, cy+r*0.4], start=270, end=90, fill="#b45309")
    elif icon_type == "Politics":
        # 지구본 (Globe)
        r = 140 * S
        draw.ellipse([cx-r+15*S, cy-r+15*S, cx+r+15*S, cy+r+15*S], fill="#00000040")
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#1e40af")
        draw.ellipse([cx-r*0.4, cy-r, cx+r*0.4, cy+r], outline="#60a5fa", width=12*S)
        draw.ellipse([cx-r*0.8, cy-r, cx+r*0.8, cy+r], outline="#60a5fa", width=12*S)
        draw.line([(cx-r, cy), (cx+r, cy)], fill="#60a5fa", width=12*S)
        draw.line([(cx-r*0.85, cy-r*0.5), (cx+r*0.85, cy-r*0.5)], fill="#60a5fa", width=12*S)
        draw.line([(cx-r*0.85, cy+r*0.5), (cx+r*0.85, cy+r*0.5)], fill="#60a5fa", width=12*S)
    elif icon_type == "Tech":
        # 마이크로칩 (Chip)
        r = 110 * S
        draw.rounded_rectangle([cx-r+15*S, cy-r+15*S, cx+r+15*S, cy+r+15*S], radius=20*S, fill="#00000040")
        draw.rounded_rectangle([cx-r, cy-r, cx+r, cy+r], radius=20*S, fill="#2e1065")
        draw.rounded_rectangle([cx-r*0.6, cy-r*0.6, cx+r*0.6, cy+r*0.6], radius=10*S, fill="#4c1d95")
        for p in [-0.7, -0.3, 0.3, 0.7]:
            draw.line([(cx+p*r, cy-r*1.3), (cx+p*r, cy-r)], fill="#a78bfa", width=15*S)
            draw.line([(cx+p*r, cy+r), (cx+p*r, cy+r*1.3)], fill="#a78bfa", width=15*S)
            draw.line([(cx-r*1.3, cy+p*r), (cx-r, cy+p*r)], fill="#a78bfa", width=15*S)
            draw.line([(cx+r, cy+p*r), (cx+r*1.3, cy+p*r)], fill="#a78bfa", width=15*S)
    elif icon_type == "Health":
        # 방패 속의 십자가 (Shield & Cross)
        r = 130 * S
        pts = [(cx-r, cy-r), (cx+r, cy-r), (cx+r, cy+r*0.2), (cx, cy+r*1.2), (cx-r, cy+r*0.2)]
        shadow = [(x+15*S, y+15*S) for x, y in pts]
        draw.polygon(shadow, fill="#00000040")
        draw.polygon(pts, fill="#064e3b")
        cr = 50 * S
        draw.rectangle([cx-cr*0.3, cy-cr, cx+cr*0.3, cy+cr*0.8], fill="#34d399")
        draw.rectangle([cx-cr, cy-cr*0.3, cx+cr, cy+cr*0.1], fill="#34d399")
    else: # Energy
        # 벼락 (Lightning Bolt)
        r = 130 * S
        draw.ellipse([cx-r+15*S, cy-r+15*S, cx+r+15*S, cy+r+15*S], fill="#00000040")
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#1e293b")
        pts = [(cx+10*S, cy-90*S), (cx-50*S, cy+10*S), (cx, cy+10*S), (cx-20*S, cy+90*S), (cx+60*S, cy-20*S), (cx+10*S, cy-20*S)]
        draw.polygon(pts, fill="#fbbf24")

def make_thumbnail(title_text, cat, tier):
    W, H, SCALE = 1200, 630, 2
    w, h = W * SCALE, H * SCALE
    
    STYLES = {
        "Economy":  {"bg": "#0f172a", "acc": "#2563eb"}, # Dark Blue / Bright Blue
        "Politics": {"bg": "#0f172a", "acc": "#dc2626"}, # Dark Blue / Red
        "Tech":     {"bg": "#0f172a", "acc": "#7c3aed"}, # Dark Blue / Purple
        "Health":   {"bg": "#0f172a", "acc": "#059669"}, # Dark Blue / Green
        "Energy":   {"bg": "#0f172a", "acc": "#d97706"}, # Dark Blue / Amber
    }
    style = STYLES.get(cat, STYLES["Economy"])
    
    img = Image.new("RGB", (w, h), style["bg"])
    draw = ImageDraw.Draw(img)
    
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

    # 1. 밀크로드 스타일 우측 사선 배경 (Slanted Split)
    pts = [(w*0.50, 0), (w, 0), (w, h), (w*0.40, h)]
    draw.polygon(pts, fill=style["acc"])
    # 입체감용 그림자 사선
    pts_shadow = [(w*0.47, 0), (w*0.50, 0), (w*0.40, h), (w*0.37, h)]
    draw.polygon(pts_shadow, fill="#00000050")

    # 2. 우측 중앙 거대 아이콘 (Flat Vector Art)
    _draw_flat_icon(draw, cat, w*0.75, h*0.5, SCALE)

    # 3. 뱃지 (Category / Date)
    pad = 70 * SCALE
    date_str = datetime.datetime.utcnow().strftime("%b %d, %Y").upper()
    badge_text = f"  {cat.upper()}  |  {date_str}  "
    draw.rounded_rectangle([pad, pad, pad + draw.textlength(badge_text, font=font_badge) + 40*SCALE, pad + 60*SCALE], radius=10*SCALE, fill="#000000")
    draw.text((pad + 20*SCALE, pad + 12*SCALE), badge_text, font=font_badge, fill="#ffffff")
    
    # 4. VIP / PRO 뱃지
    tier_text = " VIP REPORT " if tier == "vip" else " PRO REPORT "
    tier_bg = GOLD if tier == "vip" else "#3b82f6"
    tier_w = draw.textlength(tier_text, font=font_badge)
    draw.rounded_rectangle([w - pad - tier_w - 40*SCALE, pad, w - pad, pad + 60*SCALE], radius=10*SCALE, fill=tier_bg)
    draw.text((w - pad - tier_w - 20*SCALE, pad + 12*SCALE), tier_text, font=font_badge, fill="#ffffff")

    # 5. 메인 타이틀 자동 줄바꿈
    clean_title = _clean_seo_title(title_text).replace('"', '').replace("'", "")
    words = clean_title.upper().split()
    lines, current_line = [], []
    max_w = w * 0.55 # 좌측 55% 영역만 사용
    
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
    for line in lines[:4]: 
        draw.text((pad, y_pos), line, font=font_title, fill="#ffffff")
        y_pos += 100 * SCALE

    # 6. 하단 로고
    draw.text((pad, h - pad - 40*SCALE), "WARM INSIGHT", font=font_logo, fill="#94a3b8")

    img = img.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

# ═══════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════
def _make_vip_prompt(news_text, cat):
    return f"""You are a veteran financial analyst. Write a VIP deep-dive on {cat}.
Respond ONLY with XML tags.

<TITLE>Headline, max 90 chars. DO NOT mention specific stock tickers in the title.</TITLE>
<SEO_KEYWORD>focus keyphrase</SEO_KEYWORD>
<EXECUTIVE_SUMMARY>3 sentences core thesis.</EXECUTIVE_SUMMARY>

<DATA_TABLE>
Extract 3-4 key market metrics from the news.
Format exactly: Asset Name | Value or Price | UP or DOWN or SIDEWAYS | 1 sentence insight
</DATA_TABLE>

<HEATMAP>
Invent 3-4 sector risk levels (0-100%) based on the news.
Format exactly: Sector Name | Number
</HEATMAP>

<PLAIN_ENGLISH>3-4 sentences vivid analogy for beginners.</PLAIN_ENGLISH>
<MARKET_HEADLINE>Analytical headline for drivers.</MARKET_HEADLINE>
<MACRO>2 paragraphs on global context.</MACRO>
<HERD>1 paragraph on retail psychology.</HERD>
<CONTRARIAN>1 paragraph on smart money view.</CONTRARIAN>
<QUICK_FLOW>Chain of events with arrows ➡️</QUICK_FLOW>

<KEY_TAKEAWAY>The bottom line insight.</KEY_TAKEAWAY>
<PS>Historical perspective P.S.</PS>

News: {news_text[:3000]}"""

def _make_premium_prompt(news_text, cat):
    return f"""You are Warm Insight's senior analyst. Write a PRO newsletter on {cat}.
Respond ONLY with XML tags. Fill every tag richly.

<TITLE>Headline, max 80 chars. DO NOT mention specific stock tickers.</TITLE>
<SEO_KEYWORD>focus keyphrase</SEO_KEYWORD>
<EXECUTIVE_SUMMARY>3 sentences core thesis.</EXECUTIVE_SUMMARY>

<DATA_TABLE>
Extract 3-4 key market metrics. 
Format exactly: Asset Name | Value or State | UP or DOWN or SIDEWAYS | 1 sentence insight
</DATA_TABLE>

<PLAIN_ENGLISH>3-4 sentences using a vivid, relatable analogy to explain the news.</PLAIN_ENGLISH>
<MARKET_HEADLINE>Analytical headline for market drivers.</MARKET_HEADLINE>
<DEPTH><strong>🧐 WHY:</strong> Deeper structural pattern (3-4 sentences).<br><br><strong>🐑 HERD TRAP:</strong> Cognitive bias (2-3 sentences).</DEPTH>
<QUICK_FLOW>Chain of events with arrows ➡️</QUICK_FLOW>

<BULL_CASE>3-4 sentences optimistic outlook.</BULL_CASE>
<BEAR_CASE>3-4 sentences pessimistic outlook.</BEAR_CASE>

<QUICK_HITS>3 bullet points of other relevant news. Format: 1 sentence per line.</QUICK_HITS>

<PRO_INSIGHT>1-2 paragraphs cross-sector connection and second-order thinking.</PRO_INSIGHT>
<PRO_DO>1 specific action with reasoning.</PRO_DO>
<PRO_DONT>1 specific mistake to avoid.</PRO_DONT>

<KEY_TAKEAWAY>The bottom line.</KEY_TAKEAWAY>
<PS>Historical perspective or final thought.</PS>

News: {news_text[:3000]}"""

# ═══════════════════════════════════════════════
# PUBLISHER & DYNAMIC PIPELINE
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
    items_list = sorted(list(items)) 
    return items_list[:max_items]

def _upload_image(img_bytes, filename):
    try:
        resp = requests.post(f"{WP_URL}/wp-json/wp/v2/media", headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"}, data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30)
        if resp.status_code in (200, 201): return resp.json().get("id")
    except: pass
    return None

# 🚨 해결 1: 워드프레스 태그(Tag)를 강제로 생성 및 할당하여 뱃지가 "Free"로 뜨는 문제 100% 원천 차단
def get_or_create_wp_tag(tag_name):
    slug = tag_name.lower()
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/tags?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/tags", json={"name": tag_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

# 🚨 해결 2: 슬러그(Slug) 일치 검색을 통해 유령 카테고리 문제 완벽 해결
def get_or_create_wp_category(cat_name):
    slug = cat_name.lower()
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?slug={slug}", auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r.status_code == 200 and len(r.json()) > 0: return r.json()[0]["id"]
        r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/categories", json={"name": cat_name, "slug": slug}, auth=(WP_USER, WP_APP_PASS), timeout=15)
        if r2.status_code in (200, 201): return r2.json()["id"]
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    cat_id = get_or_create_wp_category(cat) # 🚨 정확한 카테고리 ID 매칭
    
    # 🚨 VIP / Pro 태그 매칭 (워드프레스 뱃지 연동용)
    tag_name = "VIP" if tier == "vip" else "Pro"
    tag_id = get_or_create_wp_tag(tag_name)

    post_data = {"title": title, "content": html, "status": "publish", "slug": slug}
    if media_id: post_data["featured_media"] = media_id
    if cat_id: post_data["categories"] = [cat_id]
    if tag_id: post_data["tags"] = [tag_id] # 🚨 태그 주입!

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
    print(f"🚀 Starting v33 Pipeline (Milk Road UI & WP Tag Sync) | Category: {cat}")
    
    if not check_env_vars() or not verify_wp_credentials(): return
    
    all_news = fetch_news_pool(cat)
    total_news = len(all_news)
    print(f"   📥 Fetched {total_news} total news items from RSS.")
    
    if total_news < 4:
        print("   🛑 Not enough news today. Aborting to maintain quality.")
        return
        
    mid = total_news // 2
    news_map = {
        "vip": "\n".join(all_news[:mid]),
        "premium": "\n".join(all_news[mid:])
    }
    
    for tier in TIERS:
        print(f"\n--- Processing {tier.upper()} ---")
        assigned_news = news_map[tier]
        
        prompt = _make_vip_prompt(assigned_news, cat) if tier == "vip" else _make_premium_prompt(assigned_news, cat)
        raw = gem_fb(tier, prompt)
        
        if raw:
            title = xtag(raw, "TITLE")
            kw = xtag(raw, "SEO_KEYWORD")
            exc = xtag(raw, "EXECUTIVE_SUMMARY") if tier == "vip" else xtag(raw, "EXCERPT")
            slug = make_slug(kw, title, cat)
            
            author = VIP_AUTHORS.get(cat, "The Warm Insight Panel")
            tf = datetime.datetime.utcnow().strftime("%B %d, %Y")
            
            html = build_html(tier, cat, raw, title, author, tf, slug, exc, kw)
            img_bytes = make_thumbnail(title, cat, tier)
            
            publish(title, html, exc, kw, cat, slug, tier, img_bytes)
            time.sleep(15)

if __name__ == "__main__":
    run_pipeline()
