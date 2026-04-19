#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v29 (Ultimate Master & Bug Fix)
# ═══════════════════════════════════════════════════════════════
import os, json, time, random, re, datetime, io
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

MODEL          = "gemini-2.5-flash"
MODEL_FALLBACK = "gemini-2.0-flash" 

SOCIAL_LINKS = {
    "youtube":  "https://www.youtube.com/@WarmInsightyou",
    "x":        "https://x.com/warminsight",
    "linkedin": "",
}
CATEGORIES  = ["Economy", "Politics", "Tech", "Health", "Energy"]
TIERS       = ["premium", "vip"]
TIER_LABELS = {"premium": "PRO", "vip": "VIP"} # SEO 최적화 (이모지 제거)

# 디자인 시스템
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
        "https://feeds.ft.com/rss/home/uk",
    ],
    "Politics": [
        "https://feeds.reuters.com/Reuters/PoliticsNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.reuters.com/Reuters/worldNews",
    ],
    "Tech": [
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://techcrunch.com/feed/",
    ],
    "Health": [
        "https://feeds.reuters.com/reuters/healthNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "https://www.who.int/rss-feeds/news-english.xml",
    ],
    "Energy": [
        "https://oilprice.com/rss/main",
        "https://feeds.reuters.com/reuters/energy",
        "https://feeds.reuters.com/reuters/environment",
    ],
}

# ═══════════════════════════════════════════════
# GEMINI CLIENT
# ═══════════════════════════════════════════════
_gemini_client = None
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client

# ═══════════════════════════════════════════════
# STARTUP CHECKS
# ═══════════════════════════════════════════════
def check_env_vars():
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY  → https://aistudio.google.com/apikey")
    if not WP_USER:
        missing.append("WP_USERNAME    → WordPress username")
    if not WP_APP_PASS:
        missing.append("WP_APP_PASSWORD → WordPress Application Password")
    if missing:
        print("❌ Missing GitHub Secrets:")
        for m in missing:
            print(f"   • {m}")
        return False
    return True

def verify_wp_credentials():
    print("🔐 Verifying WordPress credentials …")
    try:
        resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/users/me",
            auth=(WP_USER, WP_APP_PASS), timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ Authenticated as: {data.get('name','?')}  |  roles: {data.get('roles',[])}")
            return True
        elif resp.status_code == 401:
            print("   ❌ 401 Unauthorized — check WP_USERNAME and WP_APP_PASSWORD.")
            return False
        else:
            print(f"   ❌ WP auth failed: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ WP auth error: {e}")
        return False

# ═══════════════════════════════════════════════
# CORE HELPERS
# ═══════════════════════════════════════════════
def xtag(raw, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
    return m.group(1).strip() if m else ""

def is_echo(text):
    if not text or len(text) < 20:
        return True
    return any(e.lower() in text.lower() for e in ["your ", "here", "example", "placeholder", "[insert", "TODO"])

def make_slug(kw, title, cat):
    base = kw if (kw and len(kw) > 4) else title
    slug = re.sub(r"[^\w\s-]", "", base.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:55]
    ts = datetime.datetime.utcnow().strftime("%m%d")
    return f"{slug}-{ts}" if slug else f"{cat.lower()}-{ts}"

def sanitize(html):
    html = re.sub(r"<script(?!\s+type=['\"]application/ld\+json['\"])[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.DOTALL)
    return html

# ═══════════════════════════════════════════════
# 📱 MOBILE RESPONSIVE CSS INJECTOR
# ═══════════════════════════════════════════════
def _build_global_css():
    return """
    <style>
    .wi-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 35px 0; }
    .wi-grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin: 30px 0; }
    .wi-card-pad { padding: 40px 20px; }
    .wi-text-huge { font-size: 72px; }
    .wi-radar-table { width: 100%; border-collapse: collapse; }
    .wi-radar-tr { border-bottom: 1px solid #e2e8f0; }
    .wi-radar-td1 { padding: 14px 0; font-size: 15px; color: #334155; line-height: 1.6; }
    .wi-radar-td2 { padding: 14px 0 14px 16px; text-align: center; width: 65px; vertical-align: middle; }
    
    @media (max-width: 768px) {
        .wi-grid-2 { grid-template-columns: 1fr; gap: 15px; margin: 25px 0; }
        .wi-card-pad { padding: 24px 16px !important; margin: 20px auto !important; }
        .wi-text-huge { font-size: 48px !important; }
        .wi-radar-tr { display: flex; flex-direction: column; padding: 12px 0; }
        .wi-radar-td1 { padding: 0 0 10px 0 !important; }
        .wi-radar-td2 { padding: 0 !important; width: 100% !important; text-align: left !important; display: flex; align-items: center; gap: 10px; }
        .wi-radar-td2 br { display: none; }
        .wi-radar-td2 span { display: inline-block; margin-bottom: 0 !important; }
    }
    </style>
    """

# ═══════════════════════════════════════════════
# SEO BUILDERS
# ═══════════════════════════════════════════════
def _clean_seo_title(title):
    for p in ["[PRO] ", "[VIP] ", "[PRO]", "[VIP]"]:
        title = title.replace(p, "")
    return title.strip()

def _build_jsonld(title, exc, kw, cat, slug, img_url=""):
    seo_title = _clean_seo_title(title)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    schema = {
        "@context": "https://schema.org", 
        "@type": "NewsArticle",
        "headline": seo_title[:110], 
        "description": exc[:200],
        "url": f"{SITE_URL}/{slug}/", 
        "datePublished": now, 
        "dateModified": now,
        "author": {"@type": "Organization", "name": "Warm Insight"},
        "publisher": {
            "@type": "Organization", 
            "name": "Warm Insight",
            "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/wp-content/uploads/logo.png"}
        },
        "keywords": kw, 
        "articleSection": cat,
    }
    if img_url:
        schema["image"] = {"@type": "ImageObject", "url": img_url}
    return '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False) + "</script>"

def _build_faq_schema(raw):
    faqs = []
    for i in range(1, 4):
        q, a = xtag(raw, f"FAQ_{i}_Q"), xtag(raw, f"FAQ_{i}_A")
        if q and a and len(q) > 10 and len(a) > 20:
            faqs.append({
                "@type": "Question", 
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a}
            })
            
    if not faqs:
        return "", ""
        
    schema = '<script type="application/ld+json">' + json.dumps(
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faqs},
        ensure_ascii=False) + "</script>"
        
    vis = (
        f'<div style="background:{BG_LIGHT};border:1px solid {BORDER};border-radius:10px;'
        f'padding:28px;margin:35px 0;">'
        f'<h3 style="margin-top:0;font-size:20px;color:{DARK};margin-bottom:20px;">'
        '❓ Frequently Asked Questions</h3>'
    )
    for faq in faqs:
        vis += (
            f'<div style="margin-bottom:18px;border-bottom:1px solid {BORDER};padding-bottom:16px;">'
            f'<p style="font-size:16px;font-weight:700;color:{DARK};margin:0 0 8px;">{faq["name"]}</p>'
            f'<p style="font-size:15px;line-height:1.7;color:#475569;margin:0;">'
            f'{faq["acceptedAnswer"]["text"]}</p></div>'
        )
    vis += "</div>"
    return schema, vis

# ═══════════════════════════════════════════════
# 🎨 VIP RICH HTML BUILDERS
# ═══════════════════════════════════════════════
def _vip_header(author, impact, sector_tag, cat):
    date_str = datetime.datetime.utcnow().strftime("%B %d, %Y at %I:%M %p") + " (UTC)"
    impact_c = {"HIGH": "#dc2626", "MEDIUM": "#f59e0b", "LOW": "#10b981"}.get(impact.upper(), "#f59e0b")
    return (
        f'<div style="margin-bottom:28px;border-bottom:2px solid {BORDER};padding-bottom:22px;">'
        f'<p style="font-size:15px;color:{MUTED};margin:0 0 12px;">'
        f'<strong style="color:{DARK};">{author}</strong> &nbsp;|&nbsp; {date_str} '
        f'<span style="background:{GOLD};color:#fff;padding:4px 12px;border-radius:4px;'
        f'font-size:11px;font-weight:800;letter-spacing:1.5px;margin-left:10px;">VIP EXCLUSIVE</span></p>'
        f'<div style="display:flex;gap:12px;flex-wrap:wrap;">'
        f'<span style="border:2px solid {impact_c};color:{impact_c};padding:4px 16px;'
        f'border-radius:20px;font-size:12px;font-weight:700;">IMPACT: {impact.upper()}</span>'
        f'<span style="border:2px solid {AMBER};color:#d97706;padding:4px 16px;'
        f'border-radius:20px;font-size:12px;font-weight:700;">⚡ {sector_tag.upper()}</span>'
        f'</div></div>'
    )

def _vip_big_number(number, desc):
    if not number:
        return ""
    return (
        f'<div class="wi-card-pad" style="background:#fff;border:1px solid {AMBER};border-radius:10px;'
        f'margin:30px auto;text-align:center;max-width:600px;'
        f'box-shadow:0 4px 6px -1px rgba(0,0,0,0.08);">'
        f'<p class="wi-text-huge" style="font-weight:900;color:#ea580c;margin:0;line-height:1;'
        f'font-family:Impact,sans-serif;">{number}</p>'
        f'<p style="font-size:16px;color:#475569;margin:16px 0 0;line-height:1.6;">{desc}</p>'
        f'</div>'
    )

def _vip_market_dashboard(dashboard_data):
    if not dashboard_data:
        return ""
    cells = ""
    for item in dashboard_data[:4]:
        d = item.get("direction", "SIDEWAYS").upper()
        color, arrow = {"UP": ("#10b981", "▲"), "DOWN": ("#ef4444", "▼")}.get(d, ("#64748b", "—"))
        cells += (
            f'<div style="text-align:center;padding:16px 10px;'
            f'background:#1e293b;border-radius:8px;">'
            f'<p style="font-size:12px;color:#94a3b8;margin:0 0 8px;font-weight:600;'
            f'letter-spacing:0.5px;text-transform:uppercase;">{item.get("name","")}</p>'
            f'<p style="font-size:24px;font-weight:800;color:{color};margin:0;letter-spacing:1px;">'
            f'{arrow} {d}</p>'
            f'<p style="font-size:11px;color:#64748b;margin:6px 0 0;line-height:1.4;">'
            f'{item.get("desc","")[:60]}</p>'
            f'</div>'
        )
    return f'<div class="wi-grid-4" style="background:{DARK};border-radius:12px;padding:20px;">{cells}</div>'

def _vip_fear_greed(score):
    try:
        s = int(score)
    except (ValueError, TypeError):
        s = 50
    s = max(0, min(100, s))
    if s <= 25: label, color = "EXTREME FEAR", "#dc2626"
    elif s <= 45: label, color = "FEAR", "#ea580c"
    elif s <= 55: label, color = "NEUTRAL", "#eab308"
    elif s <= 75: label, color = "GREED", "#84cc16"
    else: label, color = "EXTREME GREED", "#10b981"
        
    return (
        f'<div style="background:#fff;border:1px solid {BORDER};border-radius:10px;'
        f'padding:24px;margin:30px 0;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
        f'<p style="font-size:18px;font-weight:700;color:{DARK};margin:0 0 16px;">🧭 Fear & Greed Meter</p>'
        f'<div style="display:flex;gap:2px;height:16px;border-radius:8px;overflow:hidden;margin-bottom:10px;">'
        f'<div style="flex:25;background:#dc2626;"></div><div style="flex:20;background:#ea580c;"></div>'
        f'<div style="flex:10;background:#eab308;"></div><div style="flex:20;background:#84cc16;"></div>'
        f'<div style="flex:25;background:#10b981;"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font-size:12px;color:{MUTED};margin-bottom:12px;">'
        f'<span>Fear</span><span>Greed</span></div>'
        f'<p style="text-align:center;font-size:24px;font-weight:800;color:{color};margin:0;">'
        f'{s} – {label}</p></div>'
    )

def _vip_executive_summary(text):
    if not text: return ""
    return (
        f'<h2 style="font-size:24px;color:{DARK};margin:35px 0 16px;border-bottom:2px solid {GOLD};'
        f'padding-bottom:8px;display:inline-block;">Executive Summary</h2>'
        f'<p style="{F}font-weight:500;">{text}</p>'
    )

def _vip_plain_english(text):
    if not text: return ""
    return (
        f'<div style="background:#faf5ff;border-left:4px solid #8b5cf6;border-radius:0 10px 10px 0;'
        f'padding:24px;margin:30px 0;">'
        f'<p style="font-size:18px;font-weight:700;color:#4c1d95;margin:0 0 12px;">💡 In Plain English</p>'
        f'<p style="font-size:16px;line-height:1.75;color:{SLATE};margin:0;">{text}</p>'
        f'</div>'
    )

def _vip_market_drivers(macro, herd, contrarian):
    html = (
        f'<h2 style="font-size:24px;color:{DARK};margin:40px 0 20px;border-bottom:2px solid {GOLD};'
        f'padding-bottom:8px;display:inline-block;">Market Drivers</h2>'
    )
    drivers = [
        ("🧭", "MACRO", macro, "#3b82f6", "#eff6ff"),
        ("🐑", "HERD", herd, "#8b5cf6", "#faf5ff"),
        ("🏛️", "CONTRARIAN", contrarian, "#059669", "#ecfdf5"),
    ]
    for icon, label, content, accent, bg in drivers:
        if content:
            html += (
                f'<div style="background:{bg};border-left:4px solid {accent};border-radius:0 10px 10px 0;'
                f'padding:20px 24px;margin:16px 0;">'
                f'<p style="font-size:14px;font-weight:800;color:{accent};margin:0 0 10px;'
                f'letter-spacing:1px;">{icon} {label}</p>'
                f'<p style="{F}margin:0;">{content}</p>'
                f'</div>'
            )
    return html

def _vip_quick_flow(text):
    if not text: return ""
    return (
        f'<div style="background:#fffbeb;border-left:4px solid {AMBER};border-radius:0 10px 10px 0;'
        f'padding:24px;margin:30px 0;">'
        f'<p style="font-size:18px;font-weight:700;color:#92400e;margin:0 0 12px;">🔗 Quick Flow</p>'
        f'<p style="font-size:16px;line-height:2.2;color:{SLATE};margin:0;">{text}</p>'
        f'</div>'
    )

def _vip_key_indicators(indicators):
    if not indicators: return ""
    colors = ["#f59e0b", "#f97316", "#10b981"]
    
    cards = '<div class="wi-grid-4">'
    for i, ind in enumerate(indicators[:3]):
        c = colors[i % len(colors)]
        pct = ind.get("pct", 50)
        cards += (
            f'<div style="border:2px solid {c};border-radius:10px;'
            f'padding:20px;text-align:center;background:#fff;'
            f'box-shadow:0 2px 4px rgba(0,0,0,0.05);">'
            f'<p style="font-size:36px;font-weight:800;color:{c};margin:0;">{pct}%</p>'
            f'<p style="font-size:14px;color:{MUTED};margin:8px 0 0;">{ind.get("name","")}</p>'
            f'</div>'
        )
    cards += '</div>'
    
    bars = (
        f'<div style="background:#fff;border:1px solid {BORDER};border-radius:10px;'
        f'padding:24px;margin:16px 0;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
        f'<p style="font-size:20px;font-weight:700;color:{DARK};margin:0 0 18px;">'
        f'📊 Key Market Indicators</p>'
    )
    for i, ind in enumerate(indicators[:3]):
        pct = ind.get("pct", 50)
        bc = colors[i % len(colors)]
        bars += (
            f'<div style="margin-bottom:16px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
            f'<span style="font-size:15px;font-weight:600;color:{DARK};">{ind.get("name","")}</span>'
            f'<span style="font-size:15px;font-weight:700;color:{bc};">{pct}%</span></div>'
            f'<div style="background:#e2e8f0;border-radius:8px;height:12px;overflow:hidden;">'
            f'<div style="background:{bc};height:100%;width:{pct}%;border-radius:8px;'
            f'transition:width 0.5s ease;"></div></div></div>'
        )
    bars += '</div>'
    return cards + bars

def _vip_sector_radar(sectors):
    if not sectors: return ""
    html = (
        f'<div style="background:#fff;border:1px solid {AMBER};border-radius:10px;'
        f'padding:24px;margin:30px 0;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
        f'<p style="font-size:20px;font-weight:700;color:#d97706;margin:0 0 20px;">🎯 Sector Radar</p>'
        f'<table class="wi-radar-table">'
    )
    for sec in sectors[:5]:
        s = sec.get("sentiment", "NEUTRAL").upper()
        if s == "BULLISH": color, label, bg = "#10b981", "BULL", "#ecfdf5"
        elif s == "BEARISH": color, label, bg = "#ef4444", "BEAR", "#fef2f2"
        else: color, label, bg = "#f59e0b", "NEUT", "#fffbeb"
            
        html += (
            f'<tr class="wi-radar-tr">'
            f'<td class="wi-radar-td1"><strong style="color:{DARK};">{sec.get("name","")}</strong> – {sec.get("desc","")}</td>'
            f'<td class="wi-radar-td2">'
            f'<div style="background:{bg};padding:8px 8px;border-radius:6px;border:1px solid {color}40;display:inline-block;text-align:center;">'
            f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};margin-bottom:4px;"></span><br>'
            f'<span style="font-size:11px;font-weight:800;color:{color};">{label}</span>'
            f'</div></td></tr>'
        )
    html += '</table></div>'
    return html

def _vip_bull_bear(bull, bear):
    if not bull and not bear: return ""
    html = '<div class="wi-grid-2">'
    if bull:
        html += (
            f'<div style="background:#ecfdf5;border:1px solid #a7f3d0;'
            f'border-radius:10px;padding:24px;">'
            f'<p style="font-size:18px;font-weight:700;color:#065f46;margin:0 0 12px;">🐂 Market Bull</p>'
            f'<p style="font-size:15px;line-height:1.75;color:#064e3b;margin:0;">{bull}</p></div>'
        )
    if bear:
        html += (
            f'<div style="background:#fef2f2;border:1px solid #fecaca;'
            f'border-radius:10px;padding:24px;">'
            f'<p style="font-size:18px;font-weight:700;color:#991b1b;margin:0 0 12px;">🐻 Market Bear</p>'
            f'<p style="font-size:15px;line-height:1.75;color:#7f1d1d;margin:0;">{bear}</p></div>'
        )
    html += '</div>'
    return html

def _vip_deep_analysis(technical, macro_flows, smart_money):
    html = (
        f'<h2 style="font-size:24px;color:{DARK};margin:40px 0 8px;border-bottom:2px solid {GOLD};'
        f'padding-bottom:8px;display:inline-block;">VIP: Macro & Flow Analysis</h2>'
        f'<div style="margin-top:20px;">'
    )
    sections = [
        ("TECHNICAL SIGNALS", technical, "#6366f1"),
        ("MACRO FLOWS", macro_flows, "#0ea5e9"),
        ("SMART MONEY", smart_money, "#10b981"),
    ]
    for label, content, accent in sections:
        if content:
            html += (
                f'<div style="border-left:4px solid {accent};padding:20px 24px;margin:24px 0;'
                f'background:#fff;border-radius:0 10px 10px 0;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
                f'<p style="font-size:13px;font-weight:800;color:{accent};margin:0 0 10px;'
                f'letter-spacing:1.5px;">{label}</p>'
                f'<p style="{F}margin:0;">{content}</p>'
                f'</div>'
            )
    html += '</div>'
    return html

def _vip_titans_playbook(title_text, content):
    if not content: return ""
    return (
        f'<h2 style="font-size:24px;color:{DARK};margin:40px 0 8px;border-bottom:2px solid {GOLD};'
        f'padding-bottom:8px;display:inline-block;">The Titans Playbook</h2>'
        f'<div style="border-left:4px solid {GOLD};padding:24px;margin:20px 0;'
        f'background:linear-gradient(135deg,#fffbeb,#fef3c7);border-radius:0 10px 10px 0;">'
        f'<h3 style="font-size:20px;color:#92400e;margin:0 0 14px;">{title_text}</h3>'
        f'<p style="{F}margin:0;">{content}</p>'
        f'</div>'
    )

def _vip_action_items(acts):
    if not acts: return ""
    return (
        f'<div style="background:#eff6ff;border:2px solid #93c5fd;border-radius:10px;'
        f'padding:24px;margin:35px 0;box-shadow:0 2px 4px rgba(0,0,0,0.05);">'
        f'<p style="font-size:18px;font-weight:700;color:#1e3a5f;margin:0 0 14px;">'
        f'⚡ Investor Action Items</p>{acts}</div>'
    )

# ═══════════════════════════════════════════════
# 🎨 PREMIUM HTML BUILDERS
# ═══════════════════════════════════════════════
def _pro_header(author, impact, sector_tag):
    now = datetime.datetime.utcnow()
    return (
        f'<div style="margin-bottom:24px;border-bottom:2px solid {BORDER};padding-bottom:20px;">'
        f'<p style="font-size:15px;color:{MUTED};margin:0 0 12px;">'
        f'<strong style="color:{DARK};">{author}</strong> &nbsp;|&nbsp; {now.strftime("%B %d, %Y")} '
        f'<span style="background:#6366f1;color:#fff;padding:4px 12px;border-radius:4px;'
        f'font-size:11px;font-weight:800;letter-spacing:1.5px;margin-left:10px;">PRO EXCLUSIVE</span></p>'
        f'<div style="display:flex;gap:12px;flex-wrap:wrap;">'
        f'<span style="border:2px solid {AMBER};color:#d97706;padding:4px 16px;'
        f'border-radius:20px;font-size:12px;font-weight:700;">IMPACT: {impact.upper()}</span>'
        f'<span style="border:2px solid #6366f1;color:#6366f1;padding:4px 16px;'
        f'border-radius:20px;font-size:12px;font-weight:700;">⚡ {sector_tag.upper()}</span>'
        f'</div></div>'
    )

def _pro_sentiment_badge(sent):
    c = {"BULLISH": "#10b981", "BEARISH": "#ef4444", "NEUTRAL": "#f59e0b"}.get(sent, "#f59e0b")
    bg = {"BULLISH": "#ecfdf5", "BEARISH": "#fef2f2", "NEUTRAL": "#fffbeb"}.get(sent, "#fffbeb")
    return (
        f'<div style="background:{bg};border:1px solid {c}40;border-radius:8px;'
        f'padding:14px 20px;margin:20px 0;display:flex;align-items:center;gap:12px;">'
        f'<span style="font-size:14px;font-weight:600;color:{MUTED};">Market Sentiment:</span>'
        f'<span style="background:{c};color:#fff;padding:5px 16px;border-radius:20px;'
        f'font-size:13px;font-weight:700;">{sent}</span></div>'
    )

def _pro_key_takeaways(text):
    if not text: return ""
    return (
        f'<div style="background:#f0f9ff;border-left:4px solid #3b82f6;border-radius:0 10px 10px 0;'
        f'padding:24px;margin:30px 0;">'
        f'<p style="font-size:18px;font-weight:700;color:#1e40af;margin:0 0 12px;">📌 Key Takeaway</p>'
        f'<p style="font-size:16px;line-height:1.75;color:{SLATE};margin:0;">{text}</p>'
        f'</div>'
    )

# ═══════════════════════════════════════════════
# FOOTER BUILDERS
# ═══════════════════════════════════════════════
def _build_author_bio(cat):
    author = VIP_AUTHORS.get(cat, "The Warm Insight Panel")
    first = author.split("&")[0].strip().split()[-1]
    return (
        f'<div style="background:{BG_LIGHT};border:1px solid {BORDER};border-radius:10px;'
        f'padding:24px;margin:35px 0;display:flex;gap:20px;align-items:center;">'
        f'<div style="min-width:56px;height:56px;border-radius:50%;background:{GOLD};'
        f'display:flex;align-items:center;justify-content:center;font-size:22px;'
        f'font-weight:700;color:#fff;">{first[0]}</div>'
        f'<div>'
        f'<p style="font-size:17px;font-weight:700;color:{DARK};margin:0 0 6px;">{author}</p>'
        f'<p style="font-size:14px;color:{MUTED};margin:0;line-height:1.6;">'
        f'Senior analyst at Warm Insight covering global macro-economics, humanities, and psychology for a universal audience.</p>'
        f'</div></div>'
    )

def _build_internal_links(cat):
    pillar = PILLAR_PAGES.get(cat, PILLAR_PAGES["Economy"])
    related = CAT_RELATED.get(cat, ["Economy", "Tech"])
    html = (
        f'<div style="margin:35px 0;padding:20px 24px;background:{BG_LIGHT};'
        f'border-left:4px solid {GOLD};border-radius:0 10px 10px 0;">'
        f'<p style="margin:0 0 12px;font-size:15px;font-weight:700;color:{DARK};">📌 Related Resources</p>'
        f'<p style="margin:0 0 8px;"><a href="{pillar["url"]}" '
        f'style="color:{GOLD};text-decoration:underline;font-weight:600;">{pillar["anchor"]}</a></p>'
    )
    for rc in related[:2]:
        rp = PILLAR_PAGES.get(rc)
        if rp:
            html += (
                f'<p style="margin:0 0 8px;"><a href="{rp["url"]}" '
                f'style="color:{MUTED};text-decoration:underline;">{rc} Analysis</a></p>'
            )
    html += "</div>"
    return html

def _build_social_share(title, slug):
    url = f"{SITE_URL}/{slug}/"
    et = title.replace(" ", "%20").replace("&", "%26")[:100]
    eu = url.replace(":", "%3A").replace("/", "%2F")
    return (
        f'<div style="background:#fff;border:1px solid {BORDER};border-radius:10px;'
        f'padding:24px;margin:35px 0;text-align:center;">'
        f'<p style="font-size:18px;font-weight:700;color:{DARK};margin:0 0 14px;">Share This Analysis</p>'
        f'<div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap;">'
        f'<a href="https://twitter.com/intent/tweet?text={et}&url={eu}" target="_blank" rel="noopener" '
        f'style="display:inline-block;background:#000;color:#fff;padding:10px 22px;border-radius:8px;'
        f'font-size:14px;font-weight:bold;text-decoration:none;">𝕏 Share</a>'
        f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={eu}" target="_blank" rel="noopener" '
        f'style="display:inline-block;background:#0A66C2;color:#fff;padding:10px 22px;border-radius:8px;'
        f'font-size:14px;font-weight:bold;text-decoration:none;">in Share</a>'
        f'<a href="mailto:?subject={et}&body=Check%20this%20out%3A%20{eu}" '
        f'style="display:inline-block;background:#6b7280;color:#fff;padding:10px 22px;border-radius:8px;'
        f'font-size:14px;font-weight:bold;text-decoration:none;">✉ Email</a>'
        f'</div></div>'
    )

def _build_related_posts(cat):
    pillar = PILLAR_PAGES.get(cat, PILLAR_PAGES["Economy"])
    related = CAT_RELATED.get(cat, ["Economy", "Tech"])
    html = (
        f'<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;'
        f'padding:28px;margin:35px 0;">'
        f'<h3 style="margin-top:0;font-size:20px;color:{DARK};margin-bottom:16px;">📖 Continue Reading</h3>'
        f'<div style="display:flex;flex-wrap:wrap;gap:12px;">'
        f'<a href="{pillar["url"]}" style="display:inline-block;background:#fff;border:2px solid #3b82f6;'
        f'color:#1e40af;padding:10px 18px;border-radius:8px;font-size:15px;font-weight:600;'
        f'text-decoration:none;">Browse {pillar["anchor"]} →</a>'
    )
    for rc in related[:2]:
        rp = PILLAR_PAGES.get(rc)
        if rp:
            html += (
                f'<a href="{rp["url"]}" style="display:inline-block;background:#fff;'
                f'border:1px solid {BORDER};color:{SLATE};padding:10px 18px;border-radius:8px;'
                f'font-size:15px;text-decoration:none;">{rc} Analysis →</a>'
            )
    html += (
        f'<a href="{SITE_URL}/warm-insight-vip-membership/" style="display:inline-block;'
        f'background:{GOLD};color:#fff;padding:10px 18px;border-radius:8px;font-size:15px;'
        f'font-weight:bold;text-decoration:none;">🔒 Upgrade to VIP →</a></div></div>'
    )
    return html

def _build_footer(tw, ps):
    if not tw or is_echo(tw):
        tw = "Stay disciplined, stay diversified, and let time compound in your favor."
    if not ps or is_echo(ps):
        ps = "In 40 years of watching markets, the disciplined investor always wins."
        
    si = ""
    if SOCIAL_LINKS.get("youtube"):
        si += (
            f'<a href="{SOCIAL_LINKS["youtube"]}" target="_blank" style="display:inline-block;'
            f'background:#FF0000;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;'
            f'font-weight:bold;text-decoration:none;margin:0 4px;">▶ YouTube</a>'
        )
    if SOCIAL_LINKS.get("x"):
        si += (
            f'<a href="{SOCIAL_LINKS["x"]}" target="_blank" style="display:inline-block;'
            f'background:#000;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;'
            f'font-weight:bold;text-decoration:none;margin:0 4px;">𝕏 Follow</a>'
        )
        
    return (
        f'<hr style="border:0;height:1px;background:{BORDER};margin:45px 0;">'
        f'<h2 style="font-family:Georgia,serif;font-size:26px;color:{DARK};margin-bottom:16px;">Today\'s Warm Insight</h2>'
        f'<p style="{F}font-style:italic;border-left:3px solid #cbd5e1;padding-left:16px;">"{tw}"</p>'
        f'<div style="margin-top:30px;background:{DARK};padding:28px;border-radius:10px;border-left:4px solid {GOLD};">'
        f'<p style="font-size:18px;line-height:1.8;color:#e2e8f0;margin:0;">'
        f'<span style="color:{GOLD};font-weight:bold;">P.S.</span> <span style="color:#cbd5e1;">{ps}</span></p></div>'
        f'<div style="background:{BG_LIGHT};border:1px solid {BORDER};border-radius:10px;'
        f'padding:28px;margin:40px 0;text-align:center;">'
        f'<p style="font-size:20px;font-weight:bold;color:{DARK};margin:0 0 10px;">Found this useful?</p>'
        f'<p style="font-size:15px;color:{MUTED};margin:0 0 18px;">Forward to a friend who wants smarter market analysis.</p>'
        f'<div style="margin-bottom:14px;">{si}</div>'
        f'<p style="margin:0;"><a href="{SITE_URL}" style="color:{GOLD};font-weight:600;text-decoration:underline;">Subscribe at warminsight.com</a></p></div>'
        f'<div style="background:{DARK};padding:35px;border-radius:10px;margin-top:30px;">'
        f'<p style="font-size:24px;font-weight:bold;color:{GOLD};margin:0 0 12px;text-align:center;">Warm Insight</p>'
        f'<div style="text-align:center;margin-bottom:16px;">{si}</div>'
        f'<div style="text-align:center;margin-bottom:16px;font-size:13px;">'
        f'<a href="{SITE_URL}/about-us/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">About</a>'
        f'<a href="{SITE_URL}/privacy-policy/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">Privacy</a>'
        f'<a href="{SITE_URL}/terms/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">Terms</a>'
        f'<a href="{SITE_URL}/warm-insight-vip-membership/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">VIP</a>'
        f'</div>'
        f'<p style="font-size:13px;color:#64748b;margin:0;text-align:center;">All analysis is for informational purposes only. Not financial advice.<br>&copy; 2026 Warm Insight. All rights reserved.</p></div>'
    )

# ═══════════════════════════════════════════════
# MAIN ANALYZE ROUTER (CSS INJECTION)
# ═══════════════════════════════════════════════
def analyze(raw1, raw2, cat, tier):
    full = raw1 + ("\n" + raw2 if raw2 else "")
    tr = xtag(full, "TITLE")
    exc = xtag(full, "EXCERPT") or "Expert market analysis."
    kw = xtag(full, "SEO_KEYWORD")
    tw = xtag(full, "TW")
    ps = xtag(full, "PS")
    
    title = ("[" + TIER_LABELS.get(tier, tier) + "] " + tr if tr else f"({tier.upper()}) {cat} Insight")
    slug = make_slug(kw, tr or cat, cat)

    html = _build_global_css()
    author = VIP_AUTHORS.get(cat, "The Warm Insight Panel")

    if tier == "vip":
        html += _vip_header(author, xtag(full, "IMPACT_LEVEL") or "MEDIUM", xtag(full, "SECTOR_TAG") or cat, cat)
        html += _vip_big_number(xtag(full, "BIG_NUMBER"), xtag(full, "BIG_NUMBER_DESC"))
        
        dashboard_data = [{"name": xtag(full, f"MARKET_{i}_NAME"), "direction": xtag(full, f"MARKET_{i}_DIR"), "desc": xtag(full, f"MARKET_{i}_DESC")} for i in range(1, 5) if xtag(full, f"MARKET_{i}_NAME")]
        html += _vip_market_dashboard(dashboard_data)
        
        html += _vip_fear_greed(xtag(full, "FEAR_GREED"))
        html += _vip_executive_summary(xtag(full, "EXECUTIVE_SUMMARY"))
        html += _vip_plain_english(xtag(full, "PLAIN_ENGLISH"))
        html += _vip_market_drivers(xtag(full, "MACRO"), xtag(full, "HERD"), xtag(full, "CONTRARIAN"))
        html += _vip_quick_flow(xtag(full, "QUICK_FLOW"))
        
        ind_data = [{"name": xtag(full, f"IND_{i}_NAME"), "pct": xtag(full, f"IND_{i}_PCT")} for i in range(1, 4) if xtag(full, f"IND_{i}_NAME")]
        html += _vip_key_indicators(ind_data)
        
        sec_data = [{"name": xtag(full, f"SECTOR_{i}_NAME"), "sentiment": xtag(full, f"SECTOR_{i}_SENT"), "desc": xtag(full, f"SECTOR_{i}_DESC")} for i in range(1, 5) if xtag(full, f"SECTOR_{i}_NAME")]
        html += _vip_sector_radar(sec_data)
        
        html += _vip_bull_bear(xtag(full, "BULL_CASE"), xtag(full, "BEAR_CASE"))
        html += _vip_deep_analysis(xtag(full, "TECHNICAL_SIGNALS"), xtag(full, "MACRO_FLOWS"), xtag(full, "SMART_MONEY"))
        html += _vip_titans_playbook(xtag(full, "TITANS_TITLE"), xtag(full, "TITANS_BODY"))
        html += _vip_action_items(xtag(full, "ACTION_ITEMS"))
    else:
        html += _pro_header(author, xtag(full, "IMPACT_LEVEL") or "MEDIUM", xtag(full, "SECTOR_TAG") or cat)
        if xtag(full, "EXECUTIVE_SUMMARY"):
            html += f'<p style="{F}font-weight:600;">{xtag(full, "EXECUTIVE_SUMMARY")}</p>'
        html += _pro_sentiment_badge(xtag(full, "SENTIMENT").upper() or "NEUTRAL")
        html += _pro_key_takeaways(xtag(full, "KEY_TAKEAWAY"))
        
        if xtag(full, "LEAD"):
            html += f'<p style="{F}">{xtag(full, "LEAD")}</p>\n'
        if xtag(full, "BODY"):
            html += xtag(full, "BODY") + "\n"

    faq_schema, faq_visible = _build_faq_schema(full)
    html += faq_visible
    html += _build_author_bio(cat)
    html += _build_social_share(title, slug)
    html += _build_related_posts(cat)
    html += _build_internal_links(cat)
    html += _build_footer(tw, ps)
    
    html = sanitize(html)
    return title, html, exc, kw, slug, tier, full, faq_schema

# ═══════════════════════════════════════════════
# ⬇️ 폰트 자동 다운로드 (썸네일 깨짐 방지용)
# ═══════════════════════════════════════════════
def get_font(url, filename):
    if not os.path.exists(filename):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            print(f"   ⚠️ Font download error: {e}")
    return filename

# ═══════════════════════════════════════════════
# 🎨 THUMBNAIL GENERATOR 
# ═══════════════════════════════════════════════
CAT_COLORS = {
    "Economy": ("#1a6ef5", "#ffffff", "#ffcc00"),
    "Politics": ("#dc2626", "#ffffff", "#fbbf24"),
    "Tech": ("#6366f1", "#ffffff", "#34d399"),
    "Health": ("#059669", "#ffffff", "#ffffff"),
    "Energy": ("#d97706", "#1a252c", "#1a252c"),
}

def make_thumbnail(title_text, cat, tier):
    W, H, SCALE = 1200, 630, 2
    w, h = W * SCALE, H * SCALE
    
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
    
    font_url_anton = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
    font_url_bebas = "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf"
    ft_path = get_font(font_url_anton, "fonts/Anton-Regular.ttf")
    fs_path = get_font(font_url_bebas, "fonts/BebasNeue-Regular.ttf")
    
    def lf(p, s):
        try: return ImageFont.truetype(p, s * SCALE)
        except: return ImageFont.load_default()
        
    ft = lf(ft_path, 85)
    fs = lf(fs_path, 34)
    fb = lf(fs_path, 30)

    # 1. 🌟 배경 차트 라인
    if tier == "vip":
        ex, ey = w*0.75, h*0.55
        draw.line([(w*0.4, h*0.35), (ex, ey)], fill="#ef4444", width=8*SCALE)
        draw.polygon([(ex, ey), (ex-25*SCALE, ey-5*SCALE), (ex-5*SCALE, ey-25*SCALE)], fill="#ef4444")
        tx, ty = w*0.45, h*0.25
        draw.polygon([(tx, ty-30*SCALE), (tx-30*SCALE, ty+20*SCALE), (tx+30*SCALE, ty+20*SCALE)], fill="#fde047")
        draw.line([(tx, ty-10*SCALE), (tx, ty+5*SCALE)], fill="#1e293b", width=6*SCALE)
        draw.ellipse([(tx-4*SCALE, ty+10*SCALE), (tx+4*SCALE, ty+18*SCALE)], fill="#1e293b")
    else: 
        ex, ey = w*0.8, h*0.35
        draw.line([(w*0.4, h*0.45), (w*0.6, h*0.4), (ex, ey)], fill="#4ade80", width=6*SCALE)
        draw.polygon([(ex, ey), (ex-25*SCALE, ey+5*SCALE), (ex-5*SCALE, ey+25*SCALE)], fill="#4ade80")
        gx, gy = w*0.65, h*0.2
        gr = 35*SCALE
        draw.ellipse([(gx-gr, gy-gr), (gx+gr, gy+gr)], outline="#ffffff60", width=4*SCALE)
        draw.ellipse([(gx-gr/3, gy-gr), (gx+gr/3, gy+gr)], outline="#ffffff60", width=4*SCALE)
        draw.line([(gx-gr, gy), (gx+gr, gy)], fill="#ffffff60", width=4*SCALE)
        draw.line([(gx, gy-gr), (gx, gy+gr)], fill="#ffffff60", width=4*SCALE)

    # 2. 🤖 파이썬 자체 로봇 캐릭터
    cx, cy = w * 0.85, h * 0.7
    S = SCALE
    
    draw.ellipse([cx - 45*S, cy + 60*S, cx - 15*S, cy + 90*S], fill="#047857")
    draw.ellipse([cx + 15*S, cy + 60*S, cx + 45*S, cy + 90*S], fill="#047857")
    draw.rounded_rectangle([cx - 85*S, cy - 10*S, cx - 50*S, cy + 15*S], radius=12*S, fill="#10b981")
    draw.rounded_rectangle([cx + 50*S, cy - 30*S, cx + 85*S, cy - 5*S], radius=12*S, fill="#10b981")
    draw.rounded_rectangle([cx - 50*S, cy - 70*S, cx + 50*S, cy + 70*S], radius=25*S, fill="#10b981")
    
    draw.ellipse([cx - 25*S, cy - 30*S, cx - 5*S, cy - 10*S], fill="#ffffff")
    draw.ellipse([cx + 5*S,  cy - 30*S, cx + 25*S, cy - 10*S], fill="#ffffff")
    draw.ellipse([cx - 18*S, cy - 22*S, cx - 10*S, cy - 14*S], fill="#1e293b")
    draw.ellipse([cx + 12*S, cy - 22*S, cx + 20*S, cy - 14*S], fill="#1e293b")
    draw.ellipse([cx - 40*S, cy + 5*S, cx - 25*S, cy + 20*S], fill="#f472b6")
    draw.ellipse([cx + 25*S, cy + 5*S, cx + 40*S, cy + 20*S], fill="#f472b6")
    draw.rounded_rectangle([cx - 25*S, cy + 30*S, cx + 25*S, cy + 50*S], radius=8*S, fill="#ffffff")
    
    # 3. 🎓 카테고리별 전용 악세사리
    if cat == "Economy":
        draw.polygon([(cx-5*S, cy+55*S), (cx+5*S, cy+55*S), (cx+8*S, cy+80*S), (cx, cy+90*S), (cx-8*S, cy+80*S)], fill="#ef4444")
    elif cat == "Politics":
        draw.rectangle([cx - 35*S, cy - 35*S, cx + 35*S, cy - 5*S], outline="#1e293b", width=4*S)
        draw.line([(cx - 5*S, cy - 20*S), (cx + 5*S, cy - 20*S)], fill="#1e293b", width=4*S)
    elif cat == "Tech":
        draw.line([(cx, cy-70*S), (cx, cy-110*S)], fill="#94a3b8", width=6*S)
        draw.ellipse([(cx-12*S, cy-125*S), (cx+12*S, cy-100*S)], fill="#60a5fa")
    elif cat == "Health":
        draw.rounded_rectangle([cx - 35*S, cy - 95*S, cx + 35*S, cy - 65*S], radius=5*S, fill="#ffffff")
        draw.rectangle([cx - 5*S, cy - 90*S, cx + 5*S, cy - 70*S], fill="#ef4444")
        draw.rectangle([cx - 15*S, cy - 85*S, cx + 15*S, cy - 75*S], fill="#ef4444")
    elif cat == "Energy":
        draw.chord([cx - 55*S, cy - 110*S, cx + 55*S, cy - 30*S], start=180, end=0, fill="#f59e0b")
        draw.line([(cx - 65*S, cy - 70*S), (cx + 65*S, cy - 70*S)], fill="#f59e0b", width=8*S)

    # 4. 👑 VIP 왕관
    if tier == "vip":
        cx_c, cy_c = cx + 25*S, cy - 65*S
        draw.polygon([(cx_c-15*S, cy_c), (cx_c-25*S, cy_c-30*S), (cx_c, cy_c-15*S), 
                      (cx_c+15*S, cy_c-35*S), (cx_c+20*S, cy_c-10*S), (cx_c+35*S, cy_c-25*S), 
                      (cx_c+25*S, cy_c+5*S)], fill="#fde047")

    # 5. 하단 반투명 바
    draw.rectangle([(0, h - 80 * SCALE), (w, h)], fill="#00000040")
    
    # 6. 상단 뱃지
    date_badge = datetime.datetime.utcnow().strftime("%Y. %m. %d")
    date_w = draw.textlength(date_badge, font=fb)
    draw.text((40 * SCALE, 44 * SCALE), date_badge, font=fb, fill="#ffffff80")
    
    cat_w = draw.textlength(cat.upper(), font=fb)
    badge_x = 40 * SCALE + date_w + 30 * SCALE
    draw.rounded_rectangle([(badge_x, 36 * SCALE), (badge_x + cat_w + 60 * SCALE, 86 * SCALE)], radius=25*SCALE, fill="#ffffff")
    draw.text((badge_x + 30 * SCALE, 44 * SCALE), cat.upper(), font=fb, fill="#1e293b")
    
    tl = "VIP" if tier == "vip" else "PRO"
    t_bg = "#b8974d" if tier == "vip" else "#ffffff"
    t_tc = "#ffffff" if tier == "vip" else "#1e293b"
    tier_w = draw.textlength(tl, font=fb)
    draw.rounded_rectangle([(w - 40 * SCALE - tier_w - 60 * SCALE, 36 * SCALE), (w - 40 * SCALE, 86 * SCALE)], radius=25*SCALE, fill=t_bg)
    draw.text((w - 40 * SCALE - tier_w - 30 * SCALE, 44 * SCALE), tl, font=fb, fill=t_tc)
    
    # 7. 타이틀 텍스트 그리기 
    clean_title = _clean_seo_title(title_text).split(':')[0] 
    words = clean_title.upper().split()
    lines, line = [], []
    mw = w - 400 * SCALE 
    for word in words:
        t = " ".join(line + [word])
        try: tw2 = draw.textlength(t, font=ft)
        except: tw2 = len(t) * 40 * SCALE
        if tw2 < mw: line.append(word)
        else:
            if line: lines.append(" ".join(line))
            line = [word]
    if line: lines.append(" ".join(line))
        
    y = 180 * SCALE 
    for i, ln in enumerate(lines[:3]):
        t_color = style["acc"] if i == 1 else "#ffffff" 
        draw.text((40 * SCALE, y), ln, font=ft, fill=t_color)
        try:
            bb = draw.textbbox((0, 0), ln, font=ft)
            y += (bb[3] - bb[1]) + 15 * SCALE
        except: y += 100 * SCALE
            
    # 8. 하단 푸터 텍스트
    draw.text((40 * SCALE, h - 60 * SCALE), "WARM INSIGHT", font=fs, fill="#ffffff")
    tagline = "AI-Driven Global Market Analysis"
    tw = draw.textlength(tagline, font=fs)
    draw.text((w - 40 * SCALE - tw, h - 60 * SCALE), tagline, font=fs, fill="#ffffff")
    
    img = img.convert("RGB")
    img = img.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

# ═══════════════════════════════════════════════
# WORDPRESS PUBLISHER
# ═══════════════════════════════════════════════
def _upload_image(img_bytes, filename):
    try:
        resp = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers={"Content-Disposition": f'attachment; filename="{filename}"',
                     "Content-Type": "image/jpeg"},
            data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30)
        if resp.status_code in (200, 201):
            d = resp.json()
            return d.get("id"), d.get("source_url", "")
    except Exception as e:
        print(f"   ⚠️  Image upload: {e}")
    return None, ""

def _get_category_id(cat_name):
    try:
        resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/categories",
            params={"search": cat_name, "per_page": 10},
            auth=(WP_USER, WP_APP_PASS), timeout=10)
        if resp.status_code == 200:
            for c in resp.json():
                if c["name"].lower() == cat_name.lower():
                    return c["id"]
    except:
        pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, full_raw, faq_schema):
    media_id, img_url = None, ""
    if img_bytes:
        media_id, img_url = _upload_image(img_bytes, f"{slug[:40]}.jpg")
        if media_id:
            print(f"   🖼  Thumbnail uploaded: {img_url}")
            
    seo_title = _clean_seo_title(title)
    full_content = _build_jsonld(title, exc, kw, cat, slug, img_url) + faq_schema + html
    cat_id = _get_category_id(cat)

    post_data = {
        "title": title, 
        "content": full_content, 
        "excerpt": exc,
        "status": "publish", 
        "slug": slug
    }
    if cat_id:
        post_data["categories"] = [cat_id]
    if media_id:
        post_data["featured_media"] = media_id
    if kw:
        post_data["meta"] = {
            "rank_math_title": (seo_title + " | Warm Insight")[:60],
            "rank_math_description": (exc[:120] + f" Expert {cat.lower()} analysis.")[:155],
            "rank_math_focus_keyword": kw,
        }

    delay = random.randint(3, 12)
    print(f"   ⏳ Publish delay: {delay}s …")
    time.sleep(delay)

    for attempt in range(1, 4):
        try:
            resp = requests.post(
                f"{WP_URL}/wp-json/wp/v2/posts", json=post_data,
                auth=(WP_USER, WP_APP_PASS), timeout=30)
            if resp.status_code in (200, 201):
                print(f"   ✅ Published [{tier.upper()}] {title}")
                print(f"      URL: {resp.json().get('link', '')}")
                return True
            if 400 <= resp.status_code < 500:
                print(f"   ❌ Publish failed {resp.status_code}: {resp.text[:300]}")
                return False
            print(f"   ⚠️  {resp.status_code} — retry {attempt}/3")
            time.sleep(15 * attempt)
        except requests.exceptions.Timeout:
            print(f"   ⚠️  Timeout — retry {attempt}/3")
            time.sleep(10)
        except Exception as e:
            print(f"   ❌ {e}")
            return False
    return False

# ═══════════════════════════════════════════════
# NEWS FETCHER
# ═══════════════════════════════════════════════
def fetch_news(cat, max_items=8):
    feeds = RSS_FEEDS.get(cat, RSS_FEEDS["Economy"])
    items = []
    random.shuffle(feeds)
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for entry in d.entries[:3]:
                t = entry.get("title", "").strip()
                s = re.sub(r"<[^>]+>", "", entry.get("summary", entry.get("description", ""))[:250].strip())
                if t: items.append(f"• {t}: {s}")
        except: continue
        if len(items) >= max_items: break
    random.shuffle(items)
    return "\n".join(items[:max_items]) if items else f"Latest {cat} market developments today."

def check_duplicate(title):
    if not title or not WP_USER: return False
    
    search_kw = re.sub(r'\[.*?\]\s*', '', title).strip()[:30]
    
    try:
        resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/posts",
            params={"search": search_kw, "status": "publish,draft", "per_page": 10},
            auth=(WP_USER, WP_APP_PASS), timeout=10)
        
        if resp.status_code == 200:
            for p in resp.json():
                wp_title = p.get("title", {}).get("rendered", "")
                tier_label = title.split(']')[0] + "]" if "]" in title else ""
                if search_kw.lower() in wp_title.lower() and tier_label in wp_title:
                    return True
    except: pass
    return False

# ═══════════════════════════════════════════════
# GEMINI API
# ═══════════════════════════════════════════════
def call_gemini(prompt, retries=3):
    client = _get_gemini_client()
    for attempt in range(retries):
        for model in [MODEL, MODEL_FALLBACK]:
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
                if model != MODEL:
                    print(f"   ℹ️  Used Fallback model: {model}")
                return resp.text or ""
            except Exception as e:
                print(f"   ⚠️ Gemini API error ({model}): {e}")
        if attempt < retries - 1:
            print(f"   ⏳ API overload. Waiting 10s before retry {attempt+1}/{retries}...")
            time.sleep(10)
    print("   ❌ Gemini API failed after all retries.")
    return ""

# ═══════════════════════════════════════════════
# PROMPTS — VIP
# ═══════════════════════════════════════════════
FAQ_TAGS = (
    "<FAQ_1_Q>question</FAQ_1_Q><FAQ_1_A>answer</FAQ_1_A>\n"
    "<FAQ_2_Q>question</FAQ_2_Q><FAQ_2_A>answer</FAQ_2_A>\n"
    "<FAQ_3_Q>question</FAQ_3_Q><FAQ_3_A>answer</FAQ_3_A>"
)

def _make_vip_prompt1(news_text, cat):
    return f"""You are Warm Insight's senior analyst, a 30-year expert who masterfully integrates global macro-economics, humanities, and psychology. Write a VIP deep-dive on {cat} for a universal audience.
Explain complex macro-investment trends clearly, intuitively, and engagingly, so anyone can understand the deeper human and psychological forces driving the market.

You MUST respond using ONLY these XML tags. Fill EVERY tag with substantive, original content.
<TITLE>High-impact headline, no emoji, max 90 chars. Must be specific and attention-grabbing.</TITLE>
<EXCERPT>2-3 sentence teaser, 120-150 chars</EXCERPT>
<SEO_KEYWORD>3-5 word focus keyphrase</SEO_KEYWORD>
<IMPACT_LEVEL>HIGH or MEDIUM or LOW</IMPACT_LEVEL>
<SECTOR_TAG>Short sector label</SECTOR_TAG>
<BIG_NUMBER>A single striking statistic number (e.g. "15" or "$4.2T")</BIG_NUMBER>
<BIG_NUMBER_DESC>1-2 sentences explaining why this number matters to everyday life and the economy</BIG_NUMBER_DESC>
<FEAR_GREED>A number 0-100 representing current market fear(0) vs greed(100)</FEAR_GREED>
<EXECUTIVE_SUMMARY>3-4 sentences: the key thesis and why it matters right now.</EXECUTIVE_SUMMARY>
<PLAIN_ENGLISH>3-4 sentences using a vivid analogy to explain the situation to a non-expert. Make it memorable and relatable. Example: "Think of it like..."</PLAIN_ENGLISH>
<MACRO>2-3 paragraphs. Explain the global context, central bank moves, and supply/demand dynamics through the lens of human behavior and psychology. 300-400 words.</MACRO>
<HERD>1-2 paragraphs: How is the general public (the herd) reacting? What psychological biases are driving their narrative? 150-200 words.</HERD>
<CONTRARIAN>1-2 paragraphs: The contrarian view. What does the smart observer see that the herd misses? 150-200 words.</CONTRARIAN>
<QUICK_FLOW>A chain of cause-and-effect connected by ➡️ arrows. 5-7 steps.</QUICK_FLOW>
<SENTIMENT>BULLISH or BEARISH or NEUTRAL</SENTIMENT>
<BULL_CASE>3-5 sentences: The optimistic outlook with specific catalysts.</BULL_CASE>
<BEAR_CASE>3-5 sentences: The pessimistic outlook with specific risks.</BEAR_CASE>

News inputs:
{news_text[:4000]}

Write with the warm, insightful, and accessible tone of a seasoned mentor advising the general public. No overly dry jargon."""

def _make_vip_prompt2(raw1, cat):
    title = xtag(raw1, "TITLE")
    summary = xtag(raw1, "EXECUTIVE_SUMMARY")[:400]
    sentiment = xtag(raw1, "SENTIMENT")
    return f"""Complete the VIP analysis for: "{title}" ({cat})
Context: {summary}
Sentiment: {sentiment}

Respond with ONLY these XML tags. Fill EVERY tag with substantive content:

<MARKET_1_NAME>S&P 500</MARKET_1_NAME>
<MARKET_1_DIR>UP or DOWN or SIDEWAYS</MARKET_1_DIR>
<MARKET_1_DESC>Short reason, max 50 chars</MARKET_1_DESC>
<MARKET_2_NAME>10Y Yield</MARKET_2_NAME>
<MARKET_2_DIR>UP or DOWN or SIDEWAYS</MARKET_2_DIR>
<MARKET_2_DESC>Short reason</MARKET_2_DESC>
<MARKET_3_NAME>US Dollar</MARKET_3_NAME>
<MARKET_3_DIR>UP or DOWN or SIDEWAYS</MARKET_3_DIR>
<MARKET_3_DESC>Short reason</MARKET_3_DESC>
<MARKET_4_NAME>Relevant commodity for {cat}</MARKET_4_NAME>
<MARKET_4_DIR>UP or DOWN or SIDEWAYS</MARKET_4_DIR>
<MARKET_4_DESC>Short reason</MARKET_4_DESC>

<IND_1_NAME>Key indicator name</IND_1_NAME>
<IND_1_PCT>Number 0-100</IND_1_PCT>
<IND_2_NAME>Second indicator</IND_2_NAME>
<IND_2_PCT>Number 0-100</IND_2_PCT>
<IND_3_NAME>Third indicator</IND_3_NAME>
<IND_3_PCT>Number 0-100</IND_3_PCT>

<SECTOR_1_NAME>Relevant sector ETF/index</SECTOR_1_NAME>
<SECTOR_1_SENT>BULLISH or BEARISH or NEUTRAL</SECTOR_1_SENT>
<SECTOR_1_DESC>1 sentence why</SECTOR_1_DESC>
<SECTOR_2_NAME>Second sector</SECTOR_2_NAME>
<SECTOR_2_SENT>BULLISH or BEARISH or NEUTRAL</SECTOR_2_SENT>
<SECTOR_2_DESC>1 sentence why</SECTOR_2_DESC>
<SECTOR_3_NAME>Third sector</SECTOR_3_NAME>
<SECTOR_3_SENT>BULLISH or BEARISH or NEUTRAL</SECTOR_3_SENT>
<SECTOR_3_DESC>1 sentence why</SECTOR_3_DESC>
<SECTOR_4_NAME>Fourth sector</SECTOR_4_NAME>
<SECTOR_4_SENT>BULLISH or BEARISH or NEUTRAL</SECTOR_4_SENT>
<SECTOR_4_DESC>1 sentence why</SECTOR_4_DESC>

<TECHNICAL_SIGNALS>1-2 paragraphs: Key technical levels, support/resistance, chart patterns for relevant ETFs/indices. Mention specific price levels. 150-200 words.</TECHNICAL_SIGNALS>
<MACRO_FLOWS>1-2 paragraphs: Global capital flows, yield curves, credit conditions, currency dynamics. 150-200 words.</MACRO_FLOWS>
<SMART_MONEY>1-2 paragraphs: How are institutional investors, hedge funds, sovereign wealth funds positioning? 150-200 words.</SMART_MONEY>

<TITANS_TITLE>A compelling title for the playbook section</TITANS_TITLE>
<TITANS_BODY>2-3 paragraphs: Deep strategic analysis connecting all threads. What is the meta-narrative? 200-300 words.</TITANS_BODY>

<ACTION_ITEMS>3-5 concrete investor action items as HTML: <ul><li>specific actionable steps with ticker symbols and ETF names</li></ul></ACTION_ITEMS>
<TW>One memorable market wisdom sentence</TW>
<PS>Compelling one-line P.S. from a veteran investor perspective</PS>
{FAQ_TAGS}"""

# ═══════════════════════════════════════════════
# PROMPTS — PREMIUM
# ═══════════════════════════════════════════════
def _make_premium_prompt(news_text, cat):
    return f"""You are Warm Insight's senior analyst, a 30-year expert blending global economics, humanities, and psychology. Write a Premium newsletter article on {cat} for a universal audience.
Respond ONLY using these XML tags. Fill EVERY tag with substantive, original content:

<TITLE>Compelling headline, no emoji, max 80 chars. Specific and attention-grabbing.</TITLE>
<EXCERPT>2-3 sentence SEO summary, 120-150 chars</EXCERPT>
<SEO_KEYWORD>3-5 word focus keyphrase</SEO_KEYWORD>
<IMPACT_LEVEL>HIGH or MEDIUM or LOW</IMPACT_LEVEL>
<SECTOR_TAG>Short sector label</SECTOR_TAG>
<EXECUTIVE_SUMMARY>2-3 sentences capturing the key insight simply and powerfully</EXECUTIVE_SUMMARY>
<KEY_TAKEAWAY>The single most important lesson the reader should take away. 2-3 sentences. Actionable and specific.</KEY_TAKEAWAY>
<LEAD>Strong opening paragraph hooking the reader, using human psychology or a compelling stat to draw them in.</LEAD>
<BODY>3-4 paragraphs of analysis using HTML: h2, p, strong, ul/li. 600-800 words total. Break down complex trends into intuitive, everyday concepts. End with an actionable outlook.</BODY>
<SENTIMENT>BULLISH or BEARISH or NEUTRAL</SENTIMENT>
<TW>One memorable market wisdom sentence focusing on investor psychology</TW>
<PS>One-line P.S. from a veteran mentor's perspective</PS>
{FAQ_TAGS}

News inputs:
{news_text[:3000]}

Tone: Insightful, empathetic, intuitive, and highly accessible to the general public. No generic filler text."""

# ═══════════════════════════════════════════════
# PIPELINE & RUNNER
# ═══════════════════════════════════════════════
def get_current_task():
    now = datetime.datetime.utcnow()
    total_blocks = (now.timetuple().tm_yday * 8) + (now.hour // 3)
    return CATEGORIES[total_blocks % len(CATEGORIES)]

def _run_single(cat, tier, news):
    print(f"\n{'─'*44}")
    print(f"📌 {cat} | {tier.upper()}")
    print(f"{'─'*44}")

    raw1, raw2 = "", ""
    if tier == "vip":
        print("   🤖 VIP Part 1 …")
        raw1 = call_gemini(_make_vip_prompt1(news, cat))
        if not raw1:
            print("   ❌ VIP Part 1 empty — skipping")
            return False
        print("   🤖 VIP Part 2 …")
        raw2 = call_gemini(_make_vip_prompt2(raw1, cat))
        if not raw2:
            print("   ❌ VIP Part 2 empty — skipping")
            return False
    else:
        print("   🤖 Premium generation …")
        raw1 = call_gemini(_make_premium_prompt(news, cat))
        if not raw1:
            print("   ❌ Premium generation empty — skipping")
            return False

    title, html, exc, kw, slug, tier_out, full_raw, faq_schema = analyze(raw1, raw2, cat, tier)
    print(f"   📝 {title}")

    if check_duplicate(title):
        print("   ⚠️  Duplicate — skipping")
        return False

    print("   🖌  Generating thumbnail …")
    img_bytes = make_thumbnail(title, cat, tier)
    
    return publish(title, html, exc, kw, cat, slug, tier, img_bytes, full_raw, faq_schema)

def run_pipeline():
    cat = get_current_task()
    now = datetime.datetime.utcnow()
    print(f"\n{'═'*54}")
    print(f"🚀 Warm Insight v29 | {cat} | VIP + Pro | {now:%H:%M} UTC")
    print(f"{'═'*54}")

    if not check_env_vars():
        print("🛑 Aborting — set missing GitHub Secrets.")
        return
    if not verify_wp_credentials():
        print("🛑 Aborting — fix WordPress credentials.")
        return

    # 뉴스 1회 수집 → VIP & Premium 공유
    news = fetch_news(cat)
    print(f"📰 News fetched ({len(news.splitlines())} items)")

    # 1) VIP 발행
    ok_vip = _run_single(cat, "vip", news)

    # VIP → Premium 간격 대기 (워드프레스 서버 부하 방지)
    gap = random.randint(20, 40)
    print(f"\n⏳ Waiting {gap}s before Premium …")
    time.sleep(gap)

    # 2) Premium 발행
    ok_pre = _run_single(cat, "premium", news)

    # 결과 요약
    print(f"\n{'═'*54}")
    print(f"📊 Results — {cat} ({now:%H:%M} UTC)")
    print(f"   VIP:     {'✅ OK' if ok_vip else '❌ FAIL'}")
    print(f"   Premium: {'✅ OK' if ok_pre else '❌ FAIL'}")
    print(f"{'═'*54}")

if __name__ == "__main__":
    run_pipeline()
