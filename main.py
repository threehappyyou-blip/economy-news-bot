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

print("=======================================")
print(" 🚀 40년 경력 미국 전문가 + 전면 무료(Flash) 테스트 봇 🚀")
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
CATEGORIES = {
    "Economy": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "https://finance.yahoo.com/news/rssindex"
    ],
    "Politics": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113"
    ],
    "Tech": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"
    ],
    "Health": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108"
    ],
    "Energy": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810"
    ]
}

# 🚨 [에러 완벽 수정] 텅 비어있던 TIERS 명단에 등급을 완벽하게 채웠습니다.
TIERS =

TIER_LABELS = {
    "Basic": "🌱 Free",
    "Premium": "💎 Pro",
    "Royal Premium": "👑 VIP"
}

def get_category_news(urls, count=30):
    news_list =
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
        
        # 🚨 [제자님 원칙 100% 반영] 비용 발생 전면 차단! 모든 등급을 무료(Flash) 모델로 고정!
        model_name = "gemini-2.5-flash"  
        
        # 분석 깊이는 제자님의 기획대로 철저하게 다르게 유지합니다.
        if tier == "Basic":
            news_count = "3"
            depth = "Focus strictly on the objective FACTS (What happened). Keep it concise but spark curiosity."
        elif tier == "Premium":
            news_count = "5"
            depth = "Focus on the 'WHY' using Behavioral Economics and Psychology. Explain the irrational market psychology behind the facts."
        else: 
            news_count = "10"
            depth = "Use the ultimate 'WHY / THINK / DIFFERENT THINK' framework. First, explain 'WHY' this happened. Second, explain what the masses 'THINK' (herd behavior). Third, provide a 'DIFFERENT THINK' (contrarian, historical, or philosophical perspective) to uncover the true hidden opportunity."

        # [분야별 40년 경력 미국 현지 전문가 페르소나 동적 할당]
        if category == "Politics":
            expert_persona = "a veteran US political expert with over 40 years of experience in Washington D.C. and global geopolitics"
        elif category == "Tech":
            expert_persona = "a veteran US technology expert with over 40 years of experience in Silicon Valley and global tech trends"
        elif category == "Health":
            expert_persona = "a veteran US healthcare expert with over 40 years of experience in the medical industry and bio-innovation"
        elif category == "Energy":
            expert_persona = "a veteran US energy expert with over 40 years of experience in global energy markets and infrastructure"
        else: 
            expert_persona = "a veteran US economic expert with over 40 years of experience in Wall Street and global macroeconomics"

        prompt = f"""
        [Goal] Write a highly insightful, deeply humanized blog post in English for the '{category}' section of the 'Warm Insight' website.
        {tier} Subscribers who want financial freedom and peace of mind.
        
        You are {expert_persona}. You are internally simulating a debate among top-tier experts, but YOU are writing the final output based on your 40 years of deep experience.
        
        1. NEVER use words like 'professor', 'economist', 'expert', or 'executive'.
        2. Humanize the content: Write like a wise, warm, 40-year experienced mentor. Use "We" or "I" to build strong emotional rapport.
        3. Mix short, punchy sentences with longer, reflective ones to create a natural human rhythm.
        4. Provide an 'emotional safety net': Comfort the reader's anxiety about market volatility or tech changes.
        5. If a news story is an ONGOING event, explicitly analyze what NEW information has been added today and how it changes previous assumptions.
        6. Format in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>). Do NOT use markdown (**). Do NOT include ```html.
        
        The VERY FIRST LINE must be exactly: TITLE: (Insert Catchy Title)
        The SECOND LINE must be exactly: IMAGE_PROMPT: (Insert English prompt for Nano Banana image generation, e.g., cinematic, 8k, abstract 3D)
        From the THIRD LINE onwards, write the HTML content:
        
        <h2>The Big Picture</h2>
        <p>(A warm, humanized 3-sentence summary of today's {category} news.)</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <ul>
            <li><strong>(Headline 1):</strong> (Fact + {depth} + Ongoing event update if applicable)</li>
        </ul>
        
        <h2>Today's Warm Insight</h2>
        <p>(A comforting, actionable takeaway regarding asset allocation or mindset to help readers feel safe.)</p>
        
        <p><strong>P.S.</strong> (Add a very short, relatable, human-like personal thought or anecdote about today's market vibe to build strong emotional rapport.)</p>
        
        <p><em>Disclaimer: This article is for informational purposes only. All decisions are your own.</em></p>

        Raw News to Analyze:
        {selected_news}
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        raw_text = response.text.replace("```html", "").replace("```", "").strip()
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()!= ""]
        
        pretty_tier = TIER_LABELS.get(tier, tier)
        title = f"[{pretty_tier}] Daily {category} Insight"
        image_prompt = f"Abstract 3D illustration representing global {category}, cinematic lighting, high quality, 8k resolution."
        
        if len(lines) > 0 and lines.startswith("TITLE:"):
            title = f"[{pretty_tier}] " + lines.pop(0).replace("TITLE:", "").strip()
                
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
        api_base = "[https://generativelanguage.googleapis.com](https://generativelanguage.googleapis.com)"
        url = f"{api_base}/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"
        
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
                for pred in predictions:
                    b64_img = pred.get('bytesBase64Encoded', '')
                    return base64.b64decode(b64_img)
        else:
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
            images = response.json().get('images')
            if images:
                for img in images:
                    return img.get('url')
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
            print("🎉 [성공] 자동 발행 완료!")
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
                    
                # 🚨 무료(Flash) 모델만 쓰더라도 안정적인 썸네일 생성을 위해 15초 대기
                time.sleep(15) 

        print("\n🎉 모든 카테고리 썸네일 및 지능형 자동 발행이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
