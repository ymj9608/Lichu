# Lichu → GitHub Actions → CSI 설정 가이드

검사 대상은 `https://github.com/ymj9608/Lichu`, 승인된 검사 도구는 `https://github.com/ymj9608/csi`입니다. `Lichu/`의 기존 Vue 3 + FastAPI 기능에 선택적으로 실행하는 회원가입 보안 실습을 추가했습니다.

> 현재 `dev`에는 비밀번호·로그 수정이 적용되었습니다. 아래 수정 전/패치 실습은 `baa9093` 기준입니다. 현재 검증 순서는 [전화번호 진단 실습](PHONE_NUMBER_DEMO.md)을 따르세요. 패치를 중복 적용하지 마세요.

## 1. 전체 흐름과 주소 구분

```text
Lichu 소스 수정 → git push (main, develop 또는 dev)
  → GitHub Hosted Runner
  → Lichu 소스 checkout + 승인된 CSI 커밋 checkout
  → Semgrep으로 Python/Java 소스 읽기 전용 검사
  → 문자열/주석 마스킹 → HMAC 서명 → HTTPS 접수 게이트웨이
  → Spring Boot (202 + scanId) → Kafka → LangGraph
  → business-mcp / rag-mcp → PostgreSQL → CSI 대시보드
```

| 주소 | 용도 |
|---|---|
| `http://127.0.0.1:8081/signup` | 실제 Lichu 회원가입 실습 사이트 |
| `http://127.0.0.1:5173` | CSI 보안 진단 대시보드 |
| `http://127.0.0.1:8080` | CSI 백엔드, 로컬 관리 API |
| `http://127.0.0.1:8091` | 검사 결과 접수 경로만 허용하는 게이트웨이 |
| `https://…trycloudflare.com` | GitHub Runner가 접근할 게이트웨이의 임시 HTTPS 주소 |

이 흐름은 Push한 소스코드를 검사합니다. 실행 중인 사이트의 URL을 크롤링하거나 공격하지 않습니다. Push 후 회원가입 사이트를 자동 배포하는 기능도 포함하지 않습니다. CSI 웹에서 새 결과를 자동 조회/SSE로 확인하는 흐름입니다.

## 2. 로컬 서비스 실행

Docker Desktop을 먼저 실행합니다. 터미널에서 작업 디렉터리로 이동합니다.

```sh
cd "/Users/yunmyeongjin/Desktop/MCP_실습/csi"
python3 scripts/init_env.py
docker compose up -d --build

cd ../Lichu
python3 scripts/init_csi_lab.py
docker compose --env-file .env.csi -f compose.csi-lab.yml up -d --build
docker compose -f compose.intake.yml up -d
```

`init_env.py`, `init_csi_lab.py`는 기존 환경 파일이 있으면 보존합니다. `.env.csi`는 원본 Lichu의 `.env`와 다른 파일이며 Git에서 제외됩니다. `.env.csi`의 임의 생성 비밀번호와 JWT 비밀키는 실습 DB/실습 서버에서만 사용합니다. 기존 Lichu DB에는 접속하지 않습니다.

```sh
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8091/health
curl http://127.0.0.1:8081/api/csi-lab
```

마지막 응답의 `enabled`는 `true`, `version`은 `before-fix`여야 합니다. 8081의 회원가입 화면에서 `테스트 데이터 채우기`를 누르고 가입하세요. 생성된 `csi_…` 아이디를 기억하고 `Demo-Only-2026!`로 로그인할 수 있습니다. 실습 회원가입은 `@example.com`, 테스트 이름, 고정 데모 비밀번호, 합성 휴대폰 번호만 허용하며 프로필 사진은 받지 않습니다.

## 3. CSI에 Repository 등록

`csi/.env`에서 다음 항목을 설정합니다. 현재 작업 환경에는 이미 반영했습니다.

```dotenv
CSI_REPOSITORY_ALLOWLIST=local/csi-demo,ymj9608/Lichu
```

GitHub 소유자와 저장소 이름은 대소문자까지 같은 값을 사용하고 쉼표 뒤에 공백을 넣지 않습니다.

```sh
cd ../csi
docker compose up -d backend
```

환경변수가 바뀌면 컨테이너를 재생성해야 하므로 `restart` 대신 `up -d`를 사용합니다. CSI 대시보드에 `.env`의 `CSI_ADMIN_USERNAME`/`CSI_ADMIN_PASSWORD`로 로그인한 뒤 **Projects → 프로젝트 등록**에서 다음을 입력합니다.

- Repository: `ymj9608/Lichu` (URL 전체가 아님)
- 기본 브랜치: `develop`

이미 등록되어 있다면 다시 등록하지 않습니다. 로컬 검증 도구도 같은 프로젝트를 한 번만 등록합니다.

## 4. GitHub 연결 전 로컬 전체 흐름 검증

현재 PC에는 CSI Python 환경과 Semgrep 환경이 준비되어 있습니다.

```sh
cd "/Users/yunmyeongjin/Desktop/MCP_실습/csi"
.venv/bin/python scripts/scan_repository.py ../Lichu \
  --repository ymj9608/Lichu \
  --submit-base http://127.0.0.1:8091
```

실제 소스 검사 → 게이트웨이 → HMAC 검증 → Kafka → Agent/MCP → DB 저장이 실행됩니다. 현재 수정 전 기준은 **10건**입니다.

| 방어 설계 검토 | 탐지 |
|---|---|
| 유출된 비밀번호 해시의 오프라인 추측 방어 | SEC-02, 비밀번호에 빠른 SHA-256 사용 1건 |
| 사전 계산 결과 재사용 방어 | SEC-03, 고정 Salt 1건 |
| 로그를 통한 비밀정보/개인정보 유출 방어 | SEC-05, 비밀번호·이메일·전화번호 로그 3건 |
| 사내 승인 범위를 벗어난 개인정보 처리 검토 | POL-01, 이름·휴대폰 번호 필드 후보 5건 |

마지막 항목은 독립적인 공격 기법이 아니라 정책 불일치 검토입니다. 필드 선언이 여러 계층에 있어 코드 위치별 후보가 각각 표시됩니다. 기본 PrivacyGuard 예제 정책을 그대로 적용하므로 기존 Lichu의 이름 필드도 검토 대상으로 남습니다. 실제 사내 승인 여부와 법률 위반을 확정하지 않습니다.

이 검사는 `LOCAL_DEMO`입니다. 표시된 SHA는 현재 분석한 파일들의 합성 식별자이며 GitHub Push의 commit SHA가 아닙니다.

새 PC에서 CSI Python 환경을 설치해야 한다면 `csi/README.md`의 `.venv` / `.scanner-venv` 절차를 먼저 실행합니다.

## 5. CSI 검사 도구를 GitHub에 먼저 올리기

`ymj9608/csi`에는 검사 도구 커밋이 이미 있고 `ymj9608/Lichu`에도 기존 이력이 있습니다. 기존 이력을 유지한 채 이번 변경을 커밋하고 Push합니다. CSI 검사기 코드를 바꾸지 않았다면 기존 CSI 커밋 SHA를 그대로 사용할 수 있습니다.

`csi/` 루트가 GitHub 저장소 루트여야 합니다. GitHub 파일 목록 바로 아래에 `scripts/`, `rules/`, `backend/`가 보여야 합니다.

```sh
cd "/Users/yunmyeongjin/Desktop/MCP_실습/csi"
git remote -v
# origin이 없는 경우에만 실행
git remote add origin https://github.com/ymj9608/csi.git
git add .
git diff --cached --stat
# 변경사항이 있을 때만 커밋
git commit -m "Update CSI integration documentation"
git push -u origin main
git rev-parse HEAD
```

마지막 명령의 **40자리 커밋 SHA**를 복사합니다. 해당 커밋에는 `rules/python-security.yml`, Python 파일을 허용하는 `scripts/scan.py`, 새 `scripts/submit.py`가 있어야 합니다. `.env`, `.runtime`, 가상환경은 `.gitignore`로 제외됩니다. 스테이징 목록을 확인한 뒤 Push하세요.

CSI 저장소 자신의 검사 job은 `CSI_SCAN_THIS_REPOSITORY=true`로 켜지 않는 한 건너뜁니다. 실제 검사 대상인 Lichu에는 별도 자동 워크플로가 있습니다.

## 6. GitHub Runner에서 접근할 HTTPS 주소 만들기

GitHub Hosted Runner의 `localhost`는 개발자 PC가 아닙니다. 실습에서는 검사 접수 게이트웨이를 Cloudflare Quick Tunnel로 연결할 수 있습니다.

macOS에서 `cloudflared`가 없다면 한 번 설치합니다.

```sh
brew install cloudflared
cloudflared tunnel --url http://127.0.0.1:8091
```

출력에 표시된 `https://임의이름.trycloudflare.com` 주소를 복사하고 이 터미널을 계속 켜 둡니다. **8081의 취약 실습 사이트나 8080의 관리 API 전체를 터널에 연결하지 마세요.** 제공된 게이트웨이는 `/health`와 서명된 결과 접수 경로만 전달합니다. `/api/projects`, `/internal/**` 등의 경로는 404입니다.

```sh
curl https://발급된주소.trycloudflare.com/health
```

터널을 다시 시작하면 주소가 바뀔 수 있습니다. 그때 GitHub의 `CSI_BACKEND_URL`도 갱신합니다. PC, Docker, CSI 서비스, 게이트웨이, 터널이 켜져 있어야 합니다. 장기 사용은 고정 도메인과 관리되는 HTTPS 서버로 교체합니다.

Quick Tunnel은 실습용이며 SLA가 없고 SSE를 지원하지 않습니다. 이 구성은 터널을 POST 접수에만 사용하고 CSI 대시보드는 로컬 5173에서 보므로 대시보드 SSE는 로컬 연결을 사용합니다. [Cloudflare Quick Tunnels 공식 문서](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/), [cloudflared 설치](https://developers.cloudflare.com/tunnel/downloads/).

## 7. Lichu GitHub Actions 설정

브라우저에서 `https://github.com/ymj9608/Lichu`를 열고 **Settings → Secrets and variables → Actions**로 이동합니다.

**Variables → New repository variable**에 두 개를 등록합니다.

| Name | Value |
|---|---|
| `CSI_SCANNER_REPOSITORY` | `ymj9608/csi` |
| `CSI_SCANNER_REF` | 5단계에서 Push한 CSI의 전체 40자리 SHA |

`main`, `develop`, 짧은 SHA를 `CSI_SCANNER_REF`에 넣으면 검사가 중단됩니다. 검토한 검사기 커밋에 고정해 대상 앱의 코드가 검사 규칙을 바꾸지 못하게 합니다.

**Secrets → New repository secret**에 두 개를 등록합니다.

| Name | Secret |
|---|---|
| `CSI_BACKEND_URL` | 6단계의 HTTPS 기본 주소. 예: `https://임의이름.trycloudflare.com` |
| `CSI_INTEGRATION_SECRET` | 로컬 `csi/.env`의 같은 이름 항목 값 |

`CSI_BACKEND_URL`에 `/api/integrations/github/scan-results`를 붙이지 않습니다. 전송 스크립트가 경로를 추가합니다. `CSI_INTEGRATION_SECRET`은 관리자 비밀번호, 내부 MCP 토큰, LLM API Key와 서로 다른 값입니다. Actions 로그나 YAML에 직접 적지 않습니다. [GitHub repository secrets 공식 설정 절차](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).

현재 두 저장소는 public이므로 별도의 읽기 토큰이 필요하지 않습니다. CSI 저장소를 private으로 바꾼다면 `ymj9608/csi`에만 **Contents: Read-only** 권한을 가진 토큰을 `CSI_SCANNER_READ_TOKEN` Secret에 추가합니다. Lichu의 기본 `GITHUB_TOKEN`만으로 다른 private 저장소를 읽을 수는 없습니다. [actions/checkout의 다른 private repository 예제](https://github.com/actions/checkout#checkout-multiple-repos-private).

**Settings → Actions → General**에서 워크플로 실행과 `actions/checkout`, `actions/setup-python` 사용이 허용되어 있어야 합니다. 워크플로 권한은 코드에 선언한 `contents: read`면 충분합니다. PR 쓰기 권한은 필요하지 않습니다.

## 8. Lichu의 수정 전 버전 Push

`Lichu/.github/workflows/csi-security-scan.yml`은 이미 구현되어 있습니다. `.github/`를 Lichu의 다른 디렉터리가 아닌 Lichu 저장소 루트에 두세요.

```sh
cd "/Users/yunmyeongjin/Desktop/MCP_실습/Lichu"
git remote -v
# 현재 origin은 이미 https://github.com/ymj9608/Lichu.git으로 설정되어 있습니다.
git add .
git diff --cached --stat
git commit -m "Add Lichu signup security baseline and CSI workflow"
git push -u origin main
```

GitHub **Actions → CSI Security Scan → 최신 실행**을 엽니다. 단계는 설정 검증 → 앱 checkout → 승인된 CSI checkout → Python 준비 → Semgrep 설치 → 소스 분석/마스킹 → 결과 전송 순서입니다.

검사 job은 대상 앱의 `npm`, `pytest`, `Maven`, 설치 스크립트 또는 서버를 실행하지 않습니다. 승인된 CSI 검사 코드만 실행합니다. `.py`/`.java` 외 웹 프론트엔드 TypeScript는 현재 분석 대상 밖입니다. 파일 종류와 무관하게 main/develop/dev Push는 검사 작업을 트리거합니다.

전송 성공 시 Actions Summary에 Scan ID와 정적 분석 건수가 표시됩니다. **Actions 성공은 HTTP 202 접수 성공이며 AI 완료/보안 통과 판정이 아닙니다.** CSI의 **Scan History**에서 같은 Scan ID가 `QUEUED → RUNNING → COMPLETED`로 바뀌는지 확인합니다. 실패하면 `FAILED`와 Execution Logs를 확인합니다.

기존 Local Demo와 달리 GitHub Push 검사에는 실제 commit SHA와 GitHub Actions Run URL이 표시됩니다. 강제로 같은 실행을 재시도해도 run ID/attempt로 중복 접수를 구분합니다.

수동 실행은 **Actions → CSI Security Scan → Run workflow**를 사용합니다. `workflow_dispatch`를 쓰려면 워크플로 파일이 기본 브랜치에 있어야 합니다. [GitHub 워크플로 트리거 문서](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

## 9. develop에서 수정 전/후 비교 시연

결과 비교는 같은 Repository와 같은 브랜치의 이전 완료 검사 기준입니다. 먼저 develop에 수정 전 기준을 만듭니다.

```sh
cd "/Users/yunmyeongjin/Desktop/MCP_실습/Lichu"
git switch -c develop
git push -u origin develop
```

이미 develop이 있으면 `git switch develop`을 사용합니다. **수정 전 develop 검사가 COMPLETED가 된 뒤** 아래 패치를 적용합니다.

```sh
git apply --check docs/csi/signup-remediation.patch
git apply docs/csi/signup-remediation.patch
git diff -- backend/app/core/csi_signup.py
git add backend/app/core/csi_signup.py
git commit -m "Use bcrypt cost 12 and remove sensitive signup logs"
git push
```

패치는 실제 회원가입 해시를 사용자별 무작위 Salt를 쓰는 bcrypt 비용 12로 바꾸고, 비밀번호·이메일·전화번호 로그를 제거합니다. 파일을 수동으로 수정했다면 패치를 억지로 적용하지 말고 코드 변경을 검토하세요.

현재 기준 예상: **10건 → 5건**, **5건 제거 / 5건 유지 / 0건 추가**. 남는 이름·휴대폰 번호 후보는 정책 검토가 필요합니다. 이를 없애려고 실제 수집 경로를 확인하지 않고 규칙을 비활성화하거나 승인 정책을 임의 변경하지 않습니다.

로컬 회원가입 앱에도 수정 내용을 반영하려면 다음을 실행합니다. GitHub Push 자체가 로컬 앱을 재배포하지는 않습니다.

```sh
docker compose --env-file .env.csi -f compose.csi-lab.yml up -d --build backend
```

수정 전 실습 SHA-256 계정은 이 패치 적용 후 로그인할 수 없습니다. 안전한 비밀번호 이관은 구현하지 않았으므로 `테스트 데이터 채우기`로 **새 합성 계정**을 만들어 테스트합니다. 기존 bcrypt 일반/seed 계정은 유지됩니다. 기본 제공 코드에는 패치를 적용하지 않았습니다.

## 10. 문제 해결 및 종료

| 증상 | 확인할 사항 |
|---|---|
| Actions 탭에 워크플로가 없음 | `.github/workflows/csi-security-scan.yml`을 Lichu 기본 브랜치에 Push했는지 |
| Validate scanner configuration 실패 | Variables 두 개와 전체 40자리 SHA |
| scanner checkout 실패 | CSI에 실제 커밋을 Push했는지, private이면 read token |
| No Java/Python sources | 대상에 backend/app 소스가 있는지, 올바른 Repository인지 |
| HTTPS required | URL이 https인지. Runner에 localhost 주소를 넣지 않았는지 |
| 401 | CSI_INTEGRATION_SECRET 일치, 로컬 시계/서명 Timestamp |
| 400 | Allowlist 정확한 `ymj9608/Lichu`, 백엔드 재생성, 최신 Python 수신 지원 |
| 404 | CSI Projects 등록, URL에 API 경로를 중복으로 붙이지 않았는지 |
| 502 / 연결 실패 | 터널 주소, 게이트웨이/CSI backend 실행 상태 |
| QUEUED/RUNNING에서 지연 또는 FAILED | Kafka/Agent/MCP 상태와 CSI Execution Logs |
| 분석 모드 RULE_BASED | LLM 비활성 설정. LangGraph/MCP/RAG는 실제로 실행됨 |
| LLM_FALLBACK | LLM 설정·응답 오류로 근거 기반 기본 분석 사용 |
| 수정 후 비교가 예상과 다름 | 같은 브랜치의 직전 COMPLETED 검사인지, 추가 소스 변경 여부 |

```sh
# Lichu 디렉터리: 서비스 로그
docker compose --env-file .env.csi -f compose.csi-lab.yml logs --tail=80 backend
docker compose -f compose.intake.yml logs --tail=80 intake

# csi 디렉터리: 분석 로그
docker compose logs --tail=100 backend agent business-mcp rag-mcp
```

실습용 회원가입 서버 로그에는 의도적으로 합성 비밀번호/이메일이 남습니다. CSI로 보내는 증거는 소스 위치와 마스킹된 코드이며 회원가입 DB와 런타임 로그를 수집하지 않습니다.

종료는 터널 터미널에서 Ctrl+C, Lichu 디렉터리에서 아래 명령입니다. DB volume은 유지합니다.

```sh
docker compose --env-file .env.csi -f compose.csi-lab.yml down
docker compose -f compose.intake.yml down
```

로컬 검증은 `verification.json`에 기록합니다. GitHub Secrets 등록, 외부 HTTPS 주소 연결, 실제 Push 실행이 끝나기 전에는 GitHub End-to-End 연동 완료로 간주하지 않습니다.


## 코드 변경 리뷰 스캐너

현재 workflow는 `fetch-depth: 0`으로 두 커밋을 읽고 CSI의 `scripts/scan_changes.py`로 전후를 검사합니다. `CSI_SCANNER_REF`는 이 파일과 `scripts/submit.py`의 `CSI_SCAN_FILE` 지원이 포함된 CSI 커밋 전체 SHA로 지정해야 합니다. 구버전 SHA를 유지하면 스크립트를 찾지 못해 실패합니다.

Push의 `before`와 현재 SHA가 비교 기준이며, 수동 실행은 현재 커밋의 부모를 사용합니다. 최초 Push/기준 미제공은 변경 비교 없음, 기준 객체를 찾지 못한 경우는 기준 조회 불가로 표시합니다. 파일 내용은 전송 전에 마스킹합니다. CSI 검사 상세 → **코드 변경 리뷰**에서 변경 파일을 선택해 전후 diff, 필드/함수 선언 요약, 연결된 신규·유지·미탐지 후보와 AI 분석을 확인합니다. 기존 완료 검사는 소급 갱신되지 않습니다.

새 기능을 추가하지 않고 workflow만 바꾼 Push는 Java/Python 변경 파일이 0개인 것이 정상입니다. 대상 앱 전체의 보안 검사는 계속 수행됩니다. 변경 리뷰 검증 방법과 MCP/Agent 구성은 CSI의 `docs/CHANGE_REVIEWS.md`에 있습니다.
