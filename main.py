import os
import smtplib
import feedparser
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# ==========================================
# [클라우드(GitHub) 전용 봇 세팅]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# 봇이 편지를 보낼 때 쓸 '보내는 사람' 주소
SENDER_EMAIL = "threehappyyou@gmail.com" 

# 🚨 [구독자 명단 개선] 
# 동일한 이메일로 여러 등급의 테스트 메일을 받을 수 있도록 리스트(List) 구조로 변경했습니다!
SUBSCRIBERS =
# ==========================================

client = genai.Client(api_key=GEMINI_API_KEY)

def get_financial_news():
    print("[시스템] 글로벌 주요 경제 매체의 최신 뉴스를 수집합니다...")
    
    urls_text = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664,https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml,https://finance.yahoo.com/news/rssindex,http://feeds.marketwatch.com/marketwatch/topstories/"
    rss_urls = urls_text.split(",")
    
    news_items = set() 
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:7]: 
                news_items.add(entry.title)
        except Exception:
            continue
            
    news_list = list(news_items)[:20]
    if not news_list:
        return None
        
    return "\n".join(["- " + news for news in news_list])

def generate_ai_report(news_text, tier):
    print(f"[시스템] AI 교수님들이 '{tier}' 등급 구독자를 위한 리포트를 토론 중입니다...")
    
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
    [Part 1: Executive Economic Insights]
    - 3-bullet point TL;DR of the most critical news and market drivers.
    
   
    - Synthesize the discussion among the professors based on their specific academic fields. Highlight how their different viewpoints intersect to explain the current market.
    
   
    - Based on the debate, provide broad tactical asset allocation thoughts (e.g., Equities, Commodities, Future Tech).
    
    Disclaimer: "This report is for informational and educational purposes only. All investment responsibilities lie with the investor."

    Today's Real-Time News:
    {news_text}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    # 🚨 [가독성 유지] 
    clean_report = response.text.replace("**", "").replace("*", "")
    return clean_report

def send_email(report_content, to_email, tier):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

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
        
    print(f"\n총 {len(SUBSCRIBERS)}개의 맞춤형 뉴스레터 발송 작업을 시작합니다...\n")
    
    # 수정된 리스트 구조에 맞춰 반복문 변경
    for sub in SUBSCRIBERS:
        email = sub["email"]
        tier = sub["tier"]
        
        report = generate_ai_report(news, tier)
        send_email(report, email, tier)
        time.sleep(5) # 메일 발송 간 5초 휴식

if __name__ == "__main__":
    job()
