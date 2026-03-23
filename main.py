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
print(" 🚀 40년 멘토 + VIP 타이탄 매뉴얼 + 무적 썸네일 봇 🚀")
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
        
        # 🚨 [VIP 전용 분기 처리] 기존의 안정적인 로직은 유지하되, VIP일 때만 프롬프트를 확장합니다.
        vip_extra_rules = ""
        vip_extra_sections = ""
        
        if tier == "Basic":
            depth_instruction = "<strong>🔑 The Core Fact:</strong> Explain what happened simply using ELI5 (Explain Like I'm 5)."
        elif tier == "Premium":
            depth_instruction = "<strong>🧐 WHY (The Hidden Reason):</strong> Explain using behavioral economics.<br><br><strong>🐑 THINK (What Masses Think):</strong> Explain the irrational market psychology."
        else: # Royal Premium (VIP)
            depth_instruction = "<strong>🧐 WHY (The Hidden Reason):</strong> Explain the true macroeconomic reason in deep detail.<br><br><strong>🐑 THINK (Herd Behavior):</strong> What the general public wrongly assumes.<br><br><strong>🦅 DIFFERENT THINK (Contrarian View):</strong> The hidden opportunity for true wealth."
            
            # VIP 전용 프롬프트 규칙 주입 (대표님이 주신 이미지 내용 반영)
            vip_extra_rules = """
        6. VIP EXCLUSIVE - PRO DATA: You MUST include a highly professional, analytical breakdown of relevant market data, charts, or indicators (e.g., RSI, moving averages, macro trends) related to the news.
        7. VIP EXCLUSIVE - TITAN PLAYBOOK: Integrate these 'Master Investor Rules' into the article:
           - Contrarian Focus: Extreme fear (Fear & Greed Index < 25) is a 'Generational Bargain Sale'.
           - The Seesaw (Asset Allocation): 60% Stocks, 30% Real Estate/Safe Assets, 10% Cash. Rebalance mechanically.
           - The Shield: The US Dollar & US Market (60% dominance) as the ultimate safe havens.
           - Survival Tactics: 3-part split buying (DCA), NEVER hold 100% cash, and 'Sell 50% for mental peace' if panic hits.
            """
            
            # VIP 전용 본문 섹션 주입
            vip_extra_sections = """
        <h2>📈 VIP Exclusive: Professional Chart & Data Analysis</h2>
        <p>(Provide a rigorous, professional breakdown of the underlying data, charts, or economic indicators driving this news. Use analytical terminology and explain what the 'trend lines' or 'macro data points' are signaling to institutional investors right now.)</p>

        <h2>🛡️ The Titan's Playbook: Mindset & Strategy</h2>
        <p>(Apply the 'Master Investor' principles here. Discuss the 60/30/10 asset allocation seesaw, the US Dollar shield, contrarian buying during extreme fear, and mechanical 3-part split-buying strategies tailored to today's specific news.)</p>
        <div style="background:#f8fbff; padding:15px; border-left: 5px solid #0056b3; border-radius:5px; margin-top:15px; margin-bottom:15px;">
            <strong style="color:#0056b3; font-size:1.1em;">✅ The Titan's Action Plan</strong><br><br>
            <strong>🟢 DO (Actionable Steps):</strong> (Specific action based on the Titan rules - e.g., Mechanical rebalancing, split buying)<br><br>
            <strong>🔴 DON'T (Critical Mistakes):</strong> (Specific mistake to avoid - e.g., FOMO buying at the top or panic selling 100%)
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

        OUTPUT STRUCTURE STRICTLY FOLLOW THIS:
        
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
