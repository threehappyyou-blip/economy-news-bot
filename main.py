

팀 멤버 초대
1775158045742_image.png
1775158073672_image.png
1775158110907_image.png
1775158133282_image.png

# -*- coding: utf-8 -*- """ Warm Insight v9 FINAL — Complete Clean Build All features from scratch. Zero patches. Python 3.10 safe. Features: Global RSS, 3-tier, hourly rotation, dedup, editor factcheck, SEO, VIP split-call, visual elements, professional tone, pro footer. """ import os, sys, traceba

pasted

지금 전달드린 내용을 분석을 아주 심도있게 분석 후 아래 내용이 적용되고 있는지 확인 부탁드립니다

각각 카테고리별로 1시간 단위로 랜덤으로 뉴스레터 발행 후 업로드 중이게 실행 되고 있는지?
4월 3일

코드와 로그를 검증하여 시스템 작동 상태를 진단했습니다
코드와 로그를 검증하여 시스템 작동 상태를 진단했습니다
코드와 로그, 그리고 Ghost 사이트 스크린샷을 꼼꼼히 분석했습니다. 핵심부터 말씀드리면, "카테고리별 1시간 단위"는 작동하고 있지만 "랜덤"은 아니고, 실제 발행 성공률에 심각한 문제가 있습니다.

카테고리 로테이션: 작동하지만 랜덤이 아님

get_current_category() 함수를 보면:

python
h = datetime.utcnow().hour
idx = h % len(cats)  # h % 5
이건 UTC 시간을 5로 나눈 나머지로 카테고리를 고정 배정하는 방식입니다. 즉 UTC 0시는 항상 Economy, UTC 1시는 항상 Politics, UTC 3시는 항상 Health... 이런 식으로 매일 같은 시간에 같은 카테고리가 반복됩니다. 로그에서도 UTC 18 -> Health (18 % 5 = 3)로 정확히 이 패턴을 따르고 있어요. GitHub Actions cron 0 * * * *로 매시간 실행되는 것은 맞습니다.

만약 진짜 랜덤 로테이션을 원하셨다면 random.choice()나 최소한 날짜+시간 조합의 셔플이 필요합니다.

실제 발행 상태: 심각한 실패율

로그(Image 1)에서 이 한 번의 실행(Health 카테고리)만 봐도 문제가 드러납니다:

Free 티어 — gemini-2.5-flash가 503 UNAVAILABLE 2회 연속 → 콘텐츠 생성 자체가 실패했을 가능성이 높습니다. 재시도 로직(retries=2)이 있지만 모델 자체가 다운이면 소용없습니다.

Pro 티어 — Gemini는 성공하고 Editor도 PASS했지만 두 가지 문제가 발생했습니다. 첫째, Imagen(1): 'Models' object has no attribute 'generate_images' — Imagen API 호출이 완전히 깨져 있어서 모든 썸네일이 picsum 랜덤 사진으로 대체되고 있습니다. 둘째, Ghost 퍼블리시에서 403 에러가 뜨면서 "Starter plan" 제한에 걸렸습니다. 즉 Pro 글이 실제로 발행되지 않았을 수 있어요.

VIP 티어 — 가장 심각합니다. Part 1은 성공했지만 Part 2에서 ok_tag 검증을 통과하지 못해 재시도 2회 → Fallback 프롬프트까지 갔고, 결국 Editor가 "False Causation" 이유로 2회 연속 REJECTED. 최종 결과: VIP 글 발행 실패.

최종 결과: Health | Total 3 | OK 1 | Fail 2 — 성공률 33%.

Ghost 사이트(Image 3, 4)를 보면

4월 1일자 글들이 Economy, Politics, Energy 등 여러 카테고리에서 Free/Pro/VIP 모두 올라가 있으므로, 다른 시간대에서는 성공적으로 발행된 적이 있다는 건 확인됩니다. 다만 썸네일들이 전부 picsum 풍경 사진(나무 판자길, 솔방울, 풀밭 등)인 것을 보면 Imagen이 꽤 오래전부터 실패하고 있었다는 뜻입니다.

정리하면 지금 고쳐야 할 것들의 우선순위는:

1) Ghost 403 Starter plan 제한 — 이게 가장 치명적입니다. 이미지 업로드나 특정 API 기능이 Starter plan에서 막히고 있는 것 같으니, Ghost plan을 확인하거나 upload_img 호출을 조건부로 스킵하는 처리가 필요합니다.

2) Imagen API 깨짐 — generate_images attribute가 없다는 건 genai 라이브러리 버전과 Imagen API 호출 방식이 맞지 않는 겁니다. requirements.txt에서 google-genai 버전을 확인하고 API 문서와 대조해야 합니다.

3) VIP P2 안정성 — Part 2가 너무 자주 실패합니다. is_echo() 검증이 너무 공격적이거나, 프롬프트가 너무 길어서 모델이 지시를 따르지 못하는 것일 수 있습니다. Fallback 프롬프트(VIP_FB)도 실패하면 결국 Editor에서 걸리고 있으니, P2 프롬프트 자체를 간소화하는 것도 방법입니다.

4) 랜덤 로테이션 — 현재 고정 순환이 의도된 거라면 괜찮지만, 진짜 랜덤을 원하셨다면 로직 수정이 필요합니다.

어떤 부분부터 수정 작업 들어갈까요?

4가지 모두 동시에 수정된 코드를 심도있게 고민해서 만들어주세요 그리고 다시 만든 코드에 문제가 없는지 재검토도 꼭 부탁드립니다
감사합니다

4월 3일

코드를 철저히 검토하고 문제점을 파악했습니다
코드를 철저히 검토하고 문제점을 파악했습니다
4가지 문제를 모두 동시에 수정한 v10 코드를 만들겠습니다. 각 수정 사항을 꼼꼼히 설계하고 재검토까지 진행합니다.

Warm Insight v10 — 4-Issue Fix
코드 
이제 코드 재검토를 하겠습니다.

재검토 결과: 4가지 수정 사항 검증

FIX 1 — Ghost 403 퍼블리시 재시도

publish() 함수가 이제 최대 3회 재시도하며 매번 gtoken()으로 새 JWT를 발급합니다. 403일 경우 점진적 백오프(10s → 20s → 30s)를 적용하고, 마지막 시도에서는 이미지를 제거한 채 한 번 더 시도합니다. 429 rate limit도 별도 처리합니다. upload_img()도 2회 재시도로 강화했고, 403이면 깔끔하게 None을 반환합니다. publish()가 이제 bool을 반환하므로 main()에서 성공/실패를 정확히 추적합니다.

FIX 2 — Imagen API 이중 폴백

make_thumb()에 3단계 전략을 적용했습니다. 먼저 hasattr(c.models, "generate_images")로 라이브러리 메서드 존재 여부를 체크합니다. 없으면 Imagen REST API(/v1beta/models/imagen-3.0-generate-001:predict)를 직접 호출합니다. 둘 다 실패하면 카테고리+날짜 기반 seed로 picsum을 호출해서, 같은 시간대에 같은 카테고리면 일관된 이미지를 제공합니다. import base64도 상단에 추가했습니다.

FIX 3 — VIP P2 안정성

세 가지를 동시에 수정했습니다. is_echo() 임계값을 2→3으로 올리고 시그니처를 더 구체적으로 변경해서 false positive를 줄였습니다. VIP_P2 프롬프트를 전면 재작성해서 "Write a full paragraph"처럼 자연스러운 지시로 바꾸고, "CRITICAL: Do NOT echo instructions back"을 명시했습니다. EDITOR_PROMPT에도 "일반적 시장 맥락 분석은 허용, 특정 뉴스→특정 기업 행동의 거짓 인과관계만 거부"라는 가이드라인을 추가해서 불필요한 REJECT를 방지합니다. MODEL_PRI의 Basic 티어에 gemini-2.5-pro 폴백도 추가해서 flash가 503일 때 pro로 재시도합니다.

FIX 4 — 일자별 랜덤 로테이션

get_current_category()가 이제 year*10000 + month*100 + day를 seed로 사용해 random.Random(seed).shuffle()로 매일 다른 순서를 생성합니다. 같은 날 같은 시간이면 같은 카테고리를 보장(재현성)하면서도, 매일 순서가 바뀝니다. 로그에도 seed값과 당일 순서가 출력됩니다.

추가 발견 사항 — 코드에서는 고칠 수 없는 것

Ghost 403이 플랜 제한(Starter plan의 custom integration 제약)이라면 코드 재시도만으로는 근본적 해결이 안 됩니다. Ghost 대시보드에서 현재 플랜과 API 사용 한도를 확인해보시는 걸 권장드립니다. 만약 특정 시간대에만 403이 뜬다면 rate limit일 가능성이 높고, 그 경우 이 코드의 재시도 로직으로 충분히 해결됩니다.


Run python main.py ================================================== Warm Insight v10 (4-Issue Fix) ================================================== UTC 19 -> Energy (daily seed: 20260402, order: ['Health', 'Economy', 'Politics', 'Tech', 'Energy']) Dedup fetch status: 403 --- [Energ

pasted

지금 이렇게 실행 되었는데요 제대로 실행된게 맞을까요?

4월 3일

코드 개선사항 검증하고 Ghost 플랜 제한 식별했습니다
코드 개선사항 검증하고 Ghost 플랜 제한 식별했습니다
코드 자체는 의도대로 작동했지만, Ghost 403이 플랜 제한 문제라서 코드로는 해결이 불가능한 상황입니다. 하나씩 짚어드리겠습니다.

잘 작동한 것들 (3/4 수정 성공)

FIX 4 ✅ — 랜덤 로테이션이 정상 작동합니다. daily seed: 20260402, order: ['Health', 'Economy', 'Politics', 'Tech', 'Energy']로 매일 다른 순서가 생성되고, UTC 19시에 Energy가 올바르게 선택됐습니다.

FIX 3 ✅ — VIP P2가 재시도 없이 한 번에 성공했고, Editor도 첫 시도에 PASS. v9에서 P2 retry 2회 + Fallback + REJECTED x2였던 것과 비교하면 극적인 개선입니다.

FIX 2 ✅ (부분) — hasattr 가드가 크래시 없이 작동했고, Imagen REST도 404를 깔끔하게 처리한 뒤 Picsum 폴백으로 넘어갔습니다. Imagen 404는 API 키에 Imagen 모델이 활성화되지 않아서 발생한 것으로, Google AI Studio에서 별도 활성화가 필요합니다.

해결 불가능한 문제: Ghost Starter 플랜 제한

403 에러 메시지가 핵심입니다:

"You can use all our official, built-in integrations on the Starter plan. If you upgrade to one of our higher tiers, you'll also be able to create and edit custom integrations"

이 말은 Ghost Admin API 자체가 Starter 플랜에서 차단되었다는 뜻입니다. GHOST_ADMIN_API_KEY는 custom integration이므로, 아무리 재시도해도 403이 나올 수밖에 없습니다. 이건 코드 문제가 아니라 Ghost 구독 플랜 문제입니다.

이전에 4월 1일에 글이 올라갔던 건 아마 플랜이 바뀌기 전이었거나, 무료 체험 기간이었을 가능성이 높습니다.

지금 해야 할 선택지는 두 가지입니다:

옵션 A: Ghost 플랜 업그레이드 — Creator 플랜($9/월) 이상으로 올리면 Admin API가 즉시 활성화되고, 현재 코드가 바로 작동합니다. 가장 간단한 해결책입니다.

옵션 B: Self-hosted Ghost로 전환 — 직접 서버에 Ghost를 설치하면 플랜 제한 없이 Admin API를 무제한 사용할 수 있습니다. DigitalOcean이나 Railway에 $4-6/월 정도로 운영 가능합니다. 단, 초기 설정과 유지보수 부담이 있습니다.

어떤 방향으로 가실지 결정하시면, 그에 맞춰 다음 단계를 도와드리겠습니다.

1775165143213_image.png
Creator 플랜($9/월)이 없는데 지금 전달드린 사진이 Ghost 요금제 입니다
어떤걸 해야 Admin API가 즉시 활성화 할 수 있다는건가요?

4월 3일

관리자 API 활성화를 위한 요금제 업그레이드 필요성을 분석했습니다
관리자 API 활성화를 위한 요금제 업그레이드 필요성을 분석했습니다
스크린샷 확인했습니다. Ghost(Pro) 요금제가 제가 알던 것과 달라졌네요.

핵심은 **Publisher 플랜($29/월)**의 "8,000+ integrations" 항목입니다. Starter에는 이게 없고 "Simple design settings"만 있어서 Custom Integration(= Admin API Key)이 차단되고 있는 겁니다.

현실적인 선택지 3가지:

1) Publisher 업그레이드 ($29/월) — 가장 빠른 해결책이지만, 아직 구독자 1명인 상태에서 월 $29는 부담이 클 수 있습니다. 연간 결제하면 2개월 무료라 실질 ~$24/월이긴 합니다. Paid subscriptions 기능도 포함되어 있어서, 1,000명 구독자 도달 후 바로 유료 전환이 가능하다는 장점이 있습니다.

2) Self-hosted Ghost (월 $4-6) — 비용 대비 가장 효율적입니다. Ghost 오픈소스를 직접 서버에 설치하면 Admin API 제한이 전혀 없고, 테마 커스텀, integration 전부 무제한입니다. DigitalOcean Droplet($6/월)이나 Railway, Render 같은 플랫폼에 배포할 수 있습니다. 다만 서버 관리(업데이트, 백업, SSL)를 직접 해야 하고, 이메일 발송은 Mailgun 같은 별도 서비스를 연결해야 합니다.

3) Ghost 대신 다른 플랫폼으로 전환 — Beehiiv, Substack, Buttondown 같은 뉴스레터 전문 플랫폼은 무료 플랜에서도 API를 제공합니다. 다만 지금까지 Ghost에 투자한 테마 커스텀 작업을 다시 해야 한다는 단점이 있습니다.

Jiho 님의 상황(아직 수익화 전, 자동화 파이프라인이 핵심)을 고려하면, Self-hosted Ghost가 가장 합리적이라고 봅니다. 초기 설정만 해놓으면 이후 비용도 낮고 API 제한도 없습니다. 원하시면 DigitalOcean에 Ghost 설치하는 전체 과정을 안내해드릴 수 있습니다. 어떤 방향으로 가실 건가요?

1775165533847_image.png
Publisher 업그레이드 ($29/월) 으로 업그레이드 했습니다 이제 문제 없는걸까요?

4월 3일

업그레이드 확인 후 남은 문제점 검토했습니다
업그레이드 확인 후 남은 문제점 검토했습니다
Publisher 플랜으로 업그레이드하셨으니 이제 핵심 문제가 해결됩니다.

**"8,000+ integrations"**가 포함되어 있어서 Custom Integration(Admin API Key)이 활성화됩니다. 즉, Ghost 403 에러가 더 이상 발생하지 않을 겁니다.

이제 GitHub Actions에서 다시 실행해보시면 됩니다. 확인해야 할 체크포인트는 세 가지입니다:

퍼블리시 — GHOST 403 대신 OK!가 나와야 합니다.

이미지 업로드 — img upload 403 대신 이미지 URL이 반환되어야 합니다. (Imagen은 여전히 404일 수 있지만, picsum 이미지라도 Ghost에 정상 업로드될 겁니다.)

Dedup — Dedup fetch status: 403이 Loaded N recent titles로 바뀌어야 합니다.

한번 실행해보시고 로그 결과 공유해주시면 나머지 상태도 확인해드리겠습니다.

Run python main.py
==================================================
  Warm Insight v10 (4-Issue Fix)
==================================================
  UTC 21 -> Economy (daily seed: 20260402, order: ['Health', 'Economy', 'Politics', 'Tech', 'Energy'])
  Loaded 50 recent titles
--- [Economy] ---
  [🌱 Free] 3 articles...
    [AI] gemini-2.5-flash
  Imagen-lib: generate_images not available, trying REST...
  Imagen-REST(1): 404 {
  "error": {
    "code": 404,
    "message": "models/imagen-3.0-generate-001 is not found for API
  Picsum fallback OK (seed: 26669)
  Pub: [🌱 Free] Private Credit AI Disruption: A Canary in the Tech
  OK! (attempt 1)
  Wait 144s (base+129 random)
  [💎 Pro] 3 articles...
    [AI] gemini-2.5-pro
    EDITOR REJECTED: 1.  **Fabricated events:** The newsletter attributes specific involvement to Sandisk that is not supported by the news. It states that "the tech side (Visa, Sandisk) is quietly in the corner building
    Retry after editor reject...
    [AI] gemini-2.5-pro
    Editor: PASS
  Imagen-lib: generate_images not available, trying REST...
  Imagen-REST(1): 404 {
  "error": {
    "code": 404,
    "message": "models/imagen-3.0-generate-001 is not found for API
  Picsum fallback OK (seed: 26669)
  Pub: [💎 Pro] AI in Financial Services: A Micro Signal for a Macro
  OK! (attempt 1)
  Wait 139s (base+109 random)
  [👑 VIP] 5 articles...
    [AI] gemini-2.5-pro
    Part 2...
    [AI] gemini-2.5-pro
    EDITOR REJECTED:
    Retry after editor reject...
    [AI] gemini-2.5-pro
    Part 2...
    [AI] gemini-2.5-pro
    Editor: PASS
  Imagen-lib: generate_images not available, trying REST...
  Imagen-REST(1): 404 {
  "error": {
    "code": 404,
    "message": "models/imagen-3.0-generate-001 is not found for API
  Imagen-REST(2): 404 {
  "error": {
    "code": 404,
    "message": "models/imagen-3.0-generate-001 is not found for API
  Imagen-REST(3): 404 {
  "error": {
    "code": 404,
    "message": "models/imagen-3.0-generate-001 is not found for API
  Picsum fallback OK (seed: 26669)
  Pub: [👑 VIP] The Oracle's Warning: Navigating the Global Risk Lan
  OK! (attempt 1)
  Wait 114s (base+64 random)
==================================================
  Economy | Total 3 | OK 3 | Fail 0
==================================================

해당 코드 보시고 잘 뉴스레터가 발행 된게 맞는지 확인 부탁드립니다

더 보기
4월 3일

뉴스레터 발행 성공 여부를 로그로 검증했습니다
뉴스레터 발행 성공 여부를 로그로 검증했습니다
완벽합니다! 3/3 전부 성공했습니다.

퍼블리시 ✅ — Free, Pro, VIP 모두 OK! (attempt 1)로 첫 시도에 발행 성공. Ghost 403 완전 해결.

Dedup ✅ — Loaded 50 recent titles로 기존 글 목록 정상 로드.

랜덤 로테이션 ✅ — UTC 21시에 Economy가 선택되었고, 이전 UTC 19시에는 Energy였으므로 일자별 셔플이 정상 작동.

VIP P2 ✅ — Part 2가 재시도 없이 한 번에 성공. v9에서 P2 retry 2회 + Fallback + REJECTED x2였던 것과 비교하면 큰 개선.

Editor ✅ — Pro는 첫 시도에서 Sandisk 관련 거짓 인용으로 reject됐지만, 재생성 후 PASS. VIP도 마찬가지로 재시도 후 PASS. Editor가 제 역할을 하고 있다는 뜻입니다.

남은 개선 포인트 하나만 참고하시면:

Imagen이 계속 404를 반환하고 있어서 모든 썸네일이 picsum 랜덤 사진입니다. 그리고 seed가 26669로 세 글 모두 동일한데, 이건 같은 시간대(Economy + 같은 hour)라서 그렇습니다. 이 부분은 급하지 않지만, Imagen을 쓰고 싶으시면 Google AI Studio에서 Imagen API 활성화 여부를 확인해보시면 됩니다. 혹은 tier별로 seed를 다르게 해서 최소한 Free/Pro/VIP 썸네일이 다르게 나오도록 수정할 수도 있습니다. 필요하시면 말씀해주세요!

tier별로 seed를 다르게 해서 최소한 Free/Pro/VIP 썸네일이 다르게 나오도록 수정할 수도 있습니다. <<해당 내용 해주세요
그리고 뉴스레터 한번 생성하는데(카테고리 1개 뉴스레터3개) 비용이 2000원발생하는데 이런식으로 되면 하루에 26000원 한달 78만원이나 구글 API 비용이 발생합니다<< 해당 비용 줄이는 방법 알려주세요

4월 3일

비용 절감 방안과 크론 스케줄 최적화를 분석했습니다
비용 절감 방안과 크론 스케줄 최적화를 분석했습니다
두 가지 모두 수정하겠습니다. 특히 비용 절감은 여러 레벨에서 동시에 적용합니다.

Warm Insight v10 — 4-Issue Fix
코드 ∙ 버전 2 
이제 비용 절감 관련 수정을 적용합니다.

Warm Insight v10 — 4-Issue Fix
코드 ∙ 버전 3 
VIP Part 2에 flash 모델을 적용합니다.

Warm Insight v10 — 4-Issue Fix
코드 ∙ 버전 4 
P2 재시도 로직도 flash 모델로 맞춥니다.

Warm Insight v10 — 4-Issue Fix
코드 ∙ 버전 5 
Editor 호출도 비용 모드에 맞게 수정합니다.

Warm Insight v10 — 4-Issue Fix
코드 ∙ 버전 6 
로그에 비용 모드가 표시되도록 합니다.

Warm Insight v10 — 4-Issue Fix
코드 ∙ 버전 7 
좋습니다. 이제 비용 절감 효과를 정리해드리겠습니다.

수정 1: 썸네일 seed — 이제 cat + tier + 시간으로 seed를 만들어서 Free/Pro/VIP가 각각 다른 picsum 이미지를 사용합니다.

수정 2: 비용 절감 — 3단계 구조

COST_MODE 환경변수로 제어합니다. GitHub Actions의 env에 추가하면 됩니다.

모드	1회 비용(추정)	변경 내용
full (v9 원본)	~2,000원	Pro+VIP 모두 gemini-pro 사용
balanced (기본값)	~800원	Pro→flash, VIP P2→flash, Basic editor 스킵
low	~300원	전부 flash, editor는 VIP만
핵심 절감 포인트는 세 가지입니다:

VIP Part 2(전략 섹션)를 flash로 변경했습니다. P1(분석)은 pro 품질이 중요하지만, P2(ETF 추천, DCA 조언)는 flash로도 충분합니다. 이것만으로 VIP 비용이 ~40% 줄어듭니다.

Premium 티어도 flash로 변경했습니다. Pro 분석은 VIP와 차별화되어야 하지만 flash의 품질도 꽤 좋으므로, balanced 모드에서는 flash를 사용합니다.

Basic 티어는 editor 리뷰를 스킵합니다. Free 콘텐츠에 editor 호출은 비용 낭비입니다.

추가로, cron 주기를 변경하면 가장 큰 절감 효과가 있습니다. GitHub Actions의 main.yml에서:

yaml
# 현재: 매시간 (24회/일)
- cron: '0 * * * *'

# 권장: 3시간마다 (8회/일) — 비용 67% 절감
- cron: '0 */3 * * *'
월별 예상 비용 비교:

매시간(24회)	3시간(8회)
full	~144만원	~48만원
balanced	~58만원	~19만원
low	~22만원	~7만원
가장 추천하는 조합: balanced + 3시간 주기 = 월 ~19만원 (기존 78만원 대비 75% 절감)

GitHub Actions env에 COST_MODE: balanced를 추가하고, cron을 0 */3 * * *로 바꾸시면 됩니다. 하루 8회면 5개 카테고리가 골고루 커버됩니다.

베이직 버전을 없애고 프리미엄과로얄프리미엄만 남기는 버전은 어때 low 버전에 하루 8회 구동 되는 버전으로 하면 비용은 얼마 정도 나올 것 같나요?

4월 3일

계산했던 비용 구조와 월간 예상 지출을 추정했다
계산했던 비용 구조와 월간 예상 지출을 추정했다
좋은 판단입니다. 계산해보면:

2티어 + low + 8회/일 비용 추정:

호출 내역	비용/회
Premium	flash 1회	~50원
VIP	flash 3회 (P1+P2+editor)	~150원
합계	4 flash calls	~200원
하루: 200원 × 8회 = ~1,600원 월: 1,600원 × 30일 = ~4.8만원

현재 78만원 대비 94% 절감입니다.

이 방향으로 코드를 수정할까요? 변경 사항은:

TASKS에서 Basic 제거
뉴스 배분을 Premium 5개 / VIP 5개로 조정 (기존 3/3/5에서 Basic 분량 재배분)
low 모드를 기본값으로 설정
cron을 0 */3 * * *로 변경 권장
진행할까요?

뉴스 배분을 Premium 5개 / VIP 5개로 조정 (기존 3/3/5에서 Basic 분량 재배분) << 해당 내용은 무슨 뜻인가요??
그리고 3시간마다 1개 카테고리(프리미엄,로얄프리미엄) 발행 > 다른 카테고리 1개 발행 이런식은 그대로 인거죠?

4월 3일

뉴스 배분 개념을 설명하고 회전 패턴 확인했습니다
뉴스 배분 개념을 설명하고 회전 패턴 확인했습니다
뉴스 배분 설명:

RSS에서 뉴스 20개를 가져온 뒤, 각 티어에 몇 개씩 나눠주는 겁니다. 현재는 이렇습니다:

Basic → 뉴스 3개를 받아서 → 그걸 기반으로 분석 글 1개 생성
Premium → 뉴스 3개 → 분석 글 1개
VIP → 뉴스 5개 → 분석 글 1개
Basic을 없애면 그 뉴스 3개가 남으니까, Premium에 더 줘서 분석 소스를 풍부하게 할 수 있다는 뜻이었습니다. 예: Premium 5개, VIP 5개. 하지만 기존대로 Premium 3개, VIP 5개로 유지해도 전혀 문제없습니다. 원하시는 대로 정해주세요.

로테이션은 그대로 맞습니다:

3시간마다 → 카테고리 1개 선택 → 그 카테고리로 Premium 1개 + VIP 1개 발행 → 다음 3시간 후 → 다른 카테고리 선택 → 반복

하루 8회니까 5개 카테고리가 골고루 돌아갑니다.

Premium/VIP 뉴스 개수를 어떻게 할지 정해주시면 바로 코드 수정 들어가겠습니다.

1000077513.jpg
예: Premium 5개, VIP 5개 뉴스 분배 분석글 1개
3시간마다 → 카테고리 1개 선택 → 그 카테고리로 Premium 1개 + VIP 1개 발행 → 다음 3시간 후 → 다른 카테고리 선택 → 반복
하루 8회니까 5개 카테고리가 골고루 돌아갑니다 
Premium/VIP 뉴스 개수 각각 1개씩 3시간마다 
썸네일 이미지는 같이 전달드린 이미지에서 해당케릭터가 소개하는 느낌으로 심플한 이미지로 만들수 있을까요?

4월 3일

코드 업데이트 후 사용자 요청사항 정리했습니다
코드 업데이트 후 사용자 요청사항 정리했습니다
썸네일은 Imagen이 작동하지 않는 상황이라, 가장 현실적인 방법은 Warmy 캐릭터 이미지를 카테고리별로 미리 만들어서 Ghost에 업로드하고 그 URL을 코드에 넣는 방식입니다. 매번 AI 이미지 생성 비용도 아끼고, 브랜드 일관성도 유지됩니다.

전체 수정 사항을 한번에 반영합니다:

Warm Insight v11 — 2-Tier Cost Optimized
코드 ∙ 버전 8 
코드가 완성되었습니다. 적용하려면 두 가지 작업이 필요합니다.

1) main.yml cron 변경

yaml
# 기존
- cron: '0 * * * *'
# 변경 (3시간마다)
- cron: '0 */3 * * *'
2) Warmy 마스코트 썸네일 10장 준비

코드에 이렇게 URL이 들어 있습니다:

warmy-economy-pro.png    warmy-economy-vip.png
warmy-politics-pro.png   warmy-politics-vip.png
warmy-tech-pro.png       warmy-tech-vip.png
warmy-health-pro.png     warmy-health-vip.png
warmy-energy-pro.png     warmy-energy-vip.png
Ghost 대시보드 → Settings → Design에서 이미지를 업로드하거나, 아무 글에 이미지를 넣어서 URL을 얻은 뒤 WARMY_THUMBS 딕셔너리의 URL을 교체하면 됩니다. 이미지가 준비되기 전에도 WARMY_FALLBACK URL에 기본 이미지 1장만 올려놓으면 작동합니다.

월 비용 예상: ~4.8만원 (기존 78만원 대비 94% 절감)

Warmy 캐릭터 이미지를 제가 디자인 가이드로 만들어드릴 수도 있습니다. 각 카테고리별로 캐릭터가 차트/지구본/DNA 등을 들고 있는 느낌으로요. 필요하시면 말씀해주세요!

각 카테고리 별로 캐릭터 만들어주세요

4월 3일

각 카테고리별 캐릭터 디자인을 구성했습니다
각 카테고리별 캐릭터 디자인을 구성했습니다
Warmy Mascot Thumbnails — All Categories
대화형 아티팩트 
5개 카테고리 × Pro/VIP = 총 10장의 Warmy 썸네일이 만들어졌습니다. 각 캐릭터는 카테고리별 아이템을 들고 있습니다:

Economy → 차트 📈
Politics → 지구본 🌍
Tech → 반도체 칩 💻
Health → DNA 이중나선 🧬
Energy → 번개 ⚡
VIP 버전에는 왕관이 추가되어 있습니다.

사용 방법:

각 이미지를 클릭하면 PNG로 다운로드됩니다
Ghost Admin에서 이미지를 업로드하고 URL을 복사
main.py의 WARMY_THUMBS 딕셔너리에 실제 URL로 교체
디자인 스타일이 마음에 드시나요? 색상이나 포즈, 아이템 등 수정하고 싶은 부분이 있으면 말씀해주세요.

각 이미지 클릭했는데 다운로드가 안되는데요??

오전 12:51

다운로드 문제를 진단하고 해결책을 모색했습니다
다운로드 문제를 진단하고 해결책을 모색했습니다
SVG 안에 이모지가 포함되어 있어서 btoa 인코딩이 실패하는 문제입니다. 이모지를 텍스트 라벨로 교체하고 다운로드 방식을 수정합니다.

Warmy Mascot Thumbnails — All Categories
대화형 아티팩트 ∙ 버전 2 
다운로드 방식을 수정했습니다. 이제 이모지 대신 텍스트만 사용하고, Blob URL 방식으로 변환합니다.

만약 여전히 다운로드가 안 된다면 Claude 아티팩트 샌드박스의 제한일 수 있습니다. 그 경우 대안으로, 각 이미지를 우클릭 → 이미지를 다른 이름으로 저장을 시도해보세요. 그래도 안 되면 말씀해주시면 별도 HTML 파일로 만들어서 로컬에서 다운로드할 수 있게 해드리겠습니다.

다운로드 된거 같은데 어디 폴더에 저장이 된건가요?

오전 12:55

파일 저장 위치를 기기 설정에 따라 추론했습니다
파일 저장 위치를 기기 설정에 따라 추론했습니다
브라우저 기본 다운로드 폴더에 저장됩니다.

PC(Windows)라면: C:\Users\사용자이름\Downloads 폴더에 warmy-economy-pro.png 같은 파일명으로 저장되어 있을 겁니다. 키보드에서 Ctrl + J를 누르면 브라우저 다운로드 목록에서 바로 확인할 수 있습니다.

모바일(Android)이라면: 파일 관리자 앱 → Downloads 폴더에 있습니다.

10장 모두 다운로드하셨으면, Ghost에 업로드하고 URL을 코드에 넣는 단계로 넘어가시면 됩니다. 확인되셨나요?

1775231786106_image.png
다운로드가 안된거 같아요

오전 12:56

이미지 다운로드 방식을 재구성했습니다
이미지 다운로드 방식을 재구성했습니다
아티팩트 샌드박스에서 자동 다운로드가 차단된 것 같습니다. 방식을 바꿔서, 이미지를 직접 보여드리고 우클릭 → 이미지를 다른 이름으로 저장할 수 있게 만들겠습니다.

Warmy Thumbnails — Right-click to Save
대화형 아티팩트 ∙ 버전 3 
이제 각 이미지가 실제 PNG로 렌더링됩니다. 저장 방법은:

PC: 이미지 위에서 우클릭 → 이미지를 다른 이름으로 저장 (파일명은 아래에 표시된 대로 warmy-economy-pro.png 등으로 저장하세요)

모바일: 이미지를 길게 터치 → 이미지 저장

이 방식은 브라우저 다운로드 차단과 무관하게 작동합니다. 한번 시도해보세요!

생성된 아티팩트를 실행하는 중 오류가 발생했습니다.
Unexpected token (45:3)

  Can you fix this error in warmy-thumbs?

오전 12:58

코드 호환성 개선하고 렌더링 순차 처리로 경합 조건 해결했습니다
코드 호환성 개선하고 렌더링 순차 처리로 경합 조건 해결했습니다
Warmy Thumbnails — Right-click to Save
대화형 아티팩트 ∙ 버전 4 
Template literal 문법을 모두 제거하고 순수 문자열 결합 방식으로 변환했습니다. 이제 에러 없이 10장의 이미지가 표시될 겁니다. 각 이미지를 우클릭 → 이미지를 다른 이름으로 저장해서 다운로드하세요.

생성된 아티팩트를 실행하는 중 오류가 발생했습니다.
Unexpected token, expected ";" (13:11)

  Can you fix this error in warmy-thumbs?

오전 12:59

React 아티팩트를 SVG에서 PNG로 변환하여 수정했다
React 아티팩트를 SVG에서 PNG로 변환하여 수정했다
HTML 아티팩트 파서 문제인 것 같습니다. React 컴포넌트로 전환하겠습니다.

Warmy Thumbnails — Right-click to Save
대화형 아티팩트 ∙ 버전 5 
React 컴포넌트로 완전히 재작성했습니다. 이제 각 이미지가 PNG로 렌더링되어 표시됩니다. 우클릭 → 이미지를 다른 이름으로 저장으로 다운로드해주세요.

1775232504653_image.png
이미지 10개 다 다운로드 받아서 Ghost Admin - any post했는데 지금 전달드린 사진처럼 변해버리는데 어떻게 된걸까요?

오전 1:08

필터 속성 제거로 렌더링 문제 해결했습니다
필터 속성 제거로 렌더링 문제 해결했습니다
문제를 찾았습니다. SVG의 filter="url(#sh...)" (그림자 효과)가 캔버스 렌더링에서 지원되지 않아서 Warmy 캐릭터가 통째로 사라진 겁니다. 필터를 제거하고 다시 만들겠습니다.

Warmy Thumbnails v2 — No Filter
대화형 아티팩트 ∙ 버전 6 
핵심 수정: feDropShadow 필터를 완전히 제거했습니다. 이 필터가 캔버스에서 지원되지 않아서 캐릭터 전체(<g filter="..."> 안의 모든 것)가 렌더링되지 않았던 겁니다.

이제 Warmy 캐릭터가 제대로 보이는지 확인해주세요. 보이면 다시 10장 저장해서 Ghost에 업로드하시면 됩니다.

Ghost에 업로드할때 완전 저장이 아니고 이미지 주소만 드리면 되나요?

오전 1:12

이미지 URL 획득 프로세스를 명확히 설명했습니다
이미지 URL 획득 프로세스를 명확히 설명했습니다
이미지를 Ghost 서버에 실제로 업로드해야 합니다. URL만으로는 안 됩니다. 과정은 이렇습니다:

1단계: 아티팩트에서 이미지 10장을 PC에 저장 (우클릭 → 이미지를 다른 이름으로 저장)

2단계: Ghost Admin → Posts → New post → 본문에 이미지 삽입(+버튼 → Image) → PC에 저장한 파일 업로드

3단계: 업로드된 이미지를 우클릭 → 이미지 주소 복사 → 이런 형태의 URL을 얻게 됩니다: https://www.warminsight.com/content/images/2026/04/warmy-economy-pro.png

4단계: 이 URL을 main.py의 WARMY_THUMBS에 붙여넣기

5단계: 그 draft 글은 삭제해도 됩니다. 이미지는 Ghost 서버의 /content/images/ 폴더에 남아있어서 URL이 계속 작동합니다.

즉, Ghost를 이미지 호스팅 용도로 사용하는 겁니다. 글을 발행할 필요는 없고, 이미지만 올려서 URL을 얻으면 됩니다.

ecnomy-pro 이미지 주소인데 이렇게 하면 맞나요?

https://www.warminsight.com/content/images/2026/04/economy-pro-4.svg

오전 1:18

SVG 형식 확인 및 PNG 변환 권장 검토했습니다
SVG 형식 확인 및 PNG 변환 권장 검토했습니다
URL 형태는 맞지만, 파일이 .svg로 저장된 게 조금 걱정됩니다. SVG는 이메일 클라이언트나 일부 브라우저에서 썸네일로 제대로 안 보일 수 있어서 PNG가 더 안전합니다.

확인 방법: 브라우저에서 그 URL을 직접 열어보세요. Warmy 캐릭터가 정상적으로 보이면 SVG로도 괜찮습니다.

만약 캐릭터가 안 보이면, 아티팩트에서 이미지를 저장할 때 파일 형식을 PNG로 선택해주세요. 우클릭 → 이미지를 다른 이름으로 저장 → 하단의 "파일 형식"에서 PNG (*.png)를 선택하면 됩니다.

나머지 9장도 같은 방식으로 진행하신 뒤, 10개 URL을 모아서 공유해주시면 제가 main.py의 WARMY_THUMBS에 한번에 넣어드리겠습니다.

https://www.warminsight.com/content/images/2026/04/economy-pro.png
https://www.warminsight.com/content/images/2026/04/economy-vip.png
https://www.warminsight.com/content/images/2026/04/energy-pro.png
https://www.warminsight.com/content/images/2026/04/energy-vip.png
https://www.warminsight.com/content/images/2026/04/health-pro.png
https://www.warminsight.com/content/images/2026/04/health-vip.png
https://www.warminsight.com/content/images/2026/04/politics-pro.png
https://www.warminsight.com/content/images/2026/04/politics-vip.png
https://www.warminsight.com/content/images/2026/04/tech-pro.png
https://www.warminsight.com/content/images/2026/04/tech-vip.png

지금 전달드린 각 카테고리별 이미지 주소 인데 맞는지 확인해주시고 맞다면

WARMY_THUMBS 여기에 해당 주소 넣어서 다시 코드 전달 해주시고요
이렇게 까지하면 썸네일 이미지에 지금 한 카테고리별 이미지에 추가로 제목에 맞는 이미지도 같이 들어가는건가요?

더 보기
오전 1:34

URLs 검증 후 스케줄 간격 조정 권장했습니다
URLs 검증 후 스케줄 간격 조정 권장했습니다
URL 10개 모두 정확합니다. 5개 카테고리 × Pro/VIP = 10장 완벽하게 맞습니다.

제목에 맞는 이미지 관련 답변: 아닙니다. 이 썸네일은 카테고리+티어별 고정 이미지입니다. 예를 들어 Economy Pro 글은 제목이 뭐든 항상 같은 Warmy Economy Pro 이미지가 들어갑니다. 제목별로 다른 이미지를 넣으려면 Imagen 같은 AI 이미지 생성이 필요한데, 현재 작동하지 않고 비용도 추가되기 때문에 제외한 겁니다. 브랜드 일관성 측면에서는 오히려 고정 마스코트가 더 좋습니다. Morning Brew나 Milk Road도 이 방식을 씁니다.

코드에 URL을 반영합니다:

Warm Insight v10 — 4-Issue Fix
코드 ∙ 버전 9 
URL 반영 완료입니다. 이제 해야 할 것은 두 가지입니다:

1) main.py → 아티팩트의 코드를 GitHub repo에 업로드

2) main.yml → cron을 3시간으로 변경:

yaml
- cron: '0 */3 * * *'
이걸로 전체 세팅이 끝납니다. 실행하면 이런 흐름이 됩니다:

3시간마다 → 카테고리 1개 자동 선택 → Pro 글 1개 + VIP 글 1개 발행 → Pro는 Warmy Pro 썸네일, VIP는 Warmy VIP 썸네일(왕관 버전) 자동 적용 → 월 ~4.8만원

GitHub에 코드 올리시고 한번 실행해보신 뒤 로그 공유해주시면 최종 확인해드리겠습니다.

1775234403221_image.png
지금 전달드린 사진 분석해서 확인해보시면 캐릭터는 기본으로 들어가고 해당 뉴스레터에 맞게 이미티콘 이미지와 글씨가 들어간 썸네일 이미지가 만들어서 업로드 되고 있습니다
우리가 전달 드린 이미지처럼 할 수 있을까요?

오전 1:41

썸네일 동적 요소들 분석 중입니다
썸네일 동적 요소들 분석 중입니다

주간 한도 중 75%를 사용했습니다


Claude는 AI이며 실수할 수 있습니다. 응답을 다시 한번 확인해 주세요.
# -*- coding: utf-8 -*-
"""
Warm Insight v11 — 2-Tier Cost Optimized Build
Changes from v10:
  - Basic tier removed (Premium + VIP only)
  - News: 5 per tier
  - Cost mode: low (all flash), ~200원/run
  - Cron: every 3 hours recommended (8 runs/day, ~4.8만원/month)
  - Thumbnails: pre-uploaded Warmy mascot images (no Imagen cost)
  - Imagen removed entirely

Python 3.10 safe.
"""
import os, sys, traceback, time, random, re, json
from datetime import datetime
import requests, jwt, feedparser
from google import genai
from google.genai import types

# ═══════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GHOST_API_URL = os.environ.get("GHOST_API_URL", "").rstrip("/")
GHOST_ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY")
if not all([GEMINI_API_KEY, GHOST_API_URL, GHOST_ADMIN_API_KEY]):
    sys.exit("Missing API keys")

CATEGORIES = {
    "Economy": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "https://finance.yahoo.com/news/rssindex",
        "https://feeds.bbci.co.uk/news/business/economy/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://asia.nikkei.com/rss/feed/nar"],
    "Politics": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000113",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.npr.org/1004/rss.xml"],
    "Tech": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://asia.nikkei.com/rss/feed/nar"],
    "Health": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000108",
        "https://feeds.bbci.co.uk/news/health/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml"],
    "Energy": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000810",
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://asia.nikkei.com/rss/feed/nar"],
}

# ═══════════════════════════════════════════════
# 2-TIER SETUP: Premium + VIP only
# ═══════════════════════════════════════════════
TASKS = [
    {"tier": "Premium", "count": 5},
    {"tier": "Royal Premium", "count": 5},
]
TIER_LABELS = {"Premium": "💎 Pro", "Royal Premium": "👑 VIP"}
TIER_VIS = {"Premium": "public", "Royal Premium": "public"}
TIER_SLEEP = {"Premium": 30, "Royal Premium": 50}

# All flash for cost optimization (~200원/run total)
MODEL_PRI = {
    "Royal Premium": ["gemini-2.5-flash"],
    "Premium": ["gemini-2.5-flash"],
}

# Editor only for VIP (saves 1 flash call per Premium)
SKIP_EDITOR_TIERS = ["Premium"]

EXPERT = {
    "Economy": "a veteran global macro strategist with 40 years spanning Wall Street, City of London, and Asian markets",
    "Politics": "a veteran geopolitical strategist with 40 years covering Washington, Brussels, Beijing, and Middle East",
    "Tech": "a veteran global technology analyst with 40 years covering Silicon Valley, Shenzhen, and emerging hubs",
    "Health": "a veteran global healthcare analyst with 40 years covering US pharma, European biotech, and Asian markets",
    "Energy": "a veteran global energy strategist with 40 years covering OPEC, US shale, European transition, and Asian demand",
}
CAT_THEME = {
    "Economy": {"icon": "💰", "accent": "#2563eb", "label": "MACRO & RATES"},
    "Politics": {"icon": "🏛", "accent": "#dc2626", "label": "GEOPOLITICS"},
    "Tech": {"icon": "🤖", "accent": "#7c3aed", "label": "AI & DISRUPTION"},
    "Health": {"icon": "🧬", "accent": "#059669", "label": "BIOTECH & PHARMA"},
    "Energy": {"icon": "⚡", "accent": "#d97706", "label": "OIL, GAS & RENEWABLES"},
}
CAT_ALLOC = {
    "Economy": {"s": 55, "b": 35, "c": 10, "note": "Defensive: higher bonds during macro uncertainty"},
    "Politics": {"s": 50, "b": 35, "c": 15, "note": "Elevated cash for geopolitical shock absorption"},
    "Tech": {"s": 70, "b": 20, "c": 10, "note": "Growth tilt: overweight innovation equities"},
    "Health": {"s": 60, "b": 30, "c": 10, "note": "Balanced: pharma stability with biotech upside"},
    "Energy": {"s": 65, "b": 25, "c": 10, "note": "Commodity tilt: overweight real assets"},
}
CAT_METRICS = {
    "Economy": {"pool": ["Inflation Momentum", "Recession Risk", "Consumer Pulse", "Credit Stress", "Rate Cut Odds", "Dollar Strength", "Yield Curve", "PMI Signal", "Global Trade Flow", "EM Capital Flight Risk", "G7 vs BRICS Gap"], "hint": "inflation, GDP, Fed policy, global capital flows, bloc divergence"},
    "Politics": {"pool": ["Policy Uncertainty", "Regulatory Risk", "Geopolitical Tension", "Election Volatility", "Trade War Risk", "Sanctions Impact", "Gridlock", "Defense Momentum", "Chokepoint Risk", "Alliance Cohesion"], "hint": "policy, geopolitics, chokepoints, bloc politics, de-dollarization"},
    "Tech": {"pool": ["AI Race Intensity", "Antitrust Pressure", "Chip Supply Stress", "IPO Sentiment", "Cloud Velocity", "Cyber Threat", "Big Tech Momentum", "Funding Freeze", "Tech Decoupling Risk", "Data Sovereignty"], "hint": "AI, semiconductors, regulation, tech decoupling, cyber sovereignty"},
    "Health": {"pool": ["Pipeline Confidence", "Drug Pricing Pressure", "Biotech Funding", "FDA Momentum", "Gene Therapy Index", "Hospital Stress", "Coverage Gap", "Trial Success", "Global Pharma Supply Risk"], "hint": "pharma pipelines, drug pricing, FDA, biotech, global supply chain"},
    "Energy": {"pool": ["Oil Supply Squeeze", "Green Transition", "OPEC Tension", "LNG Surge", "Renewable Growth", "Geo Shock Risk", "Grid Stress", "Carbon Heat", "Chokepoint Disruption", "Energy Independence"], "hint": "oil, OPEC, renewables, LNG, chokepoints, energy security"},
}

# ═══════════════════════════════════════════════
# WARMY MASCOT THUMBNAILS (pre-uploaded to Ghost)
# Replace these URLs after uploading your mascot images
# ═══════════════════════════════════════════════
WARMY_THUMBS = {
    "Premium": {
        "Economy":  "https://www.warminsight.com/content/images/2026/04/economy-pro.png",
        "Politics": "https://www.warminsight.com/content/images/2026/04/politics-pro.png",
        "Tech":     "https://www.warminsight.com/content/images/2026/04/tech-pro.png",
        "Health":   "https://www.warminsight.com/content/images/2026/04/health-pro.png",
        "Energy":   "https://www.warminsight.com/content/images/2026/04/energy-pro.png",
    },
    "Royal Premium": {
        "Economy":  "https://www.warminsight.com/content/images/2026/04/economy-vip.png",
        "Politics": "https://www.warminsight.com/content/images/2026/04/politics-vip.png",
        "Tech":     "https://www.warminsight.com/content/images/2026/04/tech-vip.png",
        "Health":   "https://www.warminsight.com/content/images/2026/04/health-vip.png",
        "Energy":   "https://www.warminsight.com/content/images/2026/04/energy-vip.png",
    },
}
# Fallback: Economy Pro image as default
WARMY_FALLBACK = "https://www.warminsight.com/content/images/2026/04/economy-pro.png"

# ═══════════════════════════════════════════════
# RULES
# ═══════════════════════════════════════════════
ACCURACY = (
    "STRICT ACCURACY RULES (NEVER VIOLATE):\n"
    "- ONLY analyze facts from the news provided. NEVER invent events, names, or incidents.\n"
    "- NEVER fabricate specific prices, RSI numbers, or statistics. Use directional language.\n"
    "- NEVER attribute causation unless the news explicitly states it. Say 'coincides with' not 'caused by'.\n"
    "- NEVER claim a company action was driven by a macro trend unless the news says so.\n"
    "- Use hedging: likely, suggests, indicates. Not definitive false claims.\n"
    "- Reference only real ETF tickers (SPY, XLE, XLV, IEF, GLD, EFA, VWO, etc).\n\n"
    "GEOPOLITICAL FRAMEWORK:\n"
    "- Analyze through MULTIPLE perspectives: US, Europe, China, Global South.\n"
    "- Consider chokepoints (Hormuz, Suez, Malacca, Taiwan Strait) as systemic risk.\n"
    "- Track G7 vs BRICS+ bloc divergence.\n"
    "- Map cascades: geopolitical event -> energy -> inflation -> central bank -> markets.\n"
    "- Consider Tech Decoupling, De-dollarization, Nearshoring as mega-trends.\n\n"
    "TONE RULES:\n"
    "- Write like a respected senior analyst at Goldman Sachs or Bridgewater.\n"
    "- Smart humor like Morning Brew or Matt Levine. NOT TikTok slang.\n"
    "- No: fam, slay, lit, no cap, we are cooked, its giving. Ever.\n"
    "- Every sentence must sound human-written, not AI-generated.\n"
    "- Be specific and data-driven. Vague cheerleading destroys credibility.\n"
)

# ═══════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════
PROMPT_PREMIUM = (
    "You are [PERSONA] for Warm Insight ([CATEGORY]).\n"
    "Audience: Intermediate investors wanting deeper why.\n"
    "[ACCURACY]\n"
    "STYLE: Second-Order Thinking. G7 vs BRICS+ lens. 700-900 words.\n\n"
    "OUTPUT (XML):\n"
    "<SEO_KEYWORD>4-7 word keyword</SEO_KEYWORD>\n"
    "<TITLE>Analytical title with SEO keyword</TITLE>\n"
    "<EXCERPT>1 sentence with SEO keyword</EXCERPT>\n"
    "<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>\n"
    "<SUMMARY>3 sentences. First includes SEO keyword.</SUMMARY>\n"
    "<TIKTOK>Smart witty analogy. Matt Levine meets Morning Brew. 3-4 sentences.</TIKTOK>\n"
    "<HEADLINE>Analytical headline</HEADLINE>\n"
    "<KEY_NUMBER>Most striking statistic</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>1 sentence why this changes the picture</KEY_NUMBER_CONTEXT>\n"
    "<DEPTH><strong>🧐 WHY:</strong> Deeper structural pattern. 5-6 sentences."
    "<br><br><strong>🐑 HERD TRAP:</strong> Cognitive bias making investors wrong. 4-5 sentences.</DEPTH>\n"
    '<FLOW>TEXT + emoji (5+ steps)</FLOW>\n'
    "<PRO_INSIGHT>Cross-sector connection via Second-Order Thinking. 5-6 sentences.</PRO_INSIGHT>\n"
    "<COMPARE_BULL>Bull case: 2-3 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case: 2-3 sentences.</COMPARE_BEAR>\n"
    "<PRO_DO>2 actions with reasoning</PRO_DO>\n"
    "<PRO_DONT>1 mistake with reasoning</PRO_DONT>\n"
    "<QUICK_HITS>3 headlines. 1 sentence each. 3 lines.</QUICK_HITS>\n"
    "<TAKEAWAY>Insightful takeaway</TAKEAWAY>\n"
    "<PS>Historical perspective (2-3 sentences)</PS>\n\n"
    "News: [NEWS_ITEMS]"
)

VIP_P1 = (
    "You are [PERSONA] for Warm Insight VIP ([CATEGORY]).\n"
    "Audience: Sophisticated investors paying premium.\n"
    "[ACCURACY]\n"
    "MULTI-PERSPECTIVE: US, Europe, China/Asia, Global South.\n"
    "Map cascade: geopolitical -> energy -> inflation -> central bank -> markets.\n"
    "G7 vs BRICS+ divergence. Nearshoring, tech decoupling, de-dollarization.\n\n"
    "WRITE real analysis:\n\n"
    "<SEO_KEYWORD>4-8 word keyword</SEO_KEYWORD>\n"
    "<TITLE>Institutional title with SEO keyword</TITLE>\n"
    "<EXCERPT>1 VIP sentence with SEO keyword</EXCERPT>\n"
    "<IMPACT>HIGH, MEDIUM, or LOW</IMPACT>\n"
    "<KEY_NUMBER>Critical number</KEY_NUMBER>\n"
    "<KEY_NUMBER_CONTEXT>Why institutions watch this</KEY_NUMBER_CONTEXT>\n"
    "<SENTIMENT>0-100 Fear-Greed. Just the number.</SENTIMENT>\n"
    "<SUMMARY>3 institutional sentences. First includes SEO keyword.</SUMMARY>\n"
    "<TIKTOK>Sharp sophisticated analogy. Bridgewater meets Bloomberg. 3-4 sentences.</TIKTOK>\n"
    "<HEADLINE>Alpha headline</HEADLINE>\n"
    "<DEPTH><strong>🧐 MACRO:</strong> Systems view. Structural forces. 5+ sentences."
    "<br><br><strong>🐑 HERD:</strong> Cognitive bias. 4+ sentences."
    "<br><br><strong>🦅 CONTRARIAN:</strong> 1st->2nd->3rd order. G7 vs BRICS+. 5+ sentences.</DEPTH>\n"
    '<FLOW>TEXT + emoji (6+ steps) including global actors</FLOW>\n'
    "<GRAPH_DATA>3 metrics for [CATEGORY]. [CAT_HINT]. Scores differ (25-90). Name1|Score1|Name2|Score2|Name3|Score3</GRAPH_DATA>\n"
    "<VIP_RADAR_1>Sector - BULLISH or BEARISH - why</VIP_RADAR_1>\n"
    "<VIP_RADAR_2>Sector - BULLISH or BEARISH - why</VIP_RADAR_2>\n"
    "<VIP_RADAR_3>Sector - BULLISH or BEARISH - why</VIP_RADAR_3>\n"
    "<VIP_RADAR_4>Sector - BULLISH or BEARISH - why</VIP_RADAR_4>\n"
    "<VIP_C1>Technical: sector ETF trends. 5+ sentences.</VIP_C1>\n"
    "<VIP_C2>Macro: yields, credit, dollar, global flows. 5+ sentences.</VIP_C2>\n"
    "<VIP_C3>Smart Money: US, EU, Asia institutions. 5+ sentences.</VIP_C3>\n"
    "<MARKET_SNAP>S&P 500|DIRECTION|reason\n10Y Yield|DIRECTION|reason\nUS Dollar|DIRECTION|reason\nOil WTI|DIRECTION|reason</MARKET_SNAP>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

VIP_P2 = (
    "You are [PERSONA] writing Part 2 for Warm Insight VIP ([CATEGORY]).\n"
    "[ACCURACY]\n"
    "CRITICAL: Write REAL analysis paragraphs. Do NOT echo instructions back.\n"
    "Do NOT repeat tag names or word counts in your output.\n\n"
    "Context from Part 1:\n[CTX]\n\n"
    "Now write the strategy section. Each tag must contain REAL sentences, not placeholders.\n\n"
    "<VIP_T1>What is the current fear vs greed balance globally? Reference Buffett or Templeton if relevant. Write a full paragraph.</VIP_T1>\n"
    "<VIP_T2>Recommended allocation: [ALLOC_STR]. Name real ETFs including at least one international. Write a full paragraph.</VIP_T2>\n"
    "<VIP_T3>Compare US positioning vs Europe, China, and emerging markets. Include supply chain and energy angles. Write a full paragraph.</VIP_T3>\n"
    "<VIP_T4>DCA strategy advice. Include the 50-percent panic rule with specific thresholds. Write a full paragraph.</VIP_T4>\n"
    "<VIP_DO>3 specific actions. Each must name an ETF, a percentage, and a trigger condition. Include at least 1 international ETF.</VIP_DO>\n"
    "<VIP_DONT>2 specific mistakes investors should avoid right now. Explain why each is dangerous.</VIP_DONT>\n"
    "<COMPARE_BULL>Bull case in 2-3 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case in 2-3 sentences.</COMPARE_BEAR>\n"
    "<CONVICTION>HIGH, MEDIUM, or LOW</CONVICTION>\n"
    "<TAKEAWAY>One calming sentence with global perspective.</TAKEAWAY>\n"
    "<PS>A lesson from 40 years of market history. 2-3 sentences.</PS>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

VIP_FB = (
    "You are [PERSONA]. Write a concise VIP strategy for [CATEGORY].\n"
    "[ACCURACY]\n"
    "CRITICAL: Every tag below MUST contain real analysis sentences.\n"
    "Do NOT echo these instructions. Do NOT mention word counts.\n\n"
    "Based on this headline: [CTX_SHORT]\n\n"
    "<VIP_T1>Is the market leaning toward fear or greed globally? Why? (3-4 real sentences)</VIP_T1>\n"
    "<VIP_T2>[ALLOC_STR]. Name 2 domestic ETFs and 1 international ETF with reasoning. (3-4 real sentences)</VIP_T2>\n"
    "<VIP_T3>How does the US compare to Europe or Asia right now? (2-3 real sentences)</VIP_T3>\n"
    "<VIP_T4>What DCA approach makes sense here? (3-4 real sentences)</VIP_T4>\n"
    "<VIP_DO>2 actions: name an ETF and a trigger for each.</VIP_DO>\n"
    "<VIP_DONT>1 mistake to avoid, and why.</VIP_DONT>\n"
    "<COMPARE_BULL>Bull case: 1-2 sentences.</COMPARE_BULL>\n"
    "<COMPARE_BEAR>Bear case: 1-2 sentences.</COMPARE_BEAR>\n"
    "<CONVICTION>HIGH, MEDIUM, or LOW</CONVICTION>\n"
    "<TAKEAWAY>One calming insight.</TAKEAWAY>\n"
    "<PS>Historical parallel in 1-2 sentences.</PS>\n\n"
    "NEWS: [NEWS_ITEMS]"
)

EDITOR_PROMPT = (
    "Senior editorial fact-checker. Review newsletter vs original news.\n"
    "CHECK: 1) Fabricated events 2) Fake stats 3) Invented names 4) False causation\n"
    "IMPORTANT: The newsletter may provide GENERAL market context (e.g. ETF trends, macro conditions).\n"
    "This is acceptable analysis. Only flag causation if the newsletter claims a SPECIFIC news event\n"
    "caused a SPECIFIC company action when the news does NOT say this.\n\n"
    "NEWS:\n[NEWS]\n\nNEWSLETTER:\n[CONTENT]\n\n"
    "<VERDICT>PASS or FAIL</VERDICT>\n"
    "<ISSUES>If FAIL list issues. If PASS write No issues.</ISSUES>"
)

# ═══════════════════════════════════════════════
# GHOST TOKEN + DEDUP + EDITOR
# ═══════════════════════════════════════════════
def gtoken():
    kid, sec = str(GHOST_ADMIN_API_KEY).split(":")
    iat = int(datetime.now().timestamp())
    return jwt.encode({"iat": iat, "exp": iat + 300, "aud": "/admin/"}, bytes.fromhex(sec), algorithm="HS256", headers={"alg": "HS256", "typ": "JWT", "kid": kid})

def get_recent_titles():
    try:
        r = requests.get(
            GHOST_API_URL + "/ghost/api/admin/posts/?limit=50&fields=title&order=published_at%20desc",
            headers={"Authorization": "Ghost " + gtoken()}, timeout=30)
        if r.status_code in (200, 201):
            titles = [p.get("title", "").lower() for p in r.json().get("posts", []) if p.get("title")]
            print("  Loaded " + str(len(titles)) + " recent titles")
            return titles
        else:
            print("  Dedup fetch status: " + str(r.status_code))
    except Exception as e:
        print("  Dedup err: " + str(e))
    return []

def is_duplicate(new_title, recent):
    if not new_title or not recent:
        return False
    labels = ["[💎 pro]", "[👑 vip]"]
    cn = new_title.lower()
    for lb in labels:
        cn = cn.replace(lb, "").strip()
    words_new = set(cn.split())
    if len(words_new) < 4:
        return False
    for rt in recent:
        cr = rt
        for lb in labels:
            cr = cr.replace(lb, "").strip()
        words_rt = set(cr.split())
        if len(words_rt) < 4:
            continue
        overlap = len(words_rt & words_new)
        if overlap / max(len(words_new), 1) > 0.7:
            print("  DEDUP: skip " + str(int(overlap / max(len(words_new), 1) * 100)) + "%")
            return True
    return False

def editor_review(client, news_str, html):
    try:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)[:3000]
        p = EDITOR_PROMPT.replace("[NEWS]", news_str[:2000]).replace("[CONTENT]", text)
        r = call_gem(client, "gemini-2.5-flash", p, retries=1)
        if not r:
            return True, "N/A"
        v = xtag(r, "VERDICT").upper()
        i = xtag(r, "ISSUES")
        if "FAIL" in v:
            print("    EDITOR REJECTED: " + i[:200])
            return False, i
        print("    Editor: PASS")
        return True, i
    except Exception as e:
        return True, str(e)

# ═══════════════════════════════════════════════
# ROTATION: Date-seeded daily shuffle
# ═══════════════════════════════════════════════
def get_current_category():
    cats = list(CATEGORIES.keys())
    now = datetime.utcnow()
    seed = now.year * 10000 + now.month * 100 + now.day
    rng = random.Random(seed)
    shuffled = cats[:]
    rng.shuffle(shuffled)
    idx = now.hour % len(shuffled)
    sel = shuffled[idx]
    print("  UTC " + str(now.hour) + " -> " + sel + " (daily order: " + str(shuffled) + ")")
    return sel

# ═══════════════════════════════════════════════
# UTILS
# ═══════════════════════════════════════════════
def xtag(text, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""

def get_news(urls, count=20):
    news, seen = [], set()
    for url in urls:
        try:
            for e in feedparser.parse(url).entries:
                t = getattr(e, "title", "")
                if t in seen:
                    continue
                seen.add(t)
                news.append("- " + t + ": " + getattr(e, "summary", ""))
                if len(news) >= count:
                    break
        except Exception:
            continue
    return news[:count]

def parse_graph(raw, cat):
    if not raw:
        return _fbg(cat)
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    if len(parts) < 6:
        return _fbg(cat)
    try:
        v1 = int(re.sub(r"[^0-9]", "", parts[1]))
        v2 = int(re.sub(r"[^0-9]", "", parts[3]))
        v3 = int(re.sub(r"[^0-9]", "", parts[5]))
        if v1 == v2 == v3:
            return _fbg(cat)
        return parts[0], max(10, min(95, v1)), parts[2], max(10, min(95, v2)), parts[4], max(10, min(95, v3))
    except Exception:
        return _fbg(cat)

def _fbg(cat):
    pool = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["pool"]
    lb = random.sample(pool, 3)
    return lb[0], random.randint(55, 88), lb[1], random.randint(30, 65), lb[2], random.randint(40, 78)

def is_echo(text):
    if not text or len(text) < 80:
        return True
    sigs = [
        "6+ sentences", "5+ sentences", "At least 5 sentences",
        "Write a detailed", "Write exactly", "Write real", "Write ALL",
        "Name ETFs and trigger", "which ETF to buy",
        "trigger price for each", "explain WHY in detail",
        "Include at least one international",
        "Write a full paragraph for each",
    ]
    matches = sum(1 for s in sigs if s.lower() in text.lower())
    if matches >= 3:
        print("    echo detected (" + str(matches) + " sigs)")
        return True
    return False

def ok_tag(raw, tag):
    v = xtag(raw, tag)
    return "" if not v or is_echo(v) else v

def sanitize(h):
    return re.sub(r"\s+", " ", h.replace("\n", " ").replace("\r", ""))

def make_slug(kw, title):
    t = kw if kw else title
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", t.lower())
    return re.sub(r"\s+", "-", s.strip())[:80]

# ═══════════════════════════════════════════════
# THUMBNAIL: Pre-uploaded Warmy mascot images
# ═══════════════════════════════════════════════
def get_thumb_url(tier, cat):
    """Return pre-uploaded Warmy mascot URL. No API calls needed."""
    url = WARMY_THUMBS.get(tier, {}).get(cat, WARMY_FALLBACK)
    print("  Thumb: " + url.split("/")[-1])
    return url

# ═══════════════════════════════════════════════
# GHOST API
# ═══════════════════════════════════════════════
def publish(title, html, cat, tier, feature_img_url, exc, kw="", slug=""):
    print("  Pub: " + title[:60])
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            token = gtoken()
            md = json.dumps({
                "version": "0.3.1", "markups": [], "atoms": [],
                "cards": [["html", {"html": html}]],
                "sections": [[10, 0]]
            })
            p = {
                "title": title, "mobiledoc": md,
                "status": "published",
                "visibility": TIER_VIS.get(tier, "public"),
                "tags": [{"name": cat}, {"name": tier}]
            }
            if slug:
                p["slug"] = slug
            if kw:
                mt = title + " | Warm Insight " + cat
                p["meta_title"] = mt[:300]
                p["meta_description"] = (exc[:140] + " Expert " + cat.lower() + " analysis.")[:500]
                p["og_title"] = mt[:300]
                p["og_description"] = exc[:300]
            if exc:
                p["custom_excerpt"] = exc[:290]
            if feature_img_url:
                p["feature_image"] = feature_img_url
                if kw:
                    p["feature_image_alt"] = kw + " - Warm Insight " + cat

            r = requests.post(
                GHOST_API_URL + "/ghost/api/admin/posts/",
                json={"posts": [p]},
                headers={"Authorization": "Ghost " + token, "Content-Type": "application/json"},
                timeout=60)
            if r.status_code in (200, 201):
                print("  OK! (attempt " + str(attempt) + ")")
                return True
            elif r.status_code == 403:
                print("  GHOST 403 attempt " + str(attempt) + "/" + str(max_retries) + ": " + r.text[:200])
                if attempt < max_retries:
                    time.sleep(10 * attempt)
                    continue
                return False
            elif r.status_code == 429:
                time.sleep(30 * attempt)
                continue
            else:
                print("  GHOST FAIL " + str(r.status_code) + ": " + r.text[:200])
                return False
        except Exception as e:
            print("  GHOST ERR: " + str(e))
            if attempt < max_retries:
                time.sleep(5 * attempt)
    return False

# ═══════════════════════════════════════════════
# GEMINI
# ═══════════════════════════════════════════════
def call_gem(client, model, prompt, retries=2):
    for i in range(1, retries + 1):
        try:
            r = client.models.generate_content(model=model, contents=prompt)
            return str(r.text)
        except Exception as e:
            err_str = str(e)
            print("    Gem(" + model + ")" + str(i) + ": " + err_str[:150])
            if "503" in err_str or "UNAVAILABLE" in err_str:
                time.sleep(15 * i)
            elif i < retries:
                time.sleep(10 * i)
    return None

def gem_fb(client, tier, prompt):
    for m in MODEL_PRI.get(tier, ["gemini-2.5-flash"]):
        print("    [AI] " + m)
        r = call_gem(client, m, prompt)
        if r:
            return r, m
    return None, None

# ═══════════════════════════════════════════════
# ANALYZE
# ═══════════════════════════════════════════════
def analyze(news_items, cat, tier):
    client = genai.Client(api_key=GEMINI_API_KEY)
    ns = "\n".join(news_items)
    persona = EXPERT.get(cat, EXPERT["Economy"])
    now = datetime.now()
    ts = now.strftime("%I:%M %p")
    tf = now.strftime("%B %d, %Y at %I:%M %p (UTC)")
    author = "Ethan Cole &amp; The Warm Insight Panel"
    acc = ACCURACY

    if tier == "Premium":
        prompt = (PROMPT_PREMIUM
                  .replace("[CATEGORY]", cat).replace("[PERSONA]", persona)
                  .replace("[ACCURACY]", acc).replace("[NEWS_ITEMS]", ns))
        raw, _ = gem_fb(client, tier, prompt)
        if not raw:
            return None, None, None, None, None, None
        html = build_premium(author, tf, raw)

    else:  # Royal Premium (VIP)
        hint = CAT_METRICS.get(cat, CAT_METRICS["Economy"])["hint"]
        al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
        al_str = str(al["s"]) + "% stocks, " + str(al["b"]) + "% safe, " + str(al["c"]) + "% cash (" + al["note"] + ")"

        # Part 1
        p1 = (VIP_P1
              .replace("[CATEGORY]", cat).replace("[PERSONA]", persona)
              .replace("[ACCURACY]", acc).replace("[CAT_HINT]", hint)
              .replace("[NEWS_ITEMS]", ns))
        raw1, _ = gem_fb(client, tier, p1)
        if not raw1:
            return None, None, None, None, None, None

        if not xtag(raw1, "VIP_C1") or is_echo(xtag(raw1, "VIP_C1")):
            print("    P1 quality low, retrying...")
            time.sleep(15)
            r1r, _ = gem_fb(client, tier, p1)
            if r1r and xtag(r1r, "VIP_C1") and not is_echo(xtag(r1r, "VIP_C1")):
                raw1 = r1r

        ctx = ("Title: " + xtag(raw1, "TITLE") + "\nHeadline: " + xtag(raw1, "HEADLINE")
               + "\nSummary: " + xtag(raw1, "SUMMARY") + "\nKey insight: " + xtag(raw1, "DEPTH")[:500])
        ctx_short = xtag(raw1, "HEADLINE") + ". " + xtag(raw1, "SUMMARY")

        # Part 2 (flash to save cost)
        print("    Part 2 (gemini-2.5-flash)...")
        time.sleep(10)
        p2 = (VIP_P2
              .replace("[CATEGORY]", cat).replace("[PERSONA]", persona)
              .replace("[ACCURACY]", acc).replace("[CTX]", ctx)
              .replace("[ALLOC_STR]", al_str).replace("[NEWS_ITEMS]", ns))
        raw2 = call_gem(client, "gemini-2.5-flash", p2)

        for retry in range(2):
            if raw2 and ok_tag(raw2, "VIP_T1"):
                break
            print("    P2 retry " + str(retry + 1))
            time.sleep(15)
            raw2 = call_gem(client, "gemini-2.5-flash", p2)

        if not raw2 or not ok_tag(raw2, "VIP_T1"):
            print("    P2 FAIL -> Fallback")
            time.sleep(10)
            fb = (VIP_FB
                  .replace("[CATEGORY]", cat).replace("[PERSONA]", persona)
                  .replace("[ACCURACY]", acc).replace("[CTX_SHORT]", ctx_short[:400])
                  .replace("[ALLOC_STR]", al_str).replace("[NEWS_ITEMS]", ns))
            raw2 = call_gem(client, "gemini-2.5-flash", fb)
            if not raw2:
                raw2 = ""

        raw = raw1 + "\n" + raw2
        html = build_vip(author, tf, raw, cat)

    tr = xtag(raw, "TITLE")
    exc = xtag(raw, "EXCERPT") or "Expert analysis."
    kw = xtag(raw, "SEO_KEYWORD")
    pretty = TIER_LABELS.get(tier, tier)
    title = "[" + pretty + "] " + tr if tr else "(" + tier + ") " + cat + " Insight"
    slug = make_slug(kw, tr or cat)
    html = sanitize(html)
    return title, html, exc, kw, slug, tier

# ═══════════════════════════════════════════════
# HTML HELPERS
# ═══════════════════════════════════════════════
F = "font-size:18px;line-height:1.8;color:#374151;"
MAIN = "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1a252c;width:100%;max-width:100%;overflow-x:hidden;box-sizing:border-box;word-break:break-word;margin-top:50px!important;"

def _hdr(author, tf, badge=""):
    b = ""
    if badge:
        b = (' <span style="background:#b8974d;color:#fff;padding:3px 12px;border-radius:4px;font-size:14px;font-weight:bold;">' + badge + '</span>')
    return ('<div style="border-top:3px solid #b8974d;border-bottom:1px solid #e5e7eb;padding:14px 0;margin-bottom:30px;">'
            '<p style="margin:0;font-size:16px;color:#4b5563;"><strong style="color:#1a252c;">' + author + '</strong> | ' + tf + b + '</p></div>')

def _ftr(tw, ps):
    if not tw or is_echo(tw):
        tw = "Stay disciplined, stay diversified, and let time compound in your favor."
    if not ps or is_echo(ps):
        ps = "In 40 years of watching markets, the disciplined investor always wins."
    share = ('<div style="background:#f8fafc;border:2px solid #e5e7eb;border-radius:10px;padding:28px;margin:40px 0;text-align:center;">'
             '<p style="font-size:22px;font-weight:bold;color:#1a252c;margin:0 0 8px;">Found this useful? Share the insight.</p>'
             '<p style="font-size:18px;color:#6b7280;margin:0 0 15px;">Forward this email to a colleague who wants smarter market analysis.</p>'
             '<p style="font-size:16px;color:#b8974d;font-weight:600;margin:0;">'
             '<a href="https://www.warminsight.com/#/portal/signup" style="color:#b8974d;text-decoration:underline;">Subscribe at warminsight.com</a></p></div>')
    foot = ('<div style="background:#1e293b;padding:35px;border-radius:10px;margin-top:30px;">'
            '<p style="font-size:24px;font-weight:bold;color:#b8974d;margin:0 0 8px;text-align:center;">Warm Insight</p>'
            '<p style="font-size:16px;color:#94a3b8;margin:0 0 20px;text-align:center;">AI-Driven Global Market Analysis</p>'
            '<div style="text-align:center;margin-bottom:20px;">'
            '<a href="https://www.warminsight.com/about/" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">About</a>'
            '<a href="https://www.warminsight.com/#/portal/signup" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">Subscribe</a>'
            '<a href="https://www.warminsight.com/tag/economy/" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">Economy</a>'
            '<a href="https://www.warminsight.com/tag/tech/" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">Tech</a>'
            '<a href="https://www.warminsight.com/tag/energy/" style="color:#cbd5e1;text-decoration:none;font-size:14px;margin:0 12px;">Energy</a></div>'
            '<div style="border-top:1px solid #475569;margin:20px 0;"></div>'
            '<p style="font-size:13px;color:#64748b;margin:0;text-align:center;line-height:1.8;">'
            'All analysis is for informational purposes only. Not financial advice. Always do your own research.<br>'
            'Contact: hello@warminsight.com | &copy; 2026 Warm Insight. All rights reserved.</p></div>')
    return ('<hr style="border:0;height:1px;background:#e5e7eb;margin:45px 0;">'
            '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Today\'s Warm Insight</h2>'
            '<p style="' + F + '">' + tw + '</p>'
            '<div style="margin-top:30px;background:#1e293b;padding:28px;border-radius:8px;border-left:4px solid #b8974d;">'
            '<p style="font-size:18px;line-height:1.8;color:#e2e8f0;margin:0;"><span style="color:#b8974d;font-weight:bold;font-size:20px;">P.S.</span> <span style="color:#cbd5e1;">' + ps + '</span></p></div>'
            + share + foot + '</div>')

def _up(msg):
    return '<div style="background:#fffbeb;border:2px solid #f59e0b;padding:18px;border-radius:8px;margin:35px 0;"><p style="font-size:18px;color:#92400e;margin:0;text-align:center;">' + msg + '</p></div>'

def _impact(imp):
    imp = (imp or "").upper().strip()
    cols = {"HIGH": ("#dc2626", "#fef2f2"), "MEDIUM": ("#d97706", "#fffbeb"), "LOW": ("#059669", "#ecfdf5")}
    c, bg = cols.get(imp, ("#6b7280", "#f3f4f6"))
    return ('<span style="display:inline-block;background:' + bg + ';color:' + c + ';border:2px solid ' + c + ';padding:4px 14px;border-radius:20px;font-size:14px;font-weight:bold;margin-bottom:20px;">IMPACT: ' + imp + '</span>') if imp else ""

def _keynum(kn, knc, color="#1e40af"):
    if not kn or not knc:
        return ""
    return ('<div style="background:#f0f9ff;border:2px solid ' + color + ';border-radius:12px;padding:28px;margin-bottom:30px;text-align:center;">'
            '<div style="font-size:48px;font-weight:800;color:' + color + ';margin-bottom:8px;">' + kn + '</div>'
            '<p style="font-size:18px;color:#374151;margin:0;">' + knc + '</p></div>')

def _qhits(raw):
    qh = xtag(raw, "QUICK_HITS")
    if not qh or is_echo(qh):
        return ""
    lines = [l.strip() for l in qh.strip().split("\n") if l.strip()]
    if not lines:
        return ""
    emos = ["⚡", "🔥", "📌"]
    items = ""
    for i, l in enumerate(lines[:3]):
        items += '<p style="font-size:18px;color:#374151;margin:10px 0;line-height:1.6;">' + (emos[i] if i < 3 else "•") + " " + l + '</p>'
    return ('<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:24px;margin-bottom:35px;">'
            '<h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:12px;text-transform:uppercase;letter-spacing:1px;">Quick Hits</h3>' + items + '</div>')

def _msnap(raw):
    ms = xtag(raw, "MARKET_SNAP")
    if not ms or is_echo(ms):
        return ""
    lines = [l.strip() for l in ms.strip().split("\n") if l.strip() and "|" in l]
    if len(lines) < 2:
        return ""
    icons = {"UP": ("▲", "#059669"), "DOWN": ("▼", "#dc2626"), "FLAT": ("—", "#6b7280")}
    cells = ""
    for line in lines[:4]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        name, direction = parts[0], parts[1].upper().strip()
        reason = parts[2][:40] if len(parts) > 2 else ""
        arrow, color = icons.get(direction, ("—", "#6b7280"))
        cells += ('<div style="flex:1;min-width:130px;text-align:center;padding:12px 8px;">'
                  '<div style="font-size:14px;color:#94a3b8;font-weight:600;margin-bottom:4px;">' + name + '</div>'
                  '<div style="font-size:22px;font-weight:800;color:' + color + ';">' + arrow + " " + direction + '</div>'
                  '<div style="font-size:12px;color:#64748b;margin-top:2px;">' + reason + '</div></div>')
    if not cells:
        return ""
    return '<div style="background:#1e293b;border-radius:10px;padding:12px;margin-bottom:30px;overflow-x:auto;"><div style="display:flex;flex-wrap:wrap;justify-content:space-around;">' + cells + '</div></div>'

def _compare(cb, cbear, bt="Bull Case", brt="Bear Case"):
    if not cb and not cbear:
        return ""
    bull = ('<div style="flex:1;min-width:220px;background:#ecfdf5;border:2px solid #10b981;border-radius:10px;padding:22px;">'
            '<h4 style="margin-top:0;font-size:20px;color:#065f46;">🐂 ' + bt + '</h4>'
            '<p style="font-size:18px;line-height:1.7;color:#064e3b;margin:0;">' + cb + '</p></div>') if cb else ""
    bear = ('<div style="flex:1;min-width:220px;background:#fef2f2;border:2px solid #ef4444;border-radius:10px;padding:22px;">'
            '<h4 style="margin-top:0;font-size:20px;color:#991b1b;">🐻 ' + brt + '</h4>'
            '<p style="font-size:18px;line-height:1.7;color:#7f1d1d;margin:0;">' + cbear + '</p></div>') if cbear else ""
    return '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">' + bull + bear + '</div>'

# ═══════════════════════════════════════════════
# BUILD PREMIUM
# ═══════════════════════════════════════════════
def build_premium(a, tf, r):
    return ('<div style="' + MAIN + '">' + _hdr(a, tf, "PRO") + _impact(xtag(r, "IMPACT")) + _keynum(xtag(r, "KEY_NUMBER"), xtag(r, "KEY_NUMBER_CONTEXT"))
            + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
            + '<p style="' + F + 'margin-bottom:35px;">' + xtag(r, "SUMMARY") + '</p>'
            + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:40px;">'
            + '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">💡 In Plain English</h3>'
            + '<p style="' + F + 'margin:0;">' + xtag(r, "TIKTOK") + '</p></div>'
            + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers</h2>'
            + '<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">' + xtag(r, "HEADLINE") + '</h3>'
            + '<p style="' + F + 'margin-bottom:28px;">' + xtag(r, "DEPTH") + '</p>'
            + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:20px;border-radius:8px;margin-bottom:35px;">'
            + '<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
            + '<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">' + xtag(r, "FLOW") + '</p></div>'
            + _compare(xtag(r, "COMPARE_BULL"), xtag(r, "COMPARE_BEAR")) + _qhits(r)
            + '<div style="background:#fff;border:2px solid #3b82f6;padding:28px;border-radius:8px;margin-bottom:35px;">'
            + '<h3 style="margin-top:0;color:#1e40af;font-size:22px;margin-bottom:14px;">💎 Pro-Only Insight</h3>'
            + '<p style="' + F + 'margin:0;">' + xtag(r, "PRO_INSIGHT") + '</p></div>'
            + '<div style="background:#ecfdf5;border:2px solid #10b981;padding:24px;border-radius:8px;margin-bottom:15px;">'
            + '<p style="font-size:18px;line-height:1.8;color:#065f46;margin:0;"><strong style="color:#065f46;font-size:20px;">🟢 DO:</strong> ' + xtag(r, "PRO_DO") + '</p></div>'
            + '<div style="background:#fef2f2;border:2px solid #ef4444;padding:24px;border-radius:8px;margin-bottom:35px;">'
            + '<p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;"><strong style="color:#991b1b;font-size:20px;">🔴 AVOID:</strong> ' + xtag(r, "PRO_DONT") + '</p></div>'
            + _up('🔒 Want institutional analysis? <strong>Upgrade to VIP.</strong>') + _ftr(xtag(r, "TAKEAWAY"), xtag(r, "PS")))

# ═══════════════════════════════════════════════
# BUILD VIP
# ═══════════════════════════════════════════════
def build_vip(a, tf, raw, cat):
    theme = CAT_THEME.get(cat, CAT_THEME["Economy"])
    accent = theme["accent"]
    al = CAT_ALLOC.get(cat, CAT_ALLOC["Economy"])
    l1, v1, l2, v2, l3, v3 = parse_graph(xtag(raw, "GRAPH_DATA"), cat)
    COL = [accent, "#f59e0b", "#10b981"]

    # Sentiment
    sent_h = ""
    try:
        sr = xtag(raw, "SENTIMENT")
        if sr and sr.strip():
            d = re.sub(r"[^0-9]", "", sr)
            if d:
                sv = max(0, min(100, int(d)))
                if sv <= 25: sl, sc = "EXTREME FEAR", "#dc2626"
                elif sv <= 40: sl, sc = "FEAR", "#ea580c"
                elif sv <= 60: sl, sc = "NEUTRAL", "#ca8a04"
                elif sv <= 75: sl, sc = "GREED", "#16a34a"
                else: sl, sc = "EXTREME GREED", "#059669"
                sent_h = ('<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:25px;margin-bottom:35px;">'
                          '<h3 style="margin-top:0;font-size:20px;color:#1a252c;margin-bottom:18px;">🧭 Fear &amp; Greed Meter</h3>'
                          '<div style="position:relative;width:100%;height:20px;border-radius:10px;overflow:hidden;background:linear-gradient(to right,#dc2626,#ea580c,#ca8a04,#16a34a,#059669);">'
                          '<div style="position:absolute;left:' + str(sv) + '%;top:0;width:4px;height:100%;background:#fff;border-radius:2px;box-shadow:0 0 4px rgba(0,0,0,0.5);"></div></div>'
                          '<div style="display:flex;justify-content:space-between;margin-top:8px;">'
                          '<span style="font-size:14px;color:#dc2626;font-weight:600;">Fear</span>'
                          '<span style="font-size:20px;color:' + sc + ';font-weight:800;">' + str(sv) + ' - ' + sl + '</span>'
                          '<span style="font-size:14px;color:#059669;font-weight:600;">Greed</span></div></div>')
    except Exception:
        pass

    # Conviction
    conv = xtag(raw, "CONVICTION").upper().strip()
    conv_h = ""
    if conv:
        cc = {"HIGH": ("#065f46", "#ecfdf5", "🟢"), "MEDIUM": ("#92400e", "#fffbeb", "🟡"), "LOW": ("#991b1b", "#fef2f2", "🔴")}
        c2, bg2, ci = cc.get(conv, ("#6b7280", "#f3f4f6", "⚪"))
        conv_h = ('<div style="background:' + bg2 + ';border:2px solid ' + c2 + ';border-radius:10px;padding:20px;margin-bottom:35px;text-align:center;">'
                  '<p style="font-size:14px;color:#6b7280;margin:0 0 5px;text-transform:uppercase;">Overall Conviction</p>'
                  '<p style="font-size:28px;font-weight:800;color:' + c2 + ';margin:0;">' + ci + ' ' + conv + '</p></div>')

    def gauge(lb, val, c):
        return ('<div style="margin-bottom:22px;"><div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
                '<span style="font-size:18px;font-weight:600;color:#374151;">' + lb + '</span>'
                '<span style="font-size:18px;font-weight:700;color:' + c + ';">' + str(val) + '%</span></div>'
                '<div style="width:100%;background:#e5e7eb;border-radius:8px;height:16px;overflow:hidden;">'
                '<div style="width:' + str(val) + '%;background:' + c + ';height:100%;border-radius:8px;"></div></div></div>')

    s, b, cp = al["s"], al["b"], al["c"]
    circ = 565.49
    sd, bd, cd = circ * s / 100, circ * b / 100, circ * cp / 100
    pie = ('<svg viewBox="0 0 200 200" width="200" height="200" style="display:block;margin:15px auto;">'
           '<circle cx="100" cy="100" r="90" fill="none" stroke="' + accent + '" stroke-width="30" stroke-dasharray="' + ("%.1f" % sd) + ' ' + ("%.1f" % circ) + '" stroke-dashoffset="0"/>'
           '<circle cx="100" cy="100" r="90" fill="none" stroke="#64748b" stroke-width="30" stroke-dasharray="' + ("%.1f" % bd) + ' ' + ("%.1f" % circ) + '" stroke-dashoffset="-' + ("%.1f" % sd) + '"/>'
           '<circle cx="100" cy="100" r="90" fill="none" stroke="#b8974d" stroke-width="30" stroke-dasharray="' + ("%.1f" % cd) + ' ' + ("%.1f" % circ) + '" stroke-dashoffset="-' + ("%.1f" % (sd + bd)) + '"/>'
           '<text x="100" y="92" text-anchor="middle" fill="#1a252c" font-size="16" font-weight="bold">' + str(s) + '/' + str(b) + '/' + str(cp) + '</text>'
           '<text x="100" y="114" text-anchor="middle" fill="#6b7280" font-size="11">ALLOCATION</text></svg>'
           '<div style="display:flex;justify-content:center;gap:20px;margin-bottom:8px;">'
           '<span style="font-size:16px;color:' + accent + ';">● Stocks ' + str(s) + '%</span>'
           '<span style="font-size:16px;color:#64748b;">● Safe ' + str(b) + '%</span>'
           '<span style="font-size:16px;color:#b8974d;">● Cash ' + str(cp) + '%</span></div>'
           '<p style="font-size:16px;color:#6b7280;text-align:center;font-style:italic;margin:5px 0 0;">' + al["note"] + '</p>')

    rr = ""
    for i in range(1, 5):
        v = ok_tag(raw, "VIP_RADAR_" + str(i))
        if not v:
            continue
        bull = "bullish" in v.lower()
        bg_r, tc, ic = ("#ecfdf5", "#065f46", "🟢 BULL") if bull else ("#fef2f2", "#991b1b", "🔴 BEAR")
        rr += ('<tr><td style="padding:14px;border-bottom:1px solid #e5e7eb;font-size:18px;color:#374151;">' + v + '</td>'
               '<td style="padding:14px;border-bottom:1px solid #e5e7eb;text-align:center;"><span style="background:' + bg_r + ';color:' + tc + ';padding:4px 12px;border-radius:6px;font-size:16px;font-weight:bold;">' + ic + '</span></td></tr>')
    radar = ('<div style="background:#fff;border:2px solid ' + accent + ';border-radius:8px;padding:25px;margin-bottom:35px;">'
             '<h3 style="margin-top:0;color:' + accent + ';font-size:22px;margin-bottom:18px;">🎯 Sector Radar</h3>'
             '<table style="width:100%;border-collapse:collapse;">' + rr + '</table></div>') if rr else ""

    def mc(lb, val, c):
        return ('<div style="flex:1;min-width:200px;background:#f8fafc;border:2px solid ' + c + ';border-radius:10px;padding:22px;text-align:center;">'
                '<div style="font-size:42px;font-weight:800;color:' + c + ';margin-bottom:5px;">' + str(val) + '%</div>'
                '<div style="font-size:16px;color:#4b5563;font-weight:600;">' + lb + '</div></div>')

    c1, c2, c3 = ok_tag(raw, "VIP_C1"), ok_tag(raw, "VIP_C2"), ok_tag(raw, "VIP_C3")
    t1, t2, t3, t4 = ok_tag(raw, "VIP_T1"), ok_tag(raw, "VIP_T2"), ok_tag(raw, "VIP_T3"), ok_tag(raw, "VIP_T4")
    vdo, vdont = ok_tag(raw, "VIP_DO"), ok_tag(raw, "VIP_DONT")
    tw, ps = ok_tag(raw, "TAKEAWAY"), ok_tag(raw, "PS")

    macro = ""
    if c1 or c2 or c3:
        pp = ""
        if c1:
            pp += '<p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;text-transform:uppercase;">Technical Signals</p><p style="' + F + 'margin-bottom:22px;">' + c1 + '</p>'
        if c2:
            pp += '<div style="border-top:1px solid #e5e7eb;margin:8px 0 18px;"></div><p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;text-transform:uppercase;">Macro Flows</p><p style="' + F + 'margin-bottom:22px;">' + c2 + '</p>'
        if c3:
            pp += '<div style="border-top:1px solid #e5e7eb;margin:8px 0 18px;"></div><p style="font-size:16px;color:' + accent + ';font-weight:bold;margin:0 0 8px;text-transform:uppercase;">Smart Money</p><p style="' + F + 'margin-bottom:0;">' + c3 + '</p>'
        macro = ('<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:25px;border-bottom:3px solid ' + accent + ';padding-bottom:12px;display:inline-block;">VIP: Macro &amp; Flow Analysis</h2>'
                 '<div style="background:#fff;border:1px solid #e5e7eb;border-left:5px solid ' + accent + ';padding:28px;border-radius:8px;margin-bottom:40px;">' + pp + '</div>')

    def pb(n, title, body, extra=""):
        if not body:
            return ""
        mt = "margin-top:22px;" if extra else ""
        return ('<div style="background:#f8fafc;border:1px solid #e5e7eb;border-left:4px solid ' + accent + ';padding:28px;border-radius:8px;margin-bottom:25px;">'
                '<h3 style="color:#1a252c;margin-top:0;font-size:24px;margin-bottom:18px;">' + str(n) + '. ' + title + '</h3>' + extra
                + '<p style="' + F + 'margin-bottom:0;' + mt + '">' + body + '</p></div>')

    pbc = (pb("1", "The Generational Bargain (Fear vs. Greed)", t1)
           + pb("2", "The " + str(s) + "/" + str(b) + "/" + str(cp) + " Seesaw", t2, pie)
           + pb("3", "The Global Shield (US Dollar &amp; Market)", t3)
           + pb("4", "Survival Mechanics (DCA &amp; Risk)", t4))
    pbk = ""
    if pbc:
        pbk = ('<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:12px;border-bottom:3px solid ' + accent + ';padding-bottom:12px;display:inline-block;">The Titans Playbook</h2>'
               '<p style="font-size:18px;color:#6b7280;margin-bottom:30px;font-style:italic;">Strategic manual for ' + cat.lower() + ' conditions.</p>' + pbc)

    act = ""
    if vdo or vdont:
        do_b = ('<div style="background:#ecfdf5;border:2px solid #10b981;border-radius:8px;padding:24px;margin-bottom:20px;"><p style="font-size:20px;color:#065f46;font-weight:bold;margin:0 0 12px;">🟢 DO:</p><p style="font-size:18px;line-height:1.8;color:#064e3b;margin:0;">' + vdo + '</p></div>') if vdo else ""
        dn_b = ('<div style="background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:24px;"><p style="font-size:20px;color:#991b1b;font-weight:bold;margin:0 0 12px;">🔴 AVOID:</p><p style="font-size:18px;line-height:1.8;color:#7f1d1d;margin:0;">' + vdont + '</p></div>') if vdont else ""
        act = '<div style="background:#1e293b;padding:35px;border-radius:10px;margin:45px 0 40px;"><h3 style="color:#b8974d;margin-top:0;font-size:26px;margin-bottom:25px;border-bottom:2px solid #475569;padding-bottom:15px;">✅ VIP Action Plan</h3>' + do_b + dn_b + '</div>'

    return ('<div style="' + MAIN + '">' + _hdr(a, tf, "VIP EXCLUSIVE")
            + '<div style="margin-bottom:25px;">' + _impact(xtag(raw, "IMPACT"))
            + '<span style="display:inline-block;background:#f8fafc;border:2px solid ' + accent + ';color:' + accent + ';padding:4px 14px;border-radius:20px;font-size:14px;font-weight:bold;">' + theme["icon"] + ' ' + theme["label"] + '</span></div>'
            + _keynum(xtag(raw, "KEY_NUMBER"), xtag(raw, "KEY_NUMBER_CONTEXT"), accent) + _msnap(raw) + sent_h
            + '<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:22px;margin-bottom:30px;">'
            + '<p style="font-size:16px;color:#6b7280;margin:0 0 12px;">⏱ <strong style="color:#1a252c;">8-10 min read</strong> | Full institutional analysis</p>'
            + '<div style="display:flex;flex-wrap:wrap;gap:8px;">'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">📊 Data</span>'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">🎯 Radar</span>'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">🔬 Macro</span>'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">📖 Playbook</span>'
            + '<span style="background:#e5e7eb;color:#374151;padding:4px 12px;border-radius:12px;font-size:14px;">✅ Action</span></div></div>'
            + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Executive Summary</h2>'
            + '<p style="' + F + 'margin-bottom:35px;">' + xtag(raw, "SUMMARY") + '</p>'
            + '<div style="background:#f3f4f6;border-left:5px solid #8e44ad;padding:24px;border-radius:8px;margin-bottom:40px;">'
            + '<h3 style="margin-top:0;font-size:22px;color:#1a252c;margin-bottom:12px;">💡 In Plain English</h3>'
            + '<p style="' + F + 'margin:0;">' + xtag(raw, "TIKTOK") + '</p></div>'
            + '<h2 style="font-family:Georgia,serif;font-size:28px;color:#1a252c;margin-bottom:18px;">Market Drivers &amp; Insights</h2>'
            + '<h3 style="font-size:24px;color:#1a252c;margin-bottom:14px;">' + xtag(raw, "HEADLINE") + '</h3>'
            + '<p style="' + F + 'margin-bottom:28px;">' + xtag(raw, "DEPTH") + '</p>'
            + '<div style="background:#f8fafc;border:1px solid #e5e7eb;padding:22px;border-radius:8px;margin-bottom:40px;">'
            + '<strong style="font-size:18px;color:#b8974d;">💡 Quick Flow:</strong>'
            + '<p style="font-size:20px;color:#1a252c;margin:10px 0 0;font-weight:bold;">' + xtag(raw, "FLOW") + '</p></div>'
            + '<div style="display:flex;gap:15px;flex-wrap:wrap;margin-bottom:35px;">' + mc(l1, v1, COL[0]) + mc(l2, v2, COL[1]) + mc(l3, v3, COL[2]) + '</div>'
            + '<div style="padding:28px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;margin-bottom:35px;">'
            + '<h3 style="margin-top:0;color:#1a252c;font-size:22px;border-bottom:2px solid #e5e7eb;padding-bottom:14px;margin-bottom:25px;">📊 Key Market Indicators</h3>'
            + gauge(l1, v1, COL[0]) + gauge(l2, v2, COL[1]) + gauge(l3, v3, COL[2]) + '</div>'
            + radar + _compare(ok_tag(raw, "COMPARE_BULL"), ok_tag(raw, "COMPARE_BEAR"), "Institutional Bull", "Institutional Bear")
            + macro + pbk + conv_h + act + _ftr(tw, ps))

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
def main():
    print("=" * 50)
    print("  Warm Insight v11 (2-Tier Cost Optimized)")
    print("  Tiers: Premium + VIP | Model: all flash")
    print("=" * 50)
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
            print("  ANALYZE FAILED for " + tier)
            fail += 1
            continue

        title, html, exc, kw, slug, _ = result

        if is_duplicate(title, recent):
            print("  SKIP dup")
            fail += 1
            continue

        # Editor review (skip for tiers in SKIP_EDITOR_TIERS)
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

        # Thumbnail: pre-uploaded Warmy mascot
        feature_img = get_thumb_url(tier, cat)

        # Publish
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

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nFATAL ERROR")
        traceback.print_exc()
        sys.exit(1)
