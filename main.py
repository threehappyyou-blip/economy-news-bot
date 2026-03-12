import os
import sys
import traceback
import time
import requests
import jwt
from datetime import datetime
import feedparser
from google import genai

print("=======================================")
print(" 🚀 13인 전문가 지능형 큐레이션 & Ghost 자동 발행 봇 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

GHOST_API_URL = GHOST_API_URL.rstrip('/')

# 🚨 카테고리 5개의 뉴스 출처를 튜플(Tuple)로 단단하게 묶어 에러를 방지했습니다.
CATEGORIES = {
    "Economy": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "https://finance.yahoo.com/news/rssindex"),
    "Politics": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113",),
    "Tech": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",),
    "Health": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108",),
    "Energy": ("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810",)
}

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

def analyze_with_gemini(news_items, category):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        selected_news = "\n".join(news_items)
        
        prompt = f"""
        [Goal] Write a highly insightful, warm, and easy-to-understand blog post in English for the '{category}' section of our Ghost website.
        [Persona] You are simulating a panel of 13 top-tier experts (Master PM, Economists, Psychologists, Historians, Philosophers, Senior Editor, Art Director, Fact-checker, Legal, Ghost UI Expert).
        
        Phase 1: Intelligent Curation by Master PM
        - Look at the raw news items provided below (up to 30 items).
        - As the Master PM, select ONLY the top 3 most critical news stories that will have the biggest impact on everyday people's financial freedom and psychology. Ignore repetitive or trivial news.
        
        Phase 2: Panel Debate and Drafting
        - Using ONLY those 3 selected news items, write the final blog post.
        - The experts debate the 'WHY' (behavioral psychology, history, macroeconomics).
        - The Senior Editor writes the final post in a warm, easy, 'neighborhood friend' tone (Milk Road style). No academic jargon.
        - Format the response in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>) for a Ghost website. Do NOT use markdown symbols like **. Do NOT include ```html.
        
        <h2>The Big Picture</h2>
        <p>(3-sentence warm summary of today's {category} news and why it matters to regular people.)</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <ul>
            <li><strong>(Selected News Headline 1):</strong> (Fact + The deep psychological/historical 'WHY' debated by experts)</li>
            <li><strong>(Selected News Headline 2):</strong> (Fact + The deep psychological/historical 'WHY')</li>
            <li><strong>(Selected News Headline 3):</strong> (Fact + The deep psychological/historical 'WHY')</li>
        </ul>
        
        <h2>Today's Happy Insight</h2>
        <p>(A comforting, actionable takeaway to help readers feel safe about their financial freedom.)</p>
        
        <p><em>Disclaimer: This article is for informational and educational purposes only. All decisions are your own.</em></p>

        Raw News to Analyze:
        {selected_news}
        """
        
        # 🚨 [핵심 해결책] 429 에러(무료 한도 0번)가 발생하는 2.0 대신, 
        # 무료로 넉넉하게 쓸 수 있는 최신 'gemini-2.5-flash' 모델을 장착했습니다!
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        clean_html = response.text.replace("```html", "").replace("```", "").strip()
        return clean_html
    except Exception as e:
        print(f"⚠️ [AI 에러] {category} 분석 실패: {e}")
        return None

def generate_ghost_token():
    id_str, secret_str = GHOST_ADMIN_API_KEY.split(':')
    iat = int(datetime.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id_str}
    payload = {'iat': iat, 'exp': iat + 5 * 60, 'aud': '/admin/'}
    return jwt.encode(payload, bytes.fromhex(secret_str), algorithm='HS256', headers=header)

def publish_to_ghost(title, html_content, category):
    print(f"📝 Ghost 웹사이트 '{category}' 카테고리에 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = {'Authorization': f'Ghost {token}', 'Content-Type': 'application/json'}
        
        post_data = {
            "posts": [{
                "title": title,
                "html": html_content,
                "status": "published",
                "tags": [{"name": category}] 
            }]
        }
        
        url = f"{GHOST_API_URL}/ghost/api/admin/posts/?source=html"
        response = requests.post(url, json=post_data, headers=headers_dict)
        
        if response.status_code in (200, 201):
            print(f"🎉 [성공] '{category}' 자동 발행 완료!")
        else:
            print(f"❌ [발행 실패] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ [통신 에러] Ghost 서버 연결 실패: {e}")

if __name__ == "__main__":
    try:
        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        for category, urls in CATEGORIES.items():
            print(f"\n--- [{category}] 지능형 큐레이션 시작 ---")
            
            news = get_category_news(urls, count=30)
            if not news:
                print(f"⚠️ {category} 뉴스가 없어 건너뜁니다.")
                continue
                
            report_html = analyze_with_gemini(news, category)
            
            if report_html:
                post_title = f"Daily {category} Insight: The Big Picture ({today_str})"
                publish_to_ghost(post_title, report_html, category)
                
            # 🚨 서버 과부하를 넉넉히 방지하기 위해 15초를 대기합니다.
            time.sleep(15) 

        print("\n🎉 모든 카테고리 지능형 자동 발행이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
