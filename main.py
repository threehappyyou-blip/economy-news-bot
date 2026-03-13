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

# 🚨 [에러 완벽 차단 1] 괄호가 지워지는 버그를 막기 위해, 가장 안전한 방식으로 카테고리를 세팅했습니다!
CATEGORIES = dict()

cat_eco = list()
cat_eco.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664")
cat_eco.append("https://finance.yahoo.com/news/rssindex")
CATEGORIES["Economy"] = cat_eco

cat_pol = list()
cat_pol.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113")
CATEGORIES["Politics"] = cat_pol

cat_tech = list()
cat_tech.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910")
CATEGORIES = cat_tech

cat_health = list()
cat_health.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108")
CATEGORIES["Health"] = cat_health

cat_energy = list()
cat_energy.append("https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810")
CATEGORIES["Energy"] = cat_energy

# 🚨 [에러 완벽 차단 2] 텅 비어서 에러가 났던 TIERS 부분도 절대 지워지지 않게 꽉 채웠습니다!
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
            depth = "Focus ONLY on the objective FACTS. Make it a quick, easy read."
        elif tier == "Premium":
            model_name = "gemini-2.5-pro"    
            news_count = "5"
            depth = "Focus on the 'WHY' behind the facts using behavioral economics and psychology. Provide deep, valuable insights that justify a paid subscription."
        else: # Royal Premium
            model_name = "gemini-3.1-pro-preview"    
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
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        raw_text = response.text.replace("```html", "").replace("```", "").strip()
        lines = raw_text.split('\n')
        
        title = f"[{tier}] Daily {category} Insight" 
        html_content = raw_text
        
        # 🚨 [제목 추출 에러 완벽 해결] lines 바구니의 '첫 번째 줄(lines)'을 정확히 가리키도록 수정했습니다!
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
    header = dict(alg='HS256', typ='JWT', kid=id_str)
    payload = dict(iat=iat, exp=iat + 5 * 60, aud='/admin/')
    return jwt.encode(payload, bytes.fromhex(secret_str), algorithm='HS256', headers=header)

def publish_to_ghost(title, html_content, category, tier):
    print(f"📝 Ghost 웹사이트에 '{category} - {tier}' 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = dict(Authorization='Ghost ' + token, Content_Type='application/json')
        
        visibility_setting = "public" if tier == "Basic" else "paid"
        
        tag_dict = dict(name=category)
        tier_dict = dict(name=tier)
        post_dict = dict(title=title, html=html_content, status="published", visibility=visibility_setting, tags=[tag_dict, tier_dict])
        post_data = dict(posts=[post_dict])
        
        url = GHOST_API_URL + "/ghost/api/admin/posts/?source=html"
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
                
            for tier in TIERS:
                print(f"  -> {tier} 등급 리포트 작성 중...")
                post_title, report_html = analyze_with_gemini(news, category, tier)
                
                if report_html and post_title:
                    publish_to_ghost(post_title, report_html, category, tier)
                    
                time.sleep(20) 

        print("\n🎉 모든 카테고리 & 등급별 지능형 자동 발행이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
