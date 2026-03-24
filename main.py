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
from datetime import datetime
import feedparser
from google import genai

print("=======================================")
print(" 🚀 40년 멘토 + VIP 무적 디자인(Ghost Card) + 폰트 고정 봇 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
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

# 🚨 [TikTok 바이럴 링크]
TIKTOK_LINKS = (
    "https://lite.tiktok.com/t/ZSuGXKdsU/\n"
    "https://lite.tiktok.com/t/ZSu9GYwy5/\n"
    "https://lite.tiktok.com/t/ZSuxhPSBR/\n"
    "https://lite.tiktok.com/t/ZSuXQwnvm/"
)

# 🚨 배포 설정
TASKS = [
    {"tier": "Basic", "count": 2},
    {"tier": "Premium", "count": 2},
    {"tier": "Royal Premium", "count": 3}
]

TIER_LABELS = {"Basic": "🌱 Free", "Premium": "💎 Pro", "Royal Premium": "👑 VIP"}

# 🚨 [Ghost 디자인 필터 무력화 + 폰트 18px 강제 고정 템플릿]
PROMPT_TEMPLATE = """
[Goal] Write a highly insightful blog post in ENGLISH for the '[CATEGORY]' section of the 'Warm Insight' website.
Target Audience: [TIER] Subscribers.

You are [PERSONA].

CRITICAL FORMATTING RULES:
1. Write ENTIRELY in ENGLISH. Do not use Markdown (*, -, #) for lists.
2. For diagrams, MUST use horizontal "Emoji Flows" (e.g., A 📈 ➡️ B 💥).
3. TIKTOK INFLUENCE: Create a 'Viral Social Insights 📱' section based on these vibes:
[TIKTOK_LINKS]

[VIP_RULES]

OUTPUT STRUCTURE STRICTLY FOLLOW THIS EXACT HTML TEMPLATE. REPLACE THE INSTRUCTIONAL TEXT IN PARENTHESES WITH YOUR ANALYSIS, BUT DO NOT OMIT OR CHANGE ANY HTML TAGS OR INLINE STYLES:

TITLE: (Insert Catchy Title)
IMAGE_PROMPT: (Insert simple English prompt for 3D abstract cinematic image)
EXCERPT: (Write a VERY catchy 1-sentence summary WITHOUT HTML tags.)

<p style="font-size: 18px; line-height: 1.6; color: #333;">(A warm 3-sentence summary of the news.)</p>

<h2>Viral Social Insights 📱</h2>
<p style="font-size: 18px; line-height: 1.6; color: #333;">(Translate the heavy news into a super-engaging TikTok style analogy.)</p>

<h2>Top Drivers & Deep Insights</h2>
<div style="font-family: sans-serif;">
    <strong style="font-size: 22px;">(Headline 1)</strong><br><br>
    <p style="font-size: 18px; line-height: 1.6; color: #333;">[DEPTH_INSTRUCTION]</p>
    <div style="border-left: 4px solid #999; background-color: #f4f4f4; padding: 15px; margin-top: 15px;">
        <strong style="font-size: 18px;">💡 Quick Flow:</strong> <span style="font-size: 18px;">(Insert Emoji Flow Diagram)</span>
    </div>
</div>
[VIP_SECTIONS]

<hr>
<h2>Today's Warm Insight</h2>
<p style="font-size: 18px; line-height: 1.6; color: #333;">(A comforting, actionable takeaway.)</p>
<p style="font-size: 18px; line-height: 1.6; color: #333;"><strong>P.S.</strong> (Add a very short personal thought.)</p>
<p style="font-size: 14px; color: #777;"><em>Disclaimer: This article is for informational purposes only.</em></p>

Raw News to Analyze:
[NEWS_ITEMS]
"""

VIP_EXTRA_RULES = """
4. VIP EXCLUSIVE: Act like a Wall Street Quant. Write highly detailed, 3+ long paragraphs analyzing RSI, Moving Averages, and Macro data.
5. MANDATORY DESIGN RULE: You MUST output the EXACT and <div style="..."> tags provided for the Titan's Playbook. KEEP ALL background colors, font sizes (18px), and borders EXACTLY as provided.
"""

VIP_EXTRA_SECTIONS = """
<div style="font-family: sans-serif; margin-top: 40px;">
    <h2 style="color: #2c3e50; font-size: 28px; margin-bottom: 20px;">📈 VIP Exclusive: Deep-Dive Chart & Macro Analysis</h2>
    <div style="background-color: #f8f9fa; border-left: 6px solid #2c3e50; padding: 25px; border-radius: 6px; margin-bottom: 40px;">
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;"><strong>[Institutional Money Flow & Technical Outlook]</strong></p>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;">(WRITE PARAGRAPH 1 HERE: Deeply analyze RSI, Moving Averages. At least 5 sentences.)</p>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;">(WRITE PARAGRAPH 2 HERE: Analyze Macro data, yield curves. At least 5 sentences.)</p>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">(WRITE PARAGRAPH 3 HERE: Conclude with what 'Smart Money' is doing.)</p>
    </div>

    <h2 style="color: #1a237e; font-size: 28px; margin-bottom: 10px;">🛡️ The Titan's Playbook: Master Mindset & Strategy</h2>
    <p style="font-size: 18px; color: #555; margin-bottom: 25px;"><em>How the top 1% navigate this specific market condition.</em></p>

    <div style="background-color: #fff8e1; border-left: 6px solid #f57f17; padding: 25px; border-radius: 6px; margin-bottom: 20px;">
        <h3 style="color: #f57f17; margin-top: 0; font-size: 22px;">1. The Generational Bargain (Fear vs. Greed)</h3>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">(WRITE A FULL DETAILED PARAGRAPH: Apply this to today's news. Fear & Greed Index.)</p>
    </div>

    <div style="background-color: #e8f5e9; border-left: 6px solid #2e7d32; padding: 25px; border-radius: 6px; margin-bottom: 20px;">
        <h3 style="color: #2e7d32; margin-top: 0; font-size: 22px;">2. The 60/30/10 Seesaw (Asset Allocation)</h3>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">(WRITE A FULL DETAILED PARAGRAPH: How to mechanically rebalance 60% Stocks, 30% Safe, 10% Cash today.)</p>
    </div>

    <div style="background-color: #e3f2fd; border-left: 6px solid #1565c0; padding: 25px; border-radius: 6px; margin-bottom: 20px;">
        <h3 style="color: #1565c0; margin-top: 0; font-size: 22px;">3. The Global Shield (US Dollar & Market)</h3>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">(WRITE A FULL DETAILED PARAGRAPH: Explain why holding US Assets is a crucial safety net right now.)</p>
    </div>

    <div style="background-color: #fce4ec; border-left: 6px solid #c2185b; padding: 25px; border-radius: 6px; margin-bottom: 20px;">
        <h3 style="color: #c2185b; margin-top: 0; font-size: 22px;">4. Survival Mechanics (Split Buying & Mental Peace)</h3>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;">(WRITE A FULL DETAILED PARAGRAPH: Define exactly when to use DCA and why selling 50% during panic is key.)</p>
    </div>

    <div style="background-color: #e8eaf6; border-left: 6px solid #3f51b5; padding: 30px; border-radius: 6px; margin-top: 40px; margin-bottom: 30px;">
        <h3 style="color: #3f51b5; margin-top: 0; font-size: 24px; margin-bottom: 20px;">✅ Today's VIP Action Plan</h3>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 15px;"><strong>🟢 DO (Immediate Action):</strong> (Provide 2 highly specific, actionable steps.)</p>
        <p style="font-size: 18px; line-height: 1.6; color: #333; margin-bottom: 0;"><strong>🔴 DON'T (Critical Mistakes):</strong> (Provide 1 specific mistake to avoid.)</p>
    </div>
</div>
"""

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
        except:
            continue
            
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
        
        vip_rules = ""
        vip_sections = ""
        
        if tier == "Basic":
            depth_instruction = "<strong>🔑 The Core Fact:</strong> Explain what happened simply using ELI5."
        elif tier == "Premium":
            depth_instruction = "<strong>🧐 WHY (The Hidden Reason):</strong> Explain using behavioral economics.<br><br><strong>🐑 THINK (What Masses Think):</strong> Explain the irrational market psychology."
        else: # Royal Premium
            depth_instruction = "<strong>🧐 WHY:</strong> Macroeconomic reason.<br><br><strong>🐑 THINK:</strong> Herd Behavior.<br><br><strong>🦅 DIFFERENT THINK:</strong> Contrarian View."
            vip_rules = VIP_EXTRA_RULES
            vip_sections = VIP_EXTRA_SECTIONS

        if category == "Politics": expert_persona = "a veteran US political expert"
        elif category == "Tech": expert_persona = "a veteran US technology expert"
        elif category == "Health": expert_persona = "a veteran US healthcare expert"
        elif category == "Energy": expert_persona = "a veteran US energy expert"
        else: expert_persona = "a veteran US Wall Street expert"

        prompt = PROMPT_TEMPLATE.replace("[CATEGORY]", category).replace("[TIER]", tier).replace("[PERSONA]", expert_persona).replace("[TIKTOK_LINKS]", TIKTOK_LINKS).replace("[VIP_RULES]", vip_rules).replace("[DEPTH_INSTRUCTION]", depth_instruction).replace("[VIP_SECTIONS]", vip_sections).replace("[NEWS_ITEMS]", selected_news)
        
        response = client.models.generate_content(model=model_name, contents=prompt)
        raw_text = str(response.text).replace("```html", "").replace("```", "").strip()
        lines = raw_text.split('\n')
        
        pretty_tier = TIER_LABELS.get(tier, tier)
        title = f"({tier}) Daily {category} Insight"
        image_prompt = f"Abstract 3D cinematic rendering of global {category}."
        custom_excerpt = "Insightful financial analysis for your future."
        html_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("TITLE:"):
                title = f"[{pretty_tier}] " + stripped.replace("TITLE:", "").strip()
            elif stripped.startswith("IMAGE_PROMPT:"):
                image_prompt = stripped.replace("IMAGE_PROMPT:", "").strip()
            elif stripped.startswith("EXCERPT:"):
                custom_excerpt = stripped.replace("EXCERPT:", "").strip()
            elif stripped:
                html_lines.append(stripped)
                
        html_content = "\n".join(html_lines).strip()
        current_time_str = datetime.now().strftime('%B %d, %Y at %I:%M %p (UTC)')
        author_name = "Ethan Cole & The Warm Insight Panel"
        
        # 글 맨 위에 들어가는 작성자/시간 박스도 Ghost Card로 보호합니다.
        info_box = f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #f2a900; margin-bottom: 25px; border-radius: 4px; font-family: sans-serif;">
            <p style="margin: 0; font-size: 16px; color: #555; line-height: 1.6;">
                <strong>✍️ Written by:</strong> {author_name}<br>
                <strong>⏰ Published:</strong> {current_time_str}
            </p>
        </div>
        """
        html_content = info_box + "\n" + html_content
            
        return title, image_prompt, html_content, custom_excerpt
        
    except Exception as e:
        print(f"⚠️ [AI 에러] {category} - {tier} 분석 실패: {e}")
        return None, None, None, None

def generate_thumbnail(image_prompt):
    print(f"🎨 공식 구글 고품질 AI 썸네일 생성 중... (프롬프트: {image_prompt})")
    try:
        # 구글 공식 고품질 모델(imagen 3)
        api_base = "https://generativelanguage.googleapis.com"
        url = api_base + "/v1beta/models/imagen-3.0-generate-001:predict?key=" + str(GEMINI_API_KEY)
        
        headers = {'Content-Type': 'application/json'}
        params = {"sampleCount": 1, "aspectRatio": "16:9", "outputOptions": {"mimeType": "image/jpeg"}}
        
        data = {
            "instances": [{"prompt": image_prompt}],
            "parameters": params
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            predictions = response.json().get('predictions')
            if predictions:
                print("✅ [썸네일 성공] 구글 공식 Imagen 3 썸네일 생성 완료!")
                return base64.b64decode(predictions[0].get('bytesBase64Encoded', ''))
        else:
            print(f"⚠️ [이미지 API 에러 (요금 한도 등)]: {response.status_code}")
    except Exception as e:
        print(f"⚠️ [이미지 생성 에러]: {e}")
    
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
        files = {
            'file': ('thumbnail.jpg', image_bytes, 'image/jpeg'),
            'purpose': (None, 'image')
        }
        url = str(GHOST_API_URL) + "/ghost/api/admin/images/upload/"
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code in [200, 201]:
            return response.json().get('images')[0].get('url')
    except Exception as e:
        print(f"❌ [이미지 통신 에러] {e}")
    return None

def publish_to_ghost(title, html_content, category, tier, feature_image_url, custom_excerpt):
    print(f"📝 Ghost 웹사이트에 '{title}' 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = {
            'Authorization': 'Ghost ' + token,
            'Content-Type': 'application/json'
        }
        
        post_dict = {
            "title": title,
            "html": html_content,
            "status": "published",
            "visibility": "public",
            "tags": [{"name": category}, {"name": tier}]
        }
        
        if custom_excerpt: post_dict["custom_excerpt"] = custom_excerpt
        if feature_image_url: post_dict["feature_image"] = feature_image_url
            
        url = str(GHOST_API_URL) + "/ghost/api/admin/posts/?source=html"
        response = requests.post(url, json={"posts": [post_dict]}, headers=headers_dict)
        
        if response.status_code in [200, 201]:
            print("🎉 [성공] 자동 발행 완료!")
        else:
            print(f"❌ [발행 실패] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ [통신 에러] {e}")

if __name__ == "__main__":
    try:
        for category, urls in CATEGORIES.items():
            print(f"\n--- [{category}] 지능형 큐레이션 및 분배 시작 ---")
            
            all_news = get_category_news(urls, count=20)
            if not all_news or len(all_news) < 3:
                continue
            
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
                        if image_bytes:
                            feature_image_url = upload_image_to_ghost(image_bytes)
                            
                    publish_to_ghost(post_title, report_html, category, tier, feature_image_url, custom_excerpt)
                    
                time.sleep(20) 

        print("\n🎉 모든 카테고리 중복 없는 지능형 자동 발행 완료!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
