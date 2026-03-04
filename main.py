import os
import smtplib
import feedparser
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai 

# ==========================================
# [자네의 마법 열쇠 세팅]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# 보내는 사람 이메일
SENDER_EMAIL = "threehappyyou@gmail.com" 

# 🚨 [구독자 명단 5명 세팅 완료!]
# 자네의 이메일 하나로 베이직 2명, 프리미엄 2명, 로얄프리미엄 1명 분량의 테스트를 진행합니다.
raw_subs = "threehappyyou@gmail.com/Basic,threehappyyou@gmail.com/Basic,threehappyyou@gmail.com/Premium,threehappyyou@gmail.com/Premium,threehappyyou@gmail.com/Royal Premium"
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
            # 로얄프리미엄의 10개 뉴스를 위해 넉넉하게 추출
            for entry in feed.entries[:10]: 
                news_items.add(entry.title)
        except Exception:
            continue
            
    news_list = list(news_items)[:25]
    if not news_list:
        return None
        
    return "\n".join(list("- " + news for news in news_list))

def generate_ai_report(news_text, tier):
    print("[시스템] AI가 " + tier + " 등급 독자의 '행안(행복하고 편안한)' 투자를 위한 리포트를 작성 중입니다...")
    
    # 등급별 맞춤형 프롬프트 세팅 (뉴스 개수 및 Why 심층 분석 차별화)
    if tier == "Basic":
        news_count = "3"
        depth_instruction = "Focus on the FACTS (What happened). Select the top 3 most important news items."
    elif tier == "Premium":
        news_count = "5"
        depth_instruction = "Go beyond the facts. Focus deeply on the 'WHY' (Why did this happen? What is the psychological and economic cause and effect?). Select the top 5 most important news items."
    else: # Royal Premium
        news_count = "10"
        depth_instruction = "Provide the ultimate deep dive. Analyze the 'What' and 'Why' by heavily integrating geopolitical, historical, and philosophical perspectives. Connect the dots across different domains for the top 10 most important news items."

    prompt = "You are an advanced AI financial analyst whose ultimate goal is to help people feel comfortable, happy, and confident about their financial future.\n\n"
    prompt += "Strict Rule 1: DO NOT use the words 'professor', 'economist', or 'expert' in your response. Frame the text as a warm, highly insightful, and objective newsletter.\n"
    prompt += "Strict Rule 2: Based on the provided raw news, carefully select and analyze exactly " + news_count + " news items. " + depth_instruction + "\n"
    prompt += "Strict Rule 3: Explain all complex financial jargon in very simple, easy-to-understand terms so that beginners can read it comfortably without stress.\n"
    prompt += "Strict Rule 4: Do not use markdown bolding or asterisks. Write in a clean, highly readable plain text format.\n"
    prompt += "Strict Rule 5: LEGAL GUARDRAILS - You must act strictly as a one-way informational channel. Do NOT provide direct buy/sell recommendations for specific stocks. Frame your insights as 'broad tactical considerations' based on data.\n\n"
    
    prompt += "Structure of the Newsletter:\n"
    prompt += "[Part 1: Executive Economic Insights]\n"
    prompt += "- Summarize the core facts of the " + news_count + " selected news items clearly.\n\n"
    
    prompt += "[Part 2: Multidisciplinary Market Analysis]\n"
    prompt += "- Analyze the news based on the depth required for the " + tier + " level.\n"
    prompt += "- If there are ongoing events (like geopolitical conflicts), analyze how the new information updates the previous situation.\n\n"
    
    prompt += "\n"
    prompt += "- Provide strategic ideas on asset allocation (e.g., Defensive vs. Aggressive positioning, Hard Assets, Tech) to help readers manage risk comfortably.\n\n"
    
    prompt += "Disclaimer: This report is purely for informational and educational purposes. It does not constitute personalized financial advice. All investment decisions and legal responsibilities lie entirely with the individual investor.\n\n"
    prompt += "Today's Real-Time News:\n" + news_text
    
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
        
    print("\n총 " + str(len(SUBSCRIBERS)) + "개의 맞춤형 뉴스레터 발송 작업을 시작합니다...\n")
    
    for sub in SUBSCRIBERS:
        email = sub.get("email")
        tier = sub.get("tier")
        
        report = generate_ai_report(news, tier)
        send_email(report, email, tier)
        
        # 구글 서버에 무리가 가지 않도록 메일 1통을 보낼 때마다 5초씩 대기합니다.
        time.sleep(5) 

if __name__ == "__main__":
    job()
