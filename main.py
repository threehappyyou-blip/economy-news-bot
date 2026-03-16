import os
import sys
import traceback
import time
import requests
import jwt
import base64
from datetime import datetime
import feedparser
from google import genai
from google.genai import types

print("=======================================")
print(" 🚀 13인 전문가 + 나노바나나 썸네일 자동 발행 봇 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

GHOST_API_URL = GHOST_API_URL.rstrip('/')

# 🚨 [카테고리 세팅]
CATEGORIES = dict()
CATEGORIES["Economy"] = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "https://finance.yahoo.com/news/rssindex"]
CATEGORIES["Politics"] = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113"]
CATEGORIES = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"]
CATEGORIES["Health"] = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108"]
CATEGORIES["Energy"] = ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810"]

# [등급 세팅]
TIERS = ("Basic", "Premium", "Royal Premium")

def get_category_news(urls, count=30):
    news_list = list()
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
        except Exception:
            continue
    return news_list

def analyze_with_gemini(news_items, category, tier):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        selected_news = "\n".join(news_items)
        
        # [모델 및 뎁스 설정]
        if tier == "Basic":
            model_name = "gemini-2.5-flash"  
            news_count = "3"
            depth = "Focus ONLY on the objective FACTS."
        elif tier == "Premium":
            model_name = "gemini-2.5-pro"    
            news_count = "5"
            depth = "Focus on the 'WHY' behind the facts using behavioral economics and psychology."
        else: 
            model_name = "gemini-2.5-pro"    
            news_count = "10"
            depth = "Provide the ULTIMATE deep dive using macroeconomic theory, psychology, and historical context."

        prompt = f"""
        [Goal] Write a highly insightful, professional blog post in English for the '{category}' section of our Ghost website.
        {tier} Subscribers
        
        Phase 1: Intelligent Curation
        - Select ONLY the top {news_count} most critical news stories from the raw data.
        
        Phase 2: Panel Debate and Drafting
        - {depth}
        - STRICT RULE: Write in a professional, trustworthy, and insightful tone. No casual greetings like "Hey there, neighborhood friend!". Start directly with a polished, authoritative introduction.
        - Format the response in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>). Do NOT use markdown (**). Do NOT include ```html.
        
        The VERY FIRST LINE must be exactly: TITLE: (Insert Catchy Title)
        The SECOND LINE must be exactly: IMAGE_PROMPT: (Insert English prompt for image generation)
        From the THIRD LINE onwards, write the HTML content.
        
        Raw News to Analyze:
        {selected_news}
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        raw_text = response.text.replace("```html", "").replace("```", "").strip()
        
        # 🚨 [제목/썸네일 분리 알고리즘 업그레이드] 빈 줄을 싹 무시하고 가장 첫 줄과 두 번째 줄을 정확히 찾아냅니다.
        lines = [line for line in raw_text.split('\n') if line.strip()!= ""]
        
        title = f"[{tier}] Daily {category} Insight"
        image_prompt = f"Abstract 3D illustration representing global {category}, cinematic lighting, high quality, 8k resolution."
        
        if len(lines) > 0 and lines.startswith("TITLE:"):
            title = f"[{tier}] " + lines.pop(0).replace("TITLE:", "").strip()
            
        if len(lines) > 0 and lines.startswith("IMAGE_PROMPT:"):
            image_prompt = lines.pop(0).replace("IMAGE_PROMPT:", "").strip()
                
        html_content = "\n".join(lines).strip()
            
        return title, image_prompt, html_content
        
    except Exception as e:
        print(f"⚠️ [AI 에러] {category} - {tier} 분석 실패: {e}")
        return None, None, None

def generate_thumbnail(image_prompt):
    print(f"🎨 나노바나나 AI 썸네일 생성 중... (프롬프트: {image_prompt})")
    try:
        url = f"[https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=](https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=){GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "instances": [{"prompt": image_prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "16:9",
                "outputOptions": {"mimeType": "image/jpeg"}
            }
        }
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            predictions = response.json().get('predictions')
            if predictions:
                b64_img = predictions.get('bytesBase64Encoded', '')
                return base64.b64decode(b64_img)
        print(f"⚠️ [이미지 API 에러]: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"⚠️ [이미지 생성 에러]: {e}")
        return None

def generate_ghost_token():
    id_str, secret_str = GHOST_ADMIN_API_KEY.split(':')
    iat = int(datetime.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id_str}
    payload = {'iat': iat, 'exp': iat + 5 * 60, 'aud': '/admin/'}
    return jwt.encode(payload, bytes.fromhex(secret_str), algorithm='HS256', headers=header)

def upload_image_to_ghost(image_bytes):
    try:
        token = generate_ghost_token()
        headers = {'Authorization': f'Ghost {token}'}
        files = {
            'file': ('thumbnail.jpg', image_bytes, 'image/jpeg'),
            'purpose': (None, 'image')
        }
        url = f"{GHOST_API_URL}/ghost/api/admin/images/upload/"
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code in (200, 201):
            return response.json()['images']['url']
        else:
            print(f"❌ [이미지 업로드 실패] {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ [이미지 통신 에러] {e}")
        return None

def publish_to_ghost(title, html_content, category, tier, feature_image_url):
    print(f"📝 Ghost 웹사이트에 '{title}' 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = {'Authorization': f'Ghost {token}', 'Content-Type': 'application/json'}
        
        # 🚨 [모두 무료 공개] 1000명 모일 때까지 누구나 볼 수 있게 public으로 엽니다!
        visibility_setting = "public"
        
        post_dict = {
            "title": title, 
            "html": html_content,
            "status": "published",
            "visibility": visibility_setting,
            "tags": [{"name": category}, {"name": tier}] 
        }
        
        if feature_image_url:
            post_dict["feature_image"] = feature_image_url
            
        post_data = {"posts": [post_dict]}
        
        url = f"{GHOST_API_URL}/ghost/api/admin/posts/?source=html"
        response = requests.post(url, json=post_data, headers=headers_dict)
        
        if response.status_code in (200, 201):
            print(f"🎉 [성공] 자동 발행 완료!")
        else:
            print(f"❌ [발행 실패] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ [통신 에러] Ghost 서버 연결 실패: {e}")

if __name__ == "__main__":
    try:
        for category, urls in CATEGORIES.items():
            print(f"\n--- [{category}] 지능형 큐레이션 시작 ---")
            
            news = get_category_news(urls, count=30)
            if not news:
                continue
                
            for tier in TIERS:
                print(f"  -> {tier} 등급 리포트 및 썸네일 생성 중...")
                post_title, img_prompt, report_html = analyze_with_gemini(news, category, tier)
                
                if report_html and post_title:
                    feature_image_url = None
                    if img_prompt:
                        image_bytes = generate_thumbnail(img_prompt)
                        if image_bytes:
                            feature_image_url = upload_image_to_ghost(image_bytes)
                            
                    publish_to_ghost(post_title, report_html, category, tier, feature_image_url)
                    
                time.sleep(20) 

        print("\n🎉 모든 카테고리 썸네일 및 지능형 자동 발행이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
