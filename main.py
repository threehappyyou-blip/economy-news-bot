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
SENDER_EMAIL = "threehappyyou@gmail.com" 

# 🚨 [시스템 버그 원천 차단!]
# 텍스트 시스템이 괄호를 지우는 것을 막기 위해, 순수 문자열과 list(), dict() 함수만 사용했습니다.
raw_subs = "threehappyyou@gmail.com/Basic,threehappyyou@gmail.com/Premium,threehappyyou@gmail.com/Royal Premium"
SUBSCRIBERS = list()
for sub_info in raw_subs.split(","):
    e_mail, e_tier = sub_info.split("/")
    SUBSCRIBERS.append(dict(email=e_mail, tier=e_tier))
# ==========================================

client = genai.Client(api_key=GEMINI_API_KEY)

def get_financial_news():
    print("[시스템] 글로벌 주요 경제 매체의 최신 뉴스를 수집합니다...")
    
    # 🚨 주소 부분도 괄호 버그를 피하기 위해 안전하게 변경했습니다.
    raw_urls = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664,https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml,https://finance.yahoo.com/news/rssindex,http://feeds.marketwatch.com/marketwatch/topstories/"
    rss_urls = raw_urls.split(",")
    
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
        
    return "\n".join(list("- " + news for news in news_list))

def generate_ai_report(news_text, tier):
    print("[시스템] AI 교수님들이 " + tier + " 등급 구독자를 위한 리포트를 토론 중입니다...")
    
    if tier == "Basic":
        panel_desc = "A panel of 7 top-tier Economics professors from elite US universities (e.g., Harvard, MIT, Chicago). They hold diverse economic views (Classical, Keynesian, etc.)."
    elif tier == "Premium":
        panel_desc = "A panel of 14 top-tier professors: 7 in Economics and 7 in Psychology (e.g., Stanford, Yale). They combine macroeconomic theory with human psychology and cognitive biases (e.g., loss aversion)."
    else:
        panel_desc = "A panel of 21 top-tier professors: 7 in Economics, 7 in Psychology, and 7 in Humanities, Geography, and Philosophy. They analyze news combining macroeconomics, behavioral psychology, geopolitical geography, and historical/philosophical context (e.g., Adam Smith, David Ricardo)."

    prompt = "You are an AI simulating the following expert panel:\n" + panel_desc + "\n\nRule 1: The professors are engaging in a respectful, fact-based debate. They may hold different perspectives based on their academic expertise, but they never insult each other or deceive the audience with false information.\nRule 2: Based on the provided real-time financial news, analyze the geopolitical, political, and economic correlations.\nRule 3: Write the final output as a cohesive, highly insightful newsletter for investors in English. Do not provide 1:1 personalized investment advice.\nRule 4: Do not use markdown bolding excessively. Write in a clean, highly readable text format.\n\nStructure of the Newsletter:\n[Part 1: Executive Economic Insights]\n- 3-bullet point TL;DR of the most critical news and market drivers.\n\n[Part 2: Market Analysis through Humanities & Psychology]\n- Synthesize the discussion among the professors based on their specific academic fields. Highlight how their different viewpoints intersect to explain the current market.\n\n[Part 3: Comprehensive Economic Analysis & Investment Precautions]\n- Based on the debate, provide broad tactical asset allocation thoughts (e.g., Equities, Commodities, Future Tech).\n\nDisclaimer: This report is for informational and educational purposes only. All investment responsibilities lie with the investor.\n\nToday's Real-Time News:\n" + news_text
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    clean_report = response.text.replace("**", "").replace("*", "")
    return clean_report

def send_email(report_content, to_email, tier):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg.add_header("From", SENDER_EMAIL)
    msg.add_header("To", to_email)
    msg.add_header("Subject", "Daily Global Economy Newsletter: " + tier + " Insight")

    msg.attach(MIMEText(report_content, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print("🎉 [성공] " + to_email + " 님에게 " + tier + " 등급 메일 발송 완료!")
    except Exception as e:
        print("❌ [실패] 메일 발송 실패: " + str(e))

def job():
    news = get_financial_news()
    if not news:
        print("수집된 뉴스가 없습니다.")
        return
        
    for sub in SUBSCRIBERS:
        email = sub.get("email")
        tier = sub.get("tier")
        
        report = generate_ai_report(news, tier)
        send_email(report, email, tier)
        time.sleep(5) 

if __name__ == "__main__":
    job()
