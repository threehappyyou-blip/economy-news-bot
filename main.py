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

print("=======================================")
print(" 🚀 40년 멘토 + 표(Table) 위장 디자인 + 외부 시간표시 봇 🚀")
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
        
        # XML 데이터 파싱
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
        current_time_short = datetime.now().strftime('%I:%M %p') # 시간만 뽑기 (예: 05:20 AM)
        author_name = "Ethan Cole & The Warm Insight Panel"
        
        # 🚨 [혁신 패치 2] 홈페이지 바깥쪽(Preview)에서도 시간이 보이게 요약문 맨 앞에 텍스트 강제 주입!
        custom_excerpt_with_time = f"⏰ {current_time_short} | {custom_excerpt}"
        
        # 🚨 [혁신 패치 1] Ghost가 지울 수 없는 <table width="100%"> 위장술 적용
        html_content = f"""
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; border: none;">
            <tr>
                <td style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #f2a900; border-radius: 4px;">
                    <p style="margin: 0; font-size: 16px; color: #555; line-height: 1.6; font-family: sans-serif;">
                        <strong>✍️ Written by:</strong> {author_name}<br>
                        <strong>⏰ Published:</strong> {current_time_str}
                    </p>
                </td>
            </tr>
        </table>
        
        <p style="font-size: 18px; line-height: 1.6; color: #333;">{summary}</p>
        
        <h2>Viral Social Insights 📱</h2>
        <p style="font-size: 18px; line-height: 1.6; color: #333;">{tiktok}</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <strong style="font-size: 22px;">{headline}</strong><br><br>
        <p style="font-size: 18px; line-height: 1.6; color: #333;">{depth}</p>
        
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px; border: none;">
            <tr>
                <td style="border-left: 4px solid #999; background-color: #f4f4f4; padding: 15px;">
                    <strong style="font-size: 18px;">💡 Quick Flow:</strong> <span style="font-size: 18px;">{flow}</span>
                </td>
            </tr>
        </table>
        """

        if tier == "Royal Premium":
            vip_c1 = extract_tag(raw_text, "VIP_C1")
            vip_c2 = extract_tag(raw_text, "VIP_C2")
            vip_c3 = extract_tag(raw_text, "VIP_C3")
            vip_t1 = extract_tag(raw_text, "VIP_T1")
            vip_t2 = extract_tag(raw_text, "VIP_T2")
            vip_t3 = extract_tag(raw_text, "VIP_T3")
            vip_t4 = extract_tag(raw_text, "VIP_T4")
            vip_do = extract_tag(raw_text, "VIP_DO")
            vip_dont = extract_tag(raw_text, "VIP_DONT")

            # VIP 박스들도 모두 Table 구조로 변경하여 색상과 여백을 사수합니다.
            vip_html = f"""
            <h2 style="color: #2c3e50; font-size: 28px; margin-top: 40px; margin-bottom: 20px;">📈 VIP Exclusive: Deep-Dive Chart & Macro Analysis</h2>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 40px; border: none;">
                <tr>
                    <td style="background-color: #f8f9fa; border-left: 6px solid #2c3e50; padding: 25px; border-radius: 6px;">
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;"><strong>[Institutional Money Flow & Technical Outlook]</strong></p>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;">{vip_c1}</p>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;">{vip_c2}</p>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_c3}</p>
                    </td>
                </tr>
            </table>

            <h2 style="color: #1a237e; font-size: 28px; margin-bottom: 10px;">🛡️ The Titan's Playbook: Master Mindset & Strategy</h2>
            <p style="font-size: 18px; color: #555; margin-bottom: 25px;"><em>How the top 1% navigate this specific market condition.</em></p>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; border: none;">
                <tr>
                    <td style="background-color: #fff8e1; border-left: 6px solid #f57f17; padding: 25px; border-radius: 6px;">
                        <h3 style="color: #f57f17; margin-top: 0; font-size: 22px;">1. The Generational Bargain (Fear vs. Greed)</h3>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_t1}</p>
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; border: none;">
                <tr>
                    <td style="background-color: #e8f5e9; border-left: 6px solid #2e7d32; padding: 25px; border-radius: 6px;">
                        <h3 style="color: #2e7d32; margin-top: 0; font-size: 22px;">2. The 60/30/10 Seesaw (Asset Allocation)</h3>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_t2}</p>
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; border: none;">
                <tr>
                    <td style="background-color: #e3f2fd; border-left: 6px solid #1565c0; padding: 25px; border-radius: 6px;">
                        <h3 style="color: #1565c0; margin-top: 0; font-size: 22px;">3. The Global Shield (US Dollar & Market)</h3>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_t3}</p>
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; border: none;">
                <tr>
                    <td style="background-color: #fce4ec; border-left: 6px solid #c2185b; padding: 25px; border-radius: 6px;">
                        <h3 style="color: #c2185b; margin-top: 0; font-size: 22px;">4. Survival Mechanics (Split Buying & Mental Peace)</h3>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">{vip_t4}</p>
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-top: 40px; margin-bottom: 30px; border: none;">
                <tr>
                    <td style="background-color: #e8eaf6; border-left: 6px solid #3f51b5; padding: 30px; border-radius: 6px;">
                        <h3 style="color: #3f51b5; margin-top: 0; font-size: 24px; margin-bottom: 20px;">✅ Today's VIP Action Plan</h3>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;"><strong>🟢 DO (Immediate Action):</strong> {vip_do}</p>
                        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;"><strong>🔴 DON'T (Critical Mistakes):</strong> {vip_dont}</p>
                    </td>
                </tr>
            </table>
            """
            html_content += vip_html
            
        footer_html = f"""
        <hr>
        <h2>Today's Warm Insight</h2>
        <p style="font-size: 18px; line-height: 1.6; color: #333;">{takeaway}</p>
        <p style="font-size: 18px; line-height: 1.6; color: #333;"><strong>P.S.</strong> {ps}</p>
        <p style="font-size: 14px; color: #777;"><em>Disclaimer: This article is for informational purposes only. All decisions are your own.</em></p>
        """
        html_content += footer_html
            
        return title, image_prompt, html_content, custom_excerpt_with_time
        
    except Exception as e:
        print(f"⚠️ [AI 에러] 분석 실패: {e}")
        return None, None, None, None

def generate_thumbnail(image_prompt):
    print(f"🎨 썸네일 생성 시도 중... (프롬프트: {image_prompt})")
    
    for attempt in range(3):
        try:
            seed = random.randint(1, 1000000)
            safe_prompt = urllib.parse.quote(image_prompt[:150] + " cinematic, highly detailed, 8k")
            url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true&seed={seed}"
            response = requests.get(url, timeout=20)
            
            content_type = response.headers.get('Content-Type', '')
            if response.status_code == 200 and 'image' in content_type:
                print("✅ [썸네일 성공] 고품질 AI 이미지 생성 완료!")
                return response.content
            else:
                time.sleep(3)
        except Exception:
            time.sleep(3)
            
    print("🔄 [플랜 B 가동] AI 서버 응답 지연으로 안전한 대체 이미지를 삽입합니다.")
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
