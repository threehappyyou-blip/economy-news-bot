#!/usr/bin/env python3
# ═══════════════════════════════════════════════
# Warm Insight Auto Poster — v13
# Changes from v12:
#   - MODEL updated to gemini-2.5-flash (GA) + gemini-2.0-flash fallback
#   - WordPress credential pre-verification before pipeline starts
#   - Detailed 401/403/500 error messages with fix instructions
#   - Publish retry logic (up to 2 retries on transient 5xx errors)
#   - Gemini client reuse (no per-call re-instantiation)
#   - Env-var sanity check at startup
# ═══════════════════════════════════════════════
import os, json, time, random, re, datetime, io
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

# Gemini models — tries MODEL first, falls back to MODEL_FALLBACK on 404/NOT_FOUND
MODEL          = "gemini-2.5-flash"
MODEL_FALLBACK = "gemini-2.0-flash"

SOCIAL_LINKS = {
    "youtube":  "https://www.youtube.com/@WarmInsightyou",
    "x":        "https://x.com/warminsight",
    "linkedin": "",
}
CATEGORIES  = ["Economy", "Politics", "Tech", "Health", "Energy"]
TIER_LABELS = {"premium": "💎 Pro", "vip": "👑 VIP"}

# Body text font style
F = "font-size:18px;line-height:1.8;color:#374151;font-family:Georgia,serif;"

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
        "https://feeds.reuters.com/reuters/environment",
        "https://oilprice.com/rss/main",
        "https://feeds.reuters.com/reuters/energy",
    ],
}

# ═══════════════════════════════════════════════
# GEMINI CLIENT  (initialised once, reused per run)
# ═══════════════════════════════════════════════
_gemini_client = None

def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client

# ═══════════════════════════════════════════════
# STARTUP SANITY CHECK
# ═══════════════════════════════════════════════
def check_env_vars():
    """
    Verify that all required environment variables are set.
    Prints clear instructions for any that are missing.
    Returns False if any critical variable is absent.
    """
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY  → Get from https://aistudio.google.com/apikey")
    if not WP_USER:
        missing.append("WP_USER        → Your WordPress username (e.g. admin)")
    if not WP_APP_PASS:
        missing.append(
            "WP_APP_PASS    → WordPress Application Password\n"
            "                 (WordPress Admin → Users → Profile → Application Passwords → Add New)\n"
            "                 Copy the generated password INCLUDING spaces, e.g.: xxxx xxxx xxxx xxxx xxxx xxxx"
        )
    if missing:
        print("❌ Missing GitHub Secrets — add these in your repo:")
        print("   Settings → Secrets and variables → Actions → New repository secret\n")
        for m in missing:
            print(f"   • {m}")
        return False
    return True

# ═══════════════════════════════════════════════
# WORDPRESS CREDENTIAL PRE-VERIFICATION
# ═══════════════════════════════════════════════
def verify_wp_credentials():
    """
    Call /wp-json/wp/v2/users/me to confirm authentication and role BEFORE
    running the full pipeline.  Returns True if safe to proceed.
    """
    print("🔐 Verifying WordPress credentials …")
    try:
        resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/users/me",
            auth=(WP_USER, WP_APP_PASS),
            timeout=10,
        )
        if resp.status_code == 200:
            data      = resp.json()
            name      = data.get("name", "Unknown")
            roles     = data.get("roles", [])
            caps      = data.get("capabilities", {})
            can_post  = caps.get("publish_posts") or caps.get("edit_posts") or \
                        any(r in roles for r in ("administrator", "editor", "author"))
            print(f"   ✅ Authenticated as: {name}  |  roles: {roles}")
            if not can_post:
                print("   ⚠️  WARNING: This user may not be able to publish posts.")
                print("       → Change the WordPress user role to Author / Editor / Administrator.")
                # Still return True — let the publish attempt surface the real error.
            return True

        elif resp.status_code == 401:
            print("   ❌ 401 Unauthorized — authentication failed.")
            print("      Possible causes:")
            print("      1. WP_APP_PASS is wrong or has been revoked.")
            print("      2. The Application Password was copied incorrectly (spaces matter).")
            print("      3. WP_USER is the username, NOT the email address.")
            print("   → Fix: WordPress Admin → Users → Profile → Application Passwords")
            print("          Delete the old password, generate a new one, update GitHub Secret.")
            return False

        elif resp.status_code == 403:
            print("   ❌ 403 Forbidden — user authenticated but lacks REST API access.")
            print("      → Possible cause: a security plugin is blocking REST API for this role.")
            print("      → Fix: Check plugins like Wordfence, iThemes Security, or Disable REST API.")
            return False

        elif resp.status_code == 404:
            print(f"   ❌ 404 — REST API endpoint not found at {WP_URL}/wp-json/wp/v2/users/me")
            print("      → Check WP_URL is correct and the REST API is enabled.")
            return False

        else:
            print(f"   ⚠️  Unexpected status {resp.status_code} — proceeding anyway.")
            return True

    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to {WP_URL}")
        print("      → Check WP_URL in GitHub Secrets (include https://, no trailing slash).")
        return False
    except Exception as e:
        print(f"   ⚠️  Credential check failed with exception: {e}")
        # Don't abort on unexpected network issues — let the publish attempt decide.
        return True

# ═══════════════════════════════════════════════
# CORE HELPERS
# ═══════════════════════════════════════════════
def xtag(raw, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", raw, re.DOTALL)
    return m.group(1).strip() if m else ""

def is_echo(text):
    if not text or len(text) < 20:
        return True
    echoes = ["your ", "here", "example", "placeholder", "[insert", "TODO"]
    return any(e.lower() in text.lower() for e in echoes)

def make_slug(kw, title, cat):
    base = kw if (kw and len(kw) > 4) else title
    slug = re.sub(r"[^\w\s-]", "", base.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:55]
    ts   = datetime.datetime.utcnow().strftime("%m%d")
    return f"{slug}-{ts}" if slug else f"{cat.lower()}-{ts}"

def sanitize(html):
    html = re.sub(
        r"<script(?!\s+type=['\"]application/ld\+json['\"])[^>]*>.*?</script>",
        "", html, flags=re.DOTALL
    )
    html = re.sub(r"<iframe[^>]*>.*?</iframe>", "", html, flags=re.DOTALL)
    return html

# ═══════════════════════════════════════════════
# SEO BUILDERS
# ═══════════════════════════════════════════════
def _clean_seo_title(title):
    clean = title
    for prefix in ["[💎 Pro] ", "[👑 VIP] ", "[💎 Pro]", "[👑 VIP]"]:
        clean = clean.replace(prefix, "")
    return clean.strip()

def _build_jsonld(title, exc, kw, cat, slug, img_url=""):
    seo_title = _clean_seo_title(title)
    url = SITE_URL + "/" + slug + "/"
    now = datetime.datetime.utcnow().isoformat() + "Z"
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline":      seo_title[:110],
        "description":   exc[:200],
        "url":           url,
        "datePublished": now,
        "dateModified":  now,
        "author":        {"@type": "Organization", "name": "Warm Insight"},
        "publisher": {
            "@type": "Organization",
            "name":  "Warm Insight",
            "logo":  {"@type": "ImageObject", "url": SITE_URL + "/wp-content/uploads/logo.png"},
        },
        "keywords":       kw,
        "articleSection": cat,
    }
    if img_url:
        schema["image"] = {"@type": "ImageObject", "url": img_url}
    return (
        '<script type="application/ld+json">'
        + json.dumps(schema, ensure_ascii=False)
        + "</script>"
    )

def _build_faq_schema(raw):
    faqs = []
    for i in range(1, 4):
        q = xtag(raw, f"FAQ_{i}_Q")
        a = xtag(raw, f"FAQ_{i}_A")
        if q and a and len(q) > 10 and len(a) > 20:
            faqs.append({
                "@type": "Question",
                "name":  q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            })
    if not faqs:
        return "", ""
    schema_html = (
        '<script type="application/ld+json">'
        + json.dumps(
            {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faqs},
            ensure_ascii=False,
        )
        + "</script>"
    )
    faq_visible = (
        '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;'
        'padding:28px;margin:35px 0;">'
        '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:20px;">'
        "❓ Frequently Asked Questions</h3>"
    )
    for faq in faqs:
        faq_visible += (
            '<div style="margin-bottom:18px;border-bottom:1px solid #e5e7eb;padding-bottom:16px;">'
            f'<p style="font-size:17px;font-weight:700;color:#1a252c;margin:0 0 8px;">{faq["name"]}</p>'
            f'<p style="font-size:16px;line-height:1.7;color:#374151;margin:0;">'
            f'{faq["acceptedAnswer"]["text"]}</p></div>'
        )
    faq_visible += "</div>"
    return schema_html, faq_visible

def _build_internal_links(cat):
    pillar  = PILLAR_PAGES.get(cat, PILLAR_PAGES["Economy"])
    related = CAT_RELATED.get(cat, ["Economy", "Tech"])
    html = (
        '<div style="margin:30px 0;padding:20px;background:#f9fafb;'
        'border-left:4px solid #b8974d;border-radius:0 8px 8px 0;">'
        '<p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#1a252c;">📌 Related Resources</p>'
        f'<p style="margin:0 0 8px;"><a href="{pillar["url"]}" '
        f'style="color:#b8974d;text-decoration:underline;">{pillar["anchor"]}</a></p>'
    )
    for rc in related[:2]:
        rp = PILLAR_PAGES.get(rc)
        if rp:
            html += (
                f'<p style="margin:0 0 8px;"><a href="{rp["url"]}" '
                f'style="color:#6b7280;text-decoration:underline;">{rc} Analysis</a></p>'
            )
    html += "</div>"
    return html

def _build_author_bio(cat):
    return (
        '<div style="display:flex;align-items:flex-start;gap:16px;background:#f8fafc;'
        'border:1px solid #e5e7eb;border-radius:12px;padding:24px;margin:35px 0;">'
        '<div style="flex-shrink:0;width:56px;height:56px;background:#b8974d;border-radius:50%;'
        'display:flex;align-items:center;justify-content:center;font-size:24px;">🤖</div>'
        '<div><p style="font-size:16px;font-weight:700;color:#1a252c;margin:0 0 6px;">'
        "Warm Insight Research Team</p>"
        f'<p style="font-size:14px;color:#6b7280;margin:0;">AI-powered {cat} analysis for everyday '
        "investors. We synthesize global market signals into clear, actionable insights.</p>"
        "</div></div>"
    )

def _build_social_share(title, slug):
    post_url  = SITE_URL + "/" + slug + "/"
    enc_title = title.replace(" ", "%20").replace("&", "%26")[:100]
    enc_url   = post_url.replace(":", "%3A").replace("/", "%2F")
    return (
        '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;'
        'padding:22px;margin:30px 0;text-align:center;">'
        '<p style="font-size:18px;font-weight:700;color:#1a252c;margin:0 0 14px;">Share This Analysis</p>'
        '<div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap;">'
        f'<a href="https://twitter.com/intent/tweet?text={enc_title}&url={enc_url}" '
        'target="_blank" rel="noopener" style="display:inline-block;background:#000;color:#fff;'
        'padding:10px 20px;border-radius:8px;font-size:14px;font-weight:bold;text-decoration:none;">𝕏 Share</a>'
        f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={enc_url}" '
        'target="_blank" rel="noopener" style="display:inline-block;background:#0A66C2;color:#fff;'
        'padding:10px 20px;border-radius:8px;font-size:14px;font-weight:bold;text-decoration:none;">in Share</a>'
        f'<a href="mailto:?subject={enc_title}&body=Check%20this%20out%3A%20{enc_url}" '
        'style="display:inline-block;background:#6b7280;color:#fff;'
        'padding:10px 20px;border-radius:8px;font-size:14px;font-weight:bold;text-decoration:none;">✉ Email</a>'
        "</div></div>"
    )

def _build_related_posts(cat):
    pillar       = PILLAR_PAGES.get(cat, PILLAR_PAGES["Economy"])
    related_cats = CAT_RELATED.get(cat, ["Economy", "Tech"])
    html = (
        '<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:12px;'
        'padding:28px;margin:30px 0;">'
        '<h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:16px;">📖 Continue Reading</h3>'
        '<div style="display:flex;flex-wrap:wrap;gap:12px;">'
        f'<a href="{pillar["url"]}" style="display:inline-block;background:#fff;border:2px solid #3b82f6;'
        f'color:#1e40af;padding:10px 18px;border-radius:8px;font-size:15px;font-weight:600;'
        f'text-decoration:none;">Browse {pillar["anchor"]} →</a>'
    )
    for rc in related_cats[:2]:
        rp = PILLAR_PAGES.get(rc)
        if rp:
            html += (
                f'<a href="{rp["url"]}" style="display:inline-block;background:#fff;'
                f'border:1px solid #e5e7eb;color:#374151;padding:10px 18px;border-radius:8px;'
                f'font-size:15px;text-decoration:none;">{rc} Analysis →</a>'
            )
    html += (
        f'<a href="{SITE_URL}/warm-insight-vip-membership/" style="display:inline-block;'
        'background:#b8974d;color:#fff;padding:10px 18px;border-radius:8px;font-size:15px;'
        'font-weight:bold;text-decoration:none;">🔒 Upgrade to VIP →</a>'
        "</div></div>"
    )
    return html

def _ftr(tw, ps):
    if not tw or is_echo(tw):
        tw = "Stay disciplined, stay diversified, and let time compound in your favor."
    if not ps or is_echo(ps):
        ps = "In 40 years of watching markets, the disciplined investor always wins."
    social_icons = ""
    if SOCIAL_LINKS.get("youtube"):
        social_icons += (
            f'<a href="{SOCIAL_LINKS["youtube"]}" target="_blank" style="display:inline-block;'
            'background:#FF0000;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;'
            'font-weight:bold;text-decoration:none;margin:0 4px;">▶ YouTube</a>'
        )
    if SOCIAL_LINKS.get("x"):
        social_icons += (
            f'<a href="{SOCIAL_LINKS["x"]}" target="_blank" style="display:inline-block;'
            'background:#000;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;'
            'font-weight:bold;text-decoration:none;margin:0 4px;">𝕏 Follow</a>'
        )
    if SOCIAL_LINKS.get("linkedin"):
        social_icons += (
            f'<a href="{SOCIAL_LINKS["linkedin"]}" target="_blank" style="display:inline-block;'
            'background:#0A66C2;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;'
            'font-weight:bold;text-decoration:none;margin:0 4px;">in LinkedIn</a>'
        )
    return (
        '<hr style="border:0;height:1px;background:#e5e7eb;margin:45px 0;">'
        '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">'
        "Today's Warm Insight</h2>"
        f'<p style="{F}">{tw}</p>'
        '<div style="margin-top:30px;background:#1e293b;padding:28px;border-radius:8px;'
        'border-left:4px solid #b8974d;">'
        '<p style="font-size:18px;line-height:1.8;color:#e2e8f0;margin:0;">'
        '<span style="color:#b8974d;font-weight:bold;">P.S.</span> '
        f'<span style="color:#cbd5e1;">{ps}</span></p></div>'
        '<div style="background:#f8fafc;border:2px solid #e5e7eb;border-radius:10px;'
        'padding:28px;margin:40px 0;text-align:center;">'
        '<p style="font-size:22px;font-weight:bold;color:#1a252c;margin:0 0 10px;">Found this useful?</p>'
        '<p style="font-size:16px;color:#6b7280;margin:0 0 18px;">'
        "Forward to a friend who wants smarter market analysis.</p>"
        f'<div style="margin-bottom:14px;">{social_icons}</div>'
        f'<p style="margin:0;"><a href="{SITE_URL}" '
        'style="color:#b8974d;font-weight:600;text-decoration:underline;">'
        "Subscribe at warminsight.com</a></p></div>"
        '<div style="background:#1e293b;padding:35px;border-radius:10px;margin-top:30px;">'
        '<p style="font-size:24px;font-weight:bold;color:#b8974d;margin:0 0 12px;text-align:center;">'
        "Warm Insight</p>"
        f'<div style="text-align:center;margin-bottom:16px;">{social_icons}</div>'
        '<div style="text-align:center;margin-bottom:16px;font-size:13px;">'
        f'<a href="{SITE_URL}/about-us/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">About</a>'
        f'<a href="{SITE_URL}/privacy-policy/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">Privacy</a>'
        f'<a href="{SITE_URL}/terms/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">Terms</a>'
        f'<a href="{SITE_URL}/warm-insight-vip-membership/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">VIP</a>'
        "</div>"
        '<p style="font-size:13px;color:#64748b;margin:0;text-align:center;">'
        "All analysis is for informational purposes only. Not financial advice.<br>"
        "&copy; 2026 Warm Insight. All rights reserved.</p>"
        "</div>"
    )

# ═══════════════════════════════════════════════
# THUMBNAIL GENERATOR
# ═══════════════════════════════════════════════
CAT_COLORS = {
    "Economy":  ("#1a6ef5", "#ffffff", "#ffcc00"),
    "Politics": ("#dc2626", "#ffffff", "#fbbf24"),
    "Tech":     ("#6366f1", "#ffffff", "#34d399"),
    "Health":   ("#059669", "#ffffff", "#ffffff"),
    "Energy":   ("#d97706", "#1a252c", "#1a252c"),
}

def make_thumbnail(kw, cat, tier):
    W, H  = 1200, 630
    SCALE = 2
    w, h  = W * SCALE, H * SCALE
    bg, text_c, accent = CAT_COLORS.get(cat, CAT_COLORS["Economy"])
    tier_c = "#b8974d" if tier == "vip" else "#6366f1"
    img  = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    def load_font(path, size):
        try:
            return ImageFont.truetype(path, size * SCALE)
        except Exception:
            return ImageFont.load_default()

    f_title = load_font("fonts/Anton-Regular.ttf",    80)
    f_small = load_font("fonts/BebasNeue-Regular.ttf", 32)
    f_badge = load_font("fonts/BebasNeue-Regular.ttf", 28)

    draw.rectangle([(0, h - 80 * SCALE), (w, h)], fill=accent)
    draw.rectangle([(40 * SCALE, 36 * SCALE), (260 * SCALE, 86 * SCALE)], fill="#00000033")
    draw.text((52 * SCALE, 42 * SCALE), cat.upper(), font=f_badge, fill="#ffffff")

    tier_label = "VIP" if tier == "vip" else "PRO"
    bw = 130 * SCALE
    draw.rectangle([(w - bw - 40 * SCALE, 36 * SCALE), (w - 40 * SCALE, 86 * SCALE)], fill=tier_c)
    draw.text((w - bw - 20 * SCALE, 42 * SCALE), tier_label, font=f_badge, fill="#ffffff")

    words = (kw or cat).upper().split()
    lines, line = [], []
    max_w = w - 140 * SCALE
    for word in words:
        test = " ".join(line + [word])
        try:
            tw2 = draw.textlength(test, font=f_title)
        except Exception:
            tw2 = len(test) * 38 * SCALE
        if tw2 < max_w:
            line.append(word)
        else:
            if line:
                lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))

    y = 150 * SCALE
    for ln in lines[:3]:
        draw.text((60 * SCALE, y), ln, font=f_title, fill=text_c)
        try:
            bb = draw.textbbox((0, 0), ln, font=f_title)
            y += (bb[3] - bb[1]) + 8 * SCALE
        except Exception:
            y += 95 * SCALE

    mx, my = w - 220 * SCALE, h // 2 - 20 * SCALE
    draw.rectangle([(mx, my - 55 * SCALE), (mx + 110 * SCALE, my + 55 * SCALE)], fill="#4ade80")
    draw.rectangle([(mx + 15 * SCALE, my - 28 * SCALE), (mx + 42 * SCALE, my + 4 * SCALE)], fill="#1a252c")
    draw.rectangle([(mx + 68 * SCALE, my - 28 * SCALE), (mx + 95 * SCALE, my + 4 * SCALE)], fill="#1a252c")
    draw.rectangle([(mx + 25 * SCALE, my + 15 * SCALE), (mx + 85 * SCALE, my + 28 * SCALE)], fill="#1a252c")

    draw.text((60 * SCALE, h - 62 * SCALE), "WARM INSIGHT", font=f_small, fill="#1a252c")
    draw.text((w - 520 * SCALE, h - 62 * SCALE), "AI-Driven Global Market Analysis", font=f_small, fill="#1a252c")

    img = img.resize((W, H), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

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
                title   = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", ""))[:250].strip()
                summary = re.sub(r"<[^>]+>", "", summary)
                if title:
                    items.append(f"• {title}: {summary}")
        except Exception as e:
            print(f"RSS error ({url}): {e}")
            continue
        if len(items) >= max_items:
            break
    random.shuffle(items)
    return "\n".join(items[:max_items]) if items else f"Latest {cat} market developments today."

# ═══════════════════════════════════════════════
# DUPLICATE CHECK
# ═══════════════════════════════════════════════
def check_duplicate(kw):
    if not kw or not WP_USER:
        return False
    try:
        resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/posts",
            params={"search": kw[:40], "status": "publish,draft", "per_page": 5},
            auth=(WP_USER, WP_APP_PASS),
            timeout=10,
        )
        if resp.status_code == 200:
            for post in resp.json():
                existing = post.get("title", {}).get("rendered", "").lower()
                if kw.lower()[:20] in existing:
                    print(f"⚠️  Duplicate found: {existing[:60]}")
                    return True
    except Exception as e:
        print(f"Duplicate check error: {e}")
    return False

# ═══════════════════════════════════════════════
# GEMINI API  — reuse client, model fallback
# ═══════════════════════════════════════════════
def call_gemini(prompt):
    """
    Generate content via Gemini.
    Tries MODEL first; on 404/NOT_FOUND falls back to MODEL_FALLBACK.
    """
    client         = _get_gemini_client()
    models_to_try  = [MODEL, MODEL_FALLBACK]

    for model in models_to_try:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            if model != MODEL:
                print(f"   ℹ️  Used fallback model: {model}")
            return response.text or ""
        except Exception as e:
            err = str(e)
            print(f"Gemini error ({model}): {e}")
            if ("404" in err or "NOT_FOUND" in err or "not found" in err.lower()) \
                    and model != models_to_try[-1]:
                print(f"   ⚠️  '{model}' unavailable — trying fallback …")
                continue
            # Auth errors, quota exhausted, etc. — fail immediately
            return ""

    return ""

# ═══════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════
FAQ_TAGS = (
    "<FAQ_1_Q>A question a reader would Google about this topic</FAQ_1_Q>\n"
    "<FAQ_1_A>Clear 2-3 sentence answer</FAQ_1_A>\n"
    "<FAQ_2_Q>Second question about market implications</FAQ_2_Q>\n"
    "<FAQ_2_A>Clear 2-3 sentence answer</FAQ_2_A>\n"
    "<FAQ_3_Q>Third question about what investors should do</FAQ_3_Q>\n"
    "<FAQ_3_A>Clear 2-3 sentence answer</FAQ_3_A>"
)

def _make_premium_prompt(news_text, cat):
    return f"""You are Warm Insight's AI analyst. Write a Premium newsletter article on {cat}.
Respond ONLY using these exact XML tags:
<TITLE>Compelling headline, no emoji, max 80 chars</TITLE>
<EXCERPT>2–3 sentence SEO summary, 120–150 chars</EXCERPT>
<SEO_KEYWORD>3–5 word focus keyphrase</SEO_KEYWORD>
<LEAD>Strong opening paragraph hooking the reader on the key insight</LEAD>
<BODY>3–4 paragraphs of analysis using HTML: <h2>, <p>, <strong>, <ul><li>. 600–800 words total.</BODY>
<SENTIMENT>BULLISH or BEARISH or NEUTRAL</SENTIMENT>
<TW>One memorable market wisdom sentence</TW>
<PS>One-line P.S. from a veteran investor's perspective</PS>
{FAQ_TAGS}
News inputs:
{news_text[:3000]}
Tone: professional, confident, accessible to everyday investors.
Focus on second-order effects and actionable takeaways."""

def _make_vip_prompt1(news_text, cat):
    return f"""You are Warm Insight's senior analyst. Write Part 1 of a VIP deep-dive on {cat}.
<TITLE>High-impact headline, no emoji, max 90 chars</TITLE>
<EXCERPT>Premium 2–3 sentence teaser, 120–150 chars</EXCERPT>
<SEO_KEYWORD>3–5 word focus keyphrase</SEO_KEYWORD>
<LEAD>Provocative macro thesis opening paragraph</LEAD>
<DEEP_ANALYSIS>4–5 paragraphs using HTML: <h2>, <p>, <strong>, <ul><li>. Cover macro context,
geopolitical dimensions (G7 vs BRICS+ dynamics where relevant), second-order market effects,
and fragmented multipolarity framework. 900–1100 words.</DEEP_ANALYSIS>
<SENTIMENT>BULLISH or BEARISH or NEUTRAL</SENTIMENT>
<BULL_CASE>2–3 sentences: the bull case for investors</BULL_CASE>
<BEAR_CASE>2–3 sentences: the bear case for investors</BEAR_CASE>
News inputs:
{news_text[:4000]}
Write as if advising sophisticated institutional investors."""

def _make_vip_prompt2(raw1, cat):
    title   = xtag(raw1, "TITLE")
    summary = xtag(raw1, "DEEP_ANALYSIS")[:600]
    return f"""Complete the VIP analysis for: "{title}" ({cat})
Context summary: {summary}...
Respond with ONLY these tags:
<ACTION_ITEMS>3–5 concrete investor action items as <ul><li>HTML list</ACTION_ITEMS>
<TW>Memorable market wisdom quote relevant to this story</TW>
<PS>Compelling one-line P.S. from a 40-year market veteran</PS>
{FAQ_TAGS}"""

# ═══════════════════════════════════════════════
# CONTENT ASSEMBLER
# ═══════════════════════════════════════════════
def analyze(raw1, raw2, cat, tier):
    full = raw1 + ("\n" + raw2 if raw2 else "")
    tr   = xtag(full, "TITLE")
    exc  = xtag(full, "EXCERPT") or "Expert market analysis."
    kw   = xtag(full, "SEO_KEYWORD")
    tw   = xtag(full, "TW")
    ps   = xtag(full, "PS")
    lead = xtag(full, "LEAD")
    body = xtag(full, "BODY") or xtag(full, "DEEP_ANALYSIS")
    sent = xtag(full, "SENTIMENT").upper() or "NEUTRAL"
    bull = xtag(full, "BULL_CASE")
    bear = xtag(full, "BEAR_CASE")
    acts = xtag(full, "ACTION_ITEMS")
    title = (
        "[" + TIER_LABELS.get(tier, tier) + "] " + tr
        if tr else f"({tier.upper()}) {cat} Insight"
    )
    slug = make_slug(kw, tr or cat, cat)

    html = ""
    if lead:
        html += f'<p style="{F}">{lead}</p>\n'

    s_colors = {"BULLISH": "#10b981", "BEARISH": "#ef4444", "NEUTRAL": "#f59e0b"}
    s_c = s_colors.get(sent, "#f59e0b")
    html += (
        '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px;'
        'padding:14px 20px;margin:20px 0;display:flex;align-items:center;gap:12px;">'
        '<span style="font-size:14px;font-weight:600;color:#6b7280;">Market Sentiment:</span>'
        f'<span style="background:{s_c};color:#fff;padding:4px 14px;border-radius:20px;'
        f'font-size:13px;font-weight:700;">{sent}</span></div>\n'
    )

    if body:
        html += body + "\n"

    if tier == "vip" and (bull or bear):
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:30px 0;">\n'
        if bull:
            html += (
                '<div style="background:#d1fae5;border:1px solid #6ee7b7;border-radius:10px;padding:20px;">'
                '<p style="font-size:15px;font-weight:700;color:#065f46;margin:0 0 8px;">🐂 Bull Case</p>'
                f'<p style="font-size:14px;color:#064e3b;margin:0;">{bull}</p></div>\n'
            )
        if bear:
            html += (
                '<div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:10px;padding:20px;">'
                '<p style="font-size:15px;font-weight:700;color:#7f1d1d;margin:0 0 8px;">🐻 Bear Case</p>'
                f'<p style="font-size:14px;color:#7f1d1d;margin:0;">{bear}</p></div>\n'
            )
        html += "</div>\n"

    if tier == "vip" and acts:
        html += (
            '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;'
            'padding:24px;margin:30px 0;">'
            '<p style="font-size:18px;font-weight:700;color:#1e3a5f;margin:0 0 14px;">'
            f"⚡ Investor Action Items</p>{acts}</div>\n"
        )

    faq_schema, faq_visible = _build_faq_schema(full)
    html += faq_visible
    html += _build_social_share(title, slug)
    html += _build_related_posts(cat)
    html += _build_internal_links(cat)
    html += _build_author_bio(cat)
    html += _ftr(tw, ps)
    html  = sanitize(html)
    return title, html, exc, kw, slug, tier, full, faq_schema

# ═══════════════════════════════════════════════
# WORDPRESS PUBLISHER  — with retry + clear error messages
# ═══════════════════════════════════════════════
def _upload_image(img_bytes, filename):
    try:
        resp = requests.post(
            f"{WP_URL}/wp-json/wp/v2/media",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "image/jpeg",
            },
            data=img_bytes,
            auth=(WP_USER, WP_APP_PASS),
            timeout=30,
        )
        if resp.status_code in (200, 201):
            data = resp.json()
            return data.get("id"), data.get("source_url", "")
        print(f"   ⚠️  Image upload failed {resp.status_code} — continuing without thumbnail.")
    except Exception as e:
        print(f"   ⚠️  Image upload error: {e} — continuing without thumbnail.")
    return None, ""

def _get_category_id(cat_name):
    try:
        resp = requests.get(
            f"{WP_URL}/wp-json/wp/v2/categories",
            params={"search": cat_name, "per_page": 10},
            auth=(WP_USER, WP_APP_PASS),
            timeout=10,
        )
        if resp.status_code == 200:
            for c in resp.json():
                if c["name"].lower() == cat_name.lower():
                    return c["id"]
    except Exception as e:
        print(f"Category lookup error: {e}")
    return None

def _explain_publish_error(status_code, body_text):
    """Print a human-readable explanation for common WordPress publish errors."""
    if status_code == 401:
        print("   ❌ 401 Unauthorized — WordPress rejected the credentials.")
        print("      Most likely cause: WP_APP_PASS is wrong, expired, or was copied incorrectly.")
        print()
        print("      ── HOW TO FIX ──────────────────────────────────────────────")
        print("      1. Log in to WordPress Admin.")
        print("      2. Go to Users → Profile → scroll to 'Application Passwords'.")
        print("      3. Delete the existing entry (if any), then click 'Add New'.")
        print("      4. Name it e.g. 'GitHub Actions' and click 'Add New Application Password'.")
        print("      5. Copy the generated password (format: xxxx xxxx xxxx xxxx xxxx xxxx).")
        print("      6. In GitHub repo → Settings → Secrets and variables → Actions:")
        print("         Update WP_APP_PASS with the new password (keep the spaces).")
        print("      7. Also confirm WP_USER is the exact WordPress username (not email).")
        print("      ────────────────────────────────────────────────────────────")
    elif status_code == 403:
        print("   ❌ 403 Forbidden — authenticated but not allowed to create posts.")
        print("      → The WordPress user's role must be Author / Editor / Administrator.")
        print("      → Check if a security plugin (Wordfence, iThemes, Disable REST API)")
        print("        is blocking POST requests to /wp-json/wp/v2/posts.")
    elif status_code == 500:
        print("   ❌ 500 Internal Server Error — WordPress server-side error.")
        print("      → Check the WordPress error log for details.")
        print("      → This is usually a plugin conflict or PHP error.")
    elif status_code == 503:
        print("   ❌ 503 Service Unavailable — server overloaded or in maintenance mode.")
    else:
        print(f"   ❌ HTTP {status_code} — {body_text[:200]}")

def publish(title, html, exc, kw, cat, slug, tier, img_bytes, full_raw, faq_schema):
    """Post article to WordPress with up to 2 retries on transient 5xx errors."""
    # Upload thumbnail (non-fatal)
    media_id, img_url = None, ""
    if img_bytes:
        media_id, img_url = _upload_image(img_bytes, f"{slug[:40]}.jpg")
        if media_id:
            print(f"🖼  Thumbnail uploaded: {img_url}")

    seo_title    = _clean_seo_title(title)
    schemas      = _build_jsonld(title, exc, kw, cat, slug, img_url) + faq_schema
    full_content = schemas + html

    cat_id = _get_category_id(cat)
    post_data = {
        "title":   title,
        "content": full_content,
        "excerpt": exc,
        "status":  "publish",
        "slug":    slug,
    }
    if cat_id:
        post_data["categories"] = [cat_id]
    if media_id:
        post_data["featured_media"] = media_id
    if kw:
        post_data["meta"] = {
            "rank_math_title":         (seo_title + " | Warm Insight")[:60],
            "rank_math_description":   (exc[:120] + " Expert " + cat.lower() + " analysis.")[:155],
            "rank_math_focus_keyword": kw,
        }

    delay = random.randint(3, 12)
    print(f"⏳ Publish delay: {delay}s …")
    time.sleep(delay)

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.post(
                f"{WP_URL}/wp-json/wp/v2/posts",
                json=post_data,
                auth=(WP_USER, WP_APP_PASS),
                timeout=30,
            )
            if resp.status_code in (200, 201):
                link = resp.json().get("link", "")
                print(f"✅ Published [{tier.upper()}] {title}")
                print(f"   URL: {link}")
                return True

            # 4xx errors are non-retryable
            if 400 <= resp.status_code < 500:
                _explain_publish_error(resp.status_code, resp.text)
                return False

            # 5xx — transient; retry after a short wait
            _explain_publish_error(resp.status_code, resp.text)
            if attempt < max_attempts:
                wait = 15 * attempt
                print(f"   ↻ Retrying in {wait}s … (attempt {attempt}/{max_attempts})")
                time.sleep(wait)
            else:
                print(f"   🛑 All {max_attempts} publish attempts failed.")
                return False

        except requests.exceptions.Timeout:
            print(f"   ⚠️  Request timed out (attempt {attempt}/{max_attempts}).")
            if attempt < max_attempts:
                time.sleep(10)
        except Exception as e:
            print(f"❌ Publish error: {e}")
            return False

    return False

# ═══════════════════════════════════════════════
# PIPELINE ORCHESTRATOR
# ═══════════════════════════════════════════════
def _pick_cat():
    return CATEGORIES[datetime.datetime.utcnow().hour % len(CATEGORIES)]

def _pick_tier():
    return "vip" if datetime.datetime.utcnow().hour % 2 == 0 else "premium"

def run_pipeline():
    cat  = _pick_cat()
    tier = _pick_tier()
    print(f"\n{'='*50}")
    print(f"🚀 Warm Insight v13 | {cat} | {tier.upper()} | {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC")
    print(f"{'='*50}")

    # 0. Env-var sanity check
    if not check_env_vars():
        print("🛑 Aborting — set the missing GitHub Secrets and re-run.")
        return

    # 1. WordPress credential pre-verification
    if not verify_wp_credentials():
        print("🛑 Aborting — fix WordPress credentials before retrying.")
        return

    # 2. Fetch news
    news = fetch_news(cat)
    print(f"📰 News fetched ({len(news.splitlines())} items)")

    # 3. Generate content via Gemini
    raw1, raw2 = "", ""
    if tier == "vip":
        print("🤖 VIP Part 1 …")
        raw1 = call_gemini(_make_vip_prompt1(news, cat))
        if not raw1:
            print("❌ VIP Part 1 empty — aborting")
            return
        print("🤖 VIP Part 2 …")
        raw2 = call_gemini(_make_vip_prompt2(raw1, cat))
        if not raw2:
            print("❌ VIP Part 2 empty — aborting")
            return
    else:
        print("🤖 Premium generation …")
        raw1 = call_gemini(_make_premium_prompt(news, cat))
        if not raw1:
            print("❌ Premium generation empty — aborting")
            return

    # 4. Assemble HTML
    title, html, exc, kw, slug, tier, full_raw, faq_schema = analyze(raw1, raw2, cat, tier)
    print(f"📝 Article: {title}")

    # 5. Duplicate guard
    if check_duplicate(kw or title[:30]):
        print("⚠️  Duplicate detected — skipping publish")
        return

    # 6. Thumbnail
    print("🖌  Generating thumbnail …")
    img_bytes = make_thumbnail(kw or title[:40], cat, tier)

    # 7. Publish
    publish(title, html, exc, kw, cat, slug, tier, img_bytes, full_raw, faq_schema)

# ═══════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    run_pipeline()
