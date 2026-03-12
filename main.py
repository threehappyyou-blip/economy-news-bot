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
print(" 🚀 구독 등급별 다중 AI 모델 Ghost 발행 봇 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

GHOST_API_URL = GHOST_API_URL.rstrip('/')

# [카테고리별 글로벌 뉴스 소스 세팅]
CATEGORIES = {
    "Economy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", "https://finance.yahoo.com/news/rssindex"],
    "Politics": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113"],
    "Tech": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910"],
    "Health": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108"],
    "Energy": ["https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810"]
}

# 🚨 [새로운 기능] 발행할 3가지 구독 등급 세팅
TIERS =

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
        
        # 🚨 [핵심 업데이트] 등급에 따라 'AI 모델'과 '분석 깊이'를 철저히 분리합니다!
        if tier == "Basic":
            model_name = "gemini-2.5-flash"  # 비용 최적화! 빠르고 가성비 좋은 모델
            news_count = "3"
            depth = "Focus ONLY on the objective FACTS. Make it a quick, easy read."
        elif tier == "Premium":
            model_name = "gemini-3.1-pro"    # 최고급 지능! 유료 회원을 위한 심리 분석 모델
            news_count = "5"
            depth = "Focus on the 'WHY' behind the facts using behavioral economics and psychology. Provide deep, valuable insights that justify a paid subscription."
        else: # Royal Premium
            model_name = "gemini-3.1-pro"    # 최고급 지능! VIP를 위한 거시적 통찰 모델
            news_count = "10"
            depth = "Provide the ULTIMATE deep dive. Intertwine macroeconomic theory, behavioral psychology, and historical context. This is for VIP subscribers."

        prompt = f"""
        [Goal] Write a highly insightful, professional blog post in English for the '{category}' section of our Ghost website.
        {tier} Subscribers
        
        Phase 1: Intelligent Curation
        - Select ONLY the top {news_count} most critical news stories from the raw data.
        
        Phase 2: Panel Debate and Drafting
        - {depth}
        - Write in a professional, trustworthy, and insightful tone. 
        - STRICT RULE: Do NOT use overly casual greetings. Start directly with a polished, professional introduction.
        - Format the response in clean HTML tags (<h2>, <p>, <ul>, <li>, <strong>) for a Ghost website. Do NOT use markdown (**). Do NOT include ```html.
        
        The VERY FIRST LINE of your output MUST be the title of the post, starting exactly with "TITLE: ". Create a catchy, professional title. Do NOT include the date or time.
        
        Example Output Format:
        TITLE: (Insert Catchy Professional Title Here)
        <h2>The Big Picture</h2>
        <p>(A professional summary of today's {category} news.)</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <ul>
            <li><strong>(Headline 1):</strong> (Fact + Insights matching the {tier} depth)</li>
        </ul>
        
        <h2>Today's Insight</h2>
        <p>(A comforting, actionable takeaway for {tier} readers.)</p>
        
        <p><em>Disclaimer: This article is for informational purposes only. All decisions are your own.</em></p>

        Raw News to Analyze:
        {selected_news}
        """
        
        # 지정된 모델(Flash 또는 Pro)을 사용하여 생성합니다.
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        raw_text = response.text.replace("```html", "").replace("```", "").strip()
        lines = raw_text.split('\n')
        
        title = f"[{tier}] Daily {category} Insight" 
        html_content = raw_text
        
        # 첫 줄이 TITLE: 로 시작하면 제목으로 분리
        if len(lines) > 0 and lines.startswith("TITLE:"):
            title = f"[{tier}] " + lines.replace("TITLE:", "").strip()
            html_content = "\n".join(lines[1:]).strip()
            
        return title, html_content
        
    except Exception as e:
        print(f"⚠️ [AI 에러] {category} - {tier} 분석 실패: {e}")
        return None, None

def generate_ghost_token():
    id_str, secret_str = GHOST_ADMIN_API_KEY.split(':')
    iat = int(datetime.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id_str}
    payload = {'iat': iat, 'exp': iat + 5 * 60, 'aud': '/admin/'}
    return jwt.encode(payload, bytes.fromhex(secret_str), algorithm='HS256', headers=header)

def publish_to_ghost(title, html_content, category, tier):
    print(f"📝 Ghost 웹사이트에 '{category} - {tier}' 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = {'Authorization': f'Ghost {token}', 'Content-Type': 'application/json'}
        
        # 🚨 [새로운 마법] Basic은 누구나 볼 수 있게 'public', Premium/Royal은 결제한 사람만 볼 수 있게 'paid'로 자동 잠금 처리합니다!
        visibility_setting = "public" if tier == "Basic" else "paid"
        
        post_data = {
            "posts": [{
                "title": title, 
                "html": html_content,
                "status": "published",
                "visibility": visibility_setting,
                "tags": [{"name": category}, {"name": tier}] 
            }]
        }
        
        url = f"{GHOST_API_URL}/ghost/api/admin/posts/?source=html"
        response = requests.post(url, json=post_data, headers=headers_dict)
        
        if response.status_code in (200, 201):
            print(f"🎉 [성공] '{title}' 자동 발행 완료!")
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
                print(f"⚠️ {category} 뉴스가 없어 건너뜁니다.")
                continue
                
            # 하나의 카테고리에 대해 Basic, Premium, Royal 3가지 버전을 차례대로 생성하고 발행합니다.
            for tier in TIERS:
                print(f"  -> {tier} 등급 리포트 작성 중...")
                post_title, report_html = analyze_with_gemini(news, category, tier)
                
                if report_html and post_title:
                    publish_to_ghost(post_title, report_html, category, tier)
                    
                # 최고급 Pro 모델의 과부하를 막기 위해 1건 발행 후 20초 휴식
                time.sleep(20) 

        print("\n🎉 모든 카테고리 & 등급별 지능형 자동 발행이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
