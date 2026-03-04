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

# 구독자 명단 5명 세팅 (테스트용)
raw_subs = "threehappyyou@gmail.com/Basic,threehappyyou@gmail.com/Basic,threehappyyou@gmail.com/Premium,threehappyyou@gmail.com/Premium,threehappyyou@gmail.com/Royal Premium"
SUBSCRIBERS = list()
for sub_info in raw_subs.split(","):
    e_mail, e_tier = sub_info.split("/")
    SUBSCRIBERS.append(dict(email=e_mail, tier=e_tier))
# ==========================================

client = genai.Client(api_key=GEMINI_API_KEY)

def get_financial_news():
    print("[시스템] 주요 매체의 최신 뉴스를 수집합니다...")
    raw_urls = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664,https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml,https://finance.yahoo.com/news/rssindex,http://feeds.marketwatch.com/marketwatch/topstories/"
    rss_urls = raw_urls.split(",")
    
    news_items = set() 
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]: 
                news_items.add(entry.title)
        except Exception:
            continue
            
    news_list = list(news_items)[:25]
    if not news_list:
        return None
        
    return "\n".join(list("- " + news for news in news_list))

def generate_ai_report(news_text, tier):
    print("[시스템] AI가 " + tier + " 등급 독자를 위한 영문 리포트를 작성 중입니다...")
    
    # 🚨 [핵심 업그레이드] 등급별 뉴스 개수 및 '참여 교수진의 수와 분야'를 명확히 분기!
    if tier == "Basic":
        news_count = "3"
        panel_desc = "a panel of 7 top-tier Economics professors from elite universities"
        depth_instruction = "Focus on the objective facts of the events."
    elif tier == "Premium":
        news_count = "5"
        panel_desc = "a panel of 14 top-tier professors (7 in Economics, 7 in Psychology)"
        depth_instruction = "Go beyond facts. Analyze the 'WHY' behind the events, combining economic principles with human psychological biases (e.g., loss aversion, herd behavior)."
    else: # Royal Premium
        news_count = "10"
        panel_desc = "a panel of 21 top-tier professors (7 in Economics, 7 in Psychology, 7 in Humanities, Geography, and Philosophy)"
        depth_instruction = "Provide the ultimate deep dive. Analyze the 'WHY' by intertwining macroeconomic theory, behavioral psychology, geopolitical geography, and historical/philosophical contexts."

    # AI 프롬프트 (최종 글로벌 영어 버전)
    prompt = "You are an advanced AI simulating an intense, fact-based debate among " + panel_desc + ".\n"
    prompt += "Your ultimate goal is to translate the profound insights from this academic debate into a warm, accessible newsletter to help ordinary people around the world achieve financial freedom and peace of mind.\n\n"
    
    prompt += "\n"
    prompt += "1. The final output MUST be written entirely in English.\n"
    prompt += "2. DO NOT use the words 'professor', 'economist', 'expert', or 'executive' in your response. Speak directly to the reader as a friendly, insightful financial guide.\n"
    prompt += "3. Select exactly " + news_count + " most important news items from the provided raw text. " + depth_instruction + "\n"
    prompt += "4. Explain all complex financial jargon in very simple terms so anyone can understand.\n"
    prompt += "5. Do not use markdown bolding (**) or asterisks. Write in a clean, highly readable plain text format.\n"
    prompt += "6. LEGAL GUARDRAILS - Act strictly as a one-way informational channel. Do NOT provide direct buy/sell recommendations for specific stocks.\n\n"
    
    prompt += "Structure of the Newsletter:\n"
    prompt += "\n"
    prompt += "- Summarize the core facts of the " + news_count + " selected news items clearly. What exactly happened?\n\n"
    
    prompt += "\n"
    prompt += "- Based on the panel's internal debate, analyze the news according to your tier's required depth.\n"
    prompt += "- Explain the 'WHY' behind the news.\n"
    prompt += "- If there are ongoing events (like geopolitical conflicts or strikes), analyze how the newly added information updates the previous situation and impacts daily life.\n\n"
    
    prompt += "[Part 3: Ideas for Financial Freedom]\n"
    prompt += "- Provide broad tactical asset allocation ideas (e.g., Defensive vs. Aggressive positioning, Hard Assets, Tech trends) to help everyday people manage risk comfortably.\n\n"
    
    prompt += "Disclaimer: This report is purely for informational and educational purposes. It does not constitute personalized financial advice. All investment decisions and legal responsibilities lie entirely with the individual investor.\n\n"
    
    prompt += "Today's Real-Time News:\n" + news_text
    
    # 구글 최신 2.5-flash 모델 호출
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
