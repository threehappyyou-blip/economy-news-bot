# ═══════════════════════════════════════════════
# 수정사항 4가지 — 아래 함수들만 교체하세요
# ═══════════════════════════════════════════════

# ───────────────────────────────────────────────
# 수정 1: call_gem() — 에러 로그 복원 (핵심 원인)
# ───────────────────────────────────────────────
def call_gem(client, model, prompt, retries=2):
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt)
            text = str(r.text) if r.text else ""
            if not text:
                print("    Gem(" + model + ") attempt " + str(i) + ": Empty response")
                if i < retries:
                    time.sleep(10 * i)
                continue
            return text
        except Exception as e:
            err_str = str(e)
            # ★ 이 줄이 WP 버전에서 빠져있었음 — Gemini 실패 원인이 로그에 안 나옴
            print("    Gem(" + model + ") attempt " + str(i) + ": " + err_str[:200])
            if "503" in err_str or "UNAVAILABLE" in err_str:
                time.sleep(15 * i)
            elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                print("    ★ API 할당량 초과! 30초 대기...")
                time.sleep(30 * i)
            elif "blocked" in err_str.lower() or "safety" in err_str.lower():
                print("    ★ Safety filter 차단! 프롬프트 조정 필요")
                if i < retries:
                    time.sleep(5)
            elif i < retries:
                time.sleep(10 * i)
    return None


# ───────────────────────────────────────────────
# 수정 2: publish() — 에러 로그 추가 + 카테고리 지원
# ───────────────────────────────────────────────

# WordPress 카테고리 ID 캐시 (한번 조회 후 재사용)
_wp_cat_cache = {}

def get_or_create_wp_category(cat_name):
    """WordPress에서 카테고리 ID를 가져오거나 새로 생성"""
    if cat_name in _wp_cat_cache:
        return _wp_cat_cache[cat_name]
    try:
        # 기존 카테고리 검색
        r = requests.get(
            WP_URL + "/wp-json/wp/v2/categories?search=" + cat_name + "&per_page=10",
            auth=WP_AUTH, timeout=15)
        if r.status_code == 200:
            for c in r.json():
                if c["name"].lower() == cat_name.lower():
                    _wp_cat_cache[cat_name] = c["id"]
                    print("  WP Category '" + cat_name + "' = ID " + str(c["id"]))
                    return c["id"]
        # 카테고리가 없으면 생성
        r2 = requests.post(
            WP_URL + "/wp-json/wp/v2/categories",
            auth=WP_AUTH,
            json={"name": cat_name, "slug": cat_name.lower()},
            timeout=15)
        if r2.status_code in (200, 201):
            new_id = r2.json()["id"]
            _wp_cat_cache[cat_name] = new_id
            print("  WP Category '" + cat_name + "' created = ID " + str(new_id))
            return new_id
    except Exception as e:
        print("  WP Category error: " + str(e))
    return None


def publish(title, html, cat, tier, feature_img_id, exc, kw="", slug=""):
    """워드프레스에 포스트 발행 — 에러 로그 추가 + 카테고리 지원"""
    print("  Pub: " + title[:60])
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            public_html, private_html = _split_html_for_paywall(html)
            full_content = public_html
            if private_html:
                full_content += "\n\n<!--more-->\n\n" + private_html

            seo_additions = ""
            if kw and slug:
                seo_additions = _build_jsonld(title, exc or "", kw, cat, slug, "")
            full_content = seo_additions + full_content

            post_data = {
                "title": title,
                "content": full_content,
                "status": "publish",
                "excerpt": exc[:290] if exc else "",
            }

            # ★ 카테고리 할당 (Ghost의 tag 대신)
            cat_id = get_or_create_wp_category(cat)
            if cat_id:
                post_data["categories"] = [cat_id]

            # ★ 태그 추가 (tier + SEO keyword)
            tag_names = [tier]
            if kw and len(kw) > 3:
                tag_names.append(kw[:50])
            # WP 태그는 ID가 필요하므로 이름으로 직접 설정
            # (WP REST API에서 tags는 ID 배열이 필요 — 생략 시 태그 없음)

            if slug:
                post_data["slug"] = slug
            if feature_img_id:
                post_data["featured_media"] = feature_img_id

            # ★ Yoast/Rank Math SEO 메타 (설치되어 있다면)
            if kw:
                seo_title = (kw + " | " + cat + " Analysis | Warm Insight")[:60]
                seo_desc = (exc[:120] + " Expert " + cat.lower() + " market analysis by Warm Insight.")[:155]
                # Rank Math SEO 필드 (2번 사진에서 Rank Math SEO가 보임)
                post_data["meta"] = {
                    "rank_math_title": seo_title,
                    "rank_math_description": seo_desc,
                    "rank_math_focus_keyword": kw,
                }

            r = requests.post(
                WP_URL + "/wp-json/wp/v2/posts",
                auth=WP_AUTH,
                json=post_data,
                timeout=60)

            if r.status_code in (200, 201):
                post_url = r.json().get("link", "")
                print("  ✅ WP Post OK! (attempt " + str(attempt) + ") " + post_url)
                return True
            elif r.status_code == 401:
                # ★ 인증 실패 로그 추가
                print("  ❌ WP 401 Unauthorized: Application Password가 잘못되었거나 권한 부족")
                print("     Response: " + r.text[:300])
                return False
            elif r.status_code == 403:
                # ★ 403 에러 로그 추가 (원본 WP 코드에서 누락)
                print("  ❌ WP 403 Forbidden (attempt " + str(attempt) + "): " + r.text[:300])
                if attempt < max_retries:
                    time.sleep(10 * attempt)
                    continue
                return False
            elif r.status_code == 429:
                print("  ⚠️ WP 429 Rate Limited (attempt " + str(attempt) + ")")
                time.sleep(30 * attempt)
                continue
            else:
                # ★ 기타 에러 로그 추가
                print("  ❌ WP FAIL " + str(r.status_code) + ": " + r.text[:300])
                return False
        except Exception as e:
            print("  ❌ WP Exception: " + str(e))
            if attempt < max_retries:
                time.sleep(5 * attempt)
    return False


# ───────────────────────────────────────────────
# 수정 3: upload_img() — 에러 로그 추가
# ───────────────────────────────────────────────
def upload_img(img_bytes):
    """워드프레스 미디어 라이브러리에 썸네일 업로드"""
    for attempt in range(2):
        try:
            headers = {
                'Content-Disposition': 'attachment; filename="warm_insight_thumb.jpg"',
                'Content-Type': 'image/jpeg'
            }
            r = requests.post(
                WP_URL + "/wp-json/wp/v2/media",
                auth=WP_AUTH,
                headers=headers,
                data=img_bytes,
                timeout=30)
            if r.status_code in (200, 201):
                media_id = r.json()["id"]
                print("  ✅ Image uploaded: ID " + str(media_id))
                return media_id
            else:
                # ★ 에러 로그 추가
                print("  ❌ Image upload " + str(r.status_code) + ": " + r.text[:200])
                if attempt == 0:
                    time.sleep(3)
        except Exception as e:
            print("  ❌ Image upload error: " + str(e))
            if attempt == 0:
                time.sleep(3)
    return None


# ───────────────────────────────────────────────
# 수정 4: main() — analyze 실패 시 디버그 로그 추가
# ───────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  Warm Insight v11 (WP Adapted Build)")
    print("  Tiers: Premium + VIP | Model: all flash")
    print("=" * 50)
    
    # ★ Python stdout 버퍼링 방지 (GitHub Actions에서 로그 누락 방지)
    import functools
    print = functools.partial(__builtins__['print'] if isinstance(__builtins__, dict) else getattr(__builtins__, 'print'), flush=True)
    # 또는 GitHub Actions workflow에서: PYTHONUNBUFFERED=1

    cat = get_current_category()
    urls = CATEGORIES.get(cat)
    if not urls:
        print("No URLs")
        return
    recent = get_recent_titles()
    print("\n--- [" + cat + "] ---")
    news = get_news(urls, 20)
    if len(news) < 5:
        print("  Not enough news (" + str(len(news)) + ")")
        return

    gem_client = genai.Client(api_key=GEMINI_API_KEY)
    total = ok_cnt = fail = 0

    for task in TASKS:
        tier, cnt = task["tier"], task["count"]
        if len(news) < cnt:
            print("  Skip " + tier + " (not enough news)")
            break
        target = [news.pop(0) for _ in range(cnt)]
        total += 1
        print("\n  [" + TIER_LABELS[tier] + "] " + str(cnt) + " articles...")

        result = analyze(target, cat, tier)
        if not result or not result[1]:
            # ★ 실패 원인 디버그 로그 추가
            print("  ❌ ANALYZE FAILED for " + tier)
            if result:
                print("    result[0]=" + str(result[0])[:100])
                print("    result[1]=" + str(result[1])[:100] if result[1] else "    result[1]=None")
            else:
                print("    result=None (Gemini API 호출 실패 가능성 높음)")
            fail += 1
            continue

        title, html, exc, kw, slug, _ = result
        print("  Title: " + title[:80])
        print("  Slug: " + slug[:60])

        if is_duplicate(title, recent):
            print("  SKIP dup")
            fail += 1
            continue

        if tier not in SKIP_EDITOR_TIERS:
            passed, issues = editor_review(gem_client, "\n".join(target), html)
            if not passed:
                print("    Retry after editor reject...")
                time.sleep(10)
                result2 = analyze(target, cat, tier)
                if result2 and result2[1]:
                    title, html, exc, kw, slug, _ = result2
                    p2, _ = editor_review(gem_client, "\n".join(target), html)
                    if not p2:
                        print("  REJECTED x2 — skipping " + tier)
                        fail += 1
                        continue
                else:
                    fail += 1
                    continue

        print("  Generating thumbnail...")
        thumb_bytes = make_dynamic_thumb(title, cat, tier)
        feature_img = None
        if thumb_bytes:
            feature_img = upload_img(thumb_bytes)
            if feature_img:
                print("  Thumb uploaded OK")
            else:
                print("  Thumb upload failed — publishing without image")

        success = publish(title, html, cat, tier, feature_img, exc, kw, slug)
        if success:
            ok_cnt += 1
            recent.append(title.lower())
        else:
            fail += 1

        extra = random.randint(60, 180)
        sl = TIER_SLEEP[tier] + extra
        print("  Wait " + str(sl) + "s")
        time.sleep(sl)

    print("\n" + "=" * 50)
    print("  " + cat + " | Total " + str(total) + " | OK " + str(ok_cnt) + " | Fail " + str(fail))
    print("=" * 50)
