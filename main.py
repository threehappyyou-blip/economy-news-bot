# -*- coding: utf-8 -*-
"""
Warm Insight v3 — Premium Quality Upgrade
==========================================
v2 → v3 변경사항:
  1. VIP Action Plan 검은 배경 텍스트 깨짐 수정
  2. P.S. 섹션 텍스트 잘림 수정
  3. GRAPH_DATA 카테고리별 중복 방지 (카테고리 특화 프롬프트)
  4. 등급별 콘텐츠 차등 대폭 강화 (Basic 40% / Premium 70% / VIP 100%)
  5. VIP 전용 섹션 추가 (Institutional Radar, Sector Heatmap 등)
  6. 모든 HTML 요소에 명시적 color 속성 부여 (Ghost 렌더링 호환)
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

# ✅ v3: 등급별 뉴스 할당량 차등 (VIP가 더 많은 뉴스 분석)
TASKS = [
    {"tier": "Basic",         "count": 2},
    {"tier": "Premium",       "count": 3},
    {"tier": "Royal Premium", "count": 5},
]

TIER_LABELS = {
    "Basic":         "🌱 Free",
    "Premium":       "💎 Pro",
    "Royal Premium": "👑 VIP",
}

# 구독자 1000명 달성 전까지는 전부 공개 운영
TIER_VISIBILITY = {
    "Basic":         "public",
    "Premium":       "public",   # TODO → "members"
    "Royal Premium": "public",   # TODO → "paid"
}

# ✅ v3: VIP는 더 길게 대기 (Gemini Pro rate-limit)
TIER_SLEEP = {
    "Basic":         15,
    "Premium":       30,
    "Royal Premium": 50,
}

MODEL_PRIORITY = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash"],
    "Premium":       ["gemini-2.5-pro", "gemini-2.5-flash"],
    "Basic":         ["gemini-2.5-flash"],
}

EXPERT_PERSONA = {
    "Politics": "a veteran US political strategist with 40 years of Washington experience",
    "Tech":     "a veteran Silicon Valley technology analyst with 40 years of experience",
    "Health":   "a veteran US healthcare and biotech analyst with 40 years of experience",
    "Energy":   "a veteran US energy and commodities strategist with 40 years of experience",
    "Economy":  "a veteran US Wall Street strategist with 40 years of experience",
}

# ✅ v3: 카테고리별 고유 지표 풀 (중복 방지용)
CATEGORY_METRICS = {
    "Economy": {
        "pool": [
            "Inflation Momentum", "Recession Probability", "Consumer Spending Pulse",
            "Credit Market Stress", "Rate Cut Expectation", "Liquidity Squeeze Index",
            "Wage Growth Tension", "Housing Market Fragility", "Manufacturing PMI Signal",
            "Savings Rate Erosion", "Dollar Strength Index", "Yield Curve Inversion Depth",
        ],
        "prompt_hint": "Focus on macro indicators: inflation, GDP, employment, consumer confidence, yield curves, Fed policy impact.",
    },
    "Politics": {
        "pool": [
            "Policy Uncertainty Index", "Regulatory Risk Score", "Geopolitical Tension Level",
            "Legislative Gridlock Meter", "Election Volatility Index", "Trade War Escalation Risk",
            "Bipartisan Cooperation Score", "Sanctions Impact Severity", "Defense Spending Momentum",
            "Immigration Policy Disruption", "Tariff Exposure Index", "Diplomatic Crisis Meter",
        ],
        "prompt_hint": "Focus on political risk metrics: policy uncertainty, regulatory changes, geopolitical tensions, legislative impact.",
    },
    "Tech": {
        "pool": [
            "AI Arms Race Intensity", "Antitrust Regulatory Pressure", "Semiconductor Supply Stress",
            "Tech IPO Sentiment", "Cloud Adoption Velocity", "Cybersecurity Threat Level",
            "Big Tech Earnings Momentum", "Startup Funding Freeze Index", "Data Privacy Risk Score",
            "Autonomous Tech Readiness", "Quantum Computing Proximity", "Digital Ad Market Health",
        ],
        "prompt_hint": "Focus on tech-specific metrics: AI adoption, semiconductor supply, Big Tech regulation, startup funding, cybersecurity.",
    },
    "Health": {
        "pool": [
            "Pharma Pipeline Confidence", "Drug Pricing Pressure", "Biotech Funding Pulse",
            "Healthcare Policy Risk", "FDA Approval Momentum", "Pandemic Preparedness Score",
            "Gene Therapy Breakthrough Index", "Hospital System Stress", "Insurance Coverage Gap",
            "Clinical Trial Success Rate", "Medical Device Innovation Score", "Telehealth Adoption Rate",
        ],
        "prompt_hint": "Focus on health metrics: pharma pipelines, drug pricing, biotech investment, FDA activity, healthcare affordability.",
    },
    "Energy": {
        "pool": [
            "Crude Oil Supply Squeeze", "Green Transition Velocity", "OPEC Compliance Tension",
            "LNG Demand Surge Index", "Renewable Capacity Growth", "Fossil Fuel Stranding Risk",
            "Energy Geopolitical Shock Risk", "Grid Reliability Stress", "Carbon Credit Market Heat",
            "Nuclear Revival Momentum", "EV Demand Acceleration", "Refinery Margin Pressure",
        ],
        "prompt_hint": "Focus on energy metrics: oil supply/demand, OPEC dynamics, renewable transition, LNG markets, geopolitical supply risk.",
    },
}

# ──────────────────────────────────────────────
# 1. 프롬프트 템플릿 — 등급별 완전 분리
# ──────────────────────────────────────────────

# ✅ v3: BASIC (40%) — 간단한 요약만
PROMPT_BASIC = """
[Goal] Write a SHORT, friendly blog post in ENGLISH for the '[CATEGORY]' section of 'Warm Insight'.
Target: Free Subscribers (beginners who know nothing about finance).

You are [PERSONA]. But you explain like a kind teacher to a 15-year-old.

RULES:
1. Write ENTIRELY in ENGLISH.
2. Keep it SIMPLE. No jargon. Use everyday analogies.
3. Maximum 400 words for the entire post.

OUTPUT FORMAT (STRICT XML):
<TITLE>Simple, catchy title a teenager would click</TITLE>
<IMAGE_PROMPT>Simple English prompt for 3D abstract cinematic image</IMAGE_PROMPT>
<EXCERPT>1 sentence summary a beginner can understand</EXCERPT>
<SUMMARY>3 sentences explaining the news like you're talking to a friend at coffee</SUMMARY>
<TIKTOK>Translate the news into a fun, viral TikTok-style analogy (2-3 sentences)</TIKTOK>
<HEADLINE>One-line headline of the key insight</HEADLINE>
<DEPTH>ELI5 explanation: What happened? Why should I care? What does it mean for my wallet? (3-4 sentences max)</DEPTH>
<FLOW>Simple Emoji Flow (e.g. Event 📰 ➡️ Effect 💰 ➡️ Your Life 🏠)</FLOW>
<TAKEAWAY>One comforting, actionable sentence for beginners</TAKEAWAY>
<PS>One short personal thought (1 sentence)</PS>

Raw News:
[NEWS_ITEMS]
"""

# ✅ v3: PREMIUM (70%) — 분석 + 행동경제학
PROMPT_PREMIUM = """
[Goal] Write an analytical blog post in ENGLISH for the '[CATEGORY]' section of 'Warm Insight'.
Target: Pro Subscribers (intermediate investors who want deeper "why" behind the news).

You are [PERSONA].

RULES:
1. Write ENTIRELY in ENGLISH.
2. Go beyond surface-level. Explain the behavioral economics and psychology.
3. Use horizontal "Emoji Flows" for diagrams.
4. Aim for 600-800 words.

OUTPUT FORMAT (STRICT XML):
<TITLE>Analytical, insight-driven title</TITLE>
<IMAGE_PROMPT>Simple English prompt for 3D abstract cinematic image</IMAGE_PROMPT>
<EXCERPT>1 sentence capturing the key analytical insight</EXCERPT>
<SUMMARY>3 sentence executive summary with the "so what" factor</SUMMARY>
<TIKTOK>Translate the news into a super-engaging TikTok-style analogy that reveals a hidden truth</TIKTOK>
<HEADLINE>Headline of the main analytical insight</HEADLINE>
<DEPTH><strong>🧐 WHY IT MATTERS:</strong> Explain the deeper cause using behavioral economics. Why are people reacting this way? What cognitive bias is at play? (4-5 sentences)<br><br><strong>🐑 HERD PSYCHOLOGY:</strong> What is the crowd doing wrong? What are they missing? (3-4 sentences)</DEPTH>
<FLOW>Detailed Emoji Flow showing cause-and-effect chain (at least 5 steps)</FLOW>
<PRO_INSIGHT>A "Pro-Only" insight: one non-obvious connection between this news and another sector/trend that most people miss. (4-5 sentences)</PRO_INSIGHT>
<PRO_DO>2 specific, actionable steps for intermediate investors</PRO_DO>
<PRO_DONT>1 specific mistake the herd is making right now</PRO_DONT>
<TAKEAWAY>An insightful, actionable takeaway that makes Pro subscribers feel smarter</TAKEAWAY>
<PS>A personal thought with historical perspective (2 sentences)</PS>

Raw News:
[NEWS_ITEMS]
"""

# ✅ v3: VIP (100%) — 풀 기관급 분석 + 카테고리 특화 지표
PROMPT_VIP = """
[Goal] Write an INSTITUTIONAL-GRADE, deeply analytical blog post in ENGLISH for the '[CATEGORY]' section of 'Warm Insight'.
Target: VIP Subscribers (sophisticated investors who pay premium for alpha-generating insights).

You are [PERSONA]. You write like a Goldman Sachs morning briefing crossed with a seasoned mentor's private letter.

CRITICAL RULES:
1. Write ENTIRELY in ENGLISH.
2. This must feel worth paying for. Every paragraph must contain a non-obvious insight.
3. Use horizontal "Emoji Flows" for diagrams.
4. Aim for 1200-1500 words. Depth over brevity.
5. TIKTOK INFLUENCE: Create a 'Viral Social Insights' section based on these vibes: [TIKTOK_LINKS]

OUTPUT FORMAT (STRICT XML — follow EXACTLY):
<TITLE>Institutional-grade, compelling title</TITLE>
<IMAGE_PROMPT>Simple English prompt for 3D abstract cinematic image</IMAGE_PROMPT>
<EXCERPT>1 sentence that makes VIP subscribers feel they're getting exclusive intel</EXCERPT>
<SUMMARY>3 sentence executive summary with institutional depth</SUMMARY>
<TIKTOK>Translate the news into a super-engaging TikTok style analogy that a Gen-Z investor would share</TIKTOK>
<HEADLINE>Headline capturing the alpha-generating insight</HEADLINE>
<DEPTH><strong>🧐 WHY (Macro):</strong> Deep macroeconomic analysis. Connect to global capital flows, central bank policy, and structural trends. (5+ sentences)<br><br><strong>🐑 HERD BEHAVIOR:</strong> What is the crowd doing? What cognitive bias is driving them? (4+ sentences)<br><br><strong>🦅 CONTRARIAN VIEW:</strong> What does smart money see that the herd doesn't? What's the second and third-order consequence? (5+ sentences)</DEPTH>
<FLOW>Detailed Emoji Flow showing the full cause-effect-consequence chain (6+ steps)</FLOW>
<GRAPH_DATA>CRITICAL: Analyze the SPECIFIC news provided and create 3 metrics UNIQUE to this [CATEGORY] category.
[CATEGORY_METRIC_HINT]
Assign a realistic 0-100 score to each based on the actual news severity.
FORMAT STRICTLY AS: MetricName1|Score1|MetricName2|Score2|MetricName3|Score3
Use ONLY pipe | as separator. NO colons. NO hyphens in names. NO copying examples.</GRAPH_DATA>
<VIP_RADAR>Create a "Sector Radar" — identify exactly 4 related sectors/assets affected by this news. For each, state: the sector name, whether it's BULLISH or BEARISH, and a 1-sentence reason why. Format as 4 lines.</VIP_RADAR>
<VIP_C1>PARAGRAPH 1 — Technical Outlook: Analyze RSI, Moving Averages, support/resistance levels. Reference specific price levels and timeframes. At least 5 detailed sentences.</VIP_C1>
<VIP_C2>PARAGRAPH 2 — Macro Flow Analysis: Analyze yield curves, credit spreads, capital flow data, dollar index. Connect to this specific news. At least 5 detailed sentences.</VIP_C2>
<VIP_C3>PARAGRAPH 3 — Smart Money Positioning: What are institutions, hedge funds, and insiders doing RIGHT NOW? Reference COT data, 13F filings, dark pool activity conceptually. At least 5 detailed sentences.</VIP_C3>
<VIP_T1>The Generational Bargain: Is this a moment of Extreme Fear or Extreme Greed? Apply the Fear & Greed framework to TODAY'S specific news. Where are we in the cycle? What would Buffett/Templeton do? Detailed paragraph with conviction.</VIP_T1>
<VIP_T2>The 60/30/10 Seesaw: Given TODAY'S news, should the allocation tilt? Which specific assets in each bucket? How to mechanically rebalance this week? Detailed paragraph with specific actions.</VIP_T2>
<VIP_T3>The Global Shield: Why US-denominated assets matter right now. Compare to Europe/China/EM risk. What's the dollar doing and why? Detailed paragraph with global context.</VIP_T3>
<VIP_T4>Survival Mechanics: DCA strategy for this specific situation. When to deploy cash. The 50% panic sell rule — when exactly does it trigger? Detailed paragraph with specific thresholds.</VIP_T4>
<VIP_DO>3 highly specific, actionable steps with exact details (which ETF, what percentage, what trigger)</VIP_DO>
<VIP_DONT>2 specific mistakes to avoid, with explanation of why each is dangerous right now</VIP_DONT>
<TAKEAWAY>A masterful, calming insight that makes the VIP subscriber feel they have an unfair advantage</TAKEAWAY>
<PS>A personal reflection with 40 years of wisdom — reference a specific historical parallel (2-3 sentences)</PS>

Raw News:
[NEWS_ITEMS]
"""

# ──────────────────────────────────────────────
# 2. 유틸 함수
# ──────────────────────────────────────────────
def extract_tag(text: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def get_category_news(urls: list, count: int = 20) -> list:
    news, seen = [], set()
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
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


# ✅ v3: GRAPH_DATA 파싱 — 카테고리별 fallback 풀에서 랜덤 추출
def parse_graph_data(raw: str, category: str):
    KNOWN_LAZY = {"Sector Stress", "Market Fear", "Growth Outlook", "Policy Risk",
                  "Inflation Anxiety", "Recession Probability"}
    parts = [p.strip() for p in raw.split("|") if p.strip()]

    if len(parts) >= 6:
        labels_found = {parts[0], parts[2], parts[4]}
        if labels_found & KNOWN_LAZY:
            parts = []

    if len(parts) >= 6:
        try:
            v1 = max(5, min(99, int(re.sub(r"\D", "", parts[1]))))
            v2 = max(5, min(99, int(re.sub(r"\D", "", parts[3]))))
            v3 = max(5, min(99, int(re.sub(r"\D", "", parts[5]))))
            return parts[0], v1, parts[2], v2, parts[4], v3
        except (ValueError, IndexError):
            pass

    pool = CATEGORY_METRICS.get(category, CATEGORY_METRICS["Economy"])["pool"]
    labels = random.sample(pool, 3)
    return (
        labels[0], random.randint(55, 92),
        labels[1], random.randint(35, 75),
        labels[2], random.randint(45, 88),
    )


def sanitize_html(html: str) -> str:
    html = html.replace("\n", " ").replace("\r", "")
    html = re.sub(r"\s{2,}", " ", html)
    size_kb = len(html.encode("utf-8")) / 1024
    if size_kb > 500:
        print(f"  ⚠️ HTML 크기 경고: {size_kb:.0f} KB")
    return html


# ──────────────────────────────────────────────
# 3. Ghost 통신
# ──────────────────────────────────────────────
def generate_ghost_token() -> str:
    kid, secret = str(GHOST_ADMIN_API_KEY).split(":")
    iat = int(datetime.now().timestamp())
    return jwt.encode(
        {"iat": iat, "exp": iat + 300, "aud": "/admin/"},
        bytes.fromhex(secret),
        algorithm="HS256",
        headers={"alg": "HS256", "typ": "JWT", "kid": kid},
    )


def upload_image_to_ghost(image_bytes: bytes) -> str | None:
    try:
        token = generate_ghost_token()
        resp = requests.post(
            f"{GHOST_API_URL}/ghost/api/admin/images/upload/",
            headers={"Authorization": f"Ghost {token}"},
            files={"file": ("thumbnail.jpg", image_bytes, "image/jpeg"),
                   "purpose": (None, "image")},
            timeout=30,
        )
        if resp.status_code in (200, 201):
            return resp.json()["images"][0]["url"]
        print(f"  ❌ 이미지 업로드 실패: {resp.status_code}")
    except Exception as e:
        print(f"  ❌ 이미지 업로드 에러: {e}")
    return None


def publish_to_ghost(title, html, category, tier, image_url, excerpt):
    print(f"  📝 발행 중: '{title}'")
    try:
        token = generate_ghost_token()
        headers = {
            "Authorization": f"Ghost {token}",
            "Content-Type": "application/json",
        }
        mobiledoc = json.dumps({
            "version": "0.3.1",
            "markups": [], "atoms": [],
            "cards": [["html", {"html": html}]],
            "sections": [[10, 0]],
        })
        visibility = TIER_VISIBILITY.get(tier, "public")
        post = {
            "title": title,
            "mobiledoc": mobiledoc,
            "status": "published",
            "visibility": visibility,
            "tags": [{"name": category}, {"name": tier}],
        }
        if excerpt:
            post["custom_excerpt"] = excerpt[:290] + ("..." if len(excerpt) > 290 else "")
        if image_url:
            post["feature_image"] = image_url
        resp = requests.post(
            f"{GHOST_API_URL}/ghost/api/admin/posts/",
            json={"posts": [post]},
            headers=headers,
            timeout=60,
        )
        if resp.status_code in (200, 201):
            print(f"  🎉 발행 성공! (visibility={visibility})")
        else:
            print(f"  ❌ 발행 실패: {resp.status_code}")
            try:
                print(f"     Ghost 에러: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:1000]}")
            except Exception:
                print(f"     응답: {resp.text[:500]}")
    except Exception as e:
        print(f"  ❌ 발행 통신 에러: {e}")
        traceback.print_exc()


# ──────────────────────────────────────────────
# 4. 썸네일 생성
# ──────────────────────────────────────────────
def generate_thumbnail(image_prompt: str) -> bytes | None:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        result = client.models.generate_images(
            model="imagen-3.0-generate-001",
            prompt=f"{image_prompt}, highly detailed, cinematic lighting, 8k, professional financial tone",
            config=types.GenerateImagesConfig(
                number_of_images=1, aspect_ratio="16:9", output_mime_type="image/jpeg",
            ),
        )
        if result.generated_images:
            print("  ✅ Imagen 3 썸네일 완료")
            return result.generated_images[0].image.image_bytes
    except Exception as e:
        print(f"  ⚠️ Imagen 실패: {e}")
    try:
        resp = requests.get(f"https://picsum.photos/seed/{random.randint(1,9999)}/1280/720", timeout=10)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────
# 5. Gemini 호출
# ──────────────────────────────────────────────
def call_gemini(client, model: str, prompt: str, retries: int = 2) -> str | None:
    for i in range(1, retries + 1):
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            return str(resp.text)
        except Exception as e:
            print(f"    ⚠️ Gemini 실패 (model={model}, try={i}): {type(e).__name__}: {e}")
            if i < retries:
                time.sleep(10 * i)
    return None


def run_gemini(news_items, category, tier):
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_news = "\n".join(news_items)
    persona = EXPERT_PERSONA.get(category, EXPERT_PERSONA["Economy"])

    # ✅ v3: 등급별 완전히 다른 프롬프트
    if tier == "Basic":
        prompt = (PROMPT_BASIC
                  .replace("[CATEGORY]", category)
                  .replace("[PERSONA]", persona)
                  .replace("[NEWS_ITEMS]", selected_news))
    elif tier == "Premium":
        prompt = (PROMPT_PREMIUM
                  .replace("[CATEGORY]", category)
                  .replace("[PERSONA]", persona)
                  .replace("[NEWS_ITEMS]", selected_news))
    else:  # Royal Premium
        metric_hint = CATEGORY_METRICS.get(category, CATEGORY_METRICS["Economy"])["prompt_hint"]
        prompt = (PROMPT_VIP
                  .replace("[CATEGORY]", category)
                  .replace("[PERSONA]", persona)
                  .replace("[TIKTOK_LINKS]", TIKTOK_LINKS)
                  .replace("[CATEGORY_METRIC_HINT]", metric_hint)
                  .replace("[NEWS_ITEMS]", selected_news))

    models = MODEL_PRIORITY.get(tier, ["gemini-2.5-flash"])
    raw = None
    used = None
    for m in models:
        print(f"    [AI] {tier} → {m} 시도...")
        raw = call_gemini(client, m, prompt)
        if raw:
            used = m
            break
        print(f"    ❌ {m} 실패, 다음 모델...")

    if not raw:
        print(f"  ⛔ 모든 모델 실패: {category}/{tier}")
        return None, None, None, None

    print(f"    ✅ 분석 완료 ({used})")

    # 공통 태그 추출
    title_raw = extract_tag(raw, "TITLE")
    img_prompt = extract_tag(raw, "IMAGE_PROMPT") or f"Abstract 3D cinematic rendering of global {category}."
    excerpt = extract_tag(raw, "EXCERPT") or "Insightful analysis for your future."
    summary = extract_tag(raw, "SUMMARY")
    tiktok = extract_tag(raw, "TIKTOK")
    headline = extract_tag(raw, "HEADLINE")
    depth = extract_tag(raw, "DEPTH")
    flow = extract_tag(raw, "FLOW")
    takeaway = extract_tag(raw, "TAKEAWAY")
    ps = extract_tag(raw, "PS")

    pretty = TIER_LABELS.get(tier, tier)
    title = f"[{pretty}] {title_raw}" if title_raw else f"({tier}) Daily {category} Insight"
    now = datetime.now()
    ts = now.strftime("%I:%M %p")
    tf = now.strftime("%B %d, %Y at %I:%M %p (UTC)")
    author = "Ethan Cole &amp; The Warm Insight Panel"
    excerpt_t = f"⏰ {ts} | {excerpt}"

    # 등급별 HTML 조립
    if tier == "Basic":
        html = build_basic_html(author, tf, summary, tiktok, headline, depth, flow, takeaway, ps)
    elif tier == "Premium":
        html = build_premium_html(author, tf, summary, tiktok, headline, depth, flow, raw, takeaway, ps)
    else:
        html = build_vip_html(author, tf, summary, tiktok, headline, depth, flow, raw, category, takeaway, ps)

    html = sanitize_html(html)
    return title, img_prompt, html, excerpt_t


# ──────────────────────────────────────────────
# 6. HTML 빌더 — 등급별 완전 분리
# ──────────────────────────────────────────────

# ── 공통 스타일 ──
MAIN = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;"
HDR = "border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;padding:12px 0;margin-bottom:30px;width:100%;"

def _header(author, tf, tier_badge=""):
    badge = f' <span style="background:#b8974d;color:#fff;padding:2px 10px;border-radius:4px;font-size:12px;font-weight:bold;letter-spacing:1px;">{tier_badge}</span>' if tier_badge else ""
    return f"""
    <div style="{HDR}">
      <p style="margin:0;font-size:14px;color:#4b5563;text-transform:uppercase;letter-spacing:.5px;">
        <strong style="color:#1a252c;">By {author}</strong> &nbsp;|&nbsp; {tf}{badge}
      </p>
    </div>"""


def _footer(takeaway, ps):
    return f"""
    <hr style="border:0;height:1px;background:#e5e7eb;margin:40px 0;">
    <h2 style="font-family:Georgia,serif;font-size:26px;color:#1a252c;margin-bottom:15px;">Today's Warm Insight</h2>
    <p style="font-size:18px;line-height:1.6;color:#374151;">{takeaway}</p>
    <div style="margin-top:30px;background:#1a252c;padding:25px;border-radius:6px;border-left:4px solid #b8974d;">
      <p style="font-size:18px;line-height:1.6;color:#e5e7eb;margin:0;">
        <span style="font-size:18px;color:#b8974d;font-weight:bold;">P.S.&nbsp;</span>
        <span style="color:#e5e7eb;">{ps}</span>
      </p>
    </div>
    <p style="font-size:14px;color:#9ca3af;margin-top:35px;text-align:center;text-transform:uppercase;letter-spacing:.5px;">
      Disclaimer: This article is for informational purposes only. All decisions are your own.
    </p>
    </div>"""


# ── BASIC (40%) — 깔끔하고 짧은 ──
def build_basic_html(author, tf, summary, tiktok, headline, depth, flow, takeaway, ps):
    return f"""
    <div style="{MAIN}">
      {_header(author, tf)}
      <h2 style="font-family:Georgia,serif;font-size:24px;color:#1a252c;margin-top:0;margin-bottom:15px;">What Happened</h2>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:30px;">{summary}</p>

      <div style="background:#f1f3f5;border-left:5px solid #8e44ad;padding:20px;border-radius:6px;margin-bottom:35px;width:100%;">
        <h3 style="margin-top:0;font-size:18px;color:#1a252c;margin-bottom:8px;">📱 TikTok Take</h3>
        <p style="font-size:17px;line-height:1.6;color:#4b5563;margin:0;">{tiktok}</p>
      </div>

      <strong style="font-size:20px;color:#1a252c;display:block;margin-bottom:10px;">{headline}</strong>
      <p style="font-size:17px;line-height:1.7;color:#374151;margin-bottom:25px;">{depth}</p>

      <div style="background:#f8fafc;border:1px solid #e5e7eb;padding:15px;border-radius:6px;margin-bottom:35px;width:100%;">
        <strong style="font-size:16px;color:#b8974d;">💡 Quick Flow:</strong>
        <span style="font-size:17px;color:#1a252c;display:block;margin-top:5px;font-weight:bold;">{flow}</span>
      </div>

      <div style="background:#fffbeb;border:1px solid #f59e0b;padding:15px;border-radius:6px;margin-bottom:30px;">
        <p style="font-size:14px;color:#92400e;margin:0;text-align:center;">
          🔒 Want deeper analysis, action plans, and institutional insights? <strong>Upgrade to Pro or VIP.</strong>
        </p>
      </div>
      {_footer(takeaway, ps)}"""


# ── PREMIUM (70%) — 분석 + Pro 인사이트 ──
def build_premium_html(author, tf, summary, tiktok, headline, depth, flow, raw, takeaway, ps):
    pro_insight = extract_tag(raw, "PRO_INSIGHT")
    pro_do = extract_tag(raw, "PRO_DO")
    pro_dont = extract_tag(raw, "PRO_DONT")

    return f"""
    <div style="{MAIN}">
      {_header(author, tf, "PRO")}
      <h2 style="font-family:Georgia,serif;font-size:24px;color:#1a252c;margin-top:0;margin-bottom:15px;">Executive Summary</h2>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:35px;">{summary}</p>

      <div style="background:#f1f3f5;border-left:5px solid #8e44ad;padding:20px;border-radius:6px;margin-bottom:40px;width:100%;">
        <h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:10px;">📱 Viral Social Insights</h3>
        <p style="font-size:18px;line-height:1.6;color:#4b5563;margin:0;">{tiktok}</p>
      </div>

      <h2 style="font-family:Georgia,serif;font-size:26px;color:#1a252c;margin-bottom:15px;">Market Drivers &amp; Insights</h2>
      <strong style="font-size:22px;color:#1a252c;display:block;margin-bottom:12px;">{headline}</strong>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:20px;">{depth}</p>

      <div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:6px;margin-bottom:40px;width:100%;">
        <strong style="font-size:18px;color:#b8974d;text-transform:uppercase;letter-spacing:.5px;">💡 Quick Flow:</strong>
        <span style="font-size:18px;color:#1a252c;display:block;margin-top:5px;font-weight:bold;">{flow}</span>
      </div>

      <div style="background:#ffffff;border:2px solid #3b82f6;padding:25px;border-radius:8px;margin-bottom:35px;width:100%;">
        <h3 style="margin-top:0;color:#1e40af;font-size:20px;margin-bottom:12px;">💎 Pro-Only Insight</h3>
        <p style="font-size:18px;line-height:1.7;color:#374151;margin:0;">{pro_insight}</p>
      </div>

      <div style="background:#f0fdf4;border:1px solid #22c55e;padding:20px;border-radius:6px;margin-bottom:15px;width:100%;">
        <p style="font-size:17px;line-height:1.6;color:#166534;margin:0;">
          <span style="color:#166534;font-weight:bold;">🟢 DO:</span> <span style="color:#166534;">{pro_do}</span>
        </p>
      </div>
      <div style="background:#fef2f2;border:1px solid #ef4444;padding:20px;border-radius:6px;margin-bottom:35px;width:100%;">
        <p style="font-size:17px;line-height:1.6;color:#991b1b;margin:0;">
          <span style="color:#991b1b;font-weight:bold;">🔴 DON'T:</span> <span style="color:#991b1b;">{pro_dont}</span>
        </p>
      </div>

      <div style="background:#fffbeb;border:1px solid #f59e0b;padding:15px;border-radius:6px;margin-bottom:30px;">
        <p style="font-size:14px;color:#92400e;margin:0;text-align:center;">
          🔒 Want institutional-grade analysis, The Titan's Playbook, and VIP Action Plans? <strong>Upgrade to VIP.</strong>
        </p>
      </div>
      {_footer(takeaway, ps)}"""


# ── VIP (100%) — 풀 기관급 ──
def build_vip_html(author, tf, summary, tiktok, headline, depth, flow, raw, category, takeaway, ps):
    l1, v1, l2, v2, l3, v3 = parse_graph_data(extract_tag(raw, "GRAPH_DATA"), category)

    vip_radar = extract_tag(raw, "VIP_RADAR")
    vip_c1 = extract_tag(raw, "VIP_C1")
    vip_c2 = extract_tag(raw, "VIP_C2")
    vip_c3 = extract_tag(raw, "VIP_C3")
    vip_t1 = extract_tag(raw, "VIP_T1")
    vip_t2 = extract_tag(raw, "VIP_T2")
    vip_t3 = extract_tag(raw, "VIP_T3")
    vip_t4 = extract_tag(raw, "VIP_T4")
    vip_do = extract_tag(raw, "VIP_DO")
    vip_dont = extract_tag(raw, "VIP_DONT")

    COLORS = ["#e74c3c", "#f59e0b", "#10b981"]

    def gauge(label, val, color):
        return f"""
        <div style="margin-bottom:20px;width:100%;">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span style="font-size:16px;font-weight:600;color:#4b5563;">{label}</span>
            <span style="font-size:16px;font-weight:700;color:{color};">{val}%</span>
          </div>
          <div style="width:100%;background:#e5e7eb;border-radius:6px;height:12px;overflow:hidden;">
            <div style="width:{val}%;background:{color};height:100%;"></div>
          </div>
        </div>"""

    def playbook(num, title, body, extra=""):
        return f"""
        <div style="background:#f8fafc;border:1px solid #e5e7eb;padding:25px;border-radius:6px;margin-bottom:25px;width:100%;">
          <h3 style="color:#1a252c;margin-top:0;font-size:22px;margin-bottom:15px;">{num}. {title}</h3>
          {extra}
          <p style="font-size:18px;line-height:1.7;color:#4b5563;margin-bottom:0;{'margin-top:25px;' if extra else ''}">{body}</p>
        </div>"""

    alloc_bar = """
    <div style="margin:25px 0;width:100%;">
      <div style="display:flex;width:100%;height:32px;border-radius:6px;overflow:hidden;">
        <div style="width:60%;background:#1a252c;color:#ffffff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;">STOCKS 60%</div>
        <div style="width:30%;background:#64748b;color:#ffffff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;">SAFE 30%</div>
        <div style="width:10%;background:#b8974d;color:#ffffff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;">CASH 10%</div>
      </div>
      <p style="font-size:14px;color:#9ca3af;margin:10px 0 0;text-align:center;font-style:italic;">* Mechanically rebalance to maintain this absolute ratio.</p>
    </div>"""

    # ✅ v3: Sector Radar (신규 VIP 전용)
    radar_html = ""
    if vip_radar:
        radar_lines = [line.strip() for line in vip_radar.split("\n") if line.strip()]
        radar_items = ""
        for line in radar_lines[:4]:
            is_bull = "bullish" in line.lower()
            dot_color = "#10b981" if is_bull else "#ef4444"
            radar_items += f'<p style="font-size:16px;color:#374151;margin:8px 0;line-height:1.5;"><span style="color:{dot_color};font-size:20px;">●</span> <span style="color:#374151;">{line}</span></p>'
        radar_html = f"""
        <div style="background:#fefce8;border:2px solid #eab308;padding:25px;border-radius:8px;margin-bottom:35px;width:100%;">
          <h3 style="margin-top:0;color:#854d0e;font-size:20px;margin-bottom:15px;">🎯 VIP Sector Radar</h3>
          {radar_items}
        </div>"""

    return f"""
    <div style="{MAIN}">
      {_header(author, tf, "VIP EXCLUSIVE")}
      <h2 style="font-family:Georgia,serif;font-size:24px;color:#1a252c;margin-top:0;margin-bottom:15px;">Executive Summary</h2>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:35px;">{summary}</p>

      <div style="background:#f1f3f5;border-left:5px solid #8e44ad;padding:20px;border-radius:6px;margin-bottom:40px;width:100%;">
        <h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:10px;">📱 Viral Social Insights</h3>
        <p style="font-size:18px;line-height:1.6;color:#4b5563;margin:0;">{tiktok}</p>
      </div>

      <h2 style="font-family:Georgia,serif;font-size:26px;color:#1a252c;margin-bottom:15px;">Market Drivers &amp; Insights</h2>
      <strong style="font-size:22px;color:#1a252c;display:block;margin-bottom:12px;">{headline}</strong>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:20px;">{depth}</p>

      <div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:6px;margin-bottom:40px;box-shadow:0 2px 4px rgba(0,0,0,.05);width:100%;">
        <strong style="font-size:18px;color:#b8974d;text-transform:uppercase;letter-spacing:.5px;">💡 Quick Flow:</strong>
        <span style="font-size:18px;color:#1a252c;display:block;margin-top:5px;font-weight:bold;">{flow}</span>
      </div>

      <div style="margin:40px 0 30px;padding:25px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px;width:100%;">
        <h3 style="margin-top:0;color:#1a252c;font-size:20px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #e5e7eb;padding-bottom:12px;margin-bottom:25px;">📊 Key Market Indicators</h3>
        {gauge(l1, v1, COLORS[0])}
        {gauge(l2, v2, COLORS[1])}
        {gauge(l3, v3, COLORS[2])}
      </div>

      {radar_html}

      <h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:25px;border-bottom:2px solid #b8974d;padding-bottom:10px;display:inline-block;">VIP Exclusive: Macro &amp; Flow Analysis</h2>

      <div style="background:#fff;border:1px solid #e5e7eb;border-left:5px solid #1a252c;padding:25px;border-radius:6px;margin-bottom:40px;width:100%;box-shadow:0 4px 6px rgba(0,0,0,.05);">
        <p style="font-size:17px;color:#b8974d;text-transform:uppercase;font-weight:bold;margin-top:0;margin-bottom:20px;letter-spacing:.5px;">[Institutional Technical Outlook]</p>
        <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:15px;">{vip_c1}</p>
        <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:15px;">{vip_c2}</p>
        <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:0;">{vip_c3}</p>
      </div>

      <h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:10px;border-bottom:2px solid #b8974d;padding-bottom:10px;display:inline-block;">The Titan's Playbook</h2>
      <p style="font-size:17px;color:#6b7280;margin-bottom:30px;font-style:italic;">Strategic manual for the top 1% navigating current conditions.</p>

      {playbook("1", "The Generational Bargain (Fear vs. Greed)", vip_t1)}
      {playbook("2", "The 60/30/10 Seesaw (Asset Allocation)", vip_t2, alloc_bar)}
      {playbook("3", "The Global Shield (US Dollar &amp; Market)", vip_t3)}
      {playbook("4", "Survival Mechanics (Split Buying &amp; Mental Peace)", vip_t4)}

      <div style="background:#1a252c;padding:35px;border-radius:8px;margin:45px 0 40px;width:100%;box-shadow:0 6px 12px rgba(0,0,0,.15);">
        <h3 style="color:#b8974d;margin-top:0;font-size:24px;margin-bottom:25px;border-bottom:1px solid #4b5563;padding-bottom:15px;">✅ Today's VIP Action Plan</h3>
        <div style="background:#22332b;border-radius:6px;padding:20px;margin-bottom:20px;">
          <p style="font-size:18px;line-height:1.7;color:#d1fae5;margin:0;">
            <span style="color:#34d399;font-weight:bold;font-size:20px;">🟢 DO (Action):</span>
          </p>
          <p style="font-size:17px;line-height:1.7;color:#d1fae5;margin:10px 0 0 0;">{vip_do}</p>
        </div>
        <div style="background:#3b1c1c;border-radius:6px;padding:20px;">
          <p style="font-size:18px;line-height:1.7;color:#fecaca;margin:0;">
            <span style="color:#f87171;font-weight:bold;font-size:20px;">🔴 DON'T (Avoid):</span>
          </p>
          <p style="font-size:17px;line-height:1.7;color:#fecaca;margin:10px 0 0 0;">{vip_dont}</p>
        </div>
      </div>
      {_footer(takeaway, ps)}"""


# ──────────────────────────────────────────────
# 7. 메인
# ──────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  🚀 Warm Insight v3 — Premium Quality Engine")
    print("=" * 50)

    total = success = fail = 0

    for category, urls in CATEGORIES.items():
        print(f"\n━━━ [{category}] ━━━")
        all_news = get_category_news(urls, count=20)
        if len(all_news) < 3:
            print(f"  ⚠️ 뉴스 부족 ({len(all_news)}건) → 건너뜀")
            continue

        for task in TASKS:
            tier = task["tier"]
            count = task["count"]
            if len(all_news) < count:
                print(f"  ⚠️ 남은 뉴스 부족 → {tier} 건너뜀")
                break

            target = [all_news.pop(0) for _ in range(count)]
            total += 1
            print(f"\n  🔹 [{TIER_LABELS.get(tier, tier)}] {count}개 뉴스 분석 중...")

            title, img_prompt, html, excerpt = run_gemini(target, category, tier)

            if not html or not title:
                print(f"  ⛔ AI 실패 → 건너뜀")
                fail += 1
                continue

            img_url = None
            if img_prompt:
                ib = generate_thumbnail(img_prompt)
                if ib:
                    img_url = upload_image_to_ghost(ib)

            publish_to_ghost(title, html, category, tier, img_url, excerpt)
            success += 1

            sl = TIER_SLEEP.get(tier, 20)
            print(f"  ⏳ {sl}초 대기...")
            time.sleep(sl)

    print("\n" + "=" * 50)
    print(f"  📊 총 {total}건 | ✅ {success} 성공 | ❌ {fail} 실패")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n❌ 시스템 에러")
        traceback.print_exc()
        sys.exit(1)
