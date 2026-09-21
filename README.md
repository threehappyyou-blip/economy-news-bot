# Warm Insight Daily Short — GitHub Actions 자동화

매일 07:00 KST(=22:00 UTC)에 깃허브 서버가 스스로 깨어나서:
1. 15초 쇼츠 영상을 새로 만들고 (1080x1920, 워터마크 없음, 훅 문구 14개 로테이션)
2. jh0116jh@gmail.com 으로 영상 파일을 **직접 첨부해서** 이메일을 보냅니다 (캡션·해시태그·유튜브 태그 포함).

Claude 세션이 꺼져 있어도, 이 대화가 끝나도 계속 작동합니다. 한 번만 설정하면 됩니다.

## 폴더 구조

이 zip을 풀면 이렇게 생겼습니다 — **이 구조 그대로** 깃허브 저장소에 올리시면 됩니다.

```
.github/workflows/daily-short.yml   ← 자동 실행 설정 (건드릴 필요 없음)
warminsight-daily-short/            ← 실제 영상 생성 코드
  ├─ hooks.json
  ├─ scene_template.html
  ├─ build.js
  ├─ record.js
  ├─ gen_caption.js
  ├─ send_email.js
  └─ package.json
```

## 설정 방법 (한 번만 하면 됩니다)

### 1) 저장소 준비
- 기존에 쓰시는 깃허브 저장소(예: warminsight 관련 저장소)에 이 폴더 구조를 그대로 추가하셔도 되고,
- 새 저장소를 하나 만드셔서 (Public이든 Private이든 상관없습니다) 이 zip 내용을 그대로 업로드하셔도 됩니다.
- 깃허브 웹사이트에서 "Add file → Upload files"로 폴더째 드래그해서 올리시면 됩니다 (터미널/git 명령어 몰라도 가능합니다).

### 2) Gmail 앱 비밀번호 발급
Gmail 계정 보안 때문에 일반 비밀번호로는 이메일을 자동 발송할 수 없고, "앱 비밀번호"라는 별도 16자리 코드가 필요합니다.
1. https://myaccount.google.com/apppasswords 접속 (2단계 인증이 켜져 있어야 이 메뉴가 보입니다 — 안 켜져 있다면 먼저 2단계 인증부터 켜주세요)
2. 앱 이름에 "Warm Insight Daily Short" 같은 걸 입력하고 생성
3. 나오는 16자리 코드를 복사해두세요 (공백 없이)

### 3) 깃허브 저장소에 "비밀 값(Secrets)" 3개 등록
저장소 페이지에서 **Settings → Secrets and variables → Actions → New repository secret** 으로 들어가서 아래 3개를 각각 추가합니다.

| Secret 이름 | 값 |
|---|---|
| `GMAIL_USER` | 보내는 사람 Gmail 주소 (예: threehappyyou@gmail.com) |
| `GMAIL_APP_PASSWORD` | 2번에서 발급받은 16자리 앱 비밀번호 |
| `TO_EMAIL` | 받는 사람 이메일 (jh0116jh@gmail.com) |

### 4) 테스트로 한 번 수동 실행해보기
- 저장소 페이지 → **Actions** 탭 → 왼쪽에서 "Warm Insight Daily Short" 클릭 → 오른쪽 **"Run workflow"** 버튼 클릭
- 1~2분 정도 기다리면 실행이 끝나고, 초록 체크 표시가 뜨면 성공입니다
- jh0116jh@gmail.com 메일함을 확인해서 영상이 첨부된 이메일이 왔는지 확인하세요
- 빨간 X 표시가 뜨면, 그 실행 기록을 클릭해서 나오는 로그를 캡처해서 Claude에게 보여주시면 원인을 봐드릴 수 있어요

### 5) 이후에는?
- 아무것도 안 하셔도 매일 07:00 KST에 자동으로 실행됩니다.
- 훅 문구를 바꾸거나 디자인을 수정하고 싶으시면 `warminsight-daily-short/hooks.json` 또는 `scene_template.html`을 수정해서 다시 올리시면 됩니다 (또는 Claude에게 수정된 파일을 만들어달라고 요청하시면 됩니다).

## 비용
- 깃허브 Actions는 Public 저장소는 완전 무료, Private 저장소도 매달 일정량(보통 개인 계정 기준 한 달 2,000분) 무료 제공됩니다. 이 작업은 1회 실행에 1~2분 정도만 걸리므로 매일 돌려도 한 달에 60분 이내라 사실상 무료입니다.
- Claude나 Cowork 세션 비용은 이 자동화에는 전혀 들지 않습니다 — 완전히 깃허브 서버 안에서 끝나는 작업입니다.
