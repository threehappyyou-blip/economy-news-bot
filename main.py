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

# [구독자 명단 및 등급]
# 차후 웹사이트 DB(회원가입 정보)와 연결될 핵심 부분입니다.
raw_subs = "threehappyyou@gmail.com/Basic,threehappyyou@gmail.com/Premium,threehappyyou@gmail.com/Royal Premium"
SUBSCRIBERS = list()
for sub_info in raw_subs.split(","):
    e_mail, e_tier = sub_info.split("/")
    SUBSCRIBERS.append(dict(email=e_mail, tier=e_tier))
# ==========================================

client = genai.Client(api_key=GEMINI_API_KEY)

def get_financial_news():
    print("[시스템] 주요 매체(CNBC, WSJ, Yahoo, MarketWatch)의 최신 뉴스를 수집합니다...")
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
    print(f"[시스템] AI가 '{tier}' 등급에 맞춘 다각도 분석 리포트를 생성 중입니다...")
    
    # 🚨 [핵심 업그레이드] 교수/학자 단어를 배제하고, 분석 관점(Perspective)들의 토론으로 설정
    if tier == "Basic":
        panel_desc = "Top-tier macroeconomic and fundamental market analysis perspectives."
    elif tier == "Premium":
        panel_desc = "A combination of top-tier macroeconomic analysis AND behavioral psychology perspectives (analyzing market sentiment, loss aversion, herd behavior)."
    else: # Royal Premium
        panel_desc = "A comprehensive synthesis of macroeconomic analysis, behavioral psychology, geopolitical geography, and humanities/philosophical perspectives."

    prompt = "You are an advanced AI simulating a panel discussion among " + panel_desc + "\n\n"
    prompt += "Strict Rule 1: DO NOT use the words 'professor', 'economist', or 'expert' in your response. Frame the text as a deep analytical report.\n"
    prompt += "Strict Rule 2: Deliver the hard FACTS from the news first, before diving into any analysis or theories.\n"
    prompt += "Strict Rule 3: Simulate a respectful, multi-angled debate based on different analytical models. If a topic is an ongoing event (e.g., geopolitical conflicts), highlight what new information has emerged and how it updates previous assumptions.\n"
    prompt += "Strict Rule 4: Do not use markdown bolding (**) or asterisks. Write in a clean, professional, and highly readable plain text format.\n\n"
    
    prompt += "Structure of the Newsletter:\n"
    prompt += "\n"
    prompt += "- Summarize the core facts of today's news clearly and objectively. What exactly happened?\n\n"
    
    prompt += "[Part 2: Multidisciplinary Market Analysis]\n"
    prompt += "- Analyze the facts based on the tier's designated perspectives (" + tier + " level).\n"
    prompt += "- Explore how macroeconomic principles, human psychology, and geopolitical/philosophical contexts intertwine to shape potential market movements.\n\n"
    
    prompt += "\n"
    prompt += "- Based on the preceding analysis, provide strategic ideas on asset allocation (Stocks, Hard Assets, Future Tech, etc.). Explain the 'why' behind defensive or aggressive positioning.\n\n"
    
    prompt += "Disclaimer: This report is for informational and educational purposes only. All investment responsibilities lie with the investor.\n\n"
    prompt += "Today's Real-Time News:\n" + news_text
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    # 별표 및 마크다운 완벽 제거
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
        time.sleep(5) # 구글 API 과부하 방지

if __name__ == "__main__":
    job()
