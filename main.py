import os
import smtplib
import feedparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# ==========================================
# 🚨 [가장 중요한 보안 업데이트]
# 코드를 인터넷(GitHub)에 올릴 것이므로, 비밀번호를 직접 적지 않고 '환경 변수(비밀 금고)'에서 불러옵니다!
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

SENDER_EMAIL = "threehappyyou@gmail.com"
RECEIVER_EMAIL = "threehappyyou@gmail.com"
# ==========================================

client = genai.Client(api_key=GEMINI_API_KEY)

def get_financial_news():
    print("[시스템] 최신 글로벌 경제 뉴스를 수집합니다...")
    rss_urls =
    
    news_items = set()
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                news_items.add(entry.title)
        except Exception:
            continue
            
    news_list = list(news_items)[:20]
    return "\n".join([f"- {news}" for news in news_list])
    
def generate_ai_report(news_text):
    print("[시스템] AI 교수님이 리포트를 작성 중입니다...")
    prompt = f"""
    You are an economics professor with 30 years of experience, a psychology expert, and a visionary macro-thinker. 
    Based on the following real-time financial news, write a highly insightful economic report for beginner investors in English.
    Do not provide 1:1 personalized investment advice. 

    [Part 1: Executive Economic Insights]:
    - Core Elements: Bullet points of the 3 most critical macroeconomic drivers today.
    - Condensed Summary: A 2-3 sentence TL;DR explaining what the current market situation means for everyday people.

    [Part 2: Market Analysis through Humanities & Psychology]
    - Analyze the news using the "AI Anxiety and Human Frustration" worldview. 
    - Apply behavioral economics to prevent readers from panic buying/selling.

    [Part 3: Comprehensive Economic Analysis & Investment Precautions]
    - Provide broad, strategic advice on how to allocate capital across:
      1) Individual Stocks & ETFs
      2) Hard Assets & Commodities
      3) Future Energy & Infrastructure
      4) Alternative Assets
    - Explain *why* these specific assets are defensive or aggressive in today's context.

    Disclaimer: This report is for informational and educational purposes only. All investment responsibilities lie with the investor.

    Today's Real-Time News:
    {news_text}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def send_email(report_content):
    print("[시스템] 이메일 포맷을 정리하고 발송을 준비합니다...")
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg = RECEIVER_EMAIL
    msg = "🌍 Daily Global Economy & Multi-Asset Strategy Newsletter"

    clean_report_content = report_content.replace("**", "").replace("*", "")
    msg.attach(MIMEText(clean_report_content, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("🎉 [성공] 이메일 발송 완료!")
    except Exception as e:
        print(f"❌ [실패] 이메일 발송 실패: {e}")

def job():
    news = get_financial_news()
    if news:
        report = generate_ai_report(news)
        send_email(report)

if __name__ == "__main__":
    # 클라우드 컴퓨터가 켜지면 무한 반복 없이 딱 1번만 실행하고 깔끔하게 퇴근하도록 변경함!
    job()