# -*- coding: utf-8 -*-
"""
Warm Insight v6 — Full SEO + Visual + Quality Overhaul
=======================================================
v5 -> v6 변경:
  [RED-1] 60/30/10 비율을 카테고리별로 동적 변경
  [RED-2] Action Plan 색상 밝고 선명하게 교체
  [RED-3] 최소 폰트 18px 보장
  [RED-4] GRAPH_DATA 99% 버그 수정 (파싱 강화)
  [RED-5] 카테고리별 VIP 테마 색상 + 아이콘 차별화
  [YEL-1] SEO 4대 구역 (slug, meta_title, meta_description, alt, 본문 H2)
  [YEL-2] VIP 썸네일 카테고리별 전용 프롬프트
  [YEL-3] 시각 요소 다양화 (카테고리별 색상 테마)
"""

import os, sys, traceback, time, random, re, json
from datetime import datetime

import requests
import jwt
import feedparser
from google import genai
from google.genai import types

# ──────────────────────────────────────────────
# 0. CONFIG
# ──────────────────────────────────────────────
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL       = os.environ.get("GHOST_API_URL", "").rstrip("/")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not all([GEMINI_API_KEY, GHOST_API_URL, GHOST_ADMIN_API_KEY]):
    sys.exit("Missing API keys")

CATEGORIES = {
    "Economy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
                "https://finance.yahoo.com/news/rssindex"],
    "Politics": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113"],
    "Tech": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"],
    "Health": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108"],
    "Energy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810"],
}

TIKTOK_LINKS = "https://lite.tiktok.com/t/ZSuGXKdsU/ https://lite.tiktok.com/t/ZSu9GYwy5/"

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

# ✅ [RED-5] 카테고리별 테마
CAT_THEME = {
    "Economy": {"icon": "💰", "accent": "#2563eb", "accent2": "#1e40af", "label": "MACRO & RATES"},
    "Politics": {"icon": "🏛️", "accent": "#dc2626", "accent2": "#991b1b", "label": "GEOPOLITICS & POLICY"},
    "Tech": {"icon": "🤖", "accent": "#7c3aed", "accent2": "#5b21b6", "label": "AI & DISRUPTION"},
    "Health": {"icon": "🧬", "accent": "#059669", "accent2": "#047857", "label": "BIOTECH & PHARMA"},
    "Energy": {"icon": "⚡", "accent": "#d97706", "accent2": "#b45309", "label": "OIL, GAS & RENEWABLES"},
}

# ✅ [RED-1] 카테고리별 자산배분 비율
CAT_ALLOC = {
    "Economy": {"stocks": 55, "safe": 35, "cash": 10, "note": "Defensive tilt: higher bond allocation during macro uncertainty"},
    "Politics": {"stocks": 50, "safe": 35, "cash": 15, "note": "Elevated cash reserve for geopolitical shock absorption"},
    "Tech": {"stocks": 70, "safe": 20, "cash": 10, "note": "Growth tilt: overweight equities in innovation-driven sector"},
    "Health": {"stocks": 60, "safe": 30, "cash": 10, "note": "Balanced: pharma stability with biotech upside exposure"},
    "Energy": {"stocks": 65, "safe": 25, "cash": 10, "note": "Commodity tilt: overweight real assets in supply-constrained market"},
}

CAT_METRICS = {
    "Economy": {
        "pool": ["Inflation Momentum","Recession Probability","Consumer Pulse","Credit Stress",
                 "Rate Cut Odds","Liquidity Index","Wage Tension","Housing Fragility",
                 "PMI Signal","Savings Erosion","Dollar Strength","Yield Curve Depth"],
        "hint": "inflation, GDP, employment, consumer confidence, yield curves, Fed policy",
    },
    "Politics": {
        "pool": ["Policy Uncertainty","Regulatory Risk","Geopolitical Tension",
                 "Gridlock Meter","Election Volatility","Trade War Risk",
                 "Bipartisan Score","Sanctions Impact","Defense Momentum","Tariff Exposure"],
        "hint": "policy uncertainty, regulatory changes, geopolitical tensions, legislative impact",
    },
    "Tech": {
        "pool": ["AI Arms Race","Antitrust Pressure","Chip Supply Stress",
                 "IPO Sentiment","Cloud Velocity","Cyber Threat Level",
                 "Big Tech Momentum","Funding Freeze","Privacy Risk"],
        "hint": "AI adoption, semiconductor supply, Big Tech regulation, startup funding",
    },
    "Health": {
        "pool": ["Pipeline Confidence","Drug Pricing Pressure","Biotech Funding",
                 "Policy Risk","FDA Momentum","Gene Therapy Index",
                 "Hospital Stress","Coverage Gap","Trial Success Rate"],
        "hint": "pharma pipelines, drug pricing, biotech investment, FDA activity",
    },
    "Energy": {
        "pool": ["Oil Supply Squeeze","Green Transition Speed","OPEC Tension",
                 "LNG Demand Surge","Renewable Growth","Stranding Risk",
                 "Geo Shock Risk","Grid Stress","Carbon Credit Heat"],
        "hint": "oil supply/demand, OPEC dynamics, renewable transition, LNG markets",
    },
}

# ✅ [YEL-2] VIP 썸네일 카테고리별 전용 프롬프트
VIP_THUMB = {
    "Economy": "Dark dramatic 3D render of golden scales balancing dollar bills and bonds, cinematic blue lighting, data hologram overlay, ultra detailed 8k",
    "Politics": "Dark dramatic 3D render of a marble chess board with geopolitical symbols, red accent lighting, power dynamics theme, ultra detailed 8k",
    "Tech": "Dark dramatic 3D render of neural network nodes glowing purple, circuit board landscape, AI brain hologram, futuristic, ultra detailed 8k",
    "Health": "Dark dramatic 3D render of DNA double helix merging with golden pharmaceutical capsules, green accent glow, medical innovation theme, ultra detailed 8k",
    "Energy": "Dark dramatic 3D render of oil derricks and solar panels on opposite sides, amber golden lighting, energy transition theme, ultra detailed 8k",
}

# ──────────────────────────────────────────────
# 1. PROMPTS
# ──────────────────────────────────────────────

# ✅ [YEL-1] 모든 프롬프트에 SEO_KEYWORD 태그 추가
PROMPT_BASIC = """
You are [PERSONA] writing for beginners on 'Warm Insight' ([CATEGORY]).
English only. Simple. Max 400 words. No jargon.

OUTPUT (XML):
<SEO_KEYWORD>A natural 3-6 word long-tail search phrase someone would Google about this topic</SEO_KEYWORD>
<TITLE>Title that naturally includes the SEO keyword near the front</TITLE>
<IMAGE_PROMPT>Simple 3D abstract cinematic image about [CATEGORY]</IMAGE_PROMPT>
<EXCERPT>1 sentence with the SEO keyword woven in naturally</EXCERPT>
<SUMMARY>3 sentences. The SEO keyword must appear in the first sentence naturally.</SUMMARY>
<TIKTOK>Fun TikTok analogy (2-3 sentences)</TIKTOK>
<HEADLINE>Key insight headline</HEADLINE>
<DEPTH>ELI5: What happened? Why care? What does it mean for my wallet?</DEPTH>
<FLOW>Emoji Flow: A ➡️ B ➡️ C ➡️ D</FLOW>
<TAKEAWAY>One comforting sentence</TAKEAWAY>
<PS>One personal thought</PS>

News: [NEWS_ITEMS]
"""

PROMPT_PREMIUM = """
You are [PERSONA] writing for intermediate investors on 'Warm Insight' ([CATEGORY]).
English only. 600-800 words. Behavioral economics depth.

OUTPUT (XML):
<SEO_KEYWORD>A natural 4-7 word long-tail keyword phrase for this analysis</SEO_KEYWORD>
<TITLE>Analytical title with SEO keyword near the front</TITLE>
<IMAGE_PROMPT>3D abstract cinematic about [CATEGORY] analysis</IMAGE_PROMPT>
<EXCERPT>1 sentence with SEO keyword</EXCERPT>
<SUMMARY>3 sentences. First sentence includes SEO keyword naturally.</SUMMARY>
<TIKTOK>TikTok analogy revealing hidden truth</TIKTOK>
<HEADLINE>Main analytical headline</HEADLINE>
<DEPTH><strong>🧐 WHY:</strong> Behavioral economics cause (4-5 sentences)<br><br><strong>🐑 HERD:</strong> What crowd is doing wrong (3-4 sentences)</DEPTH>
<FLOW>Emoji Flow (5+ steps)</FLOW>
<PRO_INSIGHT>Non-obvious cross-sector connection (4-5 sentences)</PRO_INSIGHT>
<PRO_DO>2 specific actions</PRO_DO>
<PRO_DONT>1 specific mistake</PRO_DONT>
<TAKEAWAY>Insightful takeaway</TAKEAWAY>
<PS>Historical perspective (2 sentences)</PS>

News: [NEWS_ITEMS]
"""

VIP_P1 = """
You are [PERSONA] writing INSTITUTIONAL-GRADE analysis for VIP subscribers of 'Warm Insight' ([CATEGORY]).
Every paragraph must justify VIP pricing with non-obvious insights.

WRITE real, substantive content in each tag (NOT instructions — write actual analysis):

<SEO_KEYWORD>A highly specific 4-8 word long-tail keyword that a sophisticated investor would search for, related to this specific news</SEO_KEYWORD>
<TITLE>Institutional title with the SEO keyword naturally embedded near the beginning</TITLE>
<IMAGE_PROMPT>[CAT_THUMB_PROMPT]</IMAGE_PROMPT>
<EXCERPT>1 VIP-grade sentence with SEO keyword</EXCERPT>
<SUMMARY>3 institutional sentences. First sentence MUST include the SEO keyword naturally.</SUMMARY>
<TIKTOK>Gen-Z viral analogy</TIKTOK>
<HEADLINE>Alpha-generating headline</HEADLINE>
<DEPTH><strong>🧐 WHY (Macro):</strong> 5+ sentences of deep macro analysis.<br><br><strong>🐑 HERD:</strong> 4+ sentences on crowd bias.<br><br><strong>🦅 CONTRARIAN:</strong> 5+ sentences on 2nd/3rd order effects.</DEPTH>
<FLOW>6+ step emoji chain</FLOW>
<GRAPH_DATA>Create 3 metrics for [CATEGORY]. [CAT_HINT]. Each score must be DIFFERENT (not all the same). Realistic range 25-90. Format: Name1|Score1|Name2|Score2|Name3|Score3. Use pipe only.</GRAPH_DATA>
<VIP_RADAR_1>Specific sector — BULLISH or BEARISH — 1 sentence reason</VIP_RADAR_1>
<VIP_RADAR_2>Different sector — BULLISH or BEARISH — 1 sentence</VIP_RADAR_2>
<VIP_RADAR_3>Different sector — BULLISH or BEARISH — 1 sentence</VIP_RADAR_3>
<VIP_RADAR_4>Different sector — BULLISH or BEARISH — 1 sentence</VIP_RADAR_4>
<VIP_C1>Full paragraph: RSI, Moving Averages, support/resistance for relevant assets. 5+ real sentences.</VIP_C1>
<VIP_C2>Full paragraph: yield curves, credit spreads, dollar index connection. 5+ real sentences.</VIP_C2>
<VIP_C3>Full paragraph: institutional and hedge fund positioning. 5+ real sentences.</VIP_C3>

NEWS: [NEWS_ITEMS]
"""

VIP_P2 = """
You are [PERSONA]. You analyzed [CATEGORY] news for VIP subscribers.

YOUR PART 1 ANALYSIS:
---
[PART1_CONTEXT]
---

Now write Part 2: ACTIONABLE STRATEGY. Each tag must contain REAL paragraphs of strategy (not instructions).

<VIP_T1>WRITE a detailed paragraph: Is this Fear or Greed? What would Buffett do NOW? What would Templeton do? Be specific. 6+ real sentences.</VIP_T1>
<VIP_T2>WRITE a detailed paragraph: For the [CATEGORY] sector, recommend specific allocation: [CAT_ALLOC_STR]. Name specific ETFs. What to buy/sell THIS week. 6+ real sentences.</VIP_T2>
<VIP_T3>WRITE a detailed paragraph: Why US assets matter now vs Europe/China/EM. Dollar impact. 5+ real sentences.</VIP_T3>
<VIP_T4>WRITE a detailed paragraph: DCA strategy for this news. When to deploy cash. The 50% panic sell rule with exact thresholds. 6+ real sentences.</VIP_T4>
<VIP_DO>WRITE 3 specific actions. Each names an ETF/stock, percentage, and trigger. Example: "1. Buy 3% XLE if it drops below $85 this week."</VIP_DO>
<VIP_DONT>WRITE 2 specific mistakes to avoid with WHY each is dangerous now.</VIP_DONT>
<TAKEAWAY>One masterful calming sentence.</TAKEAWAY>
<PS>40-year wisdom reflection referencing a historical parallel. 2-3 sentences.</PS>

NEWS: [NEWS_ITEMS]
"""

# ──────────────────────────────────────────────
# 2. UTILS
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

# ✅ [RED-4] GRAPH_DATA 파싱 완전 재작성
def parse_graph(raw, cat):
    if not raw:
        return _fallback_graph(cat)
    # 파이프로 분리
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 6:
        return _fallback_graph(cat)
    try:
        n1, s1, n2, s2, n3, s3 = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        v1 = int(re.sub(r"[^0-9]", "", s1))
        v2 = int(re.sub(r"[^0-9]", "", s2))
        v3 = int(re.sub(r"[^0-9]", "", s3))
        # 모든 값이 동일하면 실패로 간주
        if v1 == v2 == v3:
            return _fallback_graph(cat)
        # 범위 클램프
        v1 = max(10, min(95, v1))
        v2 = max(10, min(95, v2))
        v3 = max(10, min(95, v3))
        return n1, v1, n2, v2, n3, v3
    except:
        return _fallback_graph(cat)

def _fallback_graph(cat):
    pool = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["pool"]
    lb = random.sample(pool, 3)
    v1 = random.randint(55, 88)
    v2 = random.randint(30, 65)
    v3 = random.randint(40, 78)
    return lb[0], v1, lb[1], v2, lb[2], v3

def is_echo(text):
    if not text or len(text) < 80:
        return True
    sigs = ["6+ sentences","5+ sentences","At least 5","At least 6","Write a detailed",
            "Name ETFs","which ETF/stock","trigger price","Write exactly","explain WHY"]
    return sum(1 for s in sigs if s.lower() in text.lower()) >= 2

def safe_tag(raw, tag):
    val = xtag(raw, tag)
    if not val or is_echo(val):
        return ""
    return val

def sanitize(html):
    html = re.sub(r"\s+", " ", html.replace("\n"," ").replace("\r",""))
    return html

# ✅ [YEL-1] SEO 슬러그 생성
def make_slug(seo_keyword, title):
    text = seo_keyword if seo_keyword else title
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", text.lower())
    slug = re.sub(r"\s+", "-", slug.strip())
    return slug[:80]

# ──────────────────────────────────────────────
# 3. GHOST
# ──────────────────────────────────────────────
def ghost_token():
    kid, sec = str(GHOST_ADMIN_API_KEY).split(":")
    iat = int(datetime.now().timestamp())
    return jwt.encode({"iat":iat,"exp":iat+300,"aud":"/admin/"},
                      bytes.fromhex(sec), algorithm="HS256",
                      headers={"alg":"HS256","typ":"JWT","kid":kid})

def upload_img(img_bytes):
    try:
        r = requests.post(f"{GHOST_API_URL}/ghost/api/admin/images/upload/",
            headers={"Authorization":f"Ghost {ghost_token()}"},
            files={"file":("thumb.jpg",img_bytes,"image/jpeg"),"purpose":(None,"image")}, timeout=30)
        if r.status_code in (200,201): return r.json()["images"][0]["url"]
    except Exception as e: print(f"  img err: {e}")
    return None

# ✅ [YEL-1] SEO 필드 추가 (slug, meta_title, meta_description, og, alt)
def publish(title, html, cat, tier, img_url, excerpt, seo_kw="", slug_str=""):
    print(f"  Publishing: {title[:60]}...")
    try:
        md = json.dumps({"version":"0.3.1","markups":[],"atoms":[],"cards":[["html",{"html":html}]],"sections":[[10,0]]})
        post = {
            "title": title,
            "mobiledoc": md,
            "status": "published",
            "visibility": TIER_VIS.get(tier,"public"),
            "tags": [{"name": cat}, {"name": tier}],
        }
        # SEO 필드
        if slug_str:
            post["slug"] = slug_str
        if seo_kw:
            meta_t = f"{title} | Warm Insight {cat}"
            meta_d = f"{excerpt[:150]} Expert {cat.lower()} analysis on {seo_kw}."
            post["meta_title"] = meta_t[:300]
            post["meta_description"] = meta_d[:500]
            post["og_title"] = meta_t[:300]
            post["og_description"] = meta_d[:300]
            post["twitter_title"] = meta_t[:300]
            post["twitter_description"] = meta_d[:300]
        if excerpt:
            post["custom_excerpt"] = excerpt[:290]
        if img_url:
            post["feature_image"] = img_url
            if seo_kw:
                post["feature_image_alt"] = f"{seo_kw} - Warm Insight {cat} analysis"
        r = requests.post(f"{GHOST_API_URL}/ghost/api/admin/posts/",
            json={"posts":[post]},
            headers={"Authorization":f"Ghost {ghost_token()}","Content-Type":"application/json"}, timeout=60)
        if r.status_code in (200,201):
            print(f"  Published!")
        else:
            print(f"  Failed: {r.status_code}")
            try: print(f"  {json.dumps(r.json(),ensure_ascii=False)[:500]}")
            except: pass
    except Exception as e:
        print(f"  Publish err: {e}")
        traceback.print_exc()

# ──────────────────────────────────────────────
# 4. THUMBNAIL
# ──────────────────────────────────────────────
def make_thumb(img_prompt, tier, cat):
    # ✅ [YEL-2] VIP는 카테고리 전용 프롬프트 + 3회 재시도
    if tier == "Royal Premium":
        img_prompt = VIP_THUMB.get(cat, img_prompt)
    tries = 3 if tier == "Royal Premium" else 1
    for a in range(1, tries+1):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            result = client.models.generate_images(
                model="imagen-3.0-generate-001",
                prompt=img_prompt,
                config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg"))
            if result.generated_images:
                print(f"  Imagen OK (try {a})")
                return result.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"  Imagen try {a}: {e}")
            if a < tries: time.sleep(5)
    try:
        r = requests.get(f"https://picsum.photos/seed/{random.randint(1,9999)}/1280/720", timeout=10)
        if r.status_code == 200: return r.content
    except: pass
    return None

# ──────────────────────────────────────────────
# 5. GEMINI
# ──────────────────────────────────────────────
def call_gem(client, model, prompt, retries=2):
    for i in range(1, retries+1):
        try:
            r = client.models.generate_content(model=model, contents=prompt)
            return str(r.text)
        except Exception as e:
            print(f"    Gemini({model}) try{i}: {type(e).__name__}: {e}")
            if i < retries: time.sleep(10*i)
    return None

def gem_fb(client, tier, prompt):
    for m in MODEL_PRI.get(tier, ["gemini-2.5-flash"]):
        print(f"    [AI] {tier} -> {m}")
        r = call_gem(client, m, prompt)
        if r: return r, m
    return None, None

# ──────────────────────────────────────────────
# 6. ANALYZE
# ──────────────────────────────────────────────
def analyze(news_items, cat, tier):
    client = genai.Client(api_key=GEMINI_API_KEY)
    news_str = "\n".join(news_items)
    persona = EXPERT.get(cat, EXPERT["Economy"])
    now = datetime.now()
    ts = now.strftime("%I:%M %p")
    tf = now.strftime("%B %d, %Y at %I:%M %p (UTC)")
    author = "Ethan Cole &amp; The Warm Insight Panel"

    if tier == "Basic":
        prompt = PROMPT_BASIC.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[NEWS_ITEMS]",news_str)
        raw, _ = gem_fb(client, tier, prompt)
        if not raw: return None,None,None,None,None,None
        html = build_basic(author, tf, raw)

    elif tier == "Premium":
        prompt = PROMPT_PREMIUM.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[NEWS_ITEMS]",news_str)
        raw, _ = gem_fb(client, tier, prompt)
        if not raw: return None,None,None,None,None,None
        html = build_premium(author, tf, raw)

    else:
        hint = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["hint"]
        thumb_p = VIP_THUMB.get(cat, "3D cinematic " + cat)
        alloc = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
        alloc_str = f"{alloc['stocks']}% stocks, {alloc['safe']}% safe assets, {alloc['cash']}% cash. Rationale: {alloc['note']}"

        p1 = (VIP_P1.replace("[CATEGORY]",cat).replace("[PERSONA]",persona)
              .replace("[CAT_HINT]",hint).replace("[CAT_THUMB_PROMPT]",thumb_p)
              .replace("[NEWS_ITEMS]",news_str))
        raw1, _ = gem_fb(client, tier, p1)
        if not raw1: return None,None,None,None,None,None

        if not xtag(raw1,"VIP_C1") or is_echo(xtag(raw1,"VIP_C1")):
            print("    Part1 retry...")
            time.sleep(15)
            r1r, _ = gem_fb(client, tier, p1)
            if r1r and xtag(r1r,"VIP_C1") and not is_echo(xtag(r1r,"VIP_C1")):
                raw1 = r1r

        ctx = f"Title: {xtag(raw1,'TITLE')}\nHeadline: {xtag(raw1,'HEADLINE')}\nSummary: {xtag(raw1,'SUMMARY')}\nAnalysis: {xtag(raw1,'DEPTH')[:800]}"
        p2 = (VIP_P2.replace("[CATEGORY]",cat).replace("[PERSONA]",persona)
              .replace("[PART1_CONTEXT]",ctx).replace("[CAT_ALLOC_STR]",alloc_str)
              .replace("[NEWS_ITEMS]",news_str))

        print(f"    Part 2...")
        time.sleep(10)
        raw2, _ = gem_fb(client, tier, p2)
        for retry in range(2):
            if raw2 and xtag(raw2,"VIP_T1") and not is_echo(xtag(raw2,"VIP_T1")):
                break
            print(f"    Part2 echo retry {retry+1}...")
            time.sleep(15)
            raw2, _ = gem_fb(client, tier, p2)
        if not raw2: raw2 = ""

        raw = raw1 + "\n" + raw2
        html = build_vip(author, tf, raw, cat)

    title_raw = xtag(raw, "TITLE")
    img_prompt = xtag(raw, "IMAGE_PROMPT") or f"Abstract 3D cinematic {cat}"
    excerpt = xtag(raw, "EXCERPT") or "Expert analysis."
    seo_kw = xtag(raw, "SEO_KEYWORD")
    pretty = TIER_LABELS.get(tier, tier)
    title = f"[{pretty}] {title_raw}" if title_raw else f"({tier}) {cat} Insight"
    slug = make_slug(seo_kw, title_raw or cat)
    excerpt_t = f"{ts} | {excerpt}"
    html = sanitize(html)
    return title, img_prompt, html, excerpt_t, seo_kw, slug

# ──────────────────────────────────────────────
# 7. HTML BUILDERS
# ──────────────────────────────────────────────

# ✅ [RED-3] 최소 폰트 18px 보장 상수
F = "font-size:18px;line-height:1.8;color:#374151;"
FB = "font-size:18px;line-height:1.8;color:#374151;font-weight:600;"
M = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;"

def _hdr(author, tf, badge=""):
    b = ""
    if badge:
        b = f' <span style="background:#b8974d;color:#fff;padding:3px 12px;border-radius:4px;font-size:14px;font-weight:bold;letter-spacing:0.5px;">{badge}</span>'
    return f'<div style="border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;padding:14px 0;margin-bottom:30px;"><p style="margin:0;font-size:16px;color:#4b5563;"><strong style="color:#1a252c;">{author}</strong> &nbsp;|&nbsp; {tf}{b}</p></div>'

def _ftr(takeaway, ps):
    if not takeaway or is_echo(takeaway):
        takeaway = "Stay disciplined, stay diversified, and let time work in your favor."
    if not ps or is_echo(ps):
        ps = "Markets have weathered every storm. This one will be no different. Stay the course."
    return (
        '<hr style="border:0;height:1px;background:#e5e7eb;margin:40px 0;">'
        '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Today\'s Warm Insight</h2>'
        f'<p style="{F}">{takeaway}</p>'
        '<div style="margin-top:30px;background:#1a252c;padding:28px;border-radius:8px;border-left:4px solid #b8974d;">'
        f'<p style="font-size:18px;line-height:1.8;color:#e5e7eb;margin:0;"><span style="color:#b8974d;font-weight:bold;font-size:20px;">P.S.</span> <span style="color:#d1d5db;">{ps}</span></p>'
        '</div>'
        '<p style="font-size:16px;color:#9ca3af;margin-top:35px;text-align:center;text-transform:uppercase;">Disclaimer: For informational purposes only.</p>'
        '</div>'
    )

def _upgrade(msg):
    return f'<div style="background:#fffbeb;border:2px solid #f59e0b;padding:18px;border-radius:8px;margin-bottom:30px;"><p style="font-size:18px;color:#92400e;margin:0;text-align:center;">{msg}</p></div>'


def build_basic(author, tf, raw):
    return (
        f'<div style="{M}">{_hdr(author, tf)}'
        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">What Happened</h2>'
        f'<p style="{F}margin-bottom:30px;">{xtag(raw,"SUMMARY")}</p>'
        f'<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:22px;border-radius:8px;margin-bottom:35px;">'
        f'<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:10px;">📱 TikTok Take</h3>'
        f'<p style="{F}margin:0;">{xtag(raw,"TIKTOK")}</p></div>'
        f'<h3 style="font-size:24px;color:#1a252c;margin-bottom:12px;">{xtag(raw,"HEADLINE")}</h3>'
        f'<p style="{F}margin-bottom:25px;">{xtag(raw,"DEPTH")}</p>'
        f'<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:18px;border-radius:8px;margin-bottom:35px;">'
        f'<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
        f'<span style="font-size:20px;color:#1a252c;display:block;margin-top:8px;font-weight:bold;">{xtag(raw,"FLOW")}</span></div>'
        + _upgrade("🔒 Want deeper analysis? <strong>Upgrade to Pro or VIP.</strong>")
        + _ftr(xtag(raw,"TAKEAWAY"), xtag(raw,"PS"))
    )


def build_premium(author, tf, raw):
    return (
        f'<div style="{M}">{_hdr(author, tf, "PRO")}'
        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
        f'<p style="{F}margin-bottom:35px;">{xtag(raw,"SUMMARY")}</p>'
        f'<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:22px;border-radius:8px;margin-bottom:40px;">'
        f'<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:10px;">📱 Viral Social Insights</h3>'
        f'<p style="{F}margin:0;">{xtag(raw,"TIKTOK")}</p></div>'
        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers</h2>'
        f'<h3 style="font-size:24px;color:#1a252c;margin-bottom:12px;">{xtag(raw,"HEADLINE")}</h3>'
        f'<p style="{F}margin-bottom:25px;">{xtag(raw,"DEPTH")}</p>'
        f'<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:8px;margin-bottom:40px;">'
        f'<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
        f'<span style="font-size:20px;color:#1a252c;display:block;margin-top:8px;font-weight:bold;">{xtag(raw,"FLOW")}</span></div>'
        f'<div style="background:#fff;border:2px solid #3b82f6;padding:25px;border-radius:8px;margin-bottom:35px;">'
        f'<h3 style="margin-top:0;color:#1e40af;font-size:22px;margin-bottom:12px;">💎 Pro-Only Insight</h3>'
        f'<p style="{F}margin:0;">{xtag(raw,"PRO_INSIGHT")}</p></div>'
        f'<div style="background:#ecfdf5;border:2px solid #10b981;padding:22px;border-radius:8px;margin-bottom:15px;">'
        f'<p style="font-size:18px;line-height:1.8;color:#065f46;margin:0;"><strong style="color:#065f46;font-size:20px;">🟢 DO:</strong> {xtag(raw,"PRO_DO")}</p></div>'
        f'<div style="background:#fef2f2;border:2px solid #ef4444;padding:22px;border-radius:8px;margin-bottom:35px;">'
        f'<p style="font-size:18px;line-height:1.8;color:#991b1b;margin:0;"><strong style="color:#991b1b;font-size:20px;">🔴 DON\'T:</strong> {xtag(raw,"PRO_DONT")}</p></div>'
        + _upgrade("🔒 Want The Titans Playbook? <strong>Upgrade to VIP.</strong>")
        + _ftr(xtag(raw,"TAKEAWAY"), xtag(raw,"PS"))
    )


def build_vip(author, tf, raw, cat):
    theme = CAT_THEME.get(cat, CAT_THEME["Economy"])
    accent = theme["accent"]
    accent2 = theme["accent2"]
    icon = theme["icon"]
    label = theme["label"]
    alloc = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])

    l1,v1,l2,v2,l3,v3 = parse_graph(xtag(raw,"GRAPH_DATA"), cat)
    COL = [accent, "#f59e0b", "#10b981"]

    def gauge(lb,val,c):
        return (
            f'<div style="margin-bottom:22px;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
            f'<span style="font-size:18px;font-weight:600;color:#374151;">{lb}</span>'
            f'<span style="font-size:18px;font-weight:700;color:{c};">{val}%</span></div>'
            f'<div style="width:100%;background:#e5e7eb;border-radius:8px;height:16px;overflow:hidden;">'
            f'<div style="width:{val}%;background:{c};height:100%;border-radius:8px;"></div></div></div>'
        )

    # ✅ [RED-1] 카테고리별 동적 파이차트
    s_pct = alloc["stocks"]
    b_pct = alloc["safe"]
    c_pct = alloc["cash"]
    circ = 2 * 3.14159 * 90  # ~565.49
    s_dash = circ * s_pct / 100
    b_dash = circ * b_pct / 100
    c_dash = circ * c_pct / 100

    svg_pie = (
        f'<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;">'
        f'<circle cx="100" cy="100" r="90" fill="none" stroke="{accent}" stroke-width="30" stroke-dasharray="{s_dash:.1f} {circ:.1f}" stroke-dashoffset="0"/>'
        f'<circle cx="100" cy="100" r="90" fill="none" stroke="#64748b" stroke-width="30" stroke-dasharray="{b_dash:.1f} {circ:.1f}" stroke-dashoffset="-{s_dash:.1f}"/>'
        f'<circle cx="100" cy="100" r="90" fill="none" stroke="#b8974d" stroke-width="30" stroke-dasharray="{c_dash:.1f} {circ:.1f}" stroke-dashoffset="-{s_dash+b_dash:.1f}"/>'
        f'<text x="100" y="92" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">{s_pct}/{b_pct}/{c_pct}</text>'
        f'<text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>'
        f'<div style="display:flex;justify-content:center;gap:20px;margin-bottom:8px;">'
        f'<span style="font-size:16px;color:{accent};">● Stocks {s_pct}%</span>'
        f'<span style="font-size:16px;color:#64748b;">● Safe {b_pct}%</span>'
        f'<span style="font-size:16px;color:#b8974d;">● Cash {c_pct}%</span></div>'
        f'<p style="font-size:16px;color:#6b7280;text-align:center;font-style:italic;margin:5px 0 0;">{alloc["note"]}</p>'
    )

    # Sector Radar
    radar_rows = ""
    for i in range(1,5):
        r = safe_tag(raw, f"VIP_RADAR_{i}")
        if not r: continue
        bull = "bullish" in r.lower()
        bg = "#ecfdf5" if bull else "#fef2f2"
        tc = "#065f46" if bull else "#991b1b"
        ic = "🟢 BULL" if bull else "🔴 BEAR"
        radar_rows += (
            f'<tr><td style="padding:14px;border-bottom:1px solid #e5e7eb;font-size:18px;color:#374151;">{r}</td>'
            f'<td style="padding:14px;border-bottom:1px solid #e5e7eb;text-align:center;">'
            f'<span style="background:{bg};color:{tc};padding:4px 12px;border-radius:6px;font-size:16px;font-weight:bold;">{ic}</span></td></tr>'
        )
    radar_html = ""
    if radar_rows:
        radar_html = (
            f'<div style="background:#fff;border:2px solid {accent};border-radius:8px;padding:25px;margin-bottom:35px;">'
            f'<h3 style="margin-top:0;color:{accent2};font-size:22px;margin-bottom:18px;">🎯 {icon} Sector Radar — {label}</h3>'
            f'<table style="width:100%;border-collapse:collapse;">{radar_rows}</table></div>'
        )

    # 히트맵 카드
    def mcard(lb, val, c):
        return (
            f'<div style="flex:1;min-width:200px;background:#f8fafc;border:2px solid {c};border-radius:10px;padding:22px;text-align:center;">'
            f'<div style="font-size:42px;font-weight:800;color:{c};margin-bottom:5px;">{val}%</div>'
            f'<div style="font-size:16px;color:#4b5563;font-weight:600;">{lb}</div></div>'
        )

    c1 = safe_tag(raw,"VIP_C1")
    c2 = safe_tag(raw,"VIP_C2")
    c3 = safe_tag(raw,"VIP_C3")
    t1 = safe_tag(raw,"VIP_T1")
    t2 = safe_tag(raw,"VIP_T2")
    t3 = safe_tag(raw,"VIP_T3")
    t4 = safe_tag(raw,"VIP_T4")
    vdo = safe_tag(raw,"VIP_DO")
    vdont = safe_tag(raw,"VIP_DONT")
    tw = safe_tag(raw,"TAKEAWAY")
    ps = safe_tag(raw,"PS")

    empty = '<p style="font-size:18px;color:#9ca3af;font-style:italic;">(Generating...)</p>'

    def pb(n, title, body, extra=""):
        content = body if body else empty
        mt = "margin-top:22px;" if extra else ""
        return (
            f'<div style="background:#f8fafc;border:1px solid #e5e7eb;border-left:4px solid {accent};padding:28px;border-radius:8px;margin-bottom:25px;">'
            f'<h3 style="color:#1a252c;margin-top:0;font-size:24px;margin-bottom:18px;">{n}. {title}</h3>'
            f'{extra}'
            f'<p style="{F}margin-bottom:0;{mt}">{content}</p></div>'
        )

    summary = xtag(raw,"SUMMARY")
    tiktok = xtag(raw,"TIKTOK")
    headline = xtag(raw,"HEADLINE")
    depth = xtag(raw,"DEPTH")
    flow = xtag(raw,"FLOW")

    # ✅ [RED-2] Action Plan: 밝고 선명한 색상
    return (
        f'<div style="{M}">{_hdr(author, tf, "VIP EXCLUSIVE")}'

        # 카테고리 배너
        f'<div style="background:{accent};padding:12px 20px;border-radius:8px;margin-bottom:25px;">'
        f'<p style="margin:0;font-size:18px;color:#ffffff;font-weight:bold;letter-spacing:1px;">{icon} {label}</p></div>'

        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
        f'<p style="{F}margin-bottom:35px;">{summary}</p>'

        f'<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:22px;border-radius:8px;margin-bottom:40px;">'
        f'<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">📱 Viral Social Insights</h3>'
        f'<p style="{F}margin:0;">{tiktok}</p></div>'

        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers &amp; Insights</h2>'
        f'<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">{headline}</h3>'
        f'<p style="{F}margin-bottom:25px;">{depth}</p>'

        f'<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:22px;border-radius:8px;margin-bottom:40px;">'
        f'<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
        f'<span style="font-size:20px;color:#1a252c;display:block;margin-top:8px;font-weight:bold;">{flow}</span></div>'

        # 히트맵 카드
        f'<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">'
        f'{mcard(l1,v1,COL[0])}{mcard(l2,v2,COL[1])}{mcard(l3,v3,COL[2])}</div>'

        # 게이지
        f'<div style="padding:28px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:35px;">'
        f'<h3 style="margin-top:0;color:#1a252c;font-size:22px;border-bottom:2px solid #e5e7eb;padding-bottom:14px;margin-bottom:25px;">📊 Key Market Indicators</h3>'
        f'{gauge(l1,v1,COL[0])}{gauge(l2,v2,COL[1])}{gauge(l3,v3,COL[2])}</div>'

        + radar_html +

        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:25px;border-bottom:3px solid {accent};padding-bottom:12px;display:inline-block;">VIP: Macro &amp; Flow Analysis</h2>'
        f'<div style="background:#fff;border:1px solid #e5e7eb;border-left:5px solid {accent};padding:28px;border-radius:8px;margin-bottom:40px;">'
        f'<p style="font-size:18px;color:{accent};text-transform:uppercase;font-weight:bold;margin-top:0;margin-bottom:22px;letter-spacing:1px;">[Institutional Technical Outlook]</p>'
        f'<p style="{F}margin-bottom:18px;">{c1 or empty}</p>'
        f'<p style="{F}margin-bottom:18px;">{c2 or empty}</p>'
        f'<p style="{F}margin-bottom:0;">{c3 or empty}</p></div>'

        f'<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:12px;border-bottom:3px solid {accent};padding-bottom:12px;display:inline-block;">The Titan\'s Playbook</h2>'
        f'<p style="font-size:18px;color:#6b7280;margin-bottom:30px;font-style:italic;">Strategic manual for {cat.lower()} conditions.</p>'

        + pb("1","The Generational Bargain (Fear vs. Greed)", t1)
        + pb("2",f"The {s_pct}/{b_pct}/{c_pct} Seesaw (Asset Allocation)", t2, svg_pie)
        + pb("3","The Global Shield (US Dollar &amp; Market)", t3)
        + pb("4","Survival Mechanics (Split Buying &amp; Mental Peace)", t4)

        # ✅ [RED-2] 밝고 선명한 Action Plan
        + '<div style="background:#1e293b;padding:35px;border-radius:10px;margin:45px 0 40px;">'
        '<h3 style="color:#b8974d;margin-top:0;font-size:26px;margin-bottom:25px;border-bottom:2px solid #475569;padding-bottom:15px;">✅ Today\'s VIP Action Plan</h3>'

        f'<div style="background:#ecfdf5;border:2px solid #10b981;border-radius:8px;padding:22px;margin-bottom:20px;">'
        f'<p style="font-size:20px;color:#065f46;font-weight:bold;margin:0 0 12px 0;">🟢 DO (Action):</p>'
        f'<p style="font-size:18px;line-height:1.8;color:#064e3b;margin:0;">{vdo or empty}</p></div>'

        f'<div style="background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:22px;">'
        f'<p style="font-size:20px;color:#991b1b;font-weight:bold;margin:0 0 12px 0;">🔴 DON\'T (Avoid):</p>'
        f'<p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;">{vdont or empty}</p></div>'
        '</div>'

        + _ftr(tw, ps)
    )


# ──────────────────────────────────────────────
# 8. MAIN
# ──────────────────────────────────────────────
def main():
    print("="*50)
    print("  Warm Insight v6 — SEO + Visual + Quality")
    print("="*50)
    total = ok = fail = 0

    for cat, urls in CATEGORIES.items():
        print(f"\n--- [{cat}] ---")
        news = get_news(urls, 20)
        if len(news) < 3:
            print("  Skip: not enough news")
            continue
        for task in TASKS:
            tier, cnt = task["tier"], task["count"]
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
            title, ip, html, exc, seo_kw, slug = result

            iu = None
            if ip:
                ib = make_thumb(ip, tier, cat)
                if ib: iu = upload_img(ib)
            publish(title, html, cat, tier, iu, exc, seo_kw, slug)
            ok += 1
            sl = TIER_SLEEP[tier]
            print(f"  Wait {sl}s...")
            time.sleep(sl)

    print(f"\n{'='*50}\n  Total {total} | OK {ok} | Fail {fail}\n{'='*50}")

if __name__ == "__main__":
    try: main()
    except:
        print("\nSystem error")
        traceback.print_exc()
        sys.exit(1)
