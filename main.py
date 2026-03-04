import os
import feedparser
import yfinance as yf
from google import genai
from google.genai import types
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz
import re
import time

# --- [설정 및 보안] ---
# GitHub Secrets에서 가져오거나 직접 입력 (로컬 테스트용)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "자네의_API_키"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") or "자네의_앱_비밀번호"
SENDER_EMAIL = os.environ.get("MY_EMAIL") or "threehappyyou@gmail.com"

# 테스트용 수신자 설정 (모두 자네의 실제 메일로 고정하여 에러 방지)
TEST_RECIPIENTS = [
    {"email": "threehappyyou@gmail.com", "level": "Basic"},
    {"email": "threehappyyou@gmail.com", "level": "Basic"},
    {"email": "threehappyyou@gmail.com", "level": "Premium"},
    {"email": "threehappyyou@gmail.com", "level": "Premium"},
    {"email": "threehappyyou@gmail.com", "level": "Royal"}
]

# 뉴스 소스 (9대 글로벌 매체)
RSS_FEEDS = {
    "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=401&id=10000664",
    "Yahoo Finance": "https://finance.yahoo.com/rss/topstories",
    "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "WSJ": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "Fortune": "https://fortune.com/feed",
    "Forbes": "https://www.forbes.com/innovation/feed2/",
    "Business Insider": "https://feeds.businessinsider.com/custom/all",
    "Investors Daily": "https://www.investors.com/feed",
    "Financial Times": "https://www.ft.com/?format=rss"
}

# --- [기능 함수] ---

def clean_text(text):
    """지저분한 특수기호 제거 및 가독성 개선"""
    text = re.sub(r'\*+', '', text)  # ** 제거
    text = re.sub(r'#+', '', text)   # ## 제거
    text = re.sub(r'-{2,}', '', text) # --- 제거
    return text.strip()

def get_latest_news(count=10):
    """RSS 피드에서 최신 뉴스 수집 (중복 및 시간 필터링)"""
    news_list = []
    seen_titles = set()
    et_tz = pytz.timezone('US/Eastern')
    now = datetime.now(et_tz)
    
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.title in seen_titles: continue
            
            # 최근 12시간 이내 뉴스만
            published = getattr(entry, 'published_parsed', None)
            if published:
                pub_dt = datetime.fromtimestamp(time.mktime(published), pytz.UTC).astimezone(et_tz)
                if now - pub_dt > timedelta(hours=12): continue
            
            news_list.append(f"[{source}] {entry.title}: {entry.summary if 'summary' in entry else entry.link}")
            seen_titles.add(entry.title)
            if len(news_list) >= 30: break # 최대 30개 수집 후 선택
            
    return news_list[:count]

def analyze_with_gemini(news_items, level):
    """구독 등급별 페르소나 토론 및 리포트 생성"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 등급별 설정
    news_count = 3 if level == "Basic" else (5 if level == "Premium" else 10)
    selected_news = news_items[:news_count]
    
    prompt = f"""
    [Goal] Create a warm, inspiring, and easy-to-understand economic newsletter in English for everyday people seeking financial freedom.
    [Tone] Friendly, encouraging, and clear. Avoid complex jargon or 'executive' language.
    [Subscription Level] {level}
    
    [Instructions]
    1. Introduction: Start with a warm greeting and a message of hope.
    2. Fact Delivery: Present the top {news_count} essential global news stories clearly.
    3. The 'WHY' Analysis:
       - If Basic: Focus on very simple explanations of economic terms used in the news.
       - If Premium: Analyze the 'Why' using economic and psychological insights (7 experts perspective). Explain human emotions behind the market.
       - If Royal: Deep dive using 21 experts' perspectives (Economics, Psychology, Humanities, Geography, Philosophy). Explain global power shifts and long-term history.
    4. Conclusion: A supportive closing message.
    5. LEGAL DISCLAIMER: You MUST include this exactly: "Disclaimer: This report is for informational purposes only. All financial decisions and responsibilities belong to the individual. Please consult a professional for specific advice."

    [News Items to Analyze]
    {chr(10).join(selected_news)}

    Write strictly in English. Do NOT use any symbols like **, ##, or --. Make it look like a clean, professional letter.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(system_instruction="You are a kind mentor helping people reach financial freedom through easy insights."),
        contents=prompt
    )
    
    return clean_text(response.text)

def send_email(receiver_email, subject, content):
    """이메일 전송 (예외 처리 강화)"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Success: Email sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Failed: Could not send email to {receiver_email}. Error: {e}")

# --- [메인 실행부] ---

if __name__ == "__main__":
    print("1. Harvesting global news...")
    all_news = get_latest_news(30)
    
    if not all_news:
        print("⚠️ No fresh news found. Check RSS feeds.")
        all_news = ["Global markets are currently stabilizing with focus on upcoming inflation data."]

    print(f"2. Generating and sending {len(TEST_RECIPIENTS)} test reports...")
    
    for i, user in enumerate(TEST_RECIPIENTS):
        print(f"   [{i+1}/5] Processing {user['level']} level for {user['email']}...")
        try:
            report = analyze_with_gemini(all_news, user['level'])
            subject = f"🌍 Your Daily {user['level']} Insight for Financial Freedom"
            send_email(user['email'], subject, report)
            # 서버 과부하 방지 및 안정성을 위해 3초 대기
            time.sleep(3)
        except Exception as e:
            print(f"   ⚠️ Error processing user {i+1}: {e}")
            continue

    print("\n🎉 All tasks completed!")
