import os
import sys
import traceback
import time
import requests
import jwt
import base64
import urllib.parse
import random
from datetime import datetime
import feedparser
from google import genai
from google.genai import types

print("=======================================")
print(" 🚀 40년 멘토 + VIP 타이탄 매뉴얼 심층 강화 + 무적 썸네일 봇 🚀")
print("=======================================")

# --- [보안 키 점검] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")

if not GEMINI_API_KEY or not GHOST_API_URL or not GHOST_ADMIN_API_KEY:
    print("\n⛔ [시스템 중단] API 키 또는 Ghost 출입증이 없습니다. GitHub Secrets를 확인하세요.")
    sys.exit(1)

GHOST_API_URL = str(GHOST_API_URL).rstrip('/')

# 🚨 [카테고리 세팅]
CATEGORIES = dict()

cat_eco = list()
cat_eco.append("https://" + "search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664")
cat_eco.append("https://" + "finance.yahoo.com/news/rssindex")
CATEGORIES.update({"Economy": cat_eco})

cat_pol = list()
cat_pol.append("https://" + "search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113")
CATEGORIES.update({"Politics": cat_pol})

cat_tech = list()
cat_tech.append("https://" + "search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910")
CATEGORIES.update({"Tech": cat_tech})

cat_health = list()
cat_health.append("https://" + "search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108")
CATEGORIES.update({"Health": cat_health})

cat_energy = list()
cat_energy.append("https://" + "search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810")
CATEGORIES.update({"Energy": cat_energy})

# 🚨 [TikTok 바이럴 링크 세팅]
TIKTOK_LINKS = [
    "https://lite.tiktok.com/t/ZSuGXKdsU/",
    "https://lite.tiktok.com/t/ZSu9GYwy5/",
    "https://lite.tiktok.com/t/ZSuxhPSBR/",
    "https://lite.tiktok.com/t/ZSuXQwnvm/"
]

# 🚨 배포 설정
TASKS = list()
t1 = dict(); t1.update({"tier": "Basic", "count": 2}); TASKS.append(t1)
t2 = dict(); t2.update({"tier": "Premium", "count": 2}); TASKS.append(t2)
t3 = dict(); t3.update({"tier": "Royal Premium", "count": 3}); TASKS.append(t3)

TIER_LABELS = dict()
TIER_LABELS.update({"Basic": "🌱 Free"})
TIER_LABELS.update({"Premium": "💎 Pro"})
TIER_LABELS.update({"Royal Premium": "👑 VIP"})

def get_category_news(urls, count=20):
    news_list = list()
    seen_titles = set()
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title_text = getattr(entry, 'title', '')
                if title_text in seen_titles: continue
                summary_text = getattr(entry, 'summary', '')
                news_list.append("- " + str(title_text) + ": " + str(summary_text))
                seen_titles.add(title_text)
                if len(news_list) >= count: break
        except Exception:
            continue
            
    final_news = list()
    for _ in range(count):
        if len(news_list) > 0:
            final_news.append(news_list.pop(0))
    return final_news

def analyze_with_gemini(news_items, category, tier):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        selected_news = "\n".join(news_items)
        tiktok_urls_str = "\n".join(TIKTOK_LINKS)
        
        model_name = "gemini-2.5-flash"  
        
        # 🚨 [VIP 전용 프롬프트 완벽 업그레이드] AI가 대충 쓰지 못하도록 템플릿과 분량을 강제합니다.
        vip_extra_rules = ""
        vip_extra_sections = ""
        
        if tier == "Basic":
            depth_instruction = "<strong>🔑 The Core Fact:</strong> Explain what happened simply using ELI5 (Explain Like I'm 5)."
        elif tier == "Premium":
            depth_instruction = "<strong>🧐 WHY (The Hidden Reason):</strong> Explain using behavioral economics.<br><br><strong>🐑 THINK (What Masses Think):</strong> Explain the irrational market psychology."
        else: # Royal Premium (VIP)
            depth_instruction = "<strong>🧐 WHY (The Hidden Reason):</strong> Explain the true macroeconomic reason in deep detail.<br><br><strong>🐑 THINK (Herd Behavior):</strong> What the general public wrongly assumes.<br><br><strong>🦅 DIFFERENT THINK (Contrarian View):</strong> The hidden opportunity for true wealth."
            
            # 길이와 전문성을 폭발시키는 강력한 지시사항
            vip_extra_rules = """
        6. VIP EXCLUSIVE LENGTH & DEPTH: For the "VIP Exclusive" and "Titan's Playbook" sections, you MUST write VERY LONG, deeply analytical paragraphs. DO NOT summarize. Use professional terms like RSI, Moving Averages, Support/Resistance, and Macro Indicators.
        7. MANDATORY TITAN RULES: You must strictly follow the HTML template provided below to break down the 4 master rules (Generational Bargain, 60/30/10 Seesaw, Global Shield, Survival Tactics) individually.
            """
            
            # HTML 자체를 세련된 리포트 형식으로 고정하여 출력 퀄리티를 보장합니다.
            vip_extra_sections = """
        <hr style="border: 1px solid #e0e0e0; margin: 40px 0;">
        <h2 style="color: #2c3e50; font-size: 1.8em;">📈 VIP Exclusive: Deep-Dive Chart & Macro Analysis</h2>
        <p><strong>[Institutional Money Flow & Technical Outlook]</strong></p>
        <p>(WRITE 2 LONG, HIGHLY PROFESSIONAL PARAGRAPHS HERE. Act like a Wall Street Quant. Analyze specific indicators like RSI (Relative Strength Index), moving averages, yield curves, or volume trends related to this news. Explain what the 'smart money' is doing right now and where the hidden risks/rewards are in the charts. DO NOT write a short summary. Go deep into the data.)</p>

        <hr style="border: 1px solid #e0e0e0; margin: 40px 0;">
        <h2 style="color: #0056b3; font-size: 1.8em;">🛡️ The Titan's Playbook: Master Mindset & Strategy</h2>
        <p style="font-size: 1.1em; color: #555;"><em>How the top 1% navigate this specific market condition.</em></p>
        
        <ul style="list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 25px; background: #fafafa; padding: 15px; border-radius: 8px; border-left: 4px solid #f2a900;">
                <strong style="font-size: 1.2em;">1. The Generational Bargain (Fear vs. Greed)</strong><br>
                <span style="display: block; margin-top: 8px;">(WRITE A FULL PARAGRAPH applying this to today's news. Explain if the current market fear is a 'Generational Bargain Sale' or a real threat. Mention the Fear & Greed Index concept.)</span>
            </li>
            <li style="margin-bottom: 25px; background: #fafafa; padding: 15px; border-radius: 8px; border-left: 4px solid #27ae60;">
                <strong style="font-size: 1.2em;">2. The 60/30/10 Seesaw (Asset Allocation)</strong><br>
                <span style="display: block; margin-top: 8px;">(WRITE A FULL PARAGRAPH on how to adjust the golden ratio: 60% Stocks, 30% Real Estate/Safe Assets, 10% Cash based on today's events. How should we mechanically rebalance today?)</span>
            </li>
            <li style="margin-bottom: 25px; background: #fafafa; padding: 15px; border-radius: 8px; border-left: 4px solid #2980b9;">
                <strong style="font-size: 1.2em;">3. The Global Shield (US Dollar & Market)</strong><br>
                <span style="display: block; margin-top: 8px;">(WRITE A FULL PARAGRAPH explaining why holding strong US Assets and the Dollar is crucial right now as an ultimate safety net against today's volatility.)</span>
            </li>
            <li style="margin-bottom: 25px; background: #fafafa; padding: 15px; border-radius: 8px; border-left: 4px solid #e74c3c;">
                <strong style="font-size: 1.2em;">4. Survival Mechanics (Split Buying & Mental Peace)</strong><br>
                <span style="display: block; margin-top: 8px;">(WRITE A FULL PARAGRAPH defining the exact action: When to use the 3-part split buying (DCA) strategy, and why selling 50% during extreme panic is the ultimate mental defense mechanism.)</span>
            </li>
        </ul>

        <div style="background-color: #f0f7ff; border: 1px solid #cce3ff; padding: 25px; border-radius: 8px; margin-top: 35px; margin-bottom: 20px;">
            <h3 style="color: #0056b3; margin-top: 0; font-size: 1.4em;">✅ Today's VIP Action Plan</h3>
            <p style="margin-bottom: 12px; font-size: 1.05em;"><strong>🟢 DO (Immediate Action):</strong> (Provide 2 highly specific, actionable investment steps based on the news, utilizing the 60/30/10 rule or DCA.)</p>
            <p style="margin-bottom: 0; font-size: 1.05em;"><strong>🔴 DON'T (Critical Mistakes):</strong> (Provide 1 specific mistake to avoid right now, such as holding 100% cash or panic selling quality assets.)</p>
        </div>
            """

        if category == "Politics": expert_persona = "a veteran US political expert"
        elif category == "Tech": expert_persona = "a veteran US technology expert"
        elif category == "Health": expert_persona = "a veteran US healthcare expert"
        elif category == "Energy": expert_persona = "a veteran US energy expert"
        else: expert_persona = "a veteran US Wall Street expert"

        prompt = f"""
        [Goal] Write a highly insightful, deeply humanized blog post in ENGLISH for the '{category}' section of the 'Warm Insight' website.
        Target Audience: {tier} Subscribers.
        
        You are {expert_persona}.
        
        CRITICAL FORMATTING RULES:
        1. Write ENTIRELY in ENGLISH. NEVER use words like 'professor' or 'expert'.
        2. NEVER use ASCII art with vertical lines or spaces.
        3. For diagrams, MUST use horizontal "Emoji Flows" (e.g., Oil Strain 🛢️ ➡️ Shipping Costs 📈 ➡️ Inflation 💥).
        4. Use <br> tags properly so the text does not look clumped together.
        5. TIKTOK/FINTOK INFLUENCE: Create a 'Viral Social Insights 📱' section based on these vibes: {tiktok_urls_str}.{vip_extra_rules}

        OUTPUT STRUCTURE STRICTLY FOLLOW THIS EXACT HTML TEMPLATE:
        
        TITLE: (Insert Catchy Title)
        IMAGE_PROMPT: (Insert simple English prompt for image generation, e.g. cinematic abstract 3D representation of global {category})
        EXCERPT: (Write a VERY catchy 1-sentence summary WITHOUT HTML tags. This will show on the front page preview.)
        
        <h2>The Big Picture</h2>
        <p>(A warm, humanized 3-sentence summary of the news.)</p>
        
        <h2>Viral Social Insights 📱</h2>
        <p>(Translate the heavy news into a super-engaging TikTok style analogy or text meme.)</p>
        
        <h2>Top Drivers & Deep Insights</h2>
        <ul>
            <li>
                <strong style="font-size:1.2em;">(Headline 1)</strong><br><br>
                {depth_instruction}<br><br>
                <div style="background:#f4f4f4; padding:10px; border-radius:5px;">
                <strong>💡 Quick Flow:</strong> (Insert your Emoji Flow Diagram here. Example: A ➡️ B ➡️ C)
                </div>
            </li>
        </ul>
        
        {vip_extra_sections}
        
        <h2>Today's Warm Insight</h2>
        <p>(A comforting, actionable takeaway.)</p>
        
        <p><strong>P.S.</strong> (Add a very short, relatable personal thought.)</p>
        <p><em>Disclaimer: This article is for informational purposes only. All decisions are your own.</em></p>

        Raw News to Analyze:
        {selected_news}
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        raw_text = str(response.text).replace("```html", "").replace("```", "").strip()
        lines = raw_text.split('\n')
        
        pretty_tier = TIER_LABELS.get(tier, tier)
        title = f"({tier}) Daily {category} Insight"
        image_prompt = f"Abstract 3D illustration representing global {category}, cinematic lighting."
        custom_excerpt = "Insightful financial analysis for your future."
        html_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("TITLE:"):
                title = f"[{pretty_tier}] " + stripped.replace("TITLE:", "").strip()
            elif stripped.startswith("IMAGE_PROMPT:"):
                image_prompt = stripped.replace("IMAGE_PROMPT:", "").strip()
            elif stripped.startswith("EXCERPT:"):
                custom_excerpt = stripped.replace("EXCERPT:", "").strip()
            elif stripped:
                html_lines.append(stripped)
                
        html_content = "\n".join(html_lines).strip()
        
        current_time_str = datetime.now().strftime('%B %d, %Y at %I:%M %p (UTC)')
        author_name = "Ethan Cole & The Warm Insight Panel"
        
        info_box = f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #f2a900; margin-bottom: 25px; border-radius: 4px;">
            <p style="margin: 0; font-size: 0.95em; color: #555; line-height: 1.6;">
                <strong>✍️ Written by:</strong> {author_name}<br>
                <strong>⏰ Published:</strong> {current_time_str}
            </p>
        </div>
        """
        html_content = info_box + "\n" + html_content
            
        return title, image_prompt, html_content, custom_excerpt
        
    except Exception as e:
        print(f"⚠️ [AI 에러] {category} - {tier} 분석 실패: {e}")
        return None, None, None, None

def generate_thumbnail(image_prompt):
    print(f"🎨 무제한 무료 AI 썸네일 생성 시도 중... (프롬프트: {image_prompt})")
    
    for attempt in range(3):
        try:
            seed = random.randint(1, 100000)
            encoded_prompt = urllib.parse.quote(image_prompt + ", highly detailed, cinematic lighting")
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
            
            response = requests.get(url, timeout=45)
            
            if response.status_code == 200:
                print(f"✅ [썸네일 생성 성공] {attempt + 1}번째 시도만에 성공했습니다!")
                return response.content
            elif response.status_code == 429:
                print(f"⏳ [서버 과부하 429] 15초 대기 후 재시도합니다... ({attempt + 1}/3)")
                time.sleep(15)
            else:
                print(f"⚠️ [API 에러 {response.status_code}] 5초 후 재시도합니다... ({attempt + 1}/3)")
                time.sleep(5)
        except Exception as e:
            print(f"⚠️ [통신 지연] 서버가 바쁩니다. 5초 후 재시도... ({attempt + 1}/3)")
            time.sleep(5)
            
    print("🔄 [플랜 B 가동] AI 서버 응답 지연으로 대체 이미지를 사용합니다.")
    try:
        fallback_url = f"https://picsum.photos/1280/720?random={random.randint(1, 1000)}"
        response = requests.get(fallback_url, timeout=20)
        if response.status_code == 200:
            return response.content
    except:
        pass
        
    return None

def generate_ghost_token():
    id_str, secret_str = str(GHOST_ADMIN_API_KEY).split(':')
    iat = int(datetime.now().timestamp())
    header = dict(alg='HS256', typ='JWT', kid=id_str)
    payload = dict(iat=iat, exp=iat + 5 * 60, aud='/admin/')
    return jwt.encode(payload, bytes.fromhex(secret_str), algorithm='HS256', headers=header)

def upload_image_to_ghost(image_bytes):
    try:
        token = generate_ghost_token()
        headers = dict()
        headers.update({'Authorization': 'Ghost ' + token})
        
        files = dict()
        files.update({'file': ('thumbnail.jpg', image_bytes, 'image/jpeg')})
        files.update({'purpose': (None, 'image')})
        
        url = str(GHOST_API_URL) + "/ghost/api/admin/images/upload/"
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200 or response.status_code == 201:
            images = response.json().get('images')
            if images:
                for img in images:
                    return img.get('url')
        else:
            print(f"❌ [이미지 업로드 실패] {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ [이미지 통신 에러] {e}")
        return None

def publish_to_ghost(title, html_content, category, tier, feature_image_url, custom_excerpt):
    print(f"📝 Ghost 웹사이트에 '{title}' 글을 발행합니다...")
    try:
        token = generate_ghost_token()
        headers_dict = dict()
        headers_dict.update({'Authorization': 'Ghost ' + token})
        headers_dict.update({'Content-Type': 'application/json'})
        
        visibility_setting = "public"
        
        tag_dict = dict(name=category)
        tier_dict = dict(name=tier)
        tags_list = list()
        tags_list.append(tag_dict)
        tags_list.append(tier_dict)
        
        post_dict = dict()
        post_dict.update({"title": title})
        post_dict.update({"html": html_content})
        post_dict.update({"status": "published"})
        post_dict.update({"visibility": visibility_setting})
        post_dict.update({"tags": tags_list})
        
        if custom_excerpt:
            post_dict.update({"custom_excerpt": custom_excerpt})
            
        if feature_image_url:
            post_dict.update({"feature_image": feature_image_url})
            
        posts_list = list()
        posts_list.append(post_dict)
        
        post_data = dict()
        post_data.update({"posts": posts_list})
        
        url = str(GHOST_API_URL) + "/ghost/api/admin/posts/?source=html"
        response = requests.post(url, json=post_data, headers=headers_dict)
        
        if response.status_code == 200 or response.status_code == 201:
            print("🎉 [성공] 자동 발행 완료!")
        else:
            print(f"❌ [발행 실패] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ [통신 에러] Ghost 서버 연결 실패: {e}")

if __name__ == "__main__":
    try:
        for category, urls in CATEGORIES.items():
            print(f"\n--- [{category}] 지능형 큐레이션 및 분배 시작 ---")
            
            all_news = get_category_news(urls, count=20)
            if not all_news or len(all_news) < 3:
                print(f"⚠️ {category} 뉴스가 부족하여 건너뜁니다.")
                continue
            
            for task in TASKS:
                tier = task.get("tier")
                req_count = task.get("count")
                
                if len(all_news) < req_count:
                    break
                
                target_news = list()
                for _ in range(req_count):
                    target_news.append(all_news.pop(0))
                
                print(f"  -> ({tier}) 등급 리포트 ({req_count}개 뉴스) 및 썸네일 생성 중...")
                
                post_title, img_prompt, report_html, custom_excerpt = analyze_with_gemini(target_news, category, tier)
                
                if report_html and post_title:
                    feature_image_url = None
                    if img_prompt:
                        image_bytes = generate_thumbnail(img_prompt)
                        if image_bytes:
                            feature_image_url = upload_image_to_ghost(image_bytes)
                            
                    publish_to_ghost(post_title, report_html, category, tier, feature_image_url, custom_excerpt)
                    
                time.sleep(30) 

        print("\n🎉 모든 카테고리 중복 없는 지능형 자동 발행이 완료되었습니다!")
        
    except Exception as e:
        print("\n❌ 시스템 에러 발생")
        traceback.print_exc()
        sys.exit(1)
