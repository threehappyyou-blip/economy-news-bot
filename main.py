# -*- coding: utf-8 -*-
"""
Warm Insight v2 — Full Refactor
================================
변경사항 요약:
  1. visibility 티어별 분리 (public / members / paid)
  2. Gemini 모델 fallback + 상세 에러 로깅
  3. GRAPH_DATA 파싱 견고화 (하이픈·콜론 오염 방지)
  4. HTML 정리 (인라인 공백 압축, 크기 경고)
  5. 티어별 rate-limit 대기 시간 차등
  6. 재시도(retry) 로직 내장
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
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL      = os.environ.get("GHOST_API_URL", "").rstrip("/")
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
    {"tier": "Premium",       "count": 2},
    {"tier": "Royal Premium", "count": 3},
]

TIER_LABELS = {
    "Basic":         "🌱 Free",
    "Premium":       "💎 Pro",
    "Royal Premium": "👑 VIP",
}

# ✅ 티어별 Ghost visibility 매핑
# 구독자 1000명 달성 전까지는 전부 공개 운영
# 달성 후 아래 주석을 해제하면 유료 전환 완료!
TIER_VISIBILITY = {
    "Basic":         "public",   # 누구나 열람
    "Premium":       "public",   # TODO → "members" (무료 회원가입 후 열람)
    "Royal Premium": "public",   # TODO → "paid"    (유료 구독자만 열람)
}

# ✅ FIX #5 — 티어별 대기 시간 (Gemini rate-limit 대응)
TIER_SLEEP = {
    "Basic":         20,
    "Premium":       35,
    "Royal Premium": 45,
}

# Gemini 모델 우선순위 (실패 시 다음 모델로 fallback)
MODEL_PRIORITY = {
    "Royal Premium": ["gemini-2.5-pro", "gemini-2.5-flash"],
    "Premium":       ["gemini-2.5-pro", "gemini-2.5-flash"],
    "Basic":         ["gemini-2.5-flash"],
}

EXPERT_PERSONA = {
    "Politics": "a veteran US political expert",
    "Tech":     "a veteran US technology expert",
    "Health":   "a veteran US healthcare expert",
    "Energy":   "a veteran US energy expert",
}

# ──────────────────────────────────────────────
# 1. 프롬프트 템플릿
# ──────────────────────────────────────────────
PROMPT_TEMPLATE = """
[Goal] Write a highly insightful blog post in ENGLISH for the '[CATEGORY]' section of the 'Warm Insight' website.
Target Audience: [TIER] Subscribers.

You are [PERSONA].

CRITICAL RULES:
1. Write ENTIRELY in ENGLISH.
2. For diagrams, MUST use horizontal "Emoji Flows" (e.g., A 📈 ➡️ B 💥).
3. TIKTOK INFLUENCE: Create a 'Viral Social Insights' section based on these vibes: [TIKTOK_LINKS]

OUTPUT FORMAT:
You MUST return your response STRICTLY inside the following XML tags. DO NOT output any text outside these tags.

<TITLE>Catchy Title Here</TITLE>
<IMAGE_PROMPT>Simple English prompt for 3D abstract cinematic image</IMAGE_PROMPT>
<EXCERPT>1 sentence summary</EXCERPT>
<SUMMARY>3 sentence summary of the news</SUMMARY>
<TIKTOK>Translate the news into a super-engaging TikTok style analogy</TIKTOK>
<HEADLINE>Headline of the main insight</HEADLINE>
<DEPTH>[DEPTH_INSTRUCTION]</DEPTH>
<FLOW>Emoji Flow Diagram (e.g. A 📈 ➡️ B 💥)</FLOW>
[VIP_XML_TAGS]
<TAKEAWAY>A comforting, actionable takeaway</TAKEAWAY>
<PS>A very short personal thought</PS>

Raw News to Analyze:
[NEWS_ITEMS]
"""

VIP_XML_INSTRUCTIONS = """
<GRAPH_DATA>CRITICAL INSTRUCTION: Analyze the specific news and invent 3 UNIQUE, HIGHLY RELEVANT metrics.
Assign a 0-100 score to each. FORMAT STRICTLY AS:
MetricName1|Score1|MetricName2|Score2|MetricName3|Score3
Use ONLY the pipe character | as separator. Do NOT use colons or hyphens inside metric names.
Do NOT copy the example. Create completely original metrics.
Example format reference: Inflation Anxiety|82|Recession Odds|45|Consumer Confidence|70</GRAPH_DATA>
<VIP_C1>Write PARAGRAPH 1: Deeply analyze RSI, Moving Averages. At least 5 sentences.</VIP_C1>
<VIP_C2>Write PARAGRAPH 2: Analyze Macro data, yield curves. At least 5 sentences.</VIP_C2>
<VIP_C3>Write PARAGRAPH 3: Conclude with what 'Smart Money' is doing.</VIP_C3>
<VIP_T1>The Generational Bargain: Apply to today's news (Fear & Greed Index). Detailed paragraph.</VIP_T1>
<VIP_T2>The 60/30/10 Seesaw: How to mechanically rebalance today. Detailed paragraph.</VIP_T2>
<VIP_T3>The Global Shield: Explain why holding US Assets is crucial right now. Detailed paragraph.</VIP_T3>
<VIP_T4>Survival Mechanics: When to use DCA and why selling 50% during panic is key. Detailed paragraph.</VIP_T4>
<VIP_DO>2 highly specific, actionable steps.</VIP_DO>
<VIP_DONT>1 specific mistake to avoid.</VIP_DONT>
"""

# 카테고리별 fallback 지표 풀
FALLBACK_LABELS = {
    "Economy":  ["Inflation Anxiety","Recession Probability","Consumer Resilience",
                 "Market Volatility","Rate Cut Expectation","Liquidity Squeeze"],
    "Politics": ["Policy Uncertainty","Regulatory Risk","Geopolitical Tension",
                 "Market Optimism","Legislative Impact","Election Volatility"],
    "Tech":     ["Innovation Momentum","Regulatory Headwinds","Earnings Growth",
                 "AI Adoption Rate","Sector Valuation","Tech Monopoly Risk"],
    "Health":   ["Pharma Innovation","Healthcare Affordability","Policy Confidence",
                 "R&D Investment","Market Sentiment","Biotech Speculation"],
    "Energy":   ["Supply Squeeze Risk","Green Transition Pace","Fossil Fuel Demand",
                 "Geopolitical Shock Risk","Energy Cost Burden","OPEC Influence"],
}

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


# ✅ FIX #3 — GRAPH_DATA 파싱 견고화
def parse_graph_data(raw: str, category: str):
    """
    AI 응답에서 'Name|Score|Name|Score|Name|Score' 를 안전하게 추출.
    실패하거나 예시를 베낀 경우 카테고리별 랜덤 fallback 반환.
    """
    KNOWN_LAZY = {"Sector Stress", "Market Fear", "Growth Outlook", "Policy Risk"}

    # 파이프만으로 분리 (콜론·하이픈 치환 제거)
    parts = [p.strip() for p in raw.split("|") if p.strip()]

    if len(parts) >= 6:
        labels_found = {parts[0], parts[2], parts[4]}
        if labels_found & KNOWN_LAZY:
            parts = []  # 베낀 것으로 판정 → fallback

    if len(parts) >= 6:
        try:
            v1 = int(re.sub(r"\D", "", parts[1]))
            v2 = int(re.sub(r"\D", "", parts[3]))
            v3 = int(re.sub(r"\D", "", parts[5]))
            return parts[0], v1, parts[2], v2, parts[4], v3
        except (ValueError, IndexError):
            pass

    # fallback: 카테고리별 랜덤 지표
    pool = FALLBACK_LABELS.get(category, FALLBACK_LABELS["Economy"])
    labels = random.sample(pool, 3)
    return (
        labels[0], random.randint(55, 92),
        labels[1], random.randint(35, 75),
        labels[2], random.randint(45, 88),
    )


# ✅ FIX #4 — HTML 정리 (공백 압축, 크기 경고)
def sanitize_html(html: str) -> str:
    html = html.replace("\n", " ").replace("\r", "")
    html = re.sub(r"\s{2,}", " ", html)
    size_kb = len(html.encode("utf-8")) / 1024
    if size_kb > 500:
        print(f"  ⚠️ HTML 크기 경고: {size_kb:.0f} KB — Ghost 업로드 시 문제 가능")
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
    """✅ FIX #1 — visibility를 티어별로 분리하여 발행"""
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
            # ✅ FIX #2 — 상세 에러 본문 출력
            try:
                err_body = resp.json()
                print(f"     Ghost 에러 상세: {json.dumps(err_body, indent=2, ensure_ascii=False)[:1000]}")
            except Exception:
                print(f"     응답 본문: {resp.text[:500]}")
    except Exception as e:
        print(f"  ❌ 발행 통신 에러: {e}")
        traceback.print_exc()


# ──────────────────────────────────────────────
# 4. 썸네일 생성
# ──────────────────────────────────────────────
def generate_thumbnail(image_prompt: str) -> bytes | None:
    # Plan A: Google Imagen 3
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        result = client.models.generate_images(
            model="imagen-3.0-generate-001",
            prompt=f"{image_prompt}, highly detailed, cinematic lighting, 8k, professional financial tone",
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type="image/jpeg",
            ),
        )
        if result.generated_images:
            print("  ✅ Imagen 3 썸네일 생성 완료")
            return result.generated_images[0].image.image_bytes
    except Exception as e:
        print(f"  ⚠️ Imagen 실패 → 대체 이미지 사용: {e}")

    # Plan B: Picsum 랜덤 이미지
    try:
        resp = requests.get(
            f"https://picsum.photos/seed/{random.randint(1,9999)}/1280/720",
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────
# 5. Gemini 분석 (핵심 엔진)
# ──────────────────────────────────────────────
def call_gemini_with_retry(client, model: str, prompt: str, max_retries: int = 2) -> str | None:
    """✅ FIX #2 & #6 — 재시도 로직 + 상세 에러 로깅"""
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            return str(resp.text)
        except Exception as e:
            print(f"    ⚠️ Gemini 호출 실패 (모델={model}, 시도={attempt}/{max_retries}): {type(e).__name__}: {e}")
            if attempt < max_retries:
                wait = 10 * attempt
                print(f"    ⏳ {wait}초 후 재시도...")
                time.sleep(wait)
    return None


def analyze_with_gemini(news_items, category, tier):
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_news = "\n".join(news_items)

    # 프롬프트 조립
    if tier == "Basic":
        depth = "Explain what happened simply using ELI5."
        vip_xml = ""
    elif tier == "Premium":
        depth = ("<strong>🧐 WHY:</strong> Explain using behavioral economics.<br><br>"
                 "<strong>🐑 THINK:</strong> Explain the irrational market psychology.")
        vip_xml = ""
    else:
        depth = ("<strong>🧐 WHY:</strong> Macroeconomic reason.<br><br>"
                 "<strong>🐑 THINK:</strong> Herd Behavior.<br><br>"
                 "<strong>🦅 DIFFERENT THINK:</strong> Contrarian View.")
        vip_xml = VIP_XML_INSTRUCTIONS

    persona = EXPERT_PERSONA.get(category, "a veteran US Wall Street expert")

    prompt = (PROMPT_TEMPLATE
              .replace("[CATEGORY]", category)
              .replace("[TIER]", tier)
              .replace("[PERSONA]", persona)
              .replace("[TIKTOK_LINKS]", TIKTOK_LINKS)
              .replace("[VIP_XML_TAGS]", vip_xml)
              .replace("[DEPTH_INSTRUCTION]", depth)
              .replace("[NEWS_ITEMS]", selected_news))

    # ✅ FIX #2 — 모델 fallback 체인
    models = MODEL_PRIORITY.get(tier, ["gemini-2.5-flash"])
    raw_text = None
    used_model = None

    for model_name in models:
        print(f"    [AI] {tier} → {model_name} 시도 중...")
        raw_text = call_gemini_with_retry(client, model_name, prompt)
        if raw_text:
            used_model = model_name
            break
        print(f"    ❌ {model_name} 최종 실패, 다음 모델로 전환...")

    if not raw_text:
        print(f"  ⛔ 모든 모델 실패: category={category}, tier={tier}")
        return None, None, None, None

    print(f"    ✅ AI 분석 완료 (모델: {used_model})")

    # 태그 추출
    title_raw    = extract_tag(raw_text, "TITLE")
    image_prompt = extract_tag(raw_text, "IMAGE_PROMPT") or f"Abstract 3D cinematic rendering of global {category}."
    excerpt      = extract_tag(raw_text, "EXCERPT") or "Insightful financial analysis for your future."
    summary      = extract_tag(raw_text, "SUMMARY")
    tiktok       = extract_tag(raw_text, "TIKTOK")
    headline     = extract_tag(raw_text, "HEADLINE")
    depth_text   = extract_tag(raw_text, "DEPTH")
    flow         = extract_tag(raw_text, "FLOW")
    takeaway     = extract_tag(raw_text, "TAKEAWAY")
    ps           = extract_tag(raw_text, "PS")

    pretty_tier = TIER_LABELS.get(tier, tier)
    title = f"[{pretty_tier}] {title_raw}" if title_raw else f"({tier}) Daily {category} Insight"
    now = datetime.now()
    time_short = now.strftime("%I:%M %p")
    time_full  = now.strftime("%B %d, %Y at %I:%M %p (UTC)")
    author     = "Ethan Cole &amp; The Warm Insight Panel"
    excerpt_with_time = f"⏰ {time_short} | {excerpt}"

    # ── HTML 조립 ──
    html = build_html_shell(author, time_full, summary, tiktok, headline, depth_text, flow, takeaway, ps)

    if tier == "Royal Premium":
        html += build_vip_section(raw_text, category)

    html += build_footer(takeaway, ps)

    # ✅ FIX #4
    html = sanitize_html(html)

    return title, image_prompt, html, excerpt_with_time


# ──────────────────────────────────────────────
# 6. HTML 빌더 (가독성 분리)
# ──────────────────────────────────────────────
S = {  # 스타일 사전
    "main":       "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;",
    "header":     "border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;padding:12px 0;margin-bottom:30px;width:100%;",
    "header_p":   "margin:0;font-size:14px;color:#4b5563;text-transform:uppercase;letter-spacing:.5px;",
    "summary_p":  "font-size:18px;line-height:1.7;color:#374151;margin-bottom:35px;",
    "tiktok_div": "background:#f1f3f5;border-left:5px solid #8e44ad;padding:20px;border-radius:6px;margin-bottom:40px;width:100%;",
    "tiktok_p":   "font-size:18px;line-height:1.6;color:#4b5563;margin:0;",
    "h2":         "font-family:Georgia,serif;font-size:26px;color:#1a252c;margin-bottom:15px;",
    "depth_p":    "font-size:18px;line-height:1.7;color:#374151;margin-bottom:20px;",
    "flow_div":   "background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:6px;margin-bottom:40px;box-shadow:0 2px 4px rgba(0,0,0,.05);width:100%;",
    "flow_span":  "font-size:18px;color:#1a252c;display:block;margin-top:5px;font-weight:bold;",
    "takeaway_p": "font-size:18px;line-height:1.6;color:#374151;",
    "ps_div":     "margin-top:30px;background:#1a252c;padding:20px;border-radius:6px;border-left:4px solid #b8974d;color:#e5e7eb;",
    "ps_strong":  "font-size:18px;color:#b8974d;margin-right:5px;",
    "ps_p":       "font-size:18px;line-height:1.6;color:#e5e7eb;margin:0;",
    # VIP 전용
    "chart_div":  "margin:40px 0 30px;padding:25px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px;width:100%;",
    "gauge_bg":   "width:100%;background:#e5e7eb;border-radius:6px;height:12px;overflow:hidden;",
    "vip_macro":  "background:#fff;border:1px solid #e5e7eb;border-left:5px solid #1a252c;padding:25px;border-radius:6px;margin-bottom:40px;width:100%;box-shadow:0 4px 6px rgba(0,0,0,.05);",
    "playbook":   "background:#f8fafc;border:1px solid #e5e7eb;padding:25px;border-radius:6px;margin-bottom:25px;width:100%;",
    "action":     "background:#1a252c;color:#fff;padding:35px;border-radius:8px;margin:45px 0 40px;width:100%;box-shadow:0 6px 12px rgba(0,0,0,.15);",
}


def build_html_shell(author, time_full, summary, tiktok, headline, depth, flow, takeaway, ps) -> str:
    return f"""
    <div style="{S['main']}">
      <div style="{S['header']}">
        <p style="{S['header_p']}"><strong style="color:#1a252c;">By {author}</strong> &nbsp;|&nbsp; {time_full}</p>
      </div>
      <h2 style="font-family:Georgia,serif;font-size:24px;color:#1a252c;margin-top:0;margin-bottom:15px;">Executive Summary</h2>
      <p style="{S['summary_p']}">{summary}</p>
      <div style="{S['tiktok_div']}">
        <h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:10px;">📱 Viral Social Insights</h3>
        <p style="{S['tiktok_p']}">{tiktok}</p>
      </div>
      <h2 style="{S['h2']}">Market Drivers &amp; Insights</h2>
      <strong style="font-size:22px;color:#1a252c;display:block;margin-bottom:12px;">{headline}</strong>
      <p style="{S['depth_p']}">{depth}</p>
      <div style="{S['flow_div']}">
        <strong style="font-size:18px;color:#b8974d;text-transform:uppercase;letter-spacing:.5px;">💡 Quick Flow:</strong>
        <span style="{S['flow_span']}">{flow}</span>
      </div>
    """


def build_vip_section(raw_text: str, category: str) -> str:
    l1, v1, l2, v2, l3, v3 = parse_graph_data(extract_tag(raw_text, "GRAPH_DATA"), category)

    COLORS = ["#e74c3c", "#f59e0b", "#10b981"]

    def gauge(label, value, color):
        return f"""
        <div style="margin-bottom:20px;width:100%;">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span style="font-size:16px;font-weight:600;color:#4b5563;">{label}</span>
            <span style="font-size:16px;font-weight:700;color:{color};">{value}%</span>
          </div>
          <div style="{S['gauge_bg']}"><div style="width:{value}%;background:{color};height:100%;"></div></div>
        </div>"""

    chart = f"""
    <div style="{S['chart_div']}">
      <h3 style="margin-top:0;color:#1a252c;font-size:20px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #e5e7eb;padding-bottom:12px;margin-bottom:25px;">📊 Key Market Indicators</h3>
      {gauge(l1, v1, COLORS[0])}
      {gauge(l2, v2, COLORS[1])}
      {gauge(l3, v3, COLORS[2])}
    </div>"""

    vip_c1 = extract_tag(raw_text, "VIP_C1")
    vip_c2 = extract_tag(raw_text, "VIP_C2")
    vip_c3 = extract_tag(raw_text, "VIP_C3")
    vip_t1 = extract_tag(raw_text, "VIP_T1")
    vip_t2 = extract_tag(raw_text, "VIP_T2")
    vip_t3 = extract_tag(raw_text, "VIP_T3")
    vip_t4 = extract_tag(raw_text, "VIP_T4")
    vip_do = extract_tag(raw_text, "VIP_DO")
    vip_dont = extract_tag(raw_text, "VIP_DONT")

    alloc = """
    <div style="margin:25px 0;width:100%;">
      <div style="display:flex;width:100%;height:32px;border-radius:6px;overflow:hidden;">
        <div style="width:60%;background:#1a252c;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;">STOCKS 60%</div>
        <div style="width:30%;background:#64748b;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;">SAFE 30%</div>
        <div style="width:10%;background:#b8974d;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;">CASH 10%</div>
      </div>
      <p style="font-size:14px;color:#9ca3af;margin:10px 0 0;text-align:center;font-style:italic;">* Mechanically rebalance to maintain this absolute ratio.</p>
    </div>"""

    def playbook_card(num, title, body, extra=""):
        return f"""
        <div style="{S['playbook']}">
          <h3 style="color:#1a252c;margin-top:0;font-size:22px;margin-bottom:15px;">{num}. {title}</h3>
          {extra}
          <p style="font-size:18px;line-height:1.7;color:#4b5563;margin-bottom:0;{'margin-top:25px;' if extra else ''}">{body}</p>
        </div>"""

    return f"""
    {chart}

    <h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:25px;border-bottom:2px solid #b8974d;padding-bottom:10px;display:inline-block;">VIP Exclusive: Macro &amp; Flow Analysis</h2>

    <div style="{S['vip_macro']}">
      <p style="font-size:17px;color:#b8974d;text-transform:uppercase;font-weight:bold;margin-top:0;margin-bottom:20px;letter-spacing:.5px;">[Institutional Technical Outlook]</p>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:15px;">{vip_c1}</p>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:15px;">{vip_c2}</p>
      <p style="font-size:18px;line-height:1.7;color:#374151;margin-bottom:0;">{vip_c3}</p>
    </div>

    <h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:10px;border-bottom:2px solid #b8974d;padding-bottom:10px;display:inline-block;">The Titan's Playbook</h2>
    <p style="font-size:17px;color:#6b7280;margin-bottom:30px;font-style:italic;">Strategic manual for the top 1% navigating current conditions.</p>

    {playbook_card("1","The Generational Bargain (Fear vs. Greed)", vip_t1)}
    {playbook_card("2","The 60/30/10 Seesaw (Asset Allocation)", vip_t2, alloc)}
    {playbook_card("3","The Global Shield (US Dollar &amp; Market)", vip_t3)}
    {playbook_card("4","Survival Mechanics (Split Buying &amp; Mental Peace)", vip_t4)}

    <div style="{S['action']}">
      <h3 style="color:#b8974d;margin-top:0;font-size:24px;margin-bottom:25px;border-bottom:1px solid #374151;padding-bottom:15px;">✅ Today's VIP Action Plan</h3>
      <p style="font-size:18px;line-height:1.7;color:#e5e7eb;margin-bottom:20px;"><strong>🟢 DO (Action):</strong> {vip_do}</p>
      <p style="font-size:18px;line-height:1.6;color:#e5e7eb;margin-bottom:0;"><strong>🔴 DON'T (Avoid):</strong> {vip_dont}</p>
    </div>
    """


def build_footer(takeaway: str, ps: str) -> str:
    return f"""
      <hr style="border:0;height:1px;background:#e5e7eb;margin:40px 0;">
      <h2 style="font-family:Georgia,serif;font-size:26px;color:#1a252c;margin-bottom:15px;">Today's Warm Insight</h2>
      <p style="{S['takeaway_p']}">{takeaway}</p>
      <div style="{S['ps_div']}">
        <p style="{S['ps_p']}"><strong style="{S['ps_strong']}">P.S.</strong> {ps}</p>
      </div>
      <p style="font-size:14px;color:#9ca3af;margin-top:35px;text-align:center;text-transform:uppercase;letter-spacing:.5px;">
        Disclaimer: This article is for informational purposes only. All decisions are your own.
      </p>
    </div>
    """


# ──────────────────────────────────────────────
# 7. 메인 실행
# ──────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  🚀 Warm Insight v2 — Refactored Engine")
    print("=" * 50)

    total, success, fail = 0, 0, 0

    for category, urls in CATEGORIES.items():
        print(f"\n━━━ [{category}] 시작 ━━━")
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

            target_news = [all_news.pop(0) for _ in range(count)]
            total += 1
            print(f"\n  🔹 [{pretty(tier)}] {count}개 뉴스 분석 중...")

            title, img_prompt, html, excerpt = analyze_with_gemini(target_news, category, tier)

            if not html or not title:
                print(f"  ⛔ AI 분석 실패 → 발행 건너뜀")
                fail += 1
                continue

            # 썸네일
            img_url = None
            if img_prompt:
                img_bytes = generate_thumbnail(img_prompt)
                if img_bytes:
                    img_url = upload_image_to_ghost(img_bytes)

            publish_to_ghost(title, html, category, tier, img_url, excerpt)
            success += 1

            # ✅ FIX #5 — 티어별 대기
            sleep_sec = TIER_SLEEP.get(tier, 20)
            print(f"  ⏳ {sleep_sec}초 대기 (rate-limit 보호)...")
            time.sleep(sleep_sec)

    print("\n" + "=" * 50)
    print(f"  📊 결과: 총 {total}건 | ✅ 성공 {success} | ❌ 실패 {fail}")
    print("=" * 50)


def pretty(tier):
    return TIER_LABELS.get(tier, tier)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
