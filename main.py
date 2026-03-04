import os
import feedparser
import time
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz

# Google GenAI SDK (최신 버전)
from google import genai

# --- [설정 및 보안] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "자네의_API_키"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") or "자네의_앱_비밀번호"
SENDER_EMAIL = os.environ.get("MY_EMAIL") or "threehappyyou@gmail.com"

# 5통의 테스트 메일 (모두 자네의 메일로 전송)
TEST_RECIPIENTS = [
    {"email": "threehappyyou@gmail.com", "level": "Basic"},
    {"email": "threehappyyou@gmail.com", "level": "Basic"},
    {"email": "threehappyyou@gmail.com", "level": "Premium"},
    {"email": "threehappyyou@gmail.com", "level": "Premium"},
    {"email": "threehappyyou@gmail.com", "level": "Royal"}
]

# 9대 글로벌 뉴스 매체
RSS_FEEDS = {
    "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=401&id=10000664",
    "Yahoo Finance": "https://finance.yahoo.com/rss/topstories",
    "MarketWatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "WSJ": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "Forbes": "https://www.forbes.com/innovation/feed2/",
    "Business Insider": "https://feeds.businessinsider.com/custom/all",
    "Financial Times": "https://www.ft.com/?format=rss"
}

# --- [기능 함수] ---

def clean_text(text):
    """지저분한 특수기호 제거 및 가독성 개선 (Plain Text)"""
    if not text:
        return "No content generated."
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'-{2,}', '', text)
    return text.strip()

def get_latest_news(count=15):
    """최신 뉴스 수집 (중복 제거)"""
    news_list = []
    seen_titles = set()
    et_tz = pytz.timezone('US/Eastern')
    now = datetime.now(et_tz)
    
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.title in seen_titles: continue
                news_list.append(f"[{source}] {entry.title}: {entry.summary if 'summary' in entry else ''}")
                seen_titles.add(entry.title)
                if len(news_list) >= 40: break
        except Exception as e:
            continue
            
    return news_list[:count]

def analyze_with_gemini(news_items, level):
    """등급별로 편안하고 쉬운 영어 뉴스레터 생성 (에러 방어 포함)"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    news_count = 3 if level == "Basic" else (5 if level == "Premium" else 10)
    selected_news = news_items[:news_count]
    
    prompt = f"""
    [Goal] Write a warm, encouraging, and highly accessible economic newsletter in English. The ultimate goal is to help regular people find financial peace of mind and happiness.
    [Tone] Friendly, empathetic, and extremely simple. Treat the reader like a dear friend. Absolutely NO "executive", "expert", "professor", or academic jargon. 
    [Subscription Level] {level}
    
    [Instructions based on Level]
    - If Basic: Summarize the {news_count} news stories very simply. Add a short "Easy Economic Term of the Day" section to help beginners understand a related concept.
    - If Premium: Summarize the {news_count} news stories. Add a "Why It Matters" section that gently explains the human psychology and market reasons behind these events without sounding academic.
    - If Royal: Summarize the {news_count} news stories. Add a "Big Picture" section that explains the long-term global or historical context in a very easy, story-like manner. Help the reader feel safe and informed.

    [Mandatory Formatting & Rules]
    1. Output MUST be plain text. Do NOT use markdown symbols like **, ##, or --.
    2. Write beautifully structured paragraphs.
    3. Include this exact legal disclaimer at the bottom: 
       "Disclaimer: This email is for informational purposes only to help guide you toward financial happiness. All investment decisions and responsibilities are entirely your own."

    [News to Share]
    {chr(10).join(selected_news)}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        # AI가 응답을 생성했지만 안전 필터에 걸린 경우를 방어
        if response.text:
            return clean_text(response.text)
        else:
            return "This content required deeper analysis, but we paused it to ensure it remains a helpful and positive read for you. We will bring you more insights tomorrow!\n\nDisclaimer: This email is for informational purposes only. All investment decisions are your own."
    except Exception as e:
        # 완전한 에러가 난 경우 죽지 않고 안내 문구 반환
        return f"Hello! We are currently upgrading our insight engine to bring you better analysis. Here are the raw headlines for today:\n\n{chr(10).join(selected_news)}\n\nDisclaimer: This email is for informational purposes only. All investment decisions are your own."

def send_email(receiver_email, subject, content):
    """안전한 이메일 전송"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Mail Error for {receiver_email}: {e}")
        return False

# --- [메인 실행부] ---
if __name__ == "__main__":
    print("1. Gathering global news...")
    all_news = get_latest_news(20)
    
    if not all_news:
        all_news = ["Global markets are quiet today. Focus on long-term happiness."]

    print(f"2. Processing {len(TEST_RECIPIENTS)} emails (with safety delays)...")
    
    for i, user in enumerate(TEST_RECIPIENTS):
        print(f"   [{i+1}/5] Generating {user['level']} report...")
        report = analyze_with_gemini(all_news, user['level'])
        
        subject = f"🌍 Your Path to Financial Freedom ({user['level']} Edition)"
        success = send_email(user['email'], subject, report)
        
        if success:
            print(f"   ✅ Sent successfully to {user['email']}")
            
        # [핵심] API 과부하 및 에러 방지를 위해 10초 대기 (무료 티어 보호)
        time.sleep(10)

    print("\n🎉 All processes finished safely!")
