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
    print("\n⛔ (시스템 중단) API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

GHOST_API_URL = GHOST_API_URL.rstrip('/')

# 🚨 [카테고리 세팅] 에러를 방지하기 위해 가장 안전한 함수형으로 묶었습니다.
CATEGORIES = dict()

cat_eco = list()
cat_eco.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664")
cat_eco.append("https://finance.yahoo.com/news/rssindex")
CATEGORIES.update({"Economy": cat_eco})

cat_pol = list()
cat_pol.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113")
CATEGORIES.update({"Politics": cat_pol})

cat_tech = list()
cat_tech.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910")
CATEGORIES.update({"Tech": cat_tech})

cat_health = list()
cat_health.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108")
CATEGORIES.update({"Health": cat_health})

cat_energy = list()
cat_energy.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810")
CATEGORIES.update({"Energy": cat_energy})

# 🚨 등급 세팅
TIERS = list()
TIERS.append("Basic")
TIERS.append("Premium")
TIERS.append("Royal Premium")

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
        
        # 🚨 [AI 모델 라우팅] 3.1 Pro 404 에러를 차단하고 2.5 Pro 및 최신 3.1 Preview 명칭으로 정확히 지정!
        if tier == "Basic":
            model_name = "gemini-2.5-flash"  
            news_count = "3"
            depth = "Focus ONLY on the objective FACTS. Make it a quick, easy read."
        elif tier == "Premium":
            model_name = "gemini-2.5-pro"    
            news_count = "5"
            depth = "Focus on the 'WHY' behind the facts using behavioral economics and psychology. Provide deep, valuable insights that justify a paid subscription."
        else: 
            model_name = "gemini-3.1-pro-preview"    
            news_count = "10"
            depth = "Provide the ULTIMATE deep dive using macroeconomic theory, psychology, and historical context. This is for VIP subscribers."

        prompt = f"""
        (Goal) Write a highly insightful, professional blog post in English for the '{category}' section of our Ghost website.
        {tier} Subscribers
        
        (Phase 1: Intelligent Curation)
        - Select ONLY the top {news_count} most critical news stories from the raw data.
        
        (Phase 2: Panel Debate and Drafting)
        - {depth}
        - STRICT RULE: Write in a professional, trustworthy, and insightful tone. No casual greetings like 'Hey there'. Start directly with a polished introduction.
        - Format the response in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>) for a Ghost website. Do NOT use markdown (**). Do NOT include ```html.
        
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
        lines = raw_text.split('\n')
        
        title = "({tier}) Daily {category} Insight".format(tier=tier, category=category)
        image_prompt = "Abstract 3D illustration representing global {category}, cinematic lighting, high quality, 8k resolution.".format(category=category)
        
        if len(lines) > 0:
            first_line = lines.pop(0)
            if "TITLE:" in first_line:
                title = "[{}] ".format(tier) + first_line.replace("TITLE:", "").strip()
            else:
                lines.insert(0, first_line)
                
        if len(lines) > 0:
            second_line = lines.pop(0)
            if "IMAGE_PROMPT:" in second_line:
                image_prompt = second_line.replace("IMAGE_PROMPT:", "").strip()
            else:
                lines.insert(0, second_line)
                
        html_content = "\n".join(lines).strip()
            
        return title, image_prompt, html_content
        
    except Exception as e:
        print(f"⚠️ (AI 에러) {category} - {tier} 분석 실패: {e}")
        return None, None, None

def generate_thumbnail(image_prompt):
    print(f"🎨 나노바나나 AI 썸네일 생성 중... (프롬프트: {image_prompt})")
    try:
        # 🚨 [가장 중요한 수정] 오류를 내던 주소 방식을 버리고, 구글 공식 파이썬 라이브러리로 이미지를 안전하게 요청합니다!
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_images(
            model='gemini-3.1-flash-image-preview',
            prompt=image_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="16:9" 
            )
        )
        for generated_image in response.generated_images:
            return generated_image.image.image_bytes
        return None
    except Exception as e:
        print(f"⚠️ (이미지 생성 에러): {e}")
        return None

def generate_ghost_token():
    id_str, secret_str = GHOST_ADMIN_API_KEY.split(':')
    iat = int(datetime.now().timestamp())
    header = dict(alg='HS256', typ='JWT', kid=id_str)
    payload = dict(iat=iat, exp=iat + 5 * 60, aud='/admin/')
    return jwt.encode(payload, bytes.fromhex(secret_str), algorithm='HS256', headers=header)

def upload_image_to_ghost(image_bytes):
    try:
        token = generate_ghost_token()
        headers = dict()
        headers.update({'Authorization': 'Ghost ' + token})
        
        files = dict()
        files.update({'file': ('thumbnail.jpg', image_bytes, 'image/jpeg')})
        files.update({'purpose': (None, 'image')})
        
        url = GHOST_API_URL + "/ghost/api/admin/images/upload/"
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200 or response.status_code == 201:
            images = response.json().get('images')
            if images:
                for img in images:
                    return img.get('url')
        else:
            print(f"❌ (이미지 업로드 실패) {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ (이미지 통신 에러) {e}")
        return None

def publish_to_ghost(title, html_content, category, tier, feature_image_url):
    print(f"📝 Ghost 웹사이트에 '{title}' 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = dict()
        headers_dict.update({'Authorization': 'Ghost ' + token})
        headers_dict.update({'Content-Type': 'application/json'})
        
        # 1000명 모일 때까지 모두 무료 공개(Public)!
        visibility_setting = "public"
        
        tag_dict = dict(name=category)
        tier_dict = dict(name=tier)
        tags_list = list()
        tags_list.append(tag_dict)
        tags_list.append(tier_dict)
        
        post_dict = dict()
        post_dict.update({"title": title})
        post_dict.update({"html": html_content})
        post_dict.update({"status": "published"})
        post_dict.update({"visibility": visibility_setting})
        post_dict.update({"tags": tags_list})
        
        if feature_image_url:
            post_dict.update({"feature_image": feature_image_url})
            
        posts_list = list()
        posts_list.append(post_dict)
        
        post_data = dict()
        post_data.update({"posts": posts_list})
        
        url = GHOST_API_URL + "/ghost/api/admin/posts/?source=html"
        response = requests.post(url, json=post_data, headers=headers_dict)
        
        if response.status_code == 200 or response.status_code == 201:
            print("🎉 (성공) 자동 발행 완료!")
        else:
            print(f"❌ (발행 실패) {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ (통신 에러) Ghost 서버 연결 실패: {e}")

if __name__ == "__main__":
    try:
        for category, urls in CATEGORIES.items():
            print(f"\n--- ({category}) 지능형 큐레이션 시작 ---")
            
            news = get_category_news(urls, count=30)
            if not news:
                continue
                
            for tier in TIERS:
                print(f"  -> ({tier}) 등급 리포트 및 썸네일 생성 중...")
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
