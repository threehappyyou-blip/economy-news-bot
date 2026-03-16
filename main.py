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
print(" 🚀 13인 전문가 + 나노바나나 + 밀크로드 스타일 봇 가동 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")
SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

SENDER_EMAIL = "threehappyyou@gmail.com" 

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

GHOST_API_URL = GHOST_API_URL.rstrip('/')

# 🚨 [구독자 명단 5명 세팅]
raw_subs = "threehappyyou@gmail.com/Basic,threehappyyou@gmail.com/Basic,threehappyyou@gmail.com/Premium,threehappyyou@gmail.com/Premium,threehappyyou@gmail.com/Royal Premium"
SUBSCRIBERS = list()
for sub_info in raw_subs.split(","):
    e_mail, e_tier = sub_info.split("/")
    SUBSCRIBERS.append(dict(email=e_mail, tier=e_tier))

# 🚨 [카테고리 세팅]
CATEGORIES = dict()
cat_eco = list(); cat_eco.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"); cat_eco.append("https://finance.yahoo.com/news/rssindex")
CATEGORIES.update({"Economy": cat_eco})

cat_pol = list(); cat_pol.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113")
CATEGORIES.update({"Politics": cat_pol})

cat_tech = list(); cat_tech.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910")
CATEGORIES.update({"Tech": cat_tech})

cat_health = list(); cat_health.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108")
CATEGORIES.update({"Health": cat_health})

cat_energy = list(); cat_energy.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810")
CATEGORIES.update({"Energy": cat_energy})

TIERS = ("Basic", "Premium", "Royal Premium")
TIER_LABELS = {"Basic": "🌱 Free", "Premium": "💎 Pro", "Royal Premium": "👑 VIP"}

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
            depth = "Focus ONLY on the objective FACTS. Make it a quick, easy read."
        elif tier == "Premium":
            model_name = "gemini-2.5-pro"    
            news_count = "5"
            depth = "Focus on the 'WHY' behind the facts using behavioral economics and psychology."
        else: 
            model_name = "gemini-3.1-pro-preview"    
            news_count = "10"
            depth = "Provide the ULTIMATE deep dive using macroeconomic theory, psychology, and historical context."

        # 🚨 [밀크로드식 구조 + 프로페셔널 톤] 프롬프트 혁신!
        prompt = f"""
        [Goal] Write a highly insightful, highly readable blog post in English for the '{category}' section of our Ghost website.
        {tier} Subscribers
        
       
        1. Smart Brevity: Keep paragraphs very short (1-3 sentences max). Use bullet points to break up long text.
        2. Analogies: Explain complex financial or tech jargon using simple, everyday analogies (like vacuum cleaners or chessboards).
        3. Professional Tone: Maintain a trustworthy, authoritative tone. NO overly casual greetings like 'Hey there, neighbor!'. Start directly with a polished, professional hook.
        4. Focus on the "So What?": Clearly translate the news into how it impacts the reader's financial future.
        
        [Phase 1 & 2 Instructions]
        - Select ONLY the top {news_count} most critical news stories from the raw data.
        - The experts debate the 'WHY' based on the depth: {depth}
        - Format the response in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>) for a Ghost website. Do NOT use markdown (**). Do NOT include ```html.
        
        The VERY FIRST LINE must be exactly: TITLE: (Insert Catchy, Professional Title Here)
        The SECOND LINE must be exactly: IMAGE_PROMPT: (Insert English prompt for image generation, cinematic 8k)
        From the THIRD LINE onwards, write the HTML content.
        
        Example HTML Structure:
        <h2>The Big Picture (TL;DR)</h2>
        <p>(A punchy, 3-sentence summary of today's {category} news.)</p>
        
        <h2>Deep Dive & The 'Why'</h2>
        <ul>
            <li><strong>(Headline 1):</strong> (Fact + Simple Analogy + The deep 'WHY' debated by experts)</li>
            <li><strong>(Headline 2):</strong> (Fact + Simple Analogy + The deep 'WHY')</li>
        </ul>
        
        <h2>The Takeaway (Why It Matters)</h2>
        <p>(A comforting, actionable insight to help readers navigate this market.)</p>
        
        <p><em>Disclaimer: This article is for informational and educational purposes only. All decisions are your own.</em></p>

        Raw News to Analyze:
        {selected_news}
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        raw_text = response.text.replace("```html", "").replace("```", "").strip()
        lines = [line for line in raw_text.split('\n') if line.strip()!= ""]
        
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
        url = "[https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=](https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=)" + GEMINI_API_KEY
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
        
        # 1000명 돌파 전까지 무조건 전체 공개(Public)
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
            print(f"🎉 [성공] 발행 완료!")
        else:
            print(f"❌ [발행 실패] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ [통신 에러] Ghost 서버 연결 실패: {e}")

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

def send_email(report_content, to_email, tier, category, title):
    if not SENDER_PASSWORD:
        return
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    msg = MIMEMultipart()
    msg.add_header("From", SENDER_EMAIL)
    msg.add_header("To", to_email)
    msg.add_header("Subject", f"{title}")

    msg.attach(MIMEText(report_content, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"🎉 [성공] {to_email} 님에게 이메일 발송 완료!")
    except Exception as e:
        print(f"❌ [실패] 메일 발송 실패: {str(e)}")

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
                    
                    # 이메일도 예쁜 라벨이 달린 제목으로 전송됩니다!
                    for sub in SUBSCRIBERS:
                        if sub.get("tier") == tier:
                            send_email(report_html, sub.get("email"), tier, category, post_title)
                            
                time.sleep(20) 

        print("\n🎉 모든 카테고리 썸네일 및 지능형 자동 발행이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
