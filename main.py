# -*- coding: utf-8 -*-
"""
Warm Insight v4 — Split-Call + Visual Upgrade
==============================================
v3 → v4 핵심 변경:
  1. VIP 생성을 2회 분할 호출 (토큰 한도 초과 방지)
  2. VIP 전용 인라인 SVG 시각 요소 (게이지, 파이차트, 히트맵 테이블)
  3. VIP 썸네일 차별화 (전용 프롬프트 + Imagen 재시도 3회)
  4. 빈 섹션 감지 → 자동 재시도 로직
  5. 모든 HTML에 명시적 color 속성 (Ghost 렌더링 호환)
"""

import os, sys, traceback, time, random, re, json
from datetime import datetime

import requests
import jwt
import feedparser
from google import genai
from google.genai import types

# ──────────────────────────────────────────────
# 0. 환경변수 & 상수
# ──────────────────────────────────────────────
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL       = os.environ.get("GHOST_API_URL", "").rstrip("/")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not all([GEMINI_API_KEY, GHOST_API_URL, GHOST_ADMIN_API_KEY]):
    print("⛔ API 키 또는 Ghost 출입증이 없습니다.")
    sys.exit(1)

CATEGORIES = {
    "Economy": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "https://finance.yahoo.com/news/rssindex",
    ],
    "Politics": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113",
    ],
    "Tech": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
    ],
    "Health": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108",
    ],
    "Energy": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810",
    ],
}

TIKTOK_LINKS = (
    "https://lite.tiktok.com/t/ZSuGXKdsU/ "
    "https://lite.tiktok.com/t/ZSu9GYwy5/ "
    "https://lite.tiktok.com/t/ZSuxhPSBR/ "
    "https://lite.tiktok.com/t/ZSuXQwnvm/"
)

TASKS = [
    {"tier": "Basic",         "count": 2},
    {"tier": "Premium",       "count": 3},
    {"tier": "Royal Premium", "count": 5},
]

TIER_LABELS  = {"Basic": "🌱 Free", "Premium": "💎 Pro", "Royal Premium": "👑 VIP"}
TIER_VIS     = {"Basic": "public", "Premium": "public", "Royal Premium": "public"}
TIER_SLEEP   = {"Basic": 15, "Premium": 30, "Royal Premium": 50}
MODEL_PRI    = {
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

CAT_METRICS = {
    "Economy": {
        "pool": ["Inflation Momentum","Recession Probability","Consumer Spending Pulse","Credit Market Stress",
                 "Rate Cut Expectation","Liquidity Squeeze Index","Wage Growth Tension","Housing Fragility",
                 "Manufacturing PMI Signal","Savings Rate Erosion","Dollar Strength Index","Yield Curve Depth"],
        "hint": "Focus on: inflation, GDP, employment, consumer confidence, yield curves, Fed policy.",
    },
    "Politics": {
        "pool": ["Policy Uncertainty Index","Regulatory Risk Score","Geopolitical Tension Level",
                 "Legislative Gridlock Meter","Election Volatility Index","Trade War Escalation Risk",
                 "Bipartisan Score","Sanctions Impact","Defense Spending Momentum","Tariff Exposure Index"],
        "hint": "Focus on: policy uncertainty, regulatory changes, geopolitical tensions, legislative impact.",
    },
    "Tech": {
        "pool": ["AI Arms Race Intensity","Antitrust Pressure","Semiconductor Supply Stress",
                 "Tech IPO Sentiment","Cloud Adoption Velocity","Cybersecurity Threat Level",
                 "Big Tech Earnings Momentum","Startup Funding Freeze","Data Privacy Risk Score"],
        "hint": "Focus on: AI adoption, semiconductor supply, Big Tech regulation, startup funding.",
    },
    "Health": {
        "pool": ["Pharma Pipeline Confidence","Drug Pricing Pressure","Biotech Funding Pulse",
                 "Healthcare Policy Risk","FDA Approval Momentum","Gene Therapy Index",
                 "Hospital System Stress","Insurance Coverage Gap","Clinical Trial Success Rate"],
        "hint": "Focus on: pharma pipelines, drug pricing, biotech investment, FDA activity.",
    },
    "Energy": {
        "pool": ["Crude Oil Supply Squeeze","Green Transition Velocity","OPEC Compliance Tension",
                 "LNG Demand Surge Index","Renewable Capacity Growth","Fossil Fuel Stranding Risk",
                 "Energy Geopolitical Shock Risk","Grid Reliability Stress","Carbon Credit Heat"],
        "hint": "Focus on: oil supply/demand, OPEC dynamics, renewable transition, LNG markets.",
    },
}

# ──────────────────────────────────────────────
# 1. 프롬프트 — 등급별 분리
# ──────────────────────────────────────────────

PROMPT_BASIC = """
[Goal] Write a SHORT friendly blog post in ENGLISH for '[CATEGORY]' on 'Warm Insight'.
Target: Free subscribers (beginners). You are [PERSONA] explaining to a 15-year-old.

RULES: English only. Simple. No jargon. Max 400 words. Use everyday analogies.

OUTPUT (STRICT XML):
<TITLE>Simple catchy title</TITLE>
<IMAGE_PROMPT>Simple prompt for 3D abstract cinematic image about [CATEGORY]</IMAGE_PROMPT>
<EXCERPT>1 sentence summary</EXCERPT>
<SUMMARY>3 sentences explaining like talking to a friend</SUMMARY>
<TIKTOK>Fun viral TikTok-style analogy (2-3 sentences)</TIKTOK>
<HEADLINE>One-line key insight</HEADLINE>
<DEPTH>ELI5: What happened? Why care? What does it mean for my wallet? (3-4 sentences)</DEPTH>
<FLOW>Simple Emoji Flow: Event 📰 ➡️ Effect 💰 ➡️ Your Life 🏠</FLOW>
<TAKEAWAY>One comforting actionable sentence</TAKEAWAY>
<PS>One short personal thought</PS>

News: [NEWS_ITEMS]
"""

PROMPT_PREMIUM = """
[Goal] Write an analytical blog post in ENGLISH for '[CATEGORY]' on 'Warm Insight'.
Target: Pro subscribers (intermediate investors). You are [PERSONA].

RULES: English only. Go deep with behavioral economics. 600-800 words.

OUTPUT (STRICT XML):
<TITLE>Analytical insight-driven title</TITLE>
<IMAGE_PROMPT>Prompt for 3D abstract cinematic image about [CATEGORY] analysis</IMAGE_PROMPT>
<EXCERPT>1 sentence key analytical insight</EXCERPT>
<SUMMARY>3 sentence executive summary with "so what"</SUMMARY>
<TIKTOK>Engaging TikTok analogy revealing hidden truth</TIKTOK>
<HEADLINE>Main analytical insight headline</HEADLINE>
<DEPTH><strong>🧐 WHY IT MATTERS:</strong> Deeper cause via behavioral economics. (4-5 sentences)<br><br><strong>🐑 HERD PSYCHOLOGY:</strong> What the crowd is doing wrong. (3-4 sentences)</DEPTH>
<FLOW>Detailed Emoji Flow (5+ steps)</FLOW>
<PRO_INSIGHT>Non-obvious cross-sector connection most miss. (4-5 sentences)</PRO_INSIGHT>
<PRO_DO>2 specific actionable steps</PRO_DO>
<PRO_DONT>1 specific mistake the herd is making</PRO_DONT>
<TAKEAWAY>Insightful actionable takeaway</TAKEAWAY>
<PS>Personal thought with historical perspective (2 sentences)</PS>

News: [NEWS_ITEMS]
"""

# ✅ v4: VIP를 2개의 프롬프트로 분할 (토큰 초과 방지)
VIP_PROMPT_PART1 = """
[Goal] Write an INSTITUTIONAL-GRADE blog post in ENGLISH for '[CATEGORY]' on 'Warm Insight'.
Target: VIP subscribers (sophisticated investors paying premium for alpha). You are [PERSONA].

RULES: English only. Every paragraph must contain a non-obvious insight. 800+ words.

OUTPUT (STRICT XML):
<TITLE>Institutional-grade compelling title</TITLE>
<IMAGE_PROMPT>Prompt for premium 3D cinematic image: dark dramatic lighting, gold accents, data visualization overlay, [CATEGORY] theme, ultra high quality</IMAGE_PROMPT>
<EXCERPT>1 sentence making VIPs feel they get exclusive intel</EXCERPT>
<SUMMARY>3 sentence institutional-depth summary</SUMMARY>
<TIKTOK>Super-engaging TikTok analogy Gen-Z would share</TIKTOK>
<HEADLINE>Alpha-generating insight headline</HEADLINE>
<DEPTH><strong>🧐 WHY (Macro):</strong> Deep macro analysis — global capital flows, central bank policy, structural trends. (5+ sentences)<br><br><strong>🐑 HERD BEHAVIOR:</strong> Crowd's cognitive bias. (4+ sentences)<br><br><strong>🦅 CONTRARIAN VIEW:</strong> What smart money sees — 2nd/3rd order consequences. (5+ sentences)</DEPTH>
<FLOW>Full cause-effect chain (6+ steps)</FLOW>
<GRAPH_DATA>Create 3 metrics UNIQUE to [CATEGORY]. [CAT_HINT] Format: Name1|Score1|Name2|Score2|Name3|Score3. Pipe only. No colons/hyphens in names.</GRAPH_DATA>
<VIP_RADAR_1>Sector/asset name — BULLISH or BEARISH — 1 sentence reason</VIP_RADAR_1>
<VIP_RADAR_2>Sector/asset name — BULLISH or BEARISH — 1 sentence reason</VIP_RADAR_2>
<VIP_RADAR_3>Sector/asset name — BULLISH or BEARISH — 1 sentence reason</VIP_RADAR_3>
<VIP_RADAR_4>Sector/asset name — BULLISH or BEARISH — 1 sentence reason</VIP_RADAR_4>
<VIP_C1>Technical Outlook: RSI, Moving Averages, support/resistance. 5+ sentences.</VIP_C1>
<VIP_C2>Macro Flow: Yield curves, credit spreads, dollar index. 5+ sentences.</VIP_C2>
<VIP_C3>Smart Money: Institutions, hedge funds, insider activity. 5+ sentences.</VIP_C3>

News: [NEWS_ITEMS]
"""

VIP_PROMPT_PART2 = """
[Context] You already wrote Part 1 of a VIP analysis about '[CATEGORY]' news. Now write Part 2: The Titan's Playbook and Action Plan.
You are [PERSONA]. Write with conviction and specificity.

RULES: English only. Be SPECIFIC — name ETFs, percentages, thresholds. Every paragraph must justify VIP pricing.

Part 1 summary for context: [PART1_SUMMARY]

OUTPUT (STRICT XML):
<VIP_T1>The Generational Bargain: Where are we in Fear/Greed cycle for THIS news? What would Buffett/Templeton do? Specific conviction. (6+ sentences)</VIP_T1>
<VIP_T2>60/30/10 Seesaw: Which specific assets in each bucket? How to rebalance THIS week? Name ETFs, percentages. (6+ sentences)</VIP_T2>
<VIP_T3>Global Shield: Why US assets matter now vs Europe/China/EM risk. Dollar impact. (5+ sentences)</VIP_T3>
<VIP_T4>Survival Mechanics: DCA strategy for THIS situation. When to deploy cash. 50% panic rule — exact trigger thresholds. (6+ sentences)</VIP_T4>
<VIP_DO>3 specific actions with exact details: which ETF/stock, what percentage, what trigger price or condition</VIP_DO>
<VIP_DONT>2 specific mistakes to avoid with explanation of WHY each is dangerous now</VIP_DONT>
<TAKEAWAY>Masterful calming insight giving VIP subscribers an unfair advantage feeling</TAKEAWAY>
<PS>Personal 40-year wisdom reflection — reference a specific historical parallel (2-3 sentences)</PS>

News: [NEWS_ITEMS]
"""

# ──────────────────────────────────────────────
# 2. 유틸
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
    LAZY = {"Sector Stress","Market Fear","Growth Outlook","Policy Risk"}
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) >= 6 and not ({parts[0], parts[2], parts[4]} & LAZY):
        try:
            return (parts[0], max(5,min(99,int(re.sub(r"\D","",parts[1])))),
                    parts[2], max(5,min(99,int(re.sub(r"\D","",parts[3])))),
                    parts[4], max(5,min(99,int(re.sub(r"\D","",parts[5])))))
        except: pass
    pool = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["pool"]
    lb = random.sample(pool, 3)
    return lb[0],random.randint(55,92),lb[1],random.randint(35,75),lb[2],random.randint(45,88)

def sanitize(html):
    html = re.sub(r"\s+", " ", html.replace("\n"," ").replace("\r",""))
    sz = len(html.encode("utf-8")) / 1024
    if sz > 500: print(f"  ⚠️ HTML {sz:.0f}KB")
    return html

# ──────────────────────────────────────────────
# 3. Ghost
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
    except Exception as e: print(f"  ❌ 이미지 업로드: {e}")
    return None

def publish(title, html, cat, tier, img_url, excerpt):
    print(f"  📝 발행: '{title[:60]}...'")
    try:
        md = json.dumps({"version":"0.3.1","markups":[],"atoms":[],"cards":[["html",{"html":html}]],"sections":[[10,0]]})
        post = {"title":title,"mobiledoc":md,"status":"published",
                "visibility":TIER_VIS.get(tier,"public"),"tags":[{"name":cat},{"name":tier}]}
        if excerpt: post["custom_excerpt"] = excerpt[:290]
        if img_url: post["feature_image"] = img_url
        r = requests.post(f"{GHOST_API_URL}/ghost/api/admin/posts/",
            json={"posts":[post]},
            headers={"Authorization":f"Ghost {ghost_token()}","Content-Type":"application/json"}, timeout=60)
        if r.status_code in (200,201): print(f"  🎉 성공!")
        else:
            print(f"  ❌ 실패: {r.status_code}")
            try: print(f"     {json.dumps(r.json(),ensure_ascii=False)[:500]}")
            except: print(f"     {r.text[:300]}")
    except Exception as e:
        print(f"  ❌ 통신에러: {e}")
        traceback.print_exc()

# ──────────────────────────────────────────────
# 4. 썸네일 — VIP 차별화
# ──────────────────────────────────────────────
def make_thumbnail(img_prompt, tier):
    # ✅ v4: VIP는 Imagen 3회 재시도 + 전용 프롬프트
    max_tries = 3 if tier == "Royal Premium" else 1
    for attempt in range(1, max_tries + 1):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            result = client.models.generate_images(
                model="imagen-3.0-generate-001",
                prompt=img_prompt + ", highly detailed, cinematic lighting, 8k, professional",
                config=types.GenerateImagesConfig(
                    number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg"))
            if result.generated_images:
                print(f"  ✅ Imagen 썸네일 완료 (시도 {attempt})")
                return result.generated_images[0].image.image_bytes
        except Exception as e:
            print(f"  ⚠️ Imagen 시도 {attempt}: {e}")
            if attempt < max_tries: time.sleep(5)
    # Fallback
    try:
        r = requests.get(f"https://picsum.photos/seed/{random.randint(1,9999)}/1280/720", timeout=10)
        if r.status_code == 200: return r.content
    except: pass
    return None

# ──────────────────────────────────────────────
# 5. Gemini 호출
# ──────────────────────────────────────────────
def call_gem(client, model, prompt, retries=2):
    for i in range(1, retries+1):
        try:
            r = client.models.generate_content(model=model, contents=prompt)
            return str(r.text)
        except Exception as e:
            print(f"    ⚠️ Gemini({model}) 시도{i}: {type(e).__name__}: {e}")
            if i < retries: time.sleep(10*i)
    return None

def gem_with_fallback(client, tier, prompt):
    for m in MODEL_PRI.get(tier, ["gemini-2.5-flash"]):
        print(f"    [AI] {tier} → {m}")
        r = call_gem(client, m, prompt)
        if r: return r, m
    return None, None

# ──────────────────────────────────────────────
# 6. 분석 엔진
# ──────────────────────────────────────────────
def analyze(news_items, cat, tier):
    client = genai.Client(api_key=GEMINI_API_KEY)
    news_str = "\n".join(news_items)
    persona = EXPERT.get(cat, EXPERT["Economy"])
    now = datetime.now()
    ts, tf = now.strftime("%I:%M %p"), now.strftime("%B %d, %Y at %I:%M %p (UTC)")
    author = "Ethan Cole &amp; The Warm Insight Panel"

    if tier == "Basic":
        prompt = PROMPT_BASIC.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[NEWS_ITEMS]",news_str)
        raw, used = gem_with_fallback(client, tier, prompt)
        if not raw: return None,None,None,None
        html = build_basic(author, tf, raw)

    elif tier == "Premium":
        prompt = PROMPT_PREMIUM.replace("[CATEGORY]",cat).replace("[PERSONA]",persona).replace("[NEWS_ITEMS]",news_str)
        raw, used = gem_with_fallback(client, tier, prompt)
        if not raw: return None,None,None,None
        html = build_premium(author, tf, raw)

    else:  # Royal Premium
        # ✅ v4: 2회 분할 호출
        hint = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["hint"]
        p1 = (VIP_PROMPT_PART1.replace("[CATEGORY]",cat).replace("[PERSONA]",persona)
              .replace("[CAT_HINT]",hint).replace("[NEWS_ITEMS]",news_str))
        raw1, used = gem_with_fallback(client, tier, p1)
        if not raw1: return None,None,None,None

        # 빈 섹션 체크 → 1회 재시도
        if not xtag(raw1, "VIP_C1"):
            print("    ⚠️ Part1 불완전 → 재시도...")
            time.sleep(15)
            raw1_retry, _ = gem_with_fallback(client, tier, p1)
            if raw1_retry and xtag(raw1_retry, "VIP_C1"):
                raw1 = raw1_retry

        summary_for_p2 = xtag(raw1, "SUMMARY") or xtag(raw1, "HEADLINE") or "VIP analysis of " + cat
        p2 = (VIP_PROMPT_PART2.replace("[CATEGORY]",cat).replace("[PERSONA]",persona)
              .replace("[PART1_SUMMARY]",summary_for_p2[:500]).replace("[NEWS_ITEMS]",news_str))

        print(f"    [AI] Part 2 (Playbook) 생성 중...")
        time.sleep(10)
        raw2, _ = gem_with_fallback(client, tier, p2)
        if not raw2:
            print("    ⚠️ Part2 실패 → Part1만으로 발행")
            raw2 = ""

        # 빈 섹션 체크 → 1회 재시도
        if raw2 and not xtag(raw2, "VIP_T1"):
            print("    ⚠️ Part2 불완전 → 재시도...")
            time.sleep(15)
            raw2_retry, _ = gem_with_fallback(client, tier, p2)
            if raw2_retry and xtag(raw2_retry, "VIP_T1"):
                raw2 = raw2_retry

        raw = raw1 + "\n" + raw2
        html = build_vip(author, tf, raw, cat)

    title_raw = xtag(raw, "TITLE")
    img_prompt = xtag(raw, "IMAGE_PROMPT") or f"Abstract 3D cinematic {cat}"
    excerpt = xtag(raw, "EXCERPT") or "Insightful analysis."
    pretty = TIER_LABELS.get(tier, tier)
    title = f"[{pretty}] {title_raw}" if title_raw else f"({tier}) {cat} Insight"
    excerpt_t = f"⏰ {ts} | {excerpt}"
    html = sanitize(html)
    return title, img_prompt, html, excerpt_t

# ──────────────────────────────────────────────
# 7. HTML 빌더
# ──────────────────────────────────────────────
M = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;"

def _hdr(author, tf, badge=""):
    b = f' <span style="background:#b8974d;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;">{badge}</span>' if badge else ""
    return f'<div style="border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;padding:12px 0;margin-bottom:30px;"><p style="margin:0;font-size:14px;color:#4b5563;"><strong style="color:#1a252c;">By {author}</strong> &nbsp;|&nbsp; {tf}{b}</p></div>'

def _ftr(takeaway, ps):
    return f"""
    <hr style="border:0;height:1px;background:#e5e7eb;margin:40px 0;">
    <h2 style="font-family:Georgia,serif;font-size:26px;color:#1a252c;margin-bottom:15px;">Today's Warm Insight</h2>
    <p style="font-size:18px;line-height:1.6;color:#374151;">{takeaway}</p>
    <div style="margin-top:30px;background:#1a252c;padding:25px;border-radius:6px;border-left:4px solid #b8974d;">
      <p style="font-size:18px;line-height:1.6;color:#e5e7eb;margin:0;">
        <span style="color:#b8974d;font-weight:bold;">P.S.&nbsp;</span><span style="color:#d1d5db;">{ps}</span>
      </p>
    </div>
    <p style="font-size:14px;color:#9ca3af;margin-top:35px;text-align:center;text-transform:uppercase;">Disclaimer: For informational purposes only. All decisions are your own.</p>
    </div>"""

def _upgrade(msg):
    return f'<div style="background:#fffbeb;border:1px solid #f59e0b;padding:15px;border-radius:6px;margin-bottom:30px;"><p style="font-size:14px;color:#92400e;margin:0;text-align:center;">🔒 {msg}</p></div>'


def build_basic(author, tf, raw):
    return f"""<div style="{M}">{_hdr(author, tf)}
    <h2 style="font-family:Georgia,serif;font-size:24px;color:#1a252c;margin-bottom:15px;">What Happened</h2>
    <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:30px;">{xtag(raw,'SUMMARY')}</p>
    <div style="background:#f1f3f5;border-left:5px solid #8e44ad;padding:20px;border-radius:6px;margin-bottom:35px;">
      <h3 style="margin-top:0;font-size:18px;color:#1a252c;margin-bottom:8px;">📱 TikTok Take</h3>
      <p style="font-size:17px;line-height:1.6;color:#4b5563;margin:0;">{xtag(raw,'TIKTOK')}</p>
    </div>
    <strong style="font-size:20px;color:#1a252c;display:block;margin-bottom:10px;">{xtag(raw,'HEADLINE')}</strong>
    <p style="font-size:17px;line-height:1.7;color:#374151;margin-bottom:25px;">{xtag(raw,'DEPTH')}</p>
    <div style="background:#f8fafc;border:1px solid #e5e7eb;padding:15px;border-radius:6px;margin-bottom:35px;">
      <strong style="font-size:16px;color:#b8974d;">💡 Quick Flow:</strong>
      <span style="font-size:17px;color:#1a252c;display:block;margin-top:5px;font-weight:bold;">{xtag(raw,'FLOW')}</span>
    </div>
    {_upgrade('Want deeper analysis & action plans? <strong>Upgrade to Pro or VIP.</strong>')}
    {_ftr(xtag(raw,'TAKEAWAY'), xtag(raw,'PS'))}"""


def build_premium(author, tf, raw):
    return f"""<div style="{M}">{_hdr(author, tf, "PRO")}
    <h2 style="font-family:Georgia,serif;font-size:24px;color:#1a252c;margin-bottom:15px;">Executive Summary</h2>
    <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:35px;">{xtag(raw,'SUMMARY')}</p>
    <div style="background:#f1f3f5;border-left:5px solid #8e44ad;padding:20px;border-radius:6px;margin-bottom:40px;">
      <h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:10px;">📱 Viral Social Insights</h3>
      <p style="font-size:18px;line-height:1.6;color:#4b5563;margin:0;">{xtag(raw,'TIKTOK')}</p>
    </div>
    <h2 style="font-family:Georgia,serif;font-size:26px;color:#1a252c;margin-bottom:15px;">Market Drivers</h2>
    <strong style="font-size:22px;color:#1a252c;display:block;margin-bottom:12px;">{xtag(raw,'HEADLINE')}</strong>
    <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:20px;">{xtag(raw,'DEPTH')}</p>
    <div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:6px;margin-bottom:40px;">
      <strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>
      <span style="font-size:18px;color:#1a252c;display:block;margin-top:5px;font-weight:bold;">{xtag(raw,'FLOW')}</span>
    </div>
    <div style="background:#fff;border:2px solid #3b82f6;padding:25px;border-radius:8px;margin-bottom:35px;">
      <h3 style="margin-top:0;color:#1e40af;font-size:20px;margin-bottom:12px;">💎 Pro-Only Insight</h3>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin:0;">{xtag(raw,'PRO_INSIGHT')}</p>
    </div>
    <div style="background:#f0fdf4;border:1px solid #22c55e;padding:20px;border-radius:6px;margin-bottom:15px;">
      <p style="font-size:17px;line-height:1.6;color:#166534;margin:0;"><strong style="color:#166534;">🟢 DO:</strong> <span style="color:#166534;">{xtag(raw,'PRO_DO')}</span></p>
    </div>
    <div style="background:#fef2f2;border:1px solid #ef4444;padding:20px;border-radius:6px;margin-bottom:35px;">
      <p style="font-size:17px;line-height:1.6;color:#991b1b;margin:0;"><strong style="color:#991b1b;">🔴 DON'T:</strong> <span style="color:#991b1b;">{xtag(raw,'PRO_DONT')}</span></p>
    </div>
    {_upgrade('Want institutional analysis & The Titan\'s Playbook? <strong>Upgrade to VIP.</strong>')}
    {_ftr(xtag(raw,'TAKEAWAY'), xtag(raw,'PS'))}"""


# ✅ v4: VIP — 인라인 SVG 시각 요소 포함
def build_vip(author, tf, raw, cat):
    l1,v1,l2,v2,l3,v3 = parse_graph(xtag(raw,"GRAPH_DATA"), cat)
    COL = ["#e74c3c","#f59e0b","#10b981"]

    def gauge(lb,val,c):
        return f"""<div style="margin-bottom:20px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span style="font-size:16px;font-weight:600;color:#4b5563;">{lb}</span>
            <span style="font-size:16px;font-weight:700;color:{c};">{val}%</span>
          </div>
          <div style="width:100%;background:#e5e7eb;border-radius:6px;height:14px;overflow:hidden;">
            <div style="width:{val}%;background:{c};height:100%;border-radius:6px;"></div>
          </div></div>"""

    # ✅ v4: SVG 파이차트 (60/30/10 자산배분)
    svg_pie = """<svg viewBox="0 0 200 200" width="180" height="180" style="display:block;margin:15px auto;">
      <circle cx="100" cy="100" r="90" fill="none" stroke="#1a252c" stroke-width="30" stroke-dasharray="339.29 565.49" stroke-dashoffset="0"/>
      <circle cx="100" cy="100" r="90" fill="none" stroke="#64748b" stroke-width="30" stroke-dasharray="169.65 565.49" stroke-dashoffset="-339.29"/>
      <circle cx="100" cy="100" r="90" fill="none" stroke="#b8974d" stroke-width="30" stroke-dasharray="56.55 565.49" stroke-dashoffset="-508.94"/>
      <text x="100" y="95" text-anchor="middle" fill="#1a252c" font-size="14" font-weight="bold">60/30/10</text>
      <text x="100" y="115" text-anchor="middle" fill="#6b7280" font-size="10">ALLOCATION</text>
    </svg>
    <div style="display:flex;justify-content:center;gap:20px;margin-bottom:10px;">
      <span style="font-size:13px;color:#1a252c;">⬛ Stocks 60%</span>
      <span style="font-size:13px;color:#64748b;">⬛ Safe 30%</span>
      <span style="font-size:13px;color:#b8974d;">⬛ Cash 10%</span>
    </div>"""

    # ✅ v4: Sector Radar를 시각적 테이블로
    radar_rows = ""
    for i in range(1,5):
        r = xtag(raw, f"VIP_RADAR_{i}")
        if not r: continue
        is_bull = "bullish" in r.lower()
        bg = "#f0fdf4" if is_bull else "#fef2f2"
        txt_c = "#166534" if is_bull else "#991b1b"
        icon = "🟢 BULL" if is_bull else "🔴 BEAR"
        radar_rows += f'<tr><td style="padding:12px;border-bottom:1px solid #e5e7eb;font-size:15px;color:#374151;">{r}</td><td style="padding:12px;border-bottom:1px solid #e5e7eb;text-align:center;"><span style="background:{bg};color:{txt_c};padding:3px 10px;border-radius:4px;font-size:13px;font-weight:bold;">{icon}</span></td></tr>'

    radar_html = f"""
    <div style="background:#fff;border:2px solid #eab308;border-radius:8px;padding:25px;margin-bottom:35px;overflow-x:auto;">
      <h3 style="margin-top:0;color:#854d0e;font-size:20px;margin-bottom:15px;">🎯 VIP Sector Radar</h3>
      <table style="width:100%;border-collapse:collapse;">{radar_rows}</table>
    </div>""" if radar_rows else ""

    # ✅ v4: 히트맵 스타일 지표 카드
    def metric_card(lb, val, c):
        intensity = val / 100.0
        bg_opacity = f"rgba({','.join(str(int(c.lstrip('#')[i:i+2],16)) for i in (0,2,4))},{intensity*0.15 + 0.05})"
        return f"""<div style="flex:1;min-width:180px;background:{bg_opacity};border:1px solid {c};border-radius:8px;padding:20px;text-align:center;">
          <div style="font-size:36px;font-weight:800;color:{c};margin-bottom:5px;">{val}%</div>
          <div style="font-size:14px;color:#4b5563;font-weight:600;">{lb}</div>
        </div>"""

    vip_c1 = xtag(raw,"VIP_C1")
    vip_c2 = xtag(raw,"VIP_C2")
    vip_c3 = xtag(raw,"VIP_C3")
    vip_t1 = xtag(raw,"VIP_T1")
    vip_t2 = xtag(raw,"VIP_T2")
    vip_t3 = xtag(raw,"VIP_T3")
    vip_t4 = xtag(raw,"VIP_T4")
    vip_do = xtag(raw,"VIP_DO")
    vip_dont = xtag(raw,"VIP_DONT")
    takeaway = xtag(raw,"TAKEAWAY")
    ps = xtag(raw,"PS")

    def pb(n, title, body, extra=""):
        return f"""<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:25px;border-radius:6px;margin-bottom:25px;">
          <h3 style="color:#1a252c;margin-top:0;font-size:22px;margin-bottom:15px;">{n}. {title}</h3>
          {extra}
          <p style="font-size:18px;line-height:1.7;color:#4b5563;margin-bottom:0;{'margin-top:20px;' if extra else ''}">{body}</p>
        </div>"""

    # 빈 섹션 fallback 메시지
    empty_msg = '<p style="font-size:16px;color:#9ca3af;font-style:italic;">(Analysis generating — check back shortly)</p>'

    return f"""<div style="{M}">{_hdr(author, tf, "VIP EXCLUSIVE")}
    <h2 style="font-family:Georgia,serif;font-size:24px;color:#1a252c;margin-bottom:15px;">Executive Summary</h2>
    <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:35px;">{xtag(raw,'SUMMARY')}</p>

    <div style="background:#f1f3f5;border-left:5px solid #8e44ad;padding:20px;border-radius:6px;margin-bottom:40px;">
      <h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:10px;">📱 Viral Social Insights</h3>
      <p style="font-size:18px;line-height:1.6;color:#4b5563;margin:0;">{xtag(raw,'TIKTOK')}</p>
    </div>

    <h2 style="font-family:Georgia,serif;font-size:26px;color:#1a252c;margin-bottom:15px;">Market Drivers &amp; Insights</h2>
    <strong style="font-size:22px;color:#1a252c;display:block;margin-bottom:12px;">{xtag(raw,'HEADLINE')}</strong>
    <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:20px;">{xtag(raw,'DEPTH')}</p>

    <div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:6px;margin-bottom:40px;">
      <strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>
      <span style="font-size:18px;color:#1a252c;display:block;margin-top:5px;font-weight:bold;">{xtag(raw,'FLOW')}</span>
    </div>

    <!-- 히트맵 지표 카드 -->
    <div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">
      {metric_card(l1,v1,COL[0])}
      {metric_card(l2,v2,COL[1])}
      {metric_card(l3,v3,COL[2])}
    </div>

    <!-- 게이지 바 -->
    <div style="padding:25px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:35px;">
      <h3 style="margin-top:0;color:#1a252c;font-size:20px;border-bottom:2px solid #e5e7eb;padding-bottom:12px;margin-bottom:25px;">📊 Key Market Indicators</h3>
      {gauge(l1,v1,COL[0])}{gauge(l2,v2,COL[1])}{gauge(l3,v3,COL[2])}
    </div>

    {radar_html}

    <h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:25px;border-bottom:2px solid #b8974d;padding-bottom:10px;display:inline-block;">VIP Exclusive: Macro &amp; Flow Analysis</h2>
    <div style="background:#fff;border:1px solid #e5e7eb;border-left:5px solid #1a252c;padding:25px;border-radius:6px;margin-bottom:40px;box-shadow:0 4px 6px rgba(0,0,0,.05);">
      <p style="font-size:17px;color:#b8974d;text-transform:uppercase;font-weight:bold;margin-top:0;margin-bottom:20px;">[Institutional Technical Outlook]</p>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:15px;">{vip_c1 or empty_msg}</p>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:15px;">{vip_c2 or empty_msg}</p>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:0;">{vip_c3 or empty_msg}</p>
    </div>

    <h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:10px;border-bottom:2px solid #b8974d;padding-bottom:10px;display:inline-block;">The Titan's Playbook</h2>
    <p style="font-size:17px;color:#6b7280;margin-bottom:30px;font-style:italic;">Strategic manual for navigating current conditions.</p>

    {pb("1","The Generational Bargain (Fear vs. Greed)", vip_t1 or empty_msg)}
    {pb("2","The 60/30/10 Seesaw (Asset Allocation)", vip_t2 or empty_msg, svg_pie)}
    {pb("3","The Global Shield (US Dollar &amp; Market)", vip_t3 or empty_msg)}
    {pb("4","Survival Mechanics (Split Buying &amp; Mental Peace)", vip_t4 or empty_msg)}

    <div style="background:#1a252c;padding:35px;border-radius:8px;margin:45px 0 40px;box-shadow:0 6px 12px rgba(0,0,0,.15);">
      <h3 style="color:#b8974d;margin-top:0;font-size:24px;margin-bottom:25px;border-bottom:1px solid #4b5563;padding-bottom:15px;">✅ Today's VIP Action Plan</h3>
      <div style="background:#22332b;border-radius:6px;padding:20px;margin-bottom:20px;">
        <p style="font-size:18px;color:#34d399;font-weight:bold;margin:0 0 10px 0;">🟢 DO (Action):</p>
        <p style="font-size:17px;line-height:1.7;color:#d1fae5;margin:0;">{vip_do or empty_msg}</p>
      </div>
      <div style="background:#3b1c1c;border-radius:6px;padding:20px;">
        <p style="font-size:18px;color:#f87171;font-weight:bold;margin:0 0 10px 0;">🔴 DON'T (Avoid):</p>
        <p style="font-size:17px;line-height:1.7;color:#fecaca;margin:0;">{vip_dont or empty_msg}</p>
      </div>
    </div>
    {_ftr(takeaway, ps)}"""


# ──────────────────────────────────────────────
# 8. 메인
# ──────────────────────────────────────────────
def main():
    print("="*50)
    print("  🚀 Warm Insight v4 — Split-Call + Visual Engine")
    print("="*50)
    total = ok = fail = 0

    for cat, urls in CATEGORIES.items():
        print(f"\n━━━ [{cat}] ━━━")
        news = get_news(urls, 20)
        if len(news) < 3:
            print(f"  ⚠️ 뉴스 부족 → 건너뜀")
            continue
        for task in TASKS:
            tier, cnt = task["tier"], task["count"]
            if len(news) < cnt:
                print(f"  ⚠️ 뉴스 부족 → {tier} 건너뜀")
                break
            target = [news.pop(0) for _ in range(cnt)]
            total += 1
            print(f"\n  🔹 [{TIER_LABELS[tier]}] {cnt}개 뉴스 분석...")

            title, ip, html, exc = analyze(target, cat, tier)
            if not html:
                fail += 1; continue

            iu = None
            if ip:
                ib = make_thumbnail(ip, tier)
                if ib: iu = upload_img(ib)
            publish(title, html, cat, tier, iu, exc)
            ok += 1
            sl = TIER_SLEEP[tier]
            print(f"  ⏳ {sl}초 대기...")
            time.sleep(sl)

    print(f"\n{'='*50}\n  📊 총 {total} | ✅ {ok} | ❌ {fail}\n{'='*50}")

if __name__ == "__main__":
    try: main()
    except:
        print("\n❌ 시스템 에러")
        traceback.print_exc()
        sys.exit(1)
