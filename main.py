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
print(" 🚀 40년 멘토 + 단일 캡슐화(무적 디자인) + 스크롤 박멸 봇 🚀")
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
<GRAPH_DATA>Extract 3 key metrics or sentiment indicators from the news. Format EXACTLY as: Label1|Value1|Label2|Value2|Label3|Value3. (Values must be numbers 0-100. Example: Market Fear|75|Inflation Risk|40|Tech Resilience|85)</GRAPH_DATA>
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
        
        # =========================================================================
        # 🚨 [최종 혁신 패치] 전체를 단 하나의 HTML 카드로 감싸 Ghost 검열을 완벽 무력화!
        # =========================================================================
        html_content = "\n"
        html_content += f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1a252c; font-size: 18px; line-height: 1.7; word-wrap: break-word; overflow-wrap: break-word; box-sizing: border-box; width: 100%; max-width: 100%; overflow-x: hidden;">

            <div style="border-top: 3px solid #b8974d; border-bottom: 1px solid #e5e7eb; padding: 12px 0; margin-bottom: 30px; box-sizing: border-box; width: 100%;">
                <p style="margin: 0; font-size: 14px; color: #4b5563; text-transform: uppercase; letter-spacing: 0.5px;">
                    <strong style="color: #1a252c;">By {author_name}</strong> &nbsp;|&nbsp; {current_time_str}
                </p>
            </div>
            
            <h2 style="font-family: 'Georgia', serif; font-size: 24px; color: #1a252c; margin-top: 0; margin-bottom: 15px;">Executive Summary</h2>
            <p style="margin-bottom: 35px; color: #374151;">{summary}</p>
            
            <div style="background-color: #f1f3f5; border-left: 4px solid #8e44ad; padding: 20px; border-radius: 4px; margin-bottom: 40px; box-sizing: border-box; width: 100%;">
                <h3 style="margin-top: 0; font-size: 18px; color: #1a252c; margin-bottom: 10px;">📱 Viral Social Insights</h3>
                <p style="font-size: 17px; line-height: 1.6; color: #4b5563; margin: 0;">{tiktok}</p>
            </div>
            
            <h2 style="font-family: 'Georgia', serif; font-size: 24px; color: #1a252c; margin-bottom: 15px;">Market Drivers & Insights</h2>
            <strong style="font-size: 20px; color: #1a252c; display: block; margin-bottom: 12px;">{headline}</strong>
            <p style="color: #374151; margin-bottom: 20px;">{depth}</p>
            
            <div style="background-color: #ffffff; border: 1px solid #e5e7eb; padding: 15px 20px; border-radius: 4px; margin-bottom: 40px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); box-sizing: border-box; width: 100%;">
                <strong style="font-size: 16px; color: #b8974d; text-transform: uppercase; letter-spacing: 0.5px;">💡 Quick Flow:</strong> 
                <span style="font-size: 17px; color: #1a252c; display: block; margin-top: 5px;">{flow}</span>
            </div>
        """

        if tier == "Royal Premium":
            graph_data_raw = extract_tag(raw_text, "GRAPH_DATA")
            parts = [p.strip() for p in graph_data_raw.split('|')]
            if len(parts) == 6: l1, v1, l2, v2, l3, v3 = parts
            else: l1, v1, l2, v2, l3, v3 = "Market Volatility", "75", "Recession Risk", "40", "Investor Confidence", "60"
            
            try: v1_int = int("".join(filter(str.isdigit, v1)))
            except: v1_int = 50
            try: v2_int = int("".join(filter(str.isdigit, v2)))
            except: v2_int = 50
            try: v3_int = int("".join(filter(str.isdigit, v3)))
            except: v3_int = 50

            # 📊 스크롤 없는 프로그레스 게이지 바
            html_content += f"""
            <div style="margin: 40px 0 30px 0; padding: 25px; background-color: #f8fafc; border: 1px solid #e5e7eb; border-radius: 6px; box-sizing: border-box; width: 100%;">
                <h3 style="margin-top: 0; color: #1a252c; font-size: 18px; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #e5e7eb; padding-bottom: 12px; margin-bottom: 25px;">📊 Key Market Indicators</h3>
                
                <div style="margin-bottom: 20px; box-sizing: border-box; width: 100%;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-size: 15px; font-weight: 600; color: #4b5563;">{l1}</span>
                        <span style="font-size: 15px; font-weight: 700; color: #e74c3c;">{v1_int}%</span>
                    </div>
                    <div style="width: 100%; background-color: #e5e7eb; border-radius: 4px; height: 8px; overflow: hidden; box-sizing: border-box;">
                        <div style="width: {v1_int}%; background-color: #e74c3c; height: 100%;"></div>
                    </div>
                </div>

                <div style="margin-bottom: 20px; box-sizing: border-box; width: 100%;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-size: 15px; font-weight: 600; color: #4b5563;">{l2}</span>
                        <span style="font-size: 15px; font-weight: 700; color: #f59e0b;">{v2_int}%</span>
                    </div>
                    <div style="width: 100%; background-color: #e5e7eb; border-radius: 4px; height: 8px; overflow: hidden; box-sizing: border-box;">
                        <div style="width: {v2_int}%; background-color: #f59e0b; height: 100%;"></div>
                    </div>
                </div>

                <div style="margin-bottom: 5px; box-sizing: border-box; width: 100%;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="font-size: 15px; font-weight: 600; color: #4b5563;">{l3}</span>
                        <span style="font-size: 15px; font-weight: 700; color: #10b981;">{v3_int}%</span>
                    </div>
                    <div style="width: 100%; background-color: #e5e7eb; border-radius: 4px; height: 8px; overflow: hidden; box-sizing: border-box;">
                        <div style="width: {v3_int}%; background-color: #10b981; height: 100%;"></div>
                    </div>
                </div>
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

            # ⚖️ 고급스러운 자산배분 바 & VIP 섹션
            html_content += f"""
            <h2 style="font-family: 'Georgia', serif; font-size: 26px; color: #1a252c; margin-bottom: 20px; border-bottom: 2px solid #b8974d; padding-bottom: 8px; display: inline-block;">VIP Exclusive: Macro & Flow Analysis</h2>
            
            <div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-left: 4px solid #1a252c; padding: 25px; border-radius: 4px; margin-bottom: 40px; box-sizing: border-box; width: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                <p style="font-size: 16px; color: #b8974d; text-transform: uppercase; font-weight: bold; margin-top: 0; margin-bottom: 15px; letter-spacing: 0.5px;">[Institutional Technical Outlook]</p>
                <p style="margin-bottom: 15px; color: #374151;">{vip_c1}</p>
                <p style="margin-bottom: 15px; color: #374151;">{vip_c2}</p>
                <p style="margin-bottom: 0; color: #374151;">{vip_c3}</p>
            </div>

            <h2 style="font-family: 'Georgia', serif; font-size: 26px; color: #1a252c; margin-bottom: 10px; border-bottom: 2px solid #b8974d; padding-bottom: 8px; display: inline-block;">The Titan's Playbook</h2>
            <p style="font-size: 16px; color: #6b7280; margin-bottom: 25px; font-style: italic;">Strategic manual for the top 1% navigating current conditions.</p>

            <div style="background-color: #f8fafc; border: 1px solid #e5e7eb; padding: 20px 25px; border-radius: 6px; margin-bottom: 20px; box-sizing: border-box; width: 100%;">
                <h3 style="color: #1a252c; margin-top: 0; font-size: 19px; margin-bottom: 10px;">1. The Generational Bargain (Fear vs. Greed)</h3>
                <p style="margin-bottom: 0; color: #4b5563;">{vip_t1}</p>
            </div>

            <div style="background-color: #f8fafc; border: 1px solid #e5e7eb; padding: 20px 25px; border-radius: 6px; margin-bottom: 20px; box-sizing: border-box; width: 100%;">
                <h3 style="color: #1a252c; margin-top: 0; font-size: 19px; margin-bottom: 10px;">2. The 60/30/10 Seesaw (Asset Allocation)</h3>
                
                <div style="margin: 20px 0; box-sizing: border-box; width: 100%;">
                    <div style="display: flex; width: 100%; height: 26px; border-radius: 4px; overflow: hidden; box-sizing: border-box;">
                        <div style="width: 60%; background-color: #1a252c; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 12px; letter-spacing: 0.5px;">STOCKS 60%</div>
                        <div style="width: 30%; background-color: #64748b; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 12px; letter-spacing: 0.5px;">SAFE 30%</div>
                        <div style="width: 10%; background-color: #b8974d; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 12px; letter-spacing: 0.5px;">CASH 10%</div>
                    </div>
                    <p style="font-size: 13px; color: #9ca3af; margin: 8px 0 0 0; text-align: center; font-style: italic;">* Mechanically rebalance to maintain this absolute ratio.</p>
                </div>
                
                <p style="margin-bottom: 0; margin-top: 20px; color: #4b5563;">{vip_t2}</p>
            </div>

            <div style="background-color: #f8fafc; border: 1px solid #e5e7eb; padding: 20px 25px; border-radius: 6px; margin-bottom: 20px; box-sizing: border-box; width: 100%;">
                <h3 style="color: #1a252c; margin-top: 0; font-size: 19px; margin-bottom: 10px;">3. The Global Shield (US Dollar & Market)</h3>
                <p style="margin-bottom: 0; color: #4b5563;">{vip_t3}</p>
            </div>

            <div style="background-color: #f8fafc; border: 1px solid #e5e7eb; padding: 20px 25px; border-radius: 6px; margin-bottom: 20px; box-sizing: border-box; width: 100%;">
                <h3 style="color: #1a252c; margin-top: 0; font-size: 19px; margin-bottom: 10px;">4. Survival Mechanics (Split Buying & Mental Peace)</h3>
                <p style="margin-bottom: 0; color: #4b5563;">{vip_t4}</p>
            </div>

            <div style="background-color: #1a252c; color: white; padding: 30px; border-radius: 8px; margin-top: 40px; margin-bottom: 30px; box-sizing: border-box; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #b8974d; margin-top: 0; font-size: 22px; margin-bottom: 20px; border-bottom: 1px solid #374151; padding-bottom: 10px;">✅ Today's VIP Action Plan</h3>
                <p style="color: #e5e7eb; margin-bottom: 15px;"><strong>🟢 DO (Action):</strong> {vip_do}</p>
                <p style="color: #e5e7eb; margin-bottom: 0;"><strong>🔴 DON'T (Avoid):</strong> {vip_dont}</p>
            </div>
            """

        html_content += f"""
            <hr style="border: 0; height: 1px; background: #e5e7eb; margin: 40px 0;">
            <h2 style="font-family: 'Georgia', serif; font-size: 24px; color: #1a252c; margin-bottom: 15px;">Today's Warm Insight</h2>
            <p style="color: #374151;">{takeaway}</p>
            <div style="margin-top: 30px; background-color: #f9fafb; padding: 20px; border-radius: 4px; border-left: 3px solid #b8974d;">
                <p style="margin: 0; color: #4b5563;"><strong>P.S.</strong> {ps}</p>
            </div>
            <p style="font-size: 13px; color: #9ca3af; margin-top: 30px; text-align: center; text-transform: uppercase; letter-spacing: 0.5px;">Disclaimer: This article is for informational purposes only.</p>
        
        </div>
        """
            
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
            prompt=image_prompt + ", highly detailed, cinematic lighting, 8k resolution, professional financial tone",
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
