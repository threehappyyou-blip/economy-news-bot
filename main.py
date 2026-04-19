#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ═══════════════════════════════════════════════════════════════
# Warm Insight Auto Poster — v31 (Independent Topic Edition)
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
TIER_LABELS = {"premium": "PRO", "vip": "VIP"} 

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
# CORE HELPERS
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
    for p in ["[PRO] ", "[VIP] ", "[PRO]", "[VIP]"]: title = title.replace(p, "")
    return title.strip()

# ═══════════════════════════════════════════════
# 📊 VISUAL DATA BUILDERS 
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
                    <th style="padding:12px; color:{SLATE}; font-weight:700; font-size:14px;">Asset / Metric</th>
                    <th style="padding:12px; color:{SLATE}; font-weight:700; font-size:14px;">Value / State</th>
                    <th style="padding:12px; color:{SLATE}; font-weight:700; font-size:14px;">Trend</th>
                    <th style="padding:12px; color:{SLATE}; font-weight:700; font-size:14px;">Insight</th>
                </tr>
            </thead>
            <tbody>
    """
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            asset, value, trend, insight = parts[:4]
            t_upper = trend.upper()
            if "UP" in t_upper or "BULL" in t_upper: t_color = "#10b981" 
            elif "DOWN" in t_upper or "BEAR" in t_upper: t_color = "#ef4444" 
            else: t_color = "#f59e0b" 
            
            html += f"""
                <tr style="border-bottom:1px solid {BORDER};">
                    <td style="padding:12px; font-weight:600; color:{DARK};">{asset}</td>
                    <td style="padding:12px; color:{SLATE}; font-family:monospace; font-size:15px;">{value}</td>
                    <td style="padding:12px; font-weight:bold; color:{t_color};">{trend}</td>
                    <td style="padding:12px; color:{MUTED}; font-size:14px;">{insight}</td>
                </tr>
            """
    html += "</tbody></table></div></div>"
    return html

def _build_progress_bars(raw_data, title="Sector Heatmap"):
    if not raw_data: return ""
    lines = [l.strip() for l in raw_data.split('\n') if '|' in l]
    if not lines: return ""
    
    html = f"""
    <div style="background:{BG_LIGHT}; border:1px solid {BORDER}; border-radius:12px; padding:24px; margin:30px 0;">
        <h3 style="margin-top:0; font-size:18px; color:{DARK};">{title}</h3>
    """
    colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"]
    
    for i, line in enumerate(lines[:5]):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:
            name = parts[0]
            try: pct = int(re.sub(r'[^0-9]', '', parts[1]))
            except: pct = 50
            pct = max(0, min(100, pct))
            c = colors[i % len(colors)]
            
            html += f"""
            <div style="margin-bottom:15px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span style="font-weight:600; font-size:14px; color:{DARK};">{name}</span>
                    <span style="font-weight:bold; font-size:14px; color:{c};">{pct}%</span>
                </div>
                <div style="background:#e2e8f0; height:10px; border-radius:5px; overflow:hidden;">
                    <div style="background:{c}; height:100%; width:{pct}%; border-radius:5px;"></div>
                </div>
            </div>
            """
    html += "</div>"
    return html

# ═══════════════════════════════════════════════
# 🎨 HTML BUILDERS (Content Integration)
# ═══════════════════════════════════════════════
def build_html(tier, cat, raw, title, author, tf, slug, exc, kw):
    html = f"<div style=\"{F}\">\n"
    
    badge = "VIP EXCLUSIVE" if tier == "vip" else "PRO EXCLUSIVE"
    badge_bg = GOLD if tier == "vip" else "#6366f1"
    html += f"""
    <div style="border-top:3px solid {badge_bg}; border-bottom:1px solid {BORDER}; padding:14px 0; margin-bottom:30px;">
        <p style="margin:0; font-size:15px; color:{MUTED};">
            <strong style="color:{DARK};">{author}</strong> &nbsp;|&nbsp; {tf}
            <span style="background:{badge_bg}; color:#fff; padding:4px 12px; border-radius:4px; font-size:11px; font-weight:800; letter-spacing:1px; margin-left:10px;">{badge}</span>
        </p>
    </div>
    """
    
    if tier == "vip":
        html += f'<h2 style="font-size:24px; color:{DARK};">Executive Summary</h2>'
        html += f'<p><strong>{xtag(raw, "EXECUTIVE_SUMMARY")}</strong></p>'
        html += _build_data_table(xtag(raw, "DATA_TABLE"), "Global Macro Dashboard")
        html += _build_progress_bars(xtag(raw, "HEATMAP"), "Sector Risk Heatmap")
        
        html += f'<h2 style="font-size:24px; color:{DARK};">Deep Analysis</h2>'
        html += f'<p>{xtag(raw, "MACRO")}</p><p>{xtag(raw, "HERD")}</p><p>{xtag(raw, "CONTRARIAN")}</p>'
        
        html += f'<div style="background:#fffbeb; border-left:4px solid {AMBER}; padding:20px; margin:30px 0;">'
        html += f'<strong style="color:#92400e;">💡 Quick Flow:</strong><br>{xtag(raw, "QUICK_FLOW")}</div>'
        
    else: 
        html += f'<p style="font-size:19px; font-weight:600; color:{DARK};">{xtag(raw, "LEAD")}</p>'
        html += _build_data_table(xtag(raw, "DATA_TABLE"), "Market Movers")
        html += f'<div style="margin:30px 0;">{xtag(raw, "BODY")}</div>'
    
    tw = xtag(raw, "KEY_TAKEAWAY") if tier == "premium" else xtag(raw, "BULL_CASE")
    ps = xtag(raw, "PS")
    
    html += f"""
    <hr style="border:0; height:1px; background:{BORDER}; margin:40px 0;">
    <div style="background:{DARK}; padding:30px; border-radius:10px; border-left:4px solid {badge_bg};">
        <h3 style="color:#fff; margin-top:0; font-size:20px;">The Bottom Line</h3>
        <p style="color:#cbd5e1; font-size:16px;">{tw}</p>
        <p style="color:{badge_bg}; font-weight:bold; margin-bottom:0;">P.S. <span style="color:#94a3b8; font-weight:normal;">{ps}</span></p>
    </div>
    </div>
    """
    return sanitize(html)

# ═══════════════════════════════════════════════
# 🎨 MODERN THUMBNAIL GENERATOR (Milk Road Style)
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

def make_thumbnail(title_text, cat, tier):
    W, H, SCALE = 1200, 630, 2
    w, h = W * SCALE, H * SCALE
    
    STYLES = {
        "Economy":  {"bg": "#1e3a8a", "acc": "#3b82f6", "text": "#bfdbfe"}, 
        "Politics": {"bg": "#7f1d1d", "acc": "#ef4444", "text": "#fecaca"}, 
        "Tech":     {"bg": "#4c1d95", "acc": "#8b5cf6", "text": "#e9d5ff"}, 
        "Health":   {"bg": "#064e3b", "acc": "#10b981", "text": "#a7f3d0"}, 
        "Energy":   {"bg": "#78350f", "acc": "#f59e0b", "text": "#fde68a"}, 
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

    cx, cy = w * 0.75, h * 0.5
    chart_w, chart_h = w * 0.4, h * 0.5
    points = []
    import math
    for i in range(10):
        px = cx - chart_w/2 + (chart_w * i / 9)
        py = cy + (math.sin(i) * chart_h/3) + (i * 20 * SCALE if tier=="premium" else -i * 20 * SCALE)
        points.append((px, py))
    
    draw.line(points, fill=style["acc"], width=15*SCALE, joint="curve")
    
    for px, py in points:
        draw.ellipse([px-10*SCALE, py-10*SCALE, px+10*SCALE, py+10*SCALE], fill="#ffffff", outline=style["acc"], width=5*SCALE)

    for x in range(int(w * 0.6)):
        alpha = int(255 * (1 - (x / (w * 0.6))))
        draw.line([(x, 0), (x, h)], fill=(0, 0, 0, int(alpha*0.7))) 

    pad = 60 * SCALE
    date_str = datetime.datetime.utcnow().strftime("%b %d, %Y").upper()
    badge_text = f"  {cat.upper()}  |  {date_str}  "
    draw.rounded_rectangle([pad, pad, pad + draw.textlength(badge_text, font=font_badge) + 40*SCALE, pad + 60*SCALE], radius=10*SCALE, fill="#000000")
    draw.text((pad + 20*SCALE, pad + 12*SCALE), badge_text, font=font_badge, fill=style["text"])
    
    tier_text = " VIP REPORT " if tier == "vip" else " PRO REPORT "
    tier_bg = GOLD if tier == "vip" else "#3b82f6"
    tier_w = draw.textlength(tier_text, font=font_badge)
    draw.rounded_rectangle([w - pad - tier_w - 40*SCALE, pad, w - pad, pad + 60*SCALE], radius=10*SCALE, fill=tier_bg)
    draw.text((w - pad - tier_w - 20*SCALE, pad + 12*SCALE), tier_text, font=font_badge, fill="#ffffff")

    clean_title = _clean_seo_title(title_text).replace('"', '').replace("'", "")
    words = clean_title.upper().split()
    lines, current_line = [], []
    max_w = w * 0.6 
    
    for word in words:
        test_line = " ".join(current_line + [word])
        try: tw = draw.textlength(test_line, font=font_title)
        except: tw = len(test_line) * 50 * SCALE
        
        if tw <= max_w:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line: lines.append(" ".join(current_line))

    y_pos = h * 0.35
    for line in lines[:4]: 
        draw.text((pad, y_pos), line, font=font_title, fill="#ffffff")
        y_pos += 100 * SCALE

    draw.text((pad, h - pad - 40*SCALE), "WARM INSIGHT", font=font_logo, fill=style["text"])

    img = img.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

# ═══════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════
def _make_vip_prompt1(news_text, cat):
    return f"""You are a veteran financial analyst. Write a VIP deep-dive on {cat}.
Respond ONLY with XML tags.

<TITLE>Headline, max 90 chars. DO NOT mention specific stock tickers in the title.</TITLE>
<EXCERPT>2 sentence teaser.</EXCERPT>
<SEO_KEYWORD>focus keyphrase</SEO_KEYWORD>
<EXECUTIVE_SUMMARY>3 sentences core thesis.</EXECUTIVE_SUMMARY>

<DATA_TABLE>
Extract 3-4 key market metrics from the news.
Format exactly like this, separated by newlines:
Asset Name | Value or Price | Bull or Bear or Neutral | 1 sentence insight
</DATA_TABLE>

<HEATMAP>
Invent 3-4 sector risk levels (0-100%) based on the news.
Format exactly: Sector Name | Number
</HEATMAP>

<MACRO>2 paragraphs on global context.</MACRO>
<HERD>1 paragraph on retail psychology.</HERD>
<CONTRARIAN>1 paragraph on smart money view.</CONTRARIAN>
<QUICK_FLOW>Chain of events with arrows ➡️</QUICK_FLOW>

News: {news_text[:3000]}"""

def _make_premium_prompt(news_text, cat):
    return f"""You are a veteran financial analyst. Write a PRO newsletter on {cat}.
Respond ONLY with XML tags.

<TITLE>Headline, max 80 chars. DO NOT mention specific stock tickers in the title.</TITLE>
<EXCERPT>2 sentence teaser.</EXCERPT>
<SEO_KEYWORD>focus keyphrase</SEO_KEYWORD>

<DATA_TABLE>
Extract 3 key market metrics from the news.
Format exactly like this, separated by newlines:
Asset Name | Status/Value | UP or DOWN | Short insight
</DATA_TABLE>

<LEAD>1 paragraph opening hook.</LEAD>
<BODY>3 paragraphs of analysis using HTML formatting (h3, p, strong).</BODY>
<KEY_TAKEAWAY>2 actionable sentences.</KEY_TAKEAWAY>
<PS>One-line veteran advice.</PS>

News: {news_text[:3000]}"""

# ═══════════════════════════════════════════════
# PUBLISHER & PIPELINE
# ═══════════════════════════════════════════════
def fetch_news(cat, offset=0, limit=8):
    """
    뉴스 목록을 긁어와서, 특정 오프셋(offset)부터 시작하는 뉴스 묶음을 반환합니다.
    이를 통해 VIP와 PRO가 서로 겹치지 않는 완전 독립적인 뉴스를 받게 됩니다.
    """
    feeds = RSS_FEEDS.get(cat, RSS_FEEDS["Economy"])
    items = []
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for e in d.entries[:5]: # 각 피드에서 충분히 많은 뉴스를 가져옴
                items.append(f"• {e.title}: {re.sub(r'<[^>]+>', '', e.get('summary', ''))[:200]}")
        except: pass
    
    # 항상 일정한 순서 유지를 위해 해시 기반 정렬 후 슬라이싱
    items = sorted(list(set(items))) 
    
    # 요청한 범위(offset ~ offset+limit)만큼 잘라서 반환
    selected_items = items[offset : offset + limit]
    return "\n".join(selected_items)

def _upload_image(img_bytes, filename):
    try:
        resp = requests.post(f"{WP_URL}/wp-json/wp/v2/media", headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/jpeg"}, data=img_bytes, auth=(WP_USER, WP_APP_PASS), timeout=30)
        if resp.status_code in (200, 201): return resp.json().get("id")
    except: pass
    return None

def publish(title, html, exc, kw, cat, slug, tier, img_bytes):
    media_id = _upload_image(img_bytes, f"{slug[:20]}.jpg") if img_bytes else None
    
    cat_id = None
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/categories", params={"search": cat}, auth=(WP_USER, WP_APP_PASS))
        if r.status_code == 200: cat_id = r.json()[0]["id"]
    except: pass

    post_data = {"title": title, "content": html, "status": "publish", "slug": slug}
    if media_id: post_data["featured_media"] = media_id
    if cat_id: post_data["categories"] = [cat_id]

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

def call_gemini(prompt):
    client = _get_gemini_client()
    for m in [MODEL, MODEL_FALLBACK]:
        try:
            return client.models.generate_content(model=m, contents=prompt).text
        except: pass
    return ""

def run_pipeline():
    cat = CATEGORIES[(datetime.datetime.utcnow().hour // 3) % len(CATEGORIES)]
    print(f"🚀 Starting v31 Pipeline (Independent Topics) | Category: {cat}")
    
    if not check_env_vars() or not verify_wp_credentials(): return
    
    for i, tier in enumerate(TIERS):
        print(f"\n--- Processing {tier.upper()} ---")
        
        # 🚨 [주제 완전 분리 패치] 
        # VIP(i=0)는 0~8번째 뉴스 사용, PRO(i=1)는 8~16번째 뉴스 사용
        offset = i * 8 
        independent_news = fetch_news(cat, offset=offset, limit=8)
        
        if not independent_news:
            print(f"   ⚠️ Not enough distinct news for {tier}. Skipping.")
            continue
            
        prompt = _make_vip_prompt1(independent_news, cat) if tier == "vip" else _make_premium_prompt(independent_news, cat)
        raw = call_gemini(prompt)
        
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
