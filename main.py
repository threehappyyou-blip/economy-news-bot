import os
import sys
import traceback

# 1. 라이브러리 로드 방어 (여기서 에러가 나면 requirements.txt 문제임)
try:
    import feedparser
    import time
    import re
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import datetime, timedelta
    import pytz
    from google import genai
except ImportError as e:
    print(f"❌ [초기화 에러] 필수 라이브러리가 없습니다: {e}")
    print("GitHub의 requirements.txt 파일에 'google-genai', 'feedparser', 'pytz'가 정확히 있는지 확인하세요.")
    sys.exit(1)

# --- [설정 및 보안] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "자네의_API_키"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") or "자네의_앱_비밀번호"
SENDER_EMAIL = os.environ.get("MY_EMAIL") or "threehappyyou@gmail.com"

# 행복과 편안함을 전달할 테스트 수신자 5명 세팅
TEST_RECIPIENTS = [
    {"email": "threehappyyou@gmail.com", "level": "Basic"},
    {"email": "threehappyyou@gmail.com", "level": "Basic"},
    {"email": "threehappyyou@gmail.com", "level": "Premium"},
    {"email": "threehappyyou@gmail.com", "level": "Premium"},
    {"email": "threehappyyou@gmail.com", "level": "Royal"}
]

RSS_FEEDS = {
    "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=401&id=10000664",
    "Yahoo Finance": "https://finance.yahoo.com/rss/topstories",
    "WSJ": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "Forbes": "https://www.forbes.com/innovation/feed2/",
    "Financial Times": "https://www.ft.com/?format=rss"
}

# --- [기능 함수] ---
def clean_text(text):
    """특수기호를 제거하여 편안한 읽기 경험 제공"""
    if not text:
        return "Insight generation paused."
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'-{2,}', '', text)
    return text.strip()

def get_latest_news(count=15):
    """뉴스 수집"""
    news_list = []
    seen_titles = set()
    et_tz = pytz.timezone('US/Eastern')
    now = datetime.now(et_tz)
    
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.title in seen_titles: continue
                news_list.append(f"[{source}] {entry.title}")
                seen_titles.add(entry.title)
                if len(news_list) >= 30: break
        except Exception:
            continue
    return news_list[:count]

def analyze_with_gemini(news_items, level):
    """AI 분석 (에러 완벽 방어)"""
    try:
        # API 키가 없으면 여기서 즉시 에러가 발생하여 아래 except로 빠짐
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        news_count = 3 if level == "Basic" else (5 if level == "Premium" else 10)
        selected_news = news_items[:news_count]
        
        prompt = f"""
        [Goal] Write a warm, encouraging economic newsletter in English to help regular people find financial peace and happiness.
        [Tone] Friendly, empathetic, and extremely simple. Treat the reader like a dear friend. Absolutely NO academic jargon.
        [Subscription Level] {level}
        
        [Instructions based on Level]
        - If Basic: Summarize {news_count} news stories very simply. Add a short "Easy Economic Term of the Day".
        - If Premium: Summarize {news_count} news stories. Add a "Why It Matters" section that gently explains human psychology behind events.
        - If Royal: Summarize {news_count} news stories. Add a "Big Picture" section explaining the long-term historical context as an easy story.

        [Mandatory Rules]
        1. Plain text ONLY. No markdown symbols (**, ##).
        2. Always include at the bottom: "Disclaimer: This email is for informational purposes only. All investment decisions are your own."

        [News]
        {chr(10).join(selected_news)}
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return clean_text(response.text)
        
    except Exception as e:
        print(f"⚠️ [AI 생성 에러] {level} 레벨 생성 실패: {e}")
        return f"Hello! We are currently upgrading our system to bring you better insights. Here are today's headlines:\n\n{chr(10).join(selected_news)}\n\nDisclaimer: This email is for informational purposes only."

def send_email(receiver_email, subject, content):
    """이메일 발송"""
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
        print(f"❌ [메일 발송 에러] {receiver_email}로 전송 실패: {e}")
        return False

# --- [메인 실행부] ---
if __name__ == "__main__":
    try:
        print("1. Gathering global news...")
        all_news = get_latest_news(20)
        
        if not all_news:
            all_news = ["Global markets are quiet. Focus on long-term happiness."]

        print(f"2. Processing {len(TEST_RECIPIENTS)} emails...")
        
        for i, user in enumerate(TEST_RECIPIENTS):
            print(f"   [{i+1}/5] Generating {user['level']} report...")
            report = analyze_with_gemini(all_news, user['level'])
            
            subject = f"🌍 Your Path to Financial Freedom ({user['level']} Edition)"
            success = send_email(user['email'], subject, report)
            
            if success:
                print(f"   ✅ Sent successfully to {user['email']}")
                
            # 과부하 방지를 위한 10초 대기
            time.sleep(10)

        print("\n🎉 All processes finished safely!")
        
    except Exception as e:
        print(f"\n❌ [치명적 시스템 에러 발생]")
        traceback.print_exc() # 에러의 상세 원인을 액션 로그에 출력
        sys.exit(1)
