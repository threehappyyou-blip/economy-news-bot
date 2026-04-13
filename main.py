# ═══════════════════════════════════════════════
# v12 업그레이드 패치 — 아래 함수들을 main.py에서 교체하세요
# 변경 1: SEO 타이틀에서 이모지 제거
# 변경 2: AI 프롬프트에 FAQ 생성 추가
# 변경 3: FAQ Schema JSON-LD 자동 삽입
# 변경 4: 소셜 링크 + 관련 글 섹션 강화
# ═══════════════════════════════════════════════

# ── 소셜 링크 설정 (코드 상단 CONFIG 영역에 추가) ──
SOCIAL_LINKS = {
    "youtube": "https://www.youtube.com/@WarmInsightyou",
    "x": "https://x.com/warminsight",       # X(트위터) 계정이 있으면 입력
    "linkedin": "",                           # LinkedIn 있으면 입력
}

# ═══════════════════════════════════════════════
# 변경 1: publish() — SEO 타이틀에서 이모지/VIP 접두사 제거
# ═══════════════════════════════════════════════
def _clean_seo_title(title):
    """[👑 VIP] 같은 접두사를 SEO용 타이틀에서 제거"""
    clean = title
    for prefix in ["[💎 Pro] ", "[👑 VIP] ", "[💎 Pro]", "[👑 VIP]"]:
        clean = clean.replace(prefix, "")
    return clean.strip()

# publish() 함수 안의 rank_math 메타 부분을 이렇게 교체:
# (기존 코드에서 `if kw: post_data["meta"] = ...` 블록을 아래로 교체)
"""
            seo_title = _clean_seo_title(title)
            if kw:
                post_data["meta"] = {
                    "rank_math_title": (seo_title + " | Warm Insight")[:60],
                    "rank_math_description": (exc[:120] + " Expert " + cat.lower() + " analysis by Warm Insight.")[:155],
                    "rank_math_focus_keyword": kw,
                }
"""

# ═══════════════════════════════════════════════
# 변경 2: 프롬프트에 FAQ 태그 추가
# ═══════════════════════════════════════════════
# PROMPT_PREMIUM 끝에 추가 (</PS> 뒤, "News:" 앞):
FAQ_PROMPT_ADDITION = (
    "<FAQ_1_Q>A question a reader would Google about this topic</FAQ_1_Q>\n"
    "<FAQ_1_A>Clear 2-3 sentence answer</FAQ_1_A>\n"
    "<FAQ_2_Q>Second question about market implications</FAQ_2_Q>\n"
    "<FAQ_2_A>Clear 2-3 sentence answer</FAQ_2_A>\n"
    "<FAQ_3_Q>Third question about what investors should do</FAQ_3_Q>\n"
    "<FAQ_3_A>Clear 2-3 sentence answer</FAQ_3_A>\n"
)
# VIP_P1에도 동일하게 추가

# ═══════════════════════════════════════════════
# 변경 3: FAQ Schema + FAQ HTML 빌더
# ═══════════════════════════════════════════════
def _build_faq_schema(raw):
    """FAQPage JSON-LD — AI 검색(ChatGPT, Perplexity, Google AI Overview) 노출용"""
    faqs = []
    for i in range(1, 4):
        q = xtag(raw, f"FAQ_{i}_Q")
        a = xtag(raw, f"FAQ_{i}_A")
        if q and a and len(q) > 10 and len(a) > 20:
            faqs.append({"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}})
    if not faqs:
        return "", ""
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faqs
    }
    schema_html = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False) + '</script>'
    # FAQ visible section for readers
    faq_visible = '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:28px;margin:35px 0;">'
    faq_visible += '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:20px;">❓ Frequently Asked Questions</h3>'
    for faq in faqs:
        faq_visible += '<div style="margin-bottom:18px;border-bottom:1px solid #e5e7eb;padding-bottom:16px;">'
        faq_visible += '<p style="font-size:17px;font-weight:700;color:#1a252c;margin:0 0 8px;">' + faq["name"] + '</p>'
        faq_visible += '<p style="font-size:16px;line-height:1.7;color:#374151;margin:0;">' + faq["acceptedAnswer"]["text"] + '</p>'
        faq_visible += '</div>'
    faq_visible += '</div>'
    return schema_html, faq_visible

# ═══════════════════════════════════════════════
# 변경 4: 소셜 공유 버튼 + 관련 글 섹션
# ═══════════════════════════════════════════════
def _build_social_share(title, slug):
    """기사 하단 소셜 공유 버튼 (트위터, 링크드인, 이메일)"""
    post_url = SITE_URL + "/" + slug + "/"
    encoded_title = title.replace(" ", "%20").replace("&", "%26")[:100]
    encoded_url = post_url.replace(":", "%3A").replace("/", "%2F")

    return (
        '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:22px;margin:30px 0;text-align:center;">'
        '<p style="font-size:18px;font-weight:700;color:#1a252c;margin:0 0 14px;">Share This Analysis</p>'
        '<div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap;">'
        # X (Twitter)
        '<a href="https://twitter.com/intent/tweet?text=' + encoded_title + '&url=' + encoded_url + '" '
        'target="_blank" rel="noopener" style="display:inline-block;background:#000;color:#fff;'
        'padding:10px 20px;border-radius:8px;font-size:14px;font-weight:bold;text-decoration:none;">𝕏 Share</a>'
        # LinkedIn
        '<a href="https://www.linkedin.com/sharing/share-offsite/?url=' + encoded_url + '" '
        'target="_blank" rel="noopener" style="display:inline-block;background:#0A66C2;color:#fff;'
        'padding:10px 20px;border-radius:8px;font-size:14px;font-weight:bold;text-decoration:none;">in Share</a>'
        # Email
        '<a href="mailto:?subject=' + encoded_title + '&body=Check%20this%20out%3A%20' + encoded_url + '" '
        'style="display:inline-block;background:#6b7280;color:#fff;'
        'padding:10px 20px;border-radius:8px;font-size:14px;font-weight:bold;text-decoration:none;">✉ Email</a>'
        '</div>'
        '</div>'
    )

def _build_related_posts(cat):
    """관련 글 섹션 — 같은 카테고리 + 관련 카테고리 링크"""
    pillar = PILLAR_PAGES.get(cat, PILLAR_PAGES["Economy"])
    related_cats = CAT_RELATED.get(cat, ["Economy", "Tech"])

    html = '<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:12px;padding:28px;margin:30px 0;">'
    html += '<h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:16px;">📖 Continue Reading</h3>'
    html += '<div style="display:flex;flex-wrap:wrap;gap:12px;">'
    # Main category
    html += '<a href="' + pillar["url"] + '" style="display:inline-block;background:#fff;border:2px solid #3b82f6;color:#1e40af;padding:10px 18px;border-radius:8px;font-size:15px;font-weight:600;text-decoration:none;">Browse ' + pillar["anchor"] + ' →</a>'
    # Related categories
    for rc in related_cats[:2]:
        rp = PILLAR_PAGES.get(rc)
        if rp:
            html += '<a href="' + rp["url"] + '" style="display:inline-block;background:#fff;border:1px solid #e5e7eb;color:#374151;padding:10px 18px;border-radius:8px;font-size:15px;text-decoration:none;">' + rc + ' Analysis →</a>'
    # VIP CTA
    html += '<a href="' + SITE_URL + '/warm-insight-vip-membership/" style="display:inline-block;background:#b8974d;color:#fff;padding:10px 18px;border-radius:8px;font-size:15px;font-weight:bold;text-decoration:none;">🔒 Upgrade to VIP →</a>'
    html += '</div></div>'
    return html

# ═══════════════════════════════════════════════
# 변경 5: _ftr() 교체 — 소셜 아이콘 + YouTube 강화
# ═══════════════════════════════════════════════
def _ftr(tw, ps):
    if not tw or is_echo(tw): tw = "Stay disciplined, stay diversified, and let time compound in your favor."
    if not ps or is_echo(ps): ps = "In 40 years of watching markets, the disciplined investor always wins."

    social_icons = ''
    if SOCIAL_LINKS.get("youtube"):
        social_icons += '<a href="' + SOCIAL_LINKS["youtube"] + '" target="_blank" style="display:inline-block;background:#FF0000;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold;text-decoration:none;margin:0 4px;">▶ YouTube</a>'
    if SOCIAL_LINKS.get("x"):
        social_icons += '<a href="' + SOCIAL_LINKS["x"] + '" target="_blank" style="display:inline-block;background:#000;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold;text-decoration:none;margin:0 4px;">𝕏 Follow</a>'
    if SOCIAL_LINKS.get("linkedin"):
        social_icons += '<a href="' + SOCIAL_LINKS["linkedin"] + '" target="_blank" style="display:inline-block;background:#0A66C2;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:bold;text-decoration:none;margin:0 4px;">in LinkedIn</a>'

    return (
        '<hr style="border:0;height:1px;background:#e5e7eb;margin:45px 0;">'
        '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Today\'s Warm Insight</h2>'
        '<p style="' + F + '">' + tw + '</p>'
        '<div style="margin-top:30px;background:#1e293b;padding:28px;border-radius:8px;border-left:4px solid #b8974d;">'
        '<p style="font-size:18px;line-height:1.8;color:#e2e8f0;margin:0;">'
        '<span style="color:#b8974d;font-weight:bold;">P.S.</span> '
        '<span style="color:#cbd5e1;">' + ps + '</span></p></div>'
        # CTA + Social
        '<div style="background:#f8fafc;border:2px solid #e5e7eb;border-radius:10px;padding:28px;margin:40px 0;text-align:center;">'
        '<p style="font-size:22px;font-weight:bold;color:#1a252c;margin:0 0 10px;">Found this useful?</p>'
        '<p style="font-size:16px;color:#6b7280;margin:0 0 18px;">Forward to a friend who wants smarter market analysis.</p>'
        '<div style="margin-bottom:14px;">' + social_icons + '</div>'
        '<p style="margin:0;"><a href="' + SITE_URL + '" style="color:#b8974d;font-weight:600;text-decoration:underline;">Subscribe at warminsight.com</a></p>'
        '</div>'
        # Footer
        '<div style="background:#1e293b;padding:35px;border-radius:10px;margin-top:30px;">'
        '<p style="font-size:24px;font-weight:bold;color:#b8974d;margin:0 0 12px;text-align:center;">Warm Insight</p>'
        '<div style="text-align:center;margin-bottom:16px;">' + social_icons + '</div>'
        '<div style="text-align:center;margin-bottom:16px;font-size:13px;">'
        '<a href="' + SITE_URL + '/about-us/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">About</a>'
        '<a href="' + SITE_URL + '/privacy-policy/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">Privacy</a>'
        '<a href="' + SITE_URL + '/terms/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">Terms</a>'
        '<a href="' + SITE_URL + '/warm-insight-vip-membership/" style="color:#cbd5e1;text-decoration:none;margin:0 8px;">VIP</a>'
        '</div>'
        '<p style="font-size:13px;color:#64748b;margin:0;text-align:center;">'
        'All analysis is for informational purposes only. Not financial advice.<br>'
        '&copy; 2026 Warm Insight. All rights reserved.</p>'
        '</div></div>'
    )

# ═══════════════════════════════════════════════
# 변경 6: analyze() — FAQ + 소셜공유 + 관련글 추가
# ═══════════════════════════════════════════════
# analyze() 함수의 마지막 부분 (html 조립 후) 을 이렇게 교체:
"""
    # ... (기존 html 생성 코드 뒤에)
    
    tr = xtag(raw, "TITLE")
    exc = xtag(raw, "EXCERPT") or "Expert analysis."
    kw = xtag(raw, "SEO_KEYWORD")
    title = "[" + TIER_LABELS.get(tier, tier) + "] " + tr if tr else "(" + tier + ") " + cat + " Insight"
    slug = make_slug(kw, tr or cat, cat)
    
    # FAQ schema + visible FAQ section
    faq_schema, faq_visible = _build_faq_schema(raw)
    
    # Assemble SEO additions
    html += faq_visible                        # FAQ Q&A 섹션
    html += _build_social_share(title, slug)   # 소셜 공유 버튼
    html += _build_related_posts(cat)          # 관련 글 섹션
    html += _build_internal_links(cat)         # 내부 링크
    html += _build_author_bio(cat)             # 저자 프로필
    
    html = sanitize(html)
    return title, html, exc, kw, slug, tier
"""

# ═══════════════════════════════════════════════
# 변경 7: publish() — FAQ Schema를 codeinjection에 추가
# ═══════════════════════════════════════════════
# publish() 함수에서 full_content 조립 시:
"""
            # JSON-LD schemas
            schemas = ""
            if kw and slug:
                schemas += _build_jsonld(title, exc or "", kw, cat, slug, "")
            # FAQ schema도 추가
            faq_schema, _ = _build_faq_schema(raw)  # raw를 publish에 전달해야 함
            schemas += faq_schema
            
            full_content = schemas + full_content
            
            # SEO title에서 이모지 제거
            seo_title = _clean_seo_title(title)
            if kw:
                post_data["meta"] = {
                    "rank_math_title": (seo_title + " | Warm Insight")[:60],
                    "rank_math_description": (exc[:120] + " Expert " + cat.lower() + " analysis.")[:155],
                    "rank_math_focus_keyword": kw,
                }
"""
