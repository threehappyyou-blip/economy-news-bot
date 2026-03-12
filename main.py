import os
import sys
import traceback
import time
import requests
import jwt
from datetime import datetime
import feedparser
from google import genai
from google.genai import types

print("=======================================")
print(" 🚀 13인 전문가 + 나노바나나 AI 자동 발행 봇 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

GHOST_API_URL = GHOST_API_URL.rstrip('/')

CATEGORIES = {
    "Economy": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "https://finance.yahoo.com/news/rssindex"),
    "Politics": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113",),
    "Tech": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",),
    "Health": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108",),
    "Energy": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810",)
}

TIERS = ("Basic", "Premium", "Royal Premium")

def get_category_news(urls, count=30):
    news_list = list()
    seen_titles = set()
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.title in seen_titles: continue
                news_list.append("- " + str(entry.title) + ": " + str(entry.summary if 'summary' in entry else ''))
                seen_titles.add(entry.title)
                if len(news_list) >= 30: break
        except Exception:
            continue
    return news_list[:count]

def analyze_with_gemini(news_items, category, tier):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        selected_news = "\n".join(news_items)
        
        if tier == "Basic":
            model_name = "gemini-2.5-flash"  
            news_count = "3"
            depth = "Focus ONLY on the objective FACTS."
        elif tier == "Premium":
            model_name = "gemini-2.5-pro"    
            news_count = "5"
            depth = "Focus on the 'WHY' behind the facts using behavioral economics and psychology."
        else: 
            model_name = "gemini-3.1-pro"    
            news_count = "10"
            depth = "Provide the ULTIMATE deep dive using macroeconomic theory, psychology, and historical context."

        # 🚨 [프롬프트 업그레이드] 제목, 이미지 생성 명령어, 본문을 완벽하게 분리하도록 지시합니다.
        prompt = f"""
        [Goal] Write a highly insightful, professional blog post in English for the '{category}' section of our Ghost website.
        {tier} Subscribers
        
        Phase 1: Intelligent Curation
        - Select ONLY the top {news_count} most critical news stories from the raw data.
        
        Phase 2: Panel Debate and Drafting
        - {depth}
        - STRICT RULE: Write in a professional, trustworthy, and insightful tone. No casual greetings like "Hey there". Start directly with a polished introduction.
        - Format the response in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>). Do NOT use markdown (**). Do NOT include ```html.
        
       
        The VERY FIRST LINE must be: "TITLE:"
        The SECOND LINE must be: "IMAGE_PROMPT:"
        From the THIRD LINE onwards, write the HTML content:
        
        <h2>The Big Picture</h2>
        <p>(A professional summary...)</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <ul>
            <li><strong>(Headline):</strong> (Fact + Insights)</li>
        </ul>
        
        <h2>Today's Insight</h2>
        <p>(A comforting, actionable takeaway.)</p>
        
        <p><em>Disclaimer: This article is for informational and educational purposes only. All decisions are your own.</em></p>

        Raw News to Analyze:
        {selected_news}
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        raw_text = response.text.replace("```html", "").replace("```", "").strip()
        lines = raw_text.split('\n')
        
        title = f"[{tier}] Daily {category} Insight" 
        image_prompt = f"Abstract 3D illustration representing global {category}, cinematic lighting, high quality, 8k resolution."
        
        # 첫 번째 줄과 두 번째 줄에서 제목과 이미지 프롬프트를 쏙 뽑아냅니다.
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
    """나노바나나 AI를 호출하여 썸네일 이미지를 그립니다."""
    print(f"🎨 나노바나나 AI가 썸네일을 그리는 중입니다... (프롬프트: {image_prompt})")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        # 나노바나나 2 (gemini-3.1-flash-image-preview) 모델 사용
        response = client.models.generate_images(
            model='gemini-3.1-flash-image-preview',
            prompt=image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="16:9" 
            )
        )
        return response.generated_images.image.image_bytes
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
    """생성된 이미지를 Ghost 사이트에 업로드하고 URL을 받아옵니다."""
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
            print(f"❌ [이미지 업로드 실패] {response.text}")
            return None
    except Exception as e:
        print(f"❌ [이미지 서버 통신 에러] {e}")
        return None

def publish_to_ghost(title, html_content, category, tier, feature_image_url):
    print(f"📝 Ghost 웹사이트에 '{title}' 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = {'Authorization': f'Ghost {token}', 'Content-Type': 'application/json'}
        
        visibility_setting = "public" if tier == "Basic" else "paid"
        
        post_dict = {
            "title": title, 
            "html": html_content,
            "status": "published",
            "visibility": visibility_setting,
            "tags": [{"name": category}, {"name": tier}] 
        }
        
        # 🚨 [새로운 기능] 나노바나나가 그린 이미지가 있다면 메인 썸네일로 꽂아 넣습니다!
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
                print(f"  -> {tier} 등급 리포트 작성 중...")
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
