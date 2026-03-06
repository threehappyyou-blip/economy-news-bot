import os
import sys
import traceback
import time
import requests
import jwt
from datetime import datetime
import feedparser
import pytz
from google import genai

print("=======================================")
print(" 🚀 Ghost 카테고리별 자동 포스팅 봇 가동 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not all():
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다.")
    sys.exit(1)

# URL 끝의 슬래시 제거하여 통신 에러 방지
GHOST_API_URL = GHOST_API_URL.rstrip('/')

# 🚨 [카테고리별 글로벌 뉴스 소스 세팅]
# 제자님이 만든 5개의 방에 맞게, 뉴스 수집 사이트도 5개로 완벽하게 나눴습니다!
CATEGORIES = {
    "Economy":,
    "Politics": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113"],
    "Tech": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"],
    "Health": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108"],
    "Energy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810"]
}

def get_category_news(urls, count=5):
    news_list =
    seen_titles = set()
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.title in seen_titles: continue
                news_list.append(f"- {entry.title}: {entry.summary if 'summary' in entry else ''}")
                seen_titles.add(entry.title)
                if len(news_list) >= 15: break
        except Exception:
            continue
    return news_list[:count]

def analyze_with_gemini(news_items, category):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        selected_news = "\n".join(news_items)
        
        # 🚨 [8명 전문가 맞춤형 프롬프트] 카테고리(Economy, Health 등)에 따라 전문가들의 포커스가 바뀝니다.
        prompt = f"""
        [Goal] Write a highly insightful, warm, and easy-to-understand blog post in English for the '{category}' section of our website.
        [Persona] A panel of 8 top-tier experts (Economics, Psychology, Tech, Humanities, Politics, Healthcare, Energy, Philosophy) debating and synthesizing ideas to help everyday people achieve financial freedom and peace of mind.
        The current category is '{category}'. The 8 experts should heavily focus their debate on how these '{category}' news items impact everyday life, human psychology, and long-term financial well-being.

       
        1. Format the entire response in clean HTML tags (like <h2>, <p>, <ul>, <li>, <strong>) so it looks beautiful on a Ghost website.
        2. Do NOT use markdown symbols like ** or #. Use HTML only.
        3. Do NOT include ```html at the beginning or end.

       
        <h2>The Big Picture</h2>
        <p>(A friendly, 3-sentence summary of today's {category} news vibe and why it matters to regular people. Write in a warm, 'Milk Road' friendly tone.)</p>
        
        <h2>Top Drivers & Expert Insights</h2>
        <ul>
            <li><strong>(News Headline 1):</strong> (Explain the FACT simply. Then, add the 8-expert panel's psychological/philosophical 'WHY' behind it.)</li>
            <li><strong>(News Headline 2):</strong> (FACT + Expert 'WHY')</li>
            <li><strong>(News Headline 3):</strong> (FACT + Expert 'WHY')</li>
        </ul>
        
        <h2>Today's Happy Insight</h2>
        <p>(Provide a comforting, actionable takeaway or mindset tip related to {category} to help readers feel safe and smart about their future.)</p>
        
        <p><em>Disclaimer: This article is for informational and educational purposes only. All decisions are your own.</em></p>

       
        {selected_news}
        """
        
        # 429 에러 없는 안정적인 최신 2.5-flash 모델 사용
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # 웹사이트에 예쁘게 올라가도록 잔여 코드 블록 기호 제거
        clean_html = response.text.replace("```html", "").replace("```", "").strip()
        return clean_html
    except Exception as e:
        print(f"⚠️ [AI 에러] {category} 분석 실패: {e}")
        return None

def generate_ghost_token():
    """Ghost API 인증을 위한 1회용 마스터 출입증 생성"""
    id, secret = GHOST_ADMIN_API_KEY.split(':')
    iat = int(datetime.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {'iat': iat, 'exp': iat + 5 * 60, 'aud': '/admin/'}
    return jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)

def publish_to_ghost(title, html_content, category):
    print(f"📝 Ghost 웹사이트의 '{category}' 카테고리로 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers = {
            'Authorization': f'Ghost {token}',
            'Content-Type': 'application/json'
        }
        
        # 🚨 [카테고리 꽂아넣기] tags에 카테고리 이름을 넣어, 제자님이 만든 상단 메뉴에 정확히 들어가게 합니다.
        post_data = {
            "posts": [{
                "title": title,
                "html": html_content,
                "status": "published",
                "tags": [{"name": category}] 
            }]
        }
        
        url = f"{GHOST_API_URL}/ghost/api/admin/posts/?source=html"
        response = requests.post(url, json=post_data, headers=headers)
        
        if response.status_code in :
            print(f"🎉 [성공] '{category}' 카테고리에 글 발행 완료!")
        else:
            print(f"❌ [발행 실패] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ [통신 에러] Ghost 서버 연결 실패: {e}")

if __name__ == "__main__":
    try:
        today_str = datetime.now().strftime("%Y-%m-%d %H:00")
        
        # 5개의 카테고리를 순서대로 돌면서 뉴스를 수집하고, 분석하고, 웹사이트에 발행합니다.
        for category, urls in CATEGORIES.items():
            print(f"\n--- [{category}] 카테고리 작업 시작 ---")
            
            news = get_category_news(urls, 5)
            if not news:
                print(f"⚠️ {category} 뉴스가 없어 건너뜁니다.")
                continue
                
            report_html = analyze_with_gemini(news, category)
            
            if report_html:
                post_title = f"[{category}] Daily Insight & Warm Thoughts - {today_str}"
                publish_to_ghost(post_title, report_html, category)
                
            time.sleep(15) # 구글 서버 과부하 방지용 휴식

        print("\n🎉 5개 카테고리 자동 발행이 모두 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
