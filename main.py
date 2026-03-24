# -*- coding: utf-8 -*-
import os
import sys
import traceback
import time
import requests
import jwt
import base64
import urllib.parse
import random
import re
from datetime import datetime
import feedparser
from google import genai
from google.genai import types

print("=======================================")
print(" 🚀 40년 멘토 + 시각적 차트/그래프 자동생성 + 가로스크롤 박멸 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다.")
    sys.exit(1)

GHOST_API_URL = str(GHOST_API_URL).rstrip('/')

# 🚨 [카테고리 세팅]
CATEGORIES = dict()
cat_eco = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "https://finance.yahoo.com/news/rssindex"]
CATEGORIES.update({"Economy": cat_eco})
cat_pol = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113"]
CATEGORIES.update({"Politics": cat_pol})
cat_tech = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"]
CATEGORIES.update({"Tech": cat_tech})
cat_health = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108"]
CATEGORIES.update({"Health": cat_health})
cat_energy = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810"]
CATEGORIES.update({"Energy": cat_energy})

TIKTOK_LINKS = (
    "https://lite.tiktok.com/t/ZSuGXKdsU/ "
    "https://lite.tiktok.com/t/ZSu9GYwy5/ "
    "https://lite.tiktok.com/t/ZSuxhPSBR/ "
    "https://lite.tiktok.com/t/ZSuXQwnvm/"
)

TASKS = [
    {"tier": "Basic", "count": 2},
    {"tier": "Premium", "count": 2},
    {"tier": "Royal Premium", "count": 3}
]

TIER_LABELS = {"Basic": "🌱 Free", "Premium": "💎 Pro", "Royal Premium": "👑 VIP"}

# 🚨 AI 프롬프트 (XML 형식 유지)
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

# 🚨 VIP에만 들어가는 시각적 데이터(GRAPH_DATA) 추출 명령 추가
VIP_XML_INSTRUCTIONS = """
<GRAPH_DATA>Extract 3 key metrics, probabilities, or sentiment indicators from the news to visualize. Format EXACTLY as: Label1|Value1|Label2|Value2|Label3|Value3. (Values must be numbers 0-100. Example: Market Fear|75|Rate Cut Probability|40|Tech Resilience|85)</GRAPH_DATA>
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

def extract_tag(text, tag_name):
    match = re.search(f"<{tag_name}>(.*?)</{tag_name}>", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def get_category_news(urls, count=20):
    news_list = []
    seen_titles = set()
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title_text = getattr(entry, 'title', '')
                if title_text in seen_titles: continue
                summary_text = getattr(entry, 'summary', '')
                news_list.append("- " + str(title_text) + ": " + str(summary_text))
                seen_titles.add(title_text)
                if len(news_list) >= count: break
        except: continue
            
    final_news = []
    for _ in range(count):
        if len(news_list) > 0:
            final_news.append(news_list.pop(0))
    return final_news

def analyze_with_gemini(news_items, category, tier):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        selected_news = "\n".join(news_items)
        model_name = "gemini-2.5-flash"  
        
        vip_xml = ""
        if tier == "Basic":
            depth_instruction = "Explain what happened simply using ELI5."
        elif tier == "Premium":
            depth_instruction = "<strong>🧐 WHY:</strong> Explain using behavioral economics.<br><br><strong>🐑 THINK:</strong> Explain the irrational market psychology."
        else: # Royal Premium
            depth_instruction = "<strong>🧐 WHY:</strong> Macroeconomic reason.<br><br><strong>🐑 THINK:</strong> Herd Behavior.<br><br><strong>🦅 DIFFERENT THINK:</strong> Contrarian View."
            vip_xml = VIP_XML_INSTRUCTIONS

        if category == "Politics": expert_persona = "a veteran US political expert"
        elif category == "Tech": expert_persona = "a veteran US technology expert"
        elif category == "Health": expert_persona = "a veteran US healthcare expert"
        elif category == "Energy": expert_persona = "a veteran US energy expert"
        else: expert_persona = "a veteran US Wall Street expert"

        prompt = PROMPT_TEMPLATE.replace("[CATEGORY]", category).replace("[TIER]", tier).replace("[PERSONA]", expert_persona).replace("[TIKTOK_LINKS]", TIKTOK_LINKS).replace("[VIP_XML_TAGS]", vip_xml).replace("[DEPTH_INSTRUCTION]", depth_instruction).replace("[NEWS_ITEMS]", selected_news)
        
        response = client.models.generate_content(model=model_name, contents=prompt)
        raw_text = str(response.text)
        
        title_raw = extract_tag(raw_text, "TITLE")
        image_prompt = extract_tag(raw_text, "IMAGE_PROMPT") or f"Abstract 3D cinematic rendering of global {category}."
        custom_excerpt = extract_tag(raw_text, "EXCERPT") or "Insightful financial analysis for your future."
        summary = extract_tag(raw_text, "SUMMARY")
        tiktok = extract_tag(raw_text, "TIKTOK")
        headline = extract_tag(raw_text, "HEADLINE")
        depth = extract_tag(raw_text, "DEPTH")
        flow = extract_tag(raw_text, "FLOW")
        takeaway = extract_tag(raw_text, "TAKEAWAY")
        ps = extract_tag(raw_text, "PS")

        pretty_tier = TIER_LABELS.get(tier, tier)
        title = f"[{pretty_tier}] {title_raw}" if title_raw else f"({tier}) Daily {category} Insight"
        
        current_time_str = datetime.now().strftime('%B %d, %Y at %I:%M %p (UTC)')
        current_time_short = datetime.now().strftime('%I:%M %p')
        author_name = "Ethan Cole & The Warm Insight Panel"
        
        custom_excerpt_with_time = f"⏰ {current_time_short} | {custom_excerpt}"
        
        # 🚨 가로스크롤을 없앤 기본 레이아웃 (word-break 적용)
        html_content = f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #f2a900; border-radius: 4px; margin-bottom: 25px; word-break: break-word;">
            <p style="margin: 0; font-size: 16px; color: #555; line-height: 1.6; font-family: sans-serif;">
                <strong>✍️ Written by:</strong> {author_name}<br>
                <strong>⏰ Published:</strong> {current_time_str}
            </p>
        </div>
        <p style="font-size: 18px; line-height: 1.6; color: #333; word-break: break-word;">{summary}</p>
        
        <h2>Viral Social Insights 📱</h2>
        <p style="font-size: 18px; line-height: 1.6; color: #333; word-break: break-word;">{tiktok}</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <strong style="font-size: 22px;">{headline}</strong><br><br>
        <p style="font-size: 18px; line-height: 1.6; color: #333; word-break: break-word;">{depth}</p>
        
        <div style="border-left: 4px solid #999; background-color: #f4f4f4; padding: 15px; margin-top: 15px; border-radius: 4px; word-break: break-word;">
            <strong style="font-size: 18px;">💡 Quick Flow:</strong> <span style="font-size: 18px;">{flow}</span>
        </div>
        """

        if tier == "Royal Premium":
            # 🚨 시각적 데이터(그래프) 파싱 로직
            graph_data_raw = extract_tag(raw_text, "GRAPH_DATA")
            parts = [p.strip() for p in graph_data_raw.split('|')]
            if len(parts) == 6:
                l1, v1, l2, v2, l3, v3 = parts
            else:
                l1, v1, l2, v2, l3, v3 = "Market Volatility", "75", "Recession Risk", "40", "Investor Confidence", "60"
            
            # 숫자만 안전하게 추출
            v1 = "".join(filter(str.isdigit, v1)) or "50"
            v2 = "".join(filter(str.isdigit, v2)) or "50"
            v3 = "".join(filter(str.isdigit, v3)) or "50"

            # 📊 차트 디자인 생성 (반응형 바 차트)
            chart_html = f"""
            <div style="background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-top: 40px; margin-bottom: 20px; font-family: sans-serif; word-break: break-word;">
                <h3 style="margin-top: 0; color: #2c3e50; font-size: 20px; margin-bottom: 20px;">📊 Key Market Indicators</h3>
                
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong style="color: #555; font-size: 16px;">{l1}</strong>
                        <span style="color: #c0392b; font-weight: bold; font-size: 16px;">{v1}%</span>
                    </div>
                    <div style="background-color: #e9ecef; border-radius: 10px; height: 14px; width: 100%;">
                        <div style="background-color: #e74c3c; width: {v1}%; height: 100%; border-radius: 10px;"></div>
                    </div>
                </div>

                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong style="color: #555; font-size: 16px;">{l2}</strong>
                        <span style="color: #f39c12; font-weight: bold; font-size: 16px;">{v2}%</span>
                    </div>
                    <div style="background-color: #e9ecef; border-radius: 10px; height: 14px; width: 100%;">
                        <div style="background-color: #f1c40f; width: {v2}%; height: 100%; border-radius: 10px;"></div>
                    </div>
                </div>

                <div style="margin-bottom: 5px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <strong style="color: #555; font-size: 16px;">{l3}</strong>
                        <span style="color: #27ae60; font-weight: bold; font-size: 16px;">{v3}%</span>
                    </div>
                    <div style="background-color: #e9ecef; border-radius: 10px; height: 14px; width: 100%;">
                        <div style="background-color: #2ecc71; width: {v3}%; height: 100%; border-radius: 10px;"></div>
                    </div>
                </div>
            </div>
            """

            # ⚖️ 자산배분 바 디자인 생성
            allocation_html = f"""
            <div style="margin-top: 15px; margin-bottom: 10px;">
                <div style="display: flex; height: 28px; border-radius: 14px; overflow: hidden; margin-bottom: 8px;">
                    <div style="width: 60%; background-color: #3498db; display: flex; align-items: center; justify-content: center; color: white; font-size: 13px; font-weight: bold;">Stocks 60%</div>
                    <div style="width: 30%; background-color: #2ecc71; display: flex; align-items: center; justify-content: center; color: white; font-size: 13px; font-weight: bold;">Safe Assets 30%</div>
                    <div style="width: 10%; background-color: #f1c40f; display: flex; align-items: center; justify-content: center; color: white; font-size: 13px; font-weight: bold;">Cash 10%</div>
                </div>
                <p style="font-size: 14px; color: #888; margin: 0; text-align: center; font-style: italic;">* Mechanically rebalance to maintain this absolute ratio.</p>
            </div>
            """

            vip_c1 = extract_tag(raw_text, "VIP_C1")
            vip_c2 = extract_tag(raw_text, "VIP_C2")
            vip_c3 = extract_tag(raw_text, "VIP_C3")
            vip_t1 = extract_tag(raw_text, "VIP_T1")
            vip_t2 = extract_tag(raw_text, "VIP_T2")
            vip_t3 = extract_tag(raw_text, "VIP_T3")
            vip_t4 = extract_tag(raw_text, "VIP_T4")
            vip_do = extract_tag(raw_text, "VIP_DO")
            vip_dont = extract_tag(raw_text, "VIP_DONT")

            # VIP 본문 조합 (차트 및 레이아웃 포함, 가로스크롤 방지)
            vip_html = f"""
            {chart_html}
            
            <h2 style="color: #2c3e50; font-size: 28px; margin-bottom: 20px;">📈 VIP Exclusive: Deep-Dive Macro Analysis</h2>
            <div style="background-color: #f8f9fa; border-left: 6px solid #2c3e50; padding: 25px; border-radius: 6px; margin-bottom: 40px; word-break: break-word;">
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;"><strong>[Institutional Money Flow & Technical Outlook]</strong></p>
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;">{vip_c1}</p>
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;">{vip_c2}</p>
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_c3}</p>
            </div>

            <h2 style="color: #1a237e; font-size: 28px; margin-bottom: 10px;">🛡️ The Titan's Playbook: Master Mindset</h2>
            <p style="font-size: 18px; color: #555; margin-bottom: 25px;"><em>How the top 1% navigate this specific market condition.</em></p>

            <div style="background-color: #fff8e1; border-left: 6px solid #f57f17; padding: 25px; border-radius: 6px; margin-bottom: 20px; word-break: break-word;">
                <h3 style="color: #f57f17; margin-top: 0; font-size: 22px;">1. The Generational Bargain (Fear vs. Greed)</h3>
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_t1}</p>
            </div>

            <div style="background-color: #e8f5e9; border-left: 6px solid #2e7d32; padding: 25px; border-radius: 6px; margin-bottom: 20px; word-break: break-word;">
                <h3 style="color: #2e7d32; margin-top: 0; font-size: 22px;">2. The 60/30/10 Seesaw (Asset Allocation)</h3>
                {allocation_html}
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0; margin-top: 15px;">{vip_t2}</p>
            </div>

            <div style="background-color: #e3f2fd; border-left: 6px solid #1565c0; padding: 25px; border-radius: 6px; margin-bottom: 20px; word-break: break-word;">
                <h3 style="color: #1565c0; margin-top: 0; font-size: 22px;">3. The Global Shield (US Dollar & Market)</h3>
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_t3}</p>
            </div>

            <div style="background-color: #fce4ec; border-left: 6px solid #c2185b; padding: 25px; border-radius: 6px; margin-bottom: 20px; word-break: break-word;">
                <h3 style="color: #c2185b; margin-top: 0; font-size: 22px;">4. Survival Mechanics (Split Buying & Mental Peace)</h3>
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_t4}</p>
            </div>

            <div style="background-color: #e8eaf6; border-left: 6px solid #3f51b5; padding: 30px; border-radius: 6px; margin-top: 40px; margin-bottom: 30px; word-break: break-word;">
                <h3 style="color: #3f51b5; margin-top: 0; font-size: 24px; margin-bottom: 20px;">✅ Today's VIP Action Plan</h3>
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;"><strong>🟢 DO (Immediate Action):</strong> {vip_do}</p>
                <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;"><strong>🔴 DON'T (Critical Mistakes):</strong> {vip_dont}</p>
            </div>
            """
            html_content += vip_html
            
        footer_html = f"""
        <hr>
        <h2>Today's Warm Insight</h2>
        <p style="font-size: 18px; line-height: 1.6; color: #333; word-break: break-word;">{takeaway}</p>
        <p style="font-size: 18px; line-height: 1.6; color: #333; word-break: break-word;"><strong>P.S.</strong> {ps}</p>
        <p style="font-size: 14px; color: #777; word-break: break-word;"><em>Disclaimer: This article is for informational purposes only. All decisions are your own.</em></p>
        """
        html_content += footer_html
            
        return title, image_prompt, html_content, custom_excerpt_with_time
        
    except Exception as e:
        print(f"⚠️ [AI 에러] 분석 실패: {e}")
        return None, None, None, None

def generate_thumbnail(image_prompt):
    print(f"🎨 공식 구글 고품질 썸네일(Imagen 3) 생성 시도 중... (프롬프트: {image_prompt})")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        result = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=image_prompt + ", highly detailed, cinematic lighting, 8k resolution",
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type="image/jpeg"
            )
        )
        if result.generated_images:
            print("✅ [썸네일 성공] 구글 공식 Imagen 3 썸네일 생성 완료!")
            return result.generated_images[0].image.image_bytes
    except Exception as e:
        print(f"⚠️ [구글 이미지 API 오류 - 플랜 B로 넘어갑니다]: {e}")

    print("🔄 [플랜 B 가동] 안전한 대체 이미지를 삽입합니다.")
    try:
        url = f"https://picsum.photos/seed/{random.randint(1,1000)}/1280/720"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
    except Exception: pass
        
    return None

def generate_ghost_token():
    id_str, secret_str = str(GHOST_ADMIN_API_KEY).split(':')
    iat = int(datetime.now().timestamp())
    header = dict(alg='HS256', typ='JWT', kid=id_str)
    payload = dict(iat=iat, exp=iat + 5 * 60, aud='/admin/')
    return jwt.encode(payload, bytes.fromhex(secret_str), algorithm='HS256', headers=header)

def upload_image_to_ghost(image_bytes):
    try:
        token = generate_ghost_token()
        headers = {'Authorization': 'Ghost ' + token}
        files = {'file': ('thumbnail.jpg', image_bytes, 'image/jpeg'), 'purpose': (None, 'image')}
        url = str(GHOST_API_URL) + "/ghost/api/admin/images/upload/"
        response = requests.post(url, headers=headers, files=files)
        if response.status_code in [200, 201]:
            return response.json().get('images')[0].get('url')
    except Exception as e: print(f"❌ [이미지 통신 에러] {e}")
    return None

def publish_to_ghost(title, html_content, category, tier, feature_image_url, custom_excerpt):
    print(f"📝 Ghost 웹사이트에 '{title}' 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = {'Authorization': 'Ghost ' + token, 'Content-Type': 'application/json'}
        post_dict = {
            "title": title, "html": html_content, "status": "published",
            "visibility": "public", "tags": [{"name": category}, {"name": tier}]
        }
        if custom_excerpt: post_dict["custom_excerpt"] = custom_excerpt
        if feature_image_url: post_dict["feature_image"] = feature_image_url
            
        url = str(GHOST_API_URL) + "/ghost/api/admin/posts/?source=html"
        response = requests.post(url, json={"posts": [post_dict]}, headers=headers_dict)
        if response.status_code in [200, 201]: print("🎉 [성공] 자동 발행 완료!")
        else: print(f"❌ [발행 실패] {response.status_code} - {response.text}")
    except Exception as e: print(f"❌ [통신 에러] {e}")

if __name__ == "__main__":
    try:
        for category, urls in CATEGORIES.items():
            print(f"\n--- [{category}] 지능형 큐레이션 및 분배 시작 ---")
            all_news = get_category_news(urls, count=20)
            if not all_news or len(all_news) < 3: continue
            
            for task in TASKS:
                tier = task.get("tier")
                req_count = task.get("count")
                if len(all_news) < req_count: break
                
                target_news = [all_news.pop(0) for _ in range(req_count)]
                print(f"  -> ({tier}) 등급 리포트 ({req_count}개 뉴스) 및 썸네일 생성 중...")
                
                post_title, img_prompt, report_html, custom_excerpt = analyze_with_gemini(target_news, category, tier)
                
                if report_html and post_title:
                    feature_image_url = None
                    if img_prompt:
                        image_bytes = generate_thumbnail(img_prompt)
                        if image_bytes: feature_image_url = upload_image_to_ghost(image_bytes)
                            
                    publish_to_ghost(post_title, report_html, category, tier, feature_image_url, custom_excerpt)
                time.sleep(20) 

        print("\n🎉 모든 카테고리 중복 없는 지능형 자동 발행 완료!")
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
