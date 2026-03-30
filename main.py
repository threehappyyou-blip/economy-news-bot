# -*- coding: utf-8 -*-
"""
Warm Insight v8 FINAL — Clean Build
All features integrated from scratch. Zero patches.
"""

import os, sys, traceback, time, random, re, json
from datetime import datetime
import requests, jwt, feedparser
from google import genai
from google.genai import types

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL       = os.environ.get("GHOST_API_URL", "").rstrip("/")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")
if not all([GEMINI_API_KEY, GHOST_API_URL, GHOST_ADMIN_API_KEY]):
    sys.exit("Missing API keys")

CATEGORIES = {
    "Economy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
                "https://finance.yahoo.com/news/rssindex"],
    "Politics": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113"],
    "Tech":     ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"],
    "Health":   ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108"],
    "Energy":   ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810"],
}

TASKS = [
    {"tier": "Basic",         "count": 3},
    {"tier": "Premium",       "count": 3},
    {"tier": "Royal Premium", "count": 5},
]

TIER_LABELS = {"Basic": "🌱 Free", "Premium": "💎 Pro", "Royal Premium": "👑 VIP"}
TIER_VIS    = {"Basic": "public", "Premium": "public", "Royal Premium": "public"}
TIER_SLEEP  = {"Basic": 15, "Premium": 30, "Royal Premium": 50}
MODEL_PRI   = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash"],
    "Premium":       ["gemini-2.5-pro", "gemini-2.5-flash"],
    "Basic":         ["gemini-2.5-flash"],
}

EXPERT = {
    "Economy":  "a veteran US Wall Street strategist with 40 years of experience",
    "Politics": "a veteran US political strategist with 40 years of Washington experience",
    "Tech":     "a veteran Silicon Valley technology analyst with 40 years of experience",
    "Health":   "a veteran US healthcare and biotech analyst with 40 years of experience",
    "Energy":   "a veteran US energy and commodities strategist with 40 years of experience",
}

CAT_THEME = {
    "Economy":  {"icon": "💰", "accent": "#2563eb", "label": "MACRO & RATES"},
    "Politics": {"icon": "🏛",  "accent": "#dc2626", "label": "GEOPOLITICS"},
    "Tech":     {"icon": "🤖", "accent": "#7c3aed", "label": "AI & DISRUPTION"},
    "Health":   {"icon": "🧬", "accent": "#059669", "label": "BIOTECH & PHARMA"},
    "Energy":   {"icon": "⚡", "accent": "#d97706", "label": "OIL, GAS & RENEWABLES"},
}

CAT_ALLOC = {
    "Economy":  {"s": 55, "b": 35, "c": 10, "note": "Defensive: higher bonds during macro uncertainty"},
    "Politics": {"s": 50, "b": 35, "c": 15, "note": "Elevated cash for geopolitical shock absorption"},
    "Tech":     {"s": 70, "b": 20, "c": 10, "note": "Growth tilt: overweight innovation equities"},
    "Health":   {"s": 60, "b": 30, "c": 10, "note": "Balanced: pharma stability with biotech upside"},
    "Energy":   {"s": 65, "b": 25, "c": 10, "note": "Commodity tilt: overweight real assets"},
}

CAT_METRICS = {
    "Economy":  {"pool": ["Inflation Momentum","Recession Risk","Consumer Pulse","Credit Stress","Rate Cut Odds","Dollar Strength","Yield Curve","PMI Signal","Wage Tension"], "hint": "inflation, GDP, employment, Fed policy"},
    "Politics": {"pool": ["Policy Uncertainty","Regulatory Risk","Geopolitical Tension","Election Volatility","Trade War Risk","Sanctions Impact","Legislative Gridlock","Defense Momentum"], "hint": "policy, regulation, geopolitics, elections"},
    "Tech":     {"pool": ["AI Race Intensity","Antitrust Pressure","Chip Supply Stress","IPO Sentiment","Cloud Velocity","Cyber Threat","Big Tech Momentum","Funding Freeze"], "hint": "AI, semiconductors, regulation, startup funding"},
    "Health":   {"pool": ["Pipeline Confidence","Drug Pricing Pressure","Biotech Funding","FDA Momentum","Gene Therapy Index","Hospital Stress","Coverage Gap","Trial Success"], "hint": "pharma pipelines, drug pricing, FDA, biotech"},
    "Energy":   {"pool": ["Oil Supply Squeeze","Green Transition","OPEC Tension","LNG Surge","Renewable Growth","Geo Shock Risk","Grid Stress","Carbon Heat"], "hint": "oil, OPEC, renewables, LNG, geopolitics"},
}

VIP_THUMB = {
    "Economy": "Dark dramatic 3D golden scales with dollar bills, cinematic blue lighting, data hologram, 8k",
    "Politics": "Dark dramatic 3D marble chess board geopolitical symbols, red accent lighting, 8k",
    "Tech": "Dark dramatic 3D neural network purple glow, circuit landscape, AI hologram, 8k",
    "Health": "Dark dramatic 3D DNA helix with golden capsules, green glow, medical theme, 8k",
    "Energy": "Dark dramatic 3D oil derricks vs solar panels, amber golden lighting, 8k",
}

ACCURACY = """
STRICT ACCURACY RULES (NEVER VIOLATE):
- ONLY analyze facts from the news articles provided. NEVER invent events, names, or incidents.
- NEVER fabricate specific prices, RSI numbers, or statistics. Use directional language instead.
- Use hedging: "likely", "suggests", "indicates" - not definitive false claims.
- If news does not mention something, do NOT create it.
- Reference only real, well-known ETF tickers (SPY, XLE, XLV, IEF, GLD, etc).
"""

# ═══════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════

PROMPT_BASIC = (
    "You are [PERSONA] for 'Warm Insight' ([CATEGORY]).\n"
    "Audience: Smart beginners. Friendly but substantive, like Milk Road free tier.\n"
    "[ACCURACY]\n"
    "STYLE: Use the Ladder of Abstraction: start concrete, climb up (why it matters), come back down (what to do).\n"
    "English only. 500-700 words.\n\n"
    "OUTPUT (XML):\n"
    "<SEO_KEYWORD>3-6 word search phrase</SEO_KEYWORD>\n"
    "<TITLE>Catchy title with SEO keyword near front</TITLE>\n"
    "<IMAGE_PROMPT>3D abstract cinematic about [CATEGORY]</IMAGE_PROMPT>\n"
    "<EXCERPT>1 sentence with SEO keyword</EXCERPT>\n"
    "<IMPACT>Rate market impact: HIGH, MEDIUM, or LOW</IMPACT>\n"
    "<SUMMARY>3 sentences. First includes SEO keyword.</SUMMARY>\n"
    "<TIKTOK>Fun TikTok analogy (3-4 sentences)</TIKTOK>\n"
    "<HEADLINE>Key insight headline</HEADLINE>\n"
    "<KEY_NUMBER>Most important number from this news</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>1 sentence why this number matters personally</KEY_NUMBER_CONTEXT>\n"
    "<DEPTH_WHAT>WHAT HAPPENED: Clear explanation with everyday analogy. 3-4 sentences.</DEPTH_WHAT>\n"
    "<DEPTH_WHY>WHY IT MATTERS: Connect to bigger pattern. 3-4 sentences.</DEPTH_WHY>\n"
    "<DEPTH_YOU>WHAT IT MEANS FOR YOU: Daily life impact + 1 actionable tip. 3-4 sentences.</DEPTH_YOU>\n"
    '<FLOW>Each step has TEXT and emoji: "Fed Raises Rates 🦅 ➡️ Borrowing Expensive 💳 ➡️ Housing Slows 🏠"</FLOW>\n'
    "<BOTTOM_LINE>One punchy sentence capturing entire story. Start with Bottom Line:</BOTTOM_LINE>\n"
    "<WINNER>1 sector that BENEFITS, and why (1 sentence)</WINNER>\n"
    "<LOSER>1 sector that LOSES, and why (1 sentence)</LOSER>\n"
    "<QUICK_HITS>3 other interesting headlines from articles. 1 sentence each. 3 separate lines.</QUICK_HITS>\n"
    "<TEASER>Provocative 1-sentence preview of what VIP subscribers learned today</TEASER>\n"
    "<TAKEAWAY>One clear actionable sentence</TAKEAWAY>\n"
    "<PS>Warm personal thought</PS>\n\n"
    "News: [NEWS_ITEMS]"
)

PROMPT_PREMIUM = (
    "You are [PERSONA] for 'Warm Insight' ([CATEGORY]).\n"
    "Audience: Intermediate investors wanting deeper why and actionable edge.\n"
    "[ACCURACY]\n"
    "STYLE: Apply Second-Order Thinking: trace consequences 2 steps ahead. Identify behavioral biases.\n"
    "English only. 700-900 words.\n\n"
    "OUTPUT (XML):\n"
    "<SEO_KEYWORD>4-7 word long-tail keyword</SEO_KEYWORD>\n"
    "<TITLE>Analytical title with SEO keyword</TITLE>\n"
    "<IMAGE_PROMPT>3D cinematic about [CATEGORY]</IMAGE_PROMPT>\n"
    "<EXCERPT>1 sentence with SEO keyword</EXCERPT>\n"
    "<IMPACT>Rate market impact: HIGH, MEDIUM, or LOW</IMPACT>\n"
    "<SUMMARY>3 sentences. First includes SEO keyword.</SUMMARY>\n"
    "<TIKTOK>TikTok analogy revealing hidden truth (3-4 sentences)</TIKTOK>\n"
    "<HEADLINE>Analytical headline</HEADLINE>\n"
    "<KEY_NUMBER>Most striking number/statistic</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>1 sentence why this changes the investment picture</KEY_NUMBER_CONTEXT>\n"
    "<DEPTH><strong>🧐 WHY (The Pattern):</strong> Deeper structural pattern. Behavioral economics. 5-6 sentences."
    "<br><br><strong>🐑 THE HERD TRAP:</strong> What cognitive bias makes investors wrong? 4-5 sentences.</DEPTH>\n"
    '<FLOW>Each step TEXT + emoji (5+ steps): "Fed Signal 🦅 ➡️ Dollar Up 💵 ➡️ EM Pain 🌏"</FLOW>\n'
    "<PRO_INSIGHT>Non-obvious cross-sector connection using Second-Order Thinking. 5-6 sentences.</PRO_INSIGHT>\n"
    "<COMPARE_BULL>Bull case: 2-3 sentences. Who benefits?</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case: 2-3 sentences. What could go wrong?</COMPARE_BEAR>\n"
    "<PRO_DO>2 specific actionable steps with reasoning</PRO_DO>\n"
    "<PRO_DONT>1 specific mistake with reasoning</PRO_DONT>\n"
    "<QUICK_HITS>3 other interesting headlines. 1 sentence each. 3 lines.</QUICK_HITS>\n"
    "<TAKEAWAY>Insightful takeaway</TAKEAWAY>\n"
    "<PS>Historical perspective (2-3 sentences)</PS>\n\n"
    "News: [NEWS_ITEMS]"
)

VIP_P1 = (
    "You are [PERSONA] for 'Warm Insight' VIP ([CATEGORY]).\n"
    "Audience: Sophisticated investors paying premium for alpha.\n"
    "[ACCURACY]\n"
    "STYLE: Systems Thinking + 2nd/3rd Order effects. Then zoom down to specifics.\n\n"
    "WRITE real analysis in each tag (NOT instructions):\n\n"
    "<SEO_KEYWORD>4-8 word long-tail keyword</SEO_KEYWORD>\n"
    "<TITLE>Institutional title with SEO keyword near front</TITLE>\n"
    "<IMAGE_PROMPT>[CAT_THUMB]</IMAGE_PROMPT>\n"
    "<EXCERPT>1 VIP-grade sentence with SEO keyword</EXCERPT>\n"
    "<IMPACT>Rate market impact: HIGH, MEDIUM, or LOW</IMPACT>\n"
    "<KEY_NUMBER>Most critical number from this news</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>1 sentence why institutional investors watch this number</KEY_NUMBER_CONTEXT>\n"
    "<SENTIMENT>0-100 Fear-Greed score for this news. 0=Extreme Fear, 100=Extreme Greed. Just the number.</SENTIMENT>\n"
    "<SUMMARY>3 institutional sentences. First MUST include SEO keyword.</SUMMARY>\n"
    "<TIKTOK>Gen-Z viral analogy</TIKTOK>\n"
    "<HEADLINE>Alpha headline</HEADLINE>\n"
    "<DEPTH><strong>🧐 MACRO (Systems View):</strong> Structural forces, feedback loops, policy dynamics. 5+ sentences."
    "<br><br><strong>🐑 HERD BIAS:</strong> Cognitive bias making crowd wrong. 4+ sentences."
    "<br><br><strong>🦅 CONTRARIAN (2nd/3rd Order):</strong> Smart money view. Chain: 1st->2nd->3rd order. 5+ sentences.</DEPTH>\n"
    '<FLOW>Each step TEXT + emoji (6+ steps): "Supply Deficit 🛢 ➡️ Price Spike 📈 ➡️ Margin Squeeze 📉"</FLOW>\n'
    "<GRAPH_DATA>3 metrics for [CATEGORY]. [CAT_HINT]. Scores MUST differ (25-90). Format: Name1|Score1|Name2|Score2|Name3|Score3</GRAPH_DATA>\n"
    "<VIP_RADAR_1>Sector - BULLISH or BEARISH - why (1 sentence)</VIP_RADAR_1>\n"
    "<VIP_RADAR_2>Different sector - BULLISH or BEARISH - why</VIP_RADAR_2>\n"
    "<VIP_RADAR_3>Different sector - BULLISH or BEARISH - why</VIP_RADAR_3>\n"
    "<VIP_RADAR_4>Different sector - BULLISH or BEARISH - why</VIP_RADAR_4>\n"
    "<VIP_C1>Technical Outlook: directional analysis of sector ETFs. 5+ sentences.</VIP_C1>\n"
    "<VIP_C2>Macro Flow: yield curves, credit, dollar dynamics. 5+ sentences.</VIP_C2>\n"
    "<VIP_C3>Smart Money: institutional positioning. 5+ sentences.</VIP_C3>\n"
    "<MARKET_SNAP>4 indicators. Format each line: Name|UP or DOWN or FLAT|brief reason\n"
    "S&P 500|DIRECTION|reason\n10Y Yield|DIRECTION|reason\nUS Dollar|DIRECTION|reason\nOil WTI|DIRECTION|reason</MARKET_SNAP>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

VIP_P2 = (
    "You are [PERSONA]. You wrote Part 1 for VIP ([CATEGORY]).\n"
    "[ACCURACY]\n"
    "STYLE: Zoom down from macro view to SPECIFIC ACTIONS.\n\n"
    "YOUR ANALYSIS SO FAR:\n---\n[CTX]\n---\n\n"
    "Write REAL strategy paragraphs in each tag.\n\n"
    "<VIP_T1>Fear vs Greed now? What would Buffett do? Templeton? 6+ real sentences.</VIP_T1>\n"
    "<VIP_T2>Asset allocation: [ALLOC_STR]. Name real ETFs. What to adjust this week. 6+ sentences.</VIP_T2>\n"
    "<VIP_T3>Why US assets matter vs Europe/China/EM. Dollar dynamics. 5+ sentences.</VIP_T3>\n"
    "<VIP_T4>DCA strategy. When to deploy. 50% panic rule with thresholds. 6+ sentences.</VIP_T4>\n"
    "<VIP_DO>3 actions. Each: real ETF name, percentage, trigger condition.</VIP_DO>\n"
    "<VIP_DONT>2 mistakes to avoid with why dangerous now.</VIP_DONT>\n"
    "<COMPARE_BULL>Institutional bull case. 2-3 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Institutional bear case. 2-3 sentences.</COMPARE_BEAR>\n"
    "<CONVICTION>Overall conviction: HIGH, MEDIUM, or LOW</CONVICTION>\n"
    "<TAKEAWAY>One masterful calming sentence.</TAKEAWAY>\n"
    "<PS>40-year wisdom. One historical parallel. 2-3 sentences.</PS>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

VIP_FALLBACK = (
    "You are [PERSONA] writing concise strategy for VIP [CATEGORY].\n"
    "[ACCURACY]\n"
    "Based on: [CTX_SHORT]\n\n"
    "Write ALL tags with REAL content:\n\n"
    "<VIP_T1>Fear or Greed? What would a wise investor do? 3-4 sentences.</VIP_T1>\n"
    "<VIP_T2>Allocation for [CATEGORY]: [ALLOC_STR]. Name 2 ETFs. 3-4 sentences.</VIP_T2>\n"
    "<VIP_T3>Why US markets safer than alternatives. 2-3 sentences.</VIP_T3>\n"
    "<VIP_T4>DCA advice. When to buy vs hold cash. 3-4 sentences.</VIP_T4>\n"
    "<VIP_DO>2 specific actions with real ETF names.</VIP_DO>\n"
    "<VIP_DONT>1 mistake to avoid.</VIP_DONT>\n"
    "<COMPARE_BULL>Bull case: 1-2 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case: 1-2 sentences.</COMPARE_BEAR>\n"
    "<CONVICTION>HIGH, MEDIUM, or LOW</CONVICTION>\n"
    "<TAKEAWAY>One calming insight.</TAKEAWAY>\n"
    "<PS>One historical parallel. 1-2 sentences.</PS>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

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
                news.append(f"- {t}: {getattr(e, 'summary', '')}")
                if len(news) >= count:
                    break
        except Exception:
            continue
    return news[:count]

def parse_graph(raw, cat):
    if not raw:
        return _fb_graph(cat)
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 6:
        return _fb_graph(cat)
    try:
        v1 = int(re.sub(r"[^0-9]", "", parts[1]))
        v2 = int(re.sub(r"[^0-9]", "", parts[3]))
        v3 = int(re.sub(r"[^0-9]", "", parts[5]))
        if v1 == v2 == v3:
            return _fb_graph(cat)
        return (parts[0], max(10, min(95, v1)),
                parts[2], max(10, min(95, v2)),
                parts[4], max(10, min(95, v3)))
    except Exception:
        return _fb_graph(cat)

def _fb_graph(cat):
    pool = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["pool"]
    lb = random.sample(pool, 3)
    return lb[0], random.randint(55, 88), lb[1], random.randint(30, 65), lb[2], random.randint(40, 78)

def is_echo(text):
    if not text or len(text) < 80:
        return True
    sigs = ["6+ sentences", "5+ sentences", "At least 5", "Write a detailed",
            "Name ETFs", "which ETF", "trigger price", "Write exactly",
            "explain WHY", "Write real", "Write ALL", "3-4 sentences"]
    return sum(1 for s in sigs if s.lower() in text.lower()) >= 2

def ok_tag(raw, tag):
    v = xtag(raw, tag)
    if not v or is_echo(v):
        return ""
    return v

def sanitize(h):
    return re.sub(r"\s+", " ", h.replace("\n", " ").replace("\r", ""))

def make_slug(kw, title):
    t = kw if kw else title
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", t.lower())
    return re.sub(r"\s+", "-", s.strip())[:80]

# ═══════════════════════════════════════════════
# GHOST API
# ═══════════════════════════════════════════════
def gtoken():
    kid, sec = str(GHOST_ADMIN_API_KEY).split(":")
    iat = int(datetime.now().timestamp())
    return jwt.encode(
        {"iat": iat, "exp": iat + 300, "aud": "/admin/"},
        bytes.fromhex(sec), algorithm="HS256",
        headers={"alg": "HS256", "typ": "JWT", "kid": kid}
    )

def upload_img(ib):
    try:
        r = requests.post(
            f"{GHOST_API_URL}/ghost/api/admin/images/upload/",
            headers={"Authorization": f"Ghost {gtoken()}"},
            files={"file": ("t.jpg", ib, "image/jpeg"), "purpose": (None, "image")},
            timeout=30
        )
        if r.status_code in (200, 201):
            return r.json()["images"][0]["url"]
    except Exception as e:
        print(f"  img err: {e}")
    return None

def publish(title, html, cat, tier, iu, exc, kw="", slug=""):
    print(f"  Pub: {title[:50]}...")
    try:
        md = json.dumps({
            "version": "0.3.1", "markups": [], "atoms": [],
            "cards": [["html", {"html": html}]],
            "sections": [[10, 0]]
        })
        p = {
            "title": title, "mobiledoc": md, "status": "published",
            "visibility": TIER_VIS.get(tier, "public"),
            "tags": [{"name": cat}, {"name": tier}]
        }
        if slug:
            p["slug"] = slug
        if kw:
            mt = title + " | Warm Insight " + cat
            md_d = exc[:140] + " Expert " + cat.lower() + " analysis."
            p["meta_title"] = mt[:300]
            p["meta_description"] = md_d[:500]
            p["og_title"] = mt[:300]
            p["og_description"] = md_d[:300]
        if exc:
            p["custom_excerpt"] = exc[:290]
        if iu:
            p["feature_image"] = iu
            if kw:
                p["feature_image_alt"] = kw + " - Warm Insight " + cat
        r = requests.post(
            f"{GHOST_API_URL}/ghost/api/admin/posts/",
            json={"posts": [p]},
            headers={"Authorization": f"Ghost {gtoken()}", "Content-Type": "application/json"},
            timeout=60
        )
        if r.status_code in (200, 201):
            print("  OK!")
        else:
            print(f"  FAIL {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"  ERR: {e}")
        traceback.print_exc()

# ═══════════════════════════════════════════════
# THUMBNAIL
# ═══════════════════════════════════════════════
def make_thumb(ip, tier, cat):
    if tier == "Royal Premium":
        ip = VIP_THUMB.get(cat, ip)
    tries = 3 if tier == "Royal Premium" else 1
    for a in range(1, tries + 1):
        try:
            c = genai.Client(api_key=GEMINI_API_KEY)
            r = c.models.generate_images(
                model="imagen-3.0-generate-001", prompt=ip,
                config=types.GenerateImagesConfig(
                    number_of_images=1, aspect_ratio="16:9",
                    output_mime_type="image/jpeg"
                )
            )
            if r.generated_images:
                print(f"  Imagen OK({a})")
                return r.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"  Imagen({a}): {e}")
            if a < tries:
                time.sleep(5)
    try:
        r = requests.get(f"https://picsum.photos/seed/{random.randint(1, 9999)}/1280/720", timeout=10)
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return None

# ═══════════════════════════════════════════════
# GEMINI
# ═══════════════════════════════════════════════
def call_gem(client, model, prompt, retries=2):
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt)
            return str(r.text)
        except Exception as e:
            print(f"    Gem({model})try{i}: {type(e).__name__}: {e}")
            if i < retries:
                time.sleep(10 * i)
    return None

def gem_fb(client, tier, prompt):
    for m in MODEL_PRI.get(tier, ["gemini-2.5-flash"]):
        print(f"    [AI] {m}")
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

    if tier == "Basic":
        prompt = PROMPT_BASIC.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", acc).replace("[NEWS_ITEMS]", ns)
        raw, _ = gem_fb(client, tier, prompt)
        if not raw:
            return None, None, None, None, None, None
        html = build_basic(author, tf, raw)

    elif tier == "Premium":
        prompt = PROMPT_PREMIUM.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", acc).replace("[NEWS_ITEMS]", ns)
        raw, _ = gem_fb(client, tier, prompt)
        if not raw:
            return None, None, None, None, None, None
        html = build_premium(author, tf, raw)

    else:
        hint = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["hint"]
        thumb = VIP_THUMB.get(cat, "3D cinematic " + cat)
        al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
        al_str = str(al["s"]) + "% stocks, " + str(al["b"]) + "% safe, " + str(al["c"]) + "% cash (" + al["note"] + ")"

        p1 = VIP_P1.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", acc).replace("[CAT_HINT]", hint).replace("[CAT_THUMB]", thumb).replace("[NEWS_ITEMS]", ns)
        raw1, _ = gem_fb(client, tier, p1)
        if not raw1:
            return None, None, None, None, None, None

        if not xtag(raw1, "VIP_C1") or is_echo(xtag(raw1, "VIP_C1")):
            print("    P1 retry...")
            time.sleep(15)
            r1r, _ = gem_fb(client, tier, p1)
            if r1r and xtag(r1r, "VIP_C1") and not is_echo(xtag(r1r, "VIP_C1")):
                raw1 = r1r

        ctx = "Title: " + xtag(raw1, "TITLE") + "\nHeadline: " + xtag(raw1, "HEADLINE") + "\nSummary: " + xtag(raw1, "SUMMARY") + "\nDepth: " + xtag(raw1, "DEPTH")[:600]
        ctx_short = xtag(raw1, "HEADLINE") + ". " + xtag(raw1, "SUMMARY")

        print("    Part 2...")
        time.sleep(10)
        p2 = VIP_P2.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", acc).replace("[CTX]", ctx).replace("[ALLOC_STR]", al_str).replace("[NEWS_ITEMS]", ns)
        raw2, _ = gem_fb(client, tier, p2)

        for retry in range(2):
            if raw2 and ok_tag(raw2, "VIP_T1"):
                break
            print(f"    P2 echo retry {retry + 1}...")
            time.sleep(15)
            raw2, _ = gem_fb(client, tier, p2)

        if not raw2 or not ok_tag(raw2, "VIP_T1"):
            print("    P2 FAILED -> Fallback...")
            time.sleep(10)
            fb = VIP_FALLBACK.replace("[CATEGORY]", cat).replace("[PERSONA]", persona).replace("[ACCURACY]", acc).replace("[CTX_SHORT]", ctx_short[:400]).replace("[ALLOC_STR]", al_str).replace("[NEWS_ITEMS]", ns)
            raw2, _ = gem_fb(client, tier, fb)
            if not raw2:
                raw2 = ""

        raw = raw1 + "\n" + raw2
        html = build_vip(author, tf, raw, cat)

    tr = xtag(raw, "TITLE")
    ip = xtag(raw, "IMAGE_PROMPT") or ("3D cinematic " + cat)
    exc = xtag(raw, "EXCERPT") or "Expert analysis."
    kw = xtag(raw, "SEO_KEYWORD")
    pretty = TIER_LABELS.get(tier, tier)
    title = "[" + pretty + "] " + tr if tr else "(" + tier + ") " + cat + " Insight"
    slug = make_slug(kw, tr or cat)
    html = sanitize(html)
    return title, ip, html, ts + " | " + exc, kw, slug

# ═══════════════════════════════════════════════
# HTML HELPERS
# ═══════════════════════════════════════════════
F = "font-size:18px;line-height:1.8;color:#374151;"
MAIN = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;"

def _hdr(author, tf, badge=""):
    b = ""
    if badge:
        b = (' <span style="background:#b8974d;color:#fff;padding:3px 12px;'
             'border-radius:4px;font-size:14px;font-weight:bold;">'
             + badge + '</span>')
    return ('<div style="border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;'
            'padding:14px 0;margin-bottom:30px;"><p style="margin:0;font-size:16px;color:#4b5563;">'
            '<strong style="color:#1a252c;">' + author + '</strong> | ' + tf + b + '</p></div>')

def _ftr(tw, ps):
    if not tw or is_echo(tw):
        tw = "Stay disciplined, stay diversified, and let time compound in your favor."
    if not ps or is_echo(ps):
        ps = "In 40 years of watching markets, the disciplined investor always wins."
    share = (
        '<div style="background:#f8fafc;border:2px solid #e5e7eb;border-radius:10px;'
        'padding:28px;margin:40px 0;text-align:center;">'
        '<p style="font-size:22px;font-weight:bold;color:#1a252c;margin:0 0 8px;">'
        'Enjoyed this? Share the insight.</p>'
        '<p style="font-size:18px;color:#6b7280;margin:0 0 15px;">'
        'Forward this to a friend who wants to be smarter about markets.</p>'
        '<p style="font-size:16px;color:#b8974d;font-weight:600;margin:0;">'
        '<a href="https://www.warminsight.com/#/portal/signup" '
        'style="color:#b8974d;text-decoration:underline;">Subscribe at warminsight.com</a></p></div>'
    )
    return (
        '<hr style="border:0;height:1px;background:#e5e7eb;margin:45px 0;">'
        '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">'
        "Today's Warm Insight</h2>"
        '<p style="' + F + '">' + tw + '</p>'
        '<div style="margin-top:30px;background:#1e293b;padding:28px;border-radius:8px;'
        'border-left:4px solid #b8974d;">'
        '<p style="font-size:18px;line-height:1.8;color:#e2e8f0;margin:0;">'
        '<span style="color:#b8974d;font-weight:bold;font-size:20px;">P.S.</span> '
        '<span style="color:#cbd5e1;">' + ps + '</span></p></div>'
        + share
        + '<p style="font-size:16px;color:#9ca3af;margin-top:20px;text-align:center;">'
        'Disclaimer: For informational purposes only.</p></div>'
    )

def _upgrade(msg):
    return ('<div style="background:#fffbeb;border:2px solid #f59e0b;padding:18px;'
            'border-radius:8px;margin:35px 0;"><p style="font-size:18px;color:#92400e;'
            'margin:0;text-align:center;">' + msg + '</p></div>')

def _impact_badge(impact):
    imp = impact.upper().strip() if impact else ""
    colors = {"HIGH": ("#dc2626", "#fef2f2"), "MEDIUM": ("#d97706", "#fffbeb"), "LOW": ("#059669", "#ecfdf5")}
    c, bg = colors.get(imp, ("#6b7280", "#f3f4f6"))
    if not imp:
        return ""
    return ('<span style="display:inline-block;background:' + bg + ';color:' + c
            + ';border:2px solid ' + c + ';padding:4px 14px;border-radius:20px;'
            'font-size:14px;font-weight:bold;margin-bottom:20px;">IMPACT: ' + imp + '</span>')

def _key_number(kn, knc, color="#1e40af"):
    if not kn or not knc:
        return ""
    return ('<div style="background:#f0f9ff;border:2px solid ' + color
            + ';border-radius:12px;padding:28px;margin-bottom:30px;text-align:center;">'
            '<div style="font-size:48px;font-weight:800;color:' + color + ';margin-bottom:8px;">'
            + kn + '</div><p style="font-size:18px;color:#374151;margin:0;">' + knc + '</p></div>')

def _quick_hits(raw):
    qh = xtag(raw, "QUICK_HITS")
    if not qh or is_echo(qh):
        return ""
    lines = [l.strip() for l in qh.strip().split("\n") if l.strip()]
    if not lines:
        return ""
    emojis = ["⚡", "🔥", "📌"]
    items = ""
    for i, line in enumerate(lines[:3]):
        e = emojis[i] if i < len(emojis) else "•"
        items += '<p style="font-size:18px;color:#374151;margin:10px 0;line-height:1.6;">' + e + " " + line + '</p>'
    return ('<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;'
            'padding:24px;margin-bottom:35px;">'
            '<h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:12px;'
            'text-transform:uppercase;letter-spacing:1px;">Quick Hits</h3>'
            + items + '</div>')

def _market_snap(raw):
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
        name = parts[0]
        direction = parts[1].upper().strip()
        reason = parts[2][:40] if len(parts) > 2 else ""
        arrow, color = icons.get(direction, ("—", "#6b7280"))
        cells += ('<div style="flex:1;min-width:130px;text-align:center;padding:12px 8px;">'
                  '<div style="font-size:14px;color:#94a3b8;font-weight:600;margin-bottom:4px;">'
                  + name + '</div>'
                  '<div style="font-size:22px;font-weight:800;color:' + color + ';">'
                  + arrow + " " + direction + '</div>'
                  '<div style="font-size:12px;color:#64748b;margin-top:2px;">' + reason + '</div></div>')
    if not cells:
        return ""
    return ('<div style="background:#1e293b;border-radius:10px;padding:12px;margin-bottom:30px;'
            'overflow-x:auto;"><div style="display:flex;flex-wrap:wrap;justify-content:space-around;">'
            + cells + '</div></div>')

def _compare(cb, cbear, bull_title="Bull Case", bear_title="Bear Case"):
    if not cb and not cbear:
        return ""
    bull = ""
    bear = ""
    if cb:
        bull = ('<div style="flex:1;min-width:220px;background:#ecfdf5;border:2px solid #10b981;'
                'border-radius:10px;padding:22px;"><h4 style="margin-top:0;font-size:20px;'
                'color:#065f46;">🐂 ' + bull_title + '</h4>'
                '<p style="font-size:18px;line-height:1.7;color:#064e3b;margin:0;">' + cb + '</p></div>')
    if cbear:
        bear = ('<div style="flex:1;min-width:220px;background:#fef2f2;border:2px solid #ef4444;'
                'border-radius:10px;padding:22px;"><h4 style="margin-top:0;font-size:20px;'
                'color:#991b1b;">🐻 ' + bear_title + '</h4>'
                '<p style="font-size:18px;line-height:1.7;color:#7f1d1d;margin:0;">' + cbear + '</p></div>')
    return '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">' + bull + bear + '</div>'

# ═══════════════════════════════════════════════
# BUILD BASIC
# ═══════════════════════════════════════════════
def build_basic(a, tf, r):
    dw = xtag(r, "DEPTH_WHAT")
    dy = xtag(r, "DEPTH_WHY")
    du = xtag(r, "DEPTH_YOU")
    if not dw:
        dw = xtag(r, "DEPTH")
        dy = ""
        du = ""
    winner = xtag(r, "WINNER")
    loser = xtag(r, "LOSER")
    teaser = xtag(r, "TEASER")
    bl = xtag(r, "BOTTOM_LINE")

    wl = ""
    if winner or loser:
        w = ('<div style="flex:1;min-width:200px;background:#ecfdf5;border:2px solid #10b981;'
             'border-radius:10px;padding:20px;"><p style="font-size:20px;font-weight:bold;'
             'color:#065f46;margin:0 0 8px;">📈 Winner</p><p style="font-size:18px;color:#064e3b;'
             'margin:0;">' + winner + '</p></div>') if winner else ""
        l = ('<div style="flex:1;min-width:200px;background:#fef2f2;border:2px solid #ef4444;'
             'border-radius:10px;padding:20px;"><p style="font-size:20px;font-weight:bold;'
             'color:#991b1b;margin:0 0 8px;">📉 Loser</p><p style="font-size:18px;color:#7f1d1d;'
             'margin:0;">' + loser + '</p></div>') if loser else ""
        wl = '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:30px;">' + w + l + '</div>'

    bl_html = ""
    if bl:
        bl_html = ('<div style="background:#1e293b;border-radius:10px;padding:22px;margin-bottom:30px;">'
                   '<p style="font-size:20px;color:#fbbf24;font-weight:bold;margin:0;">' + bl + '</p></div>')

    teaser_html = ""
    if teaser:
        teaser_html = ('<div style="background:linear-gradient(135deg,#1e293b,#334155);border-radius:10px;'
                       'padding:24px;margin-bottom:30px;">'
                       '<p style="font-size:16px;color:#94a3b8;margin:0 0 8px;text-transform:uppercase;'
                       'letter-spacing:1px;">🔒 What VIP Subscribers Learned Today</p>'
                       '<p style="font-size:18px;color:#e2e8f0;margin:0;font-style:italic;">'
                       + teaser + '</p></div>')

    depth_cards = ('<div style="background:#fff;border:1px solid #e5e7eb;border-left:4px solid #3b82f6;'
                   'padding:24px;border-radius:8px;margin-bottom:15px;">'
                   '<h4 style="margin-top:0;font-size:20px;color:#1e40af;margin-bottom:10px;">'
                   '📰 What Happened</h4><p style="' + F + 'margin:0;">' + dw + '</p></div>')
    if dy:
        depth_cards += ('<div style="background:#fff;border:1px solid #e5e7eb;border-left:4px solid #f59e0b;'
                        'padding:24px;border-radius:8px;margin-bottom:15px;">'
                        '<h4 style="margin-top:0;font-size:20px;color:#b45309;margin-bottom:10px;">'
                        '🔍 Why It Matters</h4><p style="' + F + 'margin:0;">' + dy + '</p></div>')
    if du:
        depth_cards += ('<div style="background:#fff;border:1px solid #e5e7eb;border-left:4px solid #10b981;'
                        'padding:24px;border-radius:8px;margin-bottom:30px;">'
                        '<h4 style="margin-top:0;font-size:20px;color:#059669;margin-bottom:10px;">'
                        '💡 What It Means for You</h4><p style="' + F + 'margin:0;">' + du + '</p></div>')

    return (
        '<div style="' + MAIN + '">' + _hdr(a, tf)
        + _impact_badge(xtag(r, "IMPACT"))
        + _key_number(xtag(r, "KEY_NUMBER"), xtag(r, "KEY_NUMBER_CONTEXT"))
        + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">What Happened</h2>'
        + '<p style="' + F + 'margin-bottom:30px;">' + xtag(r, "SUMMARY") + '</p>'
        + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:35px;">'
        + '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">📱 TikTok Take</h3>'
        + '<p style="' + F + 'margin:0;">' + xtag(r, "TIKTOK") + '</p></div>'
        + '<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">' + xtag(r, "HEADLINE") + '</h3>'
        + depth_cards
        + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:8px;margin-bottom:30px;">'
        + '<strong style="font-size:18px;color:#b8974d;">⚡ Quick Flow:</strong>'
        + '<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">' + xtag(r, "FLOW") + '</p></div>'
        + bl_html + wl + _quick_hits(r) + teaser_html
        + _upgrade('🔒 Want deeper analysis? <strong>Upgrade to Pro or VIP.</strong>')
        + _ftr(xtag(r, "TAKEAWAY"), xtag(r, "PS"))
    )

# ═══════════════════════════════════════════════
# BUILD PREMIUM
# ═══════════════════════════════════════════════
def build_premium(a, tf, r):
    return (
        '<div style="' + MAIN + '">' + _hdr(a, tf, "PRO")
        + _impact_badge(xtag(r, "IMPACT"))
        + _key_number(xtag(r, "KEY_NUMBER"), xtag(r, "KEY_NUMBER_CONTEXT"))
        + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
        + '<p style="' + F + 'margin-bottom:35px;">' + xtag(r, "SUMMARY") + '</p>'
        + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:40px;">'
        + '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">📱 Viral Social Insights</h3>'
        + '<p style="' + F + 'margin:0;">' + xtag(r, "TIKTOK") + '</p></div>'
        + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers</h2>'
        + '<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">' + xtag(r, "HEADLINE") + '</h3>'
        + '<p style="' + F + 'margin-bottom:28px;">' + xtag(r, "DEPTH") + '</p>'
        + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:8px;margin-bottom:35px;">'
        + '<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
        + '<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">' + xtag(r, "FLOW") + '</p></div>'
        + _compare(xtag(r, "COMPARE_BULL"), xtag(r, "COMPARE_BEAR"))
        + _quick_hits(r)
        + '<div style="background:#fff;border:2px solid #3b82f6;padding:28px;border-radius:8px;margin-bottom:35px;">'
        + '<h3 style="margin-top:0;color:#1e40af;font-size:22px;margin-bottom:14px;">💎 Pro-Only Insight</h3>'
        + '<p style="' + F + 'margin:0;">' + xtag(r, "PRO_INSIGHT") + '</p></div>'
        + '<div style="background:#ecfdf5;border:2px solid #10b981;padding:24px;border-radius:8px;margin-bottom:15px;">'
        + '<p style="font-size:18px;line-height:1.8;color:#065f46;margin:0;"><strong style="color:#065f46;font-size:20px;">🟢 DO:</strong> '
        + xtag(r, "PRO_DO") + '</p></div>'
        + '<div style="background:#fef2f2;border:2px solid #ef4444;padding:24px;border-radius:8px;margin-bottom:35px;">'
        + '<p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;"><strong style="color:#991b1b;font-size:20px;">🔴 AVOID:</strong> '
        + xtag(r, "PRO_DONT") + '</p></div>'
        + _upgrade('🔒 Want institutional analysis? <strong>Upgrade to VIP.</strong>')
        + _ftr(xtag(r, "TAKEAWAY"), xtag(r, "PS"))
    )

# ═══════════════════════════════════════════════
# BUILD VIP
# ═══════════════════════════════════════════════
def build_vip(a, tf, raw, cat):
    theme = CAT_THEME.get(cat, CAT_THEME["Economy"])
    accent = theme["accent"]
    al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
    l1, v1, l2, v2, l3, v3 = parse_graph(xtag(raw, "GRAPH_DATA"), cat)

    # Sentiment meter
    sentiment_html = ""
    try:
        sr = xtag(raw, "SENTIMENT")
        if sr and sr.strip():
            digits = re.sub(r"[^0-9]", "", sr)
            if digits:
                sv = max(0, min(100, int(digits)))
                if sv <= 25:
                    sl, sc = "EXTREME FEAR", "#dc2626"
                elif sv <= 40:
                    sl, sc = "FEAR", "#ea580c"
                elif sv <= 60:
                    sl, sc = "NEUTRAL", "#ca8a04"
                elif sv <= 75:
                    sl, sc = "GREED", "#16a34a"
                else:
                    sl, sc = "EXTREME GREED", "#059669"
                sentiment_html = (
                    '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:25px;margin-bottom:35px;">'
                    '<h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:18px;">🧭 Fear &amp; Greed Meter</h3>'
                    '<div style="position:relative;width:100%;height:20px;border-radius:10px;overflow:hidden;'
                    'background:linear-gradient(to right,#dc2626,#ea580c,#ca8a04,#16a34a,#059669);">'
                    '<div style="position:absolute;left:' + str(sv) + '%;top:0;width:4px;height:100%;'
                    'background:#fff;border-radius:2px;box-shadow:0 0 4px rgba(0,0,0,0.5);"></div></div>'
                    '<div style="display:flex;justify-content:space-between;margin-top:8px;">'
                    '<span style="font-size:14px;color:#dc2626;font-weight:600;">Fear</span>'
                    '<span style="font-size:20px;color:' + sc + ';font-weight:800;">' + str(sv) + ' - ' + sl + '</span>'
                    '<span style="font-size:14px;color:#059669;font-weight:600;">Greed</span></div></div>'
                )
    except Exception:
        pass

    # Conviction badge
    conviction = xtag(raw, "CONVICTION").upper().strip()
    conv_html = ""
    if conviction:
        conv_colors = {"HIGH": ("#065f46", "#ecfdf5", "🟢"), "MEDIUM": ("#92400e", "#fffbeb", "🟡"), "LOW": ("#991b1b", "#fef2f2", "🔴")}
        cc, cbg, ci = conv_colors.get(conviction, ("#6b7280", "#f3f4f6", "⚪"))
        conv_html = (
            '<div style="background:' + cbg + ';border:2px solid ' + cc + ';border-radius:10px;'
            'padding:20px;margin-bottom:35px;text-align:center;">'
            '<p style="font-size:14px;color:#6b7280;margin:0 0 5px;text-transform:uppercase;">Overall Conviction</p>'
            '<p style="font-size:28px;font-weight:800;color:' + cc + ';margin:0;">' + ci + ' ' + conviction + '</p></div>'
        )

    # Gauge bars
    def gauge(lb, val, c):
        return ('<div style="margin-bottom:22px;"><div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
                '<span style="font-size:18px;font-weight:600;color:#374151;">' + lb + '</span>'
                '<span style="font-size:18px;font-weight:700;color:' + c + ';">' + str(val) + '%</span></div>'
                '<div style="width:100%;background:#e5e7eb;border-radius:8px;height:16px;overflow:hidden;">'
                '<div style="width:' + str(val) + '%;background:' + c + ';height:100%;border-radius:8px;"></div></div></div>')

    # Pie chart
    s, b, cp = al["s"], al["b"], al["c"]
    circ = 565.49
    sd = circ * s / 100
    bd = circ * b / 100
    cd = circ * cp / 100
    pie = (
        '<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;">'
        '<circle cx="100" cy="100" r="90" fill="none" stroke="' + accent + '" stroke-width="30" '
        'stroke-dasharray="' + f"{sd:.1f}" + ' ' + f"{circ:.1f}" + '" stroke-dashoffset="0"/>'
        '<circle cx="100" cy="100" r="90" fill="none" stroke="#64748b" stroke-width="30" '
        'stroke-dasharray="' + f"{bd:.1f}" + ' ' + f"{circ:.1f}" + '" stroke-dashoffset="-' + f"{sd:.1f}" + '"/>'
        '<circle cx="100" cy="100" r="90" fill="none" stroke="#b8974d" stroke-width="30" '
        'stroke-dasharray="' + f"{cd:.1f}" + ' ' + f"{circ:.1f}" + '" stroke-dashoffset="-' + f"{sd+bd:.1f}" + '"/>'
        '<text x="100" y="92" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">'
        + str(s) + '/' + str(b) + '/' + str(cp) + '</text>'
        '<text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>'
        '<div style="display:flex;justify-content:center;gap:20px;margin-bottom:8px;">'
        '<span style="font-size:16px;color:' + accent + ';">● Stocks ' + str(s) + '%</span>'
        '<span style="font-size:16px;color:#64748b;">● Safe ' + str(b) + '%</span>'
        '<span style="font-size:16px;color:#b8974d;">● Cash ' + str(cp) + '%</span></div>'
        '<p style="font-size:16px;color:#6b7280;text-align:center;font-style:italic;margin:5px 0 0;">'
        + al["note"] + '</p>'
    )

    # Sector Radar
    rr = ""
    for i in range(1, 5):
        v = ok_tag(raw, "VIP_RADAR_" + str(i))
        if not v:
            continue
        bull = "bullish" in v.lower()
        bg_r = "#ecfdf5" if bull else "#fef2f2"
        tc = "#065f46" if bull else "#991b1b"
        ic = "🟢 BULL" if bull else "🔴 BEAR"
        rr += ('<tr><td style="padding:14px;border-bottom:1px solid #e5e7eb;font-size:18px;color:#374151;">'
               + v + '</td><td style="padding:14px;border-bottom:1px solid #e5e7eb;text-align:center;">'
               '<span style="background:' + bg_r + ';color:' + tc + ';padding:4px 12px;border-radius:6px;'
               'font-size:16px;font-weight:bold;">' + ic + '</span></td></tr>')
    radar = ""
    if rr:
        radar = ('<div style="background:#fff;border:2px solid ' + accent + ';border-radius:8px;'
                 'padding:25px;margin-bottom:35px;">'
                 '<h3 style="margin-top:0;color:' + accent + ';font-size:22px;margin-bottom:18px;">'
                 '🎯 Sector Radar</h3>'
                 '<table style="width:100%;border-collapse:collapse;">' + rr + '</table></div>')

    # Metric cards
    COL = [accent, "#f59e0b", "#10b981"]
    def mcard(lb, val, c):
        return ('<div style="flex:1;min-width:200px;background:#f8fafc;border:2px solid ' + c
                + ';border-radius:10px;padding:22px;text-align:center;">'
                '<div style="font-size:42px;font-weight:800;color:' + c + ';margin-bottom:5px;">'
                + str(val) + '%</div><div style="font-size:16px;color:#4b5563;font-weight:600;">'
                + lb + '</div></div>')

    # Extract VIP sections
    c1 = ok_tag(raw, "VIP_C1")
    c2 = ok_tag(raw, "VIP_C2")
    c3 = ok_tag(raw, "VIP_C3")
    t1 = ok_tag(raw, "VIP_T1")
    t2 = ok_tag(raw, "VIP_T2")
    t3 = ok_tag(raw, "VIP_T3")
    t4 = ok_tag(raw, "VIP_T4")
    vdo = ok_tag(raw, "VIP_DO")
    vdont = ok_tag(raw, "VIP_DONT")
    tw = ok_tag(raw, "TAKEAWAY")
    ps = ok_tag(raw, "PS")

    # Macro section with sub-labels
    macro_html = ""
    if c1 or c2 or c3:
        paras = ""
        if c1:
            paras += ('<p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;'
                      'text-transform:uppercase;letter-spacing:0.5px;">Technical Signals</p>'
                      '<p style="' + F + 'margin-bottom:22px;">' + c1 + '</p>')
        if c2:
            paras += '<div style="border-top:1px solid #e5e7eb;margin:8px 0 18px;"></div>'
            paras += ('<p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;'
                      'text-transform:uppercase;letter-spacing:0.5px;">Macro Flows</p>'
                      '<p style="' + F + 'margin-bottom:22px;">' + c2 + '</p>')
        if c3:
            paras += '<div style="border-top:1px solid #e5e7eb;margin:8px 0 18px;"></div>'
            paras += ('<p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;'
                      'text-transform:uppercase;letter-spacing:0.5px;">Smart Money</p>'
                      '<p style="' + F + 'margin-bottom:0;">' + c3 + '</p>')
        macro_html = (
            '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:25px;'
            'border-bottom:3px solid ' + accent + ';padding-bottom:12px;display:inline-block;">'
            'VIP: Macro &amp; Flow Analysis</h2>'
            '<div style="background:#fff;border:1px solid #e5e7eb;border-left:5px solid ' + accent
            + ';padding:28px;border-radius:8px;margin-bottom:40px;">'
            '<p style="font-size:18px;color:' + accent + ';text-transform:uppercase;font-weight:bold;'
            'margin-top:0;margin-bottom:22px;">[Institutional Technical Outlook]</p>'
            + paras + '</div>'
        )

    # Playbook cards (empty = hidden)
    def pb(n, title, body, extra=""):
        if not body:
            return ""
        mt = "margin-top:22px;" if extra else ""
        return ('<div style="background:#f8fafc;border:1px solid #e5e7eb;border-left:4px solid '
                + accent + ';padding:28px;border-radius:8px;margin-bottom:25px;">'
                '<h3 style="color:#1a252c;margin-top:0;font-size:24px;margin-bottom:18px;">'
                + str(n) + '. ' + title + '</h3>' + extra
                + '<p style="' + F + 'margin-bottom:0;' + mt + '">' + body + '</p></div>')

    playbook_cards = ""
    playbook_cards += pb("1", "The Generational Bargain (Fear vs. Greed)", t1)
    playbook_cards += pb("2", "The " + str(s) + "/" + str(b) + "/" + str(cp) + " Seesaw (Asset Allocation)", t2, pie)
    playbook_cards += pb("3", "The Global Shield (US Dollar &amp; Market)", t3)
    playbook_cards += pb("4", "Survival Mechanics (DCA &amp; Risk Management)", t4)

    playbook_html = ""
    if playbook_cards:
        playbook_html = (
            '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:12px;'
            'border-bottom:3px solid ' + accent + ';padding-bottom:12px;display:inline-block;">'
            'The Titans Playbook</h2>'
            '<p style="font-size:18px;color:#6b7280;margin-bottom:30px;font-style:italic;">'
            'Strategic manual for ' + cat.lower() + ' conditions.</p>'
            + playbook_cards
        )

    # Action Plan
    action_html = ""
    if vdo or vdont:
        do_b = ""
        if vdo:
            do_b = ('<div style="background:#ecfdf5;border:2px solid #10b981;border-radius:8px;'
                    'padding:24px;margin-bottom:20px;">'
                    '<p style="font-size:20px;color:#065f46;font-weight:bold;margin:0 0 12px;">🟢 DO (Action):</p>'
                    '<p style="font-size:18px;line-height:1.8;color:#064e3b;margin:0;">' + vdo + '</p></div>')
        dont_b = ""
        if vdont:
            dont_b = ('<div style="background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:24px;">'
                      '<p style="font-size:20px;color:#991b1b;font-weight:bold;margin:0 0 12px;">🔴 AVOID:</p>'
                      '<p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;">' + vdont + '</p></div>')
        action_html = (
            '<div style="background:#1e293b;padding:35px;border-radius:10px;margin:45px 0 40px;">'
            '<h3 style="color:#b8974d;margin-top:0;font-size:26px;margin-bottom:25px;'
            'border-bottom:2px solid #475569;padding-bottom:15px;">✅ VIP Action Plan</h3>'
            + do_b + dont_b + '</div>'
        )

    # Assemble
    return (
        '<div style="' + MAIN + '">' + _hdr(a, tf, "VIP EXCLUSIVE")

        # Badge row
        + '<div style="margin-bottom:25px;">'
        + _impact_badge(xtag(raw, "IMPACT"))
        + '<span style="display:inline-block;background:#f8fafc;border:2px solid ' + accent
        + ';color:' + accent + ';padding:4px 14px;border-radius:20px;font-size:14px;font-weight:bold;">'
        + theme["icon"] + ' ' + theme["label"] + '</span></div>'

        + _key_number(xtag(raw, "KEY_NUMBER"), xtag(raw, "KEY_NUMBER_CONTEXT"), accent)
        + _market_snap(raw)
        + sentiment_html

        # Reading time + TOC
        + '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:22px;margin-bottom:30px;">'
        + '<p style="font-size:16px;color:#6b7280;margin:0 0 12px;">'
        + '⏱ <strong style="color:#1a252c;">8-10 min read</strong> | Full institutional analysis</p>'
        + '<div style="display:flex;flex-wrap:wrap;gap:8px;">'
        + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">📊 Data</span>'
        + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">🎯 Radar</span>'
        + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">🔬 Macro</span>'
        + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">📖 Playbook</span>'
        + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">✅ Action</span>'
        + '</div></div>'

        + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
        + '<p style="' + F + 'margin-bottom:35px;">' + xtag(raw, "SUMMARY") + '</p>'

        + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:40px;">'
        + '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">📱 Viral Social Insights</h3>'
        + '<p style="' + F + 'margin:0;">' + xtag(raw, "TIKTOK") + '</p></div>'

        + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers &amp; Insights</h2>'
        + '<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">' + xtag(raw, "HEADLINE") + '</h3>'
        + '<p style="' + F + 'margin-bottom:28px;">' + xtag(raw, "DEPTH") + '</p>'

        + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:22px;border-radius:8px;margin-bottom:40px;">'
        + '<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
        + '<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">' + xtag(raw, "FLOW") + '</p></div>'

        # Metric cards
        + '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">'
        + mcard(l1, v1, COL[0]) + mcard(l2, v2, COL[1]) + mcard(l3, v3, COL[2]) + '</div>'

        # Gauge bars
        + '<div style="padding:28px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:35px;">'
        + '<h3 style="margin-top:0;color:#1a252c;font-size:22px;border-bottom:2px solid #e5e7eb;'
        + 'padding-bottom:14px;margin-bottom:25px;">📊 Key Market Indicators</h3>'
        + gauge(l1, v1, COL[0]) + gauge(l2, v2, COL[1]) + gauge(l3, v3, COL[2]) + '</div>'

        + radar
        + _compare(ok_tag(raw, "COMPARE_BULL"), ok_tag(raw, "COMPARE_BEAR"),
                   "Institutional Bull Case", "Institutional Bear Case")
        + macro_html
        + playbook_html
        + conv_html
        + action_html
        + _ftr(tw, ps)
    )

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
def main():
    print("=" * 50 + "\n  Warm Insight v8 FINAL\n" + "=" * 50)
    total = ok_cnt = fail = 0

    for cat, urls in CATEGORIES.items():
        print(f"\n--- [{cat}] ---")
        news = get_news(urls, 20)
        if len(news) < 3:
            print("  Skip: not enough news")
            continue
        for task in TASKS:
            tier = task["tier"]
            cnt = task["count"]
            if len(news) < cnt:
                print(f"  Skip {tier}: not enough news")
                break
            target = [news.pop(0) for _ in range(cnt)]
            total += 1
            print(f"\n  [{TIER_LABELS[tier]}] {cnt} articles...")

            result = analyze(target, cat, tier)
            if not result or not result[2]:
                fail += 1
                continue
            title, ip, html, exc, kw, slug = result

            iu = None
            if ip:
                ib = make_thumb(ip, tier, cat)
                if ib:
                    iu = upload_img(ib)
            publish(title, html, cat, tier, iu, exc, kw, slug)
            ok_cnt += 1
            sl = TIER_SLEEP[tier]
            print(f"  Wait {sl}s...")
            time.sleep(sl)

    print(f"\n{'=' * 50}\n  Total {total} | OK {ok_cnt} | Fail {fail}\n{'=' * 50}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nSystem error")
        traceback.print_exc()
        sys.exit(1)
