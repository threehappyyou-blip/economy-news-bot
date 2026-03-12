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
print(" 🚀 13인 전문가 지능형 큐레이션 & Ghost 봇 🚀")
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
    client = genai.Client(api_key=GEMINI_API_KEY)
    selected_news = "\n".join(news_items)
    
    prompt = f"""
    [Goal] Write a highly insightful, warm, and easy-to-understand blog post in English for the '{category}' section of our Ghost website.
    [Persona] You are simulating a panel of 13 top-tier experts (Master PM, Economists, Psychologists, Historians, Philosophers, Senior Editor, Art Director, Fact-checker, Legal, Ghost UI Expert).
    
    Phase 1: Intelligent Curation
    - Select ONLY the top 3 most critical news stories from the raw data.
    
    Phase 2: Panel Debate and Drafting
    - The experts debate the 'WHY' (behavioral psychology, history, macroeconomics).
    - The Senior Editor writes the final post in a warm, 'neighborhood friend' tone. No academic jargon.
    - Format in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>) for a Ghost website. Do NOT use markdown (**). Do NOT include ```html.
    
    <h2>The Big Picture</h2>
    <p>(3-sentence warm summary of today's {category} news and why it matters.)</p>
    
    <h2>Top Drivers & Deep Insights</h2>
    <ul>
        <li><strong>(Headline 1):</strong> (Fact + The deep 'WHY' debated by experts)</li>
        <li><strong>(Headline 2):</strong> (Fact + The deep 'WHY')</li>
        <li><strong>(Headline 3):</strong> (Fact + The deep 'WHY')</li>
    </ul>
    
    <h2>Today's Happy Insight</h2>
    <p>(A comforting, actionable takeaway to help readers feel safe about their financial freedom.)</p>
    
    <p><em>Disclaimer: This article is for informational and educational purposes only. All decisions are your own.</em></p>

    Raw News to Analyze:
    {selected_news}
    """
    
    # 🚨 [가장 안정적인 모델로 교체] 429 과부하 에러가 거의 없는 2.0-flash 로 변경했습니다.
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    
    if not response.text:
        raise Exception("AI가 응답을 생성하지 못했습니다. (API 한도 초과 또는 차단 의심)")
        
    clean_html = response.text.replace("```html", "").replace("```", "").strip()
    return clean_html

def generate_ghost_token():
    id_str, secret_str = GHOST_ADMIN_API_KEY.split(':')
    iat = int(datetime.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id_str}
    payload = {'iat': iat, 'exp': iat + 5 * 60, 'aud': '/admin/'}
    return jwt.encode(payload, bytes.fromhex(secret_str), algorithm='HS256', headers=header)

def publish_to_ghost(title, html_content, category):
    print(f"📝 Ghost 웹사이트 '{category}' 카테고리에 글을 발행합니다...")
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
        return True
    else:
        raise Exception(f"Ghost 발행 실패: {response.status_code} - {response.text}")

if __name__ == "__main__":
    success_count = 0
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
                is_published = publish_to_ghost(post_title, report_html, category)
                if is_published:
                    success_count += 1
                
            # 서버 무리를 막기 위해 휴식 시간을 20초로 대폭 늘렸습니다.
            time.sleep(20) 

        print(f"\n🎉 총 {success_count}개 카테고리 발행 완료!")
        
        # 🚨 [침묵의 에러 방지] 만약 단 1개도 발행되지 않았다면 깃허브에 빨간불을 띄웁니다!
        if success_count == 0:
            raise Exception("발행된 글이 0개입니다. AI API 한도 초과 또는 네트워크 문제입니다.")
            
    except Exception as e:
        print("\n❌ 시스템 에러 발생 (자세한 원인은 아래를 확인하세요)")
        traceback.print_exc()
        sys.exit(1)
