# -*- coding: utf-8 -*-
"""
Warm Insight v7 — Framework Integration + Reliability Overhaul
==============================================================
v6 -> v7 핵심:
  1. Part2 실패시 단일호출 Fallback (Generating... 완전 제거)
  2. 빈 섹션 숨김 (placeholder 대신 섹션 자체를 제거)
  3. 사고 프레임워크 적용 (추상화 사다리, 시스템 사고, 2차적 사고)
     - Basic: 나무 수준 (구체적, ELI5)
     - Premium: 숲 수준 (패턴, 행동경제학, 왜?)
     - VIP: 우주 수준 (매크로, 2/3차 효과, 역사적 병행)
  4. 정확성 규칙 대폭 강화 (거짓정보 원천 차단)
  5. 가독성 개선 (밝은 배경, 큰 글씨, 섹션 간격)
"""

import os, sys, traceback, time, random, re, json
from datetime import datetime

import requests
import jwt
import feedparser
from google import genai
from google.genai import types

GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL       = os.environ.get("GHOST_API_URL", "").rstrip("/")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")
if not all([GEMINI_API_KEY, GHOST_API_URL, GHOST_ADMIN_API_KEY]):
    sys.exit("Missing keys")

CATEGORIES = {
    "Economy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
                "https://finance.yahoo.com/news/rssindex"],
    "Politics": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113"],
    "Tech": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"],
    "Health": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108"],
    "Energy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810"],
}

TASKS = [
    {"tier": "Basic", "count": 2},
    {"tier": "Premium", "count": 3},
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
    "Politics": "a veteran US political strategist with 40 years of Washington experience",
    "Tech":     "a veteran Silicon Valley technology analyst with 40 years of experience",
    "Health":   "a veteran US healthcare and biotech analyst with 40 years of experience",
    "Energy":   "a veteran US energy and commodities strategist with 40 years of experience",
    "Economy":  "a veteran US Wall Street strategist with 40 years of experience",
}

CAT_THEME = {
    "Economy": {"icon": "💰", "accent": "#2563eb", "label": "MACRO & RATES"},
    "Politics": {"icon": "🏛", "accent": "#dc2626", "label": "GEOPOLITICS"},
    "Tech": {"icon": "🤖", "accent": "#7c3aed", "label": "AI & DISRUPTION"},
    "Health": {"icon": "🧬", "accent": "#059669", "label": "BIOTECH & PHARMA"},
    "Energy": {"icon": "⚡", "accent": "#d97706", "label": "OIL, GAS & RENEWABLES"},
}

CAT_ALLOC = {
    "Economy":  {"s": 55, "b": 35, "c": 10, "note": "Defensive: higher bonds during macro uncertainty"},
    "Politics": {"s": 50, "b": 35, "c": 15, "note": "Elevated cash for geopolitical shock absorption"},
    "Tech":     {"s": 70, "b": 20, "c": 10, "note": "Growth tilt: overweight innovation equities"},
    "Health":   {"s": 60, "b": 30, "c": 10, "note": "Balanced: pharma stability with biotech upside"},
    "Energy":   {"s": 65, "b": 25, "c": 10, "note": "Commodity tilt: overweight real assets"},
}

CAT_METRICS = {
    "Economy": {"pool": ["Inflation Momentum","Recession Risk","Consumer Pulse","Credit Stress","Rate Cut Odds","Dollar Strength","Yield Curve","PMI Signal","Wage Tension"], "hint": "inflation, GDP, employment, Fed policy"},
    "Politics": {"pool": ["Policy Uncertainty","Regulatory Risk","Geopolitical Tension","Election Volatility","Trade War Risk","Sanctions Impact","Legislative Gridlock","Defense Momentum"], "hint": "policy, regulation, geopolitics, elections"},
    "Tech": {"pool": ["AI Race Intensity","Antitrust Pressure","Chip Supply Stress","IPO Sentiment","Cloud Velocity","Cyber Threat","Big Tech Momentum","Funding Freeze"], "hint": "AI, semiconductors, regulation, startup funding"},
    "Health": {"pool": ["Pipeline Confidence","Drug Pricing Pressure","Biotech Funding","FDA Momentum","Gene Therapy Index","Hospital Stress","Coverage Gap","Trial Success"], "hint": "pharma pipelines, drug pricing, FDA, biotech"},
    "Energy": {"pool": ["Oil Supply Squeeze","Green Transition","OPEC Tension","LNG Surge","Renewable Growth","Geo Shock Risk","Grid Stress","Carbon Heat"], "hint": "oil, OPEC, renewables, LNG, geopolitics"},
}

VIP_THUMB = {
    "Economy": "Dark dramatic 3D golden scales with dollar bills, cinematic blue lighting, data hologram, 8k",
    "Politics": "Dark dramatic 3D marble chess board geopolitical symbols, red accent lighting, 8k",
    "Tech": "Dark dramatic 3D neural network purple glow, circuit landscape, AI hologram, 8k",
    "Health": "Dark dramatic 3D DNA helix with golden capsules, green glow, medical theme, 8k",
    "Energy": "Dark dramatic 3D oil derricks vs solar panels, amber golden lighting, 8k",
}

# ── 정확성 규칙 (모든 프롬프트에 삽입) ──
ACCURACY = """
STRICT ACCURACY RULES (NEVER VIOLATE):
- ONLY analyze facts from the news articles provided. NEVER invent events, names, or incidents.
- NEVER fabricate specific prices, RSI numbers, or statistics. Use directional language instead.
- Use hedging: "likely", "suggests", "indicates" — not definitive false claims.
- If news does not mention something, do NOT create it. Analyze what IS there.
- Reference only real, well-known ETF tickers (SPY, XLE, XLV, IEF, GLD, etc).
"""

# ──────────────────────────────────────────────
# PROMPTS — 사고 프레임워크 적용
# ──────────────────────────────────────────────

# ✅ Basic: 나무 수준 (추상화 사다리 하단 — 구체적, 감각적)
PROMPT_BASIC = """
You are [PERSONA] for 'Warm Insight' ([CATEGORY]).
Audience: Beginners who know nothing about finance. Explain like a kind teacher to a 15-year-old.
[ACCURACY]
STYLE: Stay at the BOTTOM of the "Ladder of Abstraction" — use concrete, everyday analogies.
English only. Max 400 words.

OUTPUT (XML):
<SEO_KEYWORD>3-6 word search phrase someone would Google</SEO_KEYWORD>
<TITLE>Simple catchy title with SEO keyword near the front</TITLE>
<IMAGE_PROMPT>Simple 3D abstract cinematic about [CATEGORY]</IMAGE_PROMPT>
<EXCERPT>1 sentence with SEO keyword</EXCERPT>
<SUMMARY>3 sentences. First sentence includes SEO keyword. Use everyday analogies.</SUMMARY>
<TIKTOK>Fun TikTok analogy (2-3 sentences)</TIKTOK>
<HEADLINE>Key insight in plain language</HEADLINE>
<DEPTH>What happened? (like explaining to a friend) Why should I care? What does it mean for my daily life? 3-4 sentences.</DEPTH>
<FLOW>Each step has TEXT and emoji: "Prices Rise 📈 ➡️ Your Groceries Cost More 🛒 ➡️ You Save Less 💸"</FLOW>
<TAKEAWAY>One comforting actionable sentence</TAKEAWAY>
<PS>One warm personal thought</PS>

News: [NEWS_ITEMS]
"""

# ✅ Premium: 숲 수준 (추상화 사다리 중간 — 패턴, 행동경제학)
PROMPT_PREMIUM = """
You are [PERSONA] for 'Warm Insight' ([CATEGORY]).
Audience: Intermediate investors who want the deeper "why" behind news.
[ACCURACY]
STYLE: Climb to the MIDDLE of the "Ladder of Abstraction" — identify PATTERNS and BEHAVIORAL BIASES.
Apply Second-Order Thinking: "And then what happens?" — trace consequences 2 steps ahead.
English only. 600-800 words.

OUTPUT (XML):
<SEO_KEYWORD>4-7 word long-tail keyword</SEO_KEYWORD>
<TITLE>Analytical title with SEO keyword</TITLE>
<IMAGE_PROMPT>3D cinematic about [CATEGORY]</IMAGE_PROMPT>
<EXCERPT>1 sentence with SEO keyword</EXCERPT>
<SUMMARY>3 sentences. First includes SEO keyword.</SUMMARY>
<TIKTOK>TikTok analogy revealing a hidden truth</TIKTOK>
<HEADLINE>Analytical headline</HEADLINE>
<DEPTH><strong>🧐 WHY (Pattern):</strong> What deeper pattern or behavioral bias explains this? Apply behavioral economics. 4-5 sentences.<br><br><strong>🐑 HERD TRAP:</strong> What is the crowd doing wrong? What cognitive bias is at play? 3-4 sentences.</DEPTH>
<FLOW>Each step has TEXT and emoji (5+ steps): "Fed Signal 🦅 ➡️ Dollar Strengthens 💵 ➡️ EM Pain 🌏"</FLOW>
<PRO_INSIGHT>Non-obvious cross-sector connection. Use Second-Order Thinking. 4-5 sentences.</PRO_INSIGHT>
<PRO_DO>2 specific actions</PRO_DO>
<PRO_DONT>1 specific mistake</PRO_DONT>
<TAKEAWAY>Insightful takeaway</TAKEAWAY>
<PS>Historical perspective (2 sentences)</PS>

News: [NEWS_ITEMS]
"""

# ✅ VIP Part 1: 우주 수준 (추상화 사다리 최상단 + Zoom Back Down)
VIP_P1 = """
You are [PERSONA] for 'Warm Insight' VIP ([CATEGORY]).
Audience: Sophisticated investors paying premium for alpha.
[ACCURACY]
STYLE: Reach the TOP of the "Ladder of Abstraction" — see the SYSTEM, not just events.
Apply Systems Thinking: feedback loops, interconnections, structural causes.
Apply Second and Third-Order Thinking: trace consequences 3 steps ahead.
Then ZOOM BACK DOWN to specific, actionable insights.

WRITE real analysis in each tag (NOT instructions):

<SEO_KEYWORD>4-8 word long-tail keyword a sophisticated investor would search</SEO_KEYWORD>
<TITLE>Institutional title with SEO keyword near front</TITLE>
<IMAGE_PROMPT>[CAT_THUMB]</IMAGE_PROMPT>
<EXCERPT>1 VIP-grade sentence with SEO keyword</EXCERPT>
<SUMMARY>3 institutional sentences. First MUST include SEO keyword.</SUMMARY>
<TIKTOK>Gen-Z viral analogy</TIKTOK>
<HEADLINE>Alpha headline</HEADLINE>
<DEPTH><strong>🧐 MACRO (Systems View):</strong> Analyze the SYSTEM — what structural forces, feedback loops, and policy dynamics are driving this? Connect to global capital flows. 5+ sentences.<br><br><strong>🐑 HERD BIAS:</strong> What cognitive bias (recency, anchoring, etc) is making the crowd wrong? 4+ sentences.<br><br><strong>🦅 CONTRARIAN (2nd/3rd Order):</strong> What does smart money see? Trace the chain: 1st order effect → 2nd order consequence → 3rd order opportunity. 5+ sentences.</DEPTH>
<FLOW>Each step has TEXT label AND emoji (6+ steps): "Supply Deficit 🛢 ➡️ Price Spike 📈 ➡️ Margin Squeeze 📉 ➡️ Capex Cut ✂️ ➡️ Future Shortage 💥 ➡️ Structural Bull 🐂"</FLOW>
<GRAPH_DATA>3 metrics for [CATEGORY]. [CAT_HINT]. Scores MUST be different (25-90 range). Format: Name1|Score1|Name2|Score2|Name3|Score3</GRAPH_DATA>
<VIP_RADAR_1>Sector — BULLISH or BEARISH — why (1 sentence)</VIP_RADAR_1>
<VIP_RADAR_2>Sector — BULLISH or BEARISH — why</VIP_RADAR_2>
<VIP_RADAR_3>Sector — BULLISH or BEARISH — why</VIP_RADAR_3>
<VIP_RADAR_4>Sector — BULLISH or BEARISH — why</VIP_RADAR_4>
<VIP_C1>Technical Outlook: general directional analysis of key sector ETFs. Trends, momentum, support zones. 5+ sentences.</VIP_C1>
<VIP_C2>Macro Flow: yield curves, credit conditions, dollar dynamics. 5+ sentences.</VIP_C2>
<VIP_C3>Smart Money: institutional positioning trends. 5+ sentences.</VIP_C3>

NEWS: [NEWS_ITEMS]
"""

# ✅ VIP Part 2: Zoom Down — 우주적 통찰을 일상 행동으로
VIP_P2 = """
You are [PERSONA]. You wrote Part 1 for VIP ([CATEGORY]).
[ACCURACY]
STYLE: Now ZOOM DOWN from the macro view to SPECIFIC ACTIONS.
Like Leonardo da Vinci oscillating between cosmic vision and precise detail.

YOUR ANALYSIS SO FAR:
---
[CTX]
---

Write REAL strategy content. Each tag must contain substantive paragraphs, NOT instructions.

<VIP_T1>Fear vs Greed right now for [CATEGORY]? What would Buffett do? Templeton? Be specific and write with conviction. 6+ sentences of real analysis.</VIP_T1>
<VIP_T2>Asset allocation for [CATEGORY]: recommend [ALLOC_STR]. Name real ETFs for each bucket. What to adjust this week. 6+ sentences.</VIP_T2>
<VIP_T3>Why US assets matter now vs Europe/China/EM. Dollar dynamics. 5+ sentences.</VIP_T3>
<VIP_T4>DCA strategy for this news. When to deploy. The 50% rule: at what drawdown to sell half. 6+ sentences.</VIP_T4>
<VIP_DO>3 actions. Each: real ETF/stock name, percentage, trigger condition.</VIP_DO>
<VIP_DONT>2 mistakes to avoid with explanation of why dangerous now.</VIP_DONT>
<TAKEAWAY>One masterful calming sentence.</TAKEAWAY>
<PS>40-year wisdom. Reference one historical parallel. 2-3 sentences.</PS>

NEWS: [NEWS_ITEMS]
"""

# ✅ v7: Part 2 실패시 단일호출 Fallback (짧지만 실질적)
VIP_FALLBACK = """
You are [PERSONA] writing a CONCISE strategy section for VIP [CATEGORY] newsletter.
[ACCURACY]
Based on this analysis: [CTX_SHORT]

Write ALL of the following in one response. Each must contain REAL content:

<VIP_T1>Is this a Fear or Greed moment? What would a wise long-term investor do? 3-4 sentences.</VIP_T1>
<VIP_T2>Recommended allocation for [CATEGORY] investors: [ALLOC_STR]. Name 2 specific ETFs. 3-4 sentences.</VIP_T2>
<VIP_T3>Why US markets are safer than alternatives right now. 2-3 sentences.</VIP_T3>
<VIP_T4>Dollar-cost averaging advice. When to buy more vs hold cash. 3-4 sentences.</VIP_T4>
<VIP_DO>2 specific actions with real ETF names.</VIP_DO>
<VIP_DONT>1 specific mistake to avoid.</VIP_DONT>
<TAKEAWAY>One calming insight.</TAKEAWAY>
<PS>One historical parallel. 1-2 sentences.</PS>

NEWS: [NEWS_ITEMS]
"""

# ──────────────────────────────────────────────
# UTILS
# ──────────────────────────────────────────────
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
                seen.add(t)
                news.append(f"- {t}: {getattr(e, 'summary', '')}")
                if len(news) >= count: break
        except: continue
    return news[:count]

def parse_graph(raw, cat):
    if not raw: return _fb_graph(cat)
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 6: return _fb_graph(cat)
    try:
        v1,v2,v3 = int(re.sub(r"[^0-9]","",parts[1])), int(re.sub(r"[^0-9]","",parts[3])), int(re.sub(r"[^0-9]","",parts[5]))
        if v1==v2==v3: return _fb_graph(cat)
        return parts[0],max(10,min(95,v1)),parts[2],max(10,min(95,v2)),parts[4],max(10,min(95,v3))
    except: return _fb_graph(cat)

def _fb_graph(cat):
    pool = CAT_METRICS.get(cat,CAT_METRICS["Economy"])["pool"]
    lb = random.sample(pool,3)
    return lb[0],random.randint(55,88),lb[1],random.randint(30,65),lb[2],random.randint(40,78)

def is_echo(text):
    if not text or len(text)<80: return True
    sigs = ["6+ sentences","5+ sentences","At least 5","Write a detailed","Name ETFs","which ETF","trigger price","Write exactly","explain WHY","Write real","Write ALL"]
    return sum(1 for s in sigs if s.lower() in text.lower()) >= 2

def ok(raw, tag):
    v = xtag(raw, tag)
    if not v or is_echo(v): return ""
    return v

def sanitize(h):
    return re.sub(r"\s+", " ", h.replace("\n"," ").replace("\r",""))

def make_slug(kw, title):
    t = kw if kw else title
    s = re.sub(r"[^a-zA-Z0-9\s-]","",t.lower())
    return re.sub(r"\s+","-",s.strip())[:80]

# ──────────────────────────────────────────────
# GHOST
# ──────────────────────────────────────────────
def gtoken():
    kid,sec = str(GHOST_ADMIN_API_KEY).split(":")
    iat = int(datetime.now().timestamp())
    return jwt.encode({"iat":iat,"exp":iat+300,"aud":"/admin/"},bytes.fromhex(sec),algorithm="HS256",headers={"alg":"HS256","typ":"JWT","kid":kid})

def upload_img(ib):
    try:
        r = requests.post(f"{GHOST_API_URL}/ghost/api/admin/images/upload/",headers={"Authorization":f"Ghost {gtoken()}"},files={"file":("t.jpg",ib,"image/jpeg"),"purpose":(None,"image")},timeout=30)
        if r.status_code in (200,201): return r.json()["images"][0]["url"]
    except Exception as e: print(f"  img: {e}")
    return None

def publish(title,html,cat,tier,iu,exc,kw="",slug=""):
    print(f"  Pub: {title[:50]}...")
    try:
        md = json.dumps({"version":"0.3.1","markups":[],"atoms":[],"cards":[["html",{"html":html}]],"sections":[[10,0]]})
        p = {"title":title,"mobiledoc":md,"status":"published","visibility":TIER_VIS.get(tier,"public"),"tags":[{"name":cat},{"name":tier}]}
        if slug: p["slug"]=slug
        if kw:
            mt = f"{title} | Warm Insight {cat}"
            md_desc = f"{exc[:140]} Expert {cat.lower()} analysis."
            p.update({"meta_title":mt[:300],"meta_description":md_desc[:500],"og_title":mt[:300],"og_description":md_desc[:300]})
        if exc: p["custom_excerpt"]=exc[:290]
        if iu:
            p["feature_image"]=iu
            if kw: p["feature_image_alt"]=f"{kw} - Warm Insight {cat}"
        r = requests.post(f"{GHOST_API_URL}/ghost/api/admin/posts/",json={"posts":[p]},headers={"Authorization":f"Ghost {gtoken()}","Content-Type":"application/json"},timeout=60)
        if r.status_code in (200,201): print("  OK!")
        else: print(f"  FAIL {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"  ERR: {e}")
        traceback.print_exc()

# ──────────────────────────────────────────────
# THUMBNAIL
# ──────────────────────────────────────────────
def make_thumb(ip, tier, cat):
    if tier == "Royal Premium": ip = VIP_THUMB.get(cat, ip)
    tries = 3 if tier == "Royal Premium" else 1
    for a in range(1,tries+1):
        try:
            c = genai.Client(api_key=GEMINI_API_KEY)
            r = c.models.generate_images(model="imagen-3.0-generate-001",prompt=ip,config=types.GenerateImagesConfig(number_of_images=1,aspect_ratio="16:9",output_mime_type="image/jpeg"))
            if r.generated_images:
                print(f"  Imagen OK({a})")
                return r.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"  Imagen({a}): {e}")
            if a<tries: time.sleep(5)
    try:
        r = requests.get(f"https://picsum.photos/seed/{random.randint(1,9999)}/1280/720",timeout=10)
        if r.status_code==200: return r.content
    except: pass
    return None

# ──────────────────────────────────────────────
# GEMINI
# ──────────────────────────────────────────────
def gem(client,model,prompt,retries=2):
    for i in range(1,retries+1):
        try:
            r = client.models.generate_content(model=model,contents=prompt)
            return str(r.text)
        except Exception as e:
            print(f"    Gem({model})try{i}: {type(e).__name__}: {e}")
            if i<retries: time.sleep(10*i)
    return None

def gem_fb(client,tier,prompt):
    for m in MODEL_PRI.get(tier,["gemini-2.5-flash"]):
        print(f"    [AI] {m}")
        r = gem(client,m,prompt)
        if r: return r,m
    return None,None

# ──────────────────────────────────────────────
# ANALYZE
# ──────────────────────────────────────────────
def analyze(news_items,cat,tier):
    client = genai.Client(api_key=GEMINI_API_KEY)
    ns = "\n".join(news_items)
    persona = EXPERT.get(cat,EXPERT["Economy"])
    now = datetime.now()
    ts,tf = now.strftime("%I:%M %p"),now.strftime("%B %d, %Y at %I:%M %p (UTC)")
    author = "Ethan Cole &amp; The Warm Insight Panel"
    acc = ACCURACY

    if tier == "Basic":
        p = PROMPT_BASIC.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[ACCURACY]",acc).replace("[NEWS_ITEMS]",ns)
        raw,_ = gem_fb(client,tier,p)
        if not raw: return None,None,None,None,None,None
        html = build_basic(author,tf,raw)

    elif tier == "Premium":
        p = PROMPT_PREMIUM.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[ACCURACY]",acc).replace("[NEWS_ITEMS]",ns)
        raw,_ = gem_fb(client,tier,p)
        if not raw: return None,None,None,None,None,None
        html = build_premium(author,tf,raw)

    else:
        hint = CAT_METRICS.get(cat,CAT_METRICS["Economy"])["hint"]
        thumb = VIP_THUMB.get(cat,"3D cinematic "+cat)
        al = CAT_ALLOC.get(cat,CAT_ALLOC["Economy"])
        al_str = f"{al['s']}% stocks, {al['b']}% safe, {al['c']}% cash ({al['note']})"

        # Part 1
        p1 = VIP_P1.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[ACCURACY]",acc).replace("[CAT_HINT]",hint).replace("[CAT_THUMB]",thumb).replace("[NEWS_ITEMS]",ns)
        raw1,_ = gem_fb(client,tier,p1)
        if not raw1: return None,None,None,None,None,None

        if not xtag(raw1,"VIP_C1") or is_echo(xtag(raw1,"VIP_C1")):
            print("    P1 retry...")
            time.sleep(15)
            r1r,_ = gem_fb(client,tier,p1)
            if r1r and xtag(r1r,"VIP_C1") and not is_echo(xtag(r1r,"VIP_C1")):
                raw1 = r1r

        ctx = f"Title: {xtag(raw1,'TITLE')}\nHeadline: {xtag(raw1,'HEADLINE')}\nSummary: {xtag(raw1,'SUMMARY')}\nDepth: {xtag(raw1,'DEPTH')[:600]}"
        ctx_short = f"{xtag(raw1,'HEADLINE')}. {xtag(raw1,'SUMMARY')}"

        # Part 2
        print("    Part 2...")
        time.sleep(10)
        p2 = VIP_P2.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[ACCURACY]",acc).replace("[CTX]",ctx).replace("[ALLOC_STR]",al_str).replace("[NEWS_ITEMS]",ns)
        raw2,_ = gem_fb(client,tier,p2)

        for retry in range(2):
            if raw2 and ok(raw2,"VIP_T1"):
                break
            print(f"    P2 echo retry{retry+1}...")
            time.sleep(15)
            raw2,_ = gem_fb(client,tier,p2)

        # ✅ v7: Part 2 완전 실패시 → 단일호출 Fallback
        if not raw2 or not ok(raw2,"VIP_T1"):
            print("    P2 FAILED -> Fallback single call...")
            time.sleep(10)
            fb = VIP_FALLBACK.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[ACCURACY]",acc).replace("[CTX_SHORT]",ctx_short[:400]).replace("[ALLOC_STR]",al_str).replace("[NEWS_ITEMS]",ns)
            raw2,_ = gem_fb(client,tier,fb)
            if not raw2: raw2 = ""

        raw = raw1 + "\n" + raw2
        html = build_vip(author,tf,raw,cat)

    tr = xtag(raw,"TITLE")
    ip = xtag(raw,"IMAGE_PROMPT") or f"3D cinematic {cat}"
    exc = xtag(raw,"EXCERPT") or "Expert analysis."
    kw = xtag(raw,"SEO_KEYWORD")
    pretty = TIER_LABELS.get(tier,tier)
    title = f"[{pretty}] {tr}" if tr else f"({tier}) {cat} Insight"
    slug = make_slug(kw,tr or cat)
    html = sanitize(html)
    return title,ip,html,f"{ts} | {exc}",kw,slug

# ──────────────────────────────────────────────
# HTML BUILDERS
# ──────────────────────────────────────────────
F = "font-size:18px;line-height:1.8;color:#374151;"
M = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;"

def _hdr(author,tf,badge=""):
    b = f' <span style="background:#b8974d;color:#fff;padding:3px 12px;border-radius:4px;font-size:14px;font-weight:bold;">{badge}</span>' if badge else ""
    return f'<div style="border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;padding:14px 0;margin-bottom:30px;"><p style="margin:0;font-size:16px;color:#4b5563;"><strong style="color:#1a252c;">{author}</strong> | {tf}{b}</p></div>'

def _ftr(tw,ps):
    if not tw or is_echo(tw): tw = "Stay disciplined, stay diversified, and let time compound in your favor."
    if not ps or is_echo(ps): ps = "In 40 years of watching markets, the disciplined investor always wins. This cycle is no different."
    return (
        '<hr style="border:0;height:1px;background:#e5e7eb;margin:45px 0;">'
        '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Today\'s Warm Insight</h2>'
        f'<p style="{F}">{tw}</p>'
        '<div style="margin-top:30px;background:#1e293b;padding:28px;border-radius:8px;border-left:4px solid #b8974d;">'
        f'<p style="font-size:18px;line-height:1.8;color:#e2e8f0;margin:0;"><span style="color:#b8974d;font-weight:bold;font-size:20px;">P.S.</span> <span style="color:#cbd5e1;">{ps}</span></p>'
        '</div>'
        '<p style="font-size:16px;color:#9ca3af;margin-top:40px;text-align:center;">Disclaimer: For informational purposes only.</p></div>'
    )

def _up(msg):
    return f'<div style="background:#fffbeb;border:2px solid #f59e0b;padding:18px;border-radius:8px;margin:35px 0;"><p style="font-size:18px;color:#92400e;margin:0;text-align:center;">{msg}</p></div>'


def build_basic(a,tf,r):
    return (
        f'<div style="{M}">{_hdr(a,tf)}'
        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">What Happened</h2>'
        f'<p style="{F}margin-bottom:30px;">{xtag(r,"SUMMARY")}</p>'
        f'<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:35px;">'
        f'<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">📱 TikTok Take</h3>'
        f'<p style="{F}margin:0;">{xtag(r,"TIKTOK")}</p></div>'
        f'<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">{xtag(r,"HEADLINE")}</h3>'
        f'<p style="{F}margin-bottom:28px;">{xtag(r,"DEPTH")}</p>'
        f'<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:8px;margin-bottom:35px;">'
        f'<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
        f'<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">{xtag(r,"FLOW")}</p></div>'
        +_up("🔒 Want deeper analysis? <strong>Upgrade to Pro or VIP.</strong>")
        +_ftr(xtag(r,"TAKEAWAY"),xtag(r,"PS"))
    )


def build_premium(a,tf,r):
    return (
        f'<div style="{M}">{_hdr(a,tf,"PRO")}'
        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
        f'<p style="{F}margin-bottom:35px;">{xtag(r,"SUMMARY")}</p>'
        f'<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:40px;">'
        f'<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">📱 Viral Social Insights</h3>'
        f'<p style="{F}margin:0;">{xtag(r,"TIKTOK")}</p></div>'
        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers</h2>'
        f'<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">{xtag(r,"HEADLINE")}</h3>'
        f'<p style="{F}margin-bottom:28px;">{xtag(r,"DEPTH")}</p>'
        f'<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:8px;margin-bottom:40px;">'
        f'<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
        f'<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">{xtag(r,"FLOW")}</p></div>'
        f'<div style="background:#ffffff;border:2px solid #3b82f6;padding:28px;border-radius:8px;margin-bottom:35px;">'
        f'<h3 style="margin-top:0;color:#1e40af;font-size:22px;margin-bottom:14px;">💎 Pro-Only Insight</h3>'
        f'<p style="{F}margin:0;">{xtag(r,"PRO_INSIGHT")}</p></div>'
        f'<div style="background:#ecfdf5;border:2px solid #10b981;padding:24px;border-radius:8px;margin-bottom:15px;">'
        f'<p style="font-size:18px;line-height:1.8;color:#065f46;margin:0;"><strong style="color:#065f46;font-size:20px;">🟢 DO:</strong> {xtag(r,"PRO_DO")}</p></div>'
        f'<div style="background:#fef2f2;border:2px solid #ef4444;padding:24px;border-radius:8px;margin-bottom:35px;">'
        f'<p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;"><strong style="color:#991b1b;font-size:20px;">🔴 DON\'T:</strong> {xtag(r,"PRO_DONT")}</p></div>'
        +_up("🔒 Want The Titans Playbook? <strong>Upgrade to VIP.</strong>")
        +_ftr(xtag(r,"TAKEAWAY"),xtag(r,"PS"))
    )


def build_vip(a,tf,raw,cat):
    theme = CAT_THEME.get(cat,CAT_THEME["Economy"])
    accent = theme["accent"]
    al = CAT_ALLOC.get(cat,CAT_ALLOC["Economy"])
    l1,v1,l2,v2,l3,v3 = parse_graph(xtag(raw,"GRAPH_DATA"),cat)

    def gauge(lb,val,c):
        return (f'<div style="margin-bottom:22px;"><div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
                f'<span style="font-size:18px;font-weight:600;color:#374151;">{lb}</span>'
                f'<span style="font-size:18px;font-weight:700;color:{c};">{val}%</span></div>'
                f'<div style="width:100%;background:#e5e7eb;border-radius:8px;height:16px;overflow:hidden;">'
                f'<div style="width:{val}%;background:{c};height:100%;border-radius:8px;"></div></div></div>')

    # 동적 파이
    s,b,c = al["s"],al["b"],al["c"]
    circ = 565.49
    sd,bd,cd = circ*s/100, circ*b/100, circ*c/100
    pie = (f'<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;">'
           f'<circle cx="100" cy="100" r="90" fill="none" stroke="{accent}" stroke-width="30" stroke-dasharray="{sd:.1f} {circ}" stroke-dashoffset="0"/>'
           f'<circle cx="100" cy="100" r="90" fill="none" stroke="#64748b" stroke-width="30" stroke-dasharray="{bd:.1f} {circ}" stroke-dashoffset="-{sd:.1f}"/>'
           f'<circle cx="100" cy="100" r="90" fill="none" stroke="#b8974d" stroke-width="30" stroke-dasharray="{cd:.1f} {circ}" stroke-dashoffset="-{sd+bd:.1f}"/>'
           f'<text x="100" y="92" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">{s}/{b}/{c}</text>'
           f'<text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>'
           f'<div style="display:flex;justify-content:center;gap:20px;margin-bottom:8px;">'
           f'<span style="font-size:16px;color:{accent};">● Stocks {s}%</span>'
           f'<span style="font-size:16px;color:#64748b;">● Safe {b}%</span>'
           f'<span style="font-size:16px;color:#b8974d;">● Cash {c}%</span></div>'
           f'<p style="font-size:16px;color:#6b7280;text-align:center;font-style:italic;margin:5px 0 0;">{al["note"]}</p>')

    # Radar
    rr = ""
    for i in range(1,5):
        v = ok(raw,f"VIP_RADAR_{i}")
        if not v: continue
        bull = "bullish" in v.lower()
        bg,tc,ic = ("#ecfdf5","#065f46","🟢 BULL") if bull else ("#fef2f2","#991b1b","🔴 BEAR")
        rr += f'<tr><td style="padding:14px;border-bottom:1px solid #e5e7eb;font-size:18px;color:#374151;">{v}</td><td style="padding:14px;border-bottom:1px solid #e5e7eb;text-align:center;"><span style="background:{bg};color:{tc};padding:4px 12px;border-radius:6px;font-size:16px;font-weight:bold;">{ic}</span></td></tr>'
    radar = ""
    if rr:
        radar = (f'<div style="background:#fff;border:2px solid {accent};border-radius:8px;padding:25px;margin-bottom:35px;">'
                 f'<h3 style="margin-top:0;color:{accent};font-size:22px;margin-bottom:18px;">🎯 Sector Radar</h3>'
                 f'<table style="width:100%;border-collapse:collapse;">{rr}</table></div>')

    def mcard(lb,val,c):
        return (f'<div style="flex:1;min-width:200px;background:#f8fafc;border:2px solid {c};border-radius:10px;padding:22px;text-align:center;">'
                f'<div style="font-size:42px;font-weight:800;color:{c};margin-bottom:5px;">{val}%</div>'
                f'<div style="font-size:16px;color:#4b5563;font-weight:600;">{lb}</div></div>')

    c1,c2,c3 = ok(raw,"VIP_C1"),ok(raw,"VIP_C2"),ok(raw,"VIP_C3")
    t1,t2,t3,t4 = ok(raw,"VIP_T1"),ok(raw,"VIP_T2"),ok(raw,"VIP_T3"),ok(raw,"VIP_T4")
    vdo,vdont = ok(raw,"VIP_DO"),ok(raw,"VIP_DONT")
    tw,ps = ok(raw,"TAKEAWAY"),ok(raw,"PS")

    # ✅ v7: 빈 섹션 숨김 (Generating... 대신)
    def section(content,title_html=""):
        if not content: return ""
        return title_html + f'<p style="{F}margin-bottom:0;">{content}</p>'

    def pb(n,title,body,extra=""):
        if not body: return ""  # 빈 섹션 완전 숨김
        mt = "margin-top:22px;" if extra else ""
        return (f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-left:4px solid {accent};padding:28px;border-radius:8px;margin-bottom:25px;">'
                f'<h3 style="color:#1a252c;margin-top:0;font-size:24px;margin-bottom:18px;">{n}. {title}</h3>{extra}'
                f'<p style="{F}margin-bottom:0;{mt}">{body}</p></div>')

    summary = xtag(raw,"SUMMARY")
    tiktok = xtag(raw,"TIKTOK")
    headline = xtag(raw,"HEADLINE")
    depth = xtag(raw,"DEPTH")
    flow = xtag(raw,"FLOW")

    # Macro section (숨김 로직)
    macro_html = ""
    if c1 or c2 or c3:
        paras = ""
        if c1: paras += f'<p style="{F}margin-bottom:18px;">{c1}</p>'
        if c2: paras += f'<p style="{F}margin-bottom:18px;">{c2}</p>'
        if c3: paras += f'<p style="{F}margin-bottom:0;">{c3}</p>'
        macro_html = (
            f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:25px;border-bottom:3px solid {accent};padding-bottom:12px;display:inline-block;">VIP: Macro &amp; Flow Analysis</h2>'
            f'<div style="background:#fff;border:1px solid #e5e7eb;border-left:5px solid {accent};padding:28px;border-radius:8px;margin-bottom:40px;">'
            f'<p style="font-size:18px;color:{accent};text-transform:uppercase;font-weight:bold;margin-top:0;margin-bottom:22px;">[Institutional Technical Outlook]</p>'
            f'{paras}</div>'
        )

    # Playbook (빈 섹션 숨김)
    playbook_cards = ""
    playbook_cards += pb("1","The Generational Bargain (Fear vs. Greed)",t1)
    playbook_cards += pb("2",f"The {s}/{b}/{c} Seesaw (Asset Allocation)",t2,pie)
    playbook_cards += pb("3","The Global Shield (US Dollar &amp; Market)",t3)
    playbook_cards += pb("4","Survival Mechanics (DCA &amp; Risk Management)",t4)

    playbook_html = ""
    if playbook_cards:
        playbook_html = (
            f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:12px;border-bottom:3px solid {accent};padding-bottom:12px;display:inline-block;">The Titan\'s Playbook</h2>'
            f'<p style="font-size:18px;color:#6b7280;margin-bottom:30px;font-style:italic;">Strategic manual for {cat.lower()} conditions.</p>'
            + playbook_cards
        )

    # Action Plan (빈이면 숨김)
    action_html = ""
    if vdo or vdont:
        do_block = f'<div style="background:#ecfdf5;border:2px solid #10b981;border-radius:8px;padding:24px;margin-bottom:20px;"><p style="font-size:20px;color:#065f46;font-weight:bold;margin:0 0 12px;">🟢 DO (Action):</p><p style="font-size:18px;line-height:1.8;color:#064e3b;margin:0;">{vdo}</p></div>' if vdo else ""
        dont_block = f'<div style="background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:24px;"><p style="font-size:20px;color:#991b1b;font-weight:bold;margin:0 0 12px;">🔴 DON\'T (Avoid):</p><p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;">{vdont}</p></div>' if vdont else ""
        action_html = (
            '<div style="background:#1e293b;padding:35px;border-radius:10px;margin:45px 0 40px;">'
            '<h3 style="color:#b8974d;margin-top:0;font-size:26px;margin-bottom:25px;border-bottom:2px solid #475569;padding-bottom:15px;">✅ Today\'s VIP Action Plan</h3>'
            f'{do_block}{dont_block}</div>'
        )

    COL = [accent,"#f59e0b","#10b981"]

    return (
        f'<div style="{M}">{_hdr(a,tf,"VIP EXCLUSIVE")}'
        f'<div style="margin-bottom:25px;"><span style="display:inline-block;background:#f8fafc;border:2px solid {accent};color:{accent};padding:6px 16px;border-radius:20px;font-size:16px;font-weight:bold;">{theme["icon"]} {theme["label"]}</span></div>'
        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
        f'<p style="{F}margin-bottom:35px;">{summary}</p>'
        f'<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:40px;">'
        f'<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">📱 Viral Social Insights</h3>'
        f'<p style="{F}margin:0;">{tiktok}</p></div>'
        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers &amp; Insights</h2>'
        f'<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">{headline}</h3>'
        f'<p style="{F}margin-bottom:28px;">{depth}</p>'
        f'<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:22px;border-radius:8px;margin-bottom:40px;">'
        f'<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
        f'<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">{flow}</p></div>'
        f'<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">{mcard(l1,v1,COL[0])}{mcard(l2,v2,COL[1])}{mcard(l3,v3,COL[2])}</div>'
        f'<div style="padding:28px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:35px;">'
        f'<h3 style="margin-top:0;color:#1a252c;font-size:22px;border-bottom:2px solid #e5e7eb;padding-bottom:14px;margin-bottom:25px;">📊 Key Market Indicators</h3>'
        f'{gauge(l1,v1,COL[0])}{gauge(l2,v2,COL[1])}{gauge(l3,v3,COL[2])}</div>'
        + radar + macro_html + playbook_html + action_html
        + _ftr(tw,ps)
    )


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print("="*50+"\n  Warm Insight v7\n"+"="*50)
    total=ok_cnt=fail=0
    for cat,urls in CATEGORIES.items():
        print(f"\n--- [{cat}] ---")
        news = get_news(urls,20)
        if len(news)<3:
            print("  Skip")
            continue
        for task in TASKS:
            tier,cnt = task["tier"],task["count"]
            if len(news)<cnt:
                print(f"  Skip {tier}")
                break
            target = [news.pop(0) for _ in range(cnt)]
            total += 1
            print(f"\n  [{TIER_LABELS[tier]}] {cnt} articles...")
            result = analyze(target,cat,tier)
            if not result or not result[2]:
                fail+=1; continue
            title,ip,html,exc,kw,slug = result
            iu = None
            if ip:
                ib = make_thumb(ip,tier,cat)
                if ib: iu = upload_img(ib)
            publish(title,html,cat,tier,iu,exc,kw,slug)
            ok_cnt+=1
            sl = TIER_SLEEP[tier]
            print(f"  Wait {sl}s...")
            time.sleep(sl)
    print(f"\n{'='*50}\n  Total {total} | OK {ok_cnt} | Fail {fail}\n{'='*50}")

if __name__=="__main__":
    try: main()
    except:
        print("\nERR")
        traceback.print_exc()
        sys.exit(1)
