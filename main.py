import os
import sys
import traceback

print("=======================================")
print(" 🚀 경제 뉴스 봇 시스템 점검을 시작합니다 🚀")
print("=======================================")

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
    print("✅ 라이브러리 로드: 성공 (requirements.txt 정상)")
except ImportError as e:
    print(f"❌ 라이브러리 로드: 실패 ({e})")
    sys.exit(1)

# --- [보안 키 점검 (가장 중요!)] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
SENDER_EMAIL = os.environ.get("MY_EMAIL") or "threehappyyou@gmail.com"

print(f"🔑 API KEY 연결 상태: {'✅ 정상' if GEMINI_API_KEY else '❌ 실패 (yml 파일 env 설정 또는 Secrets 확인)'}")
print(f"📧 지메일 비밀번호 연결 상태: {'✅ 정상' if GMAIL_APP_PASSWORD else '❌ 실패 (yml 파일 env 설정 또는 Secrets 확인)'}")

if not GEMINI_API_KEY or not GMAIL_APP_PASSWORD:
    print("\n⚠️ [시스템 강제 종료] 키 값이 없어서 더 이상 진행할 수 없습니다.")
    sys.exit(1)

# ---------------------------------------------

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
    "Forbes": "https://www.forbes.com/innovation/feed2/"
}

def clean_text(text):
    if not text:
        return "Insight generation paused."
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'-{2,}', '', text)
    return text.strip()

def get_latest_news(count=15):
    news_list = []
    seen_titles = set()
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
    try:
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
        2. Always include at the bottom: "Disclaimer: This email is for informational purposes only. All investment decisions and responsibilities are your own."

        [News]
        {chr(10).join(selected_news)}
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return clean_text(response.text)
        
    except Exception as e:
        print(f"⚠️ [AI 에러] {level} 레벨 생성 실패: {e}")
        return f"Hello! We are currently upgrading our system. Here are today's headlines:\n\n{chr(10).join(selected_news)}\n\nDisclaimer: This email is for informational purposes only. All investment decisions are your own."

def send_email(receiver_email, subject, content):
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
        print(f"❌ [메일 발송 에러] 전송 실패: {e}")
        return False

if __name__ == "__main__":
    try:
        print("\n[작업 1] 뉴스 수집 중...")
        all_news = get_latest_news(20)
        
        if not all_news:
            all_news = ["Global markets are quiet. Focus on long-term happiness."]

        print(f"\n[작업 2] {len(TEST_RECIPIENTS)}명에게 메일 발송 시작...")
        
        for i, user in enumerate(TEST_RECIPIENTS):
            print(f"  -> [{i+1}/5] {user['level']} 레벨 리포트 작성 중...")
            report = analyze_with_gemini(all_news, user['level'])
            
            subject = f"🌍 Your Path to Financial Freedom ({user['level']} Edition)"
            success = send_email(user['email'], subject, report)
            
            if success:
                print(f"     ✅ 전송 성공: {user['email']}")
                
            time.sleep(10) # API 휴식

        print("\n🎉 모든 작업이 안전하게 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ [치명적 시스템 에러 발생]")
        traceback.print_exc()
        sys.exit(1)
