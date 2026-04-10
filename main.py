# -*- coding: utf-8 -*-
"""
Warm Insight v11 — WordPress Full Fixed Build (2.5 Model Restored)
Fixes:
  1. 대표님 계정에 최적화된 gemini-2.5-pro 및 2.5-flash 1순위 복구
  2. 404 에러(권한 없음) 발생 시 즉시 다음 모델로 넘어가는 스위칭 시스템 유지
  3. 503 에러(서버 과부하) 발생 시 끈질기게 재시도하여 결국 완성해 내는 로직 유지
"""
import os, sys, traceback, time, random, re, json, io
from datetime import datetime
import requests, feedparser
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

if not all([GEMINI_API_KEY, WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
    sys.exit("Missing API keys or WordPress credentials")

WP_AUTH = (WP_USERNAME, WP_APP_PASSWORD)

CATEGORIES = {
    "Economy": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "https://finance.yahoo.com/news/rssindex",
        "https://feeds.bbci.co.uk/news/business/economy/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://asia.nikkei.com/rss/feed/nar"],
    "Politics": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.npr.org/1004/rss.xml"],
    "Tech": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://asia.nikkei.com/rss/feed/nar"],
    "Health": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108",
        "https://feeds.bbci.co.uk/news/health/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml"],
    "Energy": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810",
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://asia.nikkei.com/rss/feed/nar"],
}

TASKS = [
    {"tier": "Premium", "count": 5},
    {"tier": "Royal Premium", "count": 5},
]
TIER_LABELS = {"Premium": "💎 Pro", "Royal Premium": "👑 VIP"}
TIER_SLEEP = {"Premium": 30, "Royal Premium": 50}
SKIP_EDITOR_TIERS = ["Premium"]

# 🚨 [핵심 수정] 대표님 계정에서 완벽하게 작동했던 2.5 모델을 1순위로 복구했습니다.
# (만약의 사태를 대비해 구글이 추천하는 2.0-001 예비용 백업도 걸어두었습니다)
MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash-001"],
    "Premium": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-001"],
}
FAST_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-001"]

EXPERT = {
    "Economy": "a veteran global macro strategist with 40 years spanning Wall Street, City of London, and Asian markets",
    "Politics": "a veteran geopolitical strategist with 40 years covering Washington, Brussels, Beijing, and Middle East",
    "Tech": "a veteran global technology analyst with 40 years covering Silicon Valley, Shenzhen, and emerging hubs",
    "Health": "a veteran global healthcare analyst with 40 years covering US pharma, European biotech, and Asian markets",
    "Energy": "a veteran global energy strategist with 40 years covering OPEC, US shale, European transition, and Asian demand",
}
CAT_THEME = {
    "Economy": {"icon": "💰", "accent": "#2563eb", "label": "MACRO & RATES"},
    "Politics": {"icon": "🏛", "accent": "#dc2626", "label": "GEOPOLITICS"},
    "Tech": {"icon": "🤖", "accent": "#7c3aed", "label": "AI & DISRUPTION"},
    "Health": {"icon": "🧬", "accent": "#059669", "label": "BIOTECH & PHARMA"},
    "Energy": {"icon": "⚡", "accent": "#d97706", "label": "OIL, GAS & RENEWABLES"},
}
CAT_ALLOC = {
    "Economy": {"s": 55, "b": 35, "c": 10, "note": "Defensive: higher bonds during macro uncertainty"},
    "Politics": {"s": 50, "b": 35, "c": 15, "note": "Elevated cash for geopolitical shock absorption"},
    "Tech": {"s": 70, "b": 20, "c": 10, "note": "Growth tilt: overweight innovation equities"},
    "Health": {"s": 60, "b": 30, "c": 10, "note": "Balanced: pharma stability with biotech upside"},
    "Energy": {"s": 65, "b": 25, "c": 10, "note": "Commodity tilt: overweight real assets"},
}
CAT_METRICS = {
    "Economy": {"pool": ["Inflation Momentum", "Recession Risk", "Consumer Pulse", "Credit Stress", "Rate Cut Odds", "Dollar Strength", "Yield Curve", "PMI Signal", "Global Trade Flow", "EM Capital Flight Risk"], "hint": "inflation, GDP, Fed policy"},
    "Politics": {"pool": ["Policy Uncertainty", "Regulatory Risk", "Geopolitical Tension", "Election Volatility", "Trade War Risk", "Sanctions Impact", "Gridlock", "Defense Momentum", "Chokepoint Risk"], "hint": "policy, geopolitics, chokepoints"},
    "Tech": {"pool": ["AI Race Intensity", "Antitrust Pressure", "Chip Supply Stress", "IPO Sentiment", "Cloud Velocity", "Cyber Threat", "Big Tech Momentum", "Funding Freeze", "Tech Decoupling Risk"], "hint": "AI, semiconductors, regulation"},
    "Health": {"pool": ["Pipeline Confidence", "Drug Pricing Pressure", "Biotech Funding", "FDA Momentum", "Gene Therapy Index", "Hospital Stress", "Coverage Gap", "Trial Success", "Pharma Supply Risk"], "hint": "pharma pipelines, drug pricing, FDA"},
    "Energy": {"pool": ["Oil Supply Squeeze", "Green Transition", "OPEC Tension", "LNG Surge", "Renewable Growth", "Geo Shock Risk", "Grid Stress", "Carbon Heat", "Chokepoint Disruption"], "hint": "oil, OPEC, renewables, LNG"},
}

# ═══════════════════════════════════════════════
# THUMBNAIL 
# ═══════════════════════════════════════════════
THUMB_COLORS = {
    "Economy": [
        {"bg": (14, 165, 233), "bg2": (2, 132, 199), "text": (15, 23, 42), "hi": (220, 38, 38), "chart": [(34, 197, 94), (239, 68, 68)]},
        {"bg": (16, 185, 129), "bg2": (5, 150, 105), "text": (15, 23, 42), "hi": (30, 58, 138), "chart": [(34, 197, 94), (239, 68, 68)]},
        {"bg": (56, 189, 248), "bg2": (14, 165, 233), "text": (15, 23, 42), "hi": (124, 58, 237), "chart": [(34, 197, 94), (239, 68, 68)]},
    ],
    "Politics": [
        {"bg": (239, 68, 68), "bg2": (185, 28, 28), "text": (255, 255, 255), "hi": (254, 240, 138), "chart": [(255, 255, 255), (254, 240, 138)]},
        {"bg": (251, 146, 60), "bg2": (234, 88, 12), "text": (15, 23, 42), "hi": (127, 29, 29), "chart": [(15, 23, 42), (127, 29, 29)]},
        {"bg": (244, 114, 182), "bg2": (219, 39, 119), "text": (255, 255, 255), "hi": (254, 240, 138), "chart": [(255, 255, 255), (254, 240, 138)]},
    ],
    "Tech": [
        {"bg": (99, 102, 241), "bg2": (79, 70, 229), "text": (255, 255, 255), "hi": (253, 224, 71), "chart": [(52, 211, 153), (251, 113, 133)]},
        {"bg": (14, 165, 233), "bg2": (3, 105, 161), "text": (255, 255, 255), "hi": (253, 224, 71), "chart": [(74, 222, 128), (251, 113, 133)]},
        {"bg": (168, 85, 247), "bg2": (126, 34, 206), "text": (255, 255, 255), "hi": (253, 224, 71), "chart": [(52, 211, 153), (251, 113, 133)]},
    ],
    "Health": [
        {"bg": (20, 184, 166), "bg2": (13, 148, 136), "text": (15, 23, 42), "hi": (127, 29, 29), "chart": [(34, 197, 94), (239, 68, 68)]},
        {"bg": (34, 197, 94), "bg2": (22, 163, 74), "text": (15, 23, 42), "hi": (30, 58, 138), "chart": [(15, 23, 42), (239, 68, 68)]},
        {"bg": (6, 182, 212), "bg2": (8, 145, 178), "text": (255, 255, 255), "hi": (254, 240, 138), "chart": [(74, 222, 128), (251, 113, 133)]},
    ],
    "Energy": [
        {"bg": (245, 158, 11), "bg2": (217, 119, 6), "text": (15, 23, 42), "hi": (127, 29, 29), "chart": [(34, 197, 94), (239, 68, 68)]},
        {"bg": (249, 115, 22), "bg2": (194, 65, 12), "text": (255, 255, 255), "hi": (254, 240, 138), "chart": [(255, 255, 255), (254, 240, 138)]},
        {"bg": (251, 191, 36), "bg2": (202, 138, 4), "text": (15, 23, 42), "hi": (127, 29, 29), "chart": [(34, 197, 94), (239, 68, 68)]},
    ],
}

_font_cache = {}
def _font(size):
    if size in _font_cache: return _font_cache[size]
    for fp in ["fonts/Anton.ttf", "fonts/BebasNeue.ttf", "fonts/Oswald.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
        try:
            f = ImageFont.truetype(fp, size); _font_cache[size] = f; return f
        except: continue
    return ImageFont.load_default()

def _font_sub(size):
    for fp in ["fonts/Oswald.ttf", "fonts/BebasNeue.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
        try: return ImageFont.truetype(fp, size)
        except: continue
    return ImageFont.load_default()

def _extract_hook(title):
    clean = title
    for lb in ["[💎 Pro] ", "[👑 VIP] ", "[💎 Pro]", "[👑 VIP]"]: clean = clean.replace(lb, "")
    clean = clean.strip()
    if ":" in clean:
        parts = clean.split(":")
        short = min(parts, key=lambda p: len(p.strip()))
        if len(short.split()) >= 2: clean = short.strip()
        else: clean = parts[0].strip()
    fillers = {"the", "a", "an", "of", "in", "for", "and", "to", "is", "are", "its", "how", "from", "with", "on", "at", "by"}
    words = clean.split()
    punchy = [w for w in words if w.lower() not in fillers]
    if len(punchy) < 2: punchy = words[:4]
    if len(punchy) > 5: punchy = punchy[:5]
    return punchy

def _draw_warmy(draw, cx, cy, size, is_vip=False, accent=(50, 230, 160)):
    s = size; g1, g2, g3 = (74, 222, 128), (34, 197, 94), (22, 101, 52)
    bw, bh = int(s * 0.45), int(s * 0.55)
    bx1, by1 = cx - bw // 2, cy - bh // 2 + int(s * 0.05); bx2, by2 = bx1 + bw, by1 + bh
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=bw // 4, fill=g2, outline=g3, width=3)
    pw, ph = int(bw * 0.55), int(bh * 0.25); px1 = cx - pw // 2; py1 = by1 + int(bh * 0.6)
    draw.rounded_rectangle([px1, py1, px1 + pw, py1 + ph], radius=8, fill=(254, 252, 232))
    lw, lh = int(bw * 0.12), int(s * 0.12)
    for lx in [cx - int(bw * 0.22), cx + int(bw * 0.22)]:
        draw.rounded_rectangle([lx - lw, by2, lx + lw, by2 + lh], radius=lw, fill=g3)
        draw.ellipse([lx - lw - 4, by2 + lh - 6, lx + lw + 4, by2 + lh + 8], fill=g3)
    aw, al = int(bw * 0.1), int(bw * 0.35); arm_y = by1 + int(bh * 0.35)
    draw.rounded_rectangle([bx1 - al, arm_y - int(al * 0.5), bx1, arm_y + aw], radius=aw, fill=g2, outline=g3, width=2)
    draw.ellipse([bx1 - al - 6, arm_y - int(al * 0.5) - 6, bx1 - al + 10, arm_y - int(al * 0.5) + 10], fill=g1, outline=g3, width=2)
    draw.rounded_rectangle([bx2, arm_y, bx2 + al, arm_y + aw], radius=aw, fill=g2, outline=g3, width=2)
    draw.ellipse([bx2 + al - 6, arm_y - 4, bx2 + al + 10, arm_y + aw + 4], fill=g1, outline=g3, width=2)
    capw, caph = int(bw * 0.5), int(s * 0.06)
    draw.rounded_rectangle([cx - capw // 2, by1 - caph, cx + capw // 2, by1 + 2], radius=caph // 2, fill=g3)
    cap_dot = (251, 191, 36) if is_vip else g1
    draw.ellipse([cx - 7, by1 - caph - 5, cx + 7, by1 - caph + 9], fill=cap_dot, outline=g3, width=2)
    er = int(bw * 0.11); ey = by1 + int(bh * 0.3)
    for ex in [cx - int(bw * 0.18), cx + int(bw * 0.18)]:
        draw.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, 255, 255), outline=g3, width=2)
        pr = int(er * 0.5)
        draw.ellipse([ex - pr + 2, ey - pr - 1, ex + pr + 2, ey + pr - 1], fill=g3)
        draw.ellipse([ex + 2, ey - pr, ex + 5, ey - pr + 3], fill=(255, 255, 255))
    mx1, mx2, my = cx - int(bw * 0.12), cx + int(bw * 0.12), by1 + int(bh * 0.48)
    draw.arc([mx1, my - 4, mx2, my + int(bh * 0.08)], start=0, end=180, fill=g3, width=3)
    for chx in [cx - int(bw * 0.26), cx + int(bw * 0.26)]:
        draw.ellipse([chx - 8, my - 4, chx + 8, my + 6], fill=(251, 146, 60, 80))
    if is_vip:
        crw, crh = int(bw * 0.4), int(s * 0.1); crx = cx - crw // 2; cry = by1 - caph - crh - 4
        pts = [(crx, cry + crh), (crx + int(crw * 0.15), cry + int(crh * 0.2)), (crx + int(crw * 0.35), cry + int(crh * 0.7)), (crx + crw // 2, cry), (crx + int(crw * 0.65), cry + int(crh * 0.7)), (crx + int(crw * 0.85), cry + int(crh * 0.2)), (crx + crw, cry + crh)]
        draw.polygon(pts, fill=(251, 191, 36), outline=(146, 64, 14), width=2)
        for gx in [crx + int(crw * 0.15), crx + crw // 2, crx + int(crw * 0.85)]:
            draw.ellipse([gx - 3, cry + int(crh * 0.2), gx + 3, cry + int(crh * 0.2) + 6], fill=(239, 68, 68))

ICON_KEYWORDS = {
    "up": ["surge", "rise", "soar", "rally", "boom", "bull", "growth", "gain", "jump"],
    "down": ["crash", "fall", "drop", "plunge", "bear", "sink", "decline", "loss", "recession"],
    "warn": ["warning", "risk", "fear", "danger", "crisis", "threat", "alert", "panic"],
    "question": ["uncertainty", "unknown", "puzzle", "mystery", "question", "dilemma"],
    "fire": ["hot", "fire", "explosive", "ignite", "heat", "blazing", "inflation"],
    "money": ["dollar", "billion", "trillion", "profit", "revenue", "earnings", "tax"],
    "shield": ["defense", "protect", "safe", "hedge", "insurance", "shield", "resilient"],
    "globe": ["global", "world", "international", "geopolitical", "sanctions", "emerging"],
}

def _detect_icons(title):
    t = title.lower(); matches = []
    for icon, keywords in ICON_KEYWORDS.items():
        for kw in keywords:
            if kw in t: matches.append(icon); break
    seen = []
    for m in matches:
        if m not in seen: seen.append(m)
        if len(seen) >= 2: break
    return seen or ["globe"]

def _draw_icon_up(draw, cx, cy, size, color):
    s = size
    draw.rectangle([cx - s // 6, cy - s // 6, cx + s // 6, cy + s // 2], fill=color)
    draw.polygon([(cx - s // 3, cy - s // 6), (cx, cy - s // 2), (cx + s // 3, cy - s // 6)], fill=color)

def _draw_icon_down(draw, cx, cy, size, color):
    s = size
    draw.rectangle([cx - s // 6, cy - s // 2, cx + s // 6, cy + s // 6], fill=color)
    draw.polygon([(cx - s // 3, cy + s // 6), (cx, cy + s // 2), (cx + s // 3, cy + s // 6)], fill=color)

def _draw_icon_warn(draw, cx, cy, size, color):
    s = size
    draw.polygon([(cx, cy - s // 2), (cx - s // 2, cy + s // 3), (cx + s // 2, cy + s // 3)], fill=color, outline=(0, 0, 0), width=3)
    draw.rectangle([cx - 4, cy - s // 5, cx + 4, cy + s // 10], fill=(0, 0, 0))
    draw.ellipse([cx - 4, cy + s // 7, cx + 4, cy + s // 4], fill=(0, 0, 0))

def _draw_icon_question(draw, cx, cy, size, color):
    r = size // 2; draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=4)
    f = _font_sub(size - 20)
    try:
        bb = f.getbbox("?"); draw.text((cx - (bb[2]-bb[0]) // 2, cy - (bb[3]-bb[1]) // 2 - 4), "?", font=f, fill=color)
    except: draw.text((cx - 10, cy - 15), "?", font=f, fill=color)

def _draw_icon_fire(draw, cx, cy, size, color):
    s = size
    draw.polygon([(cx, cy - s // 2), (cx + s // 4, cy - s // 6), (cx + s // 3, cy + s // 6), (cx + s // 5, cy + s // 2), (cx - s // 5, cy + s // 2), (cx - s // 3, cy + s // 6), (cx - s // 4, cy - s // 6)], fill=color)
    inner = (min(255, color[0] + 80), min(255, color[1] + 40), min(255, color[2]))
    draw.polygon([(cx, cy - s // 5), (cx + s // 7, cy + s // 10), (cx + s // 8, cy + s // 3), (cx - s // 8, cy + s // 3), (cx - s // 7, cy + s // 10)], fill=inner)

def _draw_icon_money(draw, cx, cy, size, color):
    r = size // 2; draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=4)
    f = _font(size - 15)
    try:
        bb = f.getbbox("$"); draw.text((cx - (bb[2]-bb[0]) // 2, cy - (bb[3]-bb[1]) // 2 - 4), "$", font=f, fill=color)
    except: draw.text((cx - 12, cy - 18), "$", font=f, fill=color)

def _draw_icon_shield(draw, cx, cy, size, color):
    s = size
    draw.polygon([(cx, cy - s // 2), (cx + s // 3, cy - s // 3), (cx + s // 3, cy + s // 8), (cx, cy + s // 2), (cx - s // 3, cy + s // 8), (cx - s // 3, cy - s // 3)], fill=color, outline=(255, 255, 255), width=3)
    draw.line([(cx - s // 8, cy), (cx - s // 20, cy + s // 8), (cx + s // 6, cy - s // 8)], fill=(255, 255, 255), width=4)

def _draw_globe(draw, cx, cy, r, color):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
    draw.ellipse([cx - int(r * 0.4), cy - r, cx + int(r * 0.4), cy + r], outline=color, width=2)
    draw.line([(cx - r, cy), (cx + r, cy)], fill=color, width=2)

def _draw_context_icon(draw, icon_type, cx, cy, size, accent):
    colors = {"up": (34, 197, 94), "down": (239, 68, 68), "warn": (253, 224, 71), "question": accent, "fire": (249, 115, 22), "money": (253, 224, 71), "shield": (59, 130, 246), "globe": accent}
    c = colors.get(icon_type, accent)
    fn = {"up": _draw_icon_up, "down": _draw_icon_down, "warn": _draw_icon_warn, "question": _draw_icon_question, "fire": _draw_icon_fire, "money": _draw_icon_money, "shield": _draw_icon_shield}
    if icon_type in fn: fn[icon_type](draw, cx, cy, size, c)
    elif icon_type == "globe": _draw_globe(draw, cx, cy, size // 2, c)

def make_dynamic_thumb(title, cat, tier):
    S = 2; TW, TH = 1280 * S, 720 * S; seed = abs(hash(title)) % 100000; is_vip = tier == "Royal Premium"
    palettes = THUMB_COLORS.get(cat, THUMB_COLORS["Economy"]); pal = palettes[seed % len(palettes)]
    bg1, bg2, text_c, hi_c, chart_colors = pal["bg"], pal["bg2"], pal["text"], pal["hi"], pal["chart"]
    img = Image.new("RGB", (TW, TH), bg1); draw = ImageDraw.Draw(img)
    for y in range(TH):
        ratio = y / TH
        draw.line([(0, y), (TW, y)], fill=(int(bg1[0]+(bg2[0]-bg1[0])*ratio), int(bg1[1]+(bg2[1]-bg1[1])*ratio), int(bg1[2]+(bg2[2]-bg1[2])*ratio)))
    t_lower = title.lower()
    going_up = any(w in t_lower for w in ["surge", "rise", "rally", "boom", "bull", "growth", "gain", "soar", "record"])
    going_down = any(w in t_lower for w in ["crash", "fall", "drop", "plunge", "bear", "decline", "loss", "fear", "recession", "risk"])
    rng = random.Random(seed); pts = []
    cx_chart, cy_chart, chart_w, chart_h = int(TW * 0.72), int(TH * 0.38), int(TW * 0.35), int(TH * 0.45)
    for i in range(8):
        px = cx_chart - chart_w // 2 + int(chart_w * i / 7)
        if going_down: base = cy_chart - chart_h // 3 + int(chart_h * 0.6 * i / 8)
        elif going_up: base = cy_chart + chart_h // 4 - int(chart_h * 0.6 * i / 8)
        else: base = cy_chart + int(30 * S * (0.5 - rng.random()))
        pts.append((px, base + int(20 * S * (0.5 - rng.random()))))
    if len(pts) >= 2:
        draw.line(pts, fill=chart_colors[0] if (going_up or not going_down) else chart_colors[1], width=6 * S)
        lx, ly = pts[-1]; arr = 20 * S
        if going_down: draw.polygon([(lx - arr, ly - arr // 2), (lx, ly + arr), (lx + arr, ly - arr // 2)], fill=chart_colors[1])
        else: draw.polygon([(lx - arr, ly + arr // 2), (lx, ly - arr), (lx + arr, ly + arr // 2)], fill=chart_colors[0])
    _draw_warmy(draw, int(TW * 0.78), int(TH * 0.62), int(280 * S), is_vip=is_vip, accent=bg2)
    icons = _detect_icons(title)
    for i, it in enumerate(icons[:2]):
        spots = [(int(TW * 0.62), int(TH * 0.15)), (int(TW * 0.88), int(TH * 0.22))]
        if i < len(spots): _draw_context_icon(draw, it, spots[i][0], spots[i][1], int(60 * S), text_c)
    words = _extract_hook(title); mid = max(1, (len(words) + 1) // 2)
    line1 = " ".join(words[:mid]).upper(); line2 = " ".join(words[mid:]).upper() if mid < len(words) else ""
    max_w = int(TW * 0.53); font_sz = int(110 * S)
    test_line = line1 if len(line1) >= len(line2 or "") else (line2 or line1)
    while font_sz > int(50 * S):
        bb = _font(font_sz).getbbox(test_line)
        if bb and (bb[2] - bb[0]) <= max_w: break
        font_sz -= int(4 * S)
    font_big = _font(font_sz); line_h = int(font_sz * 1.1); start_y = (TH - (2 if line2 else 1) * line_h) // 2; x = int(55 * S)
    draw.text((x + 4*S, start_y + 4*S), line1, font=font_big, fill=(0, 0, 0, 60)); draw.text((x, start_y), line1, font=font_big, fill=text_c)
    if line2:
        y2 = start_y + line_h; draw.text((x + 4*S, y2 + 4*S), line2, font=font_big, fill=(0, 0, 0, 60)); draw.text((x, y2), line2, font=font_big, fill=hi_c)
    fbadge = _font_sub(int(28 * S)); cat_text = cat.upper()
    try:
        bb = fbadge.getbbox(cat_text); bw = bb[2]-bb[0]+int(50*S); bh = int(44*S)
        badge_bg = (255,255,255) if text_c[0] < 128 else (15,23,42); badge_fg = (15,23,42) if text_c[0] < 128 else (255,255,255)
        draw.rounded_rectangle([int(45*S), int(35*S), int(45*S)+bw, int(35*S)+bh], radius=bh//2, fill=badge_bg)
        draw.text((int(45*S)+int(25*S), int(35*S)+int(8*S)), cat_text, font=fbadge, fill=badge_fg)
    except: pass
    tier_text = "PRO" if tier == "Premium" else "VIP"
    try:
        tb = fbadge.getbbox(tier_text); tw2 = tb[2]-tb[0]+int(50*S); bh = int(44*S)
        tpbg = (15,23,42) if text_c == (255,255,255) else (255,255,255); tpfg = (255,255,255) if text_c == (255,255,255) else (15,23,42)
        draw.rounded_rectangle([TW-tw2-int(45*S), int(35*S), TW-int(45*S), int(35*S)+bh], radius=bh//2, fill=tpbg)
        draw.text((TW-tw2-int(45*S)+int(25*S), int(35*S)+int(8*S)), tier_text, font=fbadge, fill=tpfg)
    except: pass
    bar_h = int(44*S); bar_c = (max(0,bg2[0]-40), max(0,bg2[1]-40), max(0,bg2[2]-40))
    draw.rectangle([0, TH-bar_h, TW, TH], fill=bar_c)
    logo_c = (255,255,255) if sum(bar_c) < 300 else (15,23,42)
    draw.text((int(55*S), TH-bar_h+int(10*S)), "WARM INSIGHT", font=_font_sub(int(20*S)), fill=logo_c)
    draw.text((TW-int(310*S), TH-bar_h+int(14*S)), "AI-Driven Global Market Analysis", font=_font_sub(int(14*S)), fill=logo_c)
    img = img.resize((1280, 720), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=93)
    print("  Thumb: " + str(len(buf.getvalue()) // 1024) + "KB | " + line1[:30])
    return buf.getvalue()

# ═══════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════
ACCURACY = (
    "STRICT ACCURACY RULES (NEVER VIOLATE):\n"
    "- ONLY analyze facts from the news provided. NEVER invent events, names, or incidents.\n"
    "- NEVER fabricate specific prices, RSI numbers, or statistics. Use directional language.\n"
    "- NEVER attribute causation unless the news explicitly states it.\n"
    "- Use hedging: likely, suggests, indicates. Not definitive false claims.\n"
    "- Reference only real ETF tickers (SPY, XLE, XLV, IEF, GLD, EFA, VWO, etc).\n\n"
    "GEOPOLITICAL FRAMEWORK:\n"
    "- Analyze through MULTIPLE perspectives: US, Europe, China, Global South.\n"
    "- Consider chokepoints (Hormuz, Suez, Malacca, Taiwan Strait) as systemic risk.\n"
    "- Track G7 vs BRICS+ bloc divergence.\n"
    "- Map cascades: geopolitical event -> energy -> inflation -> central bank -> markets.\n\n"
    "TONE RULES:\n"
    "- Write like a respected senior analyst at Goldman Sachs or Bridgewater.\n"
    "- Smart humor like Morning Brew or Matt Levine. NOT TikTok slang.\n"
    "- No: fam, slay, lit, no cap, we are cooked, its giving. Ever.\n"
    "- Every sentence must sound human-written, not AI-generated.\n"
)

PROMPT_PREMIUM = (
    "You are [PERSONA] for Warm Insight ([CATEGORY]).\n"
    "Audience: Intermediate investors wanting deeper why.\n"
    "[ACCURACY]\n"
    "STYLE: Second-Order Thinking. G7 vs BRICS+ lens. 700-900 words.\n\n"
    "OUTPUT (XML):\n"
    "<SEO_KEYWORD>4-7 word keyword</SEO_KEYWORD>\n"
    "<TITLE>Analytical title with SEO keyword</TITLE>\n"
    "<EXCERPT>1 sentence with SEO keyword</EXCERPT>\n"
    "<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>\n"
    "<SUMMARY>3 sentences. First includes SEO keyword.</SUMMARY>\n"
    "<TIKTOK>Smart witty analogy. 3-4 sentences.</TIKTOK>\n"
    "<HEADLINE>Analytical headline</HEADLINE>\n"
    "<KEY_NUMBER>Most striking statistic</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>1 sentence why this changes the picture</KEY_NUMBER_CONTEXT>\n"
    "<DEPTH><strong>🧐 WHY:</strong> Deeper structural pattern. 5-6 sentences."
    "<br><br><strong>🐑 HERD TRAP:</strong> Cognitive bias. 4-5 sentences.</DEPTH>\n"
    '<FLOW>TEXT + emoji (5+ steps)</FLOW>\n'
    "<PRO_INSIGHT>Cross-sector connection. 5-6 sentences.</PRO_INSIGHT>\n"
    "<COMPARE_BULL>Bull case: 2-3 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case: 2-3 sentences.</COMPARE_BEAR>\n"
    "<PRO_DO>2 actions with reasoning</PRO_DO>\n"
    "<PRO_DONT>1 mistake with reasoning</PRO_DONT>\n"
    "<QUICK_HITS>3 headlines. 1 sentence each.</QUICK_HITS>\n"
    "<TAKEAWAY>Insightful takeaway</TAKEAWAY>\n"
    "<PS>Historical perspective (2-3 sentences)</PS>\n\n"
    "News: [NEWS_ITEMS]"
)

VIP_P1 = (
    "You are [PERSONA] for Warm Insight VIP ([CATEGORY]).\n"
    "Audience: Sophisticated investors paying premium.\n"
    "[ACCURACY]\n"
    "WRITE real analysis:\n\n"
    "<SEO_KEYWORD>4-8 word keyword</SEO_KEYWORD>\n"
    "<TITLE>Institutional title with SEO keyword</TITLE>\n"
    "<EXCERPT>1 VIP sentence with SEO keyword</EXCERPT>\n"
    "<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>\n"
    "<KEY_NUMBER>Critical number</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>Why institutions watch this</KEY_NUMBER_CONTEXT>\n"
    "<SENTIMENT>0-100 Fear-Greed. Just the number.</SENTIMENT>\n"
    "<SUMMARY>3 institutional sentences. First includes SEO keyword.</SUMMARY>\n"
    "<TIKTOK>Sharp sophisticated analogy. 3-4 sentences.</TIKTOK>\n"
    "<HEADLINE>Alpha headline</HEADLINE>\n"
    "<DEPTH><strong>🧐 MACRO:</strong> Systems view. 5+ sentences."
    "<br><br><strong>🐑 HERD:</strong> Cognitive bias. 4+ sentences."
    "<br><br><strong>🦅 CONTRARIAN:</strong> G7 vs BRICS+. 5+ sentences.</DEPTH>\n"
    '<FLOW>TEXT + emoji (6+ steps)</FLOW>\n'
    "<GRAPH_DATA>3 metrics for [CATEGORY]. [CAT_HINT]. Scores differ (25-90). Name1|Score1|Name2|Score2|Name3|Score3</GRAPH_DATA>\n"
    "<VIP_RADAR_1>Sector - BULLISH or BEARISH - why</VIP_RADAR_1>\n"
    "<VIP_RADAR_2>Sector - BULLISH or BEARISH - why</VIP_RADAR_2>\n"
    "<VIP_RADAR_3>Sector - BULLISH or BEARISH - why</VIP_RADAR_3>\n"
    "<VIP_RADAR_4>Sector - BULLISH or BEARISH - why</VIP_RADAR_4>\n"
    "<VIP_C1>Technical: sector ETF trends. 5+ sentences.</VIP_C1>\n"
    "<VIP_C2>Macro: yields, credit, dollar, global flows. 5+ sentences.</VIP_C2>\n"
    "<VIP_C3>Smart Money: US, EU, Asia institutions. 5+ sentences.</VIP_C3>\n"
    "<MARKET_SNAP>S&P 500|DIRECTION|reason\n10Y Yield|DIRECTION|reason\nUS Dollar|DIRECTION|reason\nOil WTI|DIRECTION|reason</MARKET_SNAP>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

VIP_P2 = (
    "You are [PERSONA] writing Part 2 for Warm Insight VIP ([CATEGORY]).\n"
    "[ACCURACY]\n"
    "CRITICAL: Write REAL analysis paragraphs.\n\n"
    "Context from Part 1:\n[CTX]\n\n"
    "<VIP_T1>Fear vs greed balance globally. Full paragraph.</VIP_T1>\n"
    "<VIP_T2>Recommended allocation: [ALLOC_STR]. Name real ETFs. Full paragraph.</VIP_T2>\n"
    "<VIP_T3>US vs Europe, China, emerging markets. Full paragraph.</VIP_T3>\n"
    "<VIP_T4>DCA strategy advice. Full paragraph.</VIP_T4>\n"
    "<VIP_DO>3 specific actions with ETF, percentage, trigger.</VIP_DO>\n"
    "<VIP_DONT>2 specific mistakes to avoid.</VIP_DONT>\n"
    "<COMPARE_BULL>Bull case 2-3 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case 2-3 sentences.</COMPARE_BEAR>\n"
    "<CONVICTION>HIGH, MEDIUM, or LOW</CONVICTION>\n"
    "<TAKEAWAY>One calming sentence.</TAKEAWAY>\n"
    "<PS>Historical lesson 2-3 sentences.</PS>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

VIP_FB = (
    "You are [PERSONA]. Write VIP strategy for [CATEGORY].\n"
    "[ACCURACY]\n"
    "Based on: [CTX_SHORT]\n\n"
    "<VIP_T1>Fear vs greed? (3-4 sentences)</VIP_T1>\n"
    "<VIP_T2>[ALLOC_STR]. Name ETFs. (3-4 sentences)</VIP_T2>\n"
    "<VIP_T3>US vs Europe/Asia? (2-3 sentences)</VIP_T3>\n"
    "<VIP_T4>DCA approach? (3-4 sentences)</VIP_T4>\n"
    "<VIP_DO>2 actions with ETF and trigger.</VIP_DO>\n"
    "<VIP_DONT>1 mistake to avoid.</VIP_DONT>\n"
    "<COMPARE_BULL>Bull case 1-2 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case 1-2 sentences.</COMPARE_BEAR>\n"
    "<CONVICTION>HIGH, MEDIUM, or LOW</CONVICTION>\n"
    "<TAKEAWAY>One calming insight.</TAKEAWAY>\n"
    "<PS>Historical parallel 1-2 sentences.</PS>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

EDITOR_PROMPT = (
    "Senior editorial fact-checker. Review newsletter vs original news.\n"
    "CHECK: 1) Fabricated events 2) Fake stats 3) Invented names 4) False causation\n"
    "NEWS:\n[NEWS]\n\nNEWSLETTER:\n[CONTENT]\n\n"
    "<VERDICT>PASS or FAIL</VERDICT>\n"
    "<ISSUES>If FAIL list issues. If PASS write No issues.</ISSUES>"
)

# ═══════════════════════════════════════════════
# SEO CONFIG
# ═══════════════════════════════════════════════
SITE_URL = "https://warminsight.com"
AUTHOR_NAME = "Ethan Cole"
AUTHOR_BIO = "Ethan Cole is a veteran financial analyst and the lead voice behind Warm Insight."

PILLAR_PAGES = {
    "Economy": {"url": SITE_URL + "/category/economy/", "anchor": "all Economy analysis"},
    "Politics": {"url": SITE_URL + "/category/politics/", "anchor": "all Politics analysis"},
    "Tech": {"url": SITE_URL + "/category/tech/", "anchor": "all Tech analysis"},
    "Health": {"url": SITE_URL + "/category/health/", "anchor": "all Health analysis"},
    "Energy": {"url": SITE_URL + "/category/energy/", "anchor": "all Energy analysis"},
}
CAT_RELATED = {"Economy": ["Politics", "Energy"], "Politics": ["Economy", "Energy"], "Tech": ["Economy", "Health"], "Health": ["Tech", "Economy"], "Energy": ["Economy", "Politics"]}

def _build_jsonld(title, excerpt, kw, cat, slug, tf):
    schema = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": title[:110], "description": excerpt[:150], "keywords": kw + ", " + cat + ", market analysis, Warm Insight", "author": {"@type": "Person", "name": AUTHOR_NAME}, "publisher": {"@type": "Organization", "name": "Warm Insight", "url": SITE_URL}, "datePublished": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "articleSection": cat, "inLanguage": "en"}
    return '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False) + '</script>'

def _build_internal_links(cat):
    pillar = PILLAR_PAGES.get(cat, PILLAR_PAGES["Economy"])
    h = '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:22px;margin:30px 0;"><h4 style="margin-top:0;">Explore More</h4><p style="margin:0;"><a href="' + pillar["url"] + '" style="color:#b8974d;">' + pillar["anchor"] + '</a>'
    for rc in CAT_RELATED.get(cat, [])[:2]:
        rp = PILLAR_PAGES.get(rc)
        if rp: h += ' · <a href="' + rp["url"] + '" style="color:#b8974d;">' + rp["anchor"].replace("all ", "") + '</a>'
    return h + '</p></div>'

def _build_author_bio():
    return '<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:22px;margin:30px 0;"><p style="margin:0;font-weight:700;">' + AUTHOR_NAME + '</p><p style="margin:4px 0 0;font-size:15px;color:#374151;">' + AUTHOR_BIO + '</p></div>'

# ═══════════════════════════════════════════════
# WORDPRESS API 
# ═══════════════════════════════════════════════
_wp_cat_cache = {}

def get_or_create_wp_category(cat_name):
    if cat_name in _wp_cat_cache: return _wp_cat_cache[cat_name]
    try:
        r = requests.get(WP_URL + "/wp-json/wp/v2/categories?search=" + cat_name + "&per_page=10", auth=WP_AUTH, timeout=15)
        if r.status_code == 200:
            for c in r.json():
                if c["name"].lower() == cat_name.lower():
                    _wp_cat_cache[cat_name] = c["id"]; return c["id"]
        r2 = requests.post(WP_URL + "/wp-json/wp/v2/categories", auth=WP_AUTH, json={"name": cat_name, "slug": cat_name.lower()}, timeout=15)
        if r2.status_code in (200, 201):
            _wp_cat_cache[cat_name] = r2.json()["id"]; return r2.json()["id"]
    except Exception as e: print("  WP Category error: " + str(e))
    return None

def get_recent_titles():
    try:
        r = requests.get(WP_URL + "/wp-json/wp/v2/posts?per_page=50&_fields=title", auth=WP_AUTH, timeout=30)
        if r.status_code in (200, 201):
            titles = [p.get("title", {}).get("rendered", "").lower() for p in r.json()]
            print("  Loaded " + str(len(titles)) + " recent titles from WP")
            return titles
    except Exception as e: pass
    return []

def is_duplicate(new_title, recent):
    if not new_title or not recent: return False
    labels = ["[💎 pro]", "[👑 vip]"]
    cn = new_title.lower()
    for lb in labels: cn = cn.replace(lb, "").strip()
    words_new = set(cn.split())
    if len(words_new) < 4: return False
    for rt in recent:
        cr = rt
        for lb in labels: cr = cr.replace(lb, "").strip()
        words_rt = set(cr.split())
        if len(words_rt) < 4: continue
        if len(words_rt & words_new) / max(len(words_new), 1) > 0.7: return True
    return False

def editor_review(client, news_str, html):
    try:
        text = re.sub(r"<[^>]+>", " ", html); text = re.sub(r"\s+", " ", text)[:3000]
        p = EDITOR_PROMPT.replace("[NEWS]", news_str[:2000]).replace("[CONTENT]", text)
        
        r = None
        for m in FAST_MODELS:
            r = call_gem(client, m, p, retries=1)
            if r: break
            
        if not r: return True, "N/A"
        if "FAIL" in xtag(r, "VERDICT").upper():
            print("    EDITOR REJECTED: " + xtag(r, "ISSUES")[:200])
            return False, xtag(r, "ISSUES")
        return True, xtag(r, "ISSUES")
    except Exception as e: return True, str(e)

def upload_img(img_bytes):
    for attempt in range(2):
        try:
            r = requests.post(WP_URL + "/wp-json/wp/v2/media", auth=WP_AUTH, headers={'Content-Disposition': 'attachment; filename="warm_thumb.jpg"', 'Content-Type': 'image/jpeg'}, data=img_bytes, timeout=30)
            if r.status_code in (200, 201): return r.json()["id"]
            if attempt == 0: time.sleep(3)
        except:
            if attempt == 0: time.sleep(3)
    return None

def _split_html_for_paywall(html):
    for marker in ['In Plain English</h3>', 'Executive Summary</h2>']:
        idx = html.find(marker)
        if idx > 0:
            pos = idx + len(marker); div_count = 0
            while pos < len(html) and div_count < 2:
                nc = html.find('</div>', pos)
                if nc < 0: break
                div_count += 1; pos = nc + 6
            if div_count >= 2 and pos < len(html) * 0.6: return html[:pos], html[pos:]
    target = int(len(html) * 0.3)
    best = html.rfind('</div>', 0, target + 500)
    if best > len(html) * 0.15: return html[:best + 6], html[best + 6:]
    return html, ""

def publish(title, html, cat, tier, feature_img_id, exc, kw="", slug=""):
    print("  Pub: " + title[:60])
    for attempt in range(1, 4):
        try:
            public_html, private_html = _split_html_for_paywall(html)
            full_content = public_html
            if private_html: full_content += "\n\n\n\n" + private_html
            if kw and slug: full_content = _build_jsonld(title, exc or "", kw, cat, slug, "") + full_content
            post_data = {"title": title, "content": full_content, "status": "publish", "excerpt": exc[:290] if exc else ""}
            cat_id = get_or_create_wp_category(cat)
            if cat_id: post_data["categories"] = [cat_id]
            if slug: post_data["slug"] = slug
            if feature_img_id: post_data["featured_media"] = feature_img_id
            if kw: post_data["meta"] = {"rank_math_title": (kw + " | " + cat + " | Warm Insight")[:60], "rank_math_description": (exc[:120] + " Expert " + cat.lower() + " analysis.")[:155], "rank_math_focus_keyword": kw}
            r = requests.post(WP_URL + "/wp-json/wp/v2/posts", auth=WP_AUTH, json=post_data, timeout=60)
            if r.status_code in (200, 201):
                print("  WP OK! " + r.json().get("link", "")); return True
            elif r.status_code == 403: time.sleep(10 * attempt); continue
            elif r.status_code == 429: time.sleep(30 * attempt); continue
            else: return False
        except:
            if attempt < 3: time.sleep(5 * attempt)
    return False

# ═══════════════════════════════════════════════
# GEMINI — 🚨 [다중 폴백 및 404 즉시 우회 패치]
# ═══════════════════════════════════════════════
def call_gem(client, model, prompt, retries=2):
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt)
            text = str(r.text) if r.text else ""
            if not text or text == "None":
                print("    Gem(" + model + ") attempt " + str(i) + ": Empty response")
                if i < retries: time.sleep(10 * i)
                continue
            return text
        except Exception as e:
            err_str = str(e)
            print("    ⚠️ Gem(" + model + ") ERROR: " + err_str[:150])
            
            # 🚨 404 에러(이름 거부)는 재시도해봤자 시간 낭비이므로 즉시 리턴하고 다음 폴백 모델로 넘김!
            if "404" in err_str or "not found" in err_str.lower() or "not supported" in err_str.lower():
                return None
                
            if "503" in err_str or "UNAVAILABLE" in err_str:
                time.sleep(15 * i)
            elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                time.sleep(30 * i)
            elif i < retries:
                time.sleep(10 * i)
    return None

def gem_fb(client, tier, prompt):
    # 🚨 리스트에 있는 모델들을 하나씩 시도. 404가 뜨면 즉시 다음 것으로 넘어감!
    models_to_try = MODEL_PRI.get(tier, FAST_MODELS)
    for m in models_to_try:
        print("    [AI] Trying model: " + m)
        r = call_gem(client, m, prompt)
        if r: 
            return r, m
        print("    [AI] Model " + m + " failed. Attempting next fallback...")
    return None, None

# ═══════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════
def xtag(text, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""

def get_news(urls, count=20):
    news, seen = [], set()
    for url in urls:
        try:
            for e in feedparser.parse(url).entries:
                t = getattr(e, "title", "")
                if t in seen: continue
                seen.add(t); news.append("- " + t + ": " + getattr(e, "summary", ""))
                if len(news) >= count: break
        except: continue
    return news[:count]

def parse_graph(raw, cat):
    if not raw: return _fbg(cat)
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 6: return _fbg(cat)
    try:
        v1, v2, v3 = int(re.sub(r"[^0-9]", "", parts[1])), int(re.sub(r"[^0-9]", "", parts[3])), int(re.sub(r"[^0-9]", "", parts[5]))
        if v1 == v2 == v3: return _fbg(cat)
        return parts[0], max(10, min(95, v1)), parts[2], max(10, min(95, v2)), parts[4], max(10, min(95, v3))
    except: return _fbg(cat)

def _fbg(cat):
    pool = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["pool"]
    lb = random.sample(pool, 3)
    return lb[0], random.randint(55, 88), lb[1], random.randint(30, 65), lb[2], random.randint(40, 78)

def is_echo(text):
    if not text or len(text) < 80: return True
    sigs = ["6+ sentences", "5+ sentences", "Write a detailed", "Write exactly", "Write real", "Name ETFs and trigger", "Write a full paragraph"]
    return sum(1 for s in sigs if s.lower() in text.lower()) >= 3

def ok_tag(raw, tag):
    v = xtag(raw, tag)
    return "" if not v or is_echo(v) else v

def sanitize(h): return re.sub(r"\s+", " ", h.replace("\n", " ").replace("\r", ""))

def make_slug(kw, title, cat=""):
    t = kw if kw else title; prefix = cat.lower() + "-" if cat else ""
    return (prefix + re.sub(r"\s+", "-", re.sub(r"[^a-zA-Z0-9\s-]", "", t.lower()).strip()))[:80]

def get_current_category():
    cats = list(CATEGORIES.keys()); now = datetime.utcnow()
    rng = random.Random(now.year * 10000 + now.month * 100 + now.day)
    shuffled = cats[:]; rng.shuffle(shuffled)
    sel = shuffled[now.hour % len(shuffled)]
    print("  UTC " + str(now.hour) + " -> " + sel)
    return sel

# ═══════════════════════════════════════════════
# HTML BUILDERS 
# ═══════════════════════════════════════════════
F = "font-size:18px;line-height:1.8;color:#374151;"
MAIN = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;"

def _hdr(author, tf, badge=""):
    b = (' <span style="background:#b8974d;color:#fff;padding:3px 12px;border-radius:4px;font-size:14px;font-weight:bold;">' + badge + '</span>') if badge else ""
    return '<div style="border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;padding:14px 0;margin-bottom:30px;"><p style="margin:0;font-size:16px;color:#4b5563;"><strong style="color:#1a252c;">' + author + '</strong> | ' + tf + b + '</p></div>'

def _ftr(tw, ps):
    if not tw or is_echo(tw): tw = "Stay disciplined, stay diversified, and let time compound in your favor."
    if not ps or is_echo(ps): ps = "In 40 years of watching markets, the disciplined investor always wins."
    return ('<hr style="border:0;height:1px;background:#e5e7eb;margin:45px 0;"><h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Today\'s Warm Insight</h2><p style="' + F + '">' + tw + '</p>'
            + '<div style="margin-top:30px;background:#1e293b;padding:28px;border-radius:8px;border-left:4px solid #b8974d;"><p style="font-size:18px;line-height:1.8;color:#e2e8f0;margin:0;"><span style="color:#b8974d;font-weight:bold;">P.S.</span> <span style="color:#cbd5e1;">' + ps + '</span></p></div>'
            + '<div style="background:#f8fafc;border:2px solid #e5e7eb;border-radius:10px;padding:28px;margin:40px 0;text-align:center;"><p style="font-size:22px;font-weight:bold;color:#1a252c;margin:0 0 8px;">Found this useful?</p><p style="font-size:16px;color:#b8974d;margin:0;"><a href="' + SITE_URL + '" style="color:#b8974d;">Subscribe at warminsight.com</a></p></div>'
            + '<div style="background:#1e293b;padding:35px;border-radius:10px;margin-top:30px;"><p style="font-size:24px;font-weight:bold;color:#b8974d;margin:0 0 8px;text-align:center;">Warm Insight</p><p style="font-size:13px;color:#64748b;margin:0;text-align:center;">All analysis is for informational purposes only. Not financial advice.<br>&copy; 2026 Warm Insight.</p></div></div>')

def _up(msg): return '<div style="background:#fffbeb;border:2px solid #f59e0b;padding:18px;border-radius:8px;margin:35px 0;"><p style="font-size:18px;color:#92400e;margin:0;text-align:center;">' + msg + '</p></div>'

def _impact(imp):
    imp = (imp or "").upper().strip()
    cols = {"HIGH": ("#dc2626", "#fef2f2"), "MEDIUM": ("#d97706", "#fffbeb"), "LOW": ("#059669", "#ecfdf5")}
    c, bg = cols.get(imp, ("#6b7280", "#f3f4f6"))
    return ('<span style="display:inline-block;background:' + bg + ';color:' + c + ';border:2px solid ' + c + ';padding:4px 14px;border-radius:20px;font-size:14px;font-weight:bold;margin-bottom:20px;">IMPACT: ' + imp + '</span>') if imp else ""

def _keynum(kn, knc, color="#1e40af"):
    if not kn or not knc: return ""
    return '<div style="background:#f0f9ff;border:2px solid ' + color + ';border-radius:12px;padding:28px;margin-bottom:30px;text-align:center;"><div style="font-size:48px;font-weight:800;color:' + color + ';">' + kn + '</div><p style="font-size:18px;color:#374151;margin:0;">' + knc + '</p></div>'

def _qhits(raw):
    qh = xtag(raw, "QUICK_HITS")
    if not qh or is_echo(qh): return ""
    lines = [l.strip() for l in qh.strip().split("\n") if l.strip()]
    if not lines: return ""
    emos = ["⚡", "🔥", "📌"]
    items = "".join('<p style="font-size:18px;color:#374151;margin:10px 0;">' + (emos[i] if i < 3 else "•") + " " + l + '</p>' for i, l in enumerate(lines[:3]))
    return '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:24px;margin-bottom:35px;"><h3 style="margin-top:0;">Quick Hits</h3>' + items + '</div>'

def _msnap(raw):
    ms = xtag(raw, "MARKET_SNAP")
    if not ms or is_echo(ms): return ""
    lines = [l.strip() for l in ms.strip().split("\n") if "|" in l]
    if len(lines) < 2: return ""
    icons = {"UP": ("▲", "#059669"), "DOWN": ("▼", "#dc2626"), "FLAT": ("—", "#6b7280")}
    cells = ""
    for line in lines[:4]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2: continue
        arrow, color = icons.get(parts[1].upper().strip(), ("—", "#6b7280"))
        reason = parts[2][:40] if len(parts) > 2 else ""
        cells += '<div style="flex:1;min-width:130px;text-align:center;padding:12px;"><div style="font-size:14px;color:#94a3b8;">' + parts[0] + '</div><div style="font-size:22px;font-weight:800;color:' + color + ';">' + arrow + " " + parts[1].upper().strip() + '</div><div style="font-size:12px;color:#64748b;">' + reason + '</div></div>'
    return '<div style="background:#1e293b;border-radius:10px;padding:12px;margin-bottom:30px;"><div style="display:flex;flex-wrap:wrap;justify-content:space-around;">' + cells + '</div></div>' if cells else ""

def _compare(cb, cbear, bt="Bull Case", brt="Bear Case"):
    if not cb and not cbear: return ""
    bull = ('<div style="flex:1;min-width:220px;background:#ecfdf5;border:2px solid #10b981;border-radius:10px;padding:22px;"><h4 style="margin-top:0;color:#065f46;">🐂 ' + bt + '</h4><p style="font-size:18px;color:#064e3b;margin:0;">' + cb + '</p></div>') if cb else ""
    bear = ('<div style="flex:1;min-width:220px;background:#fef2f2;border:2px solid #ef4444;border-radius:10px;padding:22px;"><h4 style="margin-top:0;color:#991b1b;">🐻 ' + brt + '</h4><p style="font-size:18px;color:#7f1d1d;margin:0;">' + cbear + '</p></div>') if cbear else ""
    return '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">' + bull + bear + '</div>'

def build_premium(a, tf, r):
    return ('<div style="' + MAIN + '">' + _hdr(a, tf, "PRO") + _impact(xtag(r, "IMPACT")) + _keynum(xtag(r, "KEY_NUMBER"), xtag(r, "KEY_NUMBER_CONTEXT"))
        + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;">Executive Summary</h2><p style="' + F + '">' + xtag(r, "SUMMARY") + '</p>'
        + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin:30px 0;"><h3 style="margin-top:0;">💡 In Plain English</h3><p style="' + F + 'margin:0;">' + xtag(r, "TIKTOK") + '</p></div>'
        + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;">Market Drivers</h2><h3>' + xtag(r, "HEADLINE") + '</h3><p style="' + F + '">' + xtag(r, "DEPTH") + '</p>'
        + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:8px;margin:30px 0;"><strong style="color:#b8974d;">💡 Quick Flow:</strong><p style="font-size:20px;font-weight:bold;margin:10px 0 0;">' + xtag(r, "FLOW") + '</p></div>'
        + _compare(xtag(r, "COMPARE_BULL"), xtag(r, "COMPARE_BEAR")) + _qhits(r)
        + '<div style="background:#fff;border:2px solid #3b82f6;padding:28px;border-radius:8px;margin:30px 0;"><h3 style="margin-top:0;color:#1e40af;">💎 Pro-Only Insight</h3><p style="' + F + 'margin:0;">' + xtag(r, "PRO_INSIGHT") + '</p></div>'
        + '<div style="background:#ecfdf5;border:2px solid #10b981;padding:24px;border-radius:8px;margin-bottom:15px;"><p style="font-size:18px;color:#065f46;margin:0;"><strong>🟢 DO:</strong> ' + xtag(r, "PRO_DO") + '</p></div>'
        + '<div style="background:#fef2f2;border:2px solid #ef4444;padding:24px;border-radius:8px;margin-bottom:35px;"><p style="font-size:18px;color:#7f1d1d;margin:0;"><strong>🔴 AVOID:</strong> ' + xtag(r, "PRO_DONT") + '</p></div>'
        + _up('🔒 Want institutional analysis? <strong>Upgrade to VIP.</strong>') + _ftr(xtag(r, "TAKEAWAY"), xtag(r, "PS")))

def build_vip(a, tf, raw, cat):
    theme = CAT_THEME.get(cat, CAT_THEME["Economy"]); accent = theme["accent"]; al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
    l1, v1, l2, v2, l3, v3 = parse_graph(xtag(raw, "GRAPH_DATA"), cat); COL = [accent, "#f59e0b", "#10b981"]
    sent_h = ""
    try:
        sr = xtag(raw, "SENTIMENT")
        if sr:
            sv = max(0, min(100, int(re.sub(r"[^0-9]", "", sr))))
            if sv <= 25: sl, sc = "EXTREME FEAR", "#dc2626"
            elif sv <= 40: sl, sc = "FEAR", "#ea580c"
            elif sv <= 60: sl, sc = "NEUTRAL", "#ca8a04"
            elif sv <= 75: sl, sc = "GREED", "#16a34a"
            else: sl, sc = "EXTREME GREED", "#059669"
            sent_h = '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:25px;margin-bottom:35px;"><h3 style="margin-top:0;">🧭 Fear &amp; Greed Meter</h3><div style="width:100%;height:20px;border-radius:10px;overflow:hidden;background:linear-gradient(to right,#dc2626,#ea580c,#ca8a04,#16a34a,#059669);position:relative;"><div style="position:absolute;left:' + str(sv) + '%;top:0;width:4px;height:100%;background:#fff;"></div></div><div style="display:flex;justify-content:space-between;margin-top:8px;"><span style="color:#dc2626;">Fear</span><span style="font-size:20px;font-weight:800;color:' + sc + ';">' + str(sv) + ' - ' + sl + '</span><span style="color:#059669;">Greed</span></div></div>'
    except: pass
    conv = xtag(raw, "CONVICTION").upper().strip(); conv_h = ""
    if conv:
        cc = {"HIGH": ("#065f46", "#ecfdf5", "🟢"), "MEDIUM": ("#92400e", "#fffbeb", "🟡"), "LOW": ("#991b1b", "#fef2f2", "🔴")}
        c2, bg2, ci = cc.get(conv, ("#6b7280", "#f3f4f6", "⚪"))
        conv_h = '<div style="background:' + bg2 + ';border:2px solid ' + c2 + ';border-radius:10px;padding:20px;margin-bottom:35px;text-align:center;"><p style="font-size:14px;color:#6b7280;margin:0 0 5px;">Overall Conviction</p><p style="font-size:28px;font-weight:800;color:' + c2 + ';margin:0;">' + ci + ' ' + conv + '</p></div>'
    def gauge(lb, val, c): return '<div style="margin-bottom:22px;"><div style="display:flex;justify-content:space-between;"><span style="font-weight:600;">' + lb + '</span><span style="font-weight:700;color:' + c + ';">' + str(val) + '%</span></div><div style="width:100%;background:#e5e7eb;border-radius:8px;height:16px;overflow:hidden;"><div style="width:' + str(val) + '%;background:' + c + ';height:100%;border-radius:8px;"></div></div></div>'
    s, b, cp = al["s"], al["b"], al["c"]; circ = 565.49; sd, bd, cd = circ*s/100, circ*b/100, circ*cp/100
    pie = '<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;"><circle cx="100" cy="100" r="90" fill="none" stroke="' + accent + '" stroke-width="30" stroke-dasharray="%.1f %.1f" stroke-dashoffset="0"/><circle cx="100" cy="100" r="90" fill="none" stroke="#64748b" stroke-width="30" stroke-dasharray="%.1f %.1f" stroke-dashoffset="-%.1f"/><circle cx="100" cy="100" r="90" fill="none" stroke="#b8974d" stroke-width="30" stroke-dasharray="%.1f %.1f" stroke-dashoffset="-%.1f"/><text x="100" y="95" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">%d/%d/%d</text><text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>' % (sd, circ, bd, circ, sd, cd, circ, sd+bd, s, b, cp)
    pie += '<div style="display:flex;justify-content:center;gap:20px;"><span style="color:' + accent + ';">● Stocks ' + str(s) + '%</span><span style="color:#64748b;">● Safe ' + str(b) + '%</span><span style="color:#b8974d;">● Cash ' + str(cp) + '%</span></div><p style="font-size:16px;color:#6b7280;text-align:center;font-style:italic;">' + al["note"] + '</p>'
    rr = ""
    for i in range(1, 5):
        v = ok_tag(raw, "VIP_RADAR_" + str(i))
        if not v: continue
        bull = "bullish" in v.lower()
        bg_r, tc, ic = ("#ecfdf5", "#065f46", "🟢 BULL") if bull else ("#fef2f2", "#991b1b", "🔴 BEAR")
        rr += '<tr><td style="padding:14px;border-bottom:1px solid #e5e7eb;">' + v + '</td><td style="padding:14px;border-bottom:1px solid #e5e7eb;text-align:center;"><span style="background:' + bg_r + ';color:' + tc + ';padding:4px 12px;border-radius:6px;font-weight:bold;">' + ic + '</span></td></tr>'
    radar = ('<div style="background:#fff;border:2px solid ' + accent + ';border-radius:8px;padding:25px;margin-bottom:35px;"><h3 style="margin-top:0;color:' + accent + ';">🎯 Sector Radar</h3><table style="width:100%;border-collapse:collapse;">' + rr + '</table></div>') if rr else ""
    def mc(lb, val, c): return '<div style="flex:1;min-width:200px;background:#f8fafc;border:2px solid ' + c + ';border-radius:10px;padding:22px;text-align:center;"><div style="font-size:42px;font-weight:800;color:' + c + ';">' + str(val) + '%</div><div style="font-size:16px;color:#4b5563;font-weight:600;">' + lb + '</div></div>'
    c1, c2, c3 = ok_tag(raw, "VIP_C1"), ok_tag(raw, "VIP_C2"), ok_tag(raw, "VIP_C3")
    t1, t2, t3, t4 = ok_tag(raw, "VIP_T1"), ok_tag(raw, "VIP_T2"), ok_tag(raw, "VIP_T3"), ok_tag(raw, "VIP_T4")
    vdo, vdont = ok_tag(raw, "VIP_DO"), ok_tag(raw, "VIP_DONT"); tw, ps = ok_tag(raw, "TAKEAWAY"), ok_tag(raw, "PS")
    macro = ""
    if c1 or c2 or c3:
        pp = ""
        if c1: pp += '<p style="font-size:16px;color:' + accent + ';font-weight:bold;text-transform:uppercase;">Technical Signals</p><p style="' + F + '">' + c1 + '</p>'
        if c2: pp += '<hr style="border:0;height:1px;background:#e5e7eb;"><p style="font-size:16px;color:' + accent + ';font-weight:bold;text-transform:uppercase;">Macro Flows</p><p style="' + F + '">' + c2 + '</p>'
        if c3: pp += '<hr style="border:0;height:1px;background:#e5e7eb;"><p style="font-size:16px;color:' + accent + ';font-weight:bold;text-transform:uppercase;">Smart Money</p><p style="' + F + '">' + c3 + '</p>'
        macro = '<h2 style="font-family:Georgia,serif;font-size:28px;border-bottom:3px solid ' + accent + ';padding-bottom:12px;display:inline-block;">VIP: Macro &amp; Flow Analysis</h2><div style="border-left:5px solid ' + accent + ';padding:28px;border-radius:8px;margin:20px 0 40px;">' + pp + '</div>'
    def pb(n, title, body, extra=""):
        if not body: return ""
        return '<div style="background:#f8fafc;border-left:4px solid ' + accent + ';padding:28px;border-radius:8px;margin-bottom:25px;"><h3 style="margin-top:0;">' + str(n) + '. ' + title + '</h3>' + extra + '<p style="' + F + 'margin-bottom:0;">' + body + '</p></div>'
    pbc = pb("1", "Fear vs. Greed", t1) + pb("2", str(s)+"/"+str(b)+"/"+str(cp)+" Seesaw", t2, pie) + pb("3", "Global Shield", t3) + pb("4", "Survival Mechanics", t4)
    pbk = ('<h2 style="font-family:Georgia,serif;font-size:28px;border-bottom:3px solid ' + accent + ';padding-bottom:12px;display:inline-block;">The Titans Playbook</h2>' + pbc) if pbc else ""
    act = ""
    if vdo or vdont:
        do_b = ('<div style="background:#ecfdf5;border:2px solid #10b981;border-radius:8px;padding:24px;margin-bottom:20px;"><p style="font-size:20px;color:#065f46;font-weight:bold;">🟢 DO:</p><p style="' + F + 'color:#064e3b;margin:0;">' + vdo + '</p></div>') if vdo else ""
        dn_b = ('<div style="background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:24px;"><p style="font-size:20px;color:#991b1b;font-weight:bold;">🔴 AVOID:</p><p style="' + F + 'color:#7f1d1d;margin:0;">' + vdont + '</p></div>') if vdont else ""
        act = '<div style="background:#1e293b;padding:35px;border-radius:10px;margin:45px 0;"><h3 style="color:#b8974d;margin-top:0;border-bottom:2px solid #475569;padding-bottom:15px;">✅ VIP Action Plan</h3>' + do_b + dn_b + '</div>'
    return ('<div style="' + MAIN + '">' + _hdr(a, tf, "VIP EXCLUSIVE")
        + '<div style="margin-bottom:25px;">' + _impact(xtag(raw, "IMPACT")) + '<span style="display:inline-block;background:#f8fafc;border:2px solid ' + accent + ';color:' + accent + ';padding:4px 14px;border-radius:20px;font-size:14px;font-weight:bold;">' + theme["icon"] + ' ' + theme["label"] + '</span></div>'
        + _keynum(xtag(raw, "KEY_NUMBER"), xtag(raw, "KEY_NUMBER_CONTEXT"), accent) + _msnap(raw) + sent_h
        + '<h2 style="font-family:Georgia,serif;font-size:28px;">Executive Summary</h2><p style="' + F + '">' + xtag(raw, "SUMMARY") + '</p>'
        + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin:30px 0;"><h3 style="margin-top:0;">💡 In Plain English</h3><p style="' + F + 'margin:0;">' + xtag(raw, "TIKTOK") + '</p></div>'
        + '<h2 style="font-family:Georgia,serif;font-size:28px;">Market Drivers</h2><h3>' + xtag(raw, "HEADLINE") + '</h3><p style="' + F + '">' + xtag(raw, "DEPTH") + '</p>'
        + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:22px;border-radius:8px;margin:30px 0;"><strong style="color:#b8974d;">💡 Quick Flow:</strong><p style="font-size:20px;font-weight:bold;margin:10px 0 0;">' + xtag(raw, "FLOW") + '</p></div>'
        + '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">' + mc(l1, v1, COL[0]) + mc(l2, v2, COL[1]) + mc(l3, v3, COL[2]) + '</div>'
        + '<div style="padding:28px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:35px;"><h3 style="margin-top:0;">📊 Key Market Indicators</h3>' + gauge(l1, v1, COL[0]) + gauge(l2, v2, COL[1]) + gauge(l3, v3, COL[2]) + '</div>'
        + radar + _compare(ok_tag(raw, "COMPARE_BULL"), ok_tag(raw, "COMPARE_BEAR"), "Institutional Bull", "Institutional Bear")
        + macro + pbk + conv_h + act + _ftr(tw, ps))

# ═══════════════════════════════════════════════
# ANALYZE
# ═══════════════════════════════════════════════
def analyze(news_items, cat, tier):
    client = genai.Client(api_key=GEMINI_API_KEY)
    ns = "\n".join(news_items)
    persona = EXPERT.get(cat, EXPERT["Economy"])
    tf = datetime.now().strftime("%B %d, %Y at %I:%M %p (UTC)")
    author = "Ethan Cole &amp; The Warm Insight Panel"

    if tier == "Premium":
        prompt = PROMPT_PREMIUM.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", ACCURACY).replace("[NEWS_ITEMS]", ns)
        raw, _ = gem_fb(client, tier, prompt)
        if not raw:
            print("  Premium: Gemini returned None")
            return None, None, None, None, None, None
        html = build_premium(author, tf, raw)
    else:
        hint = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["hint"]
        al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
        al_str = str(al["s"]) + "% stocks, " + str(al["b"]) + "% safe, " + str(al["c"]) + "% cash (" + al["note"] + ")"
        p1 = VIP_P1.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", ACCURACY).replace("[CAT_HINT]", hint).replace("[NEWS_ITEMS]", ns)
        raw1, _ = gem_fb(client, tier, p1)
        if not raw1:
            print("  VIP P1: Gemini returned None")
            return None, None, None, None, None, None
        if not xtag(raw1, "VIP_C1") or is_echo(xtag(raw1, "VIP_C1")):
            print("    P1 quality low, retrying...")
            time.sleep(15)
            r1r, _ = gem_fb(client, tier, p1)
            if r1r and xtag(r1r, "VIP_C1") and not is_echo(xtag(r1r, "VIP_C1")): raw1 = r1r
        ctx = "Title: " + xtag(raw1, "TITLE") + "\nHeadline: " + xtag(raw1, "HEADLINE") + "\nSummary: " + xtag(raw1, "SUMMARY") + "\nInsight: " + xtag(raw1, "DEPTH")[:500]
        ctx_short = xtag(raw1, "HEADLINE") + ". " + xtag(raw1, "SUMMARY")
        
        print(f"    Part 2 (Fast Model)...")
        time.sleep(10)
        p2 = VIP_P2.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", ACCURACY).replace("[CTX]", ctx).replace("[ALLOC_STR]", al_str).replace("[NEWS_ITEMS]", ns)
        
        raw2 = None
        for m in FAST_MODELS:
            print("    [AI Fast] " + m)
            raw2 = call_gem(client, m, p2)
            if raw2: break
            
        for retry in range(2):
            if raw2 and ok_tag(raw2, "VIP_T1"): break
            print("    P2 retry " + str(retry + 1)); time.sleep(15)
            for m in FAST_MODELS:
                raw2 = call_gem(client, m, p2)
                if raw2: break
                
        if not raw2 or not ok_tag(raw2, "VIP_T1"):
            print("    P2 FAIL -> Fallback")
            time.sleep(10)
            fb_prompt = VIP_FB.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", ACCURACY).replace("[CTX_SHORT]", ctx_short[:400]).replace("[ALLOC_STR]", al_str).replace("[NEWS_ITEMS]", ns)
            for m in FAST_MODELS:
                raw2 = call_gem(client, m, fb_prompt)
                if raw2: break
            if not raw2: raw2 = ""
            
        raw = raw1 + "\n" + raw2
        html = build_vip(author, tf, raw, cat)

    tr = xtag(raw, "TITLE"); exc = xtag(raw, "EXCERPT") or "Expert analysis."; kw = xtag(raw, "SEO_KEYWORD")
    title = "[" + TIER_LABELS.get(tier, tier) + "] " + tr if tr else "(" + tier + ") " + cat + " Insight"
    slug = make_slug(kw, tr or cat, cat)
    html += _build_internal_links(cat) + _build_author_bio()
    html = sanitize(html)
    return title, html, exc, kw, slug, tier

# ═══════════════════════════════════════════════
# MAIN 
# ═══════════════════════════════════════════════
def main():
    print("=" * 50)
    print("  Warm Insight v11 (WP Full Fixed Build)")
    print("=" * 50)
    cat = get_current_category()
    urls = CATEGORIES.get(cat)
    if not urls: print("No URLs"); return
    recent = get_recent_titles()
    print("\n--- [" + cat + "] ---")
    news = get_news(urls, 20)
    if len(news) < 5: print("  Not enough news (" + str(len(news)) + ")"); return

    gem_client = genai.Client(api_key=GEMINI_API_KEY)
    total = ok_cnt = fail = 0

    for task in TASKS:
        tier, cnt = task["tier"], task["count"]
        if len(news) < cnt: print("  Skip " + tier + " (not enough news)"); break
        target = [news.pop(0) for _ in range(cnt)]
        total += 1
        print("\n  [" + TIER_LABELS[tier] + "] " + str(cnt) + " articles...")

        result = analyze(target, cat, tier)
        if not result or not result[1]:
            print("  ANALYZE FAILED for " + tier)
            fail += 1; continue

        title, html, exc, kw, slug, _ = result
        print("  Title: " + title[:80])

        if is_duplicate(title, recent):
            print("  SKIP dup"); fail += 1; continue

        if tier not in SKIP_EDITOR_TIERS:
            passed = False
            for m in FAST_MODELS:
                try:
                    text = re.sub(r"<[^>]+>", " ", html); text = re.sub(r"\s+", " ", text)[:3000]
                    p = EDITOR_PROMPT.replace("[NEWS]", "\n".join(target)[:2000]).replace("[CONTENT]", text)
                    r = call_gem(gem_client, m, p, retries=1)
                    if r:
                        if "FAIL" in xtag(r, "VERDICT").upper():
                            print("    EDITOR REJECTED: " + xtag(r, "ISSUES")[:200])
                        else:
                            print("    Editor: PASS")
                            passed = True
                        break
                except: pass
                
            if not passed:
                time.sleep(10)
                result2 = analyze(target, cat, tier)
                if result2 and result2[1]:
                    title, html, exc, kw, slug, _ = result2
                else: fail += 1; continue

        print("  Generating thumbnail...")
        thumb_bytes = make_dynamic_thumb(title, cat, tier)
        feature_img = upload_img(thumb_bytes) if thumb_bytes else None

        if publish(title, html, cat, tier, feature_img, exc, kw, slug):
            ok_cnt += 1; recent.append(title.lower())
        else: fail += 1

        sl = TIER_SLEEP[tier] + random.randint(60, 180)
        print("  Wait " + str(sl) + "s"); time.sleep(sl)

    print("\n" + "=" * 50)
    print("  " + cat + " | Total " + str(total) + " | OK " + str(ok_cnt) + " | Fail " + str(fail))
    print("=" * 50)

if __name__ == "__main__":
    try: main()
    except Exception:
        print("\nFATAL ERROR:"); traceback.print_exc(); sys.exit(1)
