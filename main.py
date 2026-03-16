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
print(" 🚀 13인 전문가 + Why/Think/Different Think 지능형 발행 봇 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ (시스템 중단) API 키 또는 Ghost 출입증이 없습니다.")
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

# 🚨 [새로운 발행 지시서] 
# 각 카테고리마다: Basic 3건 -> Premium 2건 -> Royal 1건 순서로 총 6건의 다른 뉴스를 발행합니다!
TASKS = list()
task1 = dict(); task1.update({"tier": "Basic", "count": 3}); TASKS.append(task1)
task2 = dict(); task2.update({"tier": "Basic", "count": 3}); TASKS.append(task2)
task3 = dict(); task3.update({"tier": "Basic", "count": 3}); TASKS.append(task3)
task4 = dict(); task4.update({"tier": "Premium", "count": 5}); TASKS.append(task4)
task5 = dict(); task5.update({"tier": "Premium", "count": 5}); TASKS.append(task5)
task6 = dict(); task6.update({"tier": "Royal Premium", "count": 10}); TASKS.append(task6)

TIER_LABELS = dict()
TIER_LABELS.update({"Basic": "🌱 Free"})
TIER_LABELS.update({"Premium": "💎 Pro"})
TIER_LABELS.update({"Royal Premium": "👑 VIP"})

def get_category_news(urls, max_count=30):
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
                if len(news_list) >= max_count: break
        except Exception:
            continue
            
    # 대괄호 슬라이싱 에러를 피하기 위해 pop()으로 안전하게 뽑아냅니다.
    final_news = list()
    for _ in range(max_count):
        if len(news_list) > 0:
            final_news.append(news_list.pop(0))
    return final_news

def analyze_with_gemini(news_items, category, tier):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        selected_news = "\n".join(news_items)
        
        # 🚨 제자님의 전략: 등급에 따른 명확한 차별화 프롬프트!
        if tier == "Basic":
            model_name = "gemini-2.5-flash"  
            depth = "Focus ONLY on the objective FACTS (What happened). Keep it concise but spark curiosity for the paid version."
        elif tier == "Premium":
            model_name = "gemini-2.5-pro"    
            depth = "Focus on the 'WHY' using Behavioral Economics and Psychology. Explain the irrational market psychology behind the facts."
        else: 
            model_name = "gemini-3.1-pro-preview"    
            depth = "Use the ultimate 'WHY / THINK / DIFFERENT THINK' framework. First, explain 'WHY' this happened. Second, explain what the masses 'THINK' (herd behavior). Third, provide a 'DIFFERENT THINK' (contrarian, historical, or philosophical perspective) to uncover the true hidden opportunity."

        prompt = f"""
        (Goal) Write a highly insightful, humanized blog post in English for the '{category}' section of our website.
        Target Audience: {tier} Subscribers looking for financial freedom.
        
        (Persona) A wise, warm, 30-year experienced mentor. Use "We" or "I" to build emotional rapport. NEVER use words like 'professor', 'expert', or 'economist'.
        
        (Instructions)
        - Analyze the news based on this depth: {depth}
        - STRICT RULE: Format the response in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>). Do NOT use markdown (**). Do NOT include ```html.
        
        The VERY FIRST LINE must be exactly: TITLE: (Insert Catchy Title)
        The SECOND LINE must be exactly: IMAGE_PROMPT: (Insert English prompt for cinematic image generation)
        From the THIRD LINE onwards, write the HTML content:
        
        <h2>The Big Picture</h2>
        <p>(A warm, humanized 3-sentence summary of the news.)</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <ul>
            <li><strong>(Headline 1):</strong> (Fact + Your deep insight based on the tier's instructions)</li>
        </ul>
        
        <h2>Today's Warm Insight</h2>
        <p>(A comforting, actionable takeaway to help readers feel safe.)</p>
        
        <p><strong>P.S.</strong> (Add a very short, relatable personal thought about today's market vibe.)</p>
        <p><em>Disclaimer: This article is for informational purposes only. All decisions are your own.</em></p>

        Raw News to Analyze:
        {selected_news}
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        raw_text = response.text.replace("```html", "").replace("```", "").strip()
        lines = raw_text.split('\n')
        
        pretty_tier = TIER_LABELS.get(tier, tier)
        title = "({tier}) Daily {category} Insight".format(tier=pretty_tier, category=category)
        image_prompt = "Abstract 3D illustration representing global {category}, cinematic lighting, high quality, 8k resolution.".format(category=category)
        
        # 첫 번째 줄에서 제목 뽑기
        if len(lines) > 0:
            first_line = lines.pop(0)
            if "TITLE:" in first_line:
                title = "({tier}) ".format(tier=pretty_tier) + first_line.replace("TITLE:", "").strip()
            else:
                lines.insert(0, first_line)
                
        # 두 번째 줄에서 이미지 프롬프트 뽑기
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
        api_base = "https://" + "generativelanguage.googleapis.com"
        url = api_base + "/v1beta/models/imagen-3.0-generate-002:predict?key=" + GEMINI_API_KEY
        
        headers = dict()
        headers.update({'Content-Type': 'application/json'})
        
        params = dict()
        params.update({"sampleCount": 1})
        params.update({"aspectRatio": "16:9"})
        params.update({"outputOptions": {"mimeType": "image/jpeg"}})
        
        data = dict()
        data.update({"instances": [{"prompt": image_prompt}]})
        data.update({"parameters": params})
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            predictions = response.json().get('predictions')
            if predictions:
                for pred in predictions:
                    b64_img = pred.get('bytesBase64Encoded', '')
                    return base64.b64decode(b64_img)
        else:
            print(f"⚠️ (이미지 API 에러): {response.status_code} - {response.text}")
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
        post_data = dict(posts=posts_list)
        
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
            print(f"\n--- [{category}] 지능형 큐레이션 및 분배 시작 ---")
            
            # 카테고리별로 30개의 뉴스를 가득 담아옵니다.
            all_news = get_category_news(urls, count=30)
            if not all_news or len(all_news) < 3:
                continue
            
            # 🚨 뉴스를 순서대로 쪼개어(pop) 각 등급별 기사에 중복 없이 배정합니다!
            for task in TASKS:
                tier = task.get("tier")
                req_count = task.get("count")
                
                # 남은 뉴스가 부족하면 다음 카테고리로 넘어갑니다.
                if len(all_news) < req_count:
                    break
                
                target_news = list()
                for _ in range(req_count):
                    target_news.append(all_news.pop(0))
                
                print(f"  -> ({tier}) 등급 리포트 ({req_count}개 뉴스) 및 썸네일 생성 중...")
                post_title, img_prompt, report_html = analyze_with_gemini(target_news, category, tier)
                
                if report_html and post_title:
                    feature_image_url = None
                    if img_prompt:
                        image_bytes = generate_thumbnail(img_prompt)
                        if image_bytes:
                            feature_image_url = upload_image_to_ghost(image_bytes)
                            
                    publish_to_ghost(post_title, report_html, category, tier, feature_image_url)
                    
                # 구글 모델 과부하를 막기 위해 기사 1건 발행 후 20초 휴식 (필수)
                time.sleep(20) 

        print("\n🎉 모든 카테고리 중복 없는 지능형 자동 발행이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
