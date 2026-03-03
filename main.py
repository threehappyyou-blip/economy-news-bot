import os
import smtplib
import feedparser
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# ==========================================
# [클라우드(GitHub) 전용 봇 세팅]
# GitHub Secrets에서 안전하게 비밀번호를 가져옵니다.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# 본인의 발송용 이메일 주소
SENDER_EMAIL = "threehappyyou@gmail.com" 

# 🚨 [새로운 기능: 구독자 명부 및 등급 시스템]
# 여기에 구독자들의 이메일과 등급을 적어두면 봇이 알아서 맞춤형 리포트를 보냅니다.
# 테스트를 위해 아래 3곳에 모두 자네의 이메일을 넣어보게! (각기 다른 3통의 메일이 갈 걸세)
SUBSCRIBERS = {
    "test_email_1@gmail.com": "Basic",
    "test_email_2@gmail.com": "Premium",
    "test_email_3@gmail.com": "Royal Premium"
}
# ==========================================

client = genai.Client(api_key=GEMINI_API_KEY)

def get_financial_news():
    print("[시스템] 글로벌 주요 경제 매체의 최신 뉴스를 수집합니다...")
    
    # CNBC, WSJ, 야후 파이낸스, 마켓워치 등의 실시간 RSS 주소
    urls_text = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664,https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml,https://finance.yahoo.com/news/rssindex,http://feeds.marketwatch.com/marketwatch/topstories/"
    rss_urls = urls_text.split(",")
    
    news_items = set() # 중복 방지 바구니
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:7]: # 각 매체별 최신 7개 추출
                news_items.add(entry.title)
        except Exception:
            continue
            
    news_list = list(news_items)[:20]
    if not news_list:
        return None
        
    return "\n".join(["- " + news for news in news_list])

def generate_ai_report(news_text, tier):
    print(f"[시스템] AI 교수님들이 '{tier}' 등급 구독자를 위한 리포트를 토론 중입니다...")
    
    # 등급별 페르소나(패널 구성) 분기
    if tier == "Basic":
        panel_desc = """A panel of 7 top-tier Economics professors from elite US universities (e.g., Harvard, MIT, Chicago). 
        They hold diverse economic views (Classical, Keynesian, etc.)."""
    elif tier == "Premium":
        panel_desc = """A panel of 14 top-tier professors: 7 in Economics and 7 in Psychology (e.g., Stanford, Yale). 
        They combine macroeconomic theory with human psychology and cognitive biases (e.g., loss aversion)."""
    elif tier == "Royal Premium":
        panel_desc = """A panel of 21 top-tier professors: 7 in Economics, 7 in Psychology, and 7 in Humanities, Geography, and Philosophy. 
        They analyze news combining macroeconomics, behavioral psychology, geopolitical geography, and historical/philosophical context (e.g., Adam Smith, David Ricardo)."""
    else:
        panel_desc = "An expert financial analyst."

    prompt = f"""
    You are an AI simulating the following expert panel:
    {panel_desc}
    
    Rule 1: The professors are engaging in a respectful, fact-based debate. They may hold different perspectives based on their academic expertise, but they never insult each other or deceive the audience with false information.
    Rule 2: Based on the provided real-time financial news, analyze the geopolitical, political, and economic correlations.
    Rule 3: Write the final output as a cohesive, highly insightful newsletter for investors in English. Do not provide 1:1 personalized investment advice.
    Rule 4: Do not use markdown bolding (**) excessively. Write in a clean, highly readable text format.
    
    Structure of the Newsletter:
   
    - 3-bullet point TL;DR of the most critical news and market drivers.
    
   
    - Synthesize the discussion among the professors based on their specific academic fields. Highlight how their different viewpoints intersect to explain the current market.
    
   
    - Based on the debate, provide broad tactical asset allocation thoughts (e.g., Equities, Commodities, Future Tech).
    
    Disclaimer: "This report is for informational and educational purposes only. All investment responsibilities lie with the investor."

    Today's Real-Time News:
    {news_text}
    """
    
    # 가장 똑똑한 2.5 모델 호출
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    # 🚨 [가독성 업데이트] 마크다운 별표(**, *)를 완벽하게 제거하여 가독성을 높입니다.
    clean_report = response.text.replace("**", "").replace("*", "")
    return clean_report

def send_email(report_content, to_email, tier):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # 이메일 바구니 생성 (에러가 완벽히 수정된 add_header 방식)
    msg = MIMEMultipart()
    msg.add_header('From', SENDER_EMAIL)
    msg.add_header('To', to_email)
    msg.add_header('Subject', f'🌍 Your {tier} Level Insight')

    msg.attach(MIMEText(report_content, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"🎉 [성공] '{to_email}' 님에게 '{tier}' 등급 메일 발송 완료!")
    except Exception as e:
        print(f"❌ [실패] '{to_email}' 메일 발송 실패: {e}")

def job():
    news = get_financial_news()
    if not news:
        print("수집된 뉴스가 없습니다.")
        return
        
    # 🚨 [구독자 명부 순회] 등록된 모든 구독자에게 각자의 등급에 맞는 메일을 순서대로 발송합니다.
    print(f"\n총 {len(SUBSCRIBERS)}명의 구독자에게 맞춤형 뉴스레터 제작을 시작합니다...\n")
    
    for email, tier in SUBSCRIBERS.items():
        report = generate_ai_report(news, tier)
        send_email(report, email, tier)
        time.sleep(5) # 구글 AI 서버가 너무 빠르다고 놀라지 않도록 메일 1통마다 5초씩 휴식

if __name__ == "__main__":
    job()
