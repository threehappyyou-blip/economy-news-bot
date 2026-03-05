import os
import sys
import traceback

print("=======================================")
print(" 🚀 경제 뉴스 봇 시스템 가동 시작 🚀")
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
    print("✅ 필수 라이브러리 로드 완료")
except ImportError as e:
    print(f"❌ [치명적 에러] 도구를 찾을 수 없습니다: {e}")
    sys.exit(1)

# --- [보안 키 및 이메일 설정] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# 👉 보내는 사람: 앱 비밀번호를 발급받은 제미나이 프로 계정
SENDER_EMAIL = "zubikcape@gmail.com"

if not GEMINI_API_KEY or not GMAIL_APP_PASSWORD:
    print("\n⛔ [시스템 중단] 보안 키가 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

# 👉 받는 사람: 제자님의 원래 메일함 (5통 모두 이곳으로 전송되게 세팅 완료)
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
    if not text: return "Content generation failed."
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'-{2,}', '', text)
    return text.strip()

def get_latest_news(count=15):
    news_list = []
    seen_titles = set()
    print("📡 뉴스 데이터 수집 중...")
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
    print(f"✅ 총 {len(news_list)}개의 최신 뉴스 확보")
    return news_list[:count]

def analyze_with_gemini(news_items, level):
    news_count = 3 if level == "Basic" else (5 if level == "Premium" else 10)
    selected_news = news_items[:news_count]
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        [Goal] Write a warm, encouraging economic newsletter in English.
        [Tone] Friendly, empathetic, and simple. No jargon.
        [Level] {level}
        [News] {chr(10).join(selected_news)}
        
        Instructions:
        - Basic: Summarize {news_count} news simply + Easy Term of Day.
        - Premium: Summarize + Why It Matters (Psychology).
        - Royal: Summarize + Big Picture (History/Future).
        
        * Plain text only. No markdown.
        * Disclaimer: Information only. Investment decisions are your own.
        """
        
        # 👉 [핵심 해결책] 404 에러와 429 에러를 모두 돌파하는 구글 최신 '2.5-flash' 모델!
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    
    except Exception as e:
        print(f"⚠️ [AI 생성 오류 발생] {e}")
        error_report = f"⚠️ AI Analysis Failed due to the following error:\n\n[ERROR DETAILS]:\n{str(e)}\n\n"
        error_report += f"Here are the raw headlines for now:\n{chr(10).join(selected_news)}"
        return error_report

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
        print(f"❌ [이메일 전송 실패] {e}")
        return False

if __name__ == "__main__":
    try:
        all_news = get_latest_news(20)
        if not all_news: all_news = ["Global markets quiet today."]

        print(f"\n📨 총 {len(TEST_RECIPIENTS)}통의 이메일 발송을 시작합니다...")
        
        for i, user in enumerate(TEST_RECIPIENTS):
            print(f"  [{i+1}/5] {user['level']} 레벨 생성 중...", end=" ")
            report = analyze_with_gemini(all_news, user['level'])
            
            subject = f"🌍 Your Path to Financial Freedom ({user['level']} Edition)"
            if send_email(user['email'], subject, report):
                print("✅ 전송 완료")
            else:
                print("❌ 전송 실패")
            
            # 서버 과부하를 막기 위해 20초 대기 (매우 중요)
            time.sleep(20) 

        print("\n🎉 모든 작업이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 알 수 없는 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
