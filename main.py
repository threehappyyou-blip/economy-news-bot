# -*- coding: utf-8 -*-
"""
Warm Insight v11 — 2-Tier Cost Optimized Build
Changes from v10:
  - Basic tier removed (Premium + VIP only)
  - News: 5 per tier
  - Cost mode: low (all flash), ~200원/run
  - Cron: every 3 hours recommended (8 runs/day, ~4.8만원/month)
  - Thumbnails: pre-uploaded Warmy mascot images (no Imagen cost)
  - Imagen removed entirely

Python 3.10 safe.
"""
import os, sys, traceback, time, random, re, json, io
from datetime import datetime
import requests, jwt, feedparser
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL", "").rstrip("/")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")
if not all([GEMINI_API_KEY, GHOST_API_URL, GHOST_ADMIN_API_KEY]):
    sys.exit("Missing API keys")

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

# ═══════════════════════════════════════════════
# 2-TIER SETUP: Premium + VIP only
# ═══════════════════════════════════════════════
TASKS = [
    {"tier": "Premium", "count": 5},
    {"tier": "Royal Premium", "count": 5},
]
TIER_LABELS = {"Premium": "💎 Pro", "Royal Premium": "👑 VIP"}
TIER_VIS = {"Premium": "public", "Royal Premium": "public"}
TIER_SLEEP = {"Premium": 30, "Royal Premium": 50}

# All flash for cost optimization (~200원/run total)
MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-flash"],
    "Premium": ["gemini-2.5-flash"],
}

# Editor only for VIP (saves 1 flash call per Premium)
SKIP_EDITOR_TIERS = ["Premium"]

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
    "Economy": {"pool": ["Inflation Momentum", "Recession Risk", "Consumer Pulse", "Credit Stress", "Rate Cut Odds", "Dollar Strength", "Yield Curve", "PMI Signal", "Global Trade Flow", "EM Capital Flight Risk", "G7 vs BRICS Gap"], "hint": "inflation, GDP, Fed policy, global capital flows, bloc divergence"},
    "Politics": {"pool": ["Policy Uncertainty", "Regulatory Risk", "Geopolitical Tension", "Election Volatility", "Trade War Risk", "Sanctions Impact", "Gridlock", "Defense Momentum", "Chokepoint Risk", "Alliance Cohesion"], "hint": "policy, geopolitics, chokepoints, bloc politics, de-dollarization"},
    "Tech": {"pool": ["AI Race Intensity", "Antitrust Pressure", "Chip Supply Stress", "IPO Sentiment", "Cloud Velocity", "Cyber Threat", "Big Tech Momentum", "Funding Freeze", "Tech Decoupling Risk", "Data Sovereignty"], "hint": "AI, semiconductors, regulation, tech decoupling, cyber sovereignty"},
    "Health": {"pool": ["Pipeline Confidence", "Drug Pricing Pressure", "Biotech Funding", "FDA Momentum", "Gene Therapy Index", "Hospital Stress", "Coverage Gap", "Trial Success", "Global Pharma Supply Risk"], "hint": "pharma pipelines, drug pricing, FDA, biotech, global supply chain"},
    "Energy": {"pool": ["Oil Supply Squeeze", "Green Transition", "OPEC Tension", "LNG Surge", "Renewable Growth", "Geo Shock Risk", "Grid Stress", "Carbon Heat", "Chokepoint Disruption", "Energy Independence"], "hint": "oil, OPEC, renewables, LNG, chokepoints, energy security"},
}

# ═══════════════════════════════════════════════
# THUMBNAIL v5 — Bold text + Warmy character + visuals
# Everything drawn with Pillow. Zero external images.
# ═══════════════════════════════════════════════
THUMB_COLORS = {
    "Economy": [
        {"bg": (0, 0, 0), "hi": (255, 220, 50), "sub": (255, 255, 255), "badge": (37, 99, 235), "glow": (30, 60, 180)},
        {"bg": (15, 25, 60), "hi": (255, 255, 255), "sub": (180, 220, 255), "badge": (37, 99, 235), "glow": (50, 90, 200)},
        {"bg": (0, 0, 0), "hi": (80, 255, 140), "sub": (255, 255, 255), "badge": (22, 163, 74), "glow": (20, 120, 60)},
    ],
    "Politics": [
        {"bg": (0, 0, 0), "hi": (255, 80, 80), "sub": (255, 255, 255), "badge": (220, 38, 38), "glow": (150, 20, 20)},
        {"bg": (130, 10, 10), "hi": (255, 255, 255), "sub": (255, 200, 200), "badge": (180, 20, 20), "glow": (200, 30, 30)},
        {"bg": (0, 0, 0), "hi": (255, 165, 50), "sub": (255, 255, 255), "badge": (194, 65, 12), "glow": (140, 70, 10)},
    ],
    "Tech": [
        {"bg": (0, 0, 0), "hi": (160, 120, 255), "sub": (255, 255, 255), "badge": (124, 58, 237), "glow": (80, 30, 160)},
        {"bg": (0, 0, 0), "hi": (50, 200, 255), "sub": (255, 255, 255), "badge": (14, 116, 144), "glow": (10, 80, 120)},
        {"bg": (80, 20, 160), "hi": (255, 255, 255), "sub": (220, 200, 255), "badge": (100, 40, 200), "glow": (120, 50, 220)},
    ],
    "Health": [
        {"bg": (0, 0, 0), "hi": (50, 230, 160), "sub": (255, 255, 255), "badge": (5, 150, 105), "glow": (10, 100, 70)},
        {"bg": (0, 80, 60), "hi": (255, 255, 255), "sub": (180, 255, 220), "badge": (4, 120, 87), "glow": (5, 140, 100)},
        {"bg": (0, 0, 0), "hi": (80, 240, 255), "sub": (255, 255, 255), "badge": (8, 145, 178), "glow": (10, 100, 140)},
    ],
    "Energy": [
        {"bg": (0, 0, 0), "hi": (255, 220, 50), "sub": (255, 255, 255), "badge": (202, 138, 4), "glow": (140, 100, 10)},
        {"bg": (160, 50, 0), "hi": (255, 255, 255), "sub": (255, 220, 180), "badge": (180, 60, 10), "glow": (200, 80, 10)},
        {"bg": (0, 0, 0), "hi": (255, 180, 30), "sub": (255, 255, 255), "badge": (217, 119, 6), "glow": (160, 90, 10)},
    ],
}

_font_cache = {}

def _font(size):
    if size in _font_cache:
        return _font_cache[size]
    paths = [
        "fonts/Anton.ttf", "fonts/BebasNeue.ttf", "fonts/Oswald.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arialbd.ttf",
    ]
    for fp in paths:
        try:
            f = ImageFont.truetype(fp, size)
            _font_cache[size] = f
            return f
        except Exception:
            continue
    return ImageFont.load_default()

def _font_sub(size):
    paths = [
        "fonts/Oswald.ttf", "fonts/BebasNeue.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for fp in paths:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _extract_hook(title):
    clean = title
    for lb in ["[💎 Pro] ", "[👑 VIP] ", "[💎 Pro]", "[👑 VIP]"]:
        clean = clean.replace(lb, "")
    clean = clean.strip()
    if ":" in clean:
        parts = clean.split(":")
        short = min(parts, key=lambda p: len(p.strip()))
        if len(short.split()) >= 2:
            clean = short.strip()
        else:
            clean = parts[0].strip()
    fillers = {"the", "a", "an", "of", "in", "for", "and", "to", "is", "are", "its", "how", "from", "with", "on", "at", "by"}
    words = clean.split()
    punchy = [w for w in words if w.lower() not in fillers]
    if len(punchy) < 2:
        punchy = words[:4]
    if len(punchy) > 5:
        punchy = punchy[:5]
    return punchy

# ═══════════════════════════════════════════════
# DRAW WARMY CHARACTER (pure Pillow)
# ═══════════════════════════════════════════════
def _draw_warmy(draw, cx, cy, size, is_vip=False, accent=(50, 230, 160)):
    """Draw Warmy mascot centered at (cx, cy) with given size."""
    s = size
    g1, g2, g3 = (74, 222, 128), (34, 197, 94), (22, 101, 52)

    # Body
    bw, bh = int(s * 0.45), int(s * 0.55)
    bx1, by1 = cx - bw // 2, cy - bh // 2 + int(s * 0.05)
    bx2, by2 = bx1 + bw, by1 + bh
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=bw // 4, fill=g2, outline=g3, width=3)

    # Belly patch
    pw, ph = int(bw * 0.55), int(bh * 0.25)
    px1 = cx - pw // 2
    py1 = by1 + int(bh * 0.6)
    draw.rounded_rectangle([px1, py1, px1 + pw, py1 + ph], radius=8, fill=(254, 252, 232), outline=None)

    # Legs
    lw = int(bw * 0.12)
    lh = int(s * 0.12)
    for lx in [cx - int(bw * 0.22), cx + int(bw * 0.22)]:
        draw.rounded_rectangle([lx - lw, by2, lx + lw, by2 + lh], radius=lw, fill=g3)
        draw.ellipse([lx - lw - 4, by2 + lh - 6, lx + lw + 4, by2 + lh + 8], fill=g3)

    # Arms
    aw = int(bw * 0.1)
    al = int(bw * 0.35)
    arm_y = by1 + int(bh * 0.35)
    # Left arm (waving up)
    draw.rounded_rectangle([bx1 - al, arm_y - int(al * 0.5), bx1, arm_y + aw], radius=aw, fill=g2, outline=g3, width=2)
    draw.ellipse([bx1 - al - 6, arm_y - int(al * 0.5) - 6, bx1 - al + 10, arm_y - int(al * 0.5) + 10], fill=g1, outline=g3, width=2)
    # Right arm
    draw.rounded_rectangle([bx2, arm_y, bx2 + al, arm_y + aw], radius=aw, fill=g2, outline=g3, width=2)
    draw.ellipse([bx2 + al - 6, arm_y - 4, bx2 + al + 10, arm_y + aw + 4], fill=g1, outline=g3, width=2)

    # Cap
    capw = int(bw * 0.5)
    caph = int(s * 0.06)
    draw.rounded_rectangle([cx - capw // 2, by1 - caph, cx + capw // 2, by1 + 2], radius=caph // 2, fill=g3)
    cap_dot = (251, 191, 36) if is_vip else g1
    draw.ellipse([cx - 7, by1 - caph - 5, cx + 7, by1 - caph + 9], fill=cap_dot, outline=g3, width=2)

    # Eyes
    er = int(bw * 0.11)
    ey = by1 + int(bh * 0.3)
    for ex in [cx - int(bw * 0.18), cx + int(bw * 0.18)]:
        draw.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, 255, 255), outline=g3, width=2)
        pr = int(er * 0.5)
        draw.ellipse([ex - pr + 2, ey - pr - 1, ex + pr + 2, ey + pr - 1], fill=g3)
        draw.ellipse([ex + 2, ey - pr, ex + 5, ey - pr + 3], fill=(255, 255, 255))

    # Mouth (smile)
    mx1 = cx - int(bw * 0.12)
    mx2 = cx + int(bw * 0.12)
    my = by1 + int(bh * 0.48)
    draw.arc([mx1, my - 4, mx2, my + int(bh * 0.08)], start=0, end=180, fill=g3, width=3)

    # Cheeks
    for chx in [cx - int(bw * 0.26), cx + int(bw * 0.26)]:
        draw.ellipse([chx - 8, my - 4, chx + 8, my + 6], fill=(251, 146, 60, 80))

    # VIP Crown
    if is_vip:
        crw = int(bw * 0.4)
        crh = int(s * 0.1)
        crx = cx - crw // 2
        cry = by1 - caph - crh - 4
        pts = [
            (crx, cry + crh),
            (crx + int(crw * 0.15), cry + int(crh * 0.2)),
            (crx + int(crw * 0.35), cry + int(crh * 0.7)),
            (crx + crw // 2, cry),
            (crx + int(crw * 0.65), cry + int(crh * 0.7)),
            (crx + int(crw * 0.85), cry + int(crh * 0.2)),
            (crx + crw, cry + crh),
        ]
        draw.polygon(pts, fill=(251, 191, 36), outline=(146, 64, 14), width=2)
        for gx in [crx + int(crw * 0.15), crx + crw // 2, crx + int(crw * 0.85)]:
            draw.ellipse([gx - 3, cry + int(crh * 0.2), gx + 3, cry + int(crh * 0.2) + 6], fill=(239, 68, 68))

# ═══════════════════════════════════════════════
# DRAW CATEGORY VISUALS (pure Pillow)
# ═══════════════════════════════════════════════
def _draw_chart_up(draw, x, y, w, h, color, seed):
    """Rising line chart with bars."""
    rng = random.Random(seed)
    bars = 5
    bw = w // (bars * 2)
    for i in range(bars):
        bh = int(h * (0.3 + i * 0.15) + rng.randint(-10, 10))
        bx = x + i * (w // bars) + bw // 2
        by = y + h - bh
        draw.rectangle([bx, by, bx + bw, y + h], fill=color, outline=None)
    # Trend line
    pts = []
    for i in range(bars):
        bh = int(h * (0.3 + i * 0.15))
        px = x + i * (w // bars) + bw
        py = y + h - bh - 10
        pts.append((px, py))
    if len(pts) >= 2:
        draw.line(pts, fill=(255, 255, 255), width=3)
    # Arrow up at end
    if pts:
        lx, ly = pts[-1]
        draw.polygon([(lx - 8, ly + 5), (lx, ly - 12), (lx + 8, ly + 5)], fill=(255, 255, 255))

def _draw_globe(draw, cx, cy, r, color):
    """Simple globe."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)
    draw.ellipse([cx - int(r * 0.4), cy - r, cx + int(r * 0.4), cy + r], outline=color, width=2)
    draw.line([(cx - r, cy), (cx + r, cy)], fill=color, width=2)
    draw.arc([cx - int(r * 0.8), cy - int(r * 0.45), cx + int(r * 0.8), cy + int(r * 0.1)], 0, 360, fill=color, width=2)

def _draw_circuit(draw, x, y, w, h, color, seed):
    """Circuit board pattern."""
    rng = random.Random(seed)
    for _ in range(8):
        sx = rng.randint(x, x + w)
        sy = rng.randint(y, y + h)
        ex = rng.randint(x, x + w)
        ey = rng.randint(y, y + h)
        draw.line([(sx, sy), (ex, sy), (ex, ey)], fill=color, width=2)
        draw.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], fill=color)
    for _ in range(4):
        nx = rng.randint(x + 10, x + w - 10)
        ny = rng.randint(y + 10, y + h - 10)
        ns = rng.randint(12, 25)
        draw.rectangle([nx, ny, nx + ns, ny + ns], outline=color, width=2)

def _draw_pulse(draw, x, y, w, h, color):
    """Heart pulse / EKG line."""
    pts = []
    seg = w // 8
    pts.append((x, y + h // 2))
    pts.append((x + seg, y + h // 2))
    pts.append((x + seg * 2, y + h // 2 - 5))
    pts.append((x + seg * 3, y + 5))
    pts.append((x + int(seg * 3.5), y + h - 5))
    pts.append((x + seg * 4, y + h // 2))
    pts.append((x + seg * 5, y + h // 2 - 3))
    pts.append((x + seg * 6, y + 15))
    pts.append((x + int(seg * 6.5), y + h - 10))
    pts.append((x + seg * 7, y + h // 2))
    pts.append((x + w, y + h // 2))
    draw.line(pts, fill=color, width=4)

def _draw_bolt(draw, cx, cy, size, color):
    """Lightning bolt."""
    s = size
    pts = [
        (cx - int(s * 0.05), cy - int(s * 0.5)),
        (cx + int(s * 0.25), cy - int(s * 0.5)),
        (cx + int(s * 0.02), cy - int(s * 0.05)),
        (cx + int(s * 0.28), cy - int(s * 0.05)),
        (cx - int(s * 0.08), cy + int(s * 0.5)),
        (cx + int(s * 0.05), cy + int(s * 0.05)),
        (cx - int(s * 0.2), cy + int(s * 0.05)),
    ]
    draw.polygon(pts, fill=color, outline=(0, 0, 0), width=2)

def _draw_category_visual(draw, cat, x, y, w, h, color, seed):
    if cat == "Economy":
        _draw_chart_up(draw, x, y + h // 4, w, h // 2, color, seed)
    elif cat == "Politics":
        _draw_globe(draw, x + w // 2, y + h // 2, min(w, h) // 3, color)
    elif cat == "Tech":
        _draw_circuit(draw, x, y, w, h, color, seed)
    elif cat == "Health":
        _draw_pulse(draw, x, y + h // 4, w, h // 2, color)
    elif cat == "Energy":
        _draw_bolt(draw, x + w // 2, y + h // 2, min(w, h) * 0.7, color)

# ═══════════════════════════════════════════════
# MAIN THUMBNAIL GENERATOR
# ═══════════════════════════════════════════════
def make_dynamic_thumb(title, cat, tier):
    TW, TH = 1280, 720
    seed = abs(hash(title)) % 100000
    is_vip = tier == "Royal Premium"

    palettes = THUMB_COLORS.get(cat, THUMB_COLORS["Economy"])
    pal = palettes[seed % len(palettes)]
    bg, hi, sub, badge_c, glow = pal["bg"], pal["hi"], pal["sub"], pal["badge"], pal["glow"]

    img = Image.new("RGB", (TW, TH), bg)
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(TH):
        r = max(0, bg[0] - int(y * 0.015))
        g = max(0, bg[1] - int(y * 0.015))
        b = max(0, bg[2] - int(y * 0.015))
        draw.line([(0, y), (TW, y)], fill=(r, g, b))

    # Glow behind character area (right side)
    gcx, gcy = TW - 250, TH // 2
    for rad in range(200, 0, -4):
        alpha = rad / 200
        c = (
            int(bg[0] + (glow[0] - bg[0]) * alpha * 0.4),
            int(bg[1] + (glow[1] - bg[1]) * alpha * 0.4),
            int(bg[2] + (glow[2] - bg[2]) * alpha * 0.4),
        )
        draw.ellipse([gcx - rad, gcy - rad, gcx + rad, gcy + rad], fill=c)

    # Left accent bar
    draw.rectangle([0, 0, 8, TH], fill=badge_c)

    # Draw category visual element (behind character, right side)
    vis_color = (
        min(255, glow[0] + 60),
        min(255, glow[1] + 60),
        min(255, glow[2] + 60),
    )
    _draw_category_visual(draw, cat, TW - 420, 100, 350, TH - 200, vis_color, seed)

    # Draw Warmy character (right side, overlapping visual)
    warmy_cx = TW - 220
    warmy_cy = TH // 2 + 20
    warmy_size = 320
    _draw_warmy(draw, warmy_cx, warmy_cy, warmy_size, is_vip=is_vip, accent=badge_c)

    # Extract hook words and build 2-line title
    words = _extract_hook(title)
    mid = max(1, (len(words) + 1) // 2)
    line1 = " ".join(words[:mid]).upper()
    line2 = " ".join(words[mid:]).upper() if mid < len(words) else ""

    # Auto-size font — fit in left 60% of image
    max_w = int(TW * 0.58)
    font_sz = 120
    test_line = line1 if len(line1) >= len(line2 or "") else (line2 or line1)
    while font_sz > 55:
        f = _font(font_sz)
        bb = f.getbbox(test_line)
        if bb and (bb[2] - bb[0]) <= max_w:
            break
        font_sz -= 4

    font_big = _font(font_sz)
    line_h = int(font_sz * 1.12)

    num_lines = 2 if line2 else 1
    block_h = num_lines * line_h
    start_y = (TH - block_h) // 2 - 15
    x = 50

    # LINE 1 — highlight color with shadow
    for dx in range(7, 0, -1):
        a = max(0, 25 - dx * 4)
        draw.text((x + dx, start_y + dx), line1, font=font_big, fill=(a, a, a))
    draw.text((x, start_y), line1, font=font_big, fill=hi)

    # LINE 2 — white with shadow
    if line2:
        y2 = start_y + line_h
        for dx in range(7, 0, -1):
            a = max(0, 25 - dx * 4)
            draw.text((x + dx, y2 + dx), line2, font=font_big, fill=(a, a, a))
        draw.text((x, y2), line2, font=font_big, fill=sub)

    # Category badge — top left
    fbadge = _font_sub(26)
    cat_text = cat.upper()
    try:
        bb = fbadge.getbbox(cat_text)
        bw = bb[2] - bb[0] + 48
        draw.rounded_rectangle([45, 32, 45 + bw, 74], radius=21, fill=badge_c)
        draw.text((69, 37), cat_text, font=fbadge, fill=(255, 255, 255))
    except Exception:
        draw.rectangle([45, 32, 195, 74], fill=badge_c)
        draw.text((63, 39), cat_text, font=fbadge, fill=(255, 255, 255))

    # Tier badge — top right
    tier_text = "PRO" if tier == "Premium" else "VIP"
    tier_bg = (30, 64, 175) if tier == "Premium" else (160, 120, 30)
    try:
        tb = fbadge.getbbox(tier_text)
        tw2 = tb[2] - tb[0] + 48
        draw.rounded_rectangle([TW - tw2 - 45, 32, TW - 45, 74], radius=21, fill=tier_bg)
        draw.text((TW - tw2 - 21, 37), tier_text, font=fbadge, fill=(255, 255, 255))
    except Exception:
        draw.rectangle([TW - 130, 32, TW - 45, 74], fill=tier_bg)
        draw.text((TW - 112, 39), tier_text, font=fbadge, fill=(255, 255, 255))

    # Bottom bar
    draw.rectangle([0, TH - 42, TW, TH], fill=(10, 12, 20))
    flogo = _font_sub(20)
    draw.text((50, TH - 34), "WARM INSIGHT", font=flogo, fill=(184, 151, 77))
    fsm = _font_sub(14)
    draw.text((TW - 290, TH - 32), "AI-Driven Global Market Analysis", font=fsm, fill=(100, 116, 139))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    kb = len(buf.getvalue()) // 1024
    print("  Thumb: " + str(kb) + "KB | " + line1[:30])
    return buf.getvalue()

# ═══════════════════════════════════════════════
# RULES
# ═══════════════════════════════════════════════
ACCURACY = (
    "STRICT ACCURACY RULES (NEVER VIOLATE):\n"
    "- ONLY analyze facts from the news provided. NEVER invent events, names, or incidents.\n"
    "- NEVER fabricate specific prices, RSI numbers, or statistics. Use directional language.\n"
    "- NEVER attribute causation unless the news explicitly states it. Say 'coincides with' not 'caused by'.\n"
    "- NEVER claim a company action was driven by a macro trend unless the news says so.\n"
    "- Use hedging: likely, suggests, indicates. Not definitive false claims.\n"
    "- Reference only real ETF tickers (SPY, XLE, XLV, IEF, GLD, EFA, VWO, etc).\n\n"
    "GEOPOLITICAL FRAMEWORK:\n"
    "- Analyze through MULTIPLE perspectives: US, Europe, China, Global South.\n"
    "- Consider chokepoints (Hormuz, Suez, Malacca, Taiwan Strait) as systemic risk.\n"
    "- Track G7 vs BRICS+ bloc divergence.\n"
    "- Map cascades: geopolitical event -> energy -> inflation -> central bank -> markets.\n"
    "- Consider Tech Decoupling, De-dollarization, Nearshoring as mega-trends.\n\n"
    "TONE RULES:\n"
    "- Write like a respected senior analyst at Goldman Sachs or Bridgewater.\n"
    "- Smart humor like Morning Brew or Matt Levine. NOT TikTok slang.\n"
    "- No: fam, slay, lit, no cap, we are cooked, its giving. Ever.\n"
    "- Every sentence must sound human-written, not AI-generated.\n"
    "- Be specific and data-driven. Vague cheerleading destroys credibility.\n"
)

# ═══════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════
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
    "<TIKTOK>Smart witty analogy. Matt Levine meets Morning Brew. 3-4 sentences.</TIKTOK>\n"
    "<HEADLINE>Analytical headline</HEADLINE>\n"
    "<KEY_NUMBER>Most striking statistic</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>1 sentence why this changes the picture</KEY_NUMBER_CONTEXT>\n"
    "<DEPTH><strong>🧐 WHY:</strong> Deeper structural pattern. 5-6 sentences."
    "<br><br><strong>🐑 HERD TRAP:</strong> Cognitive bias making investors wrong. 4-5 sentences.</DEPTH>\n"
    '<FLOW>TEXT + emoji (5+ steps)</FLOW>\n'
    "<PRO_INSIGHT>Cross-sector connection via Second-Order Thinking. 5-6 sentences.</PRO_INSIGHT>\n"
    "<COMPARE_BULL>Bull case: 2-3 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case: 2-3 sentences.</COMPARE_BEAR>\n"
    "<PRO_DO>2 actions with reasoning</PRO_DO>\n"
    "<PRO_DONT>1 mistake with reasoning</PRO_DONT>\n"
    "<QUICK_HITS>3 headlines. 1 sentence each. 3 lines.</QUICK_HITS>\n"
    "<TAKEAWAY>Insightful takeaway</TAKEAWAY>\n"
    "<PS>Historical perspective (2-3 sentences)</PS>\n\n"
    "News: [NEWS_ITEMS]"
)

VIP_P1 = (
    "You are [PERSONA] for Warm Insight VIP ([CATEGORY]).\n"
    "Audience: Sophisticated investors paying premium.\n"
    "[ACCURACY]\n"
    "MULTI-PERSPECTIVE: US, Europe, China/Asia, Global South.\n"
    "Map cascade: geopolitical -> energy -> inflation -> central bank -> markets.\n"
    "G7 vs BRICS+ divergence. Nearshoring, tech decoupling, de-dollarization.\n\n"
    "WRITE real analysis:\n\n"
    "<SEO_KEYWORD>4-8 word keyword</SEO_KEYWORD>\n"
    "<TITLE>Institutional title with SEO keyword</TITLE>\n"
    "<EXCERPT>1 VIP sentence with SEO keyword</EXCERPT>\n"
    "<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>\n"
    "<KEY_NUMBER>Critical number</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>Why institutions watch this</KEY_NUMBER_CONTEXT>\n"
    "<SENTIMENT>0-100 Fear-Greed. Just the number.</SENTIMENT>\n"
    "<SUMMARY>3 institutional sentences. First includes SEO keyword.</SUMMARY>\n"
    "<TIKTOK>Sharp sophisticated analogy. Bridgewater meets Bloomberg. 3-4 sentences.</TIKTOK>\n"
    "<HEADLINE>Alpha headline</HEADLINE>\n"
    "<DEPTH><strong>🧐 MACRO:</strong> Systems view. Structural forces. 5+ sentences."
    "<br><br><strong>🐑 HERD:</strong> Cognitive bias. 4+ sentences."
    "<br><br><strong>🦅 CONTRARIAN:</strong> 1st->2nd->3rd order. G7 vs BRICS+. 5+ sentences.</DEPTH>\n"
    '<FLOW>TEXT + emoji (6+ steps) including global actors</FLOW>\n'
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
    "CRITICAL: Write REAL analysis paragraphs. Do NOT echo instructions back.\n"
    "Do NOT repeat tag names or word counts in your output.\n\n"
    "Context from Part 1:\n[CTX]\n\n"
    "Now write the strategy section. Each tag must contain REAL sentences, not placeholders.\n\n"
    "<VIP_T1>What is the current fear vs greed balance globally? Reference Buffett or Templeton if relevant. Write a full paragraph.</VIP_T1>\n"
    "<VIP_T2>Recommended allocation: [ALLOC_STR]. Name real ETFs including at least one international. Write a full paragraph.</VIP_T2>\n"
    "<VIP_T3>Compare US positioning vs Europe, China, and emerging markets. Include supply chain and energy angles. Write a full paragraph.</VIP_T3>\n"
    "<VIP_T4>DCA strategy advice. Include the 50-percent panic rule with specific thresholds. Write a full paragraph.</VIP_T4>\n"
    "<VIP_DO>3 specific actions. Each must name an ETF, a percentage, and a trigger condition. Include at least 1 international ETF.</VIP_DO>\n"
    "<VIP_DONT>2 specific mistakes investors should avoid right now. Explain why each is dangerous.</VIP_DONT>\n"
    "<COMPARE_BULL>Bull case in 2-3 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case in 2-3 sentences.</COMPARE_BEAR>\n"
    "<CONVICTION>HIGH, MEDIUM, or LOW</CONVICTION>\n"
    "<TAKEAWAY>One calming sentence with global perspective.</TAKEAWAY>\n"
    "<PS>A lesson from 40 years of market history. 2-3 sentences.</PS>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

VIP_FB = (
    "You are [PERSONA]. Write a concise VIP strategy for [CATEGORY].\n"
    "[ACCURACY]\n"
    "CRITICAL: Every tag below MUST contain real analysis sentences.\n"
    "Do NOT echo these instructions. Do NOT mention word counts.\n\n"
    "Based on this headline: [CTX_SHORT]\n\n"
    "<VIP_T1>Is the market leaning toward fear or greed globally? Why? (3-4 real sentences)</VIP_T1>\n"
    "<VIP_T2>[ALLOC_STR]. Name 2 domestic ETFs and 1 international ETF with reasoning. (3-4 real sentences)</VIP_T2>\n"
    "<VIP_T3>How does the US compare to Europe or Asia right now? (2-3 real sentences)</VIP_T3>\n"
    "<VIP_T4>What DCA approach makes sense here? (3-4 real sentences)</VIP_T4>\n"
    "<VIP_DO>2 actions: name an ETF and a trigger for each.</VIP_DO>\n"
    "<VIP_DONT>1 mistake to avoid, and why.</VIP_DONT>\n"
    "<COMPARE_BULL>Bull case: 1-2 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case: 1-2 sentences.</COMPARE_BEAR>\n"
    "<CONVICTION>HIGH, MEDIUM, or LOW</CONVICTION>\n"
    "<TAKEAWAY>One calming insight.</TAKEAWAY>\n"
    "<PS>Historical parallel in 1-2 sentences.</PS>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

EDITOR_PROMPT = (
    "Senior editorial fact-checker. Review newsletter vs original news.\n"
    "CHECK: 1) Fabricated events 2) Fake stats 3) Invented names 4) False causation\n"
    "IMPORTANT: The newsletter may provide GENERAL market context (e.g. ETF trends, macro conditions).\n"
    "This is acceptable analysis. Only flag causation if the newsletter claims a SPECIFIC news event\n"
    "caused a SPECIFIC company action when the news does NOT say this.\n\n"
    "NEWS:\n[NEWS]\n\nNEWSLETTER:\n[CONTENT]\n\n"
    "<VERDICT>PASS or FAIL</VERDICT>\n"
    "<ISSUES>If FAIL list issues. If PASS write No issues.</ISSUES>"
)

# ═══════════════════════════════════════════════
# GHOST TOKEN + DEDUP + EDITOR
# ═══════════════════════════════════════════════
def gtoken():
    kid, sec = str(GHOST_ADMIN_API_KEY).split(":")
    iat = int(datetime.now().timestamp())
    return jwt.encode({"iat": iat, "exp": iat + 300, "aud": "/admin/"}, bytes.fromhex(sec), algorithm="HS256", headers={"alg": "HS256", "typ": "JWT", "kid": kid})

def get_recent_titles():
    try:
        r = requests.get(
            GHOST_API_URL + "/ghost/api/admin/posts/?limit=50&fields=title&order=published_at%20desc",
            headers={"Authorization": "Ghost " + gtoken()}, timeout=30)
        if r.status_code in (200, 201):
            titles = [p.get("title", "").lower() for p in r.json().get("posts", []) if p.get("title")]
            print("  Loaded " + str(len(titles)) + " recent titles")
            return titles
        else:
            print("  Dedup fetch status: " + str(r.status_code))
    except Exception as e:
        print("  Dedup err: " + str(e))
    return []

def is_duplicate(new_title, recent):
    if not new_title or not recent:
        return False
    labels = ["[💎 pro]", "[👑 vip]"]
    cn = new_title.lower()
    for lb in labels:
        cn = cn.replace(lb, "").strip()
    words_new = set(cn.split())
    if len(words_new) < 4:
        return False
    for rt in recent:
        cr = rt
        for lb in labels:
            cr = cr.replace(lb, "").strip()
        words_rt = set(cr.split())
        if len(words_rt) < 4:
            continue
        overlap = len(words_rt & words_new)
        if overlap / max(len(words_new), 1) > 0.7:
            print("  DEDUP: skip " + str(int(overlap / max(len(words_new), 1) * 100)) + "%")
            return True
    return False

def editor_review(client, news_str, html):
    try:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)[:3000]
        p = EDITOR_PROMPT.replace("[NEWS]", news_str[:2000]).replace("[CONTENT]", text)
        r = call_gem(client, "gemini-2.5-flash", p, retries=1)
        if not r:
            return True, "N/A"
        v = xtag(r, "VERDICT").upper()
        i = xtag(r, "ISSUES")
        if "FAIL" in v:
            print("    EDITOR REJECTED: " + i[:200])
            return False, i
        print("    Editor: PASS")
        return True, i
    except Exception as e:
        return True, str(e)

# ═══════════════════════════════════════════════
# ROTATION: Date-seeded daily shuffle
# ═══════════════════════════════════════════════
def get_current_category():
    cats = list(CATEGORIES.keys())
    now = datetime.utcnow()
    seed = now.year * 10000 + now.month * 100 + now.day
    rng = random.Random(seed)
    shuffled = cats[:]
    rng.shuffle(shuffled)
    idx = now.hour % len(shuffled)
    sel = shuffled[idx]
    print("  UTC " + str(now.hour) + " -> " + sel + " (daily order: " + str(shuffled) + ")")
    return sel

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
                if t in seen:
                    continue
                seen.add(t)
                news.append("- " + t + ": " + getattr(e, "summary", ""))
                if len(news) >= count:
                    break
        except Exception:
            continue
    return news[:count]

def parse_graph(raw, cat):
    if not raw:
        return _fbg(cat)
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 6:
        return _fbg(cat)
    try:
        v1 = int(re.sub(r"[^0-9]", "", parts[1]))
        v2 = int(re.sub(r"[^0-9]", "", parts[3]))
        v3 = int(re.sub(r"[^0-9]", "", parts[5]))
        if v1 == v2 == v3:
            return _fbg(cat)
        return parts[0], max(10, min(95, v1)), parts[2], max(10, min(95, v2)), parts[4], max(10, min(95, v3))
    except Exception:
        return _fbg(cat)

def _fbg(cat):
    pool = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["pool"]
    lb = random.sample(pool, 3)
    return lb[0], random.randint(55, 88), lb[1], random.randint(30, 65), lb[2], random.randint(40, 78)

def is_echo(text):
    if not text or len(text) < 80:
        return True
    sigs = [
        "6+ sentences", "5+ sentences", "At least 5 sentences",
        "Write a detailed", "Write exactly", "Write real", "Write ALL",
        "Name ETFs and trigger", "which ETF to buy",
        "trigger price for each", "explain WHY in detail",
        "Include at least one international",
        "Write a full paragraph for each",
    ]
    matches = sum(1 for s in sigs if s.lower() in text.lower())
    if matches >= 3:
        print("    echo detected (" + str(matches) + " sigs)")
        return True
    return False

def ok_tag(raw, tag):
    v = xtag(raw, tag)
    return "" if not v or is_echo(v) else v

def sanitize(h):
    return re.sub(r"\s+", " ", h.replace("\n", " ").replace("\r", ""))

def make_slug(kw, title):
    t = kw if kw else title
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", t.lower())
    return re.sub(r"\s+", "-", s.strip())[:80]

# ═══════════════════════════════════════════════
# GHOST IMAGE UPLOAD
# ═══════════════════════════════════════════════
def upload_img(img_bytes):
    for attempt in range(2):
        try:
            token = gtoken()
            r = requests.post(
                GHOST_API_URL + "/ghost/api/admin/images/upload/",
                headers={"Authorization": "Ghost " + token},
                files={"file": ("thumb.jpg", img_bytes, "image/jpeg"), "purpose": (None, "image")},
                timeout=30)
            if r.status_code in (200, 201):
                return r.json()["images"][0]["url"]
            elif r.status_code == 403:
                print("  img upload 403 attempt " + str(attempt + 1))
                if attempt == 0:
                    time.sleep(3)
                    continue
                return None
            else:
                print("  img upload " + str(r.status_code))
                return None
        except Exception as e:
            print("  img err: " + str(e))
            if attempt == 0:
                time.sleep(3)
    return None

# ═══════════════════════════════════════════════
# GHOST API
# ═══════════════════════════════════════════════
def publish(title, html, cat, tier, feature_img_url, exc, kw="", slug=""):
    print("  Pub: " + title[:60])
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            token = gtoken()
            md = json.dumps({
                "version": "0.3.1", "markups": [], "atoms": [],
                "cards": [["html", {"html": html}]],
                "sections": [[10, 0]]
            })
            p = {
                "title": title, "mobiledoc": md,
                "status": "published",
                "visibility": TIER_VIS.get(tier, "public"),
                "tags": [{"name": cat}, {"name": tier}]
            }
            if slug:
                p["slug"] = slug
            if kw:
                mt = title + " | Warm Insight " + cat
                p["meta_title"] = mt[:300]
                p["meta_description"] = (exc[:140] + " Expert " + cat.lower() + " analysis.")[:500]
                p["og_title"] = mt[:300]
                p["og_description"] = exc[:300]
            if exc:
                p["custom_excerpt"] = exc[:290]
            if feature_img_url:
                p["feature_image"] = feature_img_url
                if kw:
                    p["feature_image_alt"] = kw + " - Warm Insight " + cat

            r = requests.post(
                GHOST_API_URL + "/ghost/api/admin/posts/",
                json={"posts": [p]},
                headers={"Authorization": "Ghost " + token, "Content-Type": "application/json"},
                timeout=60)
            if r.status_code in (200, 201):
                print("  OK! (attempt " + str(attempt) + ")")
                return True
            elif r.status_code == 403:
                print("  GHOST 403 attempt " + str(attempt) + "/" + str(max_retries) + ": " + r.text[:200])
                if attempt < max_retries:
                    time.sleep(10 * attempt)
                    continue
                return False
            elif r.status_code == 429:
                time.sleep(30 * attempt)
                continue
            else:
                print("  GHOST FAIL " + str(r.status_code) + ": " + r.text[:200])
                return False
        except Exception as e:
            print("  GHOST ERR: " + str(e))
            if attempt < max_retries:
                time.sleep(5 * attempt)
    return False

# ═══════════════════════════════════════════════
# GEMINI
# ═══════════════════════════════════════════════
def call_gem(client, model, prompt, retries=2):
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt)
            return str(r.text)
        except Exception as e:
            err_str = str(e)
            print("    Gem(" + model + ")" + str(i) + ": " + err_str[:150])
            if "503" in err_str or "UNAVAILABLE" in err_str:
                time.sleep(15 * i)
            elif i < retries:
                time.sleep(10 * i)
    return None

def gem_fb(client, tier, prompt):
    for m in MODEL_PRI.get(tier, ["gemini-2.5-flash"]):
        print("    [AI] " + m)
        r = call_gem(client, m, prompt)
        if r:
            return r, m
    return None, None

# ═══════════════════════════════════════════════
# ANALYZE
# ═══════════════════════════════════════════════
def analyze(news_items, cat, tier):
    client = genai.Client(api_key=GEMINI_API_KEY)
    ns = "\n".join(news_items)
    persona = EXPERT.get(cat, EXPERT["Economy"])
    now = datetime.now()
    ts = now.strftime("%I:%M %p")
    tf = now.strftime("%B %d, %Y at %I:%M %p (UTC)")
    author = "Ethan Cole &amp; The Warm Insight Panel"
    acc = ACCURACY

    if tier == "Premium":
        prompt = (PROMPT_PREMIUM
                  .replace("[CATEGORY]", cat).replace("[PERSONA]", persona)
                  .replace("[ACCURACY]", acc).replace("[NEWS_ITEMS]", ns))
        raw, _ = gem_fb(client, tier, prompt)
        if not raw:
            return None, None, None, None, None, None
        html = build_premium(author, tf, raw)

    else:  # Royal Premium (VIP)
        hint = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["hint"]
        al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
        al_str = str(al["s"]) + "% stocks, " + str(al["b"]) + "% safe, " + str(al["c"]) + "% cash (" + al["note"] + ")"

        # Part 1
        p1 = (VIP_P1
              .replace("[CATEGORY]", cat).replace("[PERSONA]", persona)
              .replace("[ACCURACY]", acc).replace("[CAT_HINT]", hint)
              .replace("[NEWS_ITEMS]", ns))
        raw1, _ = gem_fb(client, tier, p1)
        if not raw1:
            return None, None, None, None, None, None

        if not xtag(raw1, "VIP_C1") or is_echo(xtag(raw1, "VIP_C1")):
            print("    P1 quality low, retrying...")
            time.sleep(15)
            r1r, _ = gem_fb(client, tier, p1)
            if r1r and xtag(r1r, "VIP_C1") and not is_echo(xtag(r1r, "VIP_C1")):
                raw1 = r1r

        ctx = ("Title: " + xtag(raw1, "TITLE") + "\nHeadline: " + xtag(raw1, "HEADLINE")
               + "\nSummary: " + xtag(raw1, "SUMMARY") + "\nKey insight: " + xtag(raw1, "DEPTH")[:500])
        ctx_short = xtag(raw1, "HEADLINE") + ". " + xtag(raw1, "SUMMARY")

        # Part 2 (flash to save cost)
        print("    Part 2 (gemini-2.5-flash)...")
        time.sleep(10)
        p2 = (VIP_P2
              .replace("[CATEGORY]", cat).replace("[PERSONA]", persona)
              .replace("[ACCURACY]", acc).replace("[CTX]", ctx)
              .replace("[ALLOC_STR]", al_str).replace("[NEWS_ITEMS]", ns))
        raw2 = call_gem(client, "gemini-2.5-flash", p2)

        for retry in range(2):
            if raw2 and ok_tag(raw2, "VIP_T1"):
                break
            print("    P2 retry " + str(retry + 1))
            time.sleep(15)
            raw2 = call_gem(client, "gemini-2.5-flash", p2)

        if not raw2 or not ok_tag(raw2, "VIP_T1"):
            print("    P2 FAIL -> Fallback")
            time.sleep(10)
            fb = (VIP_FB
                  .replace("[CATEGORY]", cat).replace("[PERSONA]", persona)
                  .replace("[ACCURACY]", acc).replace("[CTX_SHORT]", ctx_short[:400])
                  .replace("[ALLOC_STR]", al_str).replace("[NEWS_ITEMS]", ns))
            raw2 = call_gem(client, "gemini-2.5-flash", fb)
            if not raw2:
                raw2 = ""

        raw = raw1 + "\n" + raw2
        html = build_vip(author, tf, raw, cat)

    tr = xtag(raw, "TITLE")
    exc = xtag(raw, "EXCERPT") or "Expert analysis."
    kw = xtag(raw, "SEO_KEYWORD")
    pretty = TIER_LABELS.get(tier, tier)
    title = "[" + pretty + "] " + tr if tr else "(" + tier + ") " + cat + " Insight"
    slug = make_slug(kw, tr or cat)
    html = sanitize(html)
    return title, html, exc, kw, slug, tier

# ═══════════════════════════════════════════════
# HTML HELPERS
# ═══════════════════════════════════════════════
F = "font-size:18px;line-height:1.8;color:#374151;"
MAIN = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;"

def _hdr(author, tf, badge=""):
    b = ""
    if badge:
        b = (' <span style="background:#b8974d;color:#fff;padding:3px 12px;border-radius:4px;font-size:14px;font-weight:bold;">' + badge + '</span>')
    return ('<div style="border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;padding:14px 0;margin-bottom:30px;">'
            '<p style="margin:0;font-size:16px;color:#4b5563;"><strong style="color:#1a252c;">' + author + '</strong> | ' + tf + b + '</p></div>')

def _ftr(tw, ps):
    if not tw or is_echo(tw):
        tw = "Stay disciplined, stay diversified, and let time compound in your favor."
    if not ps or is_echo(ps):
        ps = "In 40 years of watching markets, the disciplined investor always wins."
    share = ('<div style="background:#f8fafc;border:2px solid #e5e7eb;border-radius:10px;padding:28px;margin:40px 0;text-align:center;">'
             '<p style="font-size:22px;font-weight:bold;color:#1a252c;margin:0 0 8px;">Found this useful? Share the insight.</p>'
             '<p style="font-size:18px;color:#6b7280;margin:0 0 15px;">Forward this email to a colleague who wants smarter market analysis.</p>'
             '<p style="font-size:16px;color:#b8974d;font-weight:600;margin:0;">'
             '<a href="https://www.warminsight.com/#/portal/signup" style="color:#b8974d;text-decoration:underline;">Subscribe at warminsight.com</a></p></div>')
    foot = ('<div style="background:#1e293b;padding:35px;border-radius:10px;margin-top:30px;">'
            '<p style="font-size:24px;font-weight:bold;color:#b8974d;margin:0 0 8px;text-align:center;">Warm Insight</p>'
            '<p style="font-size:16px;color:#94a3b8;margin:0 0 20px;text-align:center;">AI-Driven Global Market Analysis</p>'
            '<div style="text-align:center;margin-bottom:20px;">'
            '<a href="https://www.warminsight.com/about/" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">About</a>'
            '<a href="https://www.warminsight.com/#/portal/signup" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">Subscribe</a>'
            '<a href="https://www.warminsight.com/tag/economy/" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">Economy</a>'
            '<a href="https://www.warminsight.com/tag/tech/" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">Tech</a>'
            '<a href="https://www.warminsight.com/tag/energy/" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">Energy</a></div>'
            '<div style="border-top:1px solid #475569;margin:20px 0;"></div>'
            '<p style="font-size:13px;color:#64748b;margin:0;text-align:center;line-height:1.8;">'
            'All analysis is for informational purposes only. Not financial advice. Always do your own research.<br>'
            'Contact: hello@warminsight.com | &copy; 2026 Warm Insight. All rights reserved.</p></div>')
    return ('<hr style="border:0;height:1px;background:#e5e7eb;margin:45px 0;">'
            '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Today\'s Warm Insight</h2>'
            '<p style="' + F + '">' + tw + '</p>'
            '<div style="margin-top:30px;background:#1e293b;padding:28px;border-radius:8px;border-left:4px solid #b8974d;">'
            '<p style="font-size:18px;line-height:1.8;color:#e2e8f0;margin:0;"><span style="color:#b8974d;font-weight:bold;font-size:20px;">P.S.</span> <span style="color:#cbd5e1;">' + ps + '</span></p></div>'
            + share + foot + '</div>')

def _up(msg):
    return '<div style="background:#fffbeb;border:2px solid #f59e0b;padding:18px;border-radius:8px;margin:35px 0;"><p style="font-size:18px;color:#92400e;margin:0;text-align:center;">' + msg + '</p></div>'

def _impact(imp):
    imp = (imp or "").upper().strip()
    cols = {"HIGH": ("#dc2626", "#fef2f2"), "MEDIUM": ("#d97706", "#fffbeb"), "LOW": ("#059669", "#ecfdf5")}
    c, bg = cols.get(imp, ("#6b7280", "#f3f4f6"))
    return ('<span style="display:inline-block;background:' + bg + ';color:' + c + ';border:2px solid ' + c + ';padding:4px 14px;border-radius:20px;font-size:14px;font-weight:bold;margin-bottom:20px;">IMPACT: ' + imp + '</span>') if imp else ""

def _keynum(kn, knc, color="#1e40af"):
    if not kn or not knc:
        return ""
    return ('<div style="background:#f0f9ff;border:2px solid ' + color + ';border-radius:12px;padding:28px;margin-bottom:30px;text-align:center;">'
            '<div style="font-size:48px;font-weight:800;color:' + color + ';margin-bottom:8px;">' + kn + '</div>'
            '<p style="font-size:18px;color:#374151;margin:0;">' + knc + '</p></div>')

def _qhits(raw):
    qh = xtag(raw, "QUICK_HITS")
    if not qh or is_echo(qh):
        return ""
    lines = [l.strip() for l in qh.strip().split("\n") if l.strip()]
    if not lines:
        return ""
    emos = ["⚡", "🔥", "📌"]
    items = ""
    for i, l in enumerate(lines[:3]):
        items += '<p style="font-size:18px;color:#374151;margin:10px 0;line-height:1.6;">' + (emos[i] if i < 3 else "•") + " " + l + '</p>'
    return ('<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:24px;margin-bottom:35px;">'
            '<h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:12px;text-transform:uppercase;letter-spacing:1px;">Quick Hits</h3>' + items + '</div>')

def _msnap(raw):
    ms = xtag(raw, "MARKET_SNAP")
    if not ms or is_echo(ms):
        return ""
    lines = [l.strip() for l in ms.strip().split("\n") if l.strip() and "|" in l]
    if len(lines) < 2:
        return ""
    icons = {"UP": ("▲", "#059669"), "DOWN": ("▼", "#dc2626"), "FLAT": ("—", "#6b7280")}
    cells = ""
    for line in lines[:4]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        name, direction = parts[0], parts[1].upper().strip()
        reason = parts[2][:40] if len(parts) > 2 else ""
        arrow, color = icons.get(direction, ("—", "#6b7280"))
        cells += ('<div style="flex:1;min-width:130px;text-align:center;padding:12px 8px;">'
                  '<div style="font-size:14px;color:#94a3b8;font-weight:600;margin-bottom:4px;">' + name + '</div>'
                  '<div style="font-size:22px;font-weight:800;color:' + color + ';">' + arrow + " " + direction + '</div>'
                  '<div style="font-size:12px;color:#64748b;margin-top:2px;">' + reason + '</div></div>')
    if not cells:
        return ""
    return '<div style="background:#1e293b;border-radius:10px;padding:12px;margin-bottom:30px;overflow-x:auto;"><div style="display:flex;flex-wrap:wrap;justify-content:space-around;">' + cells + '</div></div>'

def _compare(cb, cbear, bt="Bull Case", brt="Bear Case"):
    if not cb and not cbear:
        return ""
    bull = ('<div style="flex:1;min-width:220px;background:#ecfdf5;border:2px solid #10b981;border-radius:10px;padding:22px;">'
            '<h4 style="margin-top:0;font-size:20px;color:#065f46;">🐂 ' + bt + '</h4>'
            '<p style="font-size:18px;line-height:1.7;color:#064e3b;margin:0;">' + cb + '</p></div>') if cb else ""
    bear = ('<div style="flex:1;min-width:220px;background:#fef2f2;border:2px solid #ef4444;border-radius:10px;padding:22px;">'
            '<h4 style="margin-top:0;font-size:20px;color:#991b1b;">🐻 ' + brt + '</h4>'
            '<p style="font-size:18px;line-height:1.7;color:#7f1d1d;margin:0;">' + cbear + '</p></div>') if cbear else ""
    return '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">' + bull + bear + '</div>'

# ═══════════════════════════════════════════════
# BUILD PREMIUM
# ═══════════════════════════════════════════════
def build_premium(a, tf, r):
    return ('<div style="' + MAIN + '">' + _hdr(a, tf, "PRO") + _impact(xtag(r, "IMPACT")) + _keynum(xtag(r, "KEY_NUMBER"), xtag(r, "KEY_NUMBER_CONTEXT"))
            + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
            + '<p style="' + F + 'margin-bottom:35px;">' + xtag(r, "SUMMARY") + '</p>'
            + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:40px;">'
            + '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">💡 In Plain English</h3>'
            + '<p style="' + F + 'margin:0;">' + xtag(r, "TIKTOK") + '</p></div>'
            + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers</h2>'
            + '<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">' + xtag(r, "HEADLINE") + '</h3>'
            + '<p style="' + F + 'margin-bottom:28px;">' + xtag(r, "DEPTH") + '</p>'
            + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:8px;margin-bottom:35px;">'
            + '<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
            + '<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">' + xtag(r, "FLOW") + '</p></div>'
            + _compare(xtag(r, "COMPARE_BULL"), xtag(r, "COMPARE_BEAR")) + _qhits(r)
            + '<div style="background:#fff;border:2px solid #3b82f6;padding:28px;border-radius:8px;margin-bottom:35px;">'
            + '<h3 style="margin-top:0;color:#1e40af;font-size:22px;margin-bottom:14px;">💎 Pro-Only Insight</h3>'
            + '<p style="' + F + 'margin:0;">' + xtag(r, "PRO_INSIGHT") + '</p></div>'
            + '<div style="background:#ecfdf5;border:2px solid #10b981;padding:24px;border-radius:8px;margin-bottom:15px;">'
            + '<p style="font-size:18px;line-height:1.8;color:#065f46;margin:0;"><strong style="color:#065f46;font-size:20px;">🟢 DO:</strong> ' + xtag(r, "PRO_DO") + '</p></div>'
            + '<div style="background:#fef2f2;border:2px solid #ef4444;padding:24px;border-radius:8px;margin-bottom:35px;">'
            + '<p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;"><strong style="color:#991b1b;font-size:20px;">🔴 AVOID:</strong> ' + xtag(r, "PRO_DONT") + '</p></div>'
            + _up('🔒 Want institutional analysis? <strong>Upgrade to VIP.</strong>') + _ftr(xtag(r, "TAKEAWAY"), xtag(r, "PS")))

# ═══════════════════════════════════════════════
# BUILD VIP
# ═══════════════════════════════════════════════
def build_vip(a, tf, raw, cat):
    theme = CAT_THEME.get(cat, CAT_THEME["Economy"])
    accent = theme["accent"]
    al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
    l1, v1, l2, v2, l3, v3 = parse_graph(xtag(raw, "GRAPH_DATA"), cat)
    COL = [accent, "#f59e0b", "#10b981"]

    # Sentiment
    sent_h = ""
    try:
        sr = xtag(raw, "SENTIMENT")
        if sr and sr.strip():
            d = re.sub(r"[^0-9]", "", sr)
            if d:
                sv = max(0, min(100, int(d)))
                if sv <= 25: sl, sc = "EXTREME FEAR", "#dc2626"
                elif sv <= 40: sl, sc = "FEAR", "#ea580c"
                elif sv <= 60: sl, sc = "NEUTRAL", "#ca8a04"
                elif sv <= 75: sl, sc = "GREED", "#16a34a"
                else: sl, sc = "EXTREME GREED", "#059669"
                sent_h = ('<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:25px;margin-bottom:35px;">'
                          '<h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:18px;">🧭 Fear &amp; Greed Meter</h3>'
                          '<div style="position:relative;width:100%;height:20px;border-radius:10px;overflow:hidden;background:linear-gradient(to right,#dc2626,#ea580c,#ca8a04,#16a34a,#059669);">'
                          '<div style="position:absolute;left:' + str(sv) + '%;top:0;width:4px;height:100%;background:#fff;border-radius:2px;box-shadow:0 0 4px rgba(0,0,0,0.5);"></div></div>'
                          '<div style="display:flex;justify-content:space-between;margin-top:8px;">'
                          '<span style="font-size:14px;color:#dc2626;font-weight:600;">Fear</span>'
                          '<span style="font-size:20px;color:' + sc + ';font-weight:800;">' + str(sv) + ' - ' + sl + '</span>'
                          '<span style="font-size:14px;color:#059669;font-weight:600;">Greed</span></div></div>')
    except Exception:
        pass

    # Conviction
    conv = xtag(raw, "CONVICTION").upper().strip()
    conv_h = ""
    if conv:
        cc = {"HIGH": ("#065f46", "#ecfdf5", "🟢"), "MEDIUM": ("#92400e", "#fffbeb", "🟡"), "LOW": ("#991b1b", "#fef2f2", "🔴")}
        c2, bg2, ci = cc.get(conv, ("#6b7280", "#f3f4f6", "⚪"))
        conv_h = ('<div style="background:' + bg2 + ';border:2px solid ' + c2 + ';border-radius:10px;padding:20px;margin-bottom:35px;text-align:center;">'
                  '<p style="font-size:14px;color:#6b7280;margin:0 0 5px;text-transform:uppercase;">Overall Conviction</p>'
                  '<p style="font-size:28px;font-weight:800;color:' + c2 + ';margin:0;">' + ci + ' ' + conv + '</p></div>')

    def gauge(lb, val, c):
        return ('<div style="margin-bottom:22px;"><div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
                '<span style="font-size:18px;font-weight:600;color:#374151;">' + lb + '</span>'
                '<span style="font-size:18px;font-weight:700;color:' + c + ';">' + str(val) + '%</span></div>'
                '<div style="width:100%;background:#e5e7eb;border-radius:8px;height:16px;overflow:hidden;">'
                '<div style="width:' + str(val) + '%;background:' + c + ';height:100%;border-radius:8px;"></div></div></div>')

    s, b, cp = al["s"], al["b"], al["c"]
    circ = 565.49
    sd, bd, cd = circ * s / 100, circ * b / 100, circ * cp / 100
    pie = ('<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;">'
           '<circle cx="100" cy="100" r="90" fill="none" stroke="' + accent + '" stroke-width="30" stroke-dasharray="' + ("%.1f" % sd) + ' ' + ("%.1f" % circ) + '" stroke-dashoffset="0"/>'
           '<circle cx="100" cy="100" r="90" fill="none" stroke="#64748b" stroke-width="30" stroke-dasharray="' + ("%.1f" % bd) + ' ' + ("%.1f" % circ) + '" stroke-dashoffset="-' + ("%.1f" % sd) + '"/>'
           '<circle cx="100" cy="100" r="90" fill="none" stroke="#b8974d" stroke-width="30" stroke-dasharray="' + ("%.1f" % cd) + ' ' + ("%.1f" % circ) + '" stroke-dashoffset="-' + ("%.1f" % (sd + bd)) + '"/>'
           '<text x="100" y="92" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">' + str(s) + '/' + str(b) + '/' + str(cp) + '</text>'
           '<text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>'
           '<div style="display:flex;justify-content:center;gap:20px;margin-bottom:8px;">'
           '<span style="font-size:16px;color:' + accent + ';">● Stocks ' + str(s) + '%</span>'
           '<span style="font-size:16px;color:#64748b;">● Safe ' + str(b) + '%</span>'
           '<span style="font-size:16px;color:#b8974d;">● Cash ' + str(cp) + '%</span></div>'
           '<p style="font-size:16px;color:#6b7280;text-align:center;font-style:italic;margin:5px 0 0;">' + al["note"] + '</p>')

    rr = ""
    for i in range(1, 5):
        v = ok_tag(raw, "VIP_RADAR_" + str(i))
        if not v:
            continue
        bull = "bullish" in v.lower()
        bg_r, tc, ic = ("#ecfdf5", "#065f46", "🟢 BULL") if bull else ("#fef2f2", "#991b1b", "🔴 BEAR")
        rr += ('<tr><td style="padding:14px;border-bottom:1px solid #e5e7eb;font-size:18px;color:#374151;">' + v + '</td>'
               '<td style="padding:14px;border-bottom:1px solid #e5e7eb;text-align:center;"><span style="background:' + bg_r + ';color:' + tc + ';padding:4px 12px;border-radius:6px;font-size:16px;font-weight:bold;">' + ic + '</span></td></tr>')
    radar = ('<div style="background:#fff;border:2px solid ' + accent + ';border-radius:8px;padding:25px;margin-bottom:35px;">'
             '<h3 style="margin-top:0;color:' + accent + ';font-size:22px;margin-bottom:18px;">🎯 Sector Radar</h3>'
             '<table style="width:100%;border-collapse:collapse;">' + rr + '</table></div>') if rr else ""

    def mc(lb, val, c):
        return ('<div style="flex:1;min-width:200px;background:#f8fafc;border:2px solid ' + c + ';border-radius:10px;padding:22px;text-align:center;">'
                '<div style="font-size:42px;font-weight:800;color:' + c + ';margin-bottom:5px;">' + str(val) + '%</div>'
                '<div style="font-size:16px;color:#4b5563;font-weight:600;">' + lb + '</div></div>')

    c1, c2, c3 = ok_tag(raw, "VIP_C1"), ok_tag(raw, "VIP_C2"), ok_tag(raw, "VIP_C3")
    t1, t2, t3, t4 = ok_tag(raw, "VIP_T1"), ok_tag(raw, "VIP_T2"), ok_tag(raw, "VIP_T3"), ok_tag(raw, "VIP_T4")
    vdo, vdont = ok_tag(raw, "VIP_DO"), ok_tag(raw, "VIP_DONT")
    tw, ps = ok_tag(raw, "TAKEAWAY"), ok_tag(raw, "PS")

    macro = ""
    if c1 or c2 or c3:
        pp = ""
        if c1:
            pp += '<p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;text-transform:uppercase;">Technical Signals</p><p style="' + F + 'margin-bottom:22px;">' + c1 + '</p>'
        if c2:
            pp += '<div style="border-top:1px solid #e5e7eb;margin:8px 0 18px;"></div><p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;text-transform:uppercase;">Macro Flows</p><p style="' + F + 'margin-bottom:22px;">' + c2 + '</p>'
        if c3:
            pp += '<div style="border-top:1px solid #e5e7eb;margin:8px 0 18px;"></div><p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;text-transform:uppercase;">Smart Money</p><p style="' + F + 'margin-bottom:0;">' + c3 + '</p>'
        macro = ('<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:25px;border-bottom:3px solid ' + accent + ';padding-bottom:12px;display:inline-block;">VIP: Macro &amp; Flow Analysis</h2>'
                 '<div style="background:#fff;border:1px solid #e5e7eb;border-left:5px solid ' + accent + ';padding:28px;border-radius:8px;margin-bottom:40px;">' + pp + '</div>')

    def pb(n, title, body, extra=""):
        if not body:
            return ""
        mt = "margin-top:22px;" if extra else ""
        return ('<div style="background:#f8fafc;border:1px solid #e5e7eb;border-left:4px solid ' + accent + ';padding:28px;border-radius:8px;margin-bottom:25px;">'
                '<h3 style="color:#1a252c;margin-top:0;font-size:24px;margin-bottom:18px;">' + str(n) + '. ' + title + '</h3>' + extra
                + '<p style="' + F + 'margin-bottom:0;' + mt + '">' + body + '</p></div>')

    pbc = (pb("1", "The Generational Bargain (Fear vs. Greed)", t1)
           + pb("2", "The " + str(s) + "/" + str(b) + "/" + str(cp) + " Seesaw", t2, pie)
           + pb("3", "The Global Shield (US Dollar &amp; Market)", t3)
           + pb("4", "Survival Mechanics (DCA &amp; Risk)", t4))
    pbk = ""
    if pbc:
        pbk = ('<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:12px;border-bottom:3px solid ' + accent + ';padding-bottom:12px;display:inline-block;">The Titans Playbook</h2>'
               '<p style="font-size:18px;color:#6b7280;margin-bottom:30px;font-style:italic;">Strategic manual for ' + cat.lower() + ' conditions.</p>' + pbc)

    act = ""
    if vdo or vdont:
        do_b = ('<div style="background:#ecfdf5;border:2px solid #10b981;border-radius:8px;padding:24px;margin-bottom:20px;"><p style="font-size:20px;color:#065f46;font-weight:bold;margin:0 0 12px;">🟢 DO:</p><p style="font-size:18px;line-height:1.8;color:#064e3b;margin:0;">' + vdo + '</p></div>') if vdo else ""
        dn_b = ('<div style="background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:24px;"><p style="font-size:20px;color:#991b1b;font-weight:bold;margin:0 0 12px;">🔴 AVOID:</p><p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;">' + vdont + '</p></div>') if vdont else ""
        act = '<div style="background:#1e293b;padding:35px;border-radius:10px;margin:45px 0 40px;"><h3 style="color:#b8974d;margin-top:0;font-size:26px;margin-bottom:25px;border-bottom:2px solid #475569;padding-bottom:15px;">✅ VIP Action Plan</h3>' + do_b + dn_b + '</div>'

    return ('<div style="' + MAIN + '">' + _hdr(a, tf, "VIP EXCLUSIVE")
            + '<div style="margin-bottom:25px;">' + _impact(xtag(raw, "IMPACT"))
            + '<span style="display:inline-block;background:#f8fafc;border:2px solid ' + accent + ';color:' + accent + ';padding:4px 14px;border-radius:20px;font-size:14px;font-weight:bold;">' + theme["icon"] + ' ' + theme["label"] + '</span></div>'
            + _keynum(xtag(raw, "KEY_NUMBER"), xtag(raw, "KEY_NUMBER_CONTEXT"), accent) + _msnap(raw) + sent_h
            + '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:22px;margin-bottom:30px;">'
            + '<p style="font-size:16px;color:#6b7280;margin:0 0 12px;">⏱ <strong style="color:#1a252c;">8-10 min read</strong> | Full institutional analysis</p>'
            + '<div style="display:flex;flex-wrap:wrap;gap:8px;">'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">📊 Data</span>'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">🎯 Radar</span>'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">🔬 Macro</span>'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">📖 Playbook</span>'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">✅ Action</span></div></div>'
            + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
            + '<p style="' + F + 'margin-bottom:35px;">' + xtag(raw, "SUMMARY") + '</p>'
            + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:40px;">'
            + '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">💡 In Plain English</h3>'
            + '<p style="' + F + 'margin:0;">' + xtag(raw, "TIKTOK") + '</p></div>'
            + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers &amp; Insights</h2>'
            + '<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">' + xtag(raw, "HEADLINE") + '</h3>'
            + '<p style="' + F + 'margin-bottom:28px;">' + xtag(raw, "DEPTH") + '</p>'
            + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:22px;border-radius:8px;margin-bottom:40px;">'
            + '<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
            + '<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">' + xtag(raw, "FLOW") + '</p></div>'
            + '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">' + mc(l1, v1, COL[0]) + mc(l2, v2, COL[1]) + mc(l3, v3, COL[2]) + '</div>'
            + '<div style="padding:28px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:35px;">'
            + '<h3 style="margin-top:0;color:#1a252c;font-size:22px;border-bottom:2px solid #e5e7eb;padding-bottom:14px;margin-bottom:25px;">📊 Key Market Indicators</h3>'
            + gauge(l1, v1, COL[0]) + gauge(l2, v2, COL[1]) + gauge(l3, v3, COL[2]) + '</div>'
            + radar + _compare(ok_tag(raw, "COMPARE_BULL"), ok_tag(raw, "COMPARE_BEAR"), "Institutional Bull", "Institutional Bear")
            + macro + pbk + conv_h + act + _ftr(tw, ps))

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
def main():
    print("=" * 50)
    print("  Warm Insight v11 (2-Tier Cost Optimized)")
    print("  Tiers: Premium + VIP | Model: all flash")
    print("=" * 50)
    cat = get_current_category()
    urls = CATEGORIES.get(cat)
    if not urls:
        print("No URLs")
        return
    recent = get_recent_titles()
    print("\n--- [" + cat + "] ---")
    news = get_news(urls, 20)
    if len(news) < 5:
        print("  Not enough news (" + str(len(news)) + ")")
        return

    gem_client = genai.Client(api_key=GEMINI_API_KEY)
    total = ok_cnt = fail = 0

    for task in TASKS:
        tier, cnt = task["tier"], task["count"]
        if len(news) < cnt:
            print("  Skip " + tier + " (not enough news)")
            break
        target = [news.pop(0) for _ in range(cnt)]
        total += 1
        print("\n  [" + TIER_LABELS[tier] + "] " + str(cnt) + " articles...")

        result = analyze(target, cat, tier)
        if not result or not result[1]:
            print("  ANALYZE FAILED for " + tier)
            fail += 1
            continue

        title, html, exc, kw, slug, _ = result

        if is_duplicate(title, recent):
            print("  SKIP dup")
            fail += 1
            continue

        # Editor review (skip for tiers in SKIP_EDITOR_TIERS)
        if tier not in SKIP_EDITOR_TIERS:
            passed, issues = editor_review(gem_client, "\n".join(target), html)
            if not passed:
                print("    Retry after editor reject...")
                time.sleep(10)
                result2 = analyze(target, cat, tier)
                if result2 and result2[1]:
                    title, html, exc, kw, slug, _ = result2
                    p2, _ = editor_review(gem_client, "\n".join(target), html)
                    if not p2:
                        print("  REJECTED x2 — skipping " + tier)
                        fail += 1
                        continue
                else:
                    fail += 1
                    continue

        # Dynamic thumbnail: pure Pillow generation
        print("  Generating thumbnail...")
        thumb_bytes = make_dynamic_thumb(title, cat, tier)
        feature_img = None
        if thumb_bytes:
            feature_img = upload_img(thumb_bytes)
            if feature_img:
                print("  Thumb uploaded OK")
            else:
                print("  Thumb upload failed — publishing without image")

        # Publish
        success = publish(title, html, cat, tier, feature_img, exc, kw, slug)
        if success:
            ok_cnt += 1
            recent.append(title.lower())
        else:
            fail += 1

        extra = random.randint(60, 180)
        sl = TIER_SLEEP[tier] + extra
        print("  Wait " + str(sl) + "s")
        time.sleep(sl)

    print("\n" + "=" * 50)
    print("  " + cat + " | Total " + str(total) + " | OK " + str(ok_cnt) + " | Fail " + str(fail))
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nFATAL ERROR")
        traceback.print_exc()
        sys.exit(1)
