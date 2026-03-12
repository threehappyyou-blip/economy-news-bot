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
print(" 🚀 13인 전문가 Ghost 자동 포스팅 봇 가동 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not all():
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

# URL 끝의 슬래시 제거하여 통신 에러 방지
GHOST_API_URL = GHOST_API_URL.rstrip('/')

# 🚨 [카테고리별 글로벌 뉴스 소스 세팅]
CATEGORIES = {
    "Economy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "https://finance.yahoo.com/news/rssindex"],
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
        
        # 🚨 [핵심!] 제자님이 슈퍼 젬스에서 테스트했던 13인 전문가 릴레이 구조를 파이썬 프롬프트로 완벽히 압축 이식했습니다!
        prompt = f"""
        [Goal] Write a highly insightful, warm, and easy-to-understand blog post in English for the '{category}' section of our Ghost website.
        [Persona] You are simulating a panel of 13 top-tier experts (Master PM, Economists, Psychologists, Historians, Philosophers, Senior Editor, Art Director, Fact-checker, Legal, Ghost UI Expert).
        
       
        1. The experts debate the news to find the deepest 'WHY' (combining behavioral psychology, history, and macroeconomics).
        2. The Senior Editor writes the final post in a warm, easy, 'neighborhood friend' tone. No academic jargon like 'professor' or 'expert'.
        3. The Ghost UI Expert formats the entire response in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>) for a Ghost website.
        4. Do NOT use markdown symbols like ** or #. Use HTML only. Do NOT include ```html at the beginning or end.
        5. The Legal expert must include: "Disclaimer: This article is for informational and educational purposes only. All investment decisions are your own." at the end.
        
       
        <h2>The Big Picture</h2>
        <p>(3-sentence warm summary of today's {category} news and why it matters to regular people, written in Axios/Milk Road style.)</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <ul>
            <li><strong>(News Headline 1):</strong> (Fact + The deep psychological/historical 'WHY' debated by the 13 experts)</li>
            <li><strong>(News Headline 2):</strong> (Fact + The deep psychological/historical 'WHY')</li>
        </ul>
        
        <h2>Today's Happy Insight</h2>
        <p>(A comforting, actionable takeaway based on philosophy and history to help readers feel safe and confident about their financial freedom.)</p>
        
        <p><em>Disclaimer: This article is for informational and educational purposes only. All decisions are your own.</em></p>

       
        {selected_news}
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Ghost 사이트가 깨지지 않도록 불필요한 마크다운 코드 제거
        clean_html = response.text.replace("```html", "").replace("```", "").strip()
        return clean_html
    except Exception as e:
        print(f"⚠️ [AI 에러] {category} 분석 실패: {e}")
        return None

def generate_ghost_token():
    """Ghost API 출입증 생성"""
    id, secret = GHOST_ADMIN_API_KEY.split(':')
    iat = int(datetime.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {'iat': iat, 'exp': iat + 5 * 60, 'aud': '/admin/'}
    return jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)

def publish_to_ghost(title, html_content, category):
    """완성된 글을 Ghost 웹사이트에 자동 발행"""
    print(f"📝 Ghost 웹사이트의 '{category}' 카테고리로 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers = {
            'Authorization': f'Ghost {token}',
            'Content-Type': 'application/json'
        }
        
        # tags에 카테고리 이름을 넣어 자동으로 제자님의 메뉴에 맞게 분류됩니다!
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
        # 제목에 시간 추가
        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        for category, urls in CATEGORIES.items():
            print(f"\n--- [{category}] 카테고리 작업 시작 ---")
            
            news = get_category_news(urls, 5)
            if not news:
                print(f"⚠️ {category} 뉴스가 없어 건너뜁니다.")
                continue
                
            report_html = analyze_with_gemini(news, category)
            
            if report_html:
                post_title = f"Daily {category} Insight: The Big Picture ({today_str})"
                publish_to_ghost(post_title, report_html, category)
                
            time.sleep(15) # 구글 서버 과부하 방지

        print("\n🎉 5개 카테고리 웹사이트 자동 발행이 모두 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
